#!/usr/bin/env python3
from __future__ import annotations
# Purpose:      Export any DDB sector sqlite to batched N-Triples (full EDM graph) and a
#               Parquet file (ProvidedCHO metadata).
# Usage:        python3 export_ddb.py <sector>.sqlite
# Inputs:       <sector>.sqlite — table objs, column bufgz (gzip-compressed cortex JSON)
# Outputs:      $OUTPUT_DIR/ddbedm-<stem>_{worker:02d}_{batch:04d}.nt  — batched N-Triples
#               $OUTPUT_DIR/<stem>_meta.parquet                         — metadata Parquet
# Dependencies: pyoxigraph, pyarrow
# Assumptions:  The cortex JSON edm.RDF structure follows the DDB non-standard
#               serialisation ($ / resource / lang value patterns, camelCase field names).

import gzip
import json
import logging
import multiprocessing
import os
import queue
import re
import sqlite3
import sys
import traceback
from io import BytesIO
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pyoxigraph as px

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_DIR             = os.environ.get("OUTPUT_DIR", "./out")
BATCH_SIZE             = int(os.environ.get("BATCH_SIZE", 100_000))
MAX_WORKERS            = int(os.environ.get("MAX_WORKERS", max(1, multiprocessing.cpu_count() - 2)))
PARQUET_CHUNK          = int(os.environ.get("PARQUET_CHUNK", 500_000))
REPORT_INTERVAL        = int(os.environ.get("REPORT_INTERVAL", 100_000))
WORKER_REPORT_INTERVAL = int(os.environ.get("WORKER_REPORT_INTERVAL", 10_000))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ---------------------------------------------------------------------------
# Namespaces
# ---------------------------------------------------------------------------

DC      = "http://purl.org/dc/elements/1.1/"
DCTERMS = "http://purl.org/dc/terms/"
EDM     = "http://www.europeana.eu/schemas/edm/"
ORE     = "http://www.openarchives.org/ore/terms/"
SKOS    = "http://www.w3.org/2004/02/skos/core#"
RDF_NS  = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
WGS84   = "http://www.w3.org/2003/01/geo/wgs84_pos#"
DDB     = "https://www.deutsche-digitale-bibliothek.de/ontology#"
CRM     = "http://www.cidoc-crm.org/cidoc-crm/"
OWL     = "http://www.w3.org/2002/07/owl#"
FOAF    = "http://xmlns.com/foaf/0.1/"
DDBEDM  = "urn:edm:"

RDF_TYPE_URI = RDF_NS + "type"

# ---------------------------------------------------------------------------
# RDF type per entity class
# ---------------------------------------------------------------------------

ENTITY_RDF_TYPE = {
    "ProvidedCHO":    EDM + "ProvidedCHO",
    "Aggregation":    ORE + "Aggregation",
    "Agent":          EDM + "Agent",
    "Place":          EDM + "Place",
    "Event":          EDM + "Event",
    "Concept":        SKOS + "Concept",
    "WebResource":    EDM + "WebResource",
    "TimeSpan":       EDM + "TimeSpan",
    "PhysicalThing":  EDM + "PhysicalThing",
    "LinguisticSystem": EDM + "LinguisticSystem",
    "Organization":   "http://www.w3.org/ns/org#Organization",
    "Address":        "http://www.w3.org/ns/locn#Address",
}

# ---------------------------------------------------------------------------
# Field name → predicate URI per entity class
# Source: data/ddbedm-properties-per-sector.csv + sample verification
# ---------------------------------------------------------------------------

