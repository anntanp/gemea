# Purpose:      Generate per-theme standalone HTML files from fig_title_lengths.jsx.
#               Reads the canonical JSX source, strips ES-module import lines and the
#               'export default' keyword, inlines title-length-analysis.json as
#               window.TITLE_DATA, and wraps each theme in a self-contained HTML shell
#               (React + Babel from CDN, Google Fonts where required).
#               Optionally converts a Markdown write-up to HTML and appends it below
#               the chart inside a <details> block.
# Usage:        python scripts/py/sr10_render_title_viz.py
#               python scripts/py/sr10_render_title_viz.py --theme retro
#               python scripts/py/sr10_render_title_viz.py \
#                   --jsx     notes/images/fig_title_lengths.jsx \
#                   --json    notes/images/title-length-analysis.json \
#                   --writeup notes/ner/fig_title_lengths_writeup.md \
#                   --output-dir notes/images \
#                   --theme all
# Inputs:       notes/images/fig_title_lengths.jsx          (canonical source)
#               notes/images/title-length-analysis.json     (sr10_analyse_title_lengths.py)
#               notes/ner/fig_title_lengths_writeup.md          (optional write-up)
# Outputs:      notes/images/fig_title_lengths_leather.html
#               notes/images/fig_title_lengths_retro.html
#               notes/images/fig_title_lengths_lighter.html
#               notes/images/fig_title_lengths_vscode_dark.html
# Dependencies: markdown (pip install markdown)
# Assumptions:  fig_title_lengths.jsx uses a THEMES object keyed by theme name and
#               reads data + theme via window.TITLE_DATA / window.CHART_THEME.
#               The component is named TitleLengthLibrary and exported as default.

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Optional

import markdown as md_lib

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
log = logging.getLogger("sr10_render_title_viz")

# ── theme metadata ────────────────────────────────────────────────────────────
# bg:           body background colour (matches T.bg in the THEMES object of the JSX).
# font_link:    <link> tag for Google Fonts, or empty string for system fonts.
# wu_bg:        write-up panel background colour.
# wu_text:      write-up body text colour.
# wu_muted:     write-up secondary / muted text colour.
# wu_heading:   write-up heading colour.
# wu_link:      write-up anchor colour.
# wu_border:    write-up hr / table border colour.
# wu_code_bg:   write-up inline code background colour.
# wu_summary:   <summary> toggle text colour.

THEMES: dict[str, dict[str, str]] = {
    "leather": {
        "title":      "DDB Title Lengths — Leather",
        "bg":         "#0f0804",
        "font_link":  "",
        "wu_bg":      "#1a1008",
        "wu_text":    "#c8a860",
        "wu_muted":   "#8a6840",
        "wu_heading": "#e0c880",
        "wu_link":    "#e0b060",
        "wu_border":  "#3d2810",
        "wu_code_bg": "#2a1a08",
        "wu_summary": "#c8a860",
    },
    "retro": {
        "title":      "DDB Title Lengths — Retro",
        "bg":         "#000033",
        "font_link":  (
            '<link rel="stylesheet" '
            'href="https://fonts.googleapis.com/css2?family=VT323&display=swap">'
        ),
        "wu_bg":      "#000028",
        "wu_text":    "#00dddd",
        "wu_muted":   "#008888",
        "wu_heading": "#FFD700",
        "wu_link":    "#FFD700",
        "wu_border":  "#003355",
        "wu_code_bg": "#001122",
        "wu_summary": "#00ffff",
    },
    "lighter": {
        "title":      "DDB Title Lengths — Lighter",
        "bg":         "#f6f8fa",
        "font_link":  (
            '<link rel="stylesheet" '
            'href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600&display=swap">'
        ),
        "wu_bg":      "#ffffff",
        "wu_text":    "#24292f",
        "wu_muted":   "#57606a",
        "wu_heading": "#1f2328",
        "wu_link":    "#0969da",
        "wu_border":  "#d0d7de",
        "wu_code_bg": "#f0f2f4",
        "wu_summary": "#0969da",
    },
    "vscode_dark": {
        "title":      "DDB Title Lengths — VS Code Dark",
        "bg":         "#1f1f1f",
        "font_link":  "",
        "wu_bg":      "#252526",
        "wu_text":    "#cccccc",
        "wu_muted":   "#858585",
        "wu_heading": "#e0e0e0",
        "wu_link":    "#4e94ce",
        "wu_border":  "#3e3e42",
        "wu_code_bg": "#1e1e1e",
        "wu_summary": "#9cdcfe",
    },
}

# Width of the SVG chart: START_X*2 + 21*(BOOK_W+BOOK_GAP) - BOOK_GAP = 1144px.
# The write-up panel is constrained to the same width so it aligns with the chart.
CHART_WIDTH_PX = 1144


# ── Markdown → HTML ───────────────────────────────────────────────────────────

