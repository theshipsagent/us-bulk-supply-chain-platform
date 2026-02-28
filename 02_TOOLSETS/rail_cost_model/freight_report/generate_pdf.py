"""
Phase 4b: Generate the freight rail analysis PDF report using fpdf2.
Professional text-only layout, no graphics.
"""

import logging
from datetime import datetime
from pathlib import Path

from fpdf import FPDF

from .config import TOPICS, STATES_46, OUTPUT_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
log = logging.getLogger(__name__)

# ── Layout constants ──────────────────────────────────────────────────────────
PAGE_W = 215.9          # Letter width mm
PAGE_H = 279.4          # Letter height mm
MARGIN = 25.4           # 1 inch
BODY_W = PAGE_W - 2 * MARGIN  # ~165mm usable

FONT_BODY = ("Helvetica", "", 11)
FONT_BOLD = ("Helvetica", "B", 11)
FONT_H1 = ("Helvetica", "B", 18)
FONT_H2 = ("Helvetica", "B", 14)
FONT_H3 = ("Helvetica", "B", 12)
FONT_SMALL = ("Helvetica", "", 9)
FONT_TITLE = ("Helvetica", "B", 26)
FONT_SUBTITLE = ("Helvetica", "", 14)


class FreightReportPDF(FPDF):
    """Custom PDF class with headers/footers."""

    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="Letter")
        self.set_auto_page_break(auto=True, margin=MARGIN + 5)
        self.set_margins(MARGIN, MARGIN, MARGIN)
        self._in_cover = False
        self._toc_entries = []  # (level, title, page_no)

    def header(self):
        if self._in_cover:
            return
        self.set_font(*FONT_SMALL)
        self.set_text_color(120, 120, 120)
        self.cell(BODY_W, 5, "Freight Rail Analysis - State-by-State Overview (DRAFT)", align="L")
        self.ln(8)
        self.set_text_color(0, 0, 0)

    def footer(self):
        if self._in_cover:
            return
        self.set_y(-MARGIN)
        self.set_font(*FONT_SMALL)
        self.set_text_color(120, 120, 120)
        self.cell(BODY_W / 2, 10, f"Draft - {datetime.now().strftime('%B %Y')}", align="L")
        self.cell(BODY_W / 2, 10, f"Page {self.page_no()}", align="R")
        self.set_text_color(0, 0, 0)

    def add_toc_entry(self, level, title):
        self._toc_entries.append((level, title, self.page_no()))

    def _write_wrapped(self, text, font=None):
        """Write text with word wrapping, handling encoding issues."""
        if font:
            self.set_font(*font)
        # Replace problematic characters for Latin-1 encoding
        safe = text.encode('latin-1', errors='replace').decode('latin-1')
        self.multi_cell(BODY_W, 5.5, safe)