PRED: dict[str, dict[str, str]] = {
    "ProvidedCHO": {
        # DC elements
        "contributor":          DC + "contributor",
        "creator":              DC + "creator",
        "date":                 DC + "date",
        "description":          DC + "description",
        "format":               DC + "format",
        "identifier":           DC + "identifier",
        "language":             DC + "language",
        "publisher":            DC + "publisher",
        "relation":             DC + "relation",
        "rights":               DC + "rights",
        "source":               DC + "source",
        "dcSubject":            DC + "subject",
        "title":                DC + "title",
        "type":                 DC + "type",
        # DC terms
        "alternative":          DCTERMS + "alternative",
        "bibliographicCitation": DCTERMS + "bibliographicCitation",
        "dcTermsLanguage":      DCTERMS + "language",
        "extent":               DCTERMS + "extent",
        "isPartOf":             DCTERMS + "isPartOf",
        "issued":               DCTERMS + "issued",
        "medium":               DCTERMS + "medium",
        "provenance":           DCTERMS + "provenance",
        "spatial":              DCTERMS + "spatial",
        "dcTermsSubject":       DCTERMS + "subject",
        "temporal":             DCTERMS + "temporal",
        # DDB
        "aggregationEntity":    DDB + "aggregationEntity",
        "hierarchyPosition":    DDB + "hierarchyPosition",
        "hierarchyType":        DDB + "hierarchyType",
        # EDM
        "currentLocation":      EDM + "currentLocation",
        "hasMet":               EDM + "hasMet",
        "hasType":              EDM + "hasType",
        "isNextInSequence":     EDM + "isNextInSequence",
        "dcType":               DC + "type",
    },
    "Aggregation": {
        "aggregatedCHO":  EDM + "aggregatedCHO",
        "dataProvider":   EDM + "dataProvider",
        "hasView":        EDM + "hasView",
        "isShownAt":      EDM + "isShownAt",
        "isShownBy":      EDM + "isShownBy",
        "object":         EDM + "object",
        "provider":       EDM + "provider",
        "edmRights":      EDM + "rights",
        "dcTermsRights":  DCTERMS + "rights",
        "aggregator":     DDB + "aggregator",
    },
    "Agent": {
        "prefLabel":             SKOS + "prefLabel",
        "altLabel":              SKOS + "altLabel",
        "note":                  SKOS + "note",
        "isPartOf":              DCTERMS + "isPartOf",
        "hasPart":               DCTERMS + "hasPart",
        "identifier":            DC + "identifier",
        "date":                  DC + "date",
        "name":                  FOAF + "name",
        "wasPresentAt":          EDM + "wasPresentAt",
        "begin":                 EDM + "begin",
        "end":                   EDM + "end",
        "hasMet":                EDM + "hasMet",
        "isRelatedTo":           EDM + "isRelatedTo",
        "biographicalInformation": EDM + "biographicalInformation",
        "dateOfBirth":           EDM + "dateOfBirth",
        "dateOfDeath":           EDM + "dateOfDeath",
        "dateOfEstablishment":   EDM + "dateOfEstablishment",
        "dateOfTermination":     EDM + "dateOfTermination",
        "gender":                EDM + "gender",
        "placeOfBirth":          EDM + "placeOfBirth",
        "placeOfDeath":          EDM + "placeOfDeath",
        "professionOrOccupation": EDM + "professionOrOccupation",
        "sameAs":                OWL + "sameAs",
        "type":                  EDM + "type",
    },
    "Place": {
        "prefLabel":        SKOS + "prefLabel",
        "altLabel":         SKOS + "altLabel",
        "note":             SKOS + "note",
        "lat":              WGS84 + "lat",
        "long":             WGS84 + "long",
        "alt":              WGS84 + "alt",
        "hasPart":          DCTERMS + "hasPart",
        "isPartOf":         DCTERMS + "isPartOf",
        "isNextInSequence": EDM + "isNextInSequence",
        "sameAs":           OWL + "sameAs",
        "type":             DC + "type",
    },
    "Event": {
        "hasType":             EDM + "hasType",
        "happenedAt":          EDM + "happenedAt",
        "occuredAt":           EDM + "occuredAt",
        "P11_had_participant": CRM + "P11_had_participant",
    },
    "Concept": {
        "notation":  SKOS + "notation",
        "prefLabel": SKOS + "prefLabel",
        "altLabel":  SKOS + "altLabel",
        "note":      SKOS + "note",
        "broader":   SKOS + "broader",
        "narrower":  SKOS + "narrower",
        "related":   SKOS + "related",
    },
    "WebResource": {
        "creator":       DC + "creator",
        "description":   DC + "description",
        "format":        DC + "format",
        "publisher":     DC + "publisher",
        "rights":        DC + "rights",
        "type":          DC + "type",
        "created":       DCTERMS + "created",
        "dcTermsRights": DCTERMS + "rights",
        "edmRights":     EDM + "rights",
    },
    "TimeSpan": {
        "begin":      EDM + "begin",
        "end":        EDM + "end",
        "notation":   SKOS + "notation",
        "prefLabel":  SKOS + "prefLabel",
    },
    "PhysicalThing": {
        "title":             DC + "title",
        "isPartOf":          DCTERMS + "isPartOf",
        "aggregationEntity": DDB + "aggregationEntity",
        "hierarchyPosition": DDB + "hierarchyPosition",
        "hierarchyType":     DDB + "hierarchyType",
    },
    "LinguisticSystem": {
        "value": RDF_NS + "value",
    },
    "Organization": {
        "prefLabel": SKOS + "prefLabel",
    },
    "Address": {},
}