def render_writeup(md_path: Path) -> str:
    """Convert a Markdown file to an HTML fragment.

    Args:
        md_path: Path to the .md source file.

    Returns:
        HTML string (no <html>/<body> wrapper) ready to embed in a <div>.
    """
    text = md_path.read_text(encoding="utf-8")
    return md_lib.markdown(text, extensions=["tables", "toc"])


# ── JSX transformation ────────────────────────────────────────────────────────

def extract_component_body(jsx_text: str) -> str:
    """Strip ES-module imports and 'export default' from JSX source.

    The HTML shell supplies React globals and window.TITLE_DATA, so ES imports
    are not needed.  'export default' is removed so the function declaration is
    a plain named function that Babel can call directly.

    Args:
        jsx_text: Raw content of fig_title_lengths.jsx.

    Returns:
        Transformed source ready to embed inside a <script type="text/babel">.
    """
    out: list[str] = []
    for line in jsx_text.splitlines():
        if re.match(r"^\s*import\s+", line):
            continue
        line = re.sub(r"^export\s+default\s+", "", line)
        out.append(line)
    return "\n".join(out).strip()


# ── HTML assembly ─────────────────────────────────────────────────────────────

def build_html(
    theme_name: str,
    meta: dict[str, str],
    json_str: str,
    component_body: str,
    writeup_html: Optional[str] = None,
) -> str:
    """Assemble a self-contained HTML file for one theme.

    Uses string concatenation rather than str.format() to avoid escaping the
    many curly braces inside the JSX component body.

    Args:
        theme_name:     Key into THEMES (e.g. 'retro').
        meta:           Theme metadata dict (title, bg, font_link, wu_* colours).
        json_str:       Compact JSON string for window.TITLE_DATA.
        component_body: Transformed JSX source (imports + export stripped).
        writeup_html:   Pre-rendered Markdown HTML to embed below the chart, or None.

    Returns:
        Complete HTML document as a string.
    """
    # Indent component body by 4 spaces for readability inside the <script> block.
    indented_body = "\n".join(
        "    " + line if line.strip() else ""
        for line in component_body.splitlines()
    )

    writeup_css = (
        f"    details.writeup-section {{"
        f" width: {CHART_WIDTH_PX}px; margin-top: 24px; }}\n"
        f"    details.writeup-section summary {{"
        f" cursor: pointer; color: {meta['wu_summary']};"
        f" font-size: 13px; padding: 6px 0; list-style: none; }}\n"
        f"    details.writeup-section summary::-webkit-details-marker {{ display:none; }}\n"
        f"    details.writeup-section summary::before {{ content: '▶  '; font-size: 10px; }}\n"
        f"    details.writeup-section[open] summary::before {{ content: '▼  '; }}\n"
        f"    .writeup {{"
        f" background: {meta['wu_bg']}; color: {meta['wu_text']};"
        f" padding: 28px 36px; margin-top: 8px;"
        f" border: 1px solid {meta['wu_border']}; border-radius: 4px;"
        f" font-size: 14px; line-height: 1.75; }}\n"
        f"    .writeup h1 {{ color: {meta['wu_heading']}; font-size: 20px;"
        f" border-bottom: 1px solid {meta['wu_border']}; padding-bottom: 8px;"
        f" margin-top: 0; }}\n"
        f"    .writeup h2 {{ color: {meta['wu_heading']}; font-size: 16px;"
        f" border-bottom: 1px solid {meta['wu_border']}; padding-bottom: 4px;"
        f" margin-top: 32px; }}\n"
        f"    .writeup h3 {{ color: {meta['wu_heading']}; font-size: 14px;"
        f" margin-top: 24px; }}\n"
        f"    .writeup h4 {{ color: {meta['wu_muted']}; font-size: 13px;"
        f" margin-top: 16px; }}\n"
        f"    .writeup a {{ color: {meta['wu_link']}; text-decoration: none;"
        f" border-bottom: 1px dotted {meta['wu_link']}; }}\n"
        f"    .writeup a:hover {{ border-bottom-style: solid; }}\n"
        f"    .writeup code {{ background: {meta['wu_code_bg']};"
        f" color: {meta['wu_text']}; padding: 1px 5px; border-radius: 3px;"
        f" font-size: 12px; }}\n"
        f"    .writeup hr {{ border: none;"
        f" border-top: 1px solid {meta['wu_border']}; margin: 24px 0; }}\n"
        f"    .writeup table {{ border-collapse: collapse; width: 100%;"
        f" font-size: 13px; margin: 16px 0; }}\n"
        f"    .writeup th {{ background: {meta['wu_code_bg']};"
        f" color: {meta['wu_heading']}; text-align: left;"
        f" padding: 6px 12px; border: 1px solid {meta['wu_border']}; }}\n"
        f"    .writeup td {{ padding: 5px 12px;"
        f" border: 1px solid {meta['wu_border']}; color: {meta['wu_text']}; }}\n"
        f"    .writeup em {{ color: {meta['wu_muted']}; }}\n"
        f"    .writeup strong {{ color: {meta['wu_heading']}; }}\n"
        f"    .writeup ul, .writeup ol {{ padding-left: 22px; }}\n"
        f"    .writeup li {{ margin-bottom: 4px; }}\n"
        f"    .writeup p {{ margin: 10px 0; }}\n"
    )

    head_lines = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '  <meta charset="UTF-8">',
        f'  <title>{meta["title"]}</title>',
        '  <script src="https://unpkg.com/react@18/umd/react.development.js"></script>',
        '  <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>',
        '  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>',
    ]
    if meta["font_link"]:
        head_lines.append(f"  {meta['font_link']}")
    head_lines += [
        "  <style>",
        (
            f'    body {{ margin: 0; background: {meta["bg"]}; '
            f"display: flex; flex-direction: column; align-items: center; padding: 40px 0; }}"
        ),
        writeup_css,
        "  </style>",
        "</head>",
    ]

    body_lines = [
        "<body>",
        '  <div id="root"></div>',
        "",
        "  <script>",
        f"    window.TITLE_DATA  = {json_str};",
        f"    window.CHART_THEME = '{theme_name}';",
        "  </script>",
        "",
        '  <script type="text/babel">',
        "    const { useRef, useState } = React;",
        "    const rawData = window.TITLE_DATA;",
        "",
        indented_body,
        "",
        "    ReactDOM.createRoot(document.getElementById('root'))",
        "      .render(<TitleLengthLibrary />);",
        "  </script>",
    ]

    if writeup_html:
        body_lines += [
            "",
            '  <details class="writeup-section">',
            "    <summary>Write-up</summary>",
            '    <div class="writeup">',
            writeup_html,
            "    </div>",
            "  </details>",
        ]

    body_lines += [
        "</body>",
        "</html>",
        "",
    ]

    return "\n".join(head_lines + body_lines)


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    here = Path(__file__).parent.parent.parent  # repo root (scripts/py/../../)
    images = here / "notes" / "images"

    parser = argparse.ArgumentParser(
        description=(
            "Generate per-theme standalone HTML from fig_title_lengths.jsx. "
            "Reads the JSX, inlines JSON data, and writes one HTML file per theme."
        )
    )
    parser.add_argument(
        "--jsx",
        default=str(images / "fig_title_lengths.jsx"),
        help="Path to fig_title_lengths.jsx (default: notes/images/fig_title_lengths.jsx)",
    )
    parser.add_argument(
        "--json",
        default=str(images / "title-length-analysis.json"),
        help="Path to title-length-analysis.json (default: notes/images/title-length-analysis.json)",
    )
    parser.add_argument(
        "--writeup",
        default=str(here / "notes" / "fig_title_lengths_writeup.md"),
        help="Path to write-up Markdown file (default: notes/ner/fig_title_lengths_writeup.md)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(images),
        help="Directory to write HTML files into (default: notes/images/)",
    )
    parser.add_argument(
        "--theme",
        default="all",
        choices=[*THEMES, "all"],
        help="Theme to render, or 'all' (default: all)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    jsx_path     = Path(args.jsx)
    json_path    = Path(args.json)
    writeup_path = Path(args.writeup)
    out_dir      = Path(args.output_dir)

    # Validate inputs
    if not jsx_path.is_file():
        log.error("JSX source not found: %s", jsx_path)
        return 1
    if not json_path.is_file():
        log.error("JSON data not found: %s", json_path)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)

    # Load and re-serialise JSON (compact, ASCII-safe for embedding in JS)
    data     = json.loads(json_path.read_text(encoding="utf-8"))
    json_str = json.dumps(data, ensure_ascii=True, separators=(",", ":"))
    log.info("loaded JSON: %d top-level keys", len(data))

    jsx_text       = jsx_path.read_text(encoding="utf-8")
    component_body = extract_component_body(jsx_text)
    log.info("extracted component body: %d lines", component_body.count("\n") + 1)

    writeup_html: Optional[str] = None
    if writeup_path.is_file():
        writeup_html = render_writeup(writeup_path)
        log.info("rendered write-up: %d chars", len(writeup_html))
    else:
        log.warning("write-up not found, skipping: %s", writeup_path)

    themes = list(THEMES) if args.theme == "all" else [args.theme]

    for theme_name in themes:
        meta     = THEMES[theme_name]
        html     = build_html(theme_name, meta, json_str, component_body, writeup_html)
        out_path = out_dir / f"fig_title_lengths_{theme_name}.html"
        out_path.write_text(html, encoding="utf-8")
        log.info("wrote %s (%d bytes)", out_path, len(html.encode("utf-8")))

    return 0


if __name__ == "__main__":
    sys.exit(main())
