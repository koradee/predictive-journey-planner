# Traffic data inspection

This directory contains Stage 7 CSV inspection and Stage 8A METR-LA validation tools for **Predictive Journey Planner Using AI for Future Traffic and Route Optimization**. Stage 8B added fitted research baselines; Stage 8C adds the explicit v2 feature contract and a gated XGBoost experiment. See the evaluation record for measured results. There is no API or database.

- [Dataset feasibility and recommendation](../docs/dataset-feasibility.md)
- [ML target, evaluation and routing specification](../docs/ml-problem-specification.md)
- [Acquisition, source hashes and local file layout](../data/README.md)
- [Stage 8A findings, conditional acceptance and frozen protocol](../docs/metr-la-validation.md)

## Requirements

For the Stage 7 CSV inspector, use Python **3.11 or newer**. That inspector uses only the standard library; `requirements.txt` deliberately lists no third-party packages. The separate Stage 8A HDF validator uses NumPy and h5py, pinned in `requirements-metr-la.txt` (Python 3.12+ for the current NumPy pin). These packages were already installed in the validation environment. Stage 8C training dependencies are pinned separately in `requirements-forecasting.txt`; only XGBoost needed installation in the recorded environment.

From the repository root:

```sh
python ml/data_inspection.py --help
python ml/data_inspection.py data/raw/pune-counts-v1/traffic.zip --member traffic/AlankarChowk/a2/a2_11.csv --collection-month 2023-01
```

Supported inputs: UTF-8 CSV, `.csv.gz`, and CSV members inside `.zip`. The ZIP is read without extracting files. An omitted `--member` inspects all CSV members; the acquired archive expands to 1.81 GB, so begin with a single member. Non-UTF-8 and unsupported formats fail explicitly. No file contents are executed.

Options:

- `--timestamp-column Time`: require an explicit timestamp field; common names are detected otherwise.
- `--target car`: identify an existing target column; never creates a travel-time label.
- `--collection-month 2023-01`: reconstruct a date only from the verified Pune camera/day filenames. Without this option, time-only values remain undated. Timezone is not inferred from the computer running the script.

The JSON summary reports columns, observed value types, numeric ranges, missing markers, malformed records, duplicates, invalid counts/directions, candidate targets, timestamps, successive time-step distributions by direction, and warnings. Blank physical lines are skipped; delimiter-only records are counted as missing observations. Zero counts remain valid numeric observations. Duplicate-key counts are file-local and do not establish whether repeated values are erroneous or cumulative. Cross-file overlap and coverage must still be investigated.

The inspector does not sort, deduplicate, fill gaps, aggregate, overwrite raw files, or write a training dataset. Reports go to standard output; diagnostics go to standard error. Exit codes: **0** for completed inspection (even when quality warnings exist), **2** for argument, file, format or parsing errors. Review warnings before approving data for modeling. Very large individual files may require a more memory-bounded duplicate audit in a later stage; sets of row hashes and timestamp keys are held in memory per file.

## Verification

```sh
python -m py_compile ml/data_inspection.py
python ml/data_inspection.py --help
```

A nonexistent path, unsupported extension, empty CSV, absent target, invalid collection month or missing ZIP member must return code 2. Successful Stage 7 inspection used real downloaded observations from three source members; no fabricated success fixture was generated. Published report hashes allow source integrity verification before and after running the inspector. HDF5 benchmark inspection is explicitly deferred.

## Stage 8A: METR-LA HDF validation

Acquire the authentic files using the [data instructions](../data/README.md). On a new environment, install only the inspection dependencies if absent:

```sh
python -m pip install -r ml/requirements-metr-la.txt
python ml/inspect_metr_la.py data/raw/metr-la/metr-la.h5 --sensor-ids data/raw/metr-la/graph_sensor_ids.txt --locations data/raw/metr-la/graph_sensor_locations.csv --distances data/raw/metr-la/distances_la_2012.csv --protocol ml/metr_la_protocol.json --output data/processed/metr-la-quality.json
python -m unittest discover -s ml -p test_inspect_metr_la.py -v
```

