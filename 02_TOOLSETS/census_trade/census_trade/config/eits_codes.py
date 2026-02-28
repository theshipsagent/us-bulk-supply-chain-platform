"""
Census Economic Indicators Time Series (EITS) - Program and Code Definitions

API Base: https://api.census.gov/data/timeseries/eits/{program_code}

All EITS endpoints share the same variable structure:
  - cell_value: The data value
  - data_type_code: What metric (shipments, inventories, orders, etc.)
  - category_code: Industry/sector classification
  - time_slot_id: Time period identifier
  - seasonally_adj: "yes" or "no"
  - geo_level_code: Geographic level
  - time: ISO-8601 date (YYYY-MM)

Required predicate: for=us:*
"""

EITS_API_BASE = "https://api.census.gov/data/timeseries/eits"

# ============================================================
# PROGRAMS (Supply Chain Priority)
# ============================================================

PROGRAMS = {
    # --- Manufacturing (Production Layer) ---
    "m3": {
        "name": "Manufacturers' Shipments, Inventories, and Orders",
        "description": "Monthly data on manufacturing activity: shipments, new/unfilled orders, inventories",
        "supply_chain_layer": "manufacturing",
        "frequency": "monthly",
    },
    "advm3": {
        "name": "Advance Report on Durable Goods",
        "description": "Advance (preliminary) monthly report on durable goods manufacturers",
        "supply_chain_layer": "manufacturing",
        "frequency": "monthly",
    },

    # --- Combined Manufacturing + Trade ---
    "mtis": {
        "name": "Manufacturing and Trade Inventories and Sales",
        "description": "Combined manufacturing, wholesale, and retail inventories and sales",
        "supply_chain_layer": "combined",
        "frequency": "monthly",
    },

    # --- Wholesale (Distribution Layer) ---
    "mwts": {
        "name": "Monthly Wholesale Trade: Sales and Inventories",
        "description": "Wholesale merchant sales and inventories by industry",
        "supply_chain_layer": "wholesale",
        "frequency": "monthly",
    },
    "mwtsadv": {
        "name": "Advance Wholesale Inventories",
        "description": "Preliminary wholesale inventory estimates",
        "supply_chain_layer": "wholesale",
        "frequency": "monthly",
    },

    # --- Retail (Demand Layer) ---
    "mrts": {
        "name": "Monthly Retail Trade and Food Services",
        "description": "Retail and food services sales and inventories",
        "supply_chain_layer": "retail",
        "frequency": "monthly",
    },
    "mrtsadv": {
        "name": "Advance Retail Inventories",
        "description": "Preliminary retail inventory estimates",
        "supply_chain_layer": "retail",
        "frequency": "monthly",
    },
    "marts": {
        "name": "Advance Monthly Sales for Retail and Food Services",
        "description": "Advance (preliminary) monthly retail sales",
        "supply_chain_layer": "retail",
        "frequency": "monthly",
    },

    # --- Services ---
    "qss": {
        "name": "Quarterly Services Survey",
        "description": "Revenue for selected service industries (transport, logistics, etc.)",
        "supply_chain_layer": "services",
        "frequency": "quarterly",
    },

    # --- Financial Health ---
    "qfr": {
        "name": "Quarterly Financial Report",
        "description": "Financial statistics for manufacturing, mining, wholesale, retail corporations",
        "supply_chain_layer": "financial",
        "frequency": "quarterly",
    },

    # --- Other Economic Indicators ---
    "ftd": {
        "name": "U.S. International Trade in Goods and Services",
        "description": "Trade flow data (also available via intltrade API)",
        "supply_chain_layer": "trade",
        "frequency": "monthly",
    },
    "ftdadv": {
        "name": "Advance U.S. International Trade in Goods",
        "description": "Preliminary trade statistics",
        "supply_chain_layer": "trade",
        "frequency": "monthly",
    },
    "bfs": {
        "name": "Business Formation Statistics",
        "description": "New business applications and formations",
        "supply_chain_layer": "ecosystem",
        "frequency": "monthly",
    },
    "resconst": {
        "name": "New Residential Construction",
        "description": "Building permits, housing starts, completions",
        "supply_chain_layer": "construction",
        "frequency": "monthly",
    },
    "ressales": {
        "name": "New Home Sales",
        "description": "New single-family home sales",
        "supply_chain_layer": "construction",
        "frequency": "monthly",
    },
    "vip": {
        "name": "Construction Spending",
        "description": "Value of construction put in place",
        "supply_chain_layer": "construction",
        "frequency": "monthly",
    },
}

