"""Frozen v2 features and safe XGBoost artifacts; offline METR-LA research only."""
import json
import time
import numpy as np
from xgboost import XGBRegressor
from forecasting import ROOT, fingerprint, valid, calendar, metrics, issue_indices
from inspect_metr_la import sha256

V2_HASH = "96e565e65a074141178678e51b6b0d6c40fcd5650a5da9b1fc9452184fc95676"


def protocol_v2():
    protocol = json.loads((ROOT / "ml/metr_la_protocol_v2.json").read_text())
    if fingerprint(protocol) != V2_HASH:
        raise ValueError("Frozen v2 protocol fingerprint mismatch")
    original = json.loads((ROOT / "ml/metr_la_protocol.json").read_text())
    for key in original:
        if key != "id" and protocol[key] != original[key]:
            raise ValueError(f"Unapproved v1 change: {key}")
    return protocol


def sensor_mapping(ids, values, times, training_end):
    end = int(np.searchsorted(times, np.datetime64(training_end)))
    observed = valid(values[:end]).any(axis=0)
    return {sensor: i for i, sensor in enumerate(sorted(sensor for sensor, seen in zip(ids, observed) if seen))}


def features(values, times, issues, horizon, ids, mapping):
    """Only index historical values; target timestamps supply calendar fields only."""
    if horizon not in (3, 6, 12) or len(issues) == 0 or min(issues) < 11 or max(issues) + horizon >= len(times):
        raise ValueError("Invalid issue/horizon bounds")
    if len(set(ids)) != len(ids) or values.shape[1] != len(ids) or any(s not in mapping for s in ids):
        raise ValueError("Unknown, duplicate or misaligned sensor IDs")
    history = values[issues[:, None] + np.arange(-11, 1)[None, :]].transpose(0, 2, 1)
    mask = valid(history)
    count = mask.sum(axis=2)
    total = np.where(mask, history, 0).sum(axis=2)
    mean = np.full(count.shape, np.nan)
    np.divide(total, count, out=mean, where=count > 0)
    variance = np.full(count.shape, np.nan)
    deviations = np.where(mask, history - mean[:, :, None], 0)
    np.divide((deviations ** 2).sum(axis=2), count, out=variance, where=count > 0)
    minimum = np.where(mask, history, np.inf).min(axis=2)
    maximum = np.where(mask, history, -np.inf).max(axis=2)
    minimum[count == 0] = np.nan
    maximum[count == 0] = np.nan
    x = np.empty((len(issues), len(ids), 32), dtype=np.float32)
    x[:, :, 0] = [mapping[s] for s in ids]
    weekday, slot = calendar(times[issues + horizon])
    x[:, :, 1] = weekday[:, None]
    x[:, :, 2] = slot[:, None]
    x[:, :, 3:15] = np.where(mask, history, np.nan)
    x[:, :, 15:27] = ~mask
    for column, statistic in enumerate([mean, np.sqrt(variance), minimum, maximum, count], 27):
        x[:, :, column] = statistic
    return x.reshape(-1, 32)


def parameters(protocol):
    return {k: v for k, v in protocol["xgboost_candidate"].items() if k not in {"class", "early_stopping", "tuning"}}


def regressor(protocol):
    return XGBRegressor(**parameters(protocol), enable_categorical=True,
                        feature_types=protocol["feature_contract"]["feature_types"])


def split_issues(protocol, times, split):
    definition = next(s for s in protocol["splits"] if s["name"] == split)
    indices = issue_indices(times, definition, protocol["history_steps"], max(protocol["horizons_steps"]))
    if not len(indices) or np.any(times[indices + 12] >= np.datetime64(definition["end_exclusive"])):
        raise ValueError("Split leakage or empty split")
    return indices


def training_arrays(directory, protocol, ids, mapping, times, values, horizon):
    """Disk-backed float32 arrays, built in chunks; no row sampling or DataFrames."""
    issues = split_issues(protocol, times, "train")
    count = int(valid(values[issues + horizon]).sum())
    x = np.lib.format.open_memmap(directory / f"train-{horizon}-x.npy", mode="w+", dtype="float32", shape=(count, 32))
    y = np.lib.format.open_memmap(directory / f"train-{horizon}-y.npy", mode="w+", dtype="float32", shape=(count,))
    offset = 0
    for start in range(0, len(issues), 256):
        ticks = issues[start:start + 256]
        target = values[ticks + horizon].reshape(-1)
        mask = valid(target)
        batch = features(values, times, ticks, horizon, ids, mapping)
        n = int(mask.sum())
        x[offset:offset + n] = batch[mask]
        y[offset:offset + n] = target[mask]
        offset += n
    if offset != count:
        raise ValueError("Training target count mismatch")
    x.flush()
    y.flush()
    return x, y


def save_model(model, directory, horizon, protocol, mapping):
    path = directory / f"xgb-{horizon}.json"
    model.save_model(path)
    metadata = dict(protocol_hash=V2_HASH, source_sha256=protocol["source_sha256"], feature_contract=protocol["feature_contract"], mapping=mapping, parameters=parameters(protocol), horizon=horizon, model_sha256=sha256(path))
    (directory / f"xgb-{horizon}-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (directory / f"xgb-{horizon}-config.json").write_text(model.get_booster().save_config())


def load_model(directory, horizon, protocol, mapping):
    metadata = json.loads((directory / f"xgb-{horizon}-metadata.json").read_text())
    path = directory / f"xgb-{horizon}.json"
    expected = dict(protocol_hash=V2_HASH, source_sha256=protocol["source_sha256"], feature_contract=protocol["feature_contract"], mapping=mapping, parameters=parameters(protocol), horizon=horizon, model_sha256=sha256(path))
    if metadata != expected:
        raise ValueError("Corrupt or incompatible XGBoost metadata")
    model = regressor(protocol)
    model.load_model(path)
    booster = model.get_booster()
    if booster.num_features() != 32 or booster.num_boosted_rounds() != 300 or booster.feature_types != protocol["feature_contract"]["feature_types"]:
        raise ValueError("XGBoost model structure mismatch")
    return model


def predict(model, values, times, issues, horizon, ids, mapping):
    prediction = np.empty((len(issues), len(ids)), dtype=np.float64)
    started = time.perf_counter()
    for start in range(0, len(issues), 256):
        ticks = issues[start:start + 256]
        prediction[start:start + len(ticks)] = model.predict(features(values, times, ticks, horizon, ids, mapping)).reshape(len(ticks), len(ids))
    return prediction, time.perf_counter() - started


def summarize(target, prediction, target_times, ids):
    mask = valid(target)
    weekday, slot = calendar(target_times)
    peak = (weekday < 5) & (((slot >= 84) & (slot < 108)) | ((slot >= 192) & (slot < 228)))
    return dict(overall=metrics(target, prediction, mask), eligible_cells=int(mask.size), coverage=float(mask.mean()), peak=metrics(target, prediction, mask & peak[:, None]), off_peak=metrics(target, prediction, mask & ~peak[:, None]), per_sensor={s: metrics(target[:, i], prediction[:, i], mask[:, i]) for i, s in enumerate(ids)})
