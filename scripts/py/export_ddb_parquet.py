#!/usr/bin/env python3
from __future__ import annotations
# Purpose:      Re-export only the Parquet metadata from a sector sqlite, skipping NT generation.
#               Use this to rebuild <stem>_meta.parquet after schema changes without re-running
#               the full export_ddb.py pipeline.
# Usage:        python3 export_ddb_parquet.py <sector>.sqlite
# Inputs:       <sector>.sqlite — table objs, column bufgz (gzip-compressed cortex JSON)
# Outputs:      $OUTPUT_DIR/<stem>_meta.parquet
# Dependencies: pyarrow
# Assumptions:  Run from project root; .venv exists

import gzip
import json
import logging
import multiprocessing
import os
import queue
import sqlite3
import sys
import traceback
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

# Re-use schema constants and internal helpers from export_ddb.
sys.path.insert(0, str(Path(__file__).parent))
from export_ddb import (
    PARQUET_SCHEMA,
    REPORT_INTERVAL,
    WORKER_REPORT_INTERVAL,
    LIDO_CREATED,
    LIDO_ISSUED,
    build_about_type_map,
    to_named_node,
    _scalar_values,
    _iter_json,
    _DDB_VOCNET,
    _BARE_ID_RE,
    _is_ext_uri,
    _parse_dc_date,
    _build_concept_labels_map,
    _new_agent_list,
    _timespan_to_date,
)


