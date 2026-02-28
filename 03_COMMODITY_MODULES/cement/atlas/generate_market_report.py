#!/usr/bin/env python3
"""
Generate comprehensive US Cement Market Intelligence Report.
Output: PDF document (30-40 pages)
"""

import json
from datetime import datetime
from pathlib import Path
from fpdf import FPDF

def safe_str(val, max_len=None):
    """Safely convert value to string, handling None and special characters."""
    s = str(val) if val is not None else ""
    # Replace non-ASCII characters that cause issues with PDF fonts
    s = s.replace('\u2011', '-')  # Non-breaking hyphen
    s = s.replace('\u2010', '-')  # Hyphen
    s = s.replace('\u2013', '-')  # En dash
    s = s.replace('\u2014', '-')  # Em dash
    s = s.replace('\u2019', "'")  # Right single quote
    s = s.replace('\u2018', "'")  # Left single quote
    s = s.replace('\u201c', '"')  # Left double quote
    s = s.replace('\u201d', '"')  # Right double quote
    s = s.replace('\u2022', '*')  # Bullet
    # Encode to latin-1, replacing unencodable chars
    s = s.encode('latin-1', 'replace').decode('latin-1')
    if max_len and len(s) > max_len:
        return s[:max_len]
    return s

def safe_num(val, default=0):
    """Safely get numeric value, handling None."""
    return val if val is not None else default

class MarketReport(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        self.set_font('Helvetica', 'I', 9)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, 'US Cement Market Intelligence Report - Confidential', align='R')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def chapter_title(self, title):
        self.set_x(self.l_margin)
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(0, 51, 102)
        self.cell(0, 15, title, ln=True)
        self.ln(5)

    def section_title(self, title):
        self.set_x(self.l_margin)
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(0, 76, 153)
        self.cell(0, 10, title, ln=True)
        self.ln(3)

    def subsection_title(self, title):
        self.set_x(self.l_margin)
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(51, 51, 51)
        self.cell(0, 8, title, ln=True)
        self.ln(2)

    def body_text(self, text):
        self.set_x(self.l_margin)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, text)
        self.ln(3)

    def bullet_point(self, text):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(0, 0, 0)
        self.set_x(self.l_margin)  # Reset to left margin
        self.cell(5, 6, "")  # Indent
        self.multi_cell(0, 6, f"* {text}")

    def add_table(self, headers, data, col_widths=None):
        self.set_x(self.l_margin)  # Reset x position before table
        self.set_font('Helvetica', 'B', 9)
        self.set_fill_color(0, 51, 102)
        self.set_text_color(255, 255, 255)

        if col_widths is None:
            col_widths = [190 / len(headers)] * len(headers)

        for i, header in enumerate(headers):
            self.cell(col_widths[i], 7, str(header), border=1, fill=True, align='C')
        self.ln()

        self.set_font('Helvetica', '', 9)
        self.set_text_color(0, 0, 0)
        fill = False
        for row in data:
            self.set_x(self.l_margin)  # Reset x at start of each row
            if fill:
                self.set_fill_color(240, 240, 240)
            else:
                self.set_fill_color(255, 255, 255)
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 6, str(cell)[:30], border=1, fill=True, align='C')
            self.ln()
            fill = not fill
        self.set_x(self.l_margin)  # Reset x position after table
        self.ln(5)


