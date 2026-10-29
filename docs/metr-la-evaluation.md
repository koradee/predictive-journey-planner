# METR-LA Stage 8B development evaluation

Project: **Predictive Journey Planner Using AI for Future Traffic and Route Optimization**

## Status and scope decision

**Partial; XGBoost and final-test evaluation blocked.** Persistence and training-only historical averages were fitted and evaluated on the authentic full validation period. No observations were subsampled. No XGBoost model, final model selection, final-test prediction or performance score exists.

The Stage 8B request explicitly authorizes an offline research benchmark with qualified native units and release-clock semantics. That is the scope decision for this baseline run; it does not resolve measurement-use rights or authorize commercial deployment.

## Feature-contract blocker

The frozen `metr-la-speed-v1` feature list requires "causal rolling statistics over that history only" but does not enumerate the statistics. Stage 8A prose likewise says "causal history summaries"; the earlier Stage 7 proposal mentions rolling means but does not define the complete frozen summary set. Choosing mean alone versus mean/standard deviation/minimum/maximum produces different XGBoost features and results. Standard-deviation degrees of freedom and all-missing summary behavior would also need specification if that statistic is included.

The task expressly says to stop affected evaluation rather than invent an interpretation of an important protocol ambiguity. Therefore XGBoost feature construction, fitting and scoring are stopped. No dependency was installed for an experiment that cannot yet honor its frozen feature contract. Specify the summary operators, windows, minimum observation counts and all-missing behavior in a versioned pre-evaluation clarification before continuing. The original protocol and its fingerprint are unchanged. The fully specified baseline work is independent of this blocker.

## Provenance and reproducibility

Authentic author-distributed METR-LA, 34,272 timestamps x 207 Los Angeles sensors; see [Stage 8A provenance](metr-la-validation.md) and [source manifest](../data/metr-la-manifest.json). All nine source files were checked against their byte counts and hashes before fitting and again by the integration tests afterward. No raw source was modified.

- Dataset SHA-256: `64784b76d6fb8ec9bff4b6decafb354da2bb37840468fdccee5044e511277c05`
- Canonical protocol SHA-256: `474f3ad531bb3b70476ecd3f6e42d13b04efb09f4b057d76266b49510d7d8144`
- Base repository commit: `c6d1a186184acf01d89635a7d75a0f6e450df6d2` (new implementation file hashes are recorded in local artifact metadata).
- Recorded training UTC timestamp: `2026-10-29T11:12:24.894325+00:00`.
- Runtime versions: python 3.14.7, numpy 2.5.4, h5py 3.15.1.
- End-to-end baseline run elapsed: 3.451 seconds; peak memory was not instrumented. No runtime/memory failure occurred.

## Splits and leakage controls

| Split | Start inclusive | End exclusive | Eligible issue ticks |
| --- | --- | --- | ---: |
| train | 2012-03-01T00:00:00 | 2012-05-23T07:10:00 | 23967 |
| validation | 2012-05-23T07:10:00 | 2012-06-04T04:45:00 | 3415 |
| test | 2012-06-04T04:45:00 | 2012-06-28T00:00:00 | 6843 |

All times are native, unlocalized release-clock timestamps. Every issue has 12 available historical ticks ending at t; t+60 minutes remains strictly before its split end. All horizons use the same issue times. Prior-period lag context is allowed, but no observation after t enters persistence. Targets are positive finite readings at t+h; zeros and nonfinite targets are excluded identically for both methods. Targets are never filled. No random split or global normalization is used.

Persistence selects the latest positive finite value in the 12-tick window, falling back to training sensor median then global training median. Historical averages use only the 23,990 training timestamps, grouped by sensor/target weekday/five-minute slot, then sensor/weekday/hour, sensor median and global median. The sensor ordering comes from the verified training matrix; it is checked on artifact reload. These tables never update on validation or test observations.

## Validation results

MAE and RMSE are in **native release speed units**. mph is a literature convention, not encoded in the HDF. Every horizon has 706,905 eligible sensor/issue cells.

| Minutes | Valid targets | Coverage | Persistence MAE | RMSE | Historical average MAE | RMSE | Best baseline only |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 15 | 657,545 | 93.017449% | 3.220535 | 6.021880 | 4.331491 | 8.097692 | persistence |
| 30 | 657,540 | 93.016742% | 3.820904 | 7.524886 | 4.328140 | 8.091763 | persistence |
| 60 | 657,549 | 93.018015% | 4.788583 | 9.601362 | 4.319000 | 8.076777 | historical_average |

**XGBoost comparison: not evaluated.** Its improvement over the best baseline is unknown. **Final selected method: none for all three horizons.** The all-candidate validation and feature-contract gates have not passed, so final-test scoring remains prohibited, including baseline test comparisons.

| Minutes | Method | MAE minus best baseline | Peak count | Peak MAE / RMSE | Off-peak count | Off-peak MAE / RMSE |
| ---: | --- | ---: | ---: | --- | ---: | --- |
| 15 | persistence | 0.000000 | 91,211 | 4.661393 / 8.299919 | 566,334 | 2.988477 / 5.568529 |
| 15 | historical_average | 1.110956 | 91,211 | 7.982781 / 12.708132 | 566,334 | 3.743432 / 7.079799 |
| 30 | persistence | 0.000000 | 90,598 | 5.805929 / 10.440119 | 566,942 | 3.503694 / 6.946566 |
| 30 | historical_average | 0.507236 | 90,598 | 7.992193 / 12.719096 | 566,942 | 3.742620 / 7.077286 |
| 60 | persistence | 0.469583 | 89,379 | 7.692447 / 13.532613 | 568,170 | 4.331775 / 8.824936 |
| 60 | historical_average | 0.000000 | 89,379 | 8.001522 / 12.730171 | 568,170 | 3.739701 / 7.071285 |

