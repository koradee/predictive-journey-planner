"""Read-only quality inspection of CSV, CSV.gz, or CSV members in a ZIP archive."""

import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
import csv
from datetime import date, datetime, time
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys
import zipfile

COUNTS = ("car", "motorbike", "bus", "truck")
MISSING = {"", "na", "n/a", "null", "nan"}


@contextmanager
def open_csv(path, member=None):
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            with archive.open(member) as stream:
                with io.TextIOWrapper(stream, encoding="utf-8-sig", newline="") as text:
                    yield text
    elif path.name.lower().endswith(".csv.gz"):
        with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as text:
            yield text
    else:
        with path.open(encoding="utf-8-sig", newline="") as text:
            yield text


def inspect_csv(stream, name, timestamp_column, target, collection_month):
    sample = stream.read(8192)
    if not sample.strip():
        raise ValueError(f"Empty CSV: {name}")
    # Streams supplied here are seekable, including ZIP members.
    stream.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    reader = csv.reader(stream, dialect)
    columns = next(reader)
    if not columns or len(set(columns)) != len(columns) or any(not c.strip() for c in columns):
        raise ValueError(f"Missing or duplicated column names: {name}")
    if target and target not in columns:
        raise ValueError(f"Target column {target!r} absent from {name}")
    if timestamp_column and timestamp_column not in columns:
        raise ValueError(f"Timestamp column {timestamp_column!r} absent from {name}")
    timestamp_column = timestamp_column or next((c for c in columns if c.lower() in {"time", "timestamp", "datetime", "date_time"}), None)
    inferred_date = None
    if collection_month:
        match = re.fullmatch(r"[ajr]\d+_(\d{2})(?:_one)?\.csv", Path(name).name, re.I)
        if not match:
            raise ValueError(f"Cannot infer collection day from filename: {name}")
        inferred_date = date.fromisoformat(f"{collection_month}-{match[1]}")
    missing = Counter()
    types = defaultdict(Counter)
    numeric_ranges = {}
    seen_rows, seen_keys = set(), set()
    duplicates = duplicate_keys = malformed = rows = invalid_counts = invalid_times = 0
    directions = Counter()
    invalid_directions = 0
    times, previous = set(), {}
    steps = Counter()
    backwards = 0
    count_schema = set(COUNTS).issubset(columns)
    for row in reader:
        if not row:
            continue
        rows += 1
        if len(row) != len(columns):
            malformed += 1
            continue
        fingerprint = hashlib.sha256(json.dumps(row, ensure_ascii=False).encode()).digest()
        duplicates += fingerprint in seen_rows
        seen_rows.add(fingerprint)
        values = dict(zip(columns, row))
        for column, value in values.items():
            if value.strip().lower() in MISSING:
                missing[column] += 1
                continue
            try:
                number = float(value)
                if not math.isfinite(number):
                    types[column]["nonfinite"] += 1
                    if count_schema and column in COUNTS:
                        invalid_counts += 1
                    continue
                types[column]["integer" if number.is_integer() else "float"] += 1
                low, high = numeric_ranges.get(column, (number, number))
                numeric_ranges[column] = (min(low, number), max(high, number))
                if count_schema and column in COUNTS and (number < 0 or not number.is_integer()):
                    invalid_counts += 1
            except ValueError:
                types[column]["string"] += 1
                if count_schema and column in COUNTS:
                    invalid_counts += 1
        direction = values.get("Direction", "")
        if "Direction" in columns:
            directions[direction] += 1
            invalid_directions += direction not in {"UP", "DOWN", "LEFT", "RIGHT"}
        if timestamp_column:
            value = values[timestamp_column]
            try:
                if inferred_date:
                    stamp = datetime.combine(inferred_date, time.fromisoformat(value))
                elif re.fullmatch(r"\d{2}:\d{2}:\d{2}(?:\.\d+)?", value):
                    stamp = time.fromisoformat(value)
                else:
                    stamp = datetime.fromisoformat(value)
                # Time-only values are intentionally NOT assigned an invented date.
                seconds = stamp.hour * 3600 + stamp.minute * 60 + stamp.second + stamp.microsecond / 1e6
                if isinstance(stamp, datetime):
                    seconds += (stamp.date() - date(1970, 1, 1)).days * 86400
                coordinate = stamp.isoformat()
                key = (coordinate, direction)
                duplicate_keys += key in seen_keys
                seen_keys.add(key)
                times.add(coordinate)
                if direction in previous:
                    delta = seconds - previous[direction]
                    steps[delta] += 1
                    backwards += delta < 0
                previous[direction] = seconds
            except (ValueError, TypeError):
                invalid_times += 1
    if rows == 0:
        raise ValueError(f"No observations in {name}")
    candidates = [target] if target else [c for c in columns if any(token in c.lower() for token in ("speed", "travel_time", "travel time", "flow", "volume"))]
    if count_schema and not target:
        candidates = list(COUNTS)
    warnings = []
    if count_schema:
        warnings.append("Vehicle counts are not speed or travel-time labels; do not convert counts to travel time.")
    if timestamp_column and not inferred_date and timestamp_column.lower() == "time":
        warnings.append("Time-of-day alone is not a dated timeline; supply --collection-month only with verified filename metadata.")
    if backwards:
        warnings.append("Time decreases within a direction; inspect ordering, session boundaries, and possible midnight rollover.")
    if duplicate_keys:
        warnings.append("Repeated time/direction keys require review; do not blindly deduplicate or sum.")
    if steps.get(0) and steps.get(1):
        warnings.append("Repeated second-resolution timestamps observed; do not assume independent five-minute observations.")
    if any(missing.values()) or malformed or invalid_times or invalid_counts or invalid_directions:
        warnings.append("Missing, malformed, or invalid values detected; review the quality counters before defining labels.")
    if steps and any(delta > 300 for delta in steps):
        warnings.append("Gaps longer than five minutes detected; missing intervals must not be replaced with zero counts.")
    return {
        "file": name, "rows": rows, "columns": columns,
        "types_observed": {c: dict(types[c]) for c in columns},
        "missing_values": {c: missing[c] for c in columns},
        "numeric_ranges": numeric_ranges, "malformed_rows": malformed,
        "duplicate_rows": duplicates, "duplicate_timestamp_direction_keys": duplicate_keys,
        "invalid_count_values": invalid_counts, "directions": dict(directions),
        "invalid_directions": invalid_directions,
        "timestamp_column": timestamp_column, "collection_date_from_filename": str(inferred_date) if inferred_date else None,
        "timezone": "not encoded in CSV; confirm source timezone before modeling",
        "timestamp_min": min(times) if times else None, "timestamp_max": max(times) if times else None,
        "unique_timestamps": len(times), "invalid_timestamps": invalid_times,
        "backward_steps_within_direction": backwards,
        "observed_step_seconds_within_direction": {str(k): v for k, v in sorted(steps.items())},
        "candidate_targets": candidates, "warnings": warnings,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="CSV, .csv.gz, or ZIP file (read only)")
    parser.add_argument("--member", help="Inspect only this CSV member of a ZIP; otherwise inspect all CSV members")
    parser.add_argument("--timestamp-column", help="Explicit timestamp column; otherwise detect a common name")
    parser.add_argument("--target", help="Explicit existing target column; does not create a label")
    parser.add_argument("--collection-month", help="Verified YYYY-MM for Pune camera filename day suffixes, e.g. 2023-01")
    args = parser.parse_args(argv)
    try:
        if not args.path.is_file():
            raise ValueError(f"File not found: {args.path}")
        if args.collection_month:
            date.fromisoformat(args.collection_month + "-01")
        if args.path.suffix.lower() == ".zip":
            with zipfile.ZipFile(args.path) as archive:
                members = [n for n in archive.namelist() if n.lower().endswith(".csv") and not n.startswith("__MACOSX/")]
            if args.member:
                if args.member not in members:
                    raise ValueError(f"CSV member not found: {args.member}")
                members = [args.member]
            if not members:
                raise ValueError("Archive contains no CSV members")
        else:
            if args.member:
                raise ValueError("--member requires a ZIP archive")
            if not (args.path.name.lower().endswith(".csv") or args.path.name.lower().endswith(".csv.gz")):
                raise ValueError("Supported formats: .csv, .csv.gz, .zip (CSV members)")
            members = [None]
        with args.path.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        reports = []
        for member in members:
            with open_csv(args.path, member) as stream:
                reports.append(inspect_csv(stream, member or args.path.name, args.timestamp_column, args.target, args.collection_month))
        print(json.dumps({"source": str(args.path), "sha256": digest, "files_inspected": len(reports), "reports": reports}, indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError, csv.Error, UnicodeError, zipfile.BadZipFile, RuntimeError) as error:
        print(f"Inspection failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
