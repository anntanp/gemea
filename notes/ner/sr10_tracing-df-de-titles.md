Update ner-bibliographic.md to address SR-10:

Backtracking source of DF_DE_TITLES:
1. ```
ann@ise-d-teach03:~/fiz-ddb/notebook$ grep -rHn "pkl_vars.*DF_DE_TITLES" *.ipynb | while IFS= read -r line; do   file=$(echo "$line" | cut -d: -f1);   echo "$(stat -f '%Sm' "$line" 2>/dev/null || stat -c '%y' "$file" 2>/dev/null) $line"; done
2026-03-23 13:19:08.540273808 +0000 2023.11 NER.ipynb:230:    "pkl_vars(DF_DE_TITLES, 'data/vars/DF_DE_TITLES.pkl')"
2026-03-23 13:17:55.235800571 +0000 2023.12 Relation Extraction.ipynb:215:    "pkl_vars(DF_DE_TITLES, 'data/vars/DF_DE_TITLES.pkl')"
2026-03-23 13:13:08.041972271 +0000 2024.01 MT-QA.ipynb:238:    "pkl_vars(DF_DE_TITLES, 'data/vars/DF_DE_TITLES_20240125b.pkl')"
2025-02-26 11:19:49.985102582 +0000 2024.03 Paper NER.ipynb:366:    "pkl_vars(DF_DE_TITLES, 'data/vars/DF_DE_TITLES.pkl')"
2025-02-26 11:19:50.017102743 +0000 2024.04 Historical NER.ipynb:321:    "pkl_vars(DF_DE_TITLES, 'data/vars/DF_DE_TITLES.pkl')"
2025-02-26 11:19:50.065102982 +0000 2024.04 Universal NER.ipynb:618:    "pkl_vars(DF_DE_TITLES, 'data/vars/DF_DE_TITLES.pkl')"
2025-02-26 11:19:50.445104877 +0000 2024.11 DC NER.ipynb:321:    "pkl_vars(DF_DE_TITLES, 'data/vars/DF_DE_TITLES.pkl')"
2025-02-26 11:19:50.717106234 +0000 DDB Languages-Copy1.ipynb:205:    "pkl_vars(DF_DE_TITLES, 'data/vars/DF_DE_TITLES.pkl')"
```

Conclusion: source of file with timestamp is "2024.01 MT-QA.ipynb"

2. From "2024.01 MT-QA.ipynb", header says,

|    | DDB                           |        No. Records |
|---:| :---------------------------- | -----------------: |
|  1 | Total Titles                  |         16,805,998 |
|  2 | TEXT                          |          8,402,999 |
|  3 | Languages                     |                236 |
|  4 | No Language Tags              | 1,521,242 (18.10%) |
|  5 | Valid HTYPES (% of TEXT)      | 1,812,559 (21.57%) |
|  6 | Languages of Valid HTYPES     |                224 |
|  7 | No Language Tags (% of VALID) |   384,405 (21.21%) |
|  8 | Titles tagged+ident as 'DE'   | 4,477,641 (53.29%) |
- From 2023.12 Relation Extraction

3. From "2023.12 Relation Extraction.ipynb", header is the same as in "2023.11 NER.ipynb", which is the source of DF_DE_TITLES. 

4. From "2023.12 Relation Extraction.ipynb"
    - 4,477,641 object are titles of all TEXT objects, tagged to be in German (`dc:language`) and identified by `langid` to be in German.
    - this includes both long and short titles.
    - also found in this script: tokenization using `nlp = spacy.load
    
    