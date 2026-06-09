# Persistent URI Plan — w3id.org Registration (GeMeA + mocho)

**Date**: 2026-05-07
**Context**: ISWC 2026 full paper due today. Namespaces must be locked before submission. w3id.org provides free, community-maintained persistent URIs via GitHub PR. Two separate registrations: one for the GeMeA dataset/resource, one for the mocho ontology.

---

## 0. Separation of Concerns

| Namespace | Purpose | Repo |
|---|---|---|
| `https://w3id.org/gemea/` | GeMeA dataset — named graphs, dataset landing, SPARQL redirect | `anntanp/gemea` |
| `https://w3id.org/mocho/` | mocho ontology — vocabulary terms, ontology document | `anntanp/mocho` |

mocho is kept separate so it can be reused by other projects without depending on GeMeA infrastructure.

---

## 1. URI Scheme

### 1.1 GeMeA (`w3id.org/gemea/`)

| Purpose | URI |
|---|---|
| Dataset landing page | `https://w3id.org/gemea/` |
| Named graph — DDB ingest | `https://w3id.org/gemea/graph/ddb` |
| Named graph — GND enrichment | `https://w3id.org/gemea/graph/gnd-enrichment` |

> The SPARQL endpoint (`https://gemea.ise.fiz-karlsruhe.de/api/sparql`) uses the VPS hostname directly — it is infrastructure, not vocabulary.

### 1.2 mocho (`w3id.org/mocho/`)

| Purpose | URI |
|---|---|
| Ontology namespace | `https://w3id.org/mocho/` |
| Ontology document | `https://w3id.org/mocho/ontology` |
| Individual terms | `https://w3id.org/mocho/#ClassName`, `https://w3id.org/mocho/#propertyName` |

---

## 2. Registration Steps (both namespaces)

The process is identical for both. Do them in the same fork/PR or as two separate PRs.

### 2.1 Fork and clone

```bash
# Fork https://github.com/perma-id/w3id.org on GitHub, then:
git clone https://github.com/anntanp/w3id.org.git
cd w3id.org
```

### 2.2 Create directories

```bash
mkdir gemea mocho
```

### 2.3 `gemea/.htaccess`

```apache
Options -MultiViews
RewriteEngine On

# Named graphs
RewriteRule ^graph/(.*)$ https://gemea.ise.fiz-karlsruhe.de/graph/$1 [R=303,L]

# Catch-all — dataset landing page
RewriteRule ^(.*)$ https://gemea.ise.fiz-karlsruhe.de/$1 [R=303,L]
```

### 2.4 `gemea/README.md`

```markdown
# w3id.org/gemea

Persistent URIs for the German Memory Atlas (GeMeA) — a knowledge graph browser
for 65 million cultural heritage objects from the Deutsche Digitale Bibliothek (DDB).

Maintainer: Ann-Kathrin Tantal <anntanp@gmail.com>
GitHub: https://github.com/anntanp/gemea
Paper: ISWC 2026 Resource Track
```

### 2.5 `mocho/.htaccess`

```apache
Options -MultiViews
RewriteEngine On

# Content negotiation — ontology document
RewriteCond %{HTTP_ACCEPT} text/turtle
RewriteRule ^ontology$ https://w3id.org/mocho/mocho.ttl [R=303,L]

RewriteCond %{HTTP_ACCEPT} application/rdf\+xml
RewriteRule ^ontology$ https://w3id.org/mocho/mocho.rdf [R=303,L]

RewriteRule ^ontology$ https://anntanp.github.io/mocho/ [R=303,L]

# Catch-all — ontology landing page
RewriteRule ^(.*)$ https://anntanp.github.io/mocho/$1 [R=303,L]
```

> Adjust the redirect targets once the mocho hosting location is confirmed (GitHub Pages, VPS, or Widoco-generated site).

### 2.6 `mocho/README.md`

```markdown
# w3id.org/mocho

Persistent URIs for mocho — an OWL ontology for bibliographic metadata normalization,
developed for the German Memory Atlas (GeMeA) project and reusable independently.

Maintainer: Ann-Kathrin Tantal <anntanp@gmail.com>
GitHub: https://github.com/anntanp/mocho
```

### 2.7 Commit and open PR

```bash
git add gemea/ mocho/
git commit -m "Add w3id.org/gemea and w3id.org/mocho persistent URI namespaces"
git push origin main
```

Open a PR against `https://github.com/perma-id/w3id.org` main.
Suggested title: `Add w3id.org/gemea (dataset) and w3id.org/mocho (ontology)`.

Maintainers typically merge within 1–5 days.

---

## 3. What to Update in the Project

Use the namespaces in the paper immediately after opening the PR — they will resolve once merged.

### 3.1 GeMeA

- [ ] `paper/iswc-2026/` — replace any VPS-hostname namespace references with `https://w3id.org/gemea/`
- [ ] QLever named graph URIs — update ingest scripts and Docker Compose config to `https://w3id.org/gemea/graph/...`
- [ ] `resource/README.md` — add `https://w3id.org/gemea/` as canonical dataset URI
- [ ] `notes/project/architecture.md` — update namespace entry

### 3.2 mocho

- [ ] `mocho.owl` / `mocho.ttl` — set `owl:ontologyIRI` to `https://w3id.org/mocho/`
- [ ] mocho `README.md` — update namespace references
- [ ] Any GeMeA scripts importing mocho terms — update prefix declarations

---

## 4. Smoke Test After Merge

```bash
# GeMeA landing page
curl -I https://w3id.org/gemea/

# GeMeA named graph URI (should 303, not 404)
curl -I https://w3id.org/gemea/graph/gnd-enrichment

# mocho ontology — HTML
curl -I https://w3id.org/mocho/ontology

# mocho ontology — Turtle
curl -IH "Accept: text/turtle" https://w3id.org/mocho/ontology
```

---

## 5. References

- w3id.org repo: https://github.com/perma-id/w3id.org
- W3C Permanent Identifier Community Group: https://www.w3.org/community/perma-id/
- Example `.htaccess` files: https://github.com/perma-id/w3id.org/tree/master/purl
