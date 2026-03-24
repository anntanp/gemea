# SR-05 — Trailing Period Abbreviation List

Curated list of German/Latin abbreviation tokens used in [`sr05_validate_trailing_period.py`](../../scripts/sr05_validate_trailing_period.py) to classify a trailing period as `ABBREV` rather than `ISBD_CLOSE`. A title ending with one of these tokens followed by `.` is not an ISBD area-close.

Source: `ABBREV_RE` in [`sr05_validate_trailing_period.py`](../../scripts/sr05_validate_trailing_period.py).

---

## 1. Role / editorial

| Token | Meaning |
|---|---|
| `Hrsg.` | Herausgeber (editor) |
| `Hg.` | Herausgeber (short form) |
| `Verf.` | Verfasser (author) |
| `bearb.` | bearbeitet (revised/edited by) |

## 2. Edition / printing

| Token | Meaning |
|---|---|
| `erg.` | ergänzte (supplemented) |
| `erw.` | erweiterte (expanded) |
| `verb.` | verbesserte (improved) |
| `überarb.` | überarbeitete (revised) |
| `Aufl.` | Auflage (edition) |
| `Ausg.` | Ausgabe (issue/edition) |

## 3. Volume / part / numbering

| Token | Meaning |
|---|---|
| `Bd.` | Band (volume) |
| `Bde.` | Bände (volumes, plural) |
| `Bdn.` | Bänden (volumes, dative) |
| `Teil.` | Teil (part) |
| `Teile.` | Teile (parts, plural) |
| `Nr.` | Nummer (number) |
| `Nrn.` | Nummern (numbers, plural) |
| `Jg.` | Jahrgang (annual volume) |
| `Jgg.` | Jahrgänge (annual volumes, plural) |
| `H.` | Heft (issue/fascicle) |
| `Heft.` | Heft (long form) |
| `Vol.` | Volume (Latin/English) |
| `Vols.` | Volumes (plural) |

## 4. Academic / personal titles

| Token | Meaning |
|---|---|
| `Dr.` | Doktor |
| `Prof.` | Professor |
| `St.` | Sankt / Saint |

## 5. Figure / illustration

| Token | Meaning |
|---|---|
| `Abb.` | Abbildung (figure) |
| `Tab.` | Tabelle (table) |
| `Fig.` | Figur / Figure |
| `Taf.` | Tafel (plate) |

## 6. Common connective abbreviations

| Token | Meaning |
|---|---|
| `u.a.` | und andere (and others) |
| `usw.` | und so weiter (etc.) |
| `bzw.` | beziehungsweise (or / respectively) |
| `etc.` | et cetera |
| `vgl.` | vergleiche (cf.) |
| `enth.` | enthält (contains) |
| `ink.` / `inkl.` | inklusive (including) |

## 7. Format / physical description

| Token | Meaning |
|---|---|
| `Kl.` | Klein (small format) |
| `Fol.` | Folio |
| `qu.` | quer (oblong/landscape) |
| `illustr.` / `ill.` | illustriert (illustrated) |

## 8. Approximation

| Token | Meaning |
|---|---|
| `ca.` | circa |
| `approx.` | approximately |

## 9. Months

`Jan.` `Feb.` `Mär.` `Mar.` `Apr.` `Mai.` `Jun.` `Jul.` `Aug.` `Sep.` `Okt.` `Oct.` `Nov.` `Dez.` `Dec.`

## 10. Days of the week

`Mo.` `Di.` `Mi.` `Do.` `Fr.` `Sa.` `So.`
