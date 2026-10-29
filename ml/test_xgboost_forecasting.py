"""Synthetic unit fixtures only; never used for reported benchmark scores."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from forecasting import fingerprint
from xgboost_forecasting import (V2_HASH, protocol_v2, features, sensor_mapping, split_issues,
                                training_arrays, regressor, save_model, load_model, summarize)
from train_metr_la import verify_gate, write_json


class XGBoostTests(unittest.TestCase):
    def setUp(self):
        self.protocol = protocol_v2()
        self.times = np.datetime64("2012-03-01T00:00") + np.arange(120) * np.timedelta64(5, "m")
        self.values = np.arange(240, dtype=float).reshape(120, 2) + 1
        self.ids = ["b", "a"]
        self.mapping = {"a": 0, "b": 1}

    def test_protocol_hash_and_unchanged_v1_fields(self):
        self.assertEqual(fingerprint(self.protocol), V2_HASH)
        with patch("xgboost_forecasting.fingerprint", return_value="wrong"):
            with self.assertRaisesRegex(ValueError, "fingerprint"):
                protocol_v2()

    def test_exact_feature_order_dtype_and_calendar(self):
        names = ["sensor_id", "target_weekday", "target_slot"] + [f"lag_{i}" for i in range(11, -1, -1)] + [f"lag_{i}_missing" for i in range(11, -1, -1)] + ["history_mean", "history_std", "history_min", "history_max", "history_valid_count"]
        self.assertEqual(self.protocol["feature_contract"]["names"], names)
        x = features(self.values, self.times, np.array([11]), 3, self.ids, self.mapping)
        self.assertEqual(x.dtype, np.float32)
        self.assertEqual(x.shape, (2, 32))
        np.testing.assert_array_equal(x[:, 0], [1, 0])
        np.testing.assert_array_equal(x[:, 1], [3, 3])
        np.testing.assert_array_equal(x[:, 2], [14, 14])
        np.testing.assert_array_equal(x[0, 3:15], self.values[:12, 0])
        np.testing.assert_array_equal(x[0, 15:27], np.zeros(12))
        np.testing.assert_allclose(x[0, 27:], [12, np.std(self.values[:12, 0]), 1, 23, 12], rtol=1e-6)

    def test_causal_statistics_missing_and_all_missing(self):
        self.values[:12] = 0
        self.values[2, 0], self.values[4, 0] = 10, 20
        self.values[6, 0], self.values[8, 0] = np.nan, np.inf
        x = features(self.values, self.times, np.array([11]), 6, self.ids, self.mapping)
        np.testing.assert_array_equal(x[0, 27:], [15, 5, 10, 20, 2])
        self.assertEqual(x[0, 15:27].sum(), 10)
        self.assertTrue(np.isnan(x[1, 3:15]).all())
        self.assertTrue(np.isnan(x[1, 27:31]).all())
        self.assertEqual(x[1, 31], 0)
        self.values[2, 0] = 0
        x = features(self.values, self.times, np.array([11]), 6, self.ids, self.mapping)
        self.assertEqual(x[0, 28], 0)

    def test_future_values_cannot_change_features(self):
        before = features(self.values, self.times, np.array([20]), 12, self.ids, self.mapping)
        self.values[21:] = 99999
        after = features(self.values, self.times, np.array([20]), 12, self.ids, self.mapping)
        np.testing.assert_array_equal(before, after)
        for h in [3, 6, 12]:
            x = features(self.values, self.times, np.array([20]), h, self.ids, self.mapping)
            self.assertEqual(x[0, 2], 20 + h)
            np.testing.assert_array_equal(x[:, 3:], before[:, 3:])

    def test_training_only_mapping_and_unknown_sensor(self):
        self.values[:60, 1] = 0
        mapping = sensor_mapping(self.ids, self.values, self.times, str(self.times[60]))
        self.assertEqual(mapping, {"b": 0})
        self.values[60:] = 999
        self.assertEqual(sensor_mapping(self.ids, self.values, self.times, str(self.times[60])), mapping)
        with self.assertRaises(ValueError):
            features(self.values, self.times, np.array([11]), 3, self.ids, mapping)

    def test_full_training_rows_alignment_and_purge(self):
        protocol = dict(self.protocol)
        protocol["splits"] = [dict(name="train", start_inclusive=str(self.times[0]), end_exclusive=str(self.times[60]))]
        self.values[14, 0] = 0
        issues = split_issues(protocol, self.times, "train")
        np.testing.assert_array_equal(issues, np.arange(11, 48))
        with tempfile.TemporaryDirectory() as tmp:
            x, y = training_arrays(Path(tmp), protocol, self.ids, self.mapping, self.times, self.values, 3)
            target = self.values[issues + 3].reshape(-1)
            mask = target > 0
            np.testing.assert_array_equal(y, target[mask])
            np.testing.assert_array_equal(x, features(self.values, self.times, issues, 3, self.ids, self.mapping)[mask])
            self.assertEqual(len(y), 73)
            del x, y

    def test_xgboost_fit_save_load_and_metadata_rejection(self):
        x = features(self.values, self.times, np.arange(11, 60), 3, self.ids, self.mapping)
        y = self.values[np.arange(11, 60) + 3].reshape(-1)
        model = regressor(self.protocol)
        model.fit(x, y)
        self.assertTrue(np.isfinite(model.predict(x)).all())
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            save_model(model, directory, 3, self.protocol, self.mapping)
            loaded = load_model(directory, 3, self.protocol, self.mapping)
            np.testing.assert_array_equal(model.predict(x), loaded.predict(x))
            with self.assertRaises(ValueError):
                load_model(directory, 3, self.protocol, {"a": 1, "b": 0})
            path = directory / "xgb-3-metadata.json"
            metadata = json.loads(path.read_text())
            metadata["protocol_hash"] = "wrong"
            path.write_text(json.dumps(metadata))
            with self.assertRaises(ValueError):
                load_model(directory, 3, self.protocol, self.mapping)

    def test_identical_target_mask_and_strata(self):
        target = np.array([[10., 0.], [np.nan, 20.]])
        times = np.array(["2012-03-05T07:00", "2012-03-05T09:00"], dtype="datetime64[m]")
        result = summarize(target, np.array([[12., 999.], [999., 16.]]), times, self.ids)
        self.assertEqual(result["overall"]["count"], 2)
        self.assertEqual(result["overall"]["mae"], 3)
        self.assertEqual(result["peak"]["count"], 1)
        self.assertEqual(result["off_peak"]["count"], 1)
        self.assertEqual(result["coverage"], .5)

    def test_gate_rejects_missing_or_changed_contract_and_marker_exclusive(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            with self.assertRaises(FileNotFoundError):
                verify_gate(directory)
            write_json(directory / "selection.json", {"protocol_hash": "wrong"})
            with self.assertRaises(ValueError):
                verify_gate(directory)
            write_json(directory / "final-started.json", {})
            with self.assertRaises(FileExistsError):
                write_json(directory / "final-started.json", {})


if __name__ == "__main__":
    unittest.main()
