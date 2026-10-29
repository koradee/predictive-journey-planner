"""Read-only METR-LA HDF5, sensor metadata, and frozen-protocol validation.

Reads the author's numeric pandas fixed-frame layout with h5py, never pickle.
Exit 0: integrity checks passed; 2: input/configuration error; 3: integrity failure.
Licensing and source-semantic limitations remain independent acceptance gates.
"""

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import platform
import sys

import h5py
import numpy as np


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def text(value):
    return value.decode("utf-8") if isinstance(value, bytes) else str(value)


def runs(mask):
    edges = np.diff(np.r_[False, mask, False].astype(np.int8))
    return np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)


def run_summary(mask, timestamps):
    starts, ends = runs(mask)
    lengths = ends - starts
    if not len(lengths):
        return {"runs": 0, "runs_at_least_60_minutes": 0, "longest_steps": 0, "start": None, "last_missing_timestamp": None}
    index = int(np.argmax(lengths))
    return {
        "runs": len(starts), "runs_at_least_60_minutes": int((lengths >= 12).sum()),
        "longest_steps": int(lengths[index]),
        "start": str(timestamps[starts[index]]),
        "last_missing_timestamp": str(timestamps[ends[index] - 1]),
    }


def read_hdf(path):
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"HDF file not found: {path}")
    if not h5py.is_hdf5(path):
        raise ValueError(f"Not a readable HDF5 file: {path}")
    with h5py.File(path, "r") as handle:
        required = ["df", "df/axis0", "df/axis1", "df/block0_items", "df/block0_values"]
        for key in required:
            if key not in handle or not isinstance(handle.get(key, getlink=True), h5py.HardLink):
                raise ValueError(f"Unsupported METR-LA layout: missing/internal hard link required at {key}")
        axes, index, items, matrix = (handle[k] for k in required[1:])
        if not all(isinstance(obj, h5py.Dataset) for obj in (axes, index, items, matrix)):
            raise ValueError("Unsupported HDF layout: numeric fixed-frame datasets required")
        if matrix.ndim != 2 or matrix.dtype.kind not in "fiu" or index.dtype.kind not in "iu":
            raise ValueError("Unsupported numeric matrix or timestamp representation")
        if axes.ndim != 1 or items.ndim != 1 or axes.dtype.kind not in "Siu" or items.dtype.kind not in "Siu":
            raise ValueError("Sensor axes must be simple fixed strings or integers; object serialization is not supported")
        if index.ndim != 1 or text(index.attrs.get("kind", b"")) != "datetime64":
            raise ValueError("Timestamp axis must declare datetime64")
        if matrix.shape != (len(index), len(axes)) or not len(index) or not len(axes):
            raise ValueError("HDF dimensions do not agree with timestamp/sensor axes")
        ids = [text(v) for v in axes[:]]
        if ids != [text(v) for v in items[:]]:
            raise ValueError("HDF axis0 and block0_items sensor order mismatch")
        timestamps = index[:].astype("datetime64[ns]")
        values = matrix[:]
        structure = {key: {"shape": list(handle[key].shape), "dtype": str(handle[key].dtype)} for key in required[1:]}
        tz_attrs, unit_attrs = [], []
        # Serialized pandas frequency attributes are intentionally not deserialized.
        for key in ["/", "df", *required[1:]]:
            for attribute in handle[key].attrs:
                if attribute.lower() in {"tz", "timezone"}:
                    tz_attrs.append({"node": key, "attribute": attribute, "value": text(handle[key].attrs[attribute])})
                if "unit" in attribute.lower():
                    unit_attrs.append({"node": key, "attribute": attribute, "value": text(handle[key].attrs[attribute])})
    return ids, timestamps, values, structure, tz_attrs, unit_attrs


def check_timestamps(timestamps):
    invalid = int(np.isnat(timestamps).sum())
    if invalid:
        raise ValueError(f"Timestamp axis contains {invalid} NaT values")
    delta = np.diff(timestamps).astype("timedelta64[ns]").astype(np.int64)
    duplicate = len(timestamps) - len(np.unique(timestamps))
    if duplicate or np.any(delta <= 0):
        raise ValueError(f"Timestamp axis must be strictly increasing and unique; duplicates={duplicate}")
    if np.any(delta != 300_000_000_000):
        raise ValueError("Timestamp frequency is not a complete five-minute grid; inspect gaps before proceeding")
    return {
        "count": len(timestamps), "first": str(timestamps[0]), "last": str(timestamps[-1]),
        "duplicate_timestamps": duplicate, "invalid_timestamps": invalid,
        "cadence_seconds": 300, "missing_grid_slots": 0,
        "timezone": "No localization applied; release timestamps are interpreted as naive datetime64[ns]",
    }


def read_csv(path, fields):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not set(fields).issubset(reader.fieldnames or []):
            raise ValueError(f"Metadata {path} must contain columns: {', '.join(fields)}")
        for row in reader:
            if None in row or any(row.get(f) is None for f in fields):
                raise ValueError(f"Malformed metadata row in {path}")
            yield row


