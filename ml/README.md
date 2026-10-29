# Traffic data inspection

This directory contains Stage 7 read-only inspection tools for **Predictive Journey Planner Using AI for Future Traffic and Route Optimization**. There is no trained model, preprocessing pipeline, API or database.

- [Dataset feasibility and recommendation](../docs/dataset-feasibility.md)
- [ML target, evaluation and routing specification](../docs/ml-problem-specification.md)
- [Acquisition, source hashes and local file layout](../data/README.md)

## Requirements

Python **3.11 or newer**. The inspector uses only the standard library; no package installation or virtual environment is required. `requirements.txt` deliberately lists no third-party packages. XGBoost is a proposed later baseline, not an installed dependency.

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

Frontend checks remain in `frontend/`: `npm test`, `npm run lint`, `npm run build`. See the feasibility report for the unresolved measurement/aggregation issues before attempting any training.
