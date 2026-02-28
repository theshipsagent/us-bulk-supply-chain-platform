"""HTML renderer — converts assembled Markdown to publication-quality HTML."""

import logging
from datetime import datetime
from pathlib import Path

import markdown

logger = logging.getLogger(__name__)

CSS = """
/* ── CSS Variables ── */
:root {
    --navy: #003366;
    --navy-dark: #001f3f;
    --navy-light: #1a4d80;
    --accent: #0066cc;
    --accent-light: #e8f0fe;
    --text: #2c3e50;
    --text-light: #5a6c7d;
    --bg: #f7f8fa;
    --white: #ffffff;
    --border: #dce1e8;
    --border-light: #e8ecf1;
    --success: #27ae60;
    --warning: #f39c12;
    --danger: #e74c3c;
    --info: #2980b9;
    --shadow: 0 2px 12px rgba(0, 51, 102, 0.08);
    --shadow-lg: 0 4px 24px rgba(0, 51, 102, 0.12);
}

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }

body {
    font-family: 'Calibri', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    line-height: 1.75;
    margin: 0;
    padding: 0;
    color: var(--text);
    background: var(--bg);
    font-size: 15px;
    -webkit-font-smoothing: antialiased;
}

.report-wrapper {
    max-width: 1000px;
    margin: 0 auto;
    padding: 0 20px;
}

/* ── Report Header ── */
.report-header {
    background: linear-gradient(135deg, var(--navy-dark) 0%, var(--navy) 50%, var(--navy-light) 100%);
    color: var(--white);
    padding: 48px 0 40px;
    margin-bottom: 0;
    border-bottom: 4px solid var(--accent);
}

.report-header .report-wrapper {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.report-header h1 {
    font-size: 32px;
    font-weight: 700;
    margin: 0;
    padding: 0;
    border: none;
    color: var(--white);
    letter-spacing: -0.5px;
    line-height: 1.2;
}

.report-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
    margin-top: 8px;
}

.report-meta span {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.85);
}

.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

.badge-proprietary {
    background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: var(--white);
}

.badge-version {
    background: var(--accent);
    color: var(--white);
}

/* ── Table of Contents ── */
.toc-container {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 28px 32px;
    margin: 0 auto;
    max-width: 1000px;
    box-shadow: var(--shadow);
}

.toc-container h2 {
    font-size: 16px;
    font-weight: 700;
    color: var(--navy);
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin: 0 0 16px 0;
    padding: 0 0 10px 0;
    border-bottom: 2px solid var(--navy);
    border-left: none;
}

.toc-container ul {
    list-style: none;
    padding: 0;
    margin: 0;
    columns: 2;
    column-gap: 32px;
}

.toc-container li {
    margin: 0;
    padding: 6px 0;
    border-bottom: 1px solid var(--border-light);
    break-inside: avoid;
}

.toc-container a {
    color: var(--navy);
    text-decoration: none;
    font-size: 14px;
    font-weight: 500;
    transition: color 0.15s;
}

.toc-container a:hover {
    color: var(--accent);
    text-decoration: underline;
}

.toc-container ul ul {
    columns: 1;
    padding-left: 20px;
    margin-top: 4px;
}

.toc-container ul ul li {
    border-bottom: none;
    padding: 2px 0;
}

.toc-container ul ul a {
    font-weight: 400;
    color: var(--text-light);
    font-size: 13px;
}

/* ── Main Content ── */
.report-body {
    background: var(--white);
    padding: 48px 56px;
    margin: 0 auto;
    max-width: 1000px;
    box-shadow: var(--shadow);
    border: 1px solid var(--border);
    border-top: none;
}

/* ── Headings ── */
h1 {
    color: var(--navy);
    font-size: 28px;
    font-weight: 700;
    border-bottom: 3px solid var(--navy);
    padding-bottom: 12px;
    margin: 48px 0 24px 0;
    letter-spacing: -0.3px;
}

h2 {
    color: var(--navy);
    font-size: 22px;
    font-weight: 600;
    margin: 40px 0 18px 0;
    border-left: 4px solid var(--navy);
    padding-left: 16px;
    line-height: 1.3;
}

h3 {
    color: var(--navy-light);
    font-size: 18px;
    font-weight: 600;
    margin: 32px 0 12px 0;
}

h4 {
    color: var(--text);
    font-size: 15px;
    font-weight: 700;
    margin: 24px 0 8px 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-size: 13px;
}

/* ── Paragraphs & Text ── */
p {
    margin: 14px 0;
    text-align: justify;
    hyphens: auto;
}

strong {
    color: var(--navy);
    font-weight: 600;
}

em {
    color: var(--text-light);
}

a {
    color: var(--accent);
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: border-color 0.15s;
}

a:hover {
    border-bottom-color: var(--accent);
}

/* ── Tables ── */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 24px 0;
    font-size: 13.5px;
    border: 1px solid var(--border);
    border-radius: 4px;
    overflow: hidden;
}

thead {
    background: var(--navy);
}

th {
    background: var(--navy);
    color: var(--white);
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
    font-size: 11.5px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    border-bottom: 2px solid var(--navy-dark);
    white-space: nowrap;
}

td {
    padding: 9px 14px;
    border-bottom: 1px solid var(--border-light);
    vertical-align: top;
}

tr:nth-child(even) {
    background: #f8f9fb;
}

tr:hover {
    background: var(--accent-light);
}

/* Right-align numeric columns */
td:last-child, th:last-child {
    text-align: right;
}

/* ── Lists ── */
ul, ol {
    margin: 14px 0;
    padding-left: 28px;
}

li {
    margin: 5px 0;
    line-height: 1.65;
}

li > strong {
    color: var(--navy);
}

/* ── Blockquotes / Callouts ── */
blockquote {
    border-left: 4px solid var(--accent);
    margin: 24px 0;
    padding: 16px 24px;
    background: var(--accent-light);
    border-radius: 0 4px 4px 0;
    color: var(--text);
    font-style: normal;
}

blockquote p {
    margin: 6px 0;
    text-align: left;
}

blockquote strong {
    color: var(--navy);
}

/* ── Code ── */
code {
    background: #f0f2f5;
    padding: 2px 7px;
    border-radius: 3px;
    font-size: 13px;
    font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
    color: var(--navy);
}

pre {
    background: #f0f2f5;
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 16px 20px;
    overflow-x: auto;
    font-size: 13px;
    line-height: 1.5;
}

pre code {
    background: none;
    padding: 0;
    border-radius: 0;
}

/* ── Horizontal Rules (Chapter Breaks) ── */
hr {
    border: none;
    border-top: 2px solid var(--navy);
    margin: 56px 0;
    position: relative;
}

hr::after {
    content: '';
    display: block;
    width: 60px;
    height: 4px;
    background: var(--accent);
    margin: -3px auto 0;
}

/* ── KPI Dashboard ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    margin: 28px 0;
}

.kpi-card {
    background: linear-gradient(135deg, var(--navy) 0%, var(--navy-light) 100%);
    color: var(--white);
    padding: 20px;
    border-radius: 6px;
    text-align: center;
    box-shadow: var(--shadow);
}

.kpi-value {
    font-size: 28px;
    font-weight: 700;
    line-height: 1.2;
    margin-bottom: 4px;
}

.kpi-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    opacity: 0.85;
}

/* ── Report Footer ── */
.report-footer {
    background: var(--navy-dark);
    color: rgba(255, 255, 255, 0.7);
    text-align: center;
    font-size: 12px;
    padding: 24px 20px;
    margin-top: 0;
    max-width: 1000px;
    margin-left: auto;
    margin-right: auto;
    border: 1px solid var(--border);
    border-top: none;
}

.report-footer .footer-line {
    margin: 4px 0;
}

.report-footer .footer-brand {
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
}

/* ── Print Styles ── */
@media print {
    body {
        background: white;
        font-size: 11pt;
        color: #000;
    }

    .report-wrapper {
        max-width: none;
        padding: 0;
    }

    .report-header {
        background: var(--navy) !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
        padding: 30px 40px;
        page-break-after: always;
    }

    .toc-container {
        box-shadow: none;
        border: 1px solid #ccc;
        page-break-after: always;
    }

    .report-body {
        box-shadow: none;
        border: none;
        padding: 0 20px;
    }

    .report-footer {
        background: none !important;
        color: #666;
        border-top: 1px solid #ccc;
        padding: 12px 0;
    }

    hr {
        page-break-after: always;
        border: none;
        margin: 0;
    }

    hr::after {
        display: none;
    }

    h1, h2, h3 {
        page-break-after: avoid;
    }

    table {
        page-break-inside: avoid;
        font-size: 10pt;
    }

    thead {
        background: var(--navy) !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }

    th {
        background: var(--navy) !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }

    blockquote {
        border-left: 3px solid var(--navy);
        background: #f5f5f5 !important;
    }

    a { color: var(--navy); }
    a[href]::after { content: none; }

    .kpi-grid {
        grid-template-columns: repeat(4, 1fr);
    }

    .kpi-card {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }
}

/* ── Responsive ── */
@media (max-width: 768px) {
    .report-body {
        padding: 24px 20px;
    }

    .toc-container ul {
        columns: 1;
    }

    .report-header h1 {
        font-size: 24px;
    }

    table {
        font-size: 12px;
    }

    th, td {
        padding: 6px 8px;
    }
}
"""