# LIDO event type URIs that carry creation/publication dates
LIDO_CREATED = {
    "http://terminology.lido-schema.org/lido00012",
    "http://terminology.lido-schema.org/eventType/creation",
    "http://terminology.lido-schema.org/lido00007",
}
LIDO_ISSUED = {
    "http://terminology.lido-schema.org/lido00228",
    "http://terminology.lido-schema.org/eventType/publication",
}

# ---------------------------------------------------------------------------
# Parquet schema
# ---------------------------------------------------------------------------

AGENT_STRUCT = pa.struct([pa.field("label", pa.string()), pa.field("uri", pa.string())])

PARQUET_SCHEMA = pa.schema([
    ("obj_id",           pa.string()),
    ("lang",             pa.string()),
    ("title",            pa.string()),
    ("dc_type",          pa.string()),
    ("dc_creator",       pa.list_(AGENT_STRUCT)),
    ("dc_contributor",   pa.list_(AGENT_STRUCT)),
    ("dc_publisher",     pa.list_(AGENT_STRUCT)),
    ("dc_subject",       pa.list_(pa.string())),
    ("dc_subject_uris",  pa.list_(pa.string())),
    ("dc_date",          pa.string()),
    ("dc_date_qualifier", pa.string()),
    ("dc_issued",        pa.list_(pa.string())),
    ("dc_created",       pa.list_(pa.string())),
    ("agents",           pa.list_(pa.string())),
    ("hierarchy_type",   pa.string()),
    ("is_part_of",       pa.bool_()),
])

# ---------------------------------------------------------------------------
# URI helpers
# ---------------------------------------------------------------------------

def to_named_node(val: str, entity_type: str) -> px.NamedNode | None:
    """Mint a NamedNode, prefixing bare IDs with the GeMeA EDM namespace."""
    if not val or not isinstance(val, str):
        return None
    if val.startswith("http") or val.startswith("urn"):
        try:
            return px.NamedNode(val)
        except Exception:
            return None
    try:
        return px.NamedNode(DDBEDM + entity_type + ":" + val)
    except Exception:
        return None


def value_to_rdf_object(val, entity_type: str) -> list[px.NamedNode | px.Literal]:
    """Convert a cortex JSON value to a list of RDF objects."""
    if val is None:
        return []
    if isinstance(val, list):
        result = []
        for item in val:
            result.extend(value_to_rdf_object(item, entity_type))
        return result
    if isinstance(val, dict):
        resource = val.get("resource")
        text = val.get("$")
        lang = val.get("lang")
        if resource:
            node = to_named_node(resource, entity_type)
            return [node] if node else []
        if text:
            if lang and lang not in ("", "zxx", "und"):
                try:
                    return [px.Literal(str(text), language=lang)]
                except Exception:
                    return [px.Literal(str(text))]
            return [px.Literal(str(text))]
        return []
    if isinstance(val, str) and val:
        return [px.Literal(val)]
    if isinstance(val, (int, float)):
        return [px.Literal(str(val))]
    return []


# ---------------------------------------------------------------------------
# EDM → RDF triples
# ---------------------------------------------------------------------------

