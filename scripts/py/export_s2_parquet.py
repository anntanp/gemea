#!/usr/bin/env python3
from __future__ import annotations
# Purpose:      Re-export only the Parquet metadata from s2.sqlite, skipping NT generation.
#               Use this to rebuild s2_meta.parquet after schema changes without re-running
#               the full export_s2.py pipeline.
# Usage:        python3 export_s2_parquet.py <s2.sqlite>
# Inputs:       s2.sqlite — table objs, column bufgz (gzip-compressed cortex JSON)
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

# Re-use schema constants and internal helpers from export_s2.
# extract_meta is redefined below with the dc_created fix.
sys.path.insert(0, str(Path(__file__).parent))
from export_s2 import (
    PARQUET_SCHEMA,
    REPORT_INTERVAL,
    WORKER_REPORT_INTERVAL,
    LIDO_CREATED,
    LIDO_ISSUED,
    parse_dc_date,
    build_about_type_map,
    to_named_node,
    _scalar_values,
    _agent_structs,
    _resource_values,
    _iter_json,
)


def extract_meta(data: dict) -> dict:
    """Extract ProvidedCHO metadata for the Parquet row.

    Fixes vs. export_s2.extract_meta:
      - dc_created: read dcterms:created from ProvidedCHO directly first,
        then extend with LIDO creation-event chain.
      - dc_issued:  read dcterms:issued from ProvidedCHO directly first (was
        already done), then extend with LIDO publication-event chain.
    Both are now consistent: direct ProvidedCHO field → hasMet traversal.
    """
    props = data.get("properties", {})
    rdf   = data.get("edm", {}).get("RDF") or {}
    cho   = rdf.get("ProvidedCHO") or {}
    agg   = rdf.get("Aggregation") or {}

    # build Event and TimeSpan lookup for date extraction
    events = rdf.get("Event") or []
    if isinstance(events, dict):
        events = [events]
    timespans = rdf.get("TimeSpan") or []
    if isinstance(timespans, dict):
        timespans = [timespans]
    ts_map = {t["about"]: t for t in timespans if isinstance(t, dict) and t.get("about")}

    # dc:date (normalised)
    dc_date_raw = _scalar_values(cho.get("date"))
    dc_date, dc_date_qualifier = (None, None)
    if dc_date_raw:
        dc_date, dc_date_qualifier = parse_dc_date(dc_date_raw[0])

    # dc_created: ProvidedCHO.dcterms:created first, then hasMet traversal
    dc_created = _scalar_values(cho.get("created"))
    for ev in events:
        if not isinstance(ev, dict):
            continue
        ht = (ev.get("hasType") or {})
        ht_uri = ht.get("resource") if isinstance(ht, dict) else None
        if ht_uri not in LIDO_CREATED:
            continue
        oc = ev.get("occuredAt")
        if not oc:
            continue
        ts_ref = oc.get("resource") if isinstance(oc, dict) else oc
        ts = ts_map.get(ts_ref, {}) if isinstance(ts_ref, str) else {}
        for key in ("begin", "end"):
            dc_created.extend(_scalar_values(ts.get(key)))

    # dc_issued: ProvidedCHO.dcterms:issued first, then hasMet traversal
    dc_issued = _scalar_values(cho.get("issued"))
    for ev in events:
        if not isinstance(ev, dict):
            continue
        ht = (ev.get("hasType") or {})
        ht_uri = ht.get("resource") if isinstance(ht, dict) else None
        if ht_uri not in LIDO_ISSUED:
            continue
        oc = ev.get("occuredAt")
        if not oc:
            continue
        ts_ref = oc.get("resource") if isinstance(oc, dict) else oc
        ts = ts_map.get(ts_ref, {}) if isinstance(ts_ref, str) else {}
        for key in ("begin", "end"):
            dc_issued.extend(_scalar_values(ts.get(key)))

    # agents via hasMet → Event.P11_had_participant
    agents = []
    hasMet = cho.get("hasMet") or []
    if isinstance(hasMet, dict):
        hasMet = [hasMet]
    event_map = {
        e["about"]: e for e in events
        if isinstance(e, dict) and e.get("about")
    }
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
            r = p.get("resource")
            if r:
                et = about_type_map.get(r, "Agent")
                node = to_named_node(r, et)
                if node:
                    agents.append(node.value)

    # dc_publisher: ProvidedCHO.publisher + Aggregation.dataProvider
    dp = agg.get("dataProvider") or []
    if isinstance(dp, dict):
        dp = [dp]
    publisher_structs = (
        _agent_structs(cho.get("publisher"), "Agent")
        + _agent_structs(dp, "Organization")
    )

    return {
        "obj_id":            props.get("item-id", ""),
        "lang":              cho.get("language") or "",
        "title":             (_scalar_values(cho.get("title")) or [""])[0],
        "dc_type":           (_scalar_values(cho.get("dcType")) or [""])[0],
        "dc_creator":        _agent_structs(cho.get("creator"), "Agent"),
        "dc_contributor":    _agent_structs(cho.get("contributor"), "Agent"),
        "dc_publisher":      publisher_structs,
        "dc_subject":        _scalar_values(cho.get("dcSubject")),
        "dc_subject_uris":   _resource_values(cho.get("dcTermsSubject"), "Concept"),
        "dc_date":           dc_date,
        "dc_date_qualifier": dc_date_qualifier,
        "dc_issued":         dc_issued,
        "dc_created":        dc_created,
        "agents":            agents,
        "hierarchy_type":    (_scalar_values(cho.get("hierarchyType")) or [None])[0],
        "is_part_of":        bool(cho.get("isPartOf")),
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
