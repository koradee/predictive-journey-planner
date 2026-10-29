# ML prediction and evaluation specification

Project: **Predictive Journey Planner Using AI for Future Traffic and Route Optimization**

Status: proposed protocol, 29 October 2026. No training, accuracy result or deployed prediction exists. See [dataset feasibility](dataset-feasibility.md) before choosing a target.

## Target depends on the evidence

| Available observations | Defensible target | What must not be claimed |
| --- | --- | --- |
| Directed segment traversal durations with known entry/exit times | Future segment travel time in seconds | Pune capability without matching Pune observations |
| METR-LA / PEMS-BAY sensor speeds | Future speed in verified source units | Directly observed road travel times or Pune accuracy |
| Acquired Pune vehicle counts | Future count in a verified camera/direction/window, only after semantics are resolved | Travel time, speed or validated congestion categories from counts alone |
| OSM road attributes only | No traffic ML target | Speed-limit tags as measured historical speed |

The intended product target remains segment travel time. A speed benchmark is a narrower research milestone, not an equivalent implementation of that product objective.

## One training example

Define issue time `t`, horizon `h`, and target-window convention before feature extraction. One example is `(location_id, issue_time, horizon)` with inputs available by `t` and a measured outcome at `t+h` (or in a declared window starting there). Keep feature timestamps, label start/end and availability times in the provenance table. All IDs refer to a real source location, not an arbitrary Pune road.

For a future travel-time dataset, define whether the label is traversal duration for vehicles entering a directed segment during the target interval, and record aggregation and vehicle population. Compute a duration from verified matched entry/exit timestamps only; account for traversal completion latency. Do not invent these events from vehicle counts.

For METR-LA, model the future five-minute sensor speed value. Initial proposed horizons are 15, 30 and 60 minutes, conditional on actual file cadence and enough history. Use separate direct regressors per horizon as a simple baseline design. For a journey scheduled days ahead, recent observations at that future departure do not exist: use an independently evaluated calendar/historical-profile model or declare the horizon unsupported. Do not reuse short-horizon evaluation to justify arbitrary future dates.

For the Pune count files, do not define a training row yet: second-level repetition and changing values at identical keys must be reconciled first. After provider confirmation, define nonoverlapping count windows, camera/direction identities, session boundaries and completeness rules. Absent windows are unknown, not zero.

## Feature availability contract

| Feature | Evidence and permitted availability |
| --- | --- |
| Location identity | Pune camera from path/filename; benchmark sensor from matrix columns; neither is a road edge without a crosswalk |
| Target hour/day-of-week | Derived from verified target timestamp and source timezone; available at issue time |
| Prior speed/count observations | Only values with source/availability time no later than `t`; account for sensor latency |
| Rolling means and lags | Within the same location/session, using past observations only; never centered windows |
| Historical seasonal profile | Estimate on training data only; freeze or update only with observations already released in a declared rolling evaluation |
| Road class, length, lanes | Optional after a validated, versioned geometry join; not present in the acquired count schema |
| Weather | Omitted initially; future experiments require observations already known or archived forecasts issued by `t` |
| Incidents/holidays | Omitted until an authenticated historical source and availability rule are defined |

Never use target-window speeds, future realized weather, whole-dataset imputation statistics, backward filling from future rows, globally computed target encodings, or future neighbor observations. A feature timestamp before `t` is insufficient if the value was not actually published by `t`. Do not aggregate overlapping primary/continuation files across split boundaries without understanding their semantics.

## Model plan (not implemented)

