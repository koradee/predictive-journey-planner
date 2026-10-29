# Traffic dataset feasibility

Project: **Predictive Journey Planner Using AI for Future Traffic and Route Optimization**

Research and inspection date: **29 October 2026**. This is a data decision, not a model evaluation. No backend, model, or predictive UI was implemented.

## Decision

**A Pune road-segment travel-time model is not currently justified by the acquired data.** A licensed local count dataset was acquired and inspected, but has no measured speeds, travel times, road lengths, or segment coordinates. Its temporal semantics also need clarification. This does not prove that suitable Pune data does not exist; it means it was not established in this research.

Select the Pune dataset for **read-only data-quality investigation only**. Recommend **METR-LA as the first conditional speed-forecasting benchmark**, with a Los Angeles road network if routing is later added. Obtain and inspect its actual data and resolve measurement-use terms before modeling. PEMS-BAY is a second benchmark, not Pune training data. Neither benchmark validates Pune predictions.

## Candidate comparison

| Candidate | Evidence available | Actual label | Pune segment travel-time suitability | Decision |
| --- | --- | --- | --- | --- |
| Pune heterogeneous traffic counts v1 | Publication, dictionary, README and ZIP; three CSV members inspected | Vehicle counts, with unresolved aggregation semantics | Insufficient | Local quality investigation only |
| METR-LA | Original paper, authors' repository and sensor locations | Highway sensor speed | No geographic transfer claim | Recommended conditional benchmark |
| PEMS-BAY | Original paper, authors' repository and Caltrans portal | Highway sensor speed | No geographic transfer claim | Secondary benchmark |
| OpenStreetMap / Geofabrik India | Official map license and extract listing | Road geometry and attributes, not measured traffic | Geometry can support Pune routing, not training labels | Geometry source only |
| Smart Cities / OGD India | Official catalogue; live page retrieval timed out | No suitable Pune measurement resource verified | Unresolved | Acquisition lead only |
| TomTom Traffic Stats / Pune Index | Provider pages | Historical analytics / city aggregates | Segment exports require access and terms | Commercial acquisition lead |
| TraffiCure Pune tool | Provider's public tool | Displayed hourly speed summaries | No licensed raw historical export verified | Acquisition lead, not a training dataset |

## Dataset dossiers

### 1. Heterogeneous Traffic Count Dataset, Pune (Jan 2023)