def _add_cover_page(pdf):
    """Generate cover page."""
    pdf._in_cover = True
    pdf.add_page()

    # Title block centered vertically
    pdf.ln(60)
    pdf.set_font(*FONT_TITLE)
    pdf.cell(BODY_W, 15, "Freight Rail Analysis", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(BODY_W, 12, "State-by-State Overview", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)

    pdf.set_font(*FONT_SUBTITLE)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(BODY_W, 8, "A Comprehensive Review of Freight Rail Infrastructure,", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.cell(BODY_W, 8, "Commodities, and Operations Across 46 States", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(25)

    pdf.set_font(*FONT_BODY)
    pdf.cell(BODY_W, 8, f"Report Date: {datetime.now().strftime('%B %d, %Y')}", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(180, 0, 0)
    pdf.cell(BODY_W, 8, "DRAFT - For Internal Review Only", align="C",
             new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(0, 0, 0)
    pdf.ln(30)
    pdf.set_font(*FONT_SMALL)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(BODY_W, 6, "Data Sources: State Rail Plans (46 states), STB Public Use Waybill Sample,",
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(BODY_W, 6, "Federal Railroad Administration, Bureau of Transportation Statistics",
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf._in_cover = False


def _add_table_of_contents(pdf, profiles):
    """Generate table of contents (placeholder page numbers filled after rendering)."""
    pdf.add_page()
    pdf.add_toc_entry(0, "Table of Contents")
    pdf.set_font(*FONT_H1)
    pdf.cell(BODY_W, 12, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # Static sections
    pdf.set_font(*FONT_BOLD)
    pdf.cell(BODY_W, 7, "Executive Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font(*FONT_BOLD)
    pdf.cell(BODY_W, 7, "State Profiles:", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # State entries
    pdf.set_font(*FONT_BODY)
    for p in profiles:
        tier_label = {1: "(Full)", 2: "(Moderate)", 3: "(Summary)"}.get(p["tier"], "")
        year_str = f" ({p['plan_year']})" if p["plan_year"] else ""
        line = f"    {p['state_name']}{year_str} {tier_label}"
        pdf.cell(BODY_W, 5.5, line, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)
    pdf.set_font(*FONT_BOLD)
    pdf.cell(BODY_W, 7, "Appendix: Data Sources & Methodology", new_x="LMARGIN", new_y="NEXT")


def _add_executive_summary(pdf, profiles):
    """Generate 1-2 page executive summary."""
    pdf.add_page()
    pdf.add_toc_entry(0, "Executive Summary")
    pdf.set_font(*FONT_H1)
    pdf.cell(BODY_W, 12, "Executive Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Compute aggregate stats
    total_states = len(profiles)
    tier_counts = {1: 0, 2: 0, 3: 0}
    states_with_waybill = 0
    for p in profiles:
        tier_counts[p["tier"]] += 1
        if p.get("waybill_total_volume", {}).get("total_tons", 0) > 0:
            states_with_waybill += 1

    pdf.set_font(*FONT_BODY)
    summary_text = (
        f"This report provides a freight rail overview for {total_states} states across the "
        f"United States, drawing on state rail plans, the STB Public Use Waybill Sample, and "
        f"supplemental federal data sources. It is intended as a draft starting point for a "
        f"larger freight rail model.\n\n"
        f"Coverage: {tier_counts[1]} states have comprehensive data across most topic areas "
        f"(Tier 1), {tier_counts[2]} states have moderate coverage (Tier 2), and "
        f"{tier_counts[3]} states have summary-level coverage (Tier 3). "
        f"Waybill commodity data was available for {states_with_waybill} of {total_states} states.\n\n"
        f"For each state, the report examines up to 10 topic areas: freight corridors, "
        f"carriers and railroads, industry and commodities, junction points and interchanges, "
        f"rail yard capacity, volume and trends, bottlenecks and constraints, efficiency and "
        f"service quality, costs and investment, and stakeholders and governance. Where "
        f"available, quantitative waybill data on commodity tonnage, origin-destination pairs, "
        f"and car type mix supplements the qualitative analysis from state rail plans.\n\n"
        f"Key national themes emerging from state rail plans include aging infrastructure on "
        f"short line railroads, capacity constraints at major junction points (notably Chicago), "
        f"growing intermodal traffic, coal volume declines offset by industrial product and "
        f"intermodal growth, and ongoing tension between freight and passenger rail capacity "
        f"on shared corridors."
    )
    pdf._write_wrapped(summary_text)


def _add_state_section(pdf, profile):
    """Generate a state section (1-3 pages depending on tier)."""
    pdf.add_page()
    state_name = profile["state_name"]
    state_abbr = profile["state_abbr"]
    plan_year = profile.get("plan_year")
    tier = profile.get("tier", 3)

    pdf.add_toc_entry(1, state_name)

    # State header
    pdf.set_font(*FONT_H1)
    header_text = f"{state_name} ({state_abbr})"
    pdf.cell(BODY_W, 12, header_text, new_x="LMARGIN", new_y="NEXT")

    # Subheader with plan year and tier
    pdf.set_font(*FONT_SMALL)
    pdf.set_text_color(100, 100, 100)
    meta_parts = []
    if plan_year:
        meta_parts.append(f"Rail Plan Year: {plan_year}")
    tier_label = {1: "Full Coverage", 2: "Moderate Coverage", 3: "Summary Coverage"}
    meta_parts.append(f"Data: {tier_label.get(tier, 'Summary')}")
    pdf.cell(BODY_W, 5, " | ".join(meta_parts), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # Horizontal rule
    y = pdf.get_y()
    pdf.set_draw_color(180, 180, 180)
    pdf.line(MARGIN, y, PAGE_W - MARGIN, y)
    pdf.ln(4)

    # Topic sections
    topics_to_show = list(TOPICS.keys())
    # For tier 3, show fewer topics
    if tier == 3:
        topics_to_show = ["freight_corridors", "carriers_railroads", "industry_commodities",
                          "volume_trends", "bottlenecks"]

    for topic_key in topics_to_show:
        content = profile.get(topic_key, "")
        if not content:
            continue

        title = TOPICS[topic_key]["title"]

        # Check if we need a new page (leave room for at least header + some text)
        if pdf.get_y() > PAGE_H - MARGIN - 40:
            pdf.add_page()

        pdf.set_font(*FONT_H3)
        pdf.cell(BODY_W, 8, title, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

        pdf.set_font(*FONT_BODY)
        pdf._write_wrapped(content)
        pdf.ln(4)

    # Waybill data section
    waybill_text = profile.get("waybill_summary", "")
    if waybill_text and "not available" not in waybill_text.lower()[:50]:
        if pdf.get_y() > PAGE_H - MARGIN - 40:
            pdf.add_page()

        pdf.set_font(*FONT_H3)
        pdf.cell(BODY_W, 8, "STB Waybill Data Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

        pdf.set_font(*FONT_BODY)
        pdf._write_wrapped(waybill_text)
        pdf.ln(4)


def _add_appendix(pdf):
    """Generate appendix with data sources and methodology."""
    pdf.add_page()
    pdf.add_toc_entry(0, "Appendix")
    pdf.set_font(*FONT_H1)
    pdf.cell(BODY_W, 12, "Appendix: Data Sources & Methodology", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    pdf.set_font(*FONT_H3)
    pdf.cell(BODY_W, 8, "Data Sources", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font(*FONT_BODY)
    sources = (
        "1. State Rail Plans: 46 state rail plan PDFs were downloaded from state DOT websites "
        "and processed into text chunks for analysis. Plans range from 2010 to 2025 in "
        "publication year.\n\n"
        "2. STB Public Use Waybill Sample: The Surface Transportation Board's waybill sample "
        "provides a stratified sample of rail carload waybills, expanded to represent total "
        "traffic. Data includes commodity codes (STCC), origin/destination BEA economic areas, "
        "car types, tonnage, carloads, and revenue.\n\n"
        "3. Federal Reports: Where available, supplemental federal reports from FRA, BTS, AAR, "
        "and ASLRRA were incorporated to provide national context.\n\n"
        "4. Technical Rail Documents: 42 technical rail industry documents were also indexed, "
        "covering operations, signaling, economics, and equipment."
    )
    pdf._write_wrapped(sources)
    pdf.ln(6)

    pdf.set_font(*FONT_H3)
    pdf.cell(BODY_W, 8, "Methodology", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font(*FONT_BODY)
    methodology = (
        "Text Extraction: State rail plan PDFs were validated (magic bytes, minimum size, "
        "extractable text), then text was extracted page-by-page using PyPDF2. Text was "
        "cleaned and chunked into ~2000-character overlapping segments with sentence-boundary "
        "snapping.\n\n"
        "RAG Indexing: All chunks (state plans + technical documents) were indexed using a "
        "TF-IDF inverted index. For each state and topic, targeted keyword queries were run "
        "against the index. Results were filtered to chunks from the state's own plan or "
        "chunks mentioning the state name, then ranked by TF-IDF score with a bonus for "
        "state-source chunks.\n\n"
        "Waybill Enrichment: DuckDB queries against the STB waybill fact table joined with "
        "dimension tables (STCC commodities, BEA economic areas, car types) to extract "
        "quantitative freight metrics per state.\n\n"
        "Report Generation: State profiles were compiled by synthesizing top-ranked text "
        "excerpts per topic into narrative sections, supplemented with waybill data tables. "
        "States were tiered by data richness (Tier 1: 7+ topics with data, Tier 2: 4+ topics, "
        "Tier 3: fewer)."
    )
    pdf._write_wrapped(methodology)
    pdf.ln(6)

    pdf.set_font(*FONT_H3)
    pdf.cell(BODY_W, 8, "Limitations", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font(*FONT_BODY)
    limitations = (
        "- State rail plans vary widely in scope, detail, and publication year. Some plans "
        "focus primarily on passenger rail with limited freight coverage.\n"
        "- PDF text extraction quality varies; some plans with complex layouts or scanned "
        "pages may have lower extraction fidelity.\n"
        "- The TF-IDF retrieval approach captures keyword relevance but may miss semantically "
        "related content that uses different terminology.\n"
        "- Waybill data is a statistical sample with expansion factors; actual volumes may "
        "differ. BEA economic areas span multiple states, so state-level attribution is "
        "approximate.\n"
        "- This report presents extracted content as-is from source documents. No independent "
        "verification of claims in state rail plans was performed."
    )
    pdf._write_wrapped(limitations)


def generate_pdf(profiles, output_path=None):
    """
    Generate the complete freight rail analysis PDF.

    Args:
        profiles: list of state profile dicts from compile_state.py
        output_path: optional Path override for output file
    """
    if output_path is None:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / "freight_rail_analysis_draft.pdf"

    log.info("Generating PDF report with %d state profiles...", len(profiles))

    pdf = FreightReportPDF()

    # Cover page
    _add_cover_page(pdf)

    # Table of Contents
    _add_table_of_contents(pdf, profiles)

    # Executive Summary
    _add_executive_summary(pdf, profiles)

    # State sections (alphabetical)
    for i, profile in enumerate(profiles, 1):
        log.info("  [%d/%d] Writing %s...", i, len(profiles), profile["state_name"])
        _add_state_section(pdf, profile)

    # Appendix
    _add_appendix(pdf)

    # Output
    pdf.output(str(output_path))
    file_size = output_path.stat().st_size
    log.info("PDF generated: %s (%.1f KB, %d pages)",
             output_path, file_size / 1024, pdf.page_no())

    return output_path
