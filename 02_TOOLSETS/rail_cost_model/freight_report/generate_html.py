"""
Phase 4b: Generate the freight rail analysis report as HTML.
UTF-8 encoding avoids the garbled text issues of fpdf2's Latin-1.
Print to PDF from browser for clean output.
"""

import html
import logging
from datetime import datetime
from pathlib import Path

from .config import TOPICS, STATES_46, OUTPUT_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
log = logging.getLogger(__name__)


CSS = """
@media print {
    .state-section { page-break-before: always; }
    .no-break { page-break-inside: avoid; }
    .cover-page { page-break-after: always; }
    .toc-page { page-break-after: always; }
    .exec-page { page-break-after: always; }
    .appendix { page-break-before: always; }
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.5;
    color: #1a1a1a;
    max-width: 8.5in;
    margin: 0 auto;
    padding: 0.75in 1in;
}
h1 { font-size: 18pt; margin: 0 0 8px 0; color: #111; }
h2 { font-size: 14pt; margin: 20px 0 6px 0; color: #222; }
h3 { font-size: 12pt; margin: 14px 0 4px 0; color: #333; }
p { margin: 0 0 8px 0; }
.cover-page {
    text-align: center;
    padding-top: 2.5in;
}
.cover-page h1 { font-size: 26pt; margin-bottom: 4px; }
.cover-page .subtitle { font-size: 20pt; font-weight: bold; color: #333; }
.cover-page .tagline { font-size: 13pt; color: #555; margin: 20px 0; }
.cover-page .date { font-size: 12pt; color: #444; margin: 18px 0 8px 0; }
.cover-page .draft { font-size: 13pt; font-weight: bold; color: #b00; margin: 10px 0 30px 0; }
.cover-page .sources { font-size: 9pt; color: #888; margin-top: 40px; }
.toc-page ul { list-style: none; padding: 0; }
.toc-page li { padding: 2px 0; font-size: 10.5pt; }
.toc-page li.tier2 { color: #555; }
.toc-page li.tier3 { color: #888; }
.state-header {
    border-bottom: 2px solid #ccc;
    padding-bottom: 4px;
    margin-bottom: 10px;
}
.state-meta { font-size: 9.5pt; color: #777; margin-top: 2px; }
.topic-section { margin-bottom: 12px; }
.topic-section h3 { color: #2a5a8a; margin-bottom: 3px; }
.topic-text { text-align: justify; }
.waybill-section { margin-top: 14px; }
.waybill-section h3 { color: #5a2a2a; }
.metric-list { padding-left: 18px; margin: 4px 0 8px 0; }
.metric-list li { font-size: 10.5pt; margin: 1px 0; }
.exec-summary { text-align: justify; }
.appendix h3 { margin-top: 16px; }
.appendix p, .appendix ul { font-size: 10.5pt; }
.appendix ul { padding-left: 20px; margin: 4px 0 10px 0; }
.appendix li { margin: 3px 0; }
hr { border: none; border-top: 1px solid #ddd; margin: 10px 0; }
"""


def _esc(text):
    """HTML-escape text and convert newlines to <br> / <p> blocks."""
    if not text:
        return ""
    escaped = html.escape(text)
    # Split on double-newline into paragraphs
    paragraphs = escaped.split("\n\n")
    parts = []
    for para in paragraphs:
        # Within a paragraph, single newlines become <br>
        para = para.replace("\n", "<br>\n")
        parts.append(f"<p>{para}</p>")
    return "\n".join(parts)


def _esc_inline(text):
    """HTML-escape a single line of text."""
    return html.escape(text) if text else ""


def _build_cover():
    now = datetime.now()
    return f"""
<div class="cover-page">
    <h1>Freight Rail Analysis</h1>
    <div class="subtitle">State-by-State Overview</div>
    <div class="tagline">A Review of Freight Rail Infrastructure,<br>
    Commodities, and Operations Across 46 States</div>
    <div class="date">Report Date: {now.strftime('%B %d, %Y')}</div>
    <div class="draft">DRAFT &mdash; For Internal Review Only</div>
    <div class="sources">Data Sources: State Rail Plans (46 states), STB Public Use Waybill Sample,<br>
    Federal Railroad Administration, Bureau of Transportation Statistics</div>
</div>
"""


