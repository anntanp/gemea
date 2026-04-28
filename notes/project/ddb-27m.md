## 1. DDB ID corpus — 27 M digitalisat objects

**Host**: `ann@ise-d-teach03` (`10.10.4.10`), path `/data/ddb/data/ids/`

### 1.1 Current files (as of 2026-04-28)

Sec_01 and sec_04 were re-fetched on 2026-04-27; the original March files are retained alongside.

| File | Sector | IDs | Size (KB) |
|---|---|---|---|
| `ids_sec_01_digitalisat.txt` | Archive | 3,486,444 | 112,364 |
| `ids_sec_01_digitalisat_20260427.txt` | Archive (re-fetch) | 3,637,488 | 117,224 |
| `ids_sec_02_digitalisat.txt` | Library | 18,570,245 | 598,460 |
| `ids_sec_03_digitalisat.txt` | Monument Preservation | 83,575 | 2,696 |
| `ids_sec_04_digitalisat.txt` | Research | 1,223,929 | 39,444 |
| `ids_sec_04_digitalisat_20260427.txt` | Research (re-fetch) | 1,227,253 | 39,552 |
| `ids_sec_05_digitalisat.txt` | Media Library | 1,799,840 | 58,004 |
| `ids_sec_06_digitalisat.txt` | Museum | 2,011,737 | 64,836 |
| `ids_sec_07_digitalisat.txt` | Others | 89,904 | 2,900 |

The 2026-04-27 re-fetches show corpus growth since March: +151,044 in sec_01, +3,324 in sec_04.

![ID counts per sector on teach03](../images/ddb_ids_sector_counts.png)

### 1.2 Provenance

IDs were fetched from the live DDB Solr API using cursor-based pagination (cursorMark) to bypass the 10,000-row `maxResultWindow` limit. One ID per line. Filter: `sector_fct:<sector>` + `digitalisat:true`.

**Source script**: [`scripts/utils/fetch-ids-by-sector.py`](https://github.com/anntanp/gemea/blob/main/scripts/utils/fetch-ids-by-sector.py)

**API endpoint**: `https://api.deutsche-digitale-bibliothek.de/search/index/search/select`

**Run dates**:
- 2026-03-19: sec_03–07
- 2026-03-23: sec_01–02
- 2026-04-27: sec_01, sec_04 (re-fetch)

**Resume support**: each run writes a `.cursor` state file; deleted on clean completion.