def generate_report():
    # Load data
    with open("output/report_data.json", "r") as f:
        data = json.load(f)

    pdf = MarketReport()
    pdf.set_title("US Cement Market Intelligence Report")
    pdf.set_author("Market Intelligence")

    # =========================================================================
    # TITLE PAGE
    # =========================================================================
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 28)
    pdf.set_text_color(0, 51, 102)
    pdf.ln(60)
    pdf.cell(0, 20, 'US CEMENT MARKET', align='C', ln=True)
    pdf.cell(0, 20, 'INTELLIGENCE REPORT', align='C', ln=True)
    pdf.ln(20)
    pdf.set_font('Helvetica', '', 14)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, 'Strategic Analysis for Market Entry and Expansion', align='C', ln=True)
    pdf.ln(10)
    pdf.cell(0, 10, 'Focus: East Coast and Gulf Coast Markets', align='C', ln=True)
    pdf.ln(30)
    pdf.set_font('Helvetica', 'I', 11)
    pdf.cell(0, 10, f'Report Date: {datetime.now().strftime("%B %Y")}', align='C', ln=True)
    pdf.cell(0, 10, 'Classification: Confidential', align='C', ln=True)

    # =========================================================================
    # TABLE OF CONTENTS
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("Table of Contents")
    pdf.set_font('Helvetica', '', 11)
    toc = [
        ("1. Executive Summary", 3),
        ("2. US Cement Market Overview", 5),
        ("   2.1 Market Size and Structure", 5),
        ("   2.2 Domestic Production Capacity", 6),
        ("   2.3 Key Market Participants", 7),
        ("3. Import Market Analysis", 9),
        ("   3.1 Import Volume and Trends", 9),
        ("   3.2 Source Country Analysis", 10),
        ("   3.3 Import Terminal Landscape", 12),
        ("4. Gulf Coast Market Analysis", 14),
        ("   4.1 Houston Market", 14),
        ("   4.2 Tampa/Florida Market", 16),
        ("   4.3 New Orleans/Louisiana Opportunity", 17),
        ("   4.4 Gulf Coast Competitive Landscape", 19),
        ("5. East Coast Market Analysis", 21),
        ("   5.1 Southeast: Georgia and Carolinas", 21),
        ("   5.2 Mid-Atlantic: Virginia and Maryland", 23),
        ("   5.3 Northeast: NY/NJ Metro and New England", 24),
        ("   5.4 East Coast Competitive Landscape", 26),
        ("6. Canadian Competition Analysis", 28),
        ("   6.1 Vessel-to-Rail Competition", 28),
        ("   6.2 Cross-Border Rail Competition", 29),
        ("   6.3 Strategic Implications", 30),
        ("7. Infrastructure and Logistics", 31),
        ("   7.1 Rail Network Coverage", 31),
        ("   7.2 Distribution Infrastructure", 32),
        ("8. Market Entry Considerations", 33),
        ("   8.1 Site Selection Factors", 33),
        ("   8.2 Competitive Positioning", 34),
        ("   8.3 Strategic Recommendations", 35),
        ("9. Data Appendix", 36),
    ]
    for item, page in toc:
        pdf.cell(0, 7, item, ln=True)

    # =========================================================================
    # EXECUTIVE SUMMARY
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("1. Executive Summary")

    cap = data["us_capacity"]
    imp = data["import_totals"]

    pdf.body_text(
        "This report provides a comprehensive analysis of the United States cement market, "
        "with particular focus on the East Coast and Gulf Coast regions. The analysis is designed "
        "to support strategic decision-making for a major cement producer with existing terminal "
        "operations in Tampa and Houston, evaluating expansion opportunities along the Eastern Seaboard "
        "and in the New Orleans/Louisiana market."
    )

    pdf.section_title("Key Market Findings")

    pdf.body_text(
        f"The US cement market represents one of the world's largest construction materials markets, "
        f"with domestic production capacity of approximately {cap['total_capacity']} million metric tons "
        f"per annum (MTPA) across {cap['total_plants']} production facilities operated by {cap['producers']} "
        f"major producers. The market is characterized by a blend of domestic production and significant "
        f"import activity, with imports playing a crucial role in meeting regional demand imbalances."
    )

    pdf.subsection_title("Import Market Dynamics")
    pdf.body_text(
        f"Over the analysis period (June 2022 to June 2025), the US imported approximately "
        f"{imp['million_tons']} million metric tons of cement through {imp['ports']} port facilities, "
        f"sourced from {imp['countries']} countries. This import volume was distributed among "
        f"{imp['importers']} active importing entities, indicating a moderately concentrated but "
        f"competitive import landscape."
    )

    # Top source countries
    top_countries = data["imports_by_country"][:5]
    pdf.body_text(
        f"The primary source countries are Turkey ({top_countries[0]['pct_share']}% market share), "
        f"Vietnam ({top_countries[1]['pct_share']}%), Canada ({top_countries[2]['pct_share']}%), "
        f"Greece ({top_countries[3]['pct_share']}%), and Colombia ({top_countries[4]['pct_share']}%). "
        f"Turkey's dominance in the import market reflects its competitive pricing, proximity to Gulf Coast "
        f"and East Coast ports via Mediterranean shipping routes, and established relationships with "
        f"major US importers."
    )

    pdf.subsection_title("Strategic Implications for Existing Operations")
    pdf.body_text(
        "The Houston terminal benefits from its position as the nation's largest cement import gateway, "
        "handling over 13 million metric tons during the analysis period. The port's extensive rail "
        "connectivity enables distribution throughout Texas, the broader Southwest, and into the Midwest "
        "via major rail corridors. Key competitors at Houston include Houston Cement Company, CEMEX, "
        "SESCO, and Argos, each with established supply chains and customer relationships."
    )

    pdf.body_text(
        "Tampa operations are strategically positioned to serve Florida's robust construction market, "
        "with the port handling approximately 3.3 million metric tons. Florida's population growth "
        "and infrastructure investment continue to drive cement demand, though competition from "
        "Greek and Turkish imports via Titan, Heidelberg, and regional distributors requires "
        "competitive pricing and service differentiation."
    )

    pdf.subsection_title("Expansion Opportunities")
    pdf.body_text(
        "Analysis indicates several attractive expansion opportunities. The New Orleans/Louisiana "
        "corridor presents compelling economics, with the Port of Gramercy handling 3.5 million "
        "metric tons and offering distribution access to the Mississippi River system and Gulf Coast "
        "markets. East Coast markets, particularly the Savannah-to-Norfolk corridor, show strong "
        "demand fundamentals with limited domestic production capacity, creating favorable conditions "
        "for import terminal development."
    )

    pdf.subsection_title("Canadian Competition Assessment")
    pdf.body_text(
        "Canadian cement enters the US market through two primary channels: vessel shipments through "
        "Great Lakes and East Coast ports, and cross-border rail movements. Analysis indicates "
        "Canadian imports totaling approximately 8.3 million metric tons, primarily serving Midwest "
        "and Northeast markets. Votorantim (via McInnis USA) represents the dominant Canadian "
        "importer, with significant volumes through Detroit and other Great Lakes facilities. "
        "This competition is most relevant for Northeast market considerations, where Canadian "
        "supply can reach coastal markets via rail."
    )

    # =========================================================================
    # US CEMENT MARKET OVERVIEW
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("2. US Cement Market Overview")

    pdf.section_title("2.1 Market Size and Structure")

    pdf.body_text(
        "The United States cement market is a mature but dynamic industry, essential to the nation's "
        "construction and infrastructure sectors. Cement consumption is closely correlated with "
        "residential construction activity, commercial development, and public infrastructure "
        "investment. The market exhibits regional variations in supply-demand balance, with coastal "
        "regions particularly dependent on imported cement to supplement domestic production."
    )

    pdf.body_text(
        "Market structure is characterized by a mix of large integrated producers operating "
        "multiple manufacturing facilities, regional players with concentrated geographic presence, "
        "and import terminals operated by both domestic producers and independent trading companies. "
        "This structure creates opportunities for market participants to compete on multiple fronts: "
        "production efficiency, logistics optimization, and strategic terminal positioning."
    )

    # USGS data
    usgs = data["usgs_shipments"]
    total_usgs = sum(s["million_short_tons"] for s in usgs)
    pdf.body_text(
        f"According to USGS data, domestic cement shipments across the analysis period totaled "
        f"approximately {total_usgs:.1f} million short tons. The geographic distribution of demand "
        f"shows concentration in high-growth states, with Texas, California, and Florida representing "
        f"the largest consumption markets."
    )

    pdf.subsection_title("Regional Demand Patterns")
    pdf.body_text(
        "USGS shipment data reveals the following major consumption centers (in million short tons):"
    )

    top_states = usgs[:10]
    headers = ["State/Region", "Million Short Tons"]
    table_data = [[safe_str(s.get("state")), f"{safe_num(s.get('million_short_tons')):.2f}"] for s in top_states]
    pdf.add_table(headers, table_data, [120, 70])

    pdf.body_text(
        "These demand patterns inform optimal terminal positioning, with Gulf Coast and Florida "
        "markets showing particularly strong fundamentals for import terminal operations."
    )

    pdf.section_title("2.2 Domestic Production Capacity")

    pdf.body_text(
        f"The United States maintains {cap['total_plants']} cement manufacturing facilities with "
        f"combined production capacity of {cap['total_capacity']} MTPA. Production is geographically "
        f"distributed to serve regional markets, with capacity concentrations in Texas, California, "
        f"Missouri, Florida, and Alabama. The following table summarizes production capacity by company:"
    )

    producers = data["producers"][:15]
    headers = ["Company", "Plants", "Capacity (MTPA)", "Market Share"]
    table_data = [[safe_str(p.get("company"), 25), safe_num(p.get("plants")), f"{safe_num(p.get('capacity_mtpa')):.2f}", f"{safe_num(p.get('market_share')):.1f}%"] for p in producers]
    pdf.add_table(headers, table_data, [80, 30, 40, 40])

    pdf.body_text(
        "The domestic production landscape is moderately concentrated, with the top five producers "
        "controlling approximately 58% of total capacity. Holcim (US) Inc leads the market with "
        "20.4 MTPA across 15 facilities, followed by Ash Grove Cement Company (11.3 MTPA), "
        "CEMEX Inc (10.2 MTPA), Argos USA LLC (9.6 MTPA), and Buzzi Unicem USA Inc (9.0 MTPA)."
    )

    pdf.add_page()
    pdf.section_title("2.3 Key Market Participants")

    pdf.subsection_title("Major Integrated Producers")

    pdf.body_text(
        "Holcim (US) Inc: The largest US cement producer with 15 plants spanning multiple regions. "
        "Holcim's geographic footprint includes significant presence in Texas, the Midwest, and "
        "Eastern markets. The company operates an integrated model combining production, import "
        "terminals, and distribution infrastructure. Strategic focus on sustainability and "
        "alternative fuels positions Holcim for evolving regulatory requirements."
    )

    pdf.body_text(
        "CEMEX Inc: A major multinational with 8 US plants and extensive terminal operations. "
        "CEMEX maintains strong positions in Texas, California, and Florida markets. The company's "
        "integrated supply chain leverages both domestic production and imports from group facilities "
        "in Mexico and other regions. CEMEX's Victorville, California plant (3.0 MTPA) is among the "
        "largest individual facilities in the country."
    )

    pdf.body_text(
        "Ash Grove Cement Company: Operates 11 facilities with 11.3 MTPA capacity, primarily serving "
        "central and western US markets. Strong regional presence in the Midwest and Mountain states. "
        "Focus on domestic production efficiency with limited import terminal operations."
    )

    pdf.body_text(
        "Argos USA LLC: With 9.6 MTPA across 6 plants, Argos has established strong positions in "
        "Southeast and Gulf Coast markets. Notable facilities include Martinsburg, WV (2.2 MTPA) and "
        "Tampa Port (1.9 MTPA). Argos actively participates in the import market, leveraging its "
        "Colombian parent company's production capabilities."
    )

    pdf.body_text(
        "Buzzi Unicem USA Inc: European-owned producer with 7 US plants totaling 9.0 MTPA. "
        "Geographic focus on Midwest and Southeast markets. The Festus, Missouri plant (2.7 MTPA) "
        "represents a major production hub serving regional distribution."
    )

    pdf.subsection_title("Regional and Specialty Producers")

    pdf.body_text(
        "Heidelberg Materials US Inc (formerly Lehigh Hanson): 13 plants with 5.5 MTPA, with strong "
        "positions in Mid-Atlantic and Southeast markets. Active importer through multiple terminal "
        "locations. The company's broad geographic distribution enables market coverage across "
        "diverse regional conditions."
    )

    pdf.body_text(
        "CalPortland Co: California-focused producer with 4 plants (4.4 MTPA). Dominant position in "
        "West Coast markets, particularly Southern California. Limited exposure to Gulf Coast and "
        "East Coast competitive dynamics."
    )

    pdf.body_text(
        "Titan America LLC: Greek-owned producer with 2 US plants (3.4 MTPA) concentrated in Florida. "
        "Integrated import operations through affiliated terminals. Strong position in Florida market "
        "through combination of domestic production and Greek imports."
    )

    # =========================================================================
    # IMPORT MARKET ANALYSIS
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("3. Import Market Analysis")

    pdf.section_title("3.1 Import Volume and Trends")

    pdf.body_text(
        f"The US cement import market has shown robust activity over the analysis period, with "
        f"{imp['shipments']:,} shipments totaling {imp['million_tons']:.1f} million metric tons. "
        f"Import activity demonstrates the market's structural dependence on foreign supply to "
        f"meet demand in coastal regions where domestic production capacity is insufficient or "
        f"logistically disadvantaged."
    )

    # Annual trends
    annual = data["annual_imports"]
    pdf.subsection_title("Annual Import Trends")
    headers = ["Year", "Shipments", "Volume (MM MT)", "Countries", "Importers"]
    table_data = [[str(safe_num(a.get("year"))), f"{safe_num(a.get('shipments')):,}", f"{safe_num(a.get('million_tons')):.2f}", safe_num(a.get("countries")), safe_num(a.get("importers"))] for a in annual]
    pdf.add_table(headers, table_data, [30, 40, 45, 35, 40])

    pdf.body_text(
        "Year-over-year trends indicate stable import volumes with seasonal fluctuations aligned "
        "with construction activity patterns. The number of active importing entities has remained "
        "relatively constant, suggesting established market participants rather than new entrant activity."
    )

    # Monthly trends narrative
    monthly = data["monthly_trends"]
    pdf.body_text(
        "Monthly import patterns reveal predictable seasonality, with volumes typically peaking "
        "during the May-August construction season and declining during winter months. This "
        "seasonality is most pronounced in northern markets, while Gulf Coast and Florida markets "
        "exhibit more stable year-round demand."
    )

    pdf.add_page()
    pdf.section_title("3.2 Source Country Analysis")

    countries = data["imports_by_country"]

    pdf.body_text(
        "Import source diversification provides supply chain resilience while creating competitive "
        "dynamics among foreign producers. The following analysis examines major source countries "
        "and their market positioning:"
    )

    headers = ["Country", "Shipments", "Volume (MM MT)", "Market Share", "US Ports"]
    table_data = [[safe_str(c.get("origin_country")), safe_num(c.get("shipments")), f"{safe_num(c.get('million_tons')):.2f}", f"{safe_num(c.get('pct_share')):.1f}%", safe_num(c.get("ports_served"))] for c in countries[:15]]
    pdf.add_table(headers, table_data, [55, 35, 40, 35, 25])

    pdf.subsection_title("Turkey")
    pdf.body_text(
        f"Turkey dominates the US import market with {countries[0]['million_tons']:.1f} million metric tons "
        f"({countries[0]['pct_share']:.1f}% market share) distributed across {countries[0]['ports_served']} "
        f"US ports. Turkish cement benefits from competitive production costs, modern facilities, and "
        f"favorable Mediterranean shipping routes to both Gulf Coast and East Coast destinations. "
        f"Major Turkish flows include Houston (11.95 MM MT), Florida ports, and East Coast terminals. "
        f"Turkish producers have established strong relationships with US importers including "
        f"Heidelberg, Houston Cement Company, SESCO, and Argos."
    )

    pdf.subsection_title("Vietnam")
    pdf.body_text(
        f"Vietnam represents the second-largest source with {countries[1]['million_tons']:.1f} million metric tons "
        f"({countries[1]['pct_share']:.1f}% share). Vietnamese cement primarily serves West Coast markets "
        f"(California, Oregon, Washington) via Pacific shipping routes, though some volume reaches "
        f"Gulf Coast terminals. Taiheiyo Cement and Two Rivers Cement are major importers of Vietnamese "
        f"product. Transit times from Vietnam to US West Coast are competitive, enabling reliable supply "
        f"chain operations."
    )

    pdf.subsection_title("Canada")
    pdf.body_text(
        f"Canada supplies {countries[2]['million_tons']:.1f} million metric tons ({countries[2]['pct_share']:.1f}% share), "
        f"primarily serving Great Lakes and Northeast markets. Canadian imports utilize both vessel "
        f"movements through Great Lakes ports and cross-border rail shipments. Votorantim (McInnis USA) "
        f"represents the dominant Canadian supplier, with a modern facility in Quebec positioned to "
        f"serve Eastern markets. Canadian competition is particularly relevant for NY/NJ and New England "
        f"market considerations."
    )

    pdf.subsection_title("Greece")
    pdf.body_text(
        f"Greece exports {countries[3]['million_tons']:.1f} million metric tons ({countries[3]['pct_share']:.1f}% share), "
        f"primarily through Titan Cement's integrated supply chain to affiliated US terminals. "
        f"Greek cement serves East Coast and Florida markets, with significant volumes through "
        f"NY/NJ, Tampa, and Norfolk. Titan's vertically integrated model provides competitive "
        f"advantages in served markets."
    )

    pdf.add_page()
    pdf.subsection_title("Other Significant Sources")

    pdf.body_text(
        "Colombia: 2.4 MM MT primarily serving Gulf Coast markets through Argos USA's integrated "
        "supply chain. Argos leverages its Colombian parent's production for US distribution."
    )

    pdf.body_text(
        "United Arab Emirates: 2.2 MM MT serving Southeast markets, particularly Georgia and "
        "Carolina ports. UAE cement benefits from modern production facilities and competitive "
        "pricing on bulk shipments."
    )

    pdf.body_text(
        "South Korea: 2.0 MM MT primarily serving West Coast markets through Oregon and Washington "
        "ports. Korean cement competes with Vietnamese product for Pacific Rim supply positioning."
    )

    pdf.body_text(
        "Mexico: 1.8 MM MT entering through Texas and California border crossings and Gulf ports. "
        "CEMEX's integrated North American operations facilitate Mexican supply to US markets."
    )

    pdf.section_title("3.3 Import Terminal Landscape")

    ports = data["imports_by_port"]

    pdf.body_text(
        f"Import terminals are distributed across {imp['ports']} US port locations, with significant "
        f"concentration at major gateway ports. The following analysis examines the top import facilities:"
    )

    headers = ["Port", "Shipments", "Volume (MM MT)", "Share", "Countries", "Importers"]
    table_data = [[safe_str(p.get("port"), 35), safe_num(p.get("shipments")), f"{safe_num(p.get('million_tons')):.2f}", f"{safe_num(p.get('pct_share')):.1f}%", safe_num(p.get("source_countries")), safe_num(p.get("importers"))] for p in ports[:12]]
    pdf.add_table(headers, table_data, [70, 25, 35, 20, 25, 25])

    pdf.body_text(
        "Houston dominates the import terminal landscape, handling over 20% of total US cement "
        "imports. The port's extensive infrastructure, rail connectivity, and geographic position "
        "enable distribution throughout Texas and the broader Southwest/Midwest regions. Secondary "
        "Gulf Coast terminals at Gramercy (Louisiana), Corpus Christi, and Florida ports provide "
        "additional regional coverage."
    )

    pdf.body_text(
        "East Coast terminals are more fragmented, with Savannah, NY/NJ, Norfolk, and Providence "
        "each handling significant but smaller volumes. This fragmentation creates opportunities "
        "for strategic terminal positioning to capture regional market share."
    )

    # =========================================================================
    # GULF COAST MARKET ANALYSIS
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("4. Gulf Coast Market Analysis")

    pdf.body_text(
        "The Gulf Coast represents the largest import gateway region for US cement, benefiting "
        "from deep-water port infrastructure, extensive rail connectivity, and proximity to "
        "major consumption markets in Texas, Louisiana, and the broader Southern United States. "
        "This section analyzes the competitive landscape and market dynamics at Gulf Coast ports, "
        "with particular attention to existing operations in Houston and Tampa, and the expansion "
        "opportunity in New Orleans/Louisiana."
    )

    pdf.section_title("4.1 Houston Market")

    houston = data["houston"]
    total_houston = sum(h["million_tons"] for h in houston)

    pdf.body_text(
        f"Houston is the nation's largest cement import port, handling {total_houston:.1f} million metric tons "
        f"during the analysis period. The port's infrastructure includes multiple terminal facilities "
        f"operated by major cement companies and independent terminal operators. Houston's position "
        f"at the intersection of Gulf shipping lanes and the US rail network enables distribution "
        f"to markets across Texas, Oklahoma, and the Midwest."
    )

    pdf.subsection_title("Houston Import Flows by Origin and Importer")
    headers = ["Origin Country", "Importer", "Shipments", "Volume (MM MT)"]
    table_data = [[safe_str(h.get("origin_country")), safe_str(h.get("importer"), 20), safe_num(h.get("shipments")), f"{safe_num(h.get('million_tons')):.2f}"] for h in houston[:15]]
    pdf.add_table(headers, table_data, [45, 60, 35, 50])

    pdf.body_text(
        "The Houston market is characterized by intense competition among established importers. "
        "Turkey represents the dominant source, with Houston Cement Company, SESCO, and Argos "
        "as major importers of Turkish product. Vietnamese cement also enters through Houston, "
        "typically en route to Texas and Southwest distribution. The diversity of source countries "
        "and importers creates a competitive pricing environment."
    )

    pdf.subsection_title("Competitive Dynamics")
    pdf.body_text(
        "Key competitors in the Houston market include:"
    )

    pdf.bullet_point(
        "Houston Cement Company: Dominant position in Turkish imports with approximately 3.7 MM MT volume. "
        "Established terminal infrastructure and customer relationships."
    )
    pdf.bullet_point(
        "CEMEX: Integrated producer/importer with terminal operations supporting both imports and "
        "domestic distribution. Leverages Mexican and Mediterranean supply sources."
    )
    pdf.bullet_point(
        "SESCO (Sesco Cement Corp): Significant importer of Turkish cement with 1.3+ MM MT volume. "
        "Focus on bulk distribution to regional markets."
    )
    pdf.bullet_point(
        "Argos USA: Colombian-owned with integrated supply from parent company plus Turkish imports. "
        "Strong regional distribution network."
    )
    pdf.bullet_point(
        "IMI: Major presence at Corpus Christi with Turkish supply, competing for Texas market share."
    )

    pdf.add_page()
    pdf.subsection_title("Market Serviceable from Houston")
    pdf.body_text(
        "Houston-based terminals can economically serve the following markets via rail and truck:"
    )

    pdf.bullet_point("Primary Markets: Houston metro, Dallas-Fort Worth, San Antonio, Austin (rail/truck)")
    pdf.bullet_point("Secondary Markets: Oklahoma City, Tulsa, Midland/Odessa (rail)")
    pdf.bullet_point("Extended Markets: Kansas City, Memphis, Little Rock (rail with competitive freight)")
    pdf.bullet_point("Competitive Overlap: Louisiana (competition with Gramercy), New Mexico (competition with El Paso)")

    pdf.body_text(
        "The Texas market represents the largest single-state cement consumption in the US, driven "
        "by population growth, commercial construction, and infrastructure investment. Houston terminals "
        "capture significant market share through combination of competitive pricing, rail economics, "
        "and established distribution relationships."
    )

    pdf.section_title("4.2 Tampa/Florida Market")

    tampa = data["tampa"]
    florida_ports = data["florida_ports"]
    total_florida = sum(p["million_tons"] for p in florida_ports)

    pdf.body_text(
        f"Florida ports collectively handle {total_florida:.1f} million metric tons of cement imports, "
        f"making the state a critical import gateway for the Southeast construction market. Tampa, "
        f"with 3.3 MM MT, serves as the primary West Florida terminal, while Port Everglades and "
        f"Jacksonville provide coverage for South and Northeast Florida respectively."
    )

    pdf.subsection_title("Florida Port Volumes")
    headers = ["Port", "Shipments", "Volume (MM MT)", "Countries", "Importers"]
    table_data = [[safe_str(p.get("port"), 40), safe_num(p.get("shipments")), f"{safe_num(p.get('million_tons')):.2f}", safe_num(p.get("countries")), safe_num(p.get("importers"))] for p in florida_ports]
    pdf.add_table(headers, table_data, [75, 30, 35, 30, 30])

    pdf.subsection_title("Tampa Import Detail")
    headers = ["Origin Country", "Importer", "Shipments", "Volume (MM MT)"]
    table_data = [[safe_str(t.get("origin_country")), safe_str(t.get("importer"), 20), safe_num(t.get("shipments")), f"{safe_num(t.get('million_tons')):.2f}"] for t in tampa]
    pdf.add_table(headers, table_data, [50, 60, 35, 45])

    pdf.body_text(
        "Tampa's import profile shows concentration among a small number of major importers. "
        "Titan dominates Greek imports, leveraging its integrated supply chain from Greek production "
        "facilities. Turkish cement enters through multiple importers, creating competitive pressure "
        "on pricing. The Florida market's strong fundamentals - population growth, tourism infrastructure, "
        "and limited domestic production - support sustained import demand."
    )

    pdf.add_page()
    pdf.subsection_title("Market Serviceable from Tampa")
    pdf.body_text(
        "Tampa-based operations can economically serve:"
    )

    pdf.bullet_point("Primary Markets: Tampa Bay metro, Orlando, Southwest Florida (truck)")
    pdf.bullet_point("Secondary Markets: North Florida, Jacksonville area (rail/truck competitive)")
    pdf.bullet_point("Extended Markets: Southeast Georgia (rail with competitive freight)")
    pdf.bullet_point("Competitive Overlap: South Florida (competition with Everglades), Georgia (competition with Savannah)")

    pdf.body_text(
        "Florida's cement consumption is driven by residential construction (particularly single-family), "
        "commercial development, and infrastructure projects. The state's exposure to hurricane-related "
        "reconstruction creates episodic demand spikes. Competition from domestic production at Titan's "
        "Pennsuco plant and imported cement through Everglades requires strategic pricing and service "
        "differentiation."
    )

    pdf.section_title("4.3 New Orleans/Louisiana Opportunity")

    louisiana = data["louisiana"]

    pdf.body_text(
        "The Louisiana market presents an attractive expansion opportunity, centered on the Port of "
        "Gramercy and potential New Orleans-area terminal development. Louisiana's strategic position "
        "at the mouth of the Mississippi River system provides unique distribution advantages for "
        "cement reaching inland markets."
    )

    pdf.subsection_title("Louisiana Import Activity")
    headers = ["Port", "Origin", "Importer", "Shipments", "Volume (MM MT)"]
    table_data = [[safe_str(l.get("port"), 25), safe_str(l.get("origin_country")), safe_str(l.get("importer"), 18), safe_num(l.get("shipments")), f"{safe_num(l.get('million_tons')):.2f}"] for l in louisiana[:12] if l]
    pdf.add_table(headers, table_data, [50, 35, 45, 30, 30])

    pdf.body_text(
        "The Port of Gramercy currently handles approximately 3.5 million metric tons of cement imports, "
        "primarily from Turkey, Algeria, and other Mediterranean sources. The port offers deep-water "
        "access, rail connections to major Class I railroads, and proximity to the Mississippi River "
        "barge system. Current operators include Argos, CEMEX, and Heidelberg, each with established "
        "terminal infrastructure."
    )

    pdf.subsection_title("Strategic Advantages of Louisiana Positioning")
    pdf.bullet_point(
        "Mississippi River Access: Barge distribution enables cost-effective supply to Memphis, "
        "St. Louis, and Midwest interior markets not efficiently served by coastal rail."
    )
    pdf.bullet_point(
        "Rail Connectivity: Multiple Class I connections (BNSF, UP, NS, CSXT) provide distribution "
        "flexibility to diverse market destinations."
    )
    pdf.bullet_point(
        "Gulf Coast Synergies: Geographic positioning between Houston and Tampa operations enables "
        "supply chain optimization and market coverage coordination."
    )
    pdf.bullet_point(
        "Petrochemical Market: Louisiana's petrochemical and industrial base generates stable cement "
        "demand for specialized applications and infrastructure maintenance."
    )

    pdf.add_page()
    pdf.subsection_title("Market Serviceable from Louisiana")
    pdf.body_text(
        "Louisiana-based terminals can economically serve:"
    )

    pdf.bullet_point("Primary Markets: New Orleans metro, Baton Rouge, Louisiana industrial corridor (truck)")
    pdf.bullet_point("River Markets: Memphis, St. Louis, Quad Cities, Minneapolis-St. Paul (barge)")
    pdf.bullet_point("Rail Markets: Jackson MS, Birmingham, Atlanta, Little Rock (rail)")
    pdf.bullet_point("Competitive Overlap: Houston territory (Texas Gulf), Mobile (Alabama)")

    pdf.body_text(
        "The Louisiana opportunity complements existing Houston and Tampa operations by extending "
        "market reach into the Mississippi River corridor and bridging the geographic gap between "
        "Texas and Florida coverage. Terminal development or acquisition in the Gramercy/New Orleans "
        "area would create a Gulf Coast network with comprehensive regional coverage."
    )

    pdf.section_title("4.4 Gulf Coast Competitive Landscape")

    gulf_production = data["gulf_production"]

    pdf.body_text(
        "Gulf Coast cement supply combines domestic production and imports, creating a competitive "
        "environment characterized by price sensitivity and logistical efficiency. The following "
        "analysis examines the domestic production base and import competition:"
    )

    pdf.subsection_title("Gulf Coast Domestic Production")
    headers = ["State", "Company", "Plant", "Capacity (MTPA)"]
    table_data = [[safe_str(p.get("state")), safe_str(p.get("company"), 20), safe_str(p.get("plant_name"), 22), f"{safe_num(p.get('capacity_mtpa')):.2f}"] for p in gulf_production[:15]]
    pdf.add_table(headers, table_data, [35, 55, 60, 40])

    pdf.body_text(
        "Texas hosts the largest concentration of Gulf Coast production, with 11 plants totaling "
        "approximately 13 MTPA. Key producers include Holcim (Midlothian), CEMEX (New Braunfels), "
        "Martin Marietta (Midlothian), and Texas Lehigh. Florida adds 7 plants with 10.4 MTPA, "
        "though import penetration remains high due to strong demand growth exceeding local capacity."
    )

    pdf.body_text(
        "The competitive dynamic between domestic production and imports creates price equilibrium "
        "influenced by production costs, freight economics, and regional demand conditions. Importers "
        "typically compete on delivered price, requiring efficient terminal operations and "
        "distribution networks to overcome freight disadvantages versus domestic production."
    )

    # =========================================================================
    # EAST COAST MARKET ANALYSIS
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("5. East Coast Market Analysis")

    pdf.body_text(
        "The East Coast cement market extends from Florida through New England, encompassing diverse "
        "regional economies and construction markets. This section analyzes import activity and "
        "competitive dynamics at major East Coast ports, with emphasis on markets serviceable by "
        "potential new terminal locations."
    )

    pdf.section_title("5.1 Southeast: Georgia and Carolinas")

    savannah = data["savannah"]

    pdf.body_text(
        "The Southeast corridor from Savannah through the Carolinas represents a growing cement "
        "market driven by population migration, manufacturing investment, and infrastructure "
        "development. Limited domestic production capacity in this region creates favorable "
        "conditions for import terminals."
    )

    pdf.subsection_title("Georgia Ports Authority (Savannah)")
    pdf.body_text(
        "Savannah serves as the primary Southeast import gateway, handling 3.7 million metric tons "
        "during the analysis period. The port's deep-water access, modern container and bulk "
        "handling infrastructure, and excellent rail connectivity (NS, CSXT) enable efficient "
        "distribution throughout the Southeast."
    )

    headers = ["Origin Country", "Importer", "Shipments", "Volume (MM MT)"]
    table_data = [[safe_str(s.get("origin_country")), safe_str(s.get("importer"), 22), safe_num(s.get("shipments")), f"{safe_num(s.get('million_tons')):.2f}"] for s in savannah[:10]]
    pdf.add_table(headers, table_data, [50, 60, 35, 45])

    pdf.body_text(
        "UAE cement represents a significant source through Savannah, with Hollingshead Cement as "
        "the primary importer handling 1.78 million metric tons. Turkish and other Mediterranean "
        "sources also enter through Savannah, distributed by multiple importers. The diversity of "
        "sources and importers creates competitive pricing dynamics."
    )

    pdf.subsection_title("Market Serviceable from Savannah")
    pdf.bullet_point("Primary Markets: Atlanta metro, Augusta, Macon, Savannah area (rail/truck)")
    pdf.bullet_point("Secondary Markets: Charlotte, Greenville-Spartanburg, Columbia SC (rail)")
    pdf.bullet_point("Extended Markets: Birmingham, Chattanooga, Nashville (rail competitive)")
    pdf.bullet_point("Competitive Overlap: North Florida (competition with Jacksonville), Tennessee (competition with Gulf)")

    pdf.body_text(
        "The Atlanta metropolitan area represents the largest demand center serviceable from "
        "Savannah, with strong fundamentals in commercial construction and infrastructure investment. "
        "Southeast population growth continues to drive residential construction demand, supporting "
        "sustained import volumes."
    )

    pdf.add_page()
    pdf.section_title("5.2 Mid-Atlantic: Virginia and Maryland")

    virginia = data["virginia"]

    pdf.body_text(
        "The Mid-Atlantic region from Virginia through Maryland serves the Washington DC metropolitan "
        "area and surrounding construction markets. Port of Virginia (Norfolk) provides the primary "
        "import gateway, with approximately 1.9 million metric tons during the analysis period."
    )

    pdf.subsection_title("Port of Virginia (Norfolk)")
    headers = ["Origin Country", "Importer", "Shipments", "Volume (MM MT)"]
    table_data = [[safe_str(v.get("origin_country")), safe_str(v.get("importer"), 22), safe_num(v.get("shipments")), f"{safe_num(v.get('million_tons')):.2f}"] for v in virginia[:8]]
    pdf.add_table(headers, table_data, [50, 60, 35, 45])

    pdf.body_text(
        "Greek cement through Titan dominates the Norfolk import profile, reflecting Titan's "
        "integrated supply chain serving the Mid-Atlantic market. The port offers excellent "
        "rail connectivity to inland markets and highway access to the Washington DC area."
    )

    pdf.subsection_title("Market Serviceable from Norfolk")
    pdf.bullet_point("Primary Markets: Hampton Roads, Richmond, Washington DC metro (truck/rail)")
    pdf.bullet_point("Secondary Markets: Baltimore, Raleigh-Durham, Virginia interior (rail)")
    pdf.bullet_point("Extended Markets: Pittsburgh, Central Pennsylvania (rail competitive)")
    pdf.bullet_point("Competitive Overlap: North Carolina (competition with Wilmington), Philadelphia (competition with Delaware River)")

    pdf.body_text(
        "The Washington DC metropolitan area represents the largest demand center, driven by "
        "federal infrastructure projects, commercial development, and residential construction. "
        "Limited domestic production in the immediate area creates sustained import demand, though "
        "competition from Argos's Martinsburg WV plant (2.2 MTPA) influences market pricing."
    )

    pdf.section_title("5.3 Northeast: NY/NJ Metro and New England")

    nynj = data["nynj"]
    providence = data["providence"]

    pdf.body_text(
        "The Northeast market encompasses the NY/NJ metropolitan area, the nation's largest "
        "population center, and the New England states. Import terminals at Newark, Providence, "
        "and Boston serve this fragmented but substantial market."
    )

    pdf.subsection_title("NY/NJ Metro (Newark)")
    pdf.body_text(
        "The New York/Newark port complex handles approximately 3.2 million metric tons, "
        "primarily from Canada and Greece. The market is characterized by concentrated importer "
        "activity and established distribution relationships."
    )

    headers = ["Origin Country", "Importer", "Shipments", "Volume (MM MT)"]
    table_data = [[safe_str(n.get("origin_country")), safe_str(n.get("importer"), 22), safe_num(n.get("shipments")), f"{safe_num(n.get('million_tons')):.2f}"] for n in nynj[:8]]
    pdf.add_table(headers, table_data, [50, 60, 35, 45])

    pdf.body_text(
        "Canadian cement (primarily from McInnis/Votorantim) and Greek cement (through Titan) "
        "dominate the NY/NJ import profile. The market's large scale and diverse construction "
        "activity create opportunities for multiple suppliers, though established relationships "
        "present barriers to new entrant market share capture."
    )

    pdf.add_page()
    pdf.subsection_title("New England (Providence)")
    headers = ["Origin Country", "Importer", "Shipments", "Volume (MM MT)"]
    table_data = [[safe_str(p.get("origin_country")), safe_str(p.get("importer"), 22), safe_num(p.get("shipments")), f"{safe_num(p.get('million_tons')):.2f}"] for p in providence[:6]]
    pdf.add_table(headers, table_data, [50, 60, 35, 45])

    pdf.body_text(
        "Providence serves as the primary New England import gateway, with Canadian and European "
        "sources predominating. The market is smaller but stable, driven by construction activity "
        "in the Boston metropolitan area and broader New England economy."
    )

    pdf.subsection_title("Market Serviceable from Northeast Ports")
    pdf.body_text("From Newark:")
    pdf.bullet_point("Primary Markets: NYC metro, North Jersey, Long Island (truck/barge)")
    pdf.bullet_point("Secondary Markets: Philadelphia, Connecticut, Hudson Valley (rail/truck)")

    pdf.body_text("From Providence:")
    pdf.bullet_point("Primary Markets: Boston metro, Rhode Island, Connecticut (truck)")
    pdf.bullet_point("Secondary Markets: New Hampshire, Maine, Vermont (truck)")

    pdf.section_title("5.4 East Coast Competitive Landscape")

    east_production = data["east_coast_production"]

    pdf.body_text(
        "East Coast domestic production is more limited than Gulf Coast capacity, creating "
        "structural import dependence in many markets. The following table summarizes East Coast "
        "production capacity:"
    )

    headers = ["State", "Company", "Plant", "Capacity (MTPA)"]
    table_data = [[safe_str(p.get("state")), safe_str(p.get("company"), 20), safe_str(p.get("plant_name"), 22), f"{safe_num(p.get('capacity_mtpa')):.2f}" if p.get('capacity_mtpa') else "N/A"] for p in east_production[:12]]
    pdf.add_table(headers, table_data, [35, 55, 60, 40])

    pdf.body_text(
        "New York hosts the largest East Coast production concentration, with Holcim's Ravena "
        "plant (2.2 MTPA) as the major facility. The Argos Martinsburg plant in West Virginia "
        "(2.2 MTPA) serves Mid-Atlantic markets. Limited production in the Southeast corridor "
        "(Georgia, Carolinas) creates favorable import economics for Savannah-based distribution."
    )

    pdf.body_text(
        "Competitive dynamics on the East Coast are influenced by: (1) Canadian supply pressure "
        "in Northeast markets via both vessel and rail; (2) Greek cement through Titan's integrated "
        "operations; (3) Turkish and other Mediterranean imports through multiple terminals; and "
        "(4) limited but strategically positioned domestic production. Successful market participation "
        "requires competitive landed costs and reliable supply chain execution."
    )

    # =========================================================================
    # CANADIAN COMPETITION ANALYSIS
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("6. Canadian Competition Analysis")

    canada = data["canada_imports"]
    canada_importers = data["canada_importers"]

    pdf.body_text(
        "Canadian cement represents a significant competitive factor in US markets, particularly "
        "for East Coast and Great Lakes regions. Canada supplies approximately 8.3 million metric "
        "tons to the US market through two primary channels: vessel shipments via Great Lakes and "
        "coastal ports, and cross-border rail movements through multiple border crossings."
    )

    pdf.section_title("6.1 Vessel-to-Rail Competition")

    pdf.body_text(
        "Canadian cement enters the US via vessel at the following major ports:"
    )

    headers = ["Port", "Shipments", "Volume (MM MT)"]
    table_data = [[safe_str(c.get("port"), 50), safe_num(c.get("shipments")), f"{safe_num(c.get('million_tons')):.2f}"] for c in canada]
    pdf.add_table(headers, table_data, [100, 40, 50])

    pdf.body_text(
        "The Great Lakes route provides Canadian producers access to Midwest markets, with Detroit "
        "as the primary gateway. Vessel movements through Seattle and other Pacific Northwest ports "
        "serve West Coast markets. This vessel-based supply chain is seasonal, with Great Lakes "
        "shipping constrained by winter ice conditions (typically December through March)."
    )

    pdf.subsection_title("Major Canadian Importers")
    headers = ["Importer", "Shipments", "Volume (MM MT)", "Ports Used"]
    table_data = [[safe_str(c.get("importer"), 30), safe_num(c.get("shipments")), f"{safe_num(c.get('million_tons')):.2f}", safe_num(c.get("ports"))] for c in canada_importers]
    pdf.add_table(headers, table_data, [80, 35, 40, 35])

    pdf.body_text(
        "Votorantim, operating through McInnis USA, dominates Canadian cement flows to the US. "
        "The McInnis cement plant in Port-Daniel-Gascons, Quebec, commissioned in 2017, provides "
        "5 MTPA of modern, efficient production capacity strategically positioned for East Coast "
        "distribution. McInnis operates integrated terminal and distribution infrastructure at "
        "multiple US locations."
    )

    pdf.section_title("6.2 Cross-Border Rail Competition")

    pdf.body_text(
        "Beyond vessel shipments, Canadian cement reaches US markets via cross-border rail movements. "
        "This rail-based supply chain operates year-round without seasonal constraints, providing "
        "competitive supply to markets within economic rail distance of Canadian production facilities."
    )

    pdf.subsection_title("Key Cross-Border Rail Corridors")
    pdf.bullet_point(
        "Detroit-Windsor: Major rail crossing connecting Ontario production to Michigan and "
        "Midwest markets. Multiple Class I railroads (CN, CP) provide interchange options."
    )
    pdf.bullet_point(
        "Buffalo-Niagara: Rail crossing connecting Ontario production to New York and Northeast "
        "markets via NS and CSXT interchanges."
    )
    pdf.bullet_point(
        "Pacific Northwest: Vancouver BC connections to Seattle, Portland, and US West Coast "
        "via BNSF and UP rail corridors."
    )

    pdf.body_text(
        "St. Marys Cement (Votorantim subsidiary) operates several Canadian plants capable of "
        "serving US markets via rail. The company's Wisconsin-based distribution capabilities "
        "extend Canadian supply influence into the Upper Midwest."
    )

    pdf.add_page()
    pdf.section_title("6.3 Strategic Implications")

    pdf.body_text(
        "Canadian competition has several strategic implications for US market positioning:"
    )

    pdf.subsection_title("Northeast Market Pressure")
    pdf.body_text(
        "The McInnis facility's proximity to the US East Coast creates competitive pressure for "
        "any Northeast terminal development. Canadian cement can reach NY/NJ and New England markets "
        "at competitive delivered costs, requiring careful analysis of terminal economics and pricing "
        "strategy. However, Canadian supply is concentrated among limited producers, potentially "
        "creating supply diversification value for alternative import sources."
    )

    pdf.subsection_title("Great Lakes Market Dynamics")
    pdf.body_text(
        "Great Lakes markets (Michigan, Ohio, Illinois, Wisconsin) experience significant Canadian "
        "supply influence, particularly during the shipping season. However, winter supply constraints "
        "create seasonal opportunities for alternative suppliers with year-round rail access. "
        "Understanding customer procurement patterns and inventory management practices is essential "
        "for competitive positioning in these markets."
    )

    pdf.subsection_title("Limited Gulf Coast Impact")
    pdf.body_text(
        "Canadian cement has minimal presence in Gulf Coast markets due to unfavorable logistics "
        "economics. The distance from Canadian production to Gulf Coast consumption centers exceeds "
        "economic rail or vessel distances, protecting Gulf Coast positions from Canadian competition. "
        "This analysis supports continued focus on Gulf Coast expansion strategies."
    )

    pdf.subsection_title("East Coast Considerations")
    pdf.body_text(
        "For East Coast terminal development, Canadian competition must be factored into market "
        "sizing and pricing assumptions. Markets south of the NY/NJ area (Mid-Atlantic, Southeast) "
        "experience less Canadian pressure due to distance, making these regions potentially more "
        "attractive for new terminal development than Northeast locations."
    )

    # =========================================================================
    # INFRASTRUCTURE AND LOGISTICS
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("7. Infrastructure and Logistics")

    pdf.section_title("7.1 Rail Network Coverage")

    rail = data["rail_summary"]
    plants_state = data["plants_by_state"]

    pdf.body_text(
        "Rail connectivity is a critical success factor for cement distribution, enabling cost-effective "
        "movement of bulk product to inland markets beyond economical truck distances. Analysis of "
        "the US rail network reveals extensive coverage of cement facilities:"
    )

    headers = ["Facility Type", "Total", "Rail Served", "Coverage %"]
    table_data = [[safe_str(r.get("facility_type")), safe_num(r.get("total")), safe_num(r.get("rail_served")), f"{100*safe_num(r.get('rail_served'))/safe_num(r.get('total'), 1):.0f}%"] for r in rail if safe_num(r.get("total")) > 2]
    pdf.add_table(headers, table_data, [60, 40, 40, 50])

    pdf.body_text(
        "Cement plants show 88% rail service coverage, reflecting the industry's reliance on rail "
        "for both inbound raw material movements and outbound product distribution. Distribution "
        "terminals, ready-mix operations, and aggregate facilities also maintain high rail connectivity, "
        "enabling integrated supply chain operations."
    )

    pdf.subsection_title("Rail Coverage by State (Cement Plants)")
    top_states = [p for p in plants_state if p["capacity_mtpa"] and p["capacity_mtpa"] > 1][:15]
    headers = ["State", "Plants", "Capacity (MTPA)", "Rail Served"]
    table_data = [[safe_str(p.get("state")), safe_num(p.get("plants")), f"{safe_num(p.get('capacity_mtpa')):.2f}" if p.get("capacity_mtpa") else "N/A", safe_num(p.get("rail_served"))] for p in top_states]
    pdf.add_table(headers, table_data, [50, 35, 50, 55])

    pdf.body_text(
        "Major production states maintain comprehensive rail coverage, with Texas, California, "
        "Missouri, and Florida all showing strong rail service percentages. This infrastructure "
        "supports efficient distribution from both domestic plants and import terminals."
    )

    pdf.section_title("7.2 Distribution Infrastructure")

    pdf.body_text(
        "Cement distribution infrastructure encompasses multiple modes and facility types, creating "
        "a complex logistics network linking production/import points to end-use customers. Key "
        "infrastructure elements include:"
    )

    pdf.subsection_title("Terminal Types")
    pdf.bullet_point(
        "Import Terminals: Deep-water facilities with pneumatic unloading, storage silos, and "
        "rail/truck loading capabilities. Typical throughput capacity 0.5-2.0 MTPA per berth."
    )
    pdf.bullet_point(
        "Distribution Terminals: Inland facilities receiving rail shipments for local truck distribution. "
        "Enable market coverage extension beyond port truck radius."
    )
    pdf.bullet_point(
        "Blending Facilities: Specialized terminals for producing blended cements and performance products. "
        "Add value through product customization."
    )

    pdf.subsection_title("Transportation Economics")
    pdf.body_text(
        "Cement transportation economics favor bulk movement modes for longer distances:"
    )
    pdf.bullet_point("Truck: Economical to approximately 150-200 miles; 25-30 ton loads typical")
    pdf.bullet_point("Rail: Economical beyond 200 miles; 100-110 ton covered hopper cars standard")
    pdf.bullet_point("Barge: Most economical per ton-mile; practical only for river-adjacent markets")
    pdf.bullet_point("Vessel: Intercontinental movement; 30,000-50,000 MT shipments typical for cement")

    pdf.body_text(
        "Terminal positioning should optimize coverage of demand centers within each transportation "
        "mode's economic range, while considering rail and barge connectivity for extended market access."
    )

    # =========================================================================
    # MARKET ENTRY CONSIDERATIONS
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("8. Market Entry Considerations")

    pdf.section_title("8.1 Site Selection Factors")

    pdf.body_text(
        "Selection of new terminal locations should consider multiple strategic and operational factors:"
    )

    pdf.subsection_title("Port Infrastructure")
    pdf.bullet_point("Draft depth: Minimum 40 feet for efficient Handymax/Supramax vessel operations")
    pdf.bullet_point("Berth availability: Dedicated or priority access for cement vessel discharge")
    pdf.bullet_point("Land availability: 10-20 acres typical for integrated terminal development")
    pdf.bullet_point("Utility infrastructure: Electrical capacity for pneumatic handling systems")

    pdf.subsection_title("Rail Connectivity")
    pdf.bullet_point("Class I railroad access: Direct connection to BNSF, UP, NS, or CSXT preferred")
    pdf.bullet_point("Interchange options: Multiple carrier access improves distribution flexibility")
    pdf.bullet_point("Track capacity: Sufficient for unit train or multi-car block operations")
    pdf.bullet_point("Yard facilities: Railcar storage and switching capabilities")

    pdf.subsection_title("Market Access")
    pdf.bullet_point("Truck radius: Major demand centers within 150-mile economical truck distance")
    pdf.bullet_point("Rail market: Viable rail destinations within 600-mile competitive rail range")
    pdf.bullet_point("Competitor position: Assessment of existing terminal capacity and utilization")
    pdf.bullet_point("Growth outlook: Construction activity trends and infrastructure investment plans")

    pdf.section_title("8.2 Competitive Positioning")

    pdf.body_text(
        "Successful market entry requires clear competitive positioning relative to established players:"
    )

    pdf.subsection_title("Cost Leadership")
    pdf.body_text(
        "Achieving delivered cost parity or advantage requires: (1) Efficient vessel operations with "
        "competitive freight rates from source; (2) Modern terminal handling with high throughput "
        "and low operating cost; (3) Optimized rail logistics with favorable carrier relationships; "
        "and (4) Scale sufficient to support fixed cost absorption."
    )

    pdf.subsection_title("Service Differentiation")
    pdf.body_text(
        "Beyond price competition, service factors influence customer decisions: (1) Supply reliability "
        "with consistent availability and delivery performance; (2) Product range including specialty "
        "cements and blends; (3) Technical support for customer applications; and (4) Flexible delivery "
        "scheduling accommodating customer operations."
    )

    pdf.subsection_title("Market Development")
    pdf.body_text(
        "New market entry may require investment in customer development: (1) Specification development "
        "with regional DOTs and specifying agencies; (2) Ready-mix producer relationships; (3) Precast "
        "and specialty product supply; and (4) Project-specific supply commitments for major construction."
    )

    pdf.add_page()
    pdf.section_title("8.3 Strategic Recommendations")

    pdf.body_text(
        "Based on the analysis presented in this report, the following strategic recommendations "
        "are offered for consideration:"
    )

    pdf.subsection_title("Gulf Coast Expansion")
    pdf.body_text(
        "1. New Orleans/Louisiana Development: The Port of Gramercy corridor offers compelling "
        "economics for terminal development or acquisition. Key advantages include Mississippi River "
        "access for barge distribution to Midwest markets, multiple Class I rail connections, and "
        "geographic positioning that complements existing Houston and Tampa operations. Recommended "
        "actions include site evaluation, competitive analysis of existing operators, and supply "
        "chain modeling for target markets."
    )

    pdf.body_text(
        "2. Houston Optimization: Continue investment in Houston terminal efficiency and rail "
        "distribution capabilities. Consider capacity expansion if throughput constraints emerge. "
        "Monitor competitor activity and market share trends."
    )

    pdf.body_text(
        "3. Tampa Market Defense: Florida market fundamentals remain strong. Focus on customer "
        "retention, service quality, and competitive pricing to maintain market position against "
        "Titan and other importers."
    )

    pdf.subsection_title("East Coast Development")
    pdf.body_text(
        "4. Southeast Priority: Savannah-to-Norfolk corridor presents favorable supply-demand "
        "dynamics with limited domestic production and growing demand. Initial focus on Mid-Atlantic "
        "(Norfolk/Virginia) or Southeast (Savannah/Georgia) depending on site availability and "
        "competitive positioning analysis. Canadian competition is less impactful in these markets "
        "versus Northeast."
    )

    pdf.body_text(
        "5. Northeast Caution: NY/NJ and New England markets face significant Canadian competition "
        "and established importer positions. Market entry would require compelling cost advantages "
        "or service differentiation. Consider these markets as secondary priority after establishing "
        "Southeast/Mid-Atlantic presence."
    )

    pdf.subsection_title("Supply Chain Considerations")
    pdf.body_text(
        "6. Source Diversification: Maintain supply relationships with multiple source countries "
        "(Turkey, Greece, Vietnam, Colombia) to ensure supply security and procurement leverage. "
        "Evaluate long-term supply agreements versus spot market procurement strategies."
    )

    pdf.body_text(
        "7. Rail Partnership: Develop strategic relationships with Class I railroads serving target "
        "markets. Rail economics are critical for inland market penetration from coastal terminals."
    )

    # =========================================================================
    # DATA APPENDIX
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("9. Data Appendix")

    pdf.body_text(
        "This appendix provides supplementary data tables supporting the analysis presented in "
        "this report. Data sources include the Global Energy Monitor (GEM) cement plant database, "
        "Panjiva trade intelligence, USGS cement statistics, and proprietary logistics databases."
    )

    pdf.section_title("A.1 Complete Import Source Country Data")
    countries = data["imports_by_country"]
    headers = ["Country", "Shipments", "Million MT", "Share %", "Ports"]
    table_data = [[safe_str(c.get("origin_country")), safe_num(c.get("shipments")), f"{safe_num(c.get('million_tons')):.2f}", f"{safe_num(c.get('pct_share')):.1f}", safe_num(c.get("ports_served"))] for c in countries]
    pdf.add_table(headers, table_data, [50, 35, 35, 30, 40])

    pdf.add_page()
    pdf.section_title("A.2 Complete US Producer Data")
    producers = data["producers"]
    headers = ["Company", "Plants", "Capacity MTPA", "Share %"]
    table_data = [[safe_str(p.get("company"), 30), safe_num(p.get("plants")), f"{safe_num(p.get('capacity_mtpa')):.2f}", f"{safe_num(p.get('market_share')):.1f}"] for p in producers]
    pdf.add_table(headers, table_data, [85, 30, 40, 35])

    pdf.add_page()
    pdf.section_title("A.3 Top 25 Import Flows")
    flows = data["trade_flows"][:25]
    headers = ["Origin", "US Port", "Importer", "Shipments", "MM MT"]
    table_data = [[safe_str(f.get("origin_country"), 12), safe_str(f.get("port"), 25), safe_str(f.get("importer"), 15), safe_num(f.get("shipments")), f"{safe_num(f.get('million_tons')):.2f}"] for f in flows]
    pdf.add_table(headers, table_data, [30, 55, 45, 25, 25])

    pdf.add_page()
    pdf.section_title("A.4 Competitor Import Positions")
    competitors = data["competitor_imports"]
    headers = ["Importer", "Total MM MT", "Gulf", "Florida", "Georgia", "NY/NJ"]
    table_data = [[safe_str(c.get("importer"), 20), f"{safe_num(c.get('total_million_tons')):.2f}", f"{safe_num(c.get('gulf_mt')):.2f}", f"{safe_num(c.get('florida_mt')):.2f}", f"{safe_num(c.get('georgia_mt')):.2f}", f"{safe_num(c.get('nynj_mt')):.2f}"] for c in competitors]
    pdf.add_table(headers, table_data, [55, 30, 25, 25, 25, 30])

    # Save PDF
    output_path = "output/US_Cement_Market_Intelligence_Report.pdf"
    pdf.output(output_path)
    print(f"Report saved to: {output_path}")
    print(f"Total pages: {pdf.page_no()}")

if __name__ == "__main__":
    generate_report()