def build_about_type_map(rdf: dict) -> dict[str, str]:
    """Map each entity's bare about-value to its entity type for URI minting."""
    mapping = {}
    for entity_type, val in rdf.items():
        if entity_type not in PRED:
            continue
        entities = val if isinstance(val, list) else [val]
        for entity in entities:
            if not isinstance(entity, dict):
                continue
            about = entity.get("about")
            if about and isinstance(about, str):
                mapping[about] = entity_type
    return mapping


def entity_to_triples(
    entity_type: str,
    entity: dict,
    about_type_map: dict,
) -> list[px.Triple]:
    """Return all triples for one entity."""
    triples = []
    about = entity.get("about")
    if not about:
        return triples

    entity_type_for_about = about_type_map.get(about, entity_type)
    subj = to_named_node(about, entity_type_for_about)
    if subj is None:
        return triples

    rdf_type = ENTITY_RDF_TYPE.get(entity_type)
    if rdf_type:
        triples.append(px.Triple(subj, px.NamedNode(RDF_TYPE_URI), px.NamedNode(rdf_type)))

    pred_map = PRED.get(entity_type, {})
    for field, raw_val in entity.items():
        if field == "about" or raw_val is None:
            continue
        pred_uri = pred_map.get(field)
        if not pred_uri:
            continue
        pred = px.NamedNode(pred_uri)
        for obj in value_to_rdf_object(raw_val, entity_type):
            triples.append(px.Triple(subj, pred, obj))

    return triples


def record_to_triples(data: dict) -> bytes:
    """Convert one cortex JSON blob to N-Triples bytes."""
    rdf = data.get("edm", {}).get("RDF") or {}
    all_triples = []

    about_type_map = build_about_type_map(rdf)

    for entity_type, val in rdf.items():
        if val is None:
            continue
        entities = val if isinstance(val, list) else [val]
        for entity in entities:
            if not isinstance(entity, dict):
                continue
            try:
                all_triples.extend(entity_to_triples(entity_type, entity, about_type_map))
            except Exception:
                pass

    return px.serialize(all_triples, format=px.RdfFormat.N_TRIPLES)


# ---------------------------------------------------------------------------
# Parquet metadata extraction
# ---------------------------------------------------------------------------

_DATE_QUALIFIER_RE = re.compile(r"\(([^)]+)\)")
_DATE_YYYYMMDD_RE  = re.compile(r"^(\d{4})(\d{2})(\d{2})$")
_DATE_YYYY_RE      = re.compile(r"\d{4}")


def parse_dc_date(raw: str) -> tuple[str | None, str | None]:
    """Return (normalised_date, qualifier) from a free-text dc:date string."""
    if not raw:
        return None, None
    qualifier = None
    m = _DATE_QUALIFIER_RE.search(raw)
    if m:
        qualifier = m.group(1).strip()
        raw = raw[:m.start()].strip()

    raw = raw.strip("[]").strip()

    # yyyymmdd → yyyy-mm-dd
    m = _DATE_YYYYMMDD_RE.match(raw)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}", qualifier

    # already ISO or range — keep as-is if it starts with a digit
    if raw and raw[0].isdigit():
        return raw, qualifier

    # fallback: extract first 4-digit year
    m = _DATE_YYYY_RE.search(raw)
    if m:
        return m.group(0), qualifier

    return None, qualifier


def _scalar_values(field_val) -> list[str]:
    """Extract string values from a cortex JSON field (scalar, dict, or list)."""
    if field_val is None:
        return []
    if isinstance(field_val, str):
        return [field_val] if field_val else []
    if isinstance(field_val, dict):
        v = field_val.get("$") or field_val.get("resource") or ""
        return [v] if v else []
    if isinstance(field_val, list):
        out = []
        for item in field_val:
            out.extend(_scalar_values(item))
        return out
    return [str(field_val)]


def _resource_values(field_val, entity_type: str) -> list[str]:
    """Extract minted URI strings from resource references."""
    if field_val is None:
        return []
    if isinstance(field_val, list):
        out = []
        for item in field_val:
            out.extend(_resource_values(item, entity_type))
        return out
    if isinstance(field_val, dict):
        r = field_val.get("resource")
        if r:
            node = to_named_node(r, entity_type)
            return [node.value] if node else []
    return []


