"""Two-phase v2 experiment: develop first; final requires an intact frozen gate."""
import argparse
from datetime import datetime, timezone
import gc
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
import numpy as np
from forecasting import (ROOT, load_verified, fit_baselines, save_baselines, load_baselines,
                         evaluate_validation, persistence, historical_average, fingerprint)
from inspect_metr_la import sha256
from xgboost_forecasting import (V2_HASH, protocol_v2, sensor_mapping, training_arrays,
                                regressor, save_model, load_model, split_issues, features,
                                predict, summarize)


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def code_hashes():
    names = ["forecasting.py", "inspect_metr_la.py", "xgboost_forecasting.py", "train_metr_la.py",
             "test_forecasting.py", "test_inspect_metr_la.py", "test_xgboost_forecasting.py",
             "metr_la_protocol_v2.json", "requirements-forecasting.txt"]
    # Normalize CRLF for source reproducibility across Git checkouts.
    return {name: fingerprint((ROOT / "ml" / name).read_text(encoding="utf-8")) for name in names}


def peak_memory_bytes():
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD)] + [(name, ctypes.c_size_t) for name in ["peak", "working", "peak_paged", "paged", "peak_nonpaged", "nonpaged", "pagefile", "peak_pagefile"]]
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        kernel = ctypes.WinDLL("kernel32")
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi = ctypes.WinDLL("psapi")
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        if psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            return counters.peak
    return None


def verify_gate(directory):
    gate = json.loads((directory / "selection.json").read_text())
    if gate["protocol_hash"] != V2_HASH or gate["code_hashes"] != code_hashes():
        raise ValueError("Frozen gate protocol/code changed")
    for name, digest in gate["artifact_hashes"].items():
        if sha256(directory / name) != digest:
            raise ValueError(f"Frozen artifact changed: {name}")
    runtime = json.loads((directory / "run.json").read_text())
    if runtime["python"] != platform.python_version() or any(importlib.metadata.version(name) != version for name, version in runtime["versions"].items()):
        raise ValueError("Frozen runtime versions changed")
    validation = json.loads((directory / "validation.json").read_text())
    for h, choice in gate["selected"].items():
        methods = validation[h]["methods"]
        expected = min(["persistence", "historical_average", "xgboost"], key=lambda m: methods[m]["overall"]["mae"])
        if choice != expected:
            raise ValueError("Selection does not match frozen validation MAE")
    return gate


def develop(directory, protocol, ids, times, values):
    directory.mkdir(parents=True, exist_ok=False)
    metadata = dict(protocol_hash=V2_HASH, source_sha256=protocol["source_sha256"], started_utc=datetime.now(timezone.utc).isoformat(), versions={name: importlib.metadata.version(name) for name in ["numpy", "h5py", "xgboost", "scikit-learn", "scipy", "joblib", "threadpoolctl", "narwhals"]}, python=platform.python_version(), code_hashes=code_hashes(), base_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), platform=platform.platform())
    write_json(directory / "run.json", metadata)
    mapping = sensor_mapping(ids, values, times, protocol["splits"][0]["end_exclusive"])
    write_json(directory / "mapping.json", mapping)
    fitted = fit_baselines(times, values, protocol["splits"][0]["end_exclusive"])
    save_baselines(directory / "baselines", fitted, ids, {"source_sha256": protocol["source_sha256"]})
    results = evaluate_validation(protocol, ids, times, values, fitted)
    issues = split_issues(protocol, times, "validation")
    for horizon in protocol["horizons_steps"]:
        started = time.perf_counter()
        print(f"Building full training arrays: {horizon * 5} minutes", flush=True)
        x, y = training_arrays(directory, protocol, ids, mapping, times, values, horizon)
        construction = time.perf_counter() - started
        print(f"Fitting {len(y):,} genuine targets, 300 trees, one worker", flush=True)
        model = regressor(protocol)
        started = time.perf_counter()
        model.fit(x, y)
        training_seconds = time.perf_counter() - started
        count = len(y)
        save_model(model, directory, horizon, protocol, mapping)
        loaded = load_model(directory, horizon, protocol, mapping)
        probe = features(values, times, issues[:2], horizon, ids, mapping)
        np.testing.assert_array_equal(model.predict(probe), loaded.predict(probe))
        prediction, prediction_seconds = predict(loaded, values, times, issues, horizon, ids, mapping)
        result = summarize(values[issues + horizon], prediction, times[issues + horizon], ids)
        result.update(training_targets=count, training_seconds=training_seconds, construction_seconds=construction, prediction_including_features_seconds=prediction_seconds, process_peak_working_set_bytes=peak_memory_bytes())
        baseline = results[str(horizon * 5)]
        if result["overall"]["count"] != baseline["valid_targets"]:
            raise ValueError("Evaluation mask mismatch")
        result["mae_minus_best_baseline"] = result["overall"]["mae"] - min(m["overall"]["mae"] for m in baseline["methods"].values())
        baseline["methods"]["xgboost"] = result
        print(horizon * 5, result["overall"], "fit seconds", training_seconds, flush=True)
        del model, loaded, x, y, prediction
        gc.collect()
        # Only temporary arrays created in this exact run directory are removed.
        for suffix in ["x", "y"]:
            (directory / f"train-{horizon}-{suffix}.npy").unlink()
    write_json(directory / "validation.json", results)
    # Mandatory gate tests execute after all fits, before final test can be opened.
    tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "ml", "-p", "test_*.py", "-v"], cwd=ROOT, capture_output=True, text=True)
    (directory / "tests.txt").write_text(tests.stdout + tests.stderr)
    if tests.returncode or "skipped=" in tests.stderr or "\nOK\n" not in tests.stderr:
        raise ValueError("Gate tests failed or skipped; final test stays locked")
    selected = {h: min(["persistence", "historical_average", "xgboost"], key=lambda m: result["methods"][m]["overall"]["mae"]) for h, result in results.items()}
    report = "# Frozen development decision\n\nProtocol: " + V2_HASH + "\n\nAll three full-data candidates completed. Lowest validation MAE selects each horizon; no tuning or validation refit.\n\n"
    for h, choice in selected.items():
        report += f"- {h} minutes: {choice}; MAE {results[h]['methods'][choice]['overall']['mae']:.9f}\n"
    (directory / "development.md").write_text(report)
    hashes = {str(path.relative_to(directory)): sha256(path) for path in directory.rglob("*") if path.is_file()}
    write_json(directory / "selection.json", dict(protocol_hash=V2_HASH, selected=selected, code_hashes=code_hashes(), artifact_hashes=hashes, frozen_utc=datetime.now(timezone.utc).isoformat()))
    print("Development decisions frozen; final scoring has NOT run.", selected, flush=True)


