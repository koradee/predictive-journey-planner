# Data acquisition and provenance

Stage 7 keeps real source files local and unmodified. `raw/` and `processed/` are ignored by `data/.gitignore`; generated statistics are not cleaned training data. The committed manifests contain metadata and quality summaries, not traffic measurements.

## Acquired Pune count dataset

Source: [Mendeley Data version 1](https://data.mendeley.com/datasets/xnf2k6n288/1), DOI **10.17632/xnf2k6n288.1**, Matange and Abraham (2026). License as published: **CC BY 4.0**. Preserve attribution, the publication URL and a record of modifications when using this data.

Download `traffic.zip`, `README.docx` and `data_dictionary.csv` from that version's Files list. Public file downloads worked without credentials on 29 October 2026. The [source manifest](source-manifest.json) records verified direct URLs, byte lengths and SHA-256 hashes. Do not rely on an unversioned mirror or generate replacement observations.

Expected local layout, from the repository root:

```text
data/
  source-manifest.json
  inspection-summary.json
  raw/
    pune-counts-v1/
      traffic.zip
      README.docx
      data_dictionary.csv
  processed/
    # Local inspection output only; no training dataset has been created.
```

Create directories if needed; a fresh clone does not contain ignored folders:

```sh
python -c "from pathlib import Path; Path('data/raw/pune-counts-v1').mkdir(parents=True, exist_ok=True); Path('data/processed').mkdir(parents=True, exist_ok=True)"
```

After downloading, verify **all three** files against the manifest without changing them:

```sh
python -c "from pathlib import Path; import hashlib,json; m=json.loads(Path('data/source-manifest.json').read_text()); base=Path('data/raw/pune-counts-v1'); assert all((base/f['filename']).stat().st_size==f['bytes'] and hashlib.sha256((base/f['filename']).read_bytes()).hexdigest()==f['sha256'] for f in m['files']); print('Source sizes and SHA-256 hashes verified')"
```

The ZIP is approximately 15.6 MB compressed but its CSV members total **1.81 GB uncompressed**. Avoid extracting everything just to inspect a sample. List member names using the standard library:

```sh
python -m zipfile -l data/raw/pune-counts-v1/traffic.zip
python ml/data_inspection.py data/raw/pune-counts-v1/traffic.zip --member traffic/AlankarChowk/a2/a2_11.csv --collection-month 2023-01
```

`--collection-month 2023-01` explicitly applies the provider's camera/day filename convention; the CSV itself contains only time-of-day. `_one` files are described as session continuations. Confirm overlaps and date rollover before combining them. Do not assume five-minute windows: the inspected files have repeated second-level timestamps. [Feasibility findings](../docs/dataset-feasibility.md) and the [machine-readable summary](inspection-summary.json) document this blocker.

The three fully inspected members are listed in `inspection-summary.json`. All other archive members were inventoried, not scanned for row quality. Rerun the inspector for each selected member to reproduce its report. Omitting `--member` scans every CSV member and can take substantially longer. Raw source files must retain their original hashes after inspection.

## Conditional benchmark acquisition: METR-LA / PEMS-BAY

Use the [original DCRNN Data Preparation section](https://github.com/liyaguang/DCRNN#data-preparation) and its author-linked Google Drive or Baidu distribution. Download `metr-la.h5` first; optionally acquire `pems-bay.h5` for a second geography. Public web links exist, but actual binary download access was **not tested** here; Google/Baidu may impose authentication or quotas. Direct [Caltrans PeMS](https://pems.dot.ca.gov/) archive access requires an approved account.

Before modeling, confirm source measurement-use rights; repository MIT code licensing does not by itself license every upstream measurement. Record version, bytes and SHA-256 in a separate benchmark manifest, and inspect timestamps, sensor count, units, missing-value encoding and quality masks. Preserve corresponding [sensor metadata](https://github.com/liyaguang/DCRNN/tree/master/data/sensor_graph) and row/column order. Review untrusted serialization before loading; do not execute arbitrary pickle files.

Use a distinct local directory such as `data/raw/metr-la/`. Do not rename California observations as Pune data. These HDF5 files were not downloaded or inspected, and the Stage 7 **CSV/ZIP inspector does not support HDF5**. Stage 8 must add a deliberate HDF5 reader, with only the dependencies it needs, after dataset access and scope are confirmed.

## Pune travel-time acquisition request

Request authorized historical directed segment speeds or measured traversal durations from Pune's data custodian, traffic authority, or a licensed provider. Include date range and timezone, sampling/aggregation rules, sensor coordinates, camera orientation, segment endpoints/direction, length, units, coverage, quality/missingness flags, data latency and ML/storage/redistribution rights. Ask for multiple weeks/months, not only citywide annual averages. No request was sent and no account or commercial purchase was made in Stage 7.

For geometry, use a dated [Geofabrik India/Western Zone extract](https://download.geofabrik.de/asia/india.html) or a bounded OSM query, following [OSM licensing](https://www.openstreetmap.org/copyright) and service policies. Avoid downloading a national extract unless needed. Geometry downloads were not performed in Stage 7. Road matching requires validation; OSM road tags do not supply measured traffic labels.