First evaluate persistence (latest valid observed value) and a training-only location/time-of-week historical average. For long horizons, report the seasonal baseline separately from persistence. Only then compare an XGBoost Regressor using squared-error regression, with bounded hyperparameter search selected on validation MAE. Missingness indicators and an explicit target mask are required; never score imputed targets as observations. Unknown locations require a declared fallback or an unavailable response. [Official XGBoost parameter reference](https://xgboost.readthedocs.io/en/stable/parameter.html).

No XGBoost, pandas, FastAPI or database dependencies are installed for Stage 7. The inspection script uses only Python's standard library.

## Reproducible evaluation

1. Record source version, URL, license, hashes, timestamp/timezone semantics, cadence, duplicates, gaps and label-validity rules. Resolve the Pune data discrepancy before generating labels.
2. Split by **global chronological timestamps across all locations**, not independently shuffled rows. Propose earliest 70% training, next 10% validation, final 20% test for a sufficiently long benchmark. Record exact date boundaries and row/label counts after acquisition. The short Pune collection cannot establish broad seasonal generalization with such fractions alone.
3. Purge examples whose label windows cross a split boundary. The gap must cover the largest forecast horizon plus any target-window/traversal-completion latency. Lag context from before a validation/test issue time is allowed only if operationally available; keep the same rule for every model. Windows may not cross camera recording gaps.
4. Fit imputation, categorical mappings, encoders and any scaling on training data only. Do not normalize using validation/test statistics. Do not interpolate missing labels. Log exclusions and missingness by location/time.
5. Use expanding chronological validation folds inside the development period when coverage permits. [TimeSeriesSplit documentation](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html) explains ordered splits and gaps; its equal-spacing assumptions require deliberate handling of irregular sessions. It is not used in the inspector.
6. Select hyperparameters and early stopping using validation only. Freeze features, quality masks and selection rules before opening the final test set. In a rolling test, consuming observations that would have become available before each issue time is allowed; refitting or selecting models on test outcomes is not.
7. Report **MAE** (`mean(abs(prediction - observed))`) and **RMSE** (`sqrt(mean((prediction - observed)^2))`) in target units, separately for each horizon, overall and per location. Include eligible target counts and coverage. MAPE is secondary only when the denominator is safely nonzero; disclose the threshold, excluded fraction and zero-target treatment. Zero vehicle counts can be valid and should not disappear from MAE/RMSE.
8. Report peak/off-peak performance using local-time windows fixed on training/validation evidence, not chosen after seeing test errors. Compare weekday/weekend only where supported. Use day/session block uncertainty estimates if enough independent periods exist, rather than treating frame repeats as independent samples.
9. Archive data hashes, script revision, split timestamps, feature list, availability cutoffs, package versions, seed, hardware and final parameter settings. Record geographic coverage and distribution shift. No numeric accuracy target or achieved accuracy is asserted now.

## Routing integration requirements (future work)

Routing needs a real directed road graph, legal turns/access rules, and a validated mapping from observation locations to graph edges. Sensor readings at a point do not automatically describe an entire edge or junction delay. Match location, direction, road level/ramp and historical map version; quantify unmapped edges.

Where representative **segment speed and measured segment length** legitimately exist, `seconds = 3600 * length_km / speed_km_per_hour` is only a derived travel-time approximation. Convert source units first. Zero speed requires an explicit unavailable/closure rule; arbitrary clipping must not create claimed measurements. For variable speeds, account for edge-entry times and traversal evolution; intersection delays and turns need their own evidence.

Evaluate candidate routes at successive predicted edge-entry times, not all at the initial departure time. Document time-dependent routing assumptions, nonnegative costs and FIFO behavior or use an algorithm suitable for the chosen cost model. Do not silently substitute an arbitrary speed for unobserved roads. End-to-end arrival-time accuracy requires independent observed journey times; sensor-speed MAE cannot certify route ranking or arrival estimates. The current Pune schematic frontend remains unchanged.

## Stage 8 acceptance gate

Acquire and inspect the actual METR-LA speed matrix, confirm sensor IDs/units/timezone/missing-value conventions and measurement-use terms, then approve frozen splits and baselines. A separate Pune acquisition request should seek timestamped directed segment speeds or traversal durations plus geometry and rights. Resolve count aggregation with the Pune authors before any count preprocessing. Stage 8 should begin only after choosing the supported target and geography; backend implementation is not a substitute for missing labels.