def _agent_structs(field_val, entity_type: str) -> list[dict]:
    """Extract {label, uri} dicts from a cortex agent field, pairing label and URI
    when both appear in the same dict entry."""
    if field_val is None:
        return []
    if isinstance(field_val, list):
        out = []
        for item in field_val:
            out.extend(_agent_structs(item, entity_type))
        return out
    if isinstance(field_val, dict):
        label    = field_val.get("$") or None
        resource = field_val.get("resource") or None
        uri = None
        if resource:
            node = to_named_node(resource, entity_type)
            uri = node.value if node else None
        if label or uri:
            return [{"label": label, "uri": uri}]
        return []
    if isinstance(field_val, str) and field_val:
        return [{"label": field_val, "uri": None}]
    return []


def extract_meta(data: dict) -> dict:
    """Extract ProvidedCHO metadata for the Parquet row."""
    props = data.get("properties", {})
    rdf   = data.get("edm", {}).get("RDF") or {}
    cho   = rdf.get("ProvidedCHO") or {}
    agg   = rdf.get("Aggregation") or {}

    # build Event and TimeSpan lookup for date extraction
    events    = rdf.get("Event") or []
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

    # dc_created via event chain
    dc_created = []
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
            vals = _scalar_values(ts.get(key))
            dc_created.extend(vals)

    # dc_issued via event chain + ProvidedCHO.issued
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
            vals = _scalar_values(ts.get(key))
            dc_issued.extend(vals)

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
    # dataProvider entries may be separate label/URI dicts in the same list, not paired
    dp = agg.get("dataProvider") or []
    if isinstance(dp, dict):
        dp = [dp]
    publisher_structs = (
        _agent_structs(cho.get("publisher"), "Agent")
        + _agent_structs(dp, "Organization")
    )

    return {
        "obj_id":        props.get("item-id", ""),
        "lang":          cho.get("language") or "",
        "title":         (_scalar_values(cho.get("title")) or [""])[0],
        "dc_type":       (_scalar_values(cho.get("dcType")) or [""])[0],
        "dc_creator":    _agent_structs(cho.get("creator"), "Agent"),
        "dc_contributor": _agent_structs(cho.get("contributor"), "Agent"),
        "dc_publisher":  publisher_structs,
        "dc_subject":       _scalar_values(cho.get("dcSubject")),
        "dc_subject_uris":  _resource_values(cho.get("dcTermsSubject"), "Concept"),
        "dc_date":          dc_date,
        "dc_date_qualifier": dc_date_qualifier,
        "dc_issued":        dc_issued,
        "dc_created":       dc_created,
        "agents":           agents,
        "hierarchy_type":   (_scalar_values(cho.get("hierarchyType")) or [None])[0],
        "is_part_of":       bool(cho.get("isPartOf")),
    }


# ---------------------------------------------------------------------------
# Worker process
# ---------------------------------------------------------------------------

def _iter_json(path: str):
    """Yield (uid, json_bytes) for each record in a JSON array or JSON Lines file."""
    with open(path, encoding="utf-8") as f:
        first = f.read(1)
        f.seek(0)
        if first == "[":
            records = json.load(f)
            for rec in records:
                uid = (rec.get("properties") or {}).get("item-id", "")
                yield uid, json.dumps(rec, ensure_ascii=False).encode()
        else:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                uid = (rec.get("properties") or {}).get("item-id", "")
                yield uid, json.dumps(rec, ensure_ascii=False).encode()


def worker(
    worker_id: int,
    work_q: multiprocessing.Queue,
    meta_q: multiprocessing.Queue,
    compressed: bool = True,
    stem: str = "out",
) -> None:
    batch_triples: list[bytes] = []
    batch_meta:    list[dict]  = []
    batch_num = _next_batch_num(worker_id, stem)
    processed = 0

    def flush_nt():
        nonlocal batch_num
        if not batch_triples:
            return
        path = Path(OUTPUT_DIR) / f"ddbedm-{stem}_{worker_id:02d}_{batch_num:04d}.nt"
        with open(path, "wb") as f:
            for chunk in batch_triples:
                f.write(chunk)
        batch_triples.clear()
        batch_num += 1

    def flush_meta():
        if not batch_meta:
            return
        meta_q.put(list(batch_meta))
        batch_meta.clear()

    while True:
        item = work_q.get()
        if item is None:
            flush_nt()
            flush_meta()
            break
        uid, blob = item
        try:
            data = json.loads(gzip.decompress(blob) if compressed else blob)
            nt_bytes = record_to_triples(data)
            meta_row = extract_meta(data)
            batch_triples.append(nt_bytes)
            batch_meta.append(meta_row)
            processed += 1
        except Exception:
            traceback.print_exc()
            continue

        if processed % WORKER_REPORT_INTERVAL == 0:
            logging.info(f"Worker {worker_id}: processed {processed:,} records")

        if len(batch_triples) >= BATCH_SIZE:
            flush_nt()
            flush_meta()


