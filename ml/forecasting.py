"""Training-only baselines for the frozen METR-LA research protocol.

No XGBoost feature interpretation or final-test evaluation is implemented.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from inspect_metr_la import inspect, read_hdf, sha256

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_HASH = "474f3ad531bb3b70476ecd3f6e42d13b04efb09f4b057d76266b49510d7d8144"


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def load_verified():
    protocol = json.loads((ROOT / "ml/metr_la_protocol.json").read_text())
    if fingerprint(protocol) != PROTOCOL_HASH:
        raise ValueError("Frozen protocol fingerprint mismatch")
    raw = ROOT / "data/raw/metr-la"
    manifest = json.loads((ROOT / "data/metr-la-manifest.json").read_text())
    for source in manifest["files"]:
        path = raw / source["filename"]
        if path.stat().st_size != source["bytes"] or sha256(path) != source["sha256"]:
            raise ValueError(f"Source hash/size mismatch: {path.name}")
    report = inspect(raw / "metr-la.h5", raw / "graph_sensor_ids.txt", raw / "graph_sensor_locations.csv", raw / "distances_la_2012.csv", ROOT / "ml/metr_la_protocol.json")
    ids, times, values, *_ = read_hdf(raw / "metr-la.h5")
    return protocol, ids, times, values, report


def valid(values):
    return np.isfinite(values) & (values > 0)


def calendar(times):
    days = times.astype("datetime64[D]")
    weekday = (days.astype(np.int64) + 3) % 7
    slot = (times - days).astype("timedelta64[m]").astype(np.int64) // 5
    return weekday, slot


def issue_indices(times, split, history=12, max_horizon=12):
    left, right = np.searchsorted(times, [np.datetime64(split["start_inclusive"]), np.datetime64(split["end_exclusive"])])
    return np.arange(max(int(left), history - 1), int(right) - max_horizon)


def fit_baselines(times, values, training_end):
    """Only observations strictly before training_end enter any fitted statistic."""
    end = int(np.searchsorted(times, np.datetime64(training_end)))
    train = values[:end]
    mask = valid(train)
    if not mask.any():
        raise ValueError("No valid training observations")
    global_median = float(np.median(train[mask]))
    medians = np.array([np.median(train[:, s][mask[:, s]]) if mask[:, s].any() else global_median for s in range(train.shape[1])])
    sensor_available = mask.any(axis=0)
    weekday, slot = calendar(times[:end])
    tables = []
    for keys, size in [(weekday * 288 + slot, 7 * 288), (weekday * 24 + slot // 12, 7 * 24)]:
        sums = np.zeros((size, train.shape[1]))
        counts = np.zeros_like(sums, dtype=np.int64)
        np.add.at(sums, keys, np.where(mask, train, 0))
        np.add.at(counts, keys, mask)
        table = np.full_like(sums, np.nan)
        np.divide(sums, counts, out=table, where=counts > 0)
        tables.append(table)
    return dict(sensor_median=medians, sensor_available=sensor_available, global_median=np.array(global_median), slot=tables[0], hour=tables[1])


def persistence(values, issues, fitted, history=12):
    prediction = np.broadcast_to(fitted["sensor_median"], (len(issues), values.shape[1])).copy()
    # Levels: latest reading=0, sensor median=1, global median=2.
    level = np.broadcast_to(np.where(fitted["sensor_available"], 1, 2), prediction.shape).copy()
    for lag in range(history - 1, -1, -1):
        observation = values[issues - lag]
        available = valid(observation)
        prediction[available] = observation[available]
        level[available] = 0
    return prediction, level


def historical_average(target_times, fitted):
    weekday, slot = calendar(target_times)
    prediction = fitted["slot"][weekday * 288 + slot].copy()
    level = np.zeros(prediction.shape, dtype=np.int8)
    missing = ~np.isfinite(prediction)
    hourly = fitted["hour"][weekday * 24 + slot // 12]
    prediction[missing] = hourly[missing]
    level[missing] = 1
    missing = ~np.isfinite(prediction)
    medians = np.broadcast_to(fitted["sensor_median"], prediction.shape)
    prediction[missing] = medians[missing]
    fallback = np.broadcast_to(np.where(fitted["sensor_available"], 2, 3), prediction.shape)
    level[missing] = fallback[missing]
    return prediction, level


def metrics(target, prediction, mask):
    if mask.shape != target.shape or prediction.shape != target.shape:
        raise ValueError("Metric shapes differ")
    if np.any(mask & ~valid(target)) or not np.isfinite(prediction[mask]).all():
        raise ValueError("Invalid scored targets or predictions")
    errors = prediction[mask] - target[mask]
    return dict(count=int(errors.size), mae=float(np.mean(np.abs(errors))) if errors.size else None, rmse=float(np.sqrt(np.mean(errors ** 2))) if errors.size else None)


def evaluate_validation(protocol, ids, times, values, fitted):
    """Deliberately exposes no test split argument while the selection gate is blocked."""
    split = next(s for s in protocol["splits"] if s["name"] == "validation")
    issues = issue_indices(times, split, protocol["history_steps"], max(protocol["horizons_steps"]))
    persistence_prediction, persistence_level = persistence(values, issues, fitted)
    report = {}
    for horizon in protocol["horizons_steps"]:
        targets = values[issues + horizon]
        mask = valid(targets)
        weekday, slot = calendar(times[issues + horizon])
        peak = (weekday < 5) & (((slot >= 84) & (slot < 108)) | ((slot >= 192) & (slot < 228)))
        ha_prediction, ha_level = historical_average(times[issues + horizon], fitted)
        methods = {}
        for name, prediction, level, names in [
            ("persistence", persistence_prediction, persistence_level, ["latest", "sensor_median", "global_median"]),
            ("historical_average", ha_prediction, ha_level, ["slot", "hour", "sensor_median", "global_median"]),
        ]:
            methods[name] = dict(overall=metrics(targets, prediction, mask), peak=metrics(targets, prediction, mask & peak[:, None]), off_peak=metrics(targets, prediction, mask & ~peak[:, None]), per_sensor={sensor: metrics(targets[:, s], prediction[:, s], mask[:, s]) for s, sensor in enumerate(ids)}, fallback_scored_counts={label: int(((level == i) & mask).sum()) for i, label in enumerate(names)}, fallback_all_eligible_counts={label: int((level == i).sum()) for i, label in enumerate(names)})
        best = min(methods, key=lambda name: methods[name]["overall"]["mae"])
        for result in methods.values():
            result["mae_minus_best_baseline"] = result["overall"]["mae"] - methods[best]["overall"]["mae"]
        report[str(horizon * 5)] = dict(eligible_cells=int(mask.size), valid_targets=int(mask.sum()), coverage=float(mask.mean()), best_baseline_only=best, methods=methods)
    return report


def save_baselines(directory, fitted, ids, metadata):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    np.savez(directory / "baselines.npz", **fitted)
    contract = {**metadata, "format": "metr-la-baselines-v1", "sensor_ids": ids, "protocol_hash": PROTOCOL_HASH, "arrays_sha256": sha256(directory / "baselines.npz")}
    (directory / "metadata.json").write_text(json.dumps(contract, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def load_baselines(directory, expected_ids, expected_source_hash):
    directory = Path(directory)
    contract = json.loads((directory / "metadata.json").read_text())
    if (contract.get("format") != "metr-la-baselines-v1" or contract.get("protocol_hash") != PROTOCOL_HASH or contract.get("sensor_ids") != expected_ids or contract.get("source_sha256") != expected_source_hash or contract.get("arrays_sha256") != sha256(directory / "baselines.npz")):
        raise ValueError("Incompatible or corrupted baseline artifact contract")
    with np.load(directory / "baselines.npz", allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    n = len(expected_ids)
    shapes = dict(sensor_median=(n,), sensor_available=(n,), global_median=(), slot=(2016, n), hour=(168, n))
    if set(arrays) != set(shapes) or any(arrays[k].shape != shape for k, shape in shapes.items()):
        raise ValueError("Invalid baseline array schema")
    if arrays["sensor_available"].dtype != np.bool_ or not valid(arrays["sensor_median"]).all() or not valid(arrays["global_median"]):
        raise ValueError("Invalid baseline fallback values")
    for name in ["slot", "hour"]:
        if np.any(~np.isnan(arrays[name]) & ~valid(arrays[name])):
            raise ValueError("Invalid historical table values")
    return arrays, contract
