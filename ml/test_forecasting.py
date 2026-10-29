"""Synthetic fixtures below are unit tests only, never benchmark training data."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from forecasting import (PROTOCOL_HASH, ROOT, calendar, evaluate_validation, fingerprint, fit_baselines, historical_average, issue_indices, load_baselines, load_verified, metrics, persistence, save_baselines, valid)


class ForecastingTests(unittest.TestCase):
    def setUp(self):
        self.times = np.datetime64("2012-03-01T00:00") + np.arange(120) * np.timedelta64(5, "m")
        self.values = np.tile(np.array([10., 20.]), (120, 1))
        self.end = str(self.times[60])
        self.fitted = fit_baselines(self.times, self.values, self.end)
        self.protocol = dict(history_steps=12, horizons_steps=[3, 6, 12], splits=[dict(name="validation", start_inclusive=str(self.times[60]), end_exclusive=str(self.times[90]))])

    def test_frozen_protocol_fingerprint(self):
        self.assertEqual(fingerprint(json.loads((ROOT / "ml/metr_la_protocol.json").read_text())), PROTOCOL_HASH)
        with patch("forecasting.fingerprint", return_value="wrong"):
            with self.assertRaisesRegex(ValueError, "fingerprint"):
                load_verified()

    def test_source_hash_mismatch(self):
        with patch("forecasting.sha256", return_value="wrong"):
            with self.assertRaisesRegex(ValueError, "hash/size"):
                load_verified()

    def test_boundary_purge_and_horizon_alignment(self):
        issues = issue_indices(self.times, self.protocol["splits"][0])
        np.testing.assert_array_equal(issues, np.arange(60, 78))
        for h in [3, 6, 12]:
            self.assertTrue(np.all(self.times[issues + h] - self.times[issues] == np.timedelta64(5 * h, "m")))
            self.assertTrue(np.all(issues + h < 90))
        train = dict(start_inclusive=str(self.times[0]), end_exclusive=str(self.times[60]))
        self.assertEqual(issue_indices(self.times, train)[0], 11)

    def test_training_only_statistics(self):
        changed = self.values.copy()
        changed[60:] = 9999
        other = fit_baselines(self.times, changed, self.end)
        for key in self.fitted:
            np.testing.assert_array_equal(self.fitted[key], other[key])

    def test_persistence_missing_lags_and_future_independence(self):
        values = self.values.copy()
        values[9, 0] = 33
        values[10:13, 0] = [0, np.nan, np.inf]
        prediction, levels = persistence(values, np.array([12]), self.fitted)
        self.assertEqual(prediction[0, 0], 33)
        self.assertEqual(levels[0, 0], 0)
        values[13:] = 888
        np.testing.assert_array_equal(persistence(values, np.array([12]), self.fitted)[0], prediction)

    def test_persistence_window_and_fallback(self):
        values = self.values.copy()
        values[1:13, 0] = 0
        values[0, 0] = 999
        prediction, levels = persistence(values, np.array([12]), self.fitted)
        self.assertEqual(prediction[0, 0], 10)
        self.assertEqual(levels[0, 0], 1)

    def test_global_fallback(self):
        values = self.values.copy()
        values[:60, 0] = 0
        fitted = fit_baselines(self.times, values, self.end)
        prediction, level = persistence(values, np.array([12]), fitted)
        self.assertEqual(prediction[0, 0], 20)
        self.assertEqual(level[0, 0], 2)
        _, level = historical_average(self.times[60:61], fitted)
        self.assertEqual(level[0, 0], 3)

    def test_historical_mean_and_hour_fallback(self):
        values = self.values.copy()
        values[0, 0] = 0
        fitted = fit_baselines(self.times, values, self.end)
        prediction, level = historical_average(self.times[:2], fitted)
        np.testing.assert_array_equal(prediction[:, 0], [10, 10])
        np.testing.assert_array_equal(level[:, 0], [1, 0])
        prediction, level = historical_average(self.times[:1] + np.timedelta64(1, "D"), fitted)
        self.assertEqual(level[0, 0], 2)
        repeated_times = np.array([self.times[0], self.times[0] + np.timedelta64(7, "D")])
        fitted = fit_baselines(repeated_times, np.array([[10.], [30.]]), str(repeated_times[-1] + np.timedelta64(5, "m")))
        self.assertEqual(historical_average(repeated_times[:1], fitted)[0][0, 0], 20)

    def test_target_mask_and_metrics(self):
        target = np.array([10., 20., 0., np.nan, np.inf])
        prediction = np.array([12., 16., 999., 999., 999.])
        result = metrics(target, prediction, valid(target))
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["mae"], 3)
        self.assertAlmostEqual(result["rmse"], np.sqrt(10))
        self.assertIsNone(metrics(target, prediction, np.zeros(5, dtype=bool))["mae"])
        with self.assertRaises(ValueError):
            metrics(target, prediction, np.ones(5, dtype=bool))
        prediction[0] = np.nan
        with self.assertRaises(ValueError):
            metrics(target, prediction, valid(target))

    def test_calendar_native_clock(self):
        weekday, slot = calendar(np.array(["2012-03-05T07:00", "2012-03-04T16:00"], dtype="datetime64[m]"))
        np.testing.assert_array_equal(weekday, [0, 6])
        np.testing.assert_array_equal(slot, [84, 192])

    def test_validation_no_test_access_and_common_masks(self):
        self.values[90:] = np.nan
        self.values[63, 0] = 0
        report = evaluate_validation(self.protocol, ["a", "b"], self.times, self.values, self.fitted)
        self.assertEqual(report["15"]["valid_targets"], 35)
        for result in report.values():
            for method in result["methods"].values():
                self.assertEqual(method["overall"]["count"], result["valid_targets"])
                self.assertEqual(sum(method["fallback_scored_counts"].values()), result["valid_targets"])
                self.assertEqual(method["peak"]["count"] + method["off_peak"]["count"], result["valid_targets"])
                self.assertEqual(method["overall"]["mae"], 0)
        with self.assertRaises(TypeError):
            evaluate_validation(self.protocol, ["a", "b"], self.times, self.values, self.fitted, split="test")

    def test_saved_predictions_and_corrupted_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / "artifact"
            save_baselines(directory, self.fitted, ["a", "b"], {"source_sha256": "unit-test-source"})
            loaded, _ = load_baselines(directory, ["a", "b"], "unit-test-source")
            np.testing.assert_array_equal(historical_average(self.times[:3], loaded)[0], historical_average(self.times[:3], self.fitted)[0])
            for ids, source in [(["b", "a"], "unit-test-source"), (["a", "b"], "wrong")]:
                with self.assertRaises(ValueError):
                    load_baselines(directory, ids, source)
            path = directory / "metadata.json"
            contract = json.loads(path.read_text())
            contract["protocol_hash"] = "wrong"
            path.write_text(json.dumps(contract))
            with self.assertRaises(ValueError):
                load_baselines(directory, ["a", "b"], "unit-test-source")

    def test_corrupted_arrays(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / "artifact"
            save_baselines(directory, self.fitted, ["a", "b"], {"source_sha256": "fixture"})
            (directory / "baselines.npz").write_bytes(b"corrupt")
            with self.assertRaises(ValueError):
                load_baselines(directory, ["a", "b"], "fixture")


if __name__ == "__main__":
    unittest.main()
