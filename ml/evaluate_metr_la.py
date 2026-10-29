"""Run development-only baseline evaluation; XGBoost and final test are blocked."""
import argparse
from datetime import datetime, timezone
import json
import platform
import subprocess
import time
import numpy as np
import h5py
from forecasting import ROOT, PROTOCOL_HASH, load_verified, fit_baselines, evaluate_validation, save_baselines, load_baselines


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-name", default="stage8b-baselines", help="New directory name under ignored data/processed")
    args = parser.parse_args()
    if not args.run_name or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in args.run_name):
        parser.error("run-name must contain only letters, numbers, hyphen or underscore")
    directory = ROOT / "data/processed" / args.run_name
    if directory.exists():
        parser.error("Run already exists; artifacts are not overwritten")
    started = time.perf_counter()
    protocol, ids, times, values, quality = load_verified()
    fitted = fit_baselines(times, values, protocol["splits"][0]["end_exclusive"])
    metadata = dict(source_sha256=protocol["source_sha256"], trained_at_utc=datetime.now(timezone.utc).isoformat(), versions=dict(python=platform.python_version(), numpy=np.__version__, h5py=h5py.__version__), code_base_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), code_files_sha256={name: __import__("inspect_metr_la").sha256(ROOT / "ml" / name) for name in ["forecasting.py", "evaluate_metr_la.py"]})
    save_baselines(directory, fitted, ids, metadata)
    loaded, _ = load_baselines(directory, ids, protocol["source_sha256"])
    report = dict(status="partial development evaluation; XGBoost feature contract unresolved; no final selection or test scoring", protocol_hash=PROTOCOL_HASH, metadata=metadata, shape=quality["shape"], splits=quality["protocol"]["splits"], validation=evaluate_validation(protocol, ids, times, values, loaded), elapsed_seconds=time.perf_counter() - started)
    (directory / "validation.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    for horizon, result in report["validation"].items():
        print(horizon, result["valid_targets"], result["coverage"], {name: value["overall"] for name, value in result["methods"].items()})
    print("Development-only report:", directory / "validation.json")


if __name__ == "__main__":
    main()
