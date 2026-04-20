# Disk space estimate for full GeMeA load

Measured April 2026. S2 NT files are the only sector already converted; all other sectors are extrapolated.

## 1. DDB EDM (NT files, P02–P08)

| Sector | Objects | NT size (actual / estimated) |
|--------|--------:|-----------------------------:|
| S2 (P02) | 18 M | 156 GB (measured) |
| S1, S3–S7 (P03–P08) | ~8 M | ~70 GB (extrapolated @ 8.7 GB/M) |
| **Total DDB** | **26 M** | **~225 GB** |

## 2. GND (P15–P20)

| File | Compressed | Uncompressed |
|------|----------:|-------------:|
| P15 `werk.nt` | — | 1.5 GB |
| P16 `werk_lds.jsonld.gz` | 85 MB | ~1.4 GB |
| P17 `person_lds.jsonld.gz` | 1.3 GB | ~13 GB |
| P18 `koerperschaft_lds.jsonld.gz` | 205 MB | ~3–4 GB |
| P19 `geografikum_lds.jsonld.gz` | 42 MB | ~0.5 GB |
| P20 `entityfacts_lds.jsonld.gz` | 1.2 GB | ~8–10 GB |
| **Total GND** | **~2.8 GB gz** | **~28–30 GB** |

## 3. QLever index

QLever index is ~30% of uncompressed NT (observed: 463 MB index from 1.5 GB werk.nt).

| Input | NT | Index |
|-------|---:|------:|
| DDB all sectors | ~225 GB | ~68 GB |
| GND all files | ~29 GB | ~9 GB |
| **Total index** | **~254 GB** | **~77 GB** |

## 4. Summary

| Layer | Size |
|-------|-----:|
| DDB NT (all sectors) | ~225 GB |
| GND NT (uncompressed) | ~29 GB |
| QLever index | ~77 GB |
| **Total** | **~330 GB** |
| **Budget (with build headroom)** | **~400 GB** |

Build headroom accounts for intermediate NT conversion files coexisting with the index during build.