def _build_toc(profiles):
    items = []
    for p in profiles:
        tier = p.get("tier", 3)
        cls = {1: "", 2: "tier2", 3: "tier3"}.get(tier, "")
        year = f" ({p['plan_year']})" if p.get("plan_year") else ""
        label = {1: "", 2: " &ndash; Moderate", 3: " &ndash; Summary"}.get(tier, "")
        items.append(f'<li class="{cls}">{_esc_inline(p["state_name"])}{year}{label}</li>')

    return f"""
<div class="toc-page">
    <h1>Table of Contents</h1>
    <h2>Executive Summary</h2>
    <h2>State Profiles</h2>
    <ul>
        {"".join(items)}
    </ul>
    <h2>Appendix: Data Sources &amp; Methodology</h2>
</div>
"""


def _build_exec_summary(profiles):
    total = len(profiles)
    tier_counts = {1: 0, 2: 0, 3: 0}
    waybill_count = 0
    for p in profiles:
        tier_counts[p.get("tier", 3)] += 1
        if p.get("waybill_total_volume", {}).get("total_tons", 0) > 0:
            waybill_count += 1

    return f"""
<div class="exec-page">
    <h1>Executive Summary</h1>
    <div class="exec-summary">
    <p>This report provides a freight rail overview for {total} states, drawing on
    state rail plans, the STB Public Use Waybill Sample, and supplemental federal sources.
    It is a draft starting point for a larger freight rail model.</p>

    <p><strong>Coverage:</strong> {tier_counts[1]} states have comprehensive data (Tier 1),
    {tier_counts[2]} have moderate coverage (Tier 2), and {tier_counts[3]} have summary-level
    coverage (Tier 3). Waybill commodity data was available for {waybill_count} of {total} states.</p>

    <p>For each state the report examines up to 10 topics: freight corridors, carriers,
    commodities, junction points, yard capacity, volume trends, bottlenecks, efficiency,
    costs/investment, and stakeholders. Quantitative waybill data on tonnage, O-D pairs,
    and car types supplements qualitative plan analysis where available.</p>

    <p><strong>National themes:</strong> aging short-line infrastructure, capacity constraints
    at major junctions (notably Chicago), growing intermodal traffic, coal decline offset by
    industrial and intermodal growth, and freight/passenger conflicts on shared corridors.</p>
    </div>
</div>
"""


def _build_waybill_html(profile):
    """Build waybill section as structured HTML instead of plain text."""
    vol = profile.get("waybill_total_volume", {})
    total_tons = vol.get("total_tons", 0)
    total_carloads = vol.get("total_carloads", 0)
    total_revenue = vol.get("total_revenue", 0)

    if not total_tons and not total_carloads:
        return ""

    parts = ['<div class="waybill-section no-break">', '<h3>STB Waybill Data</h3>']

    def fmt(v):
        if not v:
            return "N/A"
        try:
            return f"{float(v):,.0f}"
        except (ValueError, TypeError):
            return str(v)

    rev_str = f", ~${fmt(total_revenue)} revenue" if total_revenue else ""
    parts.append(f"<p>Originating freight: {fmt(total_tons)} tons, "
                 f"{fmt(total_carloads)} carloads{rev_str}.</p>")

    # Commodities
    commodities = profile.get("waybill_top_commodities", [])
    if commodities:
        parts.append("<p><strong>Top Commodities (tons):</strong></p><ul class='metric-list'>")
        for c in commodities[:5]:
            parts.append(f"<li>{_esc_inline(c['commodity'])}: {fmt(c['tons'])} tons "
                        f"({fmt(c['carloads'])} carloads)</li>")
        parts.append("</ul>")

    # O-D pairs
    od_pairs = profile.get("waybill_top_od_pairs", [])
    if od_pairs:
        parts.append("<p><strong>Top O-D Pairs:</strong></p><ul class='metric-list'>")
        for od in od_pairs[:3]:
            parts.append(f"<li>{_esc_inline(od['origin'])} &rarr; "
                        f"{_esc_inline(od['destination'])}: {fmt(od['tons'])} tons</li>")
        parts.append("</ul>")

    # Car types
    car_types = profile.get("waybill_car_types", [])
    if car_types:
        parts.append("<p><strong>Car Types:</strong></p><ul class='metric-list'>")
        for ct in car_types[:4]:
            parts.append(f"<li>{_esc_inline(ct['car_type'])}: {fmt(ct['carloads'])} carloads</li>")
        parts.append("</ul>")

    parts.append("</div>")
    return "\n".join(parts)


