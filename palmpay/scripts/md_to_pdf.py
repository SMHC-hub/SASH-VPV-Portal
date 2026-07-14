#!/usr/bin/env python3
"""Convert a Markdown file to PDF (business docs)."""
from __future__ import annotations

import sys
from pathlib import Path

import markdown
from xhtml2pdf import pisa

ROOT = Path(__file__).resolve().parents[1]

CSS = """
@page { size: A4; margin: 2cm; }
body {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10pt;
  line-height: 1.45;
  color: #1a1a1a;
}
h1 { font-size: 20pt; color: #1a365d; margin-top: 0; border-bottom: 2px solid #2c5282; padding-bottom: 8px; }
h2 { font-size: 14pt; color: #2c5282; margin-top: 22px; page-break-after: avoid; }
h3 { font-size: 11pt; color: #2d3748; margin-top: 16px; }
p, li { margin: 6px 0; }
ul, ol { margin: 8px 0 8px 20px; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 9pt; }
th, td { border: 1px solid #cbd5e0; padding: 5px 7px; text-align: left; vertical-align: top; }
th { background-color: #edf2f7; font-weight: bold; }
hr { border: none; border-top: 1px solid #e2e8f0; margin: 18px 0; }
strong { color: #1a202c; }
em { color: #4a5568; }
code { font-family: Courier, monospace; font-size: 9pt; background: #f7fafc; padding: 1px 4px; }
"""


def md_to_pdf(md_path: Path, pdf_path: Path) -> None:
    text = md_path.read_text(encoding="utf-8")
    body = markdown.markdown(text, extensions=["tables", "fenced_code", "nl2br"])
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/><style>{CSS}</style></head>
<body>{body}</body></html>"""
    with pdf_path.open("wb") as out:
        status = pisa.CreatePDF(html, dest=out, encoding="utf-8")
    if status.err:
        raise RuntimeError(f"PDF generation failed with {status.err} error(s)")


def main() -> None:
    md_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "business_plan.md"
    pdf_path = Path(sys.argv[2]) if len(sys.argv) > 2 else md_path.with_suffix(".pdf")
    md_to_pdf(md_path.resolve(), pdf_path.resolve())
    print(f"Created: {pdf_path}")


if __name__ == "__main__":
    main()
