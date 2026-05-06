# TPDL 2026 — Short Paper Draft

## Compile

Copy llncs.cls and splncs04.bst from ../iswc-2026/ first:

    cp ../iswc-2026/llncs.cls ../iswc-2026/splncs04.bst .
    pdflatex 00-main && bibtex 00-main && pdflatex 00-main && pdflatex 00-main

## Files

| File | Section |
|---|---|
| 00-main.tex | Document root, title (BLANK), authors (BLANK) |
| 00-abstract.tex | Abstract |
| 10-intro.tex | §1 Introduction |
| 20-related.tex | §2 Related Work |
| 30-methodology.tex | §3 Methodology (three-layer dispatch) |
| 40-results.tex | §4 Results |
| 50-discussion.tex | §5 Discussion |
| 60-conclusion.tex | §6 Conclusion |
| 99-bibliography.bib | Merged bib from babel-ddb/paper_3 + iswc-2026 |

## Open todos (red in PDF)

- Title and authors
- GitHub URL for pipeline scripts
- Confirm goethe-faust corpus is public
- Fill Table 2 (alignment coverage) from alignment_ddbedm_mocho.csv
- Add RDA Toolkit, RiC-O, OAEI, BIBFRAME, VRA Core bib entries
- Confirm mocho version tag
- Pipeline figure (30-methodology.tex §3.2)
- Top-10 ignored properties figure (40-results.tex §4.3)
- Spot-check: sector distribution of pilot corpus
- Confirm dc:type distinct value count