# Supply-chain focused subset
SUPPLY_CHAIN_PROGRAMS = {k: v for k, v in PROGRAMS.items()
                         if v["supply_chain_layer"] in
                         ("manufacturing", "combined", "wholesale", "retail")}

# ============================================================
# DATA TYPE CODES (What is being measured)
# ============================================================

DATA_TYPES = {
    "VS":    "Value of Shipments",
    "NO":    "New Orders",
    "UO":    "Unfilled Orders",
    "TI":    "Total Inventories",
    "FI":    "Finished Goods Inventories",
    "WI":    "Work-in-Process Inventories",
    "MI":    "Materials and Supplies Inventories",
    "IS":    "Inventories/Shipments Ratio",
    "US":    "Unfilled Orders/Shipments Ratio",
    "SM":    "Sales (monthly)",
    "IM":    "Inventories (monthly)",
    "IR":    "Inventories/Sales Ratio",
    "MPCSM": "Percent Change in Sales",
    "MPCIM": "Percent Change in Inventories",
    "MPCVS": "Percent Change in Value of Shipments",
    "MPCNO": "Percent Change in New Orders",
    "MPCTI": "Percent Change in Total Inventories",
    "MPCUO": "Percent Change in Unfilled Orders",
    "MPCFI": "Percent Change in Finished Goods Inventories",
    "MPCWI": "Percent Change in Work-in-Process Inventories",
    "MPCMI": "Percent Change in Materials Inventories",
}

# Data types relevant to each supply chain layer
MANUFACTURING_DATA_TYPES = ["VS", "NO", "UO", "TI", "FI", "WI", "MI", "IS", "US"]
WHOLESALE_DATA_TYPES = ["SM", "IM", "IR"]
RETAIL_DATA_TYPES = ["SM", "IM", "IR"]
MTIS_DATA_TYPES = ["SM", "IM", "IR"]

# ============================================================
# CATEGORY CODES (Industry/Sector)
# ============================================================

# --- Manufacturing (M3) Categories ---
M3_CATEGORIES = {
    # Totals
    "MTM": "Total Manufacturing",
    "MDM": "Durable Goods",
    "MNM": "Nondurable Goods",

    # Durable Goods Industries (NAICS 33x)
    "31S": "Wood Products (321)",
    "32S": "Nonmetallic Mineral Products (327)",
    "33S": "Primary Metals (331)",
    "33A": "Iron & Steel Mills (3311,3312)",
    "33C": "Aluminum & Nonferrous (3313,3314)",
    "33D": "Foundries (3315)",
    "33E": "Fabricated Metal Products (332)",
    "33G": "Machinery (333)",
    "33H": "Computers & Electronic Products (334)",
    "33I": "Communications Equipment (3342)",
    "33M": "Electrical Equipment & Appliances (335)",
    "34S": "Transportation Equipment (336)",
    "34A": "Motor Vehicles & Parts (3361-3363)",
    "34B": "Motor Vehicle Bodies, Trailers (3362)",
    "34C": "Motor Vehicle Parts (3363)",
    "34D": "Aircraft & Parts (3364)",
    "34E": "Other Aerospace Products (3364,3369)",
    "34H": "Ships & Boats (3366)",
    "34X": "All Other Durable Goods",
    "35S": "Furniture & Related Products (337)",
    "36S": "Miscellaneous (339)",
    "37S": "Information Technology",

    # Nondurable Goods Industries (NAICS 31x)
    "11S": "Food Products (311)",
    "11A": "Animal Food (3111)",
    "11B": "Grain & Oilseed Milling (3112)",
    "11C": "Sugar & Confectionery (3113)",
    "12S": "Beverage & Tobacco (312)",
    "13S": "Textile Mills (313)",
    "14S": "Textile Product Mills (314)",
    "15S": "Apparel (315)",
    "16S": "Leather (316)",
    "21S": "Paper Products (322)",
    "22S": "Printing (323)",
    "23S": "Petroleum & Coal Products (324)",
    "24S": "Chemical Products (325)",
    "25S": "Plastics & Rubber (326)",
    "26S": "Pharmaceutical & Medicine (3254)",
    "27S": "Other Nondurable Goods",

    # Special aggregations
    "DEF": "Defense (Capital Goods)",
    "NDE": "Nondefense (Capital Goods)",
    "CDG": "Capital Goods - Defense",
    "CNG": "Capital Goods - Nondefense",
    "COG": "Capital Goods - Nondefense ex Aircraft",
    "DAP": "Defense Aircraft & Parts",
    "NAP": "Nondefense Aircraft & Parts",
    "CRP": "Consumer Products",
    "MVP": "Motor Vehicles & Parts",
    "ANM": "All New Manufacturing",
    "BTP": "Building Materials",
    "CMS": "Consumer Materials & Supplies",
    "ITI": "Information Technology Industries",
    "ODG": "Other Durable Goods",
    "TCG": "Tech Capital Goods",
    "TGP": "Total ex Transportation",
}

