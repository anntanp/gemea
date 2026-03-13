# GeMeA — GROBID Setup

**Note**: GROBID is trained on scientific citations (academic papers, journal references), not library catalog records in ISBD format. It is **not recommended as the primary NER fallback** for DDB strings — see [ner-bibliographic.md](ner-bibliographic.md) for the preferred approach. These notes are kept in case GROBID is evaluated as a last resort.

---

## Image choice

Two flavors:

| Image | Suffix | Hardware | Use case |
|---|---|---|---|
| CRF | `-crf` | CPU only | Reference string parsing — sufficient for DDB strings |
| Full | `-full` | GPU + CPU | PDF full-text extraction — overkill for this task |

Use the CRF image.

---

## Docker Compose

Add to `docker-compose.yml`:

```yaml
grobid:
  image: grobid/grobid:0.8.2-crf
  init: true
  ulimits:
    core: 0
  ports:
    - "8070:8070"
  restart: unless-stopped
```

Or run standalone:

```bash
docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.8.2-crf
```

Health check: `http://localhost:8070/api/isalive`

---

## Python client

```bash
pip install grobid-client-python
```

Relevant endpoint for raw catalog strings: `processCitationList` — takes a list of raw reference strings, returns TEI-XML.

```python
import requests
from lxml import etree

GROBID_URL = "http://localhost:8070"

def parse_citations(strings: list[str]) -> list[dict]:
    resp = requests.post(
        f"{GROBID_URL}/api/processCitationList",
        data={
            "citations": "\n".join(strings),
            "consolidateCitations": "0",  # no external API lookups
        },
        timeout=30,
    )
    resp.raise_for_status()
    return _parse_tei(resp.text)

def _parse_tei(tei_xml: str) -> list[dict]:
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}
    root = etree.fromstring(tei_xml.encode())
    results = []
    for bibl in root.findall(".//tei:biblStruct", ns):
        title_el = bibl.find(".//tei:title[@level='m']", ns) or bibl.find(".//tei:title", ns)
        author_el = bibl.find(".//tei:persName", ns)
        date_el = bibl.find(".//tei:date", ns)
        results.append({
            "title": title_el.text if title_el is not None else None,
            "author": author_el.text if author_el is not None else None,
            "year": date_el.get("when") if date_el is not None else None,
        })
    return results
```

---

## Caveats for DDB strings

GROBID's reference parser was trained on scientific citation strings (e.g. `Goethe, J.W. (1887). Faust. Weimar: Böhlau.`), not ISBD catalog records. ISBD format is similar but not identical.

**Required before committing**: run a sample of ~200 failed-ISBD strings through GROBID and manually check `<title>` extraction precision. If precision is poor, fall back to the silver labeling approach described in [ner-bibliographic.md](ner-bibliographic.md).

---

## References

- [GROBID Docker docs](https://grobid.readthedocs.io/en/latest/Grobid-docker/)
- [grobid-client-python](https://github.com/kermitt2/grobid-client-python)
- [GROBID Service API](https://grobid.readthedocs.io/en/latest/Grobid-service/)
