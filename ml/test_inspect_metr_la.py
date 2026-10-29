"""Validation tests using local authentic data and explicitly corrupted test copies.

No observations are fabricated for model training. Download sources first; tests
skip clearly when the private raw files are absent from a fresh checkout.
"""

import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import h5py
import numpy as np

from inspect_metr_la import check_timestamps, inspect, inspect_metadata, read_hdf, sha256


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "metr-la"


class MetrLaValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        names = ["metr-la.h5", "graph_sensor_ids.txt", "graph_sensor_locations.csv", "distances_la_2012.csv"]
        if not all((RAW / name).is_file() for name in names):
            raise unittest.SkipTest("Authentic METR-LA data/metadata absent; follow acquisition instructions")
        cls.ids, cls.times, cls.values, *_ = read_hdf(RAW / "metr-la.h5")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="metr-la-test-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def inspect_path(self, path, **changes):
        options = dict(ids_path=RAW / "graph_sensor_ids.txt", locations_path=RAW / "graph_sensor_locations.csv", distances_path=RAW / "distances_la_2012.csv")
        options.update(changes)
        return inspect(path, **options)

    def write_copy(self, mutate=None):
        path = self.directory / "numeric-test-copy.h5"
        values = self.values[:24].copy()
        if mutate:
            mutate(values)
        with h5py.File(path, "w") as handle:
            handle.create_dataset("df/axis0", data=np.array(self.ids, dtype="S6"))
            handle.create_dataset("df/block0_items", data=np.array(self.ids, dtype="S6"))
            index = handle.create_dataset("df/axis1", data=self.times[:24].astype("int64"))
            index.attrs["kind"] = np.bytes_("datetime64")
            handle.create_dataset("df/block0_values", data=values)
        return path

    def test_authentic_release_and_frozen_protocol(self):
        report = self.inspect_path(RAW / "metr-la.h5", protocol_path=ROOT / "ml" / "metr_la_protocol.json")
        self.assertEqual(report["shape"], [34272, 207])
        self.assertEqual(report["values"]["zero_count"], 575302)
        self.assertEqual(report["values"]["valid_positive_finite_count"], 6519002)
        self.assertEqual(report["timestamps"]["duplicate_timestamps"], 0)
        self.assertEqual(report["timezone_attributes"], [])
        self.assertEqual(report["unit_attributes"], [])
        self.assertEqual(len(report["per_sensor"]), 207)
        self.assertEqual([s["timestamps"] for s in report["protocol"]["splits"]], [23990, 3427, 6855])
        for split in report["protocol"]["splits"]:
            self.assertLess(np.datetime64(split["last_issue"]) + np.timedelta64(60, "m"), np.datetime64(split["end_exclusive"]))
            self.assertEqual(set(split["label_coverage_by_horizon_minutes"]), {"15", "30", "60"})

    def test_all_source_hashes_remain_unchanged(self):
        manifest = json.loads((ROOT / "data" / "metr-la-manifest.json").read_text())
        for item in manifest["files"]:
            self.assertEqual((RAW / item["filename"]).stat().st_size, item["bytes"])
            self.assertEqual(sha256(RAW / item["filename"]), item["sha256"])

    def test_missing_file_cli(self):
        result = self.cli(self.directory / "absent.h5")
        self.assertEqual(result.returncode, 2)
        self.assertIn("not found", result.stderr)

    def test_missing_metadata_cli(self):
        result = self.cli(RAW / "metr-la.h5", ids=self.directory / "absent-ids.txt")
        self.assertEqual(result.returncode, 2)
        self.assertIn("not found", result.stderr)

    def cli(self, path, ids=None):
        return subprocess.run([sys.executable, str(ROOT / "ml" / "inspect_metr_la.py"), str(path), "--sensor-ids", str(ids or RAW / "graph_sensor_ids.txt"), "--locations", str(RAW / "graph_sensor_locations.csv"), "--distances", str(RAW / "distances_la_2012.csv")], capture_output=True, text=True)

    def test_corrupt_file_cli(self):
        path = self.directory / "corrupt.h5"
        path.write_bytes(b"deliberately invalid HDF test file")
        result = self.cli(path)
        self.assertEqual(result.returncode, 3)
        self.assertIn("HDF5", result.stderr)

    def test_report_cannot_overwrite_source(self):
        command = [sys.executable, str(ROOT / "ml" / "inspect_metr_la.py"), str(RAW / "metr-la.h5"), "--sensor-ids", str(RAW / "graph_sensor_ids.txt"), "--locations", str(RAW / "graph_sensor_locations.csv"), "--distances", str(RAW / "distances_la_2012.csv"), "--output", str(RAW / "metr-la.h5")]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("must not overwrite", result.stderr)

    def test_wrong_hdf_layout(self):
        path = self.directory / "wrong-layout.h5"
        with h5py.File(path, "w"):
            pass
        with self.assertRaisesRegex(ValueError, "layout"):
            read_hdf(path)

    def test_axis_order_mismatch(self):
        path = self.write_copy()
        with h5py.File(path, "r+") as handle:
            handle["df/block0_items"][0] = b"999999"
        with self.assertRaisesRegex(ValueError, "order mismatch"):
            read_hdf(path)

    def test_sensor_id_mismatch(self):
        path = self.directory / "mismatched-ids.txt"
        ids = list(self.ids)
        ids[0], ids[1] = ids[1], ids[0]
        path.write_text(",".join(ids))
        with self.assertRaisesRegex(ValueError, "exact order"):
            inspect_metadata(self.ids, path, RAW / "graph_sensor_locations.csv", RAW / "distances_la_2012.csv")

    def test_duplicate_location_ids_and_invalid_coordinates(self):
        with (RAW / "graph_sensor_locations.csv").open(newline="") as stream:
            reader = csv.DictReader(stream)
            fields, rows = reader.fieldnames, list(reader)
        for defect in ["duplicate", "invalid-coordinate"]:
            changed = [dict(row) for row in rows]
            if defect == "duplicate":
                changed[0]["sensor_id"] = changed[1]["sensor_id"]
            else:
                changed[0]["latitude"] = "nan"
            path = self.directory / f"{defect}.csv"
            with path.open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(changed)
            with self.assertRaises(ValueError):
                inspect_metadata(self.ids, RAW / "graph_sensor_ids.txt", path, RAW / "distances_la_2012.csv")

    def test_duplicate_reverse_missing_and_nat_timestamps(self):
        for defect in ["duplicate", "reverse", "gap", "nat"]:
            times = self.times[:24].copy()
            if defect == "duplicate":
                times[1] = times[0]
            elif defect == "reverse":
                times = times[::-1]
            elif defect == "gap":
                times[1:] += np.timedelta64(5, "m")
            else:
                times[0] = np.datetime64("NaT", "ns")
            with self.assertRaises(ValueError, msg=defect):
                check_timestamps(times)

    def test_missingness_reporting_on_explicitly_corrupted_copy(self):
        def mutate(values):
            values[0, 0], values[1, 0], values[2, 0] = 0, np.nan, np.inf
        report = self.inspect_path(self.write_copy(mutate))
        self.assertEqual(report["values"]["nan_count"], 1)
        self.assertEqual(report["values"]["infinite_count"], 1)
        self.assertGreaterEqual(report["per_sensor"][0]["unavailable_count"], 3)
        self.assertFalse(report["interpretation"]["training_performed"])

    def test_negative_values_require_review(self):
        def mutate(values):
            values[0, 0] = -1
        with self.assertRaisesRegex(ValueError, "Negative"):
            self.inspect_path(self.write_copy(mutate))

    def test_frozen_hash_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "hash or dimensions"):
            self.inspect_path(self.write_copy(), protocol_path=ROOT / "ml" / "metr_la_protocol.json")


if __name__ == "__main__":
    unittest.main()