Peak means release-clock Monday-Friday 07:00-09:00 or 16:00-19:00, half-open. Off-peak is its complement; these are not verified civil Los Angeles peak hours.

## Fallbacks and missingness

Validation unavailable target rates are 1 minus the coverage above. Fallback percentages below use valid scored targets as denominator; the reproducible local report also records counts over all eligible cells.

| Minutes | Method | Scored fallback counts and rates |
| ---: | --- | --- |
| 15 | persistence | latest: 655,309 (99.659947%); sensor_median: 2,236 (0.340053%); global_median: 0 (0.000000%) |
| 15 | historical_average | slot: 657,545 (100.000000%); hour: 0 (0.000000%); sensor_median: 0 (0.000000%); global_median: 0 (0.000000%) |
| 30 | persistence | latest: 653,424 (99.374030%); sensor_median: 4,116 (0.625970%); global_median: 0 (0.000000%) |
| 30 | historical_average | slot: 657,540 (100.000000%); hour: 0 (0.000000%); sensor_median: 0 (0.000000%); global_median: 0 (0.000000%) |
| 60 | persistence | latest: 650,625 (98.946999%); sensor_median: 6,924 (1.053001%); global_median: 0 (0.000000%) |
| 60 | historical_average | slot: 657,549 (100.000000%); hour: 0 (0.000000%); sensor_median: 0 (0.000000%); global_median: 0 (0.000000%) |

## Per-sensor summaries

All 207 sensor summaries (count, MAE, RMSE) per method/horizon are saved in ignored `data/processed/stage8b-baselines/validation.json`, reproducible with the command below. The following aggregates give equal weight to sensors, unlike the overall cell-weighted metrics.

| Minutes | Method | Sensor MAE min / median / max | Sensor RMSE min / median / max | Largest-MAE sensor |
| ---: | --- | --- | --- | --- |
| 15 | persistence | 1.367174 / 3.140149 / 6.193526 | 1.993336 / 5.659039 / 10.871260 | 718496 |
| 15 | historical_average | 1.142440 / 3.986925 / 10.733681 | 1.593199 / 7.317668 / 16.426344 | 717468 |
| 30 | persistence | 1.380839 / 3.699563 / 7.220168 | 1.981144 / 7.051458 / 14.578309 | 718045 |
| 30 | historical_average | 1.144721 / 3.987472 / 10.712852 | 1.596548 / 7.318510 / 16.419706 | 717468 |
| 60 | persistence | 1.411695 / 4.725345 / 9.916096 | 2.015356 / 9.203442 / 19.416951 | 717468 |
| 60 | historical_average | 1.148271 / 3.933136 / 10.671084 | 1.602272 / 7.318770 / 16.400853 | 717468 |

## Artifacts and reproduction

Run from the repository root after acquiring Stage 8A sources:

```sh
python -m pip install -r ml/requirements-metr-la.txt
python -m unittest discover -s ml -p "test_*.py" -v
python ml/evaluate_metr_la.py --run-name stage8b-baselines
```

The runner refuses to overwrite an existing run. Use a new run name for a deliberate validation reproduction; there is no test-split switch. Artifacts are stored under ignored `data/processed/<run-name>/`: `baselines.npz`, `metadata.json`, and aggregate `validation.json`. Loading checks the source/protocol fingerprints, sensor order, archive hash, array shapes and valid fallback/table values. NumPy loading explicitly disables pickle. Hashes detect accidental modification; they do not authenticate arbitrary externally supplied artifacts. Only locally generated artifacts should be loaded.

Pinned existing NumPy/h5py requirements suffice. No XGBoost package or model is claimed. Its frozen candidate remains 300 trees, depth 4, learning rate 0.05, full row/column sampling, L2 1, histogram method, seed 42, one worker, squared-error objective, separate direct horizons, no early stopping. No tuning has occurred.

## Verification

- 27 Python unit/integration tests passed without skips: 13 baseline tests plus 14 existing authentic-data inspector tests.
- Tests cover source/protocol mismatch, boundaries/horizon alignment, target masks, causal persistence, training-only tables, all fallback levels, metrics, calendar handling, sensor ordering, saved prediction parity, artifact corruption and development/test separation.
- Synthetic observations appear only in explicitly labeled unit fixtures; reported results use genuine METR-LA measurements.
- Python syntax compilation, full existing METR-LA inspector CLI, 11 frontend tests, frontend lint and production build passed.
- Git whitespace checks passed. Existing unrelated staged/unstaged frontend and root documentation changes are preserved.
- XGBoost feature ordering, XGBoost persistence, full candidate selection and final-test performance are unverified because their implementation/evaluation is blocked. Browser interaction was not rerun; no frontend files were modified by Stage 8B.

## Limitations and Stage 9 recommendation

Data is from Los Angeles, not Pune. Predictions concern future sensor-speed values, not measured road travel times. Units are native release speed units; mph is a literature convention, not encoded in the HDF. Source timestamps have no confirmed timezone. Zero targets are unavailable under the author benchmark convention. Observation publication latency remains unknown. Underlying measurement commercial-use rights remain unresolved. This benchmark does not establish multi-day forecasting or real route optimization. No backend, frontend prediction integration or commercial assets were created.

**Do not advance to Stage 9 model integration yet.** First resolve and version the rolling-feature contract, implement and test that fixed XGBoost candidate, record validation comparisons and freeze the full selection before a single documented final-test evaluation. Do not use the baseline results to choose a favorable rolling-feature interpretation. Retain the same splits/masks and record any protocol clarification before XGBoost evaluation.