def final(directory, protocol, ids, times, values):
    gate = verify_gate(directory)
    # Exclusive persistent marker prohibits retry, even if scoring later fails.
    write_json(directory / "final-started.json", dict(started_utc=datetime.now(timezone.utc).isoformat(), selection_sha256=sha256(directory / "selection.json")))
    mapping = json.loads((directory / "mapping.json").read_text())
    fitted, _ = load_baselines(directory / "baselines", ids, protocol["source_sha256"])
    issues = split_issues(protocol, times, "test")
    pp, pl = persistence(values, issues, fitted)
    results = {}
    for horizon in protocol["horizons_steps"]:
        key = str(horizon * 5)
        target = values[issues + horizon]
        target_times = times[issues + horizon]
        hp, hl = historical_average(target_times, fitted)
        methods = {"persistence": summarize(target, pp, target_times, ids), "historical_average": summarize(target, hp, target_times, ids)}
        for name, levels in [("persistence", pl), ("historical_average", hl)]:
            mask = np.isfinite(target) & (target > 0)
            methods[name]["fallback_scored_level_counts"] = {str(i): int(((levels == i) & mask).sum()) for i in range(3 if name == "persistence" else 4)}
        choice = gate["selected"][key]
        if choice == "xgboost":
            model = load_model(directory, horizon, protocol, mapping)
            prediction, seconds = predict(model, values, times, issues, horizon, ids, mapping)
            methods[choice] = summarize(target, prediction, target_times, ids)
            methods[choice]["prediction_including_features_seconds"] = seconds
            del model, prediction
        results[key] = dict(selected=choice, methods=methods)
        print("FINAL", key, choice, methods[choice]["overall"], flush=True)
    write_json(directory / "final.json", dict(selection_sha256=sha256(directory / "selection.json"), completed_utc=datetime.now(timezone.utc).isoformat(), results=results, process_peak_working_set_bytes=peak_memory_bytes()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["develop", "final"])
    parser.add_argument("--run-name", default="stage8c-v2")
    args = parser.parse_args()
    if not args.run_name or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in args.run_name):
        parser.error("Invalid run name")
    protocol = protocol_v2()
    _, ids, times, values, _ = load_verified()
    directory = ROOT / "data/processed" / args.run_name
    if args.phase == "develop":
        develop(directory, protocol, ids, times, values)
    else:
        final(directory, protocol, ids, times, values)


if __name__ == "__main__":
    main()