def extract_meta(data: dict) -> dict:
    """Extract ProvidedCHO metadata for the Parquet row."""
    props     = data.get("properties", {})
    prov_info = data.get("provider-info") or {}
    rdf       = data.get("edm", {}).get("RDF") or {}
    cho       = rdf.get("ProvidedCHO") or {}
    if isinstance(cho, list):
        cho = cho[0] if cho else {}

    events    = rdf.get("Event") or []
    if isinstance(events, dict):
        events = [events]
    timespans = rdf.get("TimeSpan") or []
    if isinstance(timespans, dict):
        timespans = [timespans]
    ts_map = {t["about"]: t for t in timespans if isinstance(t, dict) and t.get("about")}

    concept_labels = _build_concept_labels_map(rdf)

    # -- title + lang_title --
    title_raw  = cho.get("title")
    title_str  = ""
    lang_title = ""
    if isinstance(title_raw, list):
        title_raw = title_raw[0] if title_raw else None
    if isinstance(title_raw, dict):
        title_str  = title_raw.get("$") or ""
        lang_title = title_raw.get("lang") or ""
    elif isinstance(title_raw, str):
        title_str = title_raw

    # -- lang_obj --
    lang_obj_raw = cho.get("language") or cho.get("dcTermsLanguage")
    lang_obj = (_scalar_values(lang_obj_raw) or [""])[0]

    # -- description --
    description = _scalar_values(cho.get("description"))

    # -- dc_type structs --
    dc_type: list[dict] = []
    dc_type_raw = cho.get("dcType") or []
    if not isinstance(dc_type_raw, list):
        dc_type_raw = [dc_type_raw]
    for v in dc_type_raw:
        if isinstance(v, dict):
            lit = v.get("$") or ""
            res = v.get("resource") or ""
            if lit:
                dc_type.append({"name": lit, "is_ext_uri": False})
            elif res and not res.startswith(_DDB_VOCNET) and _is_ext_uri(res):
                label = concept_labels.get(res)
                if label:
                    dc_type.append({"name": label, "is_ext_uri": True})
        elif isinstance(v, str) and v:
            dc_type.append({"name": v, "is_ext_uri": False})

    # -- dc_subject structs --
    dc_subj: list[dict] = []
    for key in ("dcSubject", "dcTermsSubject", "dcTermSubject"):
        items = cho.get(key) or []
        if not isinstance(items, list):
            items = [items]
        for v in items:
            if isinstance(v, dict):
                lit = v.get("$") or ""
                res = v.get("resource") or ""
                if lit:
                    dc_subj.append({"name": lit, "is_ext_uri": False})
                elif res and _is_ext_uri(res) and not res.startswith(_DDB_VOCNET):
                    label = concept_labels.get(res)
                    if label:
                        dc_subj.append({"name": label, "is_ext_uri": True})
            elif isinstance(v, str) and v and not _BARE_ID_RE.match(v):
                dc_subj.append({"name": v, "is_ext_uri": False})

    # -- agents unified --
    lido_agents: list[dict] = []
    hasMet = cho.get("hasMet") or []
    if isinstance(hasMet, dict):
        hasMet = [hasMet]
    event_map = {e["about"]: e for e in events if isinstance(e, dict) and e.get("about")}
    about_type_map = build_about_type_map(rdf)
    for hm in hasMet:
        if not isinstance(hm, dict):
            continue
        ev_ref = hm.get("resource")
        if not ev_ref:
            continue
        ev = event_map.get(ev_ref, {})
        participants = ev.get("P11_had_participant") or []
        if isinstance(participants, dict):
            participants = [participants]
        for p in participants:
            if not isinstance(p, dict):
                continue
            r = p.get("resource") or ""
            lit = p.get("$") or ""
            if r:
                et = about_type_map.get(r, "Agent")
                node = to_named_node(r, et)
                name = lit or (node.value if node else "")
                ext  = _is_ext_uri(r)
                lido_agents.append({"name": name, "type": "unknown_event", "is_ext_uri": ext})

    agents = (
        _new_agent_list(cho.get("creator"),      "creation")
        + _new_agent_list(cho.get("publisher"),  "publication")
        + _new_agent_list(cho.get("contributor"), "contribution")
        + lido_agents
    )

    # -- dates unified --
    dates: list[dict] = []
    dc_date_raw2 = _scalar_values(cho.get("date"))
    if dc_date_raw2:
        normed = _parse_dc_date(dc_date_raw2[0])
        if normed:
            dates.append({"value": normed, "begin": None, "end": None, "type": "unknown_event"})
    for val in _scalar_values(cho.get("created")):
        dates.append({"value": val, "begin": None, "end": None, "type": "creation"})
    for val in _scalar_values(cho.get("issued")):
        dates.append({"value": val, "begin": None, "end": None, "type": "publication"})
    for ev in events:
        if not isinstance(ev, dict):
            continue
        ht = (ev.get("hasType") or {})
        ht_uri = ht.get("resource") if isinstance(ht, dict) else None
        for lido_set, dtype in ((LIDO_CREATED, "creation"), (LIDO_ISSUED, "publication")):
            if ht_uri not in lido_set:
                continue
            oc = ev.get("occuredAt") or ev.get("occurredAt")
            if not oc:
                continue
            ts_ref = oc.get("resource") if isinstance(oc, dict) else oc
            ts = ts_map.get(ts_ref, {}) if isinstance(ts_ref, str) else {}
            d = _timespan_to_date(ts, dtype)
            if d:
                dates.append(d)

    # -- mediatype / sector (int16) --
    mediatype: int | None = None
    sector:    int | None = None
    concepts_list = rdf.get("Concept") or []
    if isinstance(concepts_list, dict):
        concepts_list = [concepts_list]
    for c in concepts_list:
        if not isinstance(c, dict):
            continue
        about = c.get("about") or ""
        if mediatype is None and "/medientyp/mt" in about:
            try:
                mediatype = int(about.rsplit("/mt", 1)[-1])
            except ValueError:
                pass
        if sector is None and "/sparte/sparte" in about:
            try:
                sector = int(about.rsplit("/sparte", 1)[-1])
            except ValueError:
                pass

    # -- hierarchy_type (int16) --
    raw_ht = (_scalar_values(cho.get("hierarchyType")) or [None])[0]
    htype: int | None = None
    if raw_ht:
        try:
            htype = int(raw_ht.replace("htype_", ""))
        except ValueError:
            pass

    return {
        "obj_id":         props.get("item-id", ""),
        "title":          title_str,
        "lang_title":     lang_title,
        "lang_obj":       lang_obj,
        "description":    description,
        "provider_id":    prov_info.get("provider-ddb-id", ""),
        "dataset_id":     props.get("dataset-id", ""),
        "dc_type":        dc_type,
        "agents":         agents,
        "dates":          dates,
        "dc_subject":     dc_subj,
        "hierarchy_type": htype,
        "mediatype":      mediatype,
        "sector":         sector,
        "is_part_of":     bool(cho.get("isPartOf")),
    }

