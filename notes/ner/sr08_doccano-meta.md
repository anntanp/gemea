# SR-08: Doccano Meta Fields (htype + DDB URL)

## Instance

- URL: `https://doccano.ise.fiz-karlsruhe.de`
- Dummy test project: `/projects/2/`
- Auth: Token via `POST /v1/auth/login/`

## API docs

Live interactive docs (Swagger UI and ReDoc) are available on the instance:

| URL | Format |
|-----|--------|
| `https://doccano.ise.fiz-karlsruhe.de/v1/swagger/` | Swagger UI |
| `https://doccano.ise.fiz-karlsruhe.de/v1/redoc/` | ReDoc |
| `https://doccano.ise.fiz-karlsruhe.de/v1/schema/` | Raw OpenAPI schema |

## API curl reference

```bash
HOST="https://doccano.ise.fiz-karlsruhe.de"
PID=1  # project ID

# ── Auth ─────────────────────────────────────────────────────────────────────

# Authenticate — returns {"key": "<token>"}
curl -s -X POST $HOST/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"<user>","password":"<pass>"}'

TOKEN="<token>"  # set from response above

# Get CSRF cookie (required for POST/PATCH/DELETE)
curl -s -c cookies.txt -X POST $HOST/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"<user>","password":"<pass>"}' > /dev/null
CSRF=$(grep csrftoken cookies.txt | awk '{print $7}')

# Current user profile (includes user id)
curl -s -H "Authorization: Token $TOKEN" $HOST/v1/auth/user/

# ── Users & members ──────────────────────────────────────────────────────────

# List project members (includes user IDs and roles)
curl -s -H "Authorization: Token $TOKEN" $HOST/v1/projects/$PID/members

# ── Examples (documents) ─────────────────────────────────────────────────────

# List examples — paginated; use ?offset=N to page
curl -s -H "Authorization: Token $TOKEN" \
  "$HOST/v1/projects/$PID/examples?limit=200"

# Get single example
curl -s -H "Authorization: Token $TOKEN" \
  "$HOST/v1/projects/$PID/examples/<example_id>"

# PATCH meta onto an existing example (no re-import needed)
curl -s -X PATCH \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF" -b "csrftoken=$CSRF" \
  -d '{"meta": {"htype": "htype_018 (Kapitel)", "url": "https://..."}}' \
  "$HOST/v1/projects/$PID/examples/<example_id>"

# ── Spans (annotations) ──────────────────────────────────────────────────────

# Get spans for an example — returns authenticated user's spans only
curl -s -H "Authorization: Token $TOKEN" \
  "$HOST/v1/projects/$PID/examples/<example_id>/spans?limit=50"

# ── Label types ──────────────────────────────────────────────────────────────

# List span label types (returns id, text, color per label)
curl -s -H "Authorization: Token $TOKEN" \
  "$HOST/v1/projects/$PID/span-types"

# ── Assignments ──────────────────────────────────────────────────────────────

# POST assignment — assignee must be user ID integer, not username
# No trailing slash (405 with slash)
curl -s -X POST \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF" -b "csrftoken=$CSRF" \
  -d '{"assignee": <user_id>, "example": <example_id>}' \
  "$HOST/v1/projects/$PID/assignments"
```

## Annotator comments (export-20260608-1221)

Data: `data/processed/ner/sr08_comments_export-20260608-1221.csv`

**Total: 49 comments across 3 annotators**

| Annotator | Comments |
|-----------|----------|
| gundi     | 38       |
| frankp    | 8        |
| maria     | 3        |

Gundi's 38 comments are all the same pattern: *"Keine Annotation, da es sich um ein Kapitel/Aufsatz/Abschnitt handelt."* — she skipped structural htypes (Kapitel, Aufsatz, Abschnitt) and flagged them explicitly.

frankp's 8 comments are substantive: boundary ambiguities, suspected misprints, multi-title entries, authorship uncertainty.

maria's 3 comments flag missing or incorrect title data in the source record.

## Findings

- `meta` is a **document-level field**, not per-annotator — patching it once updates the display for all users in the project; run `--patch-meta` once with any annotator's JSONL
- `Authorization: Token <key>` (not `Bearer`) — Doccano uses DRF token auth
- `assignee` in assignment POST must be a **user ID integer** (not username); get it from `GET /v1/auth/user/` or `GET /v1/projects/<pid>/members`
- Assignment endpoint: no trailing slash — `405` with slash
- POST/PATCH require CSRF token from login cookie (`csrftoken`); pass as `X-CSRFToken` header and cookie
- `/spans` endpoint returns **only the authenticated user's** annotations — to verify another annotator's spans, authenticate as that user
- Doccano behind a reverse proxy returns `http://` in pagination `next` URLs — the script rewrites the scheme automatically
- Example IDs in project 1 match JSONL doc IDs 1–395 (imported sequentially)
