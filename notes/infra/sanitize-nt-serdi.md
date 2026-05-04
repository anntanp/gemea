# NT IRI Sanitization — pyoxigraph vs. serd

## 1. Problem

QLever's NT parser is strict: IRIs inside `<…>` must not contain `<`, `>`, `"`, `{`, `}`, `|`, `\`, `^`, `` ` ``, space, or control characters. pyoxigraph's `NamedNode` constructor accepts these characters without raising, so they pass through to the `.nt` files unescaped and cause index-build failures.

Example error:

```
Parse error at byte position 157905043037: Unterminated IRI reference
(found '<' but no '>' before one of the following characters: <, ", newline)
<http://www.deutsche-digitale-bibliothek.de/item/DQVP5…
```

## 2. Fix applied

`_sanitize_iri()` in `scripts/py/export_ddb.py` percent-encodes all characters forbidden in N-Triples IRI references before constructing any `NamedNode`:

```python
_IRI_UNSAFE_RE = re.compile(r'[\x00-\x20<>"{}|\\^`\x7f]')

def _sanitize_iri(iri: str) -> str:
    return _IRI_UNSAFE_RE.sub(lambda m: f"%{ord(m.group()):02X}", iri)
```

Called in `to_named_node()` for both absolute IRIs and minted `urn:edm:` IRIs.

## 3. serd as alternative

Serd (`serd-main/`) is a pure C library and CLI (`serdi`) — no Python bindings. It cannot replace pyoxigraph inside the Python pipeline directly.

| Approach | What it does | Trade-off |
|---|---|---|
| pyoxigraph + `_sanitize_iri` (current) | Encode forbidden chars before `NamedNode` construction | Fix at source; no extra step |
| pyoxigraph → `serdi` post-pass | Pipe each `.nt` through `serdi -i ntriples -o ntriples` | Catches any residual escaping issues; adds latency over ~2.5 TB of NT |

**Decision**: the source-level sanitization is sufficient. A `serdi` post-pass would only be warranted if pyoxigraph's serializer introduced additional escaping bugs beyond what `_sanitize_iri` covers.
