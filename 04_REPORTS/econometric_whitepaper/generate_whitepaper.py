"""
Generate Econometric Model Technical Documentation PDF using FPDF2
Pure Python - no external system dependencies required.
"""

from fpdf import FPDF
from pathlib import Path
from datetime import date

OUTPUT_DIR = Path(r"G:\My Drive\LLM\econometric_model_documentation")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TODAY = date.today().strftime("%Y-%m-%d")
TODAY_DISPLAY = date.today().strftime("%B %d, %Y")


class TechDocPDF(FPDF):
    """Custom PDF class for technical documentation."""

    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='Letter')
        self.set_auto_page_break(auto=True, margin=25)
        self.current_section = ""
        self.is_cover = False

    def header(self):
        if self.page_no() <= 1 or self.is_cover:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, self.current_section, align="R", new_x="LMARGIN", new_y="NEXT")
        self.line(20, 15, self.w - 20, 15)
        self.ln(3)

    def footer(self):
        if self.page_no() <= 1 or self.is_cover:
            return
        self.set_y(-20)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.line(20, self.h - 22, self.w - 20, self.h - 22)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def cover_page(self):
        self.is_cover = True
        self.add_page()
        self.ln(60)
        self.set_font("Helvetica", "B", 26)
        self.set_text_color(26, 58, 92)
        self.multi_cell(0, 12, "Econometric Model\nTechnical Documentation", align="C")
        self.ln(10)
        self.set_font("Helvetica", "", 14)
        self.set_text_color(74, 106, 140)
        self.multi_cell(0, 8, "Barge, Rail, and Port Economic Impact Systems\nArchitecture, Methodology, Data Sources, and System Requirements", align="C")
        self.ln(25)
        self.set_font("Helvetica", "", 13)
        self.set_text_color(51, 51, 51)
        self.cell(0, 8, "William S. Davis III", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(3)
        self.set_font("Helvetica", "", 12)
        self.set_text_color(85, 85, 85)
        self.cell(0, 8, TODAY_DISPLAY, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(15)
        self.set_font("Helvetica", "I", 11)
        self.set_text_color(119, 119, 119)
        self.cell(0, 8, "Version 1.0 -- Initial Technical Audit", align="C", new_x="LMARGIN", new_y="NEXT")
        self.is_cover = False

    def section_heading(self, title, level=1):
        """Add a section heading."""
        if level == 1:
            self.add_page()
            self.current_section = title
            self.set_font("Helvetica", "B", 18)
            self.set_text_color(26, 58, 92)
            self.multi_cell(0, 10, title)
            self.set_draw_color(26, 58, 92)
            self.line(20, self.get_y(), self.w - 20, self.get_y())
            self.ln(6)
        elif level == 2:
            self.ln(4)
            self.set_font("Helvetica", "B", 13)
            self.set_text_color(26, 58, 92)
            self.multi_cell(0, 8, title)
            self.set_draw_color(200, 200, 200)
            self.line(20, self.get_y(), self.w - 20, self.get_y())
            self.ln(4)
        elif level == 3:
            self.ln(3)
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(42, 74, 108)
            self.multi_cell(0, 7, title)
            self.ln(2)
        elif level == 4:
            self.ln(2)
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(58, 90, 124)
            self.multi_cell(0, 6, title)
            self.ln(1)

    def body_text(self, text):
        """Add body text."""
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(26, 26, 26)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def bold_text(self, text):
        """Add bold text inline."""
        self.set_font("Helvetica", "B", 9.5)
        self.set_text_color(26, 26, 26)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def code_block(self, code):
        """Add a code block."""
        self.set_fill_color(244, 245, 247)
        self.set_draw_color(208, 212, 216)
        x = self.get_x()
        y = self.get_y()
        self.set_font("Courier", "", 7.5)
        self.set_text_color(30, 30, 30)
        lines = code.strip().split('\n')
        h = len(lines) * 4 + 6
        # Check page break
        if y + h > self.h - 25:
            self.add_page()
            y = self.get_y()
        self.rect(20, y, self.w - 40, h, style='DF')
        self.set_xy(23, y + 3)
        for line in lines:
            self.cell(0, 4, line, new_x="LMARGIN", new_y="NEXT")
            self.set_x(23)
        self.set_y(y + h + 2)
        self.ln(2)

    def equation_block(self, text, label=""):
        """Add an equation block."""
        self.set_fill_color(248, 249, 251)
        self.set_draw_color(26, 58, 92)
        y = self.get_y()
        if y + 12 > self.h - 25:
            self.add_page()
            y = self.get_y()
        self.set_fill_color(248, 249, 251)
        self.rect(20, y, self.w - 40, 10, style='F')
        # Left border
        self.set_draw_color(26, 58, 92)
        self.line(20, y, 20, y + 10)
        self.line(20.5, y, 20.5, y + 10)
        self.line(21, y, 21, y + 10)
        self.set_xy(25, y + 2)
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(26, 26, 26)
        self.cell(self.w - 80, 6, text)
        if label:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(119, 119, 119)
            self.cell(30, 6, label, align="R")
        self.set_y(y + 13)

    def note_box(self, text):
        """Add an info note box."""
        self.set_fill_color(232, 240, 254)
        y = self.get_y()
        self.set_font("Helvetica", "", 8.5)
        lines = self.multi_cell(self.w - 50, 4.5, text, split_only=True)
        h = len(lines) * 4.5 + 6
        if y + h > self.h - 25:
            self.add_page()
            y = self.get_y()
        self.rect(20, y, self.w - 40, h, style='F')
        self.set_draw_color(66, 133, 244)
        self.line(20, y, 20, y + h)
        self.line(20.5, y, 20.5, y + h)
        self.line(21, y, 21, y + h)
        self.set_xy(25, y + 3)
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(26, 26, 26)
        self.multi_cell(self.w - 50, 4.5, text)
        self.set_y(y + h + 3)

    def add_table(self, headers, rows, col_widths=None):
        """Add a formatted table."""
        if col_widths is None:
            n = len(headers)
            available = self.w - 40
            col_widths = [available / n] * n

        self.set_font("Helvetica", "B", 7.5)
        self.set_fill_color(26, 58, 92)
        self.set_text_color(255, 255, 255)
        self.set_draw_color(26, 58, 92)

        x_start = 20
        self.set_x(x_start)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 6, h, border=1, fill=True, align="L")
        self.ln()

        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(26, 26, 26)
        self.set_draw_color(200, 200, 200)

        for row_idx, row in enumerate(rows):
            if row_idx % 2 == 0:
                self.set_fill_color(247, 249, 251)
            else:
                self.set_fill_color(255, 255, 255)

            # Check page break
            if self.get_y() + 6 > self.h - 25:
                self.add_page()
                # Re-draw headers
                self.set_font("Helvetica", "B", 7.5)
                self.set_fill_color(26, 58, 92)
                self.set_text_color(255, 255, 255)
                self.set_x(x_start)
                for i, h in enumerate(headers):
                    self.cell(col_widths[i], 6, h, border=1, fill=True, align="L")
                self.ln()
                self.set_font("Helvetica", "", 7.5)
                self.set_text_color(26, 26, 26)

            self.set_x(x_start)
            for i, val in enumerate(row):
                self.cell(col_widths[i], 5.5, str(val), border='B', fill=True, align="L")
            self.ln()

        self.ln(3)

    def status_label(self, text, status="operational"):
        """Add a colored status label."""
        if status == "operational":
            self.set_fill_color(230, 244, 234)
            self.set_text_color(19, 115, 51)
        elif status == "prototype":
            self.set_fill_color(254, 247, 224)
            self.set_text_color(176, 96, 0)
        elif status == "inprogress":
            self.set_fill_color(232, 240, 254)
            self.set_text_color(26, 115, 232)
        self.set_font("Helvetica", "B", 8)
        w = self.get_string_width(text) + 6
        self.cell(w, 5, text, fill=True)
        self.set_text_color(26, 26, 26)
        self.ln(7)

    def bullet_list(self, items):
        """Add a bulleted list."""
        self.set_font("Helvetica", "", 9)
        self.set_text_color(26, 26, 26)
        for item in items:
            x = self.get_x()
            self.set_x(25)
            self.cell(5, 5, "-")
            self.multi_cell(self.w - 55, 5, item)
            self.ln(1)
        self.ln(2)

    def file_ref(self, text):
        """Inline file reference (just return formatted string)."""
        return text


def build_document():
    """Build the complete technical documentation PDF."""
    pdf = TechDocPDF()
    pdf.set_margins(20, 20, 20)

    # ================================================================
    # COVER PAGE
    # ================================================================
    pdf.cover_page()

    # ================================================================
    # TABLE OF CONTENTS
    # ================================================================
    pdf.add_page()
    pdf.current_section = "Table of Contents"
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(26, 58, 92)
    pdf.cell(0, 10, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(26, 58, 92)
    pdf.line(20, pdf.get_y(), pdf.w - 20, pdf.get_y())
    pdf.ln(6)

    toc_items = [
        (0, "Section 1: Executive Overview"),
        (0, "Section 2: Barge Cost Model (project_barge)"),
        (1, "2.1 Model Purpose and Scope"),
        (1, "2.2 Econometric Methodology"),
        (1, "2.3 Data Sources and Inputs"),
        (1, "2.4 Data Pipeline and Processing Logic"),
        (1, "2.5 Outputs and Deliverables"),
        (1, "2.6 Current Status and Known Limitations"),
        (0, "Section 3: Rail Cost Model (project_rail)"),
        (1, "3.1 Model Purpose and Scope"),
        (1, "3.2 Econometric Methodology"),
        (1, "3.3 Data Sources and Inputs"),
        (1, "3.4 Data Pipeline and Processing Logic"),
        (1, "3.5 Outputs and Deliverables"),
        (1, "3.6 Current Status and Known Limitations"),
        (0, "Section 4: Port Economic Impact Model (project_port_nickle)"),
        (1, "4.1 Model Purpose and Scope"),
        (1, "4.2 Econometric Methodology"),
        (1, "4.3 Data Sources and Inputs"),
        (1, "4.4 Data Pipeline and Processing Logic"),
        (1, "4.5 Outputs and Deliverables"),
        (1, "4.6 Current Status and Known Limitations"),
        (0, "Section 5: Cross-Model Integration"),
        (1, "5.1 Shared Data Sources and Common Infrastructure"),
        (1, "5.2 Model Interdependencies"),
        (0, "Section 6: System Architecture Overview"),
        (1, "6.1 Technology Stack Summary"),
        (1, "6.2 Directory and File Structure"),
        (0, "Annex A: Consolidated Python Package Requirements"),
        (0, "Annex B: External Data Source Registry"),
        (0, "Annex C: Formula and Model Reference"),
        (0, "Annex D: System Prerequisites and Environment Setup"),
    ]

    for level, text in toc_items:
        if level == 0:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_x(25)
            pdf.ln(2)
        else:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_x(35)
        pdf.set_text_color(26, 26, 26)
        pdf.cell(0, 5, text, new_x="LMARGIN", new_y="NEXT")

    # ================================================================
    # SECTION 1: EXECUTIVE OVERVIEW
    # ================================================================
    pdf.section_heading("Section 1: Executive Overview")

    pdf.section_heading("Purpose of This Document", 2)
    pdf.body_text(f"This document provides a comprehensive technical audit of three interrelated econometric modeling systems developed for freight transportation and regional economic impact analysis. It documents every formula, data source, processing pipeline, and system dependency found in the codebase as of {TODAY_DISPLAY}. The intended audience includes transportation economists, developers who will maintain or extend these systems, and stakeholders who need to understand the methodological underpinnings of the models.")

    pdf.section_heading("Summary of the Three Model Systems", 2)

    pdf.add_table(
        ["Project", "Purpose", "Geography", "Status"],
        [
            ["project_barge", "Waterway barge cost modeling, route optimization, rate forecasting", "U.S. Inland Waterway System", "Operational/Prototype"],
            ["project_rail", "Rail freight cost (URCS), waybill analytics, rate benchmarking", "U.S. Class I railroad network", "In Development"],
            ["project_port_nickle", "Regional economic impact for Braithwaite Cement Terminal", "SE Louisiana (5-parish area)", "Prototype"],
        ],
        [30, 60, 45, 30]
    )

    pdf.section_heading("Model Interrelationships", 2)
    pdf.body_text("The three models share a common analytical thread: understanding the economics of freight movement and port development in the Gulf Coast region. The barge cost model calculates waterway transport cost-competitiveness versus rail. The rail cost model provides URCS-based costing for precise rail cost estimates. The port economic impact model evaluates regional economic effects of a cement terminal served by barge and rail. Together, they form a multimodal freight economics toolkit.")

    # ================================================================
    # SECTION 2: BARGE COST MODEL
    # ================================================================
    pdf.section_heading("Section 2: Barge Cost Model")

    pdf.section_heading("2.1 Model Purpose and Scope", 2)
    pdf.body_text("The barge cost model (project_barge) calculates the total cost of transporting cargo by barge on the U.S. inland waterway system. It serves two primary functions:")
    pdf.bullet_list([
        "Route Costing: Given origin/destination (river + mile marker), calculates optimal waterway route, locks, transit time, and total cost including fuel, crew, lock fees, and terminal charges.",
        "Rate Forecasting: Uses USDA Grain Transportation Report data to forecast near-term barge freight rates across 7 Mississippi River zones using VAR and SpVAR models.",
    ])
    pdf.body_text("Covers all major navigable rivers: Mississippi (Upper/Lower), Ohio, Illinois, Missouri, Tennessee, Arkansas, Cumberland, Monongahela, and Allegheny. Supports multi-river routing through 8 known river confluences.")

    pdf.section_heading("2.2 Econometric Methodology", 2)
    pdf.section_heading("2.2.1 Operational Cost Functions", 3)
    pdf.body_text("The barge model implements two parallel cost calculation frameworks: CostEngine (used with FastAPI backend) and BargeCostCalculator (used in Streamlit costing tool).")

    pdf.section_heading("Fuel Cost", 4)
    pdf.equation_block("Fuel_gallons = Consumption_rate x (Transit_hours / 24)", "(Eq. 1)")
    pdf.equation_block("Fuel_cost = Fuel_gallons x Price_per_gallon", "(Eq. 2)")
    pdf.body_text("CostEngine implementation (cost_engine.py:72-77):")
    pdf.code_block("transit_days = transit_time_hours / 24\ntotal_gallons = consumption_rate * transit_days\ntotal_cost = total_gallons * fuel_price")
    pdf.body_text("BargeCostCalculator implementation (barge_cost_calculator.py:701):")
    pdf.code_block("fuel_cost = (transit_hours / 24) * self.FUEL_GALLONS_PER_DAY * self.FUEL_PRICE_PER_GALLON")

    pdf.add_table(
        ["Variable", "Description", "CostEngine", "BargeCostCalc", "Unit"],
        [
            ["Consumption_rate", "Daily fuel consumption", "100", "3,000", "gal/day"],
            ["Price_per_gallon", "Diesel fuel price", "3.50", "3.50", "USD/gal"],
        ],
        [30, 40, 25, 30, 20]
    )

    pdf.note_box("Note: CostEngine uses 100 gal/day (single vessel) while BargeCostCalculator uses 3,000 gal/day (full towboat pushing 15-barge tow). These reflect different operational scales.")

    pdf.section_heading("Crew Cost", 4)
    pdf.equation_block("Crew_cost = Crew_size x Daily_Rate x (Total_hours / 24)", "(Eq. 3)")
    pdf.body_text("CostEngine (cost_engine.py:99-107): crew=8, $800/day. BargeCostCalculator (barge_cost_calculator.py:702): crew=12, $1,200/day.")

    pdf.section_heading("Lock Passage Fees", 4)
    pdf.equation_block("Lock_fees = N_locks x Fee_per_lock ($50)", "(Eq. 4)")

    pdf.section_heading("Lock Delay Estimation", 4)
    pdf.equation_block("Delay = 3.5h (double lockage) or 1.5h (single lockage)", "(Eq. 5)")
    pdf.body_text("Implementation (barge_cost_calculator.py:49-55): Double lockage when tow_length > chamber_length.")

    pdf.section_heading("Terminal Fees", 4)
    pdf.equation_block("Terminal_fees = Fee_origin + Fee_destination ($750 each)", "(Eq. 6)")

    pdf.section_heading("Total Route Cost", 4)
    pdf.equation_block("Total = Fuel + Crew + Lock_fees + Terminal_fees", "(Eq. 7)")

    pdf.section_heading("Cost Efficiency Metrics", 4)
    pdf.equation_block("Cost_per_ton = Total_Cost / Cargo_tons", "(Eq. 8)")
    pdf.equation_block("Cost_per_ton_mile = Total_Cost / (Cargo_tons x Distance)", "(Eq. 9)")

    pdf.section_heading("Transit Time", 4)
    pdf.equation_block("Transit_hours = Distance_miles / Speed_mph", "(Eq. 10)")
    pdf.equation_block("Total_hours = Transit_hours + Sum(Lock_Delays)", "(Eq. 11)")

    pdf.add_table(
        ["Speed Parameter", "Value", "Unit"],
        [
            ["Downstream (loaded)", "8.0", "mph"],
            ["Upstream (loaded)", "5.0", "mph"],
            ["Average (default)", "6.0", "mph"],
        ],
        [55, 30, 30]
    )

    pdf.section_heading("Rail Comparison", 4)
    pdf.equation_block("Rail_cost_per_ton = Rail_rate ($0.04/ton-mi) x Distance", "(Eq. 12)")
    pdf.equation_block("Barge_Savings = Rail_cost - Barge_cost", "(Eq. 13)")

    pdf.section_heading("2.2.2 USDA Barge Rate Forecasting", 3)
    pdf.equation_block("Rate_forecast = mean(Rate_t-1...t-4) per USDA segment", "(Eq. 14)")
    pdf.equation_block("Total_Rate = Rate_forecast + $2.00/ton markup", "(Eq. 15)")
    pdf.body_text("Implementation (barge_cost_calculator.py:785-809): Uses most recent 4-week average from USDA rate data, or VAR model forecast if available.")

    pdf.section_heading("2.2.3 Vector Autoregressive (VAR) Model", 3)
    pdf.equation_block("r_t = Phi_1*r_{t-1} + ... + Phi_p*r_{t-p} + epsilon_t", "(Eq. 16)")
    pdf.body_text("Where r_t is a 7x1 vector of barge rates (one per USDA segment), Phi_i are 7x7 coefficient matrices, p is the lag order selected by AIC (max 10). Implementation (03_var_estimation.py:134-153) uses statsmodels VAR. Forecast horizons: 1-5 weeks ahead.")

    pdf.section_heading("2.2.4 Spatial VAR (SpVAR) Model", 3)
    pdf.equation_block("r_t = rho*W*r_t + Phi_1*r_{t-1} + ... + Phi_p*r_{t-p} + eps", "(Eq. 17)")
    pdf.body_text("Where W is a 7x7 row-standardized inverse-distance spatial weight matrix and rho is the spatial autocorrelation parameter.")

    pdf.equation_block("W_ij = (1/d_ij) / Sum_j(1/d_ij) for i!=j; W_ii=0", "(Eq. 18)")
    pdf.body_text("d_ij = absolute difference in river miles from Gulf between segments. Implementation (04_spvar_estimation.py:82-112).")

    pdf.add_table(
        ["Segment", "Description", "Miles from Gulf"],
        [
            ["1", "Twin Cities to Lock 13", "1,800"],
            ["2", "Mid-Mississippi (Lock 13 to St. Louis)", "1,200"],
            ["3", "Illinois River", "850"],
            ["4", "Ohio River", "600"],
            ["5", "Cairo to Memphis", "400"],
            ["6", "Memphis to Greenville", "200"],
            ["7", "Greenville to New Orleans", "50"],
        ],
        [20, 75, 40]
    )

    pdf.equation_block("rho = mean_i[Corr(y_i,t, (Wy)_i,t)]", "(Eq. 19)")
    pdf.equation_block("y_transformed = y - rho * W * y", "(Eq. 20)")

    pdf.section_heading("2.3 Data Sources and Inputs", 2)
    pdf.add_table(
        ["Data Source", "Provider", "Format", "Description"],
        [
            ["Waterway Network Links", "BTS", "CSV", "Segments w/ nodes, river names, miles, lengths"],
            ["Waterway Network Nodes", "BTS", "CSV", "Junction points on waterway network"],
            ["Lock Characteristics", "BTS", "CSV", "Lock dimensions, location (04_bts_locks/)"],
            ["Navigation Facilities", "BTS", "CSV", "Dock locations (05_bts_navigation_fac/)"],
            ["Link Tonnages", "BTS/USACE", "CSV", "Historical tonnage by waterway link"],
            ["USDA Barge Rates", "USDA AMS", "CSV", "Weekly rates for 7 Mississippi segments"],
            ["Vessel Register", "Various", "CSV", "Ship characteristics (01.03_vessels/)"],
        ],
        [35, 25, 15, 70]
    )

    pdf.section_heading("2.4 Data Pipeline and Processing Logic", 2)
    pdf.body_text("Route calculation pipeline:")
    pdf.bullet_list([
        "1. Data Loading: Lock CSV, waterway link CSV, graph pickle loaded by BargeCostCalculator.load_data()",
        "2. Graph Construction: NetworkX undirected graph from waterway links (ANODE -> BNODE with length)",
        "3. Node Resolution: Origin/destination (river + mile) mapped to nearest graph node",
        "4. Junction Detection: KNOWN_JUNCTIONS (8 confluences) searched for multi-river routes",
        "5. Lock Detection: Locks between origin/destination mile markers identified per segment",
        "6. Rate Forecasting: Segments mapped to USDA zones; 4-week average + $2 markup",
        "7. Cost Calculation: Fuel, crew, lock fees computed; rail comparison at $0.04/ton-mile",
    ])

    pdf.section_heading("2.5 Outputs and Deliverables", 2)
    pdf.bullet_list([
        "Streamlit Dashboard (costing_tool/app.py): Interactive web app for route cost calculation",
        "FastAPI REST API (src/api/): Programmatic routing and costing endpoints",
        "Forecasting outputs: VAR/SpVAR model pickles, rolling forecast CSVs, accuracy JSONs, plots",
        "RouteResult dataclass: Comprehensive result with distance, locks, time, rates, costs",
    ])

    pdf.section_heading("2.6 Current Status and Known Limitations", 2)
    pdf.status_label("OPERATIONAL: BargeCostCalculator costing tool with Streamlit frontend", "operational")
    pdf.status_label("OPERATIONAL: VAR and SpVAR forecasting pipeline with trained models", "operational")
    pdf.status_label("PROTOTYPE: FastAPI/PostgreSQL routing engine", "prototype")
    pdf.body_text("Known limitations:")
    pdf.bullet_list([
        "Two parallel cost parameter sets with different values should be harmonized",
        "Lock fees ($50/passage) hardcoded; USACE does not charge per-passage on most locks",
        "Rail comparison uses flat $0.04/ton-mile rather than commodity/distance-specific rates",
        "SpVAR rho estimated via simplified correlation method rather than full MLE",
        "Lower Mississippi routing uses approximate mile markers",
    ])

    # ================================================================
    # SECTION 3: RAIL COST MODEL
    # ================================================================
    pdf.section_heading("Section 3: Rail Cost Model")

    pdf.section_heading("3.1 Model Purpose and Scope", 2)
    pdf.body_text("The rail cost model (project_rail) implements the STB's Uniform Rail Costing System (URCS) methodology to calculate variable cost of rail freight. Primary purposes:")
    pdf.bullet_list([
        "Rate Benchmarking: Compare actual revenues against URCS costs for R/VC ratio analysis",
        "Waybill Analytics: Analyze STB Carload Waybill Sample via DuckDB analytical database",
        "Network Routing: Build rail graph from NARN geospatial data for distance calculation",
    ])
    pdf.body_text("Covers entire U.S. Class I railroad network with year-specific unit costs for 2019-2023 and inflation-adjusted estimates back to 2006. Regional variants: Eastern District, Western District, system average.")

    pdf.section_heading("3.2 Econometric Methodology", 2)
    pdf.section_heading("3.2.1 URCS Variable Cost Calculation", 3)
    pdf.body_text("Implementation: rail_analytics/src/urcs_model.py:412-565. Decomposes rail costs into five categories.")

    pdf.section_heading("Service Unit Calculations", 4)
    pdf.equation_block("Loaded Car-Miles = Route_Miles x Num_Cars", "(Eq. 21)")
    pdf.equation_block("Empty Car-Miles = Loaded_CM x Empty_Ratio (0.5-0.7)", "(Eq. 22)")
    pdf.equation_block("Total Car-Miles = Loaded + Empty", "(Eq. 23)")
    pdf.equation_block("Gross Ton-Miles = (Tons/Car + Tare) x Loaded_CM", "(Eq. 24)")
    pdf.equation_block("Train-Miles = (Miles x Cars) / Cars_per_Train", "(Eq. 25)")
    pdf.equation_block("Locomotive-Miles = Train-Miles x Locos_per_Train", "(Eq. 26)")
    pdf.body_text("Cars per train: 100 (unit train), 65 (manifest). Locomotives: 2.0 (unit), 1.5 (manifest). Empty ratio: 0.7 for coal/grain hoppers, 0.5 for others.")

    pdf.section_heading("Transit Time Estimation", 4)
    pdf.equation_block("Transit_Days = ceil(Miles/(Speed*Hours/Day) + Terminal_Days)", "(Eq. 27)")
    pdf.body_text("Speed: 22 mph (unit train), 18 mph (manifest). Operating hours: 18/day. Terminal days: 1 (unit), 2 (manifest).")

    pdf.section_heading("Line-Haul Costs", 4)
    pdf.equation_block("LH = CM*UC_cm + TrM*UC_tm + GTM*UC_gtm + LM*UC_lm", "(Eq. 28)")

    pdf.section_heading("Terminal Costs", 4)
    pdf.equation_block("Terminal = 2*Cars*UC_switch + Yard_Days*UC_yard", "(Eq. 29)")

    pdf.section_heading("Car Ownership Costs", 4)
    pdf.equation_block("Car = LH_Days*UC_car_line + Yard_Days*UC_car_yard", "(Eq. 30)")

    pdf.section_heading("Administrative Costs", 4)
    pdf.equation_block("Admin = Cars * (UC_originated + UC_terminated)", "(Eq. 31)")

    pdf.section_heading("Loss and Damage", 4)
    pdf.equation_block("L&D = (Commodity_Value / 1000) x UC_loss_damage", "(Eq. 32)")

    pdf.section_heading("Special Services", 4)
    pdf.equation_block("Special = (Handling_Factor - 1.0) x LH + Hazmat($150/car)", "(Eq. 33)")

    pdf.section_heading("Total Variable Cost", 4)
    pdf.equation_block("Total_VC = LH + Terminal + Car + Admin + Special + L&D", "(Eq. 34)")
    pdf.equation_block("Unit Train: Total_VC = Total_VC x 0.85 (15% discount)", "(Eq. 35)")

    pdf.section_heading("3.2.2 Revenue-to-Variable-Cost (R/VC) Ratio", 3)
    pdf.equation_block("R/VC = (Actual_Revenue / URCS_Variable_Cost) x 100%", "(Eq. 36)")
    pdf.body_text("STB jurisdiction threshold: 180%. Rates exceeding this are subject to rate reasonableness review.")

    pdf.section_heading("3.2.3 URCS Unit Costs (2023 System Average)", 3)
    pdf.add_table(
        ["Cost Component", "Unit Cost", "Unit"],
        [
            ["Car-mile", "$0.42", "per car-mile"],
            ["Train-mile", "$48.50", "per train-mile"],
            ["Gross ton-mile", "$0.0085", "per GTM"],
            ["Locomotive-mile", "$3.85", "per loco-mile"],
            ["Car-day (yard)", "$28.50", "per car-day"],
            ["Switch move", "$42.00", "per switch"],
            ["Terminal switch", "$185.00", "per terminal switch"],
            ["Car-day (line)", "$45.00", "per car-day"],
            ["Car-day (total)", "$52.00", "per car-day"],
            ["Carload originated", "$85.00", "per carload"],
            ["Carload terminated", "$65.00", "per carload"],
            ["Loss & damage", "$0.35", "per $1,000 value"],
        ],
        [40, 30, 40]
    )

    pdf.section_heading("3.2.4 Haversine Distance", 3)
    pdf.equation_block("d = R * 2 * arcsin(sqrt(sin^2(dphi/2) + cos*cos*sin^2(dl/2)))", "(Eq. 37)")
    pdf.body_text("R = 3,959 miles. 1.25 circuity factor applied for rail. Used in graph_builder.py:158-177 and DuckDB views (urcs_model.py:681-697).")

    pdf.section_heading("3.3 Data Sources and Inputs", 2)
    pdf.add_table(
        ["Data Source", "Provider", "Format", "Description"],
        [
            ["STB Waybill Sample", "STB", "CSV", "1% sample of all rail movements"],
            ["STB URCS Worktables", "STB", "Hardcoded", "Annual unit costs by region (2019-2023)"],
            ["NARN Rail Lines", "NTAD/BTS", "GeoJSON", "Geometry, owner, track class, signals"],
            ["NARN Rail Nodes", "NTAD/BTS", "GeoJSON", "Junction/terminal nodes (FRANODEID)"],
            ["FAF5 Commodity Flows", "FHWA/BTS", "CSV", "Freight analysis commodity flow data"],
            ["BEA Economic Areas", "BEA", "Hardcoded", "179 regions with coordinates"],
            ["STCC Codes", "AAR/STB", "Hardcoded", "45+ commodity codes with metadata"],
        ],
        [35, 25, 18, 65]
    )

    pdf.section_heading("3.4 Data Pipeline and Processing Logic", 2)
    pdf.body_text("Database initialization (database.py:27-46):")
    pdf.bullet_list([
        "1. STCC Dimension: 45+ commodity codes with industry knowledge",
        "2. BEA Dimension: 50+ Economic Areas with lat/lon coordinates",
        "3. Car Type Dimension: 15 STB car types",
        "4. Time Dimension: Daily calendar 2015-2030",
        "5. Waybill Fact Table: CSV chunks loaded via DuckDB read_csv_auto()",
        "6. Analytical Views: v_commodity_flows, v_top_od_pairs, v_commodity_summary",
        "7. URCS Views: v_rvc_analysis, v_rvc_by_commodity, v_rvc_by_distance",
    ])

    pdf.section_heading("3.5 Outputs and Deliverables", 2)
    pdf.bullet_list([
        "DuckDB Analytical Database: Star schema with fact_waybill and dimension tables",
        "URCS Cost Estimates: Detailed URCSCostBreakdown with 5 cost components",
        "R/VC Ratio Analysis: Shipment and commodity-level distributions",
        "Rail Network Graph: NetworkX MultiDiGraph for shortest-path routing",
    ])

    pdf.section_heading("3.6 Current Status and Known Limitations", 2)
    pdf.status_label("OPERATIONAL: URCS cost calculation engine", "operational")
    pdf.status_label("OPERATIONAL: DuckDB database and analytical views", "operational")
    pdf.status_label("IN DEVELOPMENT: Rail network graph builder", "inprogress")
    pdf.body_text("Known limitations:")
    pdf.bullet_list([
        "URCS unit costs hardcoded rather than dynamically loaded from STB website",
        "Pre-2019 costs use 3% annual deflation estimate - actual STB values may differ",
        "Distance estimation uses Haversine + 1.25x circuity - actual rail distances vary",
        "Two parallel URCS implementations should be consolidated",
        "Unit train discount (15%) is fixed - actual discounts vary by railroad/contract",
    ])

    # ================================================================
    # SECTION 4: PORT ECONOMIC IMPACT MODEL
    # ================================================================
    pdf.section_heading("Section 4: Port Economic Impact Model")

    pdf.section_heading("4.1 Model Purpose and Scope", 2)
    pdf.body_text("The port economic impact model (project_port_nickle) quantifies the regional economic impact of the proposed Braithwaite Cement Terminal & Processing Facility in Plaquemines Parish, Louisiana. Uses LED multiplier methodology calibrated from CCI Methanol Plant precedent (same site, 2014).")
    pdf.body_text("Calculates: employment impacts (direct/indirect/induced), earnings impacts, economic output, tax revenue (state income, local sales, payroll, UI), and construction phase impacts. Geographic scope: SE Louisiana 5-parish labor shed.")

    pdf.section_heading("4.2 Econometric Methodology", 2)
    pdf.section_heading("4.2.1 LED Employment Multiplier", 3)
    pdf.equation_block("Indirect_Jobs = Direct_Jobs x 5.82", "(Eq. 38)")
    pdf.equation_block("Induced_Jobs = Direct_Jobs x 1.5", "(Eq. 39)")
    pdf.equation_block("Total_Jobs = Direct + Indirect + Induced", "(Eq. 40)")
    pdf.body_text("Source: CCI Methanol Plant LED analysis (50 direct -> 291 indirect = 5.82x). Implementation: economic_impact_calculator.py:86-88.")

    pdf.section_heading("4.2.2 Earnings Multiplier", 3)
    pdf.equation_block("Indirect_Wages = Direct_Wages x 0.6 (mult 1.6 - 1)", "(Eq. 41)")
    pdf.equation_block("Induced_Wages = Direct_Wages x 0.3 (mult 1.3 - 1)", "(Eq. 42)")
    pdf.equation_block("Total_Wages = Direct + Indirect + Induced (2.9x)", "(Eq. 43)")

    pdf.section_heading("4.2.3 Output Multiplier", 3)
    pdf.equation_block("Indirect_Output = Direct_Output x 1.2 (mult 2.2 - 1)", "(Eq. 44)")
    pdf.equation_block("Induced_Output = Direct_Output x 0.4 (mult 1.4 - 1)", "(Eq. 45)")
    pdf.equation_block("Total_Output = Direct + Indirect + Induced (3.6x)", "(Eq. 46)")

    pdf.section_heading("4.2.4 Tax Revenue Calculations", 3)
    pdf.equation_block("State_Income_Tax = Total_Wages x Local% x 4.25%", "(Eq. 47)")
    pdf.equation_block("Local_Sales_Tax = Total_Wages x Retail% x 10.5%", "(Eq. 48)")
    pdf.equation_block("Payroll_Tax = Direct_Wages x (7.65% + 2.7%)", "(Eq. 49)")
    pdf.equation_block("Total_Tax = State_Income + Sales + Payroll", "(Eq. 50)")

    pdf.section_heading("4.2.5 Construction Phase Impact", 3)
    pdf.equation_block("Job-Years = Peak_Jobs x Duration_years", "(Eq. 51)")
    pdf.equation_block("Indirect_Constr = Peak_Jobs x 0.5", "(Eq. 52)")
    pdf.equation_block("Induced_Constr = Peak_Jobs x 0.3", "(Eq. 53)")
    pdf.equation_block("Indirect_Wages = Direct x 0.4", "(Eq. 54)")
    pdf.equation_block("Induced_Wages = Direct x 0.2", "(Eq. 55)")

    pdf.section_heading("4.2.6 Multiplier Reference Table", 3)
    pdf.add_table(
        ["Impact Type", "Indirect", "Induced", "Total", "Source"],
        [
            ["Employment", "5.82x", "1.5x", "8.32x", "LED/CCI Methanol"],
            ["Earnings", "1.6x", "1.3x", "2.9x", "Manufacturing typical"],
            ["Output", "2.2x", "1.4x", "3.6x", "Supply chain+consumer"],
        ],
        [30, 20, 20, 20, 40]
    )

    pdf.section_heading("4.2.7 Scenario Definitions", 3)
    pdf.add_table(
        ["Scenario", "Direct Jobs", "Avg Wage", "Revenue", "Constr. Jobs", "Duration"],
        [
            ["Conservative", "75", "$80,000", "$50M", "600", "2.0 yrs"],
            ["Moderate", "125", "$90,000", "$85M", "1,000", "2.5 yrs"],
            ["Optimistic", "200", "$95,000", "$125M", "1,500", "3.0 yrs"],
            ["CCI Historical", "50", "$72,000", "--", "1,000", "2.0 yrs"],
        ],
        [25, 20, 22, 23, 25, 20]
    )

    pdf.section_heading("4.3 Data Sources and Inputs", 2)
    pdf.add_table(
        ["Data Source", "Provider", "Format", "Description"],
        [
            ["QCEW Employment", "BLS", "API/JSON", "Employment/wages for 5 parishes"],
            ["OEWS Wages", "BLS", "API/JSON", "Occupation wages for MSA 35380"],
            ["Census ACS", "Census", "API", "Demographics for workforce analysis"],
            ["LED Multipliers", "Louisiana ED", "Hardcoded", "5.82x from CCI precedent"],
            ["Tax Rates", "LA Dept Revenue", "Hardcoded", "State/local/payroll rates"],
        ],
        [30, 25, 22, 65]
    )

    pdf.section_heading("4.4 Data Pipeline and Processing Logic", 2)
    pdf.bullet_list([
        "1. BLS Data Collection: QCEW API for 5 parish FIPS, OEWS wages for MSA 35380",
        "2. Impact Calculation: LED multipliers applied to scenario inputs",
        "3. Scenario Generation: 4 pre-defined scenarios compared side-by-side",
        "4. Report Output: Text reports and JSON data to data/economic_impact_scenarios/",
    ])

    pdf.section_heading("4.5 Outputs and Deliverables", 2)
    pdf.bullet_list([
        "Scenario comparison reports (text format)",
        "JSON data files (all_scenarios.json)",
        "Employment/wages/output tables with multipliers",
        "Tax revenue projections (annual and 10-year cumulative)",
    ])

    pdf.section_heading("4.6 Current Status and Known Limitations", 2)
    pdf.status_label("OPERATIONAL: Economic impact calculator with 4 scenarios", "operational")
    pdf.status_label("PROTOTYPE: BLS data collection scripts", "prototype")
    pdf.body_text("Known limitations:")
    pdf.bullet_list([
        "Employment multiplier (5.82x) based on single CCI Methanol precedent",
        "No formal I-O tables (BEA/IMPLAN) - relies on simpler multiplier approach",
        "Tax calculations use top marginal rate rather than graduated brackets",
        "No temporal discounting or inflation in 10-year projections",
        "Construction multipliers are estimates, not empirically derived",
        "Household spending percentages sum to 110% (overlap with savings leakage)",
    ])

    # ================================================================
    # SECTION 5: CROSS-MODEL INTEGRATION
    # ================================================================
    pdf.section_heading("Section 5: Cross-Model Integration")

    pdf.section_heading("5.1 Shared Data Sources and Common Infrastructure", 2)
    pdf.add_table(
        ["Data Source", "Used By", "Purpose"],
        [
            ["BTS Network Data", "Barge, Rail", "Waterway network (barge), NARN rail (rail)"],
            ["BEA Economic Areas", "Rail, Port", "O-D classification, regional analysis"],
            ["NetworkX", "Barge, Rail", "Graph pathfinding (both projects)"],
            ["pandas/numpy", "All", "Core data manipulation"],
            ["GeoPandas/Shapely", "Barge, Rail", "Geospatial processing"],
        ],
        [35, 30, 75]
    )

    pdf.section_heading("5.2 Model Interdependencies", 2)
    pdf.body_text("Current interdependencies:")
    pdf.bullet_list([
        "Barge model's rail comparison ($0.04/ton-mile) could use URCS-derived costs from rail model",
        "Port model evaluates terminal served by barge/rail - cost models could provide transport cost inputs",
    ])
    pdf.body_text("Opportunities for further integration:")
    pdf.bullet_list([
        "Feed URCS estimates into barge model for commodity-specific rail benchmarking",
        "Use barge/rail costs as inputs to port model revenue assumptions",
        "Create unified multimodal cost comparison tool",
        "Standardize geographic references (BEA areas) across all models",
    ])

    # ================================================================
    # SECTION 6: SYSTEM ARCHITECTURE
    # ================================================================
    pdf.section_heading("Section 6: System Architecture Overview")

    pdf.section_heading("6.1 Technology Stack Summary", 2)
    pdf.add_table(
        ["Category", "Technology", "Used By"],
        [
            ["Language", "Python 3.10+", "All"],
            ["Data", "pandas, numpy", "All"],
            ["Statistics", "scipy, statsmodels", "Barge"],
            ["Graph/Network", "NetworkX", "Barge, Rail"],
            ["Geospatial", "geopandas, shapely, pyproj", "Barge, Rail"],
            ["Visualization", "matplotlib, plotly, seaborn, folium", "Barge, Rail"],
            ["Web Framework", "Streamlit, FastAPI", "Barge"],
            ["Database", "DuckDB, PostgreSQL/PostGIS", "Rail, Barge"],
            ["ORM", "SQLAlchemy", "Barge"],
            ["Validation", "Pydantic, pydantic-settings", "Barge"],
            ["Task Queue", "Celery + Redis (planned)", "Barge"],
            ["Web Scraping", "requests, beautifulsoup4", "Port"],
        ],
        [30, 60, 40]
    )

    pdf.section_heading("6.2 Directory and File Structure", 2)
    pdf.body_text("project_barge/")
    pdf.code_block("src/engines/cost_engine.py     - CostEngine (fuel/crew/lock/terminal)\nsrc/engines/routing_engine.py  - RoutingEngine (NetworkX Dijkstra/A*)\nsrc/config/settings.py         - Pydantic settings, cost constants\nsrc/models/route.py            - Route/cost/constraint models\ncosting_tool/barge_cost_calculator.py - Unified BargeCostCalculator\ncosting_tool/app.py            - Streamlit dashboard\nforecasting/scripts/01-04      - Rate download, VAR, SpVAR\ndata/                          - BTS waterway, lock, dock data")

    pdf.body_text("project_rail/")
    pdf.code_block("rail_analytics/src/urcs_model.py  - Full URCS implementation (908 lines)\nrail_analytics/src/database.py    - DuckDB analytics database\nrail_cost_model/src/costing/      - Simplified URCS, route costing\nrail_cost_model/src/network/      - NARN graph builder\nrail_cost_model/config/config.yaml - Data source URLs")

    pdf.body_text("project_port_nickle/")
    pdf.code_block("Workforce/braithwaite-workforce-project/scripts/\n  economic_impact_calculator.py    - LED multiplier model\n  collect_bls_data.py              - BLS QCEW/OEWS collection")

    # ================================================================
    # ANNEX A
    # ================================================================
    pdf.section_heading("Annex A: Consolidated Python Package Requirements")

    for category, packages in [
        ("Core Scientific Computing", [
            ("numpy", ">=1.24.0", "All"),
            ("pandas", ">=2.0.0", "All"),
            ("scipy", ">=1.10.0", "Barge"),
        ]),
        ("Econometrics", [
            ("statsmodels", ">=0.14.0", "Barge"),
        ]),
        ("Graph/Network", [
            ("networkx", ">=3.0", "Barge, Rail"),
        ]),
        ("Geospatial", [
            ("geopandas", ">=0.14.0", "Barge, Rail"),
            ("shapely", ">=2.0.0", "Barge, Rail"),
            ("pyproj", ">=3.6.0", "Rail"),
            ("fiona", ">=1.9.0", "Rail"),
        ]),
        ("Visualization", [
            ("matplotlib", ">=3.7.0", "Barge, Rail"),
            ("plotly", ">=5.18.0", "Barge, Rail"),
            ("seaborn", ">=0.12.0", "Barge"),
            ("folium", ">=0.15.0", "Rail"),
        ]),
        ("Web Frameworks", [
            ("streamlit", ">=1.28.0", "Barge"),
            ("fastapi", ">=0.100.0", "Barge"),
            ("uvicorn", ">=0.23.0", "Barge"),
        ]),
        ("Database", [
            ("duckdb", ">=0.9.0", "Rail"),
            ("sqlalchemy", ">=2.0.0", "Barge"),
            ("psycopg2-binary", ">=2.9.0", "Barge"),
        ]),
        ("Configuration", [
            ("pydantic", ">=2.0.0", "Barge"),
            ("pydantic-settings", ">=2.0.0", "Barge"),
            ("python-dotenv", ">=1.0.0", "Barge"),
            ("pyyaml", ">=6.0.0", "Rail"),
        ]),
        ("Data Ingestion", [
            ("requests", ">=2.31.0", "All"),
            ("beautifulsoup4", ">=4.12.0", "Port"),
            ("lxml", ">=4.9.0", "Port"),
        ]),
        ("File Formats", [
            ("openpyxl", ">=3.1.0", "Rail, Port"),
            ("pyarrow", ">=14.0.0", "Rail"),
        ]),
    ]:
        pdf.section_heading(category, 3)
        pdf.add_table(
            ["Package", "Version", "Used By"],
            [[p, v, u] for p, v, u in packages],
            [45, 40, 45]
        )

    # ================================================================
    # ANNEX B
    # ================================================================
    pdf.section_heading("Annex B: External Data Source Registry")

    sources = [
        ["Waterway Links", "BTS", "CSV download", "CSV", "Annual", "Barge", "ANODE, BNODE, RIVERNAME"],
        ["Waterway Nodes", "BTS", "CSV download", "CSV", "Annual", "Barge", "Node ID, coordinates"],
        ["Lock Data", "BTS", "CSV download", "CSV", "Annual", "Barge", "PMSNAME, RIVER, RIVERMI"],
        ["USDA Barge Rates", "USDA AMS", "Download script", "CSV", "Weekly", "Barge", "Date, segment rates"],
        ["STB Waybill", "STB", "Restricted", "CSV", "Annual", "Rail", "Revenue, tons, O-D, STCC"],
        ["URCS Worktables", "STB", "stb.gov", "Hardcoded", "Annual", "Rail", "Unit costs by region"],
        ["NARN Rail Lines", "NTAD/BTS", "ArcGIS REST", "GeoJSON", "Annual", "Rail", "Geometry, owner, class"],
        ["FAF5 Flows", "FHWA/BTS", "Download", "CSV", "5-year", "Rail", "O-D, commodity, tons"],
        ["BLS QCEW", "BLS", "API", "JSON", "Quarterly", "Port", "Employment by parish"],
        ["BLS OEWS", "BLS", "API", "JSON", "Annual", "Port", "Occupation wages MSA"],
        ["Census ACS", "Census", "API", "JSON", "Annual", "Port", "Demographics"],
    ]

    pdf.add_table(
        ["Source", "Provider", "Access", "Format", "Freq.", "Project", "Key Fields"],
        sources,
        [25, 18, 22, 15, 15, 14, 35]
    )

    # ================================================================
    # ANNEX C
    # ================================================================
    pdf.section_heading("Annex C: Formula and Model Reference")

    eqs = [
        ["1", "Fuel gallons = Rate x Hours/24", "Barge", "2.2"],
        ["2", "Fuel cost = Gallons x Price", "Barge", "2.2"],
        ["3", "Crew cost = Size x Rate x Days", "Barge", "2.2"],
        ["4", "Lock fees = N x $50", "Barge", "2.2"],
        ["5", "Lock delay = 3.5h/1.5h", "Barge", "2.2"],
        ["6", "Terminal fees", "Barge", "2.2"],
        ["7", "Total = Fuel+Crew+Lock+Term", "Barge", "2.2"],
        ["8-9", "Cost/ton, Cost/ton-mile", "Barge", "2.2"],
        ["10-11", "Transit & total time", "Barge", "2.2"],
        ["12-13", "Rail comparison & savings", "Barge", "2.2"],
        ["14-15", "USDA rate forecast+markup", "Barge", "2.2"],
        ["16", "VAR model", "Barge", "2.2"],
        ["17", "SpVAR model", "Barge", "2.2"],
        ["18", "Spatial weight matrix W", "Barge", "2.2"],
        ["19", "Spatial parameter rho", "Barge", "2.2"],
        ["20", "Spatial transformation", "Barge", "2.2"],
        ["21-26", "URCS service units", "Rail", "3.2"],
        ["27", "Transit days", "Rail", "3.2"],
        ["28", "Line-haul cost (4 comp.)", "Rail", "3.2"],
        ["29", "Terminal cost", "Rail", "3.2"],
        ["30", "Car ownership cost", "Rail", "3.2"],
        ["31", "Administrative cost", "Rail", "3.2"],
        ["32", "Loss & damage", "Rail", "3.2"],
        ["33", "Special services", "Rail", "3.2"],
        ["34-35", "Total VC + unit train", "Rail", "3.2"],
        ["36", "R/VC ratio", "Rail", "3.2"],
        ["37", "Haversine distance", "Rail", "3.2"],
        ["38-40", "LED employment multipliers", "Port", "4.2"],
        ["41-43", "Earnings multipliers", "Port", "4.2"],
        ["44-46", "Output multipliers", "Port", "4.2"],
        ["47-50", "Tax revenue calcs", "Port", "4.2"],
        ["51-55", "Construction phase", "Port", "4.2"],
    ]

    pdf.add_table(
        ["Eq.", "Formula Description", "Model", "Section"],
        eqs,
        [15, 65, 20, 20]
    )

    # ================================================================
    # ANNEX D
    # ================================================================
    pdf.section_heading("Annex D: System Prerequisites and Environment Setup")

    pdf.section_heading("D.1 Python Version", 2)
    pdf.body_text("Python 3.10 or later required (tested on 3.14 via Miniconda on Windows 11).")

    pdf.section_heading("D.2 Virtual Environment", 2)
    pdf.code_block("python -m venv .venv\n# Windows: .venv\\Scripts\\activate\n# Linux/Mac: source .venv/bin/activate")

    pdf.section_heading("D.3 System-Level Dependencies", 2)
    pdf.bullet_list([
        "PostgreSQL 14+ with PostGIS (optional - for barge transactional DB)",
        "Redis (optional - for Celery async routing)",
        "GDAL/OGR (for Fiona geospatial support - install via conda recommended)",
        "MS Visual C++ Build Tools (Windows - for compiling some packages)",
    ])

    pdf.section_heading("D.4 pip Install", 2)
    pdf.code_block("# Recommended: install geospatial via conda first\nconda install -c conda-forge geopandas shapely pyproj fiona\n\n# Then install everything else\npip install -r requirements.txt")

    pdf.section_heading("D.5 Environment Variables (.env)", 2)
    pdf.code_block("DATABASE_URL=postgresql://postgres:password@localhost:5432/barge_db\nREDIS_URL=redis://localhost:6379/0\nUSACE_LPMS_API_KEY=your_key\nNOAA_API_KEY=your_key\nEIA_API_KEY=your_key\nBLS_API_KEY=your_key")

    pdf.section_heading("D.6 API Keys Required", 2)
    pdf.add_table(
        ["Key Name", "Purpose", "Required?", "Project"],
        [
            ["USACE_LPMS_API_KEY", "Lock Performance data", "Optional", "Barge"],
            ["NOAA_API_KEY", "Weather/water levels", "Optional", "Barge"],
            ["EIA_API_KEY", "Fuel price data", "Optional", "Barge"],
            ["BLS_API_KEY", "BLS employment data", "Recommended", "Port"],
            ["CENSUS_API_KEY", "Census demographics", "Optional", "Port"],
        ],
        [40, 40, 25, 25]
    )

    pdf.section_heading("D.7 Initial Setup Scripts", 2)
    pdf.bullet_list([
        "1. Barge rates: Run project_barge/forecasting/scripts/01_data_download.py",
        "2. Rate preprocessing: Run 02_preprocessing.py",
        "3. VAR model: Run 03_var_estimation.py",
        "4. SpVAR model: Run 04_spvar_estimation.py",
        "5. Rail database: python -c 'from rail_analytics.src.database import init_database; init_database()'",
        "6. BLS data: Run project_port_nickle/.../scripts/collect_bls_data.py",
    ])

    return pdf


def main():
    print("Generating Econometric Model Technical Documentation PDF...")
    print(f"Output directory: {OUTPUT_DIR}")

    pdf = build_document()

    # Save PDF
    pdf_path = OUTPUT_DIR / f"Econometric_Model_Technical_Documentation_{TODAY}.pdf"
    pdf.output(str(pdf_path))
    print(f"  PDF generated: {pdf_path.name}")
    print(f"  PDF size: {pdf_path.stat().st_size / 1024:.0f} KB")

    # Write consolidated requirements.txt
    req_path = OUTPUT_DIR / "requirements.txt"
    req_content = f"""# Consolidated requirements for all three projects
# (project_barge, project_rail, project_port_nickle)
# Generated: {TODAY}

# Core Scientific Computing
numpy>=1.24.0
pandas>=2.0.0
scipy>=1.10.0

# Econometrics and Statistics
statsmodels>=0.14.0

# Graph/Network Analysis
networkx>=3.0

# Geospatial
geopandas>=0.14.0
shapely>=2.0.0
pyproj>=3.6.0
fiona>=1.9.0

# Visualization
matplotlib>=3.7.0
plotly>=5.18.0
seaborn>=0.12.0
folium>=0.15.0

# Web Frameworks
streamlit>=1.28.0
fastapi>=0.100.0
uvicorn>=0.23.0

# Database
duckdb>=0.9.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0

# Data Validation and Configuration
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
pyyaml>=6.0.0

# Data Ingestion and Web Scraping
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0

# File Format Support
openpyxl>=3.1.0
pyarrow>=14.0.0

# Development and Notebooks
jupyterlab>=4.0.0
ipywidgets>=8.1.0
"""
    with open(req_path, "w", encoding="utf-8") as f:
        f.write(req_content)
    print(f"  requirements.txt written: {req_path.name}")

    print(f"\nDone!")
    print(f"  PDF: {pdf_path}")
    print(f"  Requirements: {req_path}")


if __name__ == "__main__":
    main()
