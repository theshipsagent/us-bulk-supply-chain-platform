"""
Freight Report Configuration
Constants, topic keywords, state list, paths.
"""

from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
CHUNKS_DIR = PROJECT_ROOT / "read_rail" / "processed_docs" / "chunks"
DB_PATH = PROJECT_ROOT / "rail_analytics" / "data" / "rail_analytics.duckdb"
PDF_DIR = PROJECT_ROOT / "data" / "state_rail_plans"
OUTPUT_DIR = Path(__file__).parent / "output"
LOGS_DIR = PROJECT_ROOT / "logs"

# ── RAG Parameters ────────────────────────────────────────────────────────────
RAG_TOP_K = 10           # chunks per query from RAG
CHUNKS_PER_TOPIC = 3     # best chunks kept per topic after dedup

# ── 46 states with valid rail plan chunks ─────────────────────────────────────
STATES_46 = {
    "AL": "Alabama",    "AK": "Alaska",       "AZ": "Arizona",      "AR": "Arkansas",
    "CA": "California", "CO": "Colorado",      "CT": "Connecticut",  "DE": "Delaware",
    "FL": "Florida",    "GA": "Georgia",       "IA": "Iowa",         "ID": "Idaho",
    "IL": "Illinois",   "IN": "Indiana",       "KS": "Kansas",       "KY": "Kentucky",
    "LA": "Louisiana",  "MA": "Massachusetts", "MD": "Maryland",     "ME": "Maine",
    "MI": "Michigan",   "MN": "Minnesota",     "MO": "Missouri",     "MS": "Mississippi",
    "MT": "Montana",    "NC": "North Carolina","ND": "North Dakota", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico",    "NV": "Nevada",       "OH": "Ohio",
    "OK": "Oklahoma",   "OR": "Oregon",        "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina","SD": "South Dakota","TN": "Tennessee",   "TX": "Texas",
    "UT": "Utah",       "VT": "Vermont",       "WA": "Washington",   "WV": "West Virginia",
    "WI": "Wisconsin",  "WY": "Wyoming",
}

# ── Topic definitions with query templates ────────────────────────────────────
# {state} is replaced with the full state name at query time.
TOPICS = {
    "freight_corridors": {
        "title": "Major Freight Corridors",
        "queries": [
            "{state} freight corridor",
            "{state} rail line route",
            "{state} mainline",
        ],
    },
    "carriers_railroads": {
        "title": "Carriers & Railroads",
        "queries": [
            "{state} Class I railroad",
            "{state} short line railroad",
            "{state} carrier",
        ],
    },
    "industry_commodities": {
        "title": "Industry & Commodities",
        "queries": [
            "{state} commodity shipped rail",
            "{state} industry served",
            "{state} freight commodity",
        ],
    },
    "junction_points": {
        "title": "Junction Points & Interchanges",
        "queries": [
            "{state} junction point",
            "{state} rail interchange",
            "{state} intermodal terminal",
        ],
    },
    "rail_yard_capacity": {
        "title": "Rail Yard Capacity",
        "queries": [
            "{state} rail yard",
            "{state} classification yard",
            "{state} terminal capacity",
        ],
    },
    "volume_trends": {
        "title": "Volume & Trends",
        "queries": [
            "{state} freight volume tons",
            "{state} carload traffic",
            "{state} rail traffic trend",
        ],
    },
    "bottlenecks": {
        "title": "Bottlenecks & Constraints",
        "queries": [
            "{state} rail bottleneck",
            "{state} capacity constraint",
            "{state} congestion",
        ],
    },
    "efficiency": {
        "title": "Efficiency & Service Quality",
        "queries": [
            "{state} rail efficiency",
            "{state} on-time performance",
            "{state} service quality",
        ],
    },
    "costs_investment": {
        "title": "Costs & Investment",
        "queries": [
            "{state} rail investment",
            "{state} infrastructure cost",
            "{state} capital improvement",
        ],
    },
    "stakeholders": {
        "title": "Stakeholders & Governance",
        "queries": [
            "{state} railroad stakeholder",
            "{state} rail authority",
            "{state} freight advisory",
        ],
    },
}

# ── Federal Report Sources (Phase 1) ─────────────────────────────────────────
FEDERAL_REPORTS = {
    "FRA_National_Rail_Plan": {
        "search_query": "FRA National Rail Plan PDF site:fra.dot.gov OR site:railroads.dot.gov",
        "fallback_urls": [
            "https://railroads.dot.gov/sites/fra.dot.gov/files/2024-12/Preliminary-National-Rail-Plan.pdf",
            "https://railroads.dot.gov/sites/fra.dot.gov/files/fra_net/15124/Preliminary_National_Rail_Plan.pdf",
        ],
        "filename": "FRA_National_Rail_Plan.pdf",
    },
    "STB_Annual_Report": {
        "search_query": "STB Surface Transportation Board annual report PDF site:stb.gov",
        "fallback_urls": [
            "https://www.stb.gov/wp-content/uploads/2024/02/STB-Annual-Report-2023.pdf",
        ],
        "filename": "STB_Annual_Report.pdf",
    },
    "BTS_Freight_Facts": {
        "search_query": "BTS freight facts and figures PDF site:bts.gov",
        "fallback_urls": [
            "https://data.bts.gov/api/views/gkni-2e7n/files/Freight_Facts_Figures.pdf",
            "https://www.bts.gov/sites/bts.dot.gov/files/2024-03/Freight-Facts-Figures-2023.pdf",
        ],
        "filename": "BTS_Freight_Facts_Figures.pdf",
    },
    "AAR_Railroad_Facts": {
        "search_query": "AAR Railroad Facts overview freight PDF site:aar.org",
        "fallback_urls": [
            "https://www.aar.org/wp-content/uploads/2024/02/AAR-Rail-Industry-Overview-2024.pdf",
        ],
        "filename": "AAR_Railroad_Facts.pdf",
    },
    "ASLRRA_Short_Line": {
        "search_query": "ASLRRA short line railroad report PDF site:aslrra.org",
        "fallback_urls": [
            "https://www.aslrra.org/web/About/Short_Line_Facts.aspx",
        ],
        "filename": "ASLRRA_Short_Line_Report.pdf",
    },
}

DOWNLOAD_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/pdf,*/*",
}
