#!/usr/bin/env python3
# Purpose:      Inject meta (htype + DDB URL) into a Doccano annotator JSONL export;
#               POST assignments to the Doccano API after import (--assign mode);
#               or PATCH meta directly onto existing Doccano examples without re-importing (--patch-meta mode)
# Usage:        # Enrich mode — generate new JSONL for import
#               python scripts/ner/sr08_add_meta_to_export.py \
#                   --input  data/annotation/doccano/export-20260608-1221/maria.jsonl \
#                   --output data/annotation/doccano/export-20260608-1221/maria.meta.jsonl
#
#               # Assign mode — run after importing the enriched JSONL into Doccano
#               python scripts/ner/sr08_add_meta_to_export.py --assign \
#                   --input      data/annotation/doccano/export-20260608-1221/maria.jsonl \
#                   --host       http://localhost:8000 \
#                   --username   <user> \
#                   --password   <pass> \
#                   --project-id <n> \
#                   --assignee   maria
#
#               # Patch-meta mode — add meta to existing project without re-importing
#               python scripts/ner/sr08_add_meta_to_export.py --patch-meta \
#                   --input      data/annotation/doccano/export-20260608-1221/maria.jsonl \
#                   --host       https://doccano.ise.fiz-karlsruhe.de \
#                   --username   <user> \
#                   --password   <pass> \
#                   --project-id <n>
# Inputs:       --input: annotator JSONL from Doccano export
#               data/annotation/sr08_gold_sample.csv
#               data/schema/ddbedm-htype.csv
# Outputs:      --output: enriched JSONL (enrich mode); stdout summary (assign/patch-meta modes)
# Dependencies: pandas; requests (assign/patch-meta modes only)
# Assumptions:  Doccano id (1-indexed) == row index + 1 in sr08_gold_sample.csv

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

BASE   = Path(__file__).resolve().parents[2]
SAMPLE = BASE / "data/annotation/sr08_gold_sample.csv"
HTYPE  = BASE / "data/schema/ddbedm-htype.csv"

MONOGRAPH_FALLBACK = "htype_021 (Monografie)"


def build_htype_lookup(path: Path) -> dict:
    df = pd.read_csv(path)
    return {row["label_de"]: f"{row['htype_code']} ({row['label_de']})"
            for _, row in df.iterrows()}


def derive_htype(type_str, lookup: dict):
    if not isinstance(type_str, str):
        return None
    last = type_str.split("|")[-1].strip()
    if last == "Monograph":
        return MONOGRAPH_FALLBACK
    return lookup.get(last)


def load_doccano(path: Path) -> list:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def build_meta_map(doccano: list) -> dict[str, dict]:
    """Return {text: meta_payload} for all records, derived from sr08_gold_sample.csv."""
    lookup    = build_htype_lookup(HTYPE)
    sample_df = pd.read_csv(SAMPLE).reset_index(drop=True)

    if len(doccano) != len(sample_df):
        sys.exit(f"Record count mismatch: {len(doccano)} doccano vs {len(sample_df)} sample rows")
    for i, (rec, (_, row)) in enumerate(zip(doccano, sample_df.iterrows())):
        if rec["text"].strip() != str(row["title"]).strip():
            raise ValueError(
                f"Title mismatch at index {i}:\n  doccano: {rec['text']!r}\n  sample:  {row['title']!r}"
            )

    meta_map: dict[str, dict] = {}
    for i, rec in enumerate(doccano):
        row = sample_df.iloc[i]
        meta_map[rec["text"]] = {
            "htype": derive_htype(row["dc_type"], lookup),
            "url":   row["ddb_link"],
        }
    return meta_map


def cmd_enrich(args):
    doccano  = load_doccano(Path(args.input))
    meta_map = build_meta_map(doccano)

    out = [dict(rec, meta=meta_map[rec["text"]]) for rec in doccano]

    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        for rec in out:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Wrote {len(out)} records → {output_path}")


def _make_session(host: str, username: str, password: str):
    """Authenticate and return (session, base_url)."""
    try:
        import requests
    except ImportError:
        sys.exit("requests is required: pip install requests")

    base = host.rstrip("/")
    login_resp = requests.post(
        f"{base}/v1/auth/login/",
        json={"username": username, "password": password},
    )
    login_resp.raise_for_status()
    token = login_resp.json()["key"]
    csrf  = login_resp.cookies.get("csrftoken", "")

    session = requests.Session()
    session.headers["Authorization"] = f"Token {token}"
    session.headers["X-CSRFToken"]   = csrf
    session.cookies.set("csrftoken", csrf)
    return session, base