[Original publication](https://data.mendeley.com/datasets/xnf2k6n288/1), DOI **10.17632/xnf2k6n288.1**, Ashwini Matange and Jibi Abraham; published 23 July 2026. Geography: Alankar, Jehangir and RTO junctions, Pune. Collection dates are stated as 11?18 January 2023; the description also says seven days, so continuous coverage must not be assumed. Version 1 is labeled **CC BY 4.0**; retain attribution and identify any modifications.

The publication describes approximately five-minute directional counts from CCTV processing. The dictionary defines `Time`, `Direction`, `car`, `motorbike`, `bus`, `truck`. Camera IDs and collection days are encoded in CSV filenames; these are not OSM segment IDs. Format: CSVs in ZIP, with CSV dictionary and DOCX README. Complete dataset row count is not published or counted here. Candidate target: future vehicle count only, pending verified interval semantics. No direct travel-time prediction; geographic junction matching requires camera coordinates, orientation, and approach mapping that were not found in the inspected schema.

### 2. METR-LA

[Original paper](https://arxiv.org/html/1707.01926v3) and [authors' download instructions](https://github.com/liyaguang/DCRNN#data-preparation). Geography: Los Angeles highways, 207 sensors; published collection span March?June 2012. Paper reports **6,519,002 observed values**, not CSV rows. Native format: `metr-la.h5`, timestamp-indexed sensor speed matrix. Target: future sensor speed; five-minute aggregation supports short horizons, with published experiments at 15, 30 and 60 minutes. Inputs include sensor ID, time and prior speed.

[Sensor coordinates](https://github.com/liyaguang/DCRNN/blob/master/data/sensor_graph/graph_sensor_locations.csv) allow candidate matching to **Los Angeles** OSM roads, subject to direction, ramps, dated geometry and coverage checks. No direct Pune matching. Missing speed observations need an explicit mask; do not assume zero is a stopped vehicle or a missing value without checking the release convention. The repository is MIT-licensed; this alone does not establish measurement redistribution rights. HDF data were not downloaded or inspected in Stage 7.

### 3. PEMS-BAY

Same [original study](https://arxiv.org/html/1707.01926v3) and [author distribution](https://github.com/liyaguang/DCRNN#data-preparation), originating from [Caltrans PeMS](https://pems.dot.ca.gov/). Geography: California Bay Area, 325 sensors. Published dates: January?May 2017; paper reports **16,937,179 observed values**. Format: `pems-bay.h5`, timestamp-indexed sensor speed matrix; five-minute cadence; future speed target. Features: sensor ID, timestamps, historical speed. [Bay sensor coordinates](https://github.com/liyaguang/DCRNN/blob/master/data/sensor_graph/graph_sensor_locations_bay.csv) exist in the author repository.

Missing-value and sensor-quality checks remain unperformed. Matching is potentially possible to Bay Area OSM highways after validation, not to Pune. The paper's prose calls January?May six months; use verified file timestamps rather than that duration wording. For licensing, distinguish repository MIT code from [Caltrans terms](https://pems.dot.ca.gov/?view=tou); portal accounts are required for direct archive access. Suitable for an independent speed benchmark; no route-level accuracy claim. Data were not downloaded here.

### 4. OpenStreetMap road-network data

[Official license](https://www.openstreetmap.org/copyright), [India extract](https://download.geofabrik.de/asia/india.html). Coverage includes Pune; extracts change over time, so record snapshot date. Number of road records depends on the chosen boundary and snapshot; none counted here. Features may include coordinates, way/node IDs, highway type, access, lanes, one-way direction and speed-limit tags. Format includes OSM PBF; no regular traffic measurement interval or measured traffic target. Missing tags, outdated roads and turn restrictions require validation. OSM identifiers are native to the road network, but a way ID alone may not identify a directed routing edge. ODbL attribution and applicable share-alike obligations apply. Useful geometry, **not historical speeds**; do not treat `maxspeed` or map-edit timestamps as traffic labels.

### 5. Government portal discovery

[Smart Cities Mission Data Portal](https://smartcities.data.gov.in/) was searched alongside OGD Pune traffic queries. The catalogue advertises Government Open Data License?India, but no specific downloadable Pune historical segment-speed/travel-time resource was verified; direct portal access timed out. Geography, collection dates, row count, temporal resolution, features, target, identifiers and file format of a suitable resource therefore remain **unverified**. No missing-value assessment or OSM match is possible without an identified export. The portal's general license is not evidence that a particular traffic archive is available. Request resource-level metadata from the responsible Pune data custodian.

### 6. TomTom

[Traffic Stats](https://www.tomtom.com/products/traffic-stats/) provides provider-described historical road analytics. [Pune Traffic Index](https://www.tomtom.com/traffic-index/city/pune/) displays city-level travel/speed summaries, including a 2025 reporting period. These pages are not a verified public raw training dataset. Requested export dates, record count, feature schema, cadence, IDs, file format and missingness remain unverified. Speeds/travel times may be suitable labels in an approved segment export, but summary averages cannot substitute for timestamped observations. Access, ML-use rights, storage and redistribution terms require provider confirmation; no purchase or account action was taken. OSM matching would need licensed geometry and a validated crosswalk. Treat as a paid/permissioned Pune acquisition option.

### 7. TraffiCure Pune

The provider's [Pune departure-time tool](https://trafficure.com/tools/best-time-to-leave-pune) displays hourly summaries and states a Pune Traffic Police partnership. That statement was not independently verified. No raw download, underlying collection dates, observation count, detailed feature schema, persistent road IDs, file format, missingness assessment or training/redistribution license was established. Hourly display resolution is not raw sampling cadence. Potential speed target and Pune road matching require an authorized export with geometry, timestamps and provenance. Public display access does not confer training rights. Not selected as a dataset.

## Acquired-file evidence and limitations

Download URLs, byte lengths and SHA-256 hashes are in [the source manifest](../data/source-manifest.json). [Inspection results](../data/inspection-summary.json) are generated from **three complete CSV members**, one per junction; the remaining files were inventoried only. These measurements are our own file inspection, not claims from a dataset summary page.

The 15,582,506-byte ZIP contains **115 CSV members totaling 1,812,118,340 uncompressed bytes**. It was not extracted in full. Observed schema has six columns and no coordinates, speeds, travel times, distance or OSM IDs.

| Inspected member | Rows excluding blank physical lines | Exact duplicate rows | Missing values in each column | Unique time-of-day values |
| --- | ---: | ---: | ---: | ---: |
| `a2_11.csv` | 877,100 | 840,756 | 1,880 | 8,753 |
| `j3_16_one.csv` | 184,500 | 176,101 | 12 | 1,845 |
| `r1_18_one.csv` | 177,560 | 169,320 | 44 | 1,930 |

Across these files, positive successive time steps within a direction are **one second**, with many zero-second repeats. Some repeated time/direction keys contain different count values. Therefore, summing rows, taking arbitrary duplicates, or claiming five-minute independent observations would be unjustified. Counts could reflect repeated/cumulative updates; their meaning must be confirmed with the authors. This is not evidence of 1.24 million independent traffic intervals. No full-archive quality claim is made.

The supplied README explains camera/day filenames and `_one` continuations, but does not resolve the observed repetition. Timestamps lack timezone and full date; January 2023 filename reconstruction is explicit in the inspector. Confirm Asia/Kolkata with the provider before modeling. Published description, README aggregation wording and observed files disagree. No preprocessing was performed.

## Feasibility gates and acquisition decision

For genuine Pune travel-time prediction, obtain directed segment geometries/coordinates, dated timestamped measured speeds or traversal durations, observation/aggregation definitions, units, coverage and missingness flags, and permission for ML use. Aim for multiple weeks/months covering peak/off-peak and different weekdays; no fixed sample count guarantees adequacy. Audit availability latency and any imputed labels. Match each sensor/trajectory to a versioned Pune road graph and validate direction, intersections and segment extent manually on a pilot corridor.

Option A is blocked on those observations. Option B is recommended for defensible model-method research: METR-LA speed forecasting in its actual geography, after acquisition and rights review. Option C may illustrate Pune routing separately with an explicit foreign-data label, but must not produce claims of Pune-trained accuracy or real Pune route recommendations. Geometry-only routing and predictive traffic validation are separate milestones.

**Stage 8 recommendation:** acquire and inspect METR-LA plus its location metadata, resolve measurement-use terms, then approve a chronological speed-forecasting protocol. In parallel, clarify Pune count semantics and request genuine Pune segment measurements. Do not start a Pune travel-time model, backend, or public AI prediction feature on the strength of these counts.