OUTPUT_DIR    = os.environ.get("OUTPUT_DIR", "./out")
MAX_WORKERS   = int(os.environ.get("MAX_WORKERS", max(1, multiprocessing.cpu_count() - 2)))
PARQUET_CHUNK = int(os.environ.get("PARQUET_CHUNK", 500_000))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------

def worker(
    worker_id: int,
    work_q: multiprocessing.Queue,
    meta_q: multiprocessing.Queue,
    compressed: bool = True,
) -> None:
    processed = 0
    batch: list[dict] = []

    def flush():
        if not batch:
            return
        meta_q.put(list(batch))
        batch.clear()

    while True:
        item = work_q.get()
        if item is None:
            flush()
            break
        uid, blob = item
        try:
            data = json.loads(gzip.decompress(blob) if compressed else blob)
            batch.append(extract_meta(data))
            processed += 1
        except Exception:
            traceback.print_exc()
            continue

        if processed % WORKER_REPORT_INTERVAL == 0:
            logging.info(f"Worker {worker_id}: processed {processed:,} records")

        if len(batch) >= 10_000:
            flush()


# ---------------------------------------------------------------------------
# Meta writer
# ---------------------------------------------------------------------------

def meta_writer(meta_q: multiprocessing.Queue, output_path: str) -> None:
    tmp_path = output_path + ".tmp"
    writer = None
    total = 0
    buffer: list[dict] = []

    def flush():
        nonlocal writer, total
        if not buffer:
            return
        arrays = {col: [row.get(col) for row in buffer] for col in PARQUET_SCHEMA.names}
        table = pa.table(arrays, schema=PARQUET_SCHEMA)
        if writer is None:
            writer = pq.ParquetWriter(tmp_path, PARQUET_SCHEMA)
        writer.write_table(table)
        total += len(buffer)
        buffer.clear()

    while True:
        try:
            batch = meta_q.get(timeout=5)
        except queue.Empty:
            continue
        if batch is None:
            break
        buffer.extend(batch)
        if len(buffer) >= PARQUET_CHUNK:
            flush()

    flush()
    if writer:
        writer.close()
        Path(tmp_path).rename(output_path)
        logging.info(f"Parquet writer: {total:,} rows written → {output_path}")
    else:
        logging.warning("Parquet writer: no rows written")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <input.sqlite|input.json>", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    is_json    = Path(input_path).suffix.lower() == ".json"
    compressed = not is_json

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    stem         = Path(input_path).stem
    parquet_path = str(Path(OUTPUT_DIR) / f"{stem}_meta.parquet")

    logging.info(f"Workers: {MAX_WORKERS}")
    logging.info(f"Output: {parquet_path}")

    work_q = multiprocessing.Queue(MAX_WORKERS * 4)
    meta_q = multiprocessing.Queue(1000)

    workers = [
        multiprocessing.Process(target=worker, args=(i, work_q, meta_q, compressed), daemon=True)
        for i in range(MAX_WORKERS)
    ]
    for w in workers:
        w.start()

    writer_proc = multiprocessing.Process(
        target=meta_writer, args=(meta_q, parquet_path), daemon=True
    )
    writer_proc.start()

    count = 0

    if is_json:
        records = list(_iter_json(input_path))
        total   = len(records)
        logging.info(f"Processing {total:,} records from {input_path}")
        for uid, blob in records:
            work_q.put((uid, blob))
            count += 1
            if count % REPORT_INTERVAL == 0:
                logging.info(f"Queued {count:,} / {total:,}")
    else:
        db = sqlite3.connect(input_path)
        cur = db.cursor()
        cur.execute("SELECT max(rowid) FROM objs")
        total = cur.fetchone()[0] or 0
        logging.info(f"Processing ~{total:,} records from {input_path}")

        cur.execute("SELECT uid, bufgz FROM objs WHERE bufgz IS NOT NULL ORDER BY rowid")
        for uid, blob in cur:
            work_q.put((uid, blob))
            count += 1
            if count % REPORT_INTERVAL == 0:
                logging.info(f"Queued {count:,} / ~{total:,}")

    for _ in range(MAX_WORKERS):
        work_q.put(None)

    for w in workers:
        w.join()

    meta_q.put(None)
    writer_proc.join()

    logging.info(f"Done. {count:,} records processed.")


if __name__ == "__main__":
    main()