def inspect_metadata(ids, ids_path, locations_path, distances_path):
    declared = [v.strip() for v in Path(ids_path).read_text(encoding="utf-8-sig").strip().split(",")]
    if len(set(ids)) != len(ids) or any(not value for value in ids):
        raise ValueError("Duplicate or empty HDF sensor IDs")
    if len(set(declared)) != len(declared) or any(not value for value in declared):
        raise ValueError("Duplicate or empty sensor IDs in ID metadata")
    if declared != ids:
        raise ValueError("Sensor ID metadata must match HDF columns in exact order")
    locations = list(read_csv(locations_path, ("sensor_id", "latitude", "longitude")))
    location_ids = [row["sensor_id"] for row in locations]
    if len(set(location_ids)) != len(location_ids):
        raise ValueError("Duplicate sensor IDs in location metadata")
    if set(location_ids) != set(ids):
        raise ValueError("Location sensor IDs do not match HDF sensors")
    coords = []
    for row in locations:
        lat, lon = float(row["latitude"]), float(row["longitude"])
        if not np.isfinite([lat, lon]).all() or not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError(f"Missing or invalid coordinates for sensor {row['sensor_id']}")
        if not (33 <= lat <= 35 and -120 <= lon <= -117):
            raise ValueError(f"Coordinates outside a broad Los Angeles sanity boundary: {row['sensor_id']}")
        coords.append((lat, lon))
    selected = set(ids)
    pairs, endpoints, covered = set(), set(), set()
    rows = selected_pairs = duplicate_pairs = 0
    for row in read_csv(distances_path, ("from", "to", "cost")):
        a, b, cost = row["from"].strip(), row["to"].strip(), float(row["cost"])
        if not a or not b or not np.isfinite(cost) or cost < 0:
            raise ValueError("Distance metadata contains empty IDs, invalid or negative cost")
        pair = (a, b)
        duplicate_pairs += pair in pairs
        pairs.add(pair)
        endpoints.update(pair)
        rows += 1
        if a in selected and b in selected:
            selected_pairs += 1
            covered.update(pair)
    if not rows or covered != selected:
        raise ValueError("Distance metadata does not cover every selected sensor")
    if duplicate_pairs:
        raise ValueError("Distance metadata contains duplicate directed pairs")
    return {
        "sensor_count": len(ids), "id_order_matches_hdf": True,
        "location_rows": len(locations), "duplicate_sensor_ids": 0, "missing_or_invalid_coordinates": 0,
        "location_order_matches_hdf": location_ids == ids,
        "latitude_range": [min(p[0] for p in coords), max(p[0] for p in coords)],
        "longitude_range": [min(p[1] for p in coords), max(p[1] for p in coords)],
        "duplicate_coordinate_pairs": len(coords) - len(set(coords)),
        "distance_rows": rows, "distance_distinct_endpoints": len(endpoints),
        "distance_pairs_with_both_endpoints_selected": selected_pairs,
        "distance_duplicate_directed_pairs": duplicate_pairs,
        "distance_cost_units": "not encoded; no conversion or routing-cost interpretation applied",
        "routing_limit": "Coordinates support a mapping pilot, but distances are not OSM edges, turn rules or segment geometry",
    }


