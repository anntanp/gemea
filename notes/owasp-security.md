# GeMeA — OWASP Security Notes

Reference: OWASP Top 10 (2021). The three most relevant for a public-facing read-only KG service:

---

## A03 — Injection

Untrusted data sent to an interpreter as part of a command or query.

**SPARQL injection**: a user-controlled string embedded in a SPARQL query template could escape the string context and add/modify query logic.
- Mitigation: parameterized SPARQL templates; never string-concatenate user input into queries; QLever is read-only by default; block `UPDATE`/`INSERT`/`DELETE` at the proxy layer.

**Search input (Elasticsearch)**: a malicious string in `q=` could manipulate the ES query DSL if passed raw.
- Mitigation: sanitize and escape all query params before building the ES query object; strip HTML/script from all inputs.

**Most active attack surface for GeMeA.**

---

## A04 — Insecure Design

Architectural decisions that make the system structurally vulnerable, regardless of implementation quality.

The SPARQL endpoint is powerful by design — a single query could dump the entire dataset or trigger a long-running join.
- Mitigation: rate limiting (token bucket: `/sparql` 10 req/s, `/search` 50 req/s); query timeout enforced at the QLever level; read-only proxy.

---

## A05 — Security Misconfiguration

Default settings left in place, unnecessary services exposed, missing hardening.

- **Exposed internal services**: Elasticsearch and QLever admin ports must not be publicly reachable — behind the API only, firewall-blocked externally.
- **Missing security headers**: Next.js and FastAPI ship no security headers by default — set via Nginx: `Content-Security-Policy`, `Strict-Transport-Security`, `X-Frame-Options`, `Referrer-Policy`.
- **Secrets in repo**: `.env.example` with placeholder values only; actual credentials in environment variables, never committed.

---

## Implementation checklist (Phase 4)

- [ ] A03: Parameterized SPARQL templates in all query builders
- [ ] A03: Input sanitization middleware in FastAPI (strip HTML/script)
- [ ] A04: Rate limiting in Nginx (`limit_req_zone`)
- [ ] A04: QLever query timeout configured
- [ ] A05: Elasticsearch + QLever admin ports blocked at network level
- [ ] A05: Security headers in `nginx.conf`
- [ ] A05: `.env.example` reviewed — no real values
