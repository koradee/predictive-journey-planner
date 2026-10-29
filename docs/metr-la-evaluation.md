# METR-LA evaluation record

Stage 8B findings below are preserved as historical evidence. Stage 8C continuation is appended after that record.

# Stage 8B development evaluation

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

# Stage 8C: explicit v2 feature contract

Before any XGBoost training or final-test scoring, Stage 8C created [metr-la-speed-v2](../ml/metr_la_protocol_v2.json) as the user-requested feature clarification. The frozen v1 file remains unchanged. The dataset, target mask, history, horizons, split boundaries, baseline definitions and XGBoost candidate are unchanged. This clarification follows the supplied operators, not a validation-based feature search.

Canonical v2 SHA-256: `96e565e65a074141178678e51b6b0d6c40fcd5650a5da9b1fc9452184fc95676`.

Exactly 32 float32 features, in order:

1. `sensor_id`: native categorical integer code from lexicographically sorted training-observed sensor IDs; unknown sensors rejected.
2. `target_weekday`, `target_slot`: numeric release-clock Monday=0 through Sunday=6 and five-minute slot 0..287 at t+h.
3. `lag_11` through `lag_0`: the 12 readings from t-55 minutes through t, oldest first; invalid readings become NaN.
4. `lag_11_missing` through `lag_0_missing`: corresponding 0/1 missing indicators.
5. `history_mean`, `history_std`, `history_min`, `history_max`, `history_valid_count`: positive finite history only; float64 accumulation, float32 storage; population standard deviation (`ddof=0`). One valid reading gives standard deviation zero. With none, the four speed summaries are NaN and count is zero.

No scaling, interpolation, imputation, clipping, extra features or tuning. Sensor encoding uses XGBoost's native categorical feature type; calendar columns remain numeric. JSON model persistence retains categorical structure; see [official categorical documentation](https://xgboost.readthedocs.io/en/stable/tutorials/categorical.html). Models train sequentially using chunk-built disk-backed arrays containing every valid training target.

The development command must finish all three fits, record validation comparisons, pass the complete Python test suite, and freeze artifact/code hashes and per-horizon selections before the separate final command can run. An exclusive final-start marker prohibits repeated final scoring, even after a failed attempt. No final outcomes may change selections.

## Stage 8C development results and frozen selection

Selections were saved at **2026-10-29T11:57:12.848254+00:00**, after all 36 Python tests passed without skips and before final-test scoring. All three models trained on the full eligible training data. No features, masks, parameters or candidates were retuned.

Selection artifact SHA-256: `baa4dba7ba3d5ccbfdbc1b42d01aa019d13642778ec2b006230ed6d281da07ea`.

| Minutes | Training targets | Validation targets | Persistence MAE / RMSE | Historical average MAE / RMSE | XGBoost MAE / RMSE | Selected |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 15 | 4,607,441 | 657,545 | 3.220535 / 6.021880 | 4.331491 / 8.097692 | 2.892508 / 5.314734 | xgboost |
| 30 | 4,607,439 | 657,540 | 3.820904 / 7.524886 | 4.328140 / 8.091763 | 3.486431 / 6.381196 | xgboost |
| 60 | 4,607,444 | 657,549 | 4.788583 / 9.601362 | 4.319000 / 8.076777 | 4.219314 / 7.452943 | xgboost |

All metrics use native release speed units. XGBoost improves validation MAE over the strongest baseline at all three horizons. All baseline aggregates, per-sensor scores and fallback counts exactly match Stage 8B. The same masks and issue times were used for XGBoost. Lowest validation MAE selected the method; exact ties would have favored persistence, then historical average, then XGBoost. No refit on validation observations occurred.

| Minutes | Array construction seconds | Fit seconds | Validation prediction including features seconds | Process peak working set MiB |
| ---: | ---: | ---: | ---: | ---: |
| 15 | 3.257 | 229.043 | 7.114 | 1896.9 |
| 30 | 3.349 | 262.978 | 7.308 | 1897.4 |
| 60 | 2.686 | 234.533 | 7.315 | 1897.4 |

Memory is the cumulative Windows process peak working set, not a separate per-model allocation estimate; child test-process memory is excluded. Models ran sequentially, single-worker CPU, with about 1.9 GiB peak working set. Temporary training matrices were removed after fitting. No memory/runtime failure or reduced-data training occurred.

## Stage 8C final-test results

One final evaluation began at **2026-10-29T11:58:45.092580+00:00** and completed at **2026-10-29T11:59:20.470556+00:00**. The frozen selection hash was verified before scoring. All selected models remained XGBoost; both baselines were scored in this same final phase, after selections were frozen, for transparent comparison. No model, feature, mask or selection changed after test results were available.