def inspect_protocol(protocol_path, source_hash, timestamps, values, valid):
    protocol = json.loads(Path(protocol_path).read_text(encoding="utf-8"))
    if protocol["source_sha256"] != source_hash or protocol["expected_shape"] != list(values.shape):
        raise ValueError("Source hash or dimensions do not match the frozen protocol")
    if np.datetime64(protocol["native_timestamp_start"], "ns") != timestamps[0] or np.datetime64(protocol["native_timestamp_end_inclusive"], "ns") != timestamps[-1]:
        raise ValueError("Timestamp range does not match the frozen protocol")
    horizons = protocol["horizons_steps"]
    history = protocol["history_steps"]
    if horizons != [3, 6, 12] or history != 12 or protocol["cadence_seconds"] != 300:
        raise ValueError("Unsupported frozen history, horizon, or cadence configuration")
    results, last_end = [], timestamps[0]
    for split in protocol["splits"]:
        start, end = np.datetime64(split["start_inclusive"], "ns"), np.datetime64(split["end_exclusive"], "ns")
        if start != last_end or end <= start:
            raise ValueError("Protocol splits must be contiguous, chronological and nonempty")
        left, right = int(np.searchsorted(timestamps, start)), int(np.searchsorted(timestamps, end))
        if left >= right or timestamps[left] != start:
            raise ValueError("Protocol split boundary is outside the timestamp grid")
        issues = np.arange(max(left, history - 1), right - max(horizons))
        if not len(issues):
            raise ValueError("Protocol split contains no eligible issue timestamps")
        results.append({
            **split, "timestamps": right - left,
            "first_issue": str(timestamps[issues[0]]), "last_issue": str(timestamps[issues[-1]]),
            "issue_timestamps_after_common_60_minute_purge": len(issues),
            "raw_cells": int(values[left:right].size), "valid_raw_cells": int(valid[left:right].sum()),
            "label_coverage_by_horizon_minutes": {
                str(h * 5): {"eligible_cells": int(valid[issues + h].size), "valid_targets": int(valid[issues + h].sum()), "unavailable_targets": int((~valid[issues + h]).sum())}
                for h in horizons
            },
        })
        last_end = end
    if [s["name"] for s in results] != ["train", "validation", "test"] or last_end != timestamps[-1] + np.timedelta64(5, "m"):
        raise ValueError("Protocol must cover the whole release exactly once with train/validation/test")
    canonical = json.dumps(protocol, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return {"id": protocol["id"], "canonical_json_sha256": hashlib.sha256(canonical).hexdigest(), "splits": results, "evaluation_performed": False}


def inspect(path, ids_path, locations_path, distances_path, protocol_path=None):
    source_hash = sha256(path)
    ids, timestamps, values, structure, tz_attrs, unit_attrs = read_hdf(path)
    time_report = check_timestamps(timestamps)
    metadata = inspect_metadata(ids, ids_path, locations_path, distances_path)
    valid = np.isfinite(values) & (values > 0)
    per_sensor = []
    for column, sensor in enumerate(ids):
        unavailable = ~valid[:, column]
        per_sensor.append({
            "sensor_id": sensor, "zero_count": int((values[:, column] == 0).sum()),
            "nonfinite_count": int((~np.isfinite(values[:, column])).sum()),
            "unavailable_count": int(unavailable.sum()), "unavailable_fraction": float(unavailable.mean()),
            "outages": run_summary(unavailable, timestamps),
        })
    finite = values[np.isfinite(values)]
    if not len(finite):
        raise ValueError("Matrix contains no finite speed values")
    if np.any(values < 0):
        raise ValueError("Negative speed readings detected; source integrity requires review")
    report = {
        "source": {"filename": Path(path).name, "bytes": Path(path).stat().st_size, "sha256": source_hash},
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "h5py": h5py.__version__},
        "hdf_structure": structure, "shape": list(values.shape), "timestamps": time_report,
        "timezone_attributes": tz_attrs, "unit_attributes": unit_attrs,
        "metadata": metadata,
        "values": {
            "total_cells": int(values.size), "finite_min": float(finite.min()), "finite_max": float(finite.max()),
            "nan_count": int(np.isnan(values).sum()), "infinite_count": int(np.isinf(values).sum()),
            "zero_count": int((values == 0).sum()), "negative_count": 0,
            "over_100_native_units_screen_count": int((values > 100).sum()),
            "valid_positive_finite_count": int(valid.sum()), "unavailable_fraction": float((~valid).mean()),
            "all_sensors_unavailable_rows": int((~valid).all(axis=1).sum()),
            "simultaneous_outages": run_summary((~valid).all(axis=1), timestamps),
        },
        "per_sensor": per_sensor,
        "interpretation": {
            "zeros": "Unavailable under DCRNN benchmark mask; cannot identify true stopped traffic versus outages from this release",
            "units": "Not encoded; native speed scale retained. mph is a literature convention requiring explicit qualification",
            "timezone": "Not localized; naive timestamps do not establish UTC or America/Los_Angeles wall time",
            "geography": "Los Angeles sensors, not Pune road segments",
            "rights": "Underlying measurement-use rights unresolved; no redistribution/commercial authorization established",
            "training_performed": False,
        },
    }
    if protocol_path:
        report["protocol"] = inspect_protocol(protocol_path, source_hash, timestamps, values, valid)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--sensor-ids", type=Path, required=True)
    parser.add_argument("--locations", type=Path, required=True)
    parser.add_argument("--distances", type=Path, required=True)
    parser.add_argument("--protocol", type=Path)
    parser.add_argument("--output", type=Path, help="Optional JSON report outside raw/source directories; stdout otherwise")
    args = parser.parse_args(argv)
    inputs = [args.path, args.sensor_ids, args.locations, args.distances, *([args.protocol] if args.protocol else [])]
    for path in inputs:
        if not path.is_file():
            print(f"Input file not found: {path}", file=sys.stderr)
            return 2
    if args.output:
        destination = args.output.resolve()
        if (destination in {p.resolve() for p in inputs} or
                destination.is_relative_to(args.path.parent.resolve()) or
                any(part.lower() == "raw" for part in destination.parts)):
            print("Report output must not overwrite inputs or be written inside raw/source directories", file=sys.stderr)
            return 2
    try:
        result = inspect(args.path, args.sensor_ids, args.locations, args.distances, args.protocol)
        encoded = json.dumps(result, indent=2, allow_nan=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded, encoding="utf-8")
            print(f"Validation report written: {args.output}")
        else:
            print(encoded, end="")
        return 0
    except (OSError, ValueError, TypeError, KeyError, csv.Error, OverflowError) as error:
        print(f"METR-LA validation failed: {error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