def _build_state_section(profile):
    state_name = profile["state_name"]
    state_abbr = profile["state_abbr"]
    plan_year = profile.get("plan_year")
    tier = profile.get("tier", 3)

    tier_label = {1: "Full Coverage", 2: "Moderate Coverage", 3: "Summary Coverage"}
    meta_parts = []
    if plan_year:
        meta_parts.append(f"Plan Year: {plan_year}")
    meta_parts.append(tier_label.get(tier, "Summary"))

    parts = [
        '<div class="state-section">',
        f'<div class="state-header">',
        f'<h1>{_esc_inline(state_name)} ({_esc_inline(state_abbr)})</h1>',
        f'<div class="state-meta">{" | ".join(meta_parts)}</div>',
        '</div>',
    ]

    # Topic sections
    topics_to_show = list(TOPICS.keys())
    if tier == 3:
        topics_to_show = ["freight_corridors", "carriers_railroads", "industry_commodities",
                          "volume_trends", "bottlenecks"]

    for topic_key in topics_to_show:
        content = profile.get(topic_key, "")
        if not content or "no specific data" in content.lower()[:50]:
            continue

        title = TOPICS[topic_key]["title"]
        parts.append(f'<div class="topic-section no-break">')
        parts.append(f'<h3>{_esc_inline(title)}</h3>')
        parts.append(f'<div class="topic-text">{_esc(content)}</div>')
        parts.append('</div>')

    # Waybill
    waybill_html = _build_waybill_html(profile)
    if waybill_html:
        parts.append(waybill_html)

    parts.append('</div>')
    return "\n".join(parts)


def _build_appendix():
    return """
<div class="appendix">
    <h1>Appendix: Data Sources &amp; Methodology</h1>

    <h3>Data Sources</h3>
    <ul>
        <li><strong>State Rail Plans:</strong> 46 state rail plan PDFs from state DOT websites,
        processed into text chunks. Plans range from 2010 to 2025.</li>
        <li><strong>STB Waybill Sample:</strong> Stratified sample of rail carload waybills
        with expansion factors. Includes STCC codes, BEA areas, car types, tonnage, and revenue.</li>
        <li><strong>Technical Documents:</strong> 42 rail industry documents covering operations,
        signaling, economics, and equipment.</li>
    </ul>

    <h3>Methodology</h3>
    <ul>
        <li><strong>Text Extraction:</strong> PDFs validated, text extracted via PyPDF2,
        cleaned and chunked into ~2,000-character overlapping segments.</li>
        <li><strong>RAG Indexing:</strong> TF-IDF inverted index across all chunks. Per-state
        keyword queries filtered to state-source chunks or chunks mentioning the state.</li>
        <li><strong>Waybill Enrichment:</strong> DuckDB queries against STB waybill fact table
        joined with STCC, BEA, and car type dimensions.</li>
        <li><strong>Tiering:</strong> Tier 1 (7+ topics, 20+ chunks), Tier 2 (4+ topics,
        10+ chunks), Tier 3 (fewer).</li>
    </ul>

    <h3>Limitations</h3>
    <ul>
        <li>State plans vary in scope, detail, and year. Some emphasize passenger rail.</li>
        <li>PDF text extraction quality varies with document layout.</li>
        <li>TF-IDF captures keyword relevance but may miss semantically related content.</li>
        <li>Waybill data uses expansion factors; BEA areas span multiple states.</li>
        <li>Extracted content presented as-is from sources without independent verification.</li>
    </ul>
</div>
"""


def generate_html(profiles, output_path=None):
    """
    Generate the freight rail analysis report as HTML.

    Args:
        profiles: list of state profile dicts from compile_state.py
        output_path: optional Path override
    Returns:
        Path to output file
    """
    if output_path is None:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / "freight_rail_analysis_draft.html"

    log.info("Generating HTML report with %d state profiles...", len(profiles))

    sections = []

    # Cover
    sections.append(_build_cover())
    # TOC
    sections.append(_build_toc(profiles))
    # Executive Summary
    sections.append(_build_exec_summary(profiles))

    # State sections
    for i, profile in enumerate(profiles, 1):
        log.info("  [%d/%d] Writing %s...", i, len(profiles), profile["state_name"])
        sections.append(_build_state_section(profile))

    # Appendix
    sections.append(_build_appendix())

    body = "\n<hr>\n".join(sections)

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Freight Rail Analysis - State-by-State Overview (Draft)</title>
    <style>{CSS}</style>
</head>
<body>
{body}
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(doc)

    file_size = output_path.stat().st_size
    log.info("HTML generated: %s (%.1f KB)", output_path, file_size / 1024)
    return output_path