| Minutes | Valid test targets | Coverage | Persistence MAE / RMSE | Historical average MAE / RMSE | Selected XGBoost MAE / RMSE |
| ---: | ---: | ---: | --- | --- | --- |
| 15 | 1,244,834 | 87.880912% | 3.489806 / 6.395693 | 4.188563 / 7.855377 | 3.100979 / 5.615293 |
| 30 | 1,244,816 | 87.879641% | 4.188552 / 8.016618 | 4.188795 / 7.855531 | 3.719889 / 6.694513 |
| 60 | 1,244,780 | 87.877100% | 5.344904 / 10.290940 | 4.189303 / 7.855886 | 4.468847 / 7.781769 |

**The 60-minute XGBoost model did not beat historical average on final-test MAE** (4.468847 versus 4.189303), although its RMSE was slightly lower. Its validation MAE had been better, so the frozen XGBoost selection was retained; no post-test winner switch or tuning occurred. XGBoost beat both baselines on test MAE at 15 and 30 minutes.

All final-test errors are in native release speed units; mph remains a literature convention rather than an HDF-encoded unit. Eligible test cells are 1,416,501 per horizon. Unavailable target rates equal one minus coverage; missing targets were not imputed. Results are descriptive for this fixed split, not uncertainty intervals or independent proof of physical measurement accuracy.

## Stage 8C peak/off-peak and per-sensor results

| Phase | Minutes | Method | Peak count | Peak MAE / RMSE | Off-peak count | Off-peak MAE / RMSE |
| --- | ---: | --- | ---: | --- | ---: | --- |
| validation | 15 | xgboost | 91,211 | 4.554455 / 7.665752 | 566,334 | 2.624843 / 4.830261 |
| validation | 30 | xgboost | 90,598 | 5.824911 / 9.413842 | 566,942 | 3.112740 / 5.750222 |
| validation | 60 | xgboost | 89,379 | 7.606688 / 11.453063 | 568,170 | 3.686445 / 6.606782 |
| test | 15 | persistence | 210,024 | 4.677439 / 8.354576 | 1,034,810 | 3.248765 / 5.919509 |
| test | 15 | historical_average | 210,024 | 6.617996 / 10.681849 | 1,034,810 | 3.695487 / 7.146533 |
| test | 15 | xgboost | 210,024 | 4.457015 / 7.609812 | 1,034,810 | 2.825760 / 5.116437 |
| test | 30 | persistence | 210,024 | 5.950777 / 10.663330 | 1,034,792 | 3.830886 / 7.364211 |
| test | 30 | historical_average | 210,024 | 6.617996 / 10.681849 | 1,034,792 | 3.695758 / 7.146724 |
| test | 30 | xgboost | 210,024 | 5.654096 / 9.264948 | 1,034,792 | 3.327317 / 6.040730 |
| test | 60 | persistence | 210,024 | 7.952974 / 13.816441 | 1,034,756 | 4.815546 / 9.415569 |
| test | 60 | historical_average | 210,024 | 6.617996 / 10.681849 | 1,034,756 | 3.696352 / 7.147166 |
| test | 60 | xgboost | 210,024 | 7.265569 / 11.054015 | 1,034,756 | 3.901197 / 6.931511 |

Validation baseline strata are retained in the Stage 8B table above. All strata use the unchanged release-clock definition, not a claimed confirmed local timezone.

| Phase | Minutes | Method | Sensor MAE min / median / max | Sensor RMSE min / median / max |
| --- | ---: | --- | --- | --- |
| validation | 15 | xgboost | 1.079570 / 2.739354 / 5.473923 | 1.510038 / 4.928591 / 9.980390 |
| validation | 30 | xgboost | 1.123638 / 3.349627 / 7.233234 | 1.567669 / 6.018619 / 12.739151 |
| validation | 60 | xgboost | 1.226066 / 4.017271 / 9.965754 | 1.697535 / 6.983294 / 15.120631 |
| test | 15 | persistence | 1.468084 / 3.204993 / 6.354655 | 2.692567 / 5.972676 / 11.683721 |
| test | 15 | historical_average | 1.216012 / 3.669083 / 12.735459 | 2.161830 / 6.750577 / 19.479174 |
| test | 15 | xgboost | 1.164005 / 2.817450 / 6.095495 | 2.101888 / 5.191143 / 10.527862 |
| test | 30 | persistence | 1.506017 / 3.897145 / 8.063920 | 2.811541 / 7.574388 / 15.476028 |
| test | 30 | historical_average | 1.215686 / 3.669223 / 12.735951 | 2.161536 / 6.750579 / 19.479250 |
| test | 30 | xgboost | 1.221955 / 3.492037 / 8.243256 | 2.135717 / 6.211619 / 13.143908 |
| test | 60 | persistence | 1.560821 / 5.246010 / 11.060827 | 2.875470 / 9.775959 / 19.698769 |
| test | 60 | historical_average | 1.215280 / 3.669208 / 12.737823 | 2.161946 / 6.750738 / 19.479648 |
| test | 60 | xgboost | 1.322249 / 4.310092 / 10.764208 | 2.202717 / 7.217697 / 16.027220 |

