# GND QLever Setup — Troubleshooting Log

Status: **index build in progress** (as of 2026-03-17)

Script: `scripts/setup_gnd_qlever.sh`

---

## Pipeline

1. **JSON-LD → N-Triples**: `scripts/jsonld_to_nt.py` (rdflib, runs on host)
2. **Index build**: `qlever index` inside `adfreiburg/qlever` Docker container
3. **Server**: `qlever start` inside same container, kept alive with `wait`

Source files: `data/gnd/authorities-gnd-*.jsonld.gz`
Index dir: `qlever-gnd-index/` (NT files under `nt/`, Qleverfile, binary index)

---

## Issues encountered

### 1. Fuseki HTTP GSP: OOM on JSON-LD upload
Fuseki's GSP endpoint (`PUT /dataset/data`) buffers the entire JSON-LD document in the JVM heap before parsing. The werk file (96 MB compressed, ~500 MB uncompressed) causes `Java heap space` with HTTP 500. `--data-binary` also OOMs curl before it even reaches Fuseki. Switching to `-T` (streaming) avoided the curl OOM but not Fuseki's.

**Resolution**: abandoned Fuseki, switched to QLever.

### 2. Jena `riot` Docker: OOM on JSON-LD conversion
`stain/jena riot --out=NT` also OOMs on the werk file — same root cause: the Titanium JSON-LD parser (`com.apicatalog.jsonld`) loads the entire document into memory.

**Resolution**: replaced with `jsonld_to_nt.py` using Python `rdflib`, which runs on the host with full RAM access (~2 GB peak for werk).

### 3. `adfreiburg/qlever`: bash 3.2 on macOS
Initial script used `declare -A` (associative arrays), which requires bash 4+. macOS ships with bash 3.2.

**Resolution**: replaced with `case` statement.

### 4. QLever container: `groupmod: GID '20' already exists`
Passing `-e GID=$(id -g)` fails on macOS because GID 20 (`staff`) already exists in the container as `dialout`.

**Resolution**: use `-u $(id -u):$(id -g)` instead of `-e UID/GID`. Causes a harmless `whoami: cannot find name for user ID 502` warning but does not affect execution.

### 5. `qlever index`: `--index-basename` not a valid CLI argument
The index basename is set via the Qleverfile `name` field in `[DEFAULT]`, not via CLI.

**Resolution**: write a minimal Qleverfile with `name = gnd` before invoking the container.

### 6. `qlever index`: requires both `--input-files` AND `--cat-input-files`
`--input-files` alone does not satisfy the required `CAT_INPUT_FILES` argument. Both must be passed:
```
--input-files 'nt/werk.nt' --cat-input-files 'cat nt/werk.nt'
```

### 7. `qlever index`: Docker-in-Docker — `docker: command not found`
With `system = docker` (the default), `qlever index` tries to spawn a new Docker container from inside the running container. Docker is not available inside the container.

**Resolution**: add `[runtime]\nsystem = native` to the Qleverfile. This causes qlever to run `qlever-index` directly as a subprocess.

---

## Current Qleverfile (written dynamically by script)

```ini
[DEFAULT]
name = gnd

[runtime]
system = native
```

## Working `qlever index` invocation

```bash
docker run --rm \
    -u "$(id -u):$(id -g)" \
    -v "${INDEX_DIR}:/data" \
    -w /data \
    adfreiburg/qlever \
    -c "qlever index --input-files 'nt/werk.nt' --cat-input-files 'cat nt/werk.nt'"
```

---

## Next: start server

`qlever start` will hit the same Docker-in-Docker issue — Qleverfile `system = native` should fix it. Command:
```bash
docker run -d --name gemea-qlever-gnd \
    -v "${INDEX_DIR}:/data" -p 7001:7001 -w /data \
    adfreiburg/qlever \
    -c "qlever start --port 7001 --num-threads 8 --memory-for-queries 4096M && wait"
```

SPARQL endpoint (once running): `http://localhost:7001`