# --- Wholesale Trade (MWTS) Categories (NAICS codes) ---
MWTS_CATEGORIES = {
    "42":    "Merchant Wholesalers Total",
    "423":   "Durable Goods Wholesalers",
    "4231":  "Motor Vehicle & Parts",
    "4232":  "Furniture & Home Furnishings",
    "4233":  "Lumber & Construction Materials",
    "4234":  "Professional & Commercial Equipment",
    "42343": "Computer Equipment",
    "4235":  "Metals & Minerals",
    "4236":  "Household Appliances & Electronics",
    "4237":  "Hardware & Plumbing",
    "4238":  "Machinery & Equipment",
    "4239":  "Misc. Durable Goods",
    "424":   "Nondurable Goods Wholesalers",
    "4241":  "Paper & Paper Products",
    "4242":  "Drugs & Sundries",
    "4243":  "Apparel",
    "4244":  "Grocery & Related Products",
    "4245":  "Farm Products",
    "4246":  "Chemicals & Allied Products",
    "4247":  "Petroleum Products",
    "4248":  "Beer, Wine & Spirits",
    "4249":  "Misc. Nondurable Goods",
}

# --- Retail Trade (MRTS) Categories (NAICS codes) ---
MRTS_CATEGORIES = {
    "44X72": "Retail and Food Services Total",
    "44000": "Retail Trade Total",
    "4400A": "Retail Trade & Food Services (excl Motor Vehicles)",
    "4400C": "Retail Trade & Food Services (excl Gas Stations)",
    "441": "Motor Vehicle & Parts Dealers",
    "442": "Furniture & Home Furnishings",
    "443": "Electronics & Appliance Stores",
    "444": "Building Material & Garden",
    "445": "Food & Beverage Stores",
    "446": "Health & Personal Care Stores",
    "447": "Gasoline Stations",
    "448": "Clothing & Accessories",
    "451": "Sporting Goods, Hobby, Book, Music",
    "452": "General Merchandise Stores",
    "453": "Miscellaneous Store Retailers",
    "454": "Nonstore Retailers",
    "722": "Food Services & Drinking Places",
}

# --- MTIS (Combined) Categories ---
MTIS_CATEGORIES = {
    "TOTBUS": "Total Business",
    "MNFCTR": "Manufacturing",
    "WHLSLR": "Merchant Wholesalers",
    "RETAIL": "Retail Trade",
}

# ============================================================
# PROGRAM-TO-CATEGORIES MAPPING
# ============================================================

PROGRAM_CATEGORIES = {
    "m3": M3_CATEGORIES,
    "advm3": M3_CATEGORIES,  # Uses same categories
    "mwts": MWTS_CATEGORIES,
    "mwtsadv": MWTS_CATEGORIES,
    "mrts": MRTS_CATEGORIES,
    "mrtsadv": MRTS_CATEGORIES,
    "marts": MRTS_CATEGORIES,
    "mtis": MTIS_CATEGORIES,
}