The validator checks HDF structure, numeric readings, timestamp grid, zero/nonfinite patterns and outage runs by sensor, sensor/location alignment, distance metadata, and frozen split/label coverage. It reads HDF arrays directly without pandas/PyTables or pickle deserialization. It never trains, imputes, modifies raw inputs or computes model accuracy. It loads the roughly 57 MB matrix into memory; it is specific to the documented author fixed-frame layout rather than a generic HDF converter.

Omit `--output` to print JSON; supplied output must be outside raw/source directories and cannot overwrite an input. Exit 0 means integrity validation succeeded; missing inputs/arguments return 2 and format/integrity failures return 3. [The evaluation protocol](metr_la_protocol.json) remains conditional on measurement-use terms and explicit unit/clock qualifications. The generated full quality report is ignored. On a fresh checkout without raw files, integration tests explicitly skip; download data before claiming a successful validation run.

Frontend checks remain in `frontend/`: `npm test`, `npm run lint`, `npm run build`. See the feasibility and Stage 8A reports for unresolved data limitations before attempting any training.

## Stage 8B: development baselines (historical partial stage)

See [the evaluation report and blocker](../docs/metr-la-evaluation.md) for actual validation results, provenance, scope limitations and required next steps. `forecasting.py` implements persistence, training-only historical averages, masked metrics and validated non-pickle artifact loading. `evaluate_metr_la.py` revalidates all source hashes and the frozen protocol before fitting; it exposes validation only and never scores final test targets.

```sh
python -m unittest discover -s ml -p "test_*.py" -v
python ml/evaluate_metr_la.py --run-name stage8b-baselines
```

Run names must be new: existing artifacts are not overwritten. Artifacts and detailed aggregate reports remain ignored under `data/processed/<run-name>/`. No new dependencies are needed beyond `requirements-metr-la.txt`. At the end of Stage 8B, XGBoost fitting was blocked because v1 did not enumerate rolling-summary operators; no feature set was invented or final method selected in that stage. This is an offline Los Angeles sensor-speed benchmark, not Pune prediction or routing functionality.

## Stage 8C: v2 XGBoost development and gated final evaluation

The user-specified v2 contract resolves the rolling-feature ambiguity without changing v1. Read [the evaluation record](../docs/metr-la-evaluation.md#stage-8c-explicit-v2-feature-contract) and [the exact protocol](metr_la_protocol_v2.json) before reproducing.

```sh
python -m pip install -r ml/requirements-forecasting.txt
python -m unittest discover -s ml -p "test_*.py" -v
python ml/train_metr_la.py develop --run-name stage8c-v2
# Only after development finishes and selection.json is frozen:
python ml/train_metr_la.py final --run-name stage8c-v2
```

Use a new run name only for a deliberate reproduction; development never overwrites a run. The final command refuses changed code, protocol, dependencies or artifacts and creates an exclusive attempt marker before scoring. A failed final attempt must be investigated and documented, not silently retried. Final performance must never influence tuning or selection.

`xgboost_forecasting.py` implements the 32 ordered features, native categorical sensor encoding, chunked arrays, JSON model loading and metrics. `train_metr_la.py` fits three full-data direct regressors sequentially, compares validation MAE, runs the full Python test suite and saves the selection before allowing final evaluation. All artifacts remain ignored under `data/processed/<run-name>/`, including per-sensor scores, runtime/configuration metadata and model JSON. No pickle deserialization is used. Dependencies are pinned; native floating-point results may still vary across platforms.

This remains an offline Los Angeles sensor-speed benchmark. Native units, unknown source timezone/publication latency, unavailable zero targets and unresolved measurement-use rights remain explicit. There is no Pune prediction, routing, backend or frontend integration.
