# METR-LA acquisition, validation and frozen evaluation

Project: **Predictive Journey Planner Using AI for Future Traffic and Route Optimization**

Stage 8A decision, **29 October 2026: CONDITIONAL**. Authentic source data and sensor metadata were acquired and inspected successfully. Technical integrity supports a short-horizon, native-unit speed benchmark. Underlying measurement-use rights, provider-confirmed units, timezone and observation-publication semantics remain unresolved. No model was trained, baseline scored, backend implemented or UI changed.

## 1. Provenance and acquisition

Preferred source: [the original DCRNN repository](https://github.com/liyaguang/DCRNN), pinned to revision **602afd9d767d3aa1c9b3eac51710d6aeee12c227**. Its [Data Preparation instructions](https://github.com/liyaguang/DCRNN/blob/602afd9d767d3aa1c9b3eac51710d6aeee12c227/README.md#data-preparation) link to the [author's Google Drive folder](https://drive.google.com/open?id=10FOTa6HXPqX8Pf5WRoRwcFnW9BrNZEIX). That folder lists `metr-la.h5`, file ID `1pAGRfzMx6K9WWsfDcD1NMbIif0T0saFC`. Its public [download endpoint](https://drive.google.com/uc?export=download&id=1pAGRfzMx6K9WWsfDcD1NMbIif0T0saFC) returned the binary directly without credentials. No mirror was used.

HDF file size: **57,038,056 bytes**. SHA-256:

```text
64784b76d6fb8ec9bff4b6decafb354da2bb37840468fdccee5044e511277c05
```

[The manifest](../data/metr-la-manifest.json) records exact pinned URLs, byte sizes and hashes for the HDF, sensor ID list, sensor coordinates, distances, original README/license, and source code used to check the author's masking convention. All downloads are under ignored `data/raw/metr-la/`. Source code was inspected as text, not executed. Serialized frequency attributes and adjacency pickles were not deserialized.

## 2. Verified file-level results

The following values were calculated from the downloaded file, not copied from a paper or mirror description.

| Check | Verified result |
| --- | --- |
| Container | HDF5, pandas fixed frame in `/df` |
| Values | `/df/block0_values`, `float64`, shape **34,272 x 207** |
| Sensor axes | `/df/axis0` and `/df/block0_items`, matching 207 fixed-string IDs |
| Timestamp axis | `/df/axis1`, integer nanoseconds in pandas datetime64 layout |
| First / last timestamp, inclusive | **2012-03-01 00:00:00 / 2012-06-27 23:55:00** |
| Cadence | Every successive difference is exactly **300 seconds** |
| Duplicate / invalid timestamps | **0 / 0** |
| Missing timestamp-grid slots | **0** |
| Total measurement cells | **7,094,304** |
| Positive finite cells | **6,519,002** |
| Zero cells | **575,302 (8.10935%)** |
| NaN / infinity / negative values | **0 / 0 / 0** |
| Observed finite range | **0 to 70**, in native release speed units |
| Values over 100 native units (diagnostic screen only) | **0** |
| Timestamps with all 207 sensors unavailable | **2,148** |

The release ends on **27 June**, not the nominal end-of-June range often quoted for the study. The positive-cell count agrees with the original paper's stated observed-value total, supporting consistency with the author distribution. This is not independent certification of each measurement.

A complete time grid does **not** imply complete traffic observations. The longest simultaneous unavailable run is **381 five-minute ticks**, from 26 March 08:25 to 27 March 16:05, inclusive. Sensor `717490` has a longest unavailable run of **1,683 ticks**, from 5 June 12:25 to 11 June 08:35. Durations here count unavailable five-minute bins; the elapsed difference between first and last timestamp is one bin shorter.

Each sensor has between **2,148 and 6,890 zero entries** (6.2675% to 20.1039% unavailable). Per-sensor counts, fractions and run details are in the locally generated `data/processed/metr-la-quality.json`. The report is ignored and reproducible using the commands below; raw measurement arrays and generated artifacts are not committed.

## 3. Units, zeros and clock interpretation

**Verified author convention:** the [pinned supervisor](https://github.com/liyaguang/DCRNN/blob/602afd9d767d3aa1c9b3eac51710d6aeee12c227/model/dcrnn_supervisor.py) sets `null_val=0` for loss/evaluation. The [baseline implementation](https://github.com/liyaguang/DCRNN/blob/602afd9d767d3aa1c9b3eac51710d6aeee12c227/scripts/eval_baseline_methods.py) also masks zero labels. Therefore this protocol treats nonfinite and nonpositive targets as unavailable. It does not assert that every zero is physically a sensor fault, and never interprets unknown zeros as stopped traffic. Targets are not filled or interpolated.

**Units:** no speed-unit attribute was found in the HDF. Later [published benchmark work](https://www.nature.com/articles/s41598-025-32795-0) describes mph, but this is supporting literature, not a units certificate for this binary. Keep all values on the native scale and label results **native release speed units (mph convention)** until provider confirmation. Do not infer units from the numerical range, convert units silently, or treat a speed value as a measured segment travel time. The upper range of 70 is observed, not proof of a physical limit or a known clipping policy. The release contains no per-reading quality flags or verified curation/imputation history; the physical accuracy of positive values was not independently established.

**Timezone:** no timezone attribute was found. The regular naive clock spans the US spring DST transition without a missing/duplicated clock hour; it does not establish UTC, civil Pacific time, or fixed standard time. No localization or DST correction is applied. Day/hour features and peak strata use the **release clock**, explicitly qualified. Aggregation start/end labeling and observation-release latency are also unknown. Offline forecasting assumes the reading indexed `t` has become available before an issue at `t`; no real-time service availability is claimed.

## 4. Sensor and distance integrity

All **207** HDF IDs match the ID-list file in exact order and the coordinate file by ID. The coordinate file also has the same order. There are no duplicate sensor IDs, missing/invalid coordinates, or identical coordinate pairs. Latitude spans **34.04301 to 34.22164**; longitude **-118.5368 to -118.1829**. These coordinates are consistent with Los Angeles, not Pune.

The distance CSV has **295,374 directed pairs** over **4,106 distinct endpoints**; **11,753 pairs** have both endpoints in the selected 207 sensors. All selected sensors occur in that subset. No duplicate directed pairs, nonfinite costs or negative costs were found. Its extra IDs are expected broader-network metadata, not evidence of 4,106 speed-matrix columns. Cost units are not encoded or converted.

There is enough location information to start a **later Los Angeles map-matching pilot**, but not to certify routing. A pilot still needs dated road geometry, driving direction, ramps/road levels, access/turn rules, sensor-to-directed-edge crosswalks and edge-length validation. Pairwise distances are not road edges, do not provide turn geometry, and should not be used as speed-derived journey durations. No OSM matching was performed.

## 5. Frozen protocol: metr-la-speed-v1

[Machine-readable configuration](../ml/metr_la_protocol.json), frozen before any model fitting or performance evaluation. It is bound to the source hash and dimensions above. Its canonical-JSON SHA-256 is:

```text
474f3ad531bb3b70476ecd3f6e42d13b04efb09f4b057d76266b49510d7d8144
```

Canonical JSON uses sorted keys, compact separators, UTF-8 and no NaN values, so the protocol fingerprint does not change with Windows versus Unix line endings. Protocol changes require a new version and a reason independent of final test performance.

### Global chronological periods

All sensors share the same boundaries in the **native naive release clock**. Intervals are start-inclusive and end-exclusive.

| Period | Start | End exclusive | Timestamp count |
| --- | --- | --- | ---: |
| Training | 2012-03-01 00:00 | 2012-05-23 07:10 | 23,990 |
| Validation | 2012-05-23 07:10 | 2012-06-04 04:45 | 3,427 |
| Final test | 2012-06-04 04:45 | 2012-06-28 00:00 | 6,855 |

These boundaries use floor(70% x 34,272) and floor(80% x 34,272) on the timestamp axis, not shuffled rows or the author's pre-generated overlapping sample splits. They are not selected for model performance.

### Issue times, labels and leakage controls

- Predict the **sensor speed at timestamp `t+h`**, for **15, 30 and 60 minutes** (3, 6 and 12 ticks). One row is `(sensor ID, issue tick t, horizon h)`.
- Use the last **12 readings ending at `t`** (offsets -11 through 0); this spans 55 minutes between endpoints. All readings must already be released under the offline availability assumption. Real deployment would require verified latency.
- Purge the last **12 possible issue ticks** before each split's end for every horizon. Every retained issue satisfies `t+60 minutes < split end`. This yields **23,967 / 3,415 / 6,843** issue timestamps for training/validation/test respectively. The training start also discards the first 11 ticks for history. Validation/test may use prior-period readings as already available lag context.
- Retain NaN plus explicit feature-missing masks; compute causal rolling summaries from positive finite history only. No centered windows, future interpolation/backfill, target encodings from validation/test, or actual future weather. Fit any imputation fallback, categorical mapping or normalization on training only.
- Include sensor identity, release-clock target weekday/five-minute slot, 12 historical readings/masks and causal history summaries. Exclude weather, incidents and road attributes until legitimately sourced with availability timestamps.
- Mask unavailable targets identically for every model; never manufacture labels. Report target coverage and fallback usage. Finite negative readings are a source-integrity failure, not silently clipped.

Coverage inspection is not model evaluation. For the frozen final test period, there are **1,416,501 eligible sensor/issue cells per horizon**. Valid positive targets number **1,244,834 / 1,244,816 / 1,244,780** at 15/30/60 minutes. Do not use those quality counts to tune a model or alter the split.

### Baselines and candidate, not executed

1. **Persistence:** latest positive finite reading within the 12-step history. If none exists, use the training sensor median, then the global training median; disclose fallback rates.
2. **Historical average:** training-only mean by sensor, target weekday and five-minute slot. Fall back to sensor/weekday/hour mean, sensor median, global training median. Freeze the table; do not update it from validation/test targets.
3. **XGBoost candidate:** separate direct regressor per horizon; squared-error objective, 300 trees, depth 4, learning rate 0.05, subsample/column sample 1.0, L2 1.0, histogram method, seed 42, one worker, no early stopping for this first candidate. No tuning or XGBoost installation occurred here. Later tuning may use validation only and must finish before final test scoring.

Report **MAE and RMSE** in native speed units per horizon, overall and per sensor. MAPE is not a primary metric. Use identical issue/target masks for fair comparisons. Peak strata are fixed as release-clock Monday-Friday **07:00-09:00** and **16:00-19:00**, half-open windows, with off-peak as the complement. These are benchmark strata, not verified local LA peak periods. Record eligible counts; avoid claims based on tiny strata. Any uncertainty estimate should respect day/session blocks rather than assume independent sensor ticks.

Record source/metadata hashes, canonical protocol hash, code commit, Python/NumPy/h5py versions, future training-package versions, feature contract, seed and missingness decisions. The final test remains unused for fitting, selection and performance evaluation; Stage 8A examined integrity/missingness only. No MAE, RMSE or accuracy result is claimed.

### Supported scope

The grid supports the proposed short horizons numerically, with substantial unavailable periods that must be masked. A future calendar date days ahead cannot use recent readings from that future departure. Such forecasting needs a separate seasonal/calendar-only evaluation, with no claim that a 60-minute benchmark establishes multi-day reliability. Sensor-speed evaluation does not establish route ranking or end-to-end travel-time accuracy.

## 6. Reproduction and tests

From the repository root, use the acquired source paths:

```sh
python -m py_compile ml/inspect_metr_la.py ml/test_inspect_metr_la.py
python ml/inspect_metr_la.py data/raw/metr-la/metr-la.h5 --sensor-ids data/raw/metr-la/graph_sensor_ids.txt --locations data/raw/metr-la/graph_sensor_locations.csv --distances data/raw/metr-la/distances_la_2012.csv --protocol ml/metr_la_protocol.json --output data/processed/metr-la-quality.json
python -m unittest discover -s ml -p test_inspect_metr_la.py -v
```

The HDF validator uses NumPy and h5py already available in this environment; no package installation was needed. Tested versions are Python **3.14.7**, NumPy **2.5.4**, h5py **3.15.1**. Pinned inspection dependencies are in `ml/requirements-metr-la.txt`; this NumPy pin requires Python 3.12+. The Stage 7 standard-library CSV inspector and requirements remain unchanged.

Tests cover the authentic release, source hashes, frozen split eligibility, missing/corrupt files, unsupported HDF layout, mismatched HDF axes, sensor-ID mismatch, missing metadata, duplicate location IDs, invalid coordinates, duplicate/reversed/gapped/NaT timestamps, negative speeds, nonfinite/zero reporting and protocol hash mismatch. Defect tests use temporary, explicitly altered copies of actual observations or invalid structural fixtures; they are not training data or successful acquisition substitutes. Source hashes are checked after testing.

The validator's output distinguishes masked values from physical explanations. It does not deserialize pandas frequency pickles, generate samples, impute observations, fit a model or compute performance metrics. Reports cannot overwrite inputs or be written inside raw/source directories. CLI exit 0 means file integrity checks succeeded, not that all acceptance gates are cleared. Missing inputs/arguments return 2; format/integrity errors return 3. Tests skip explicitly on a fresh checkout without private raw data; no skipped run should be reported as successful data validation.

Executed on 29 October 2026: Python syntax compilation, the full authentic-file validator including report output, and all **14 validation tests** passed without skips. Source checksums were rechecked after testing. Existing frontend tests (**11**), lint and production build passed; Git whitespace checks passed. No model-performance metrics were computed.

## 7. Rights and acceptance gate

The author distribution is publicly accessible and requests research citation. The repository MIT license concerns the published repository material; it does not by itself establish all upstream measurement permissions. No separate measurement license, production-use approval or commercial redistribution grant was established. Raw speeds, metadata source files, cached author code and generated reports stay ignored; only provenance, code, protocol and written aggregate findings are committed. Confirm provider terms before training, deployment or sharing measurement files. No provider was contacted and no rights approval is implied.

| Gate | Result |
| --- | --- |
| Authentic author-source HDF acquired and inspected | PASS |
| Provenance, hashes and known rights limits documented | PASS; rights unresolved |
| Timestamp and sensor integrity evaluated | PASS |
| Target defined | PASS: future native-unit sensor speed, not road travel time |
| Physical units/timezone independently established | CONDITIONAL: no encoded units/timezone; no silent assumptions |
| Chronological evaluation frozen | PASS; no scoring or training |
| No Pune prediction claim | PASS |

**Stage 8A is CONDITIONAL, not full modeling or deployment readiness.** Stage 8B can use this as a technical specification, but should not begin training until measurement-use terms and the qualified unit/clock policy are resolved and recorded. Obtain provider confirmation where possible; if unresolved, retain the native-unit/naive-clock limitations explicitly and make a documented scope decision before training. A genuine Pune model remains blocked on Pune measurements and a validated road crosswalk. Stop here; no Stage 8B execution has occurred.
