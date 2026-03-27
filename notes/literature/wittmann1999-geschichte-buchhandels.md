# Geschichte des deutschen Buchhandels

**Citation**: Wittmann, R. (1999). *Geschichte des deutschen Buchhandels* (2nd ed.). C.H. Beck.
**ISBN**: 3-406-42104-0
**Track**: A — Library Science / Historical context

---

## Scope

Standard history of the German book trade. Covers the full arc from manuscript culture through the 20th century. Relevant here for the Enlightenment transformation of German publishing in the late 18th century.

---

## Chapters consulted

| Chapter | Title | Start page | Assessed |
|---------|-------|-----------|---------|
| IV | Die Entstehung des modernen Buchhandels: Nettohandel, Nachdruck, Reformversuche | 121 | Read (p. 122); quantitative data on Latin decline 1740–1800 — directly citable for SR-06 |
| V | Der Dichter auf dem Markt: die Entstehung des freien Schriftstellers | 155 | Read (p. 159); authorship economics only — no title-page content |

---

## Chapter V — "Der Dichter auf dem Markt: die Entstehung des freien Schriftstellers"

**Pages consulted:** 155, 159

### Verbatim (p. 159)

> Vom Beginn der sechziger Jahre an, als der neue belletristische Lesegeschmack sich in Mittel- und Norddeutschland immer rascher ausbreitete, als die Nettohändler die Gunst der Stunde nutzten, die begehrte literarische Ware verstärkt anboten und zur Sicherung des nötigen Nachschubs nach geschwind und billig produzierenden Zulieferern Ausschau hielten, erkannten die Autoren immer deutlicher, was der Preis dafür war, sich von den ständischen Fesseln zu lösen und das Publikum als alleinigen Souverän anzuerkennen.

### What this passage says

From the 1760s onward, the spread of belletristic reading taste in central and northern Germany drove *Nettohändler* (cash-based booksellers, as opposed to the old exchange/fair system) to demand fast, cheap production from suppliers. Authors in turn recognized the market as the new sovereign, replacing the patron.

### What it supports

- **Periodization**: the commercial shift begins in the 1760s and accelerates through the 1770s–1780s — consistent with the token-length drop visible in the 1775–1799 bucket of `DF_DE_TITLES`.
- **Mechanism**: market pressure for throughput and low cost.
- **Geography**: Mittel- und Norddeutschland — consistent with DDB's coverage.

### What it does not support

- No mention of title-page format, title length, or bibliographic conventions.
- Cannot be cited as evidence that title pages shortened or that Baroque descriptive titles declined.
- The chapter is about authorship economics (shift from patronage to market), not bibliographic practice.

---

## Chapter IV — "Die Entstehung des modernen Buchhandels: Nettohandel, Nachdruck, Reformversuche"

**Pages consulted:** 122

### Verbatim (p. 122)

> Parallel zum rapiden allgemeinen Wachstum der Buchproduktion im letzten Jahrhundertdrittel ist ein rascher Niedergang der jahrhundertelang unverzichtbaren lingua franca der Gelehrtenrepublik festzustellen. Nun bildete sich eine deutsche Wissenschaftssprache mit differenzierter Begrifflichkeit heraus. Noch 1740 wurden 27,7% aller Meßnovitäten in lateinischer Sprache gedruckt — dabei ist die umfangreiche katholisch-theologische Produktion noch kaum berücksichtigt, 1770 hat sich der Prozentsatz auf 14,25% fast halbiert, und wiederum dreißig Jahre später ist er auf unbedeutende 3,97% geschrumpft.

### What this passage says

Parallel to the rapid growth of book production in the last third of the 18th century, Latin — the centuries-long *lingua franca* of the Republic of Letters — declined sharply. A German scholarly language with differentiated terminology emerged. Quantitative data from Leipzig fair new titles (*Meßnovitäten*):

| Year | Latin share of Meßnovitäten |
|------|-----------------------------|
| 1740 | 27.7% |
| 1770 | 14.25% (nearly halved) |
| 1800 | 3.97% (negligible) |

Note: Catholic theological production is described as barely counted in these figures, suggesting the true Latin share was somewhat higher.

### What this passage supports

- **SR-06 (Latin scope):** directly supports the ~0.5% Latin prevalence finding in `DF_DE_TITLES`. By 1800 Latin was already at 3.97% of new German book production; a corpus of DDB holdings (predominantly 19th–20th century) would inherit near-zero Latin prevalence. This is the strongest external anchor for the no-Latin-stratum decision.
- **SR-10 (token-length shift):** Latin scholarly titles (*dissertatio*, *tractatus*, *de* + ablative constructions) are structurally long. Their disappearance from the German book market between 1740 and 1800 contributes mechanically to shorter median token counts in the 1775–1799 bucket — a secondary, indirect connection.
- **Periodization:** the shift is clearly underway by 1770 and essentially complete by 1800 — consistent with both the token-length drop in sr10 and the pre-1700 / 1700–1800 stratum boundary in SR-08.

### What it does not support

- No direct statement about title-page length or bibliographic conventions.
- The data source (*Meßnovitäten* = Leipzig fair catalogues) covers new German book production, not the DDB corpus specifically. The proportion in DDB may differ if DDB over- or under-represents pre-1800 holdings.

---

## Decision for sr10 / paper

**Do not cite Wittmann for the token-length claim.** The passage establishes commercial context and periodization but makes no claim about title-page structure or length. Citing it for the length observation would overreach.

**Use option 2 instead**: report the token-length shift as an empirical finding from `DF_DE_TITLES` and note that it is *consistent with* the known commercialization of German publishing in the late 18th century, without sourcing the bibliographic convention claim to Wittmann.

Suggested framing for the paper:

> The post-1775 contraction in title token length is consistent with the well-documented commercialization of German publishing from the 1760s onward (Wittmann 1999, p. 159), though the quantitative evidence is drawn from `DF_DE_TITLES` itself; no source making the title-length claim explicitly has been identified.

Or, more cleanly, omit the citation entirely and treat the length distribution as a corpus observation.

---

## If a stronger source is needed later

- *Archiv für Geschichte des Buchwesens* (Börsenverein des Deutschen Buchhandels) — primary journal for early modern German book history; search terms: *Titelblatt*, *Titelei*, *barocke Titelform*, *Titelseite 18. Jahrhundert*.
- Johann Goldfriedrich, *Geschichte des deutschen Buchhandels* (4 vols., 1886–1913) — older but bibliographically detailed; may contain direct discussion of title-page conventions.

---

## BibTeX

```bibtex
@book{wittmann1999buchhandel,
  title     = {{Geschichte des deutschen Buchhandels}},
  author    = {Wittmann, Reinhard},
  edition   = {2},
  publisher = {C.H. Beck},
  year      = {1999},
  isbn      = {3-406-42104-0}
}
```