class HtmlRenderer:
    """Render Markdown to publication-quality HTML with professional styling."""

    def render(
        self,
        markdown_content: str,
        output_path: Path,
        title: str = "",
        metadata: dict | None = None,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert Markdown to HTML with TOC extension
        md = markdown.Markdown(
            extensions=[
                "tables",
                "toc",
                "smarty",
                "sane_lists",
            ],
            extension_configs={
                "toc": {
                    "title": "",
                    "toc_depth": "1-3",
                    "anchorlink": True,
                },
            },
            output_format="html5",
        )
        body_html = md.convert(markdown_content)
        toc_html = getattr(md, "toc", "")

        # Build metadata
        meta = metadata or {}
        display_title = title or "Report"
        author = meta.get("author", "William S. Davis III")
        version = meta.get("version", "1.0")
        classification = meta.get("classification", "Proprietary")
        generated = datetime.now().strftime("%B %d, %Y at %H:%M")
        generated_date = datetime.now().strftime("%B %Y")

        # Build KPI dashboard HTML if data context provided stats
        kpi_html = ""
        if meta.get("kpi_cards"):
            cards = "".join(
                f'<div class="kpi-card">'
                f'<div class="kpi-value">{card["value"]}</div>'
                f'<div class="kpi-label">{card["label"]}</div>'
                f'</div>'
                for card in meta["kpi_cards"]
            )
            kpi_html = f'<div class="kpi-grid">{cards}</div>'

        # Build TOC section
        toc_section = ""
        if toc_html and toc_html.strip():
            toc_section = f"""
    <div class="toc-container">
        <h2>Table of Contents</h2>
        {toc_html}
    </div>"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="author" content="{author}">
    <meta name="generator" content="US Bulk Supply Chain Reporting Platform">
    <title>{display_title}</title>
    <style>
{CSS}
    </style>
</head>
<body>
    <!-- Report Header -->
    <div class="report-header">
        <div class="report-wrapper">
            <h1>{display_title}</h1>
            <div class="report-meta">
                <span>{author}</span>
                <span>&bull;</span>
                <span>{generated_date}</span>
                <span>&bull;</span>
                <span class="badge badge-proprietary">{classification}</span>
                <span class="badge badge-version">v{version}</span>
            </div>
        </div>
    </div>

    <!-- Table of Contents -->
    {toc_section}

    <!-- KPI Dashboard -->
    {kpi_html}

    <!-- Report Body -->
    <div class="report-body">
        {body_html}
    </div>

    <!-- Footer -->
    <div class="report-footer">
        <div class="footer-line footer-brand">US Bulk Supply Chain Reporting Platform</div>
        <div class="footer-line">Prepared by {author}</div>
        <div class="footer-line">Generated {generated}</div>
    </div>
</body>
</html>"""

        output_path.write_text(html, encoding="utf-8")
        logger.info("Wrote HTML: %s (%d chars)", output_path, len(html))
        return output_path