Detailed counts and errors for each of the 207 sensors are preserved in the ignored aggregate `validation.json` and `final.json` artifacts. These summaries weight sensors equally; the overall MAE/RMSE weights valid target cells equally.

## Stage 8C artifacts, audit trail and reproduction

Only XGBoost 3.4.1 needed installation. Tested pins in `ml/requirements-forecasting.txt`: numpy 2.5.4, h5py 3.15.1, xgboost 3.4.1, scikit-learn 1.9.1, scipy 1.18.1, joblib 1.6.0, threadpoolctl 3.7.0, narwhals 2.27.1. Python 3.14.7.

Run from the repository root:

```sh
python -m pip install -r ml/requirements-forecasting.txt
python -m unittest discover -s ml -p "test_*.py" -v
python ml/train_metr_la.py develop --run-name stage8c-v2
# Review saved development.md and selection.json; final refuses a changed gate.
python ml/train_metr_la.py final --run-name stage8c-v2
```

The original run directory already exists and cannot be overwritten. A deliberate reproduction needs a new name. Never create a new run merely to bypass a failed final-test attempt or improve results. Training failure preserves evidence; a final failure preserves its exclusive start marker. Gates are safeguards against accidental changes, not cryptographic authentication of untrusted external files. Only locally generated model artifacts should be loaded.

Under ignored `data/processed/stage8c-v2/`:

- `run.json`: source/protocol fingerprints, exact library/Python versions, base Git commit, platform and normalized-source code fingerprints. Code fingerprints hash canonical JSON strings of source text with normalized newlines; artifact fingerprints hash actual bytes.
- `mapping.json`: training-derived sensor mapping; `baselines/`: unchanged training-only baseline contract and statistics.
- `xgb-3.json`, `xgb-6.json`, `xgb-12.json`: 15/30/60-minute model JSON, with matching metadata and full XGBoost configuration files. Model loading verifies model hash, protocol, source hash, feature contract, mapping, parameters, 32 features and 300 boosting rounds. No pickle is loaded.
- `validation.json`, `development.md`, `tests.txt`, `selection.json`: complete development evidence frozen before final scoring.
- `final-started.json`, `final.json`: the single final attempt and aggregate test results. No raw observation rows or per-example prediction exports were committed.

| Horizon minutes | Model SHA-256 |
| ---: | --- |
| 15 | `c390bed02357f473910da34077d94cca9b1156cf63e47670508df5f45dc754b1` |
| 30 | `58843acbfab17bb87fcf3042cf3b5f9bd0acfee4bd882b4d5a7d28e563e8e316` |
| 60 | `e5258c87548fa4d592e1a046e3e435b5315259a8c08f3e0854e202910c5f050c` |

Final aggregate report SHA-256: `7aabe164e93cbac3e92b79720adac1a1f6aa924d6fc2f56205c2afffafb6444a`.

Final prediction times (including feature construction): 15 minutes: 10.753 seconds, 30 minutes: 10.668 seconds, 60 minutes: 10.725 seconds. Final process peak working set: 465.1 MiB.

## Stage 8C verification and remaining limits

- Nine new synthetic-fixture unit tests passed before full-data fitting. Fixtures never enter benchmark training or evaluation.
- All 36 Python tests passed without skips as the development gate, after training and before final scoring. Tests include exact ordering/dtypes, population rolling statistics, all-missing/one-reading windows, horizons, split purge, future-mutation invariance, training-only mappings, masks, model fit/save/load, incompatible metadata, protocol fingerprints and final-marker exclusivity.
- Saved/reloaded models produced exactly equal probe predictions for each real-data horizon. Stage 8B baseline results were reproduced exactly, including per-sensor and fallback summaries.
- Existing METR-LA inspector passed with v2; all nine source files were hash-checked before fitting, during gate tests and before final scoring. V1 protocol stayed byte-for-byte unchanged.
- Python syntax checks, 11 frontend tests, frontend lint, production build and Git whitespace checks passed. No frontend files or backend components were changed by this stage.
- No full experiment retraining for cross-machine determinism, browser testing or live-service latency verification was performed. Timings and memory describe this Windows run only.

The feature ambiguity is resolved and Stage 8C completes the offline benchmark. The original limitations remain: Los Angeles data, no Pune prediction capability; future sensor speeds rather than observed road travel times; native units with mph only a literature convention; unconfirmed source timezone; zero targets masked under author convention; unknown publication latency; unresolved underlying commercial-use rights; no validated multi-day forecasting, road matching, route optimization or production deployment. No routing, backend development or frontend integration was started.
