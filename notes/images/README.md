# PNG Inventory

All figures saved to `notes/images/`. Add an entry here whenever a new PNG is produced.

| Filename | Title | Description | Producing script |
|----------|-------|-------------|-----------------|
| `fig_dctype_by_era.png` | dc:type share by era (v2, 9.21M) | Stacked bar chart showing percentage share of each `dc:type` value per time-period era stratum | `scripts/ner/sr11_dctype_by_era.py` |
| `fig_silver_tiers.png` | Silver-tier composition by era | Stacked bar chart of tier-1 and tier-2 silver corpus sizes per era (tier-0 annotated but not plotted) | `scripts/sr06_plot_silver_tiers.py` |
| `fig_title_lengths.png` | Title-length distribution over time (v2, BPE) | Median all-token and content-token title lengths per year bucket, plotted as a panel figure | `scripts/ner/sr10_analyse_title_lengths.py` |
| `fig_title_lengths_bw.html` | Title-length distribution — B&W variant | Same as `fig_title_lengths.png` but rendered as interactive HTML with black-and-white theme | `scripts/ner/sr10_analyse_title_lengths.py` |
| `fig_token_distribution.png` | Raw token-count distribution (v2, BPE) | Histogram of `all_tokens` and `content_tokens` across the DE-titles corpus (9.21M, xlm-roberta BPE), used to identify short/medium/long breakpoints | `scripts/ner/sr10_explore_token_distribution.py` |
| `hierarchy_type_counts.png` | Hierarchy-type breakdown (Sector 2) | Side-by-side horizontal bar charts of primary and secondary object counts per `hierarchy_type`, including UNK (null) | `scripts/analysis/count_hierarchy_types.py` |
| `htype_title_quality.png` | Hierarchy-type title quality (generic%) | Horizontal stacked bar showing fraction of generic/null titles per candidate htype (strong = red, partial = orange) | `scripts/analysis/validate_htype_title_quality.py` |
| `title_class_breakdown.png` | Title classification by hierarchy_type | Stacked bar of work_title / section_label / physical_label percentages per htype; green % = share usable for GND Werk linking | `scripts/analysis/filter_content_titles.py` |
| `lang_counts.png` | Language distribution (Sector 2) | Horizontal bar chart of object counts per language code; multi-value `lang` fields are exploded; red bar marks records with no language | `scripts/analysis/count_lang.py` |
| `lang_by_year.png` | Language distribution by decade (Sector 2) | Stacked area chart of object counts per language × decade bucket; year from `dc_issued`; 82.6% of objects have a valid year | `scripts/analysis/lang_by_year.py` |
| `lang_by_year_no_top1.png` | Language distribution by decade — German excluded | Same as `lang_by_year.png` but with the top-1 language (ger) removed to reveal minority-language trends | `scripts/analysis/lang_by_year.py` |
| `wordcloud_book.png` | "Book" word cloud by language | Word cloud of the word "book" in each DDB language, sized by object count; covers 99.7% of objects across 39 language codes | `scripts/analysis/wordcloud_book.py` |
| `ddb_ids_sector_counts.png` | DDB ID file listing on teach03 | Terminal screenshot showing `ls -al` and `wc -l` output for the 7 sector ID files (27.3M total) on `ise-d-teach03:/data/ddb/data/ids/` | screenshot (manual) |