def _fetch_all_examples(session, base: str, pid: int) -> list:
    """Fetch all examples from a project, following pagination.

    Rewrites the scheme in Doccano's 'next' URLs to match the configured base —
    Doccano behind a reverse proxy may return http:// links even on an https:// host.
    """
    scheme = base.split("://")[0]  # "https" or "http"

    def _fix_scheme(url: str) -> str:
        if url and url.startswith("http://") and scheme == "https":
            return "https://" + url[len("http://"):]
        return url

    examples = []
    url = f"{base}/v1/projects/{pid}/examples?limit=200"
    while url:
        resp = session.get(url)
        resp.raise_for_status()
        data = resp.json()
        examples.extend(data["results"])
        url = _fix_scheme(data.get("next"))
    return examples


def cmd_assign(args):
    doccano = load_doccano(Path(args.input))
    texts   = {rec["text"] for rec in doccano}

    session, base = _make_session(args.host, args.username, args.password)
    pid = args.project_id

    # Resolve assignee username → user ID via project members
    members_resp = session.get(f"{base}/v1/projects/{pid}/members")
    members_resp.raise_for_status()
    members = {m["username"]: m["user"] for m in members_resp.json()}
    if args.assignee not in members:
        sys.exit(
            f"Assignee '{args.assignee}' not in project {pid}. "
            f"Available: {list(members.keys())}"
        )
    assignee_id = members[args.assignee]

    examples = _fetch_all_examples(session, base, pid)

    # Match by text and POST assignment (no trailing slash — 405 with slash)
    matched = skipped = errors = 0
    for ex in examples:
        if ex["text"] not in texts:
            skipped += 1
            continue
        resp = session.post(
            f"{base}/v1/projects/{pid}/assignments",
            json={"assignee": assignee_id, "example": ex["id"]},
        )
        if resp.status_code in (200, 201, 409):  # 409 = already assigned
            matched += 1
        else:
            print(f"  WARN id={ex['id']}: {resp.status_code} {resp.text[:80]}", file=sys.stderr)
            errors += 1

    print(
        f"Assigned {matched} docs to '{args.assignee}' (id={assignee_id}) "
        f"(skipped {skipped} unmatched, {errors} errors)"
    )


def cmd_patch_meta(args):
    """PATCH meta onto existing project examples — no import, no data loss."""
    doccano  = load_doccano(Path(args.input))
    meta_map = build_meta_map(doccano)

    session, base = _make_session(args.host, args.username, args.password)
    pid = args.project_id

    examples = _fetch_all_examples(session, base, pid)

    patched = skipped = errors = 0
    for ex in examples:
        text = ex["text"]
        if text not in meta_map:
            skipped += 1
            continue
        resp = session.patch(
            f"{base}/v1/projects/{pid}/examples/{ex['id']}",
            json={"meta": meta_map[text]},
        )
        if resp.status_code == 200:
            patched += 1
        else:
            print(f"  WARN id={ex['id']}: {resp.status_code} {resp.text[:80]}", file=sys.stderr)
            errors += 1

    print(
        f"Patched meta on {patched} examples in project {pid} "
        f"(skipped {skipped} unmatched, {errors} errors)"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Add meta to Doccano export (enrich), POST assignments (assign), "
                    "or PATCH meta onto existing project (patch-meta)"
    )
    parser.add_argument("--input", required=True, help="Annotator JSONL from Doccano export")

    parser.add_argument("--output", help="Output path for enriched JSONL (enrich mode)")

    parser.add_argument("--assign",     action="store_true",
                        help="POST assignments to Doccano API (run after import)")
    parser.add_argument("--patch-meta", action="store_true", dest="patch_meta",
                        help="PATCH meta onto existing Doccano examples (no re-import needed)")
    parser.add_argument("--host",       help="Doccano host URL")
    parser.add_argument("--username",   help="Doccano login username")
    parser.add_argument("--password",   help="Doccano login password")
    parser.add_argument("--project-id", type=int, dest="project_id",
                        help="Doccano project ID")
    parser.add_argument("--assignee",   help="Doccano username to assign documents to (assign mode)")

    args = parser.parse_args()

    if args.patch_meta:
        for flag, attr in [("host", "host"), ("username", "username"),
                           ("password", "password"), ("project-id", "project_id")]:
            if not getattr(args, attr):
                parser.error(f"--{flag} is required for --patch-meta mode")
        cmd_patch_meta(args)
    elif args.assign:
        for flag, attr in [("host", "host"), ("username", "username"), ("password", "password"),
                           ("project-id", "project_id"), ("assignee", "assignee")]:
            if not getattr(args, attr):
                parser.error(f"--{flag} is required for --assign mode")
        cmd_assign(args)
    else:
        if not args.output:
            parser.error("--output is required for enrich mode")
        cmd_enrich(args)


if __name__ == "__main__":
    main()
