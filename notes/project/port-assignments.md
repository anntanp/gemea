# GeMeA — Port Assignments

**Date**: 2026-04-18

---

## Canonical port map

| Service | Port |
|---------|------|
| SHMARQL EDM (26M objects) | **42003** |
| QLever EDM (26M objects) | **42004** |
| MCPO EDM | **42005** |
| QLever GND (werk + person + koerperschaft) | **42006** |

goethe-faust (PoC, 115K records) — unchanged: QLever 7030, SHMARQL 7032, MCPO 8001.

---

## Files to update

| File | Change |
|------|--------|
| `docker-compose.qlever-gnd.yml` | `7020` → `42006`; internal port `7019` stays |
| `scripts/sh/setup-gnd-werk-qlever-mcp.sh` | `7020` → `42006` |
| `scripts/sh/setup_gnd_qlever.sh` | `7001` → `42006`; fix `jsonld_to_nt.py` path bug (`$SCRIPT_DIR` → `$SCRIPT_DIR/../utils`) |
| New `docker-compose.yml` (EDM stack) | QLever `42004`, SHMARQL `42003`, MCPO `42005` |
| `notes/project/entity-linking-plan.md` | Update port references |
| `notes/project/roadmap-revised.md` | Update port references |

---

## Context

- Fuseki (port 3030) is stale — not included.
- goethe-faust is the mocho PoC reference implementation (115K DDB records).
- GeMeA replicates the same service stack (QLever + SHMARQL + MCPO) at 26M object scale.
- GND QLever consolidates Werk + Person + CorporateBody into one instance (42006), replacing both `docker-compose.qlever-gnd.yml` (was 7020) and `setup_gnd_qlever.sh` (was 7001).