# ---------------------------------------------------------------------------
# Meta writer process
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
# Checkpoint helpers
# ---------------------------------------------------------------------------

def _checkpoint_path() -> Path:
    return Path(OUTPUT_DIR) / ".export_progress.json"


def _load_checkpoint() -> int:
    """Return last rowid successfully queued, or 0 if no checkpoint."""
    p = _checkpoint_path()
    if p.exists():
        try:
            return int(json.loads(p.read_text()).get("last_rowid", 0))
        except Exception:
            return 0
    return 0


def _save_checkpoint(last_rowid: int) -> None:
    _checkpoint_path().write_text(json.dumps({"last_rowid": last_rowid}))


def _next_batch_num(worker_id: int, stem: str) -> int:
    """Scan OUTPUT_DIR to find the next unused batch number for this worker."""
    existing = sorted(Path(OUTPUT_DIR).glob(f"ddbedm-{stem}_{worker_id:02d}_*.nt"))
    if not existing:
        return 0
    return int(existing[-1].stem.split("_")[-1]) + 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <input.sqlite|input.json>", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    suffix     = Path(input_path).suffix.lower()
    is_json    = suffix == ".json"
    compressed = not is_json

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    stem         = Path(input_path).stem
    parquet_path = str(Path(OUTPUT_DIR) / f"{stem}_meta.parquet")

    logging.info(f"Workers: {MAX_WORKERS}, batch size: {BATCH_SIZE:,}")
    logging.info(f"Output dir: {OUTPUT_DIR}")

    work_q = multiprocessing.Queue(MAX_WORKERS * 4)
    meta_q = multiprocessing.Queue(1000)

    workers = [
        multiprocessing.Process(target=worker, args=(i, work_q, meta_q, compressed, stem), daemon=True)
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
        last_rowid = _load_checkpoint()
        if last_rowid:
            logging.info(f"Resuming from rowid {last_rowid:,}")
            if Path(parquet_path).exists():
                logging.warning(
                    f"Existing {parquet_path} found — this run will write a new file "
                    f"covering only rows after rowid {last_rowid:,}. "
                    f"Concatenate both files afterwards."
                )
                parquet_path = str(Path(OUTPUT_DIR) / f"{stem}_meta_resume_{last_rowid}.parquet")

        db  = sqlite3.connect(input_path)
        cur = db.cursor()
        cur.execute("SELECT max(rowid) FROM objs")
        total = (cur.fetchone()[0] or 0) - last_rowid
        logging.info(f"Processing ~{total:,} records from {input_path}")

        cur.execute(
            "SELECT rowid, uid, bufgz FROM objs WHERE bufgz IS NOT NULL AND rowid > ? ORDER BY rowid",
            (last_rowid,),
        )
        last_seen_rowid = last_rowid
        for rowid, uid, blob in cur:
            work_q.put((uid, blob))
            count += 1
            last_seen_rowid = rowid
            if count % REPORT_INTERVAL == 0:
                _save_checkpoint(last_seen_rowid)
                logging.info(f"Queued {count:,} / ~{total:,} (rowid {last_seen_rowid:,})")

        _checkpoint_path().unlink(missing_ok=True)

    for _ in range(MAX_WORKERS):
        work_q.put(None)

    for w in workers:
        w.join()

    meta_q.put(None)
    writer_proc.join()

    logging.info(f"Done. {count:,} records processed.")


if __name__ == "__main__":
    main()
