# GeMeA — Entity Linking Plan (Bare-Minimum, No Fine-Tuning)

**Date**: 2026-04-18
**Context**: Bare-minimum ISWC 2026 submission; entity linking must be feasible before May 7 without training a custom model.

---

## 1. Constraints

- **NuNER Zero**: evaluated 2026-03-27 (SR-09) — FAIL. F1 = 0.000 all labels. Root cause: token classifier trained on English newswire; no concept of ISBD bibliographic field segmentation. Not viable.
- **GLiNER**: same zero-shot paradigm, same failure mode on this domain. Not worth trying.
- **Fine-tuning xlm-roberta-base**: confirmed path per SR-09, but requires full SR-08 gold annotation pipeline → out of scope.

---

## 2. GND QLever Infrastructure

Two parallel setups exist (both kept):

| Setup | Port | Index dir | NT dir | Multi-type | JSON-LD conversion |
|-------|------|-----------|--------|------------|--------------------|
| `setup_gnd_qlever.sh` | 7001 | `qlever-gnd-index/` | `qlever-gnd-index/nt/` | Yes (`--load`) | Yes (built-in) |
| `docker-compose.qlever-gnd.yml` | 7020 | `data/gnd/qlever-index/` | `data/gnd/nt/` | No (hardcoded `werk.nt`) | No |

**Source files** (`data/gnd/`):

| File | Type |
|------|------|
| `authorities-gnd-werk_lds.jsonld.gz` | GND Werk |
| `authorities-gnd-person_lds_20260217.jsonld.gz` | Person |
| `authorities-gnd-koerperschaft_lds.jsonld.gz` | CorporateBody |
| `authorities-gnd-kongress_lds.jsonld.gz` | Congress |
| `authorities-gnd-geografikum_lds.jsonld.gz` | Geographic entity |
| `authorities-gnd-sachbegriff_lds.jsonld.gz` | Subject concept |
| `authorities-gnd_entityfacts.jsonld.gz` | EntityFacts |

**Bug in `setup_gnd_qlever.sh`** — `convert_to_nt()` references wrong path:

```bash
# current (broken)
python3 "$SCRIPT_DIR/jsonld_to_nt.py" "$gz_path" "$nt_path"

# fixed
python3 "$SCRIPT_DIR/../utils/jsonld_to_nt.py" "$gz_path" "$nt_path"
```

**To load Werk + Person + CorporateBody into one QLever instance (after fix):**

```bash
./scripts/sh/setup_gnd_qlever.sh --load werk,person,koerperschaft --rebuild
# SPARQL endpoint: http://localhost:7001
```

With Person + CorporateBody loaded, lobid-gnd API is no longer needed for agent linking.

---

## 3. Entity Linking Pipeline (Option A — Recommended)

| Component | Method | Endpoint | Coverage | Effort |
|-----------|--------|----------|----------|--------|
| Title extraction | ISBD rule-based parser (already built) | — | ~28% of CHOs | zero |
| GND Werk lookup | SPARQL Pattern C | local GND QLever (`localhost:7001` or `7020`) | covers ISBD-extracted titles | `link_gnd_works.py` Steps 1+3–6 |
| Agent linking | SPARQL against local GND QLever | `localhost:7001` (after adding `person,koerperschaft`) | agents with name labels | `link_gnd_agents.py` |

**Skip Step 2 (NER fallback) in `link_gnd_works.py` entirely.**
**Change SPARQL target** from `sparql.dnb.de` to `localhost:7001`.

### 3.1 What to report in the paper

- X% of CHOs linked to GND Werk URI (rule-based ISBD path)
- Y% of agents linked to GND Person/CorporateBody authority
- Coverage is partial by design — state honestly as rule-based baseline
- NER-augmented path → v1.1

### 3.2 Optional: raw dc:title pass (Option C)

Run a parallel pass with raw normalized `dc:title` (no extraction) → DNB SPARQL. Covers 100% of CHOs at lower precision. Evaluate precision on a 200-record sample. Report comparison vs. ISBD-extracted titles. Costs < 1 day.

---

## 4. Alternatives Considered

| Option | Method | Why not chosen |
|--------|--------|---------------|
| B — LLM API on subset | Claude/GPT-4o batch title extraction | Adds API cost + prompt engineering; entity linking is not the main contribution |
| C — Raw dc:title | Skip extraction, query GND directly | Lower precision; viable as supplementary pass |

---

## 5. Bug Fix — File to Edit

`gemea/scripts/sh/setup_gnd_qlever.sh` — one line in `convert_to_nt()`:

```bash
# old
python3 "$SCRIPT_DIR/jsonld_to_nt.py" "$gz_path" "$nt_path"
# new
python3 "$SCRIPT_DIR/../utils/jsonld_to_nt.py" "$gz_path" "$nt_path"
```
