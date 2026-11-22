# Dataset and preparation provenance

John Hogue (2019), Metro Interstate Traffic Volume. UCI Machine Learning Repository.
DOI: https://doi.org/10.24432/C5X60B
Source: https://archive.ics.uci.edu/dataset/492/metro+interstate+traffic+volume
Licence: Creative Commons Attribution 4.0, https://creativecommons.org/licenses/by/4.0/.

The original unmodified compressed CSV was retrieved from UCI on 28 October 2026 for
Part 2 and is reused in `data/Metro_Interstate_Traffic_Volume.csv.gz` for Part 3.
Its SHA-256 is stored under `audit.input_sha256` in `outputs/data_audit.json`.
The prepared hourly table is `data/traffic_hourly.csv`; its cleaning, weather priority,
label convention and chronological partitions are documented in README.md.
The source timestamps remain naive dataset-local times; no timezone conversion is invented.
No real accident dataset or additional route dataset was sourced.
