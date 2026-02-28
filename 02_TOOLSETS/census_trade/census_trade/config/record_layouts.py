"""
Census Foreign Trade - Fixed-Width Record Layout Definitions

Each layout is a list of (field_name, start_position, length, data_type) tuples.
start_position is 0-indexed. data_type is 'str' or 'int'.

Source: https://www.census.gov/foreign-trade/reference/products/layouts/
"""

# ============================================================
# MERCHANDISE EXPORTS
# ============================================================

EXPORT_DETAIL = [
    # EXP_DETL.TXT - 323 bytes per record
    ("df",           0,   1, "str"),   # Domestic/Foreign (1=domestic, 2=foreign)
    ("commodity",    1,  10, "str"),   # 10-digit Schedule B code
    ("cty_code",    11,   4, "str"),   # 4-digit country code
    ("district",    15,   2, "str"),   # 2-digit district code
    ("year",        17,   4, "int"),
    ("month",       21,   2, "int"),
    ("cards_mo",    23,  15, "int"),
    ("qty_1_mo",    38,  15, "int"),
    ("qty_2_mo",    53,  15, "int"),
    ("all_val_mo",  68,  15, "int"),   # Total value monthly (USD)
    ("air_val_mo",  83,  15, "int"),
    ("air_wgt_mo",  98,  15, "int"),   # Air shipping weight (kg)
    ("ves_val_mo", 113,  15, "int"),
    ("ves_wgt_mo", 128,  15, "int"),
    ("cnt_val_mo", 143,  15, "int"),   # Containerized vessel value
    ("cnt_wgt_mo", 158,  15, "int"),
    ("cards_yr",   173,  15, "int"),
    ("qty_1_yr",   188,  15, "int"),
    ("qty_2_yr",   203,  15, "int"),
    ("all_val_yr", 218,  15, "int"),
    ("air_val_yr", 233,  15, "int"),
    ("air_wgt_yr", 248,  15, "int"),
    ("ves_val_yr", 263,  15, "int"),
    ("ves_wgt_yr", 278,  15, "int"),
    ("cnt_val_yr", 293,  15, "int"),
    ("cnt_wgt_yr", 308,  15, "int"),
]

EXPORT_COMMODITY = [
    # EXP_COMM.TXT - 373 bytes
    ("df",           0,   1, "str"),
    ("commodity",    1,  10, "str"),
    ("comm_desc",   11,  50, "str"),
    ("unit_qy1",    61,   3, "str"),
    ("unit_qy2",    64,   3, "str"),
    ("year",        67,   4, "int"),
    ("month",       71,   2, "int"),
    ("cards_mo",    73,  15, "int"),
    ("qty_1_mo",    88,  15, "int"),
    ("qty_2_mo",   103,  15, "int"),
    ("all_val_mo", 118,  15, "int"),
    ("air_val_mo", 133,  15, "int"),
    ("air_wgt_mo", 148,  15, "int"),
    ("ves_val_mo", 163,  15, "int"),
    ("ves_wgt_mo", 178,  15, "int"),
    ("cnt_val_mo", 193,  15, "int"),
    ("cnt_wgt_mo", 208,  15, "int"),
    ("cards_yr",   223,  15, "int"),
    ("qty_1_yr",   238,  15, "int"),
    ("qty_2_yr",   253,  15, "int"),
    ("all_val_yr", 268,  15, "int"),
    ("air_val_yr", 283,  15, "int"),
    ("air_wgt_yr", 298,  15, "int"),
    ("ves_val_yr", 313,  15, "int"),
    ("ves_wgt_yr", 328,  15, "int"),
    ("cnt_val_yr", 343,  15, "int"),
    ("cnt_wgt_yr", 358,  15, "int"),
]

EXPORT_COUNTRY = [
    # EXP_CTY.TXT - 280 bytes
    ("cty_code",     0,   4, "str"),
    ("cty_name",     4,  30, "str"),
    ("year",        34,   4, "int"),
    ("month",       38,   2, "int"),
    ("cards_mo",    40,  15, "int"),
    ("all_val_mo",  55,  15, "int"),
    ("air_val_mo",  70,  15, "int"),
    ("air_wgt_mo",  85,  15, "int"),
    ("ves_val_mo", 100,  15, "int"),
    ("ves_wgt_mo", 115,  15, "int"),
    ("cnt_val_mo", 130,  15, "int"),
    ("cnt_wgt_mo", 145,  15, "int"),
    ("cards_yr",   160,  15, "int"),
    ("all_val_yr", 175,  15, "int"),
    ("air_val_yr", 190,  15, "int"),
    ("air_wgt_yr", 205,  15, "int"),
    ("ves_val_yr", 220,  15, "int"),
    ("ves_wgt_yr", 235,  15, "int"),
    ("cnt_val_yr", 250,  15, "int"),
    ("cnt_wgt_yr", 265,  15, "int"),
]

EXPORT_DISTRICT = [
    # EXP_DIST.TXT - 278 bytes
    ("district",     0,   2, "str"),
    ("dist_name",    2,  30, "str"),
    ("year",        32,   4, "int"),
    ("month",       36,   2, "int"),
    ("cards_mo",    38,  15, "int"),
    ("all_val_mo",  53,  15, "int"),
    ("air_val_mo",  68,  15, "int"),
    ("air_wgt_mo",  83,  15, "int"),
    ("ves_val_mo",  98,  15, "int"),
    ("ves_wgt_mo", 113,  15, "int"),
    ("cnt_val_mo", 128,  15, "int"),
    ("cnt_wgt_mo", 143,  15, "int"),
    ("cards_yr",   158,  15, "int"),
    ("all_val_yr", 173,  15, "int"),
    ("air_val_yr", 188,  15, "int"),
    ("air_wgt_yr", 203,  15, "int"),
    ("ves_val_yr", 218,  15, "int"),
    ("ves_wgt_yr", 233,  15, "int"),
    ("cnt_val_yr", 248,  15, "int"),
    ("cnt_wgt_yr", 263,  15, "int"),
]

# ============================================================
# MERCHANDISE IMPORTS
# ============================================================

IMPORT_DETAIL = [
    # IMP_DETL.TXT - 688 bytes
    ("commodity",     0,  10, "str"),  # 10-digit HTS code
    ("cty_code",     10,   4, "str"),
    ("cty_subco",    14,   2, "str"),  # Country subcode
    ("dist_entry",   16,   2, "str"),  # District of entry
    ("dist_unlad",   18,   2, "str"),  # District of unlading
    ("rate_prov",    20,   2, "str"),  # Rate provision code
    ("year",         22,   4, "int"),
    ("month",        26,   2, "int"),
    ("cards_mo",     28,  15, "int"),
    ("con_qy1_mo",   43,  15, "int"),  # Consumption qty 1
    ("con_qy2_mo",   58,  15, "int"),
    ("con_val_mo",   73,  15, "int"),  # Consumption value
    ("dut_val_mo",   88,  15, "int"),  # Dutiable value
    ("cal_dut_mo",  103,  15, "int"),  # Calculated duty
    ("con_cha_mo",  118,  15, "int"),  # Consumption charges
    ("con_cif_mo",  133,  15, "int"),  # Consumption CIF
    ("gen_qy1_mo",  148,  15, "int"),  # General imports qty 1
    ("gen_qy2_mo",  163,  15, "int"),
    ("gen_val_mo",  178,  15, "int"),  # General imports value
    ("gen_cha_mo",  193,  15, "int"),
    ("gen_cif_mo",  208,  15, "int"),
    ("air_val_mo",  223,  15, "int"),
    ("air_wgt_mo",  238,  15, "int"),
    ("air_cha_mo",  253,  15, "int"),
    ("ves_val_mo",  268,  15, "int"),
    ("ves_wgt_mo",  283,  15, "int"),
    ("ves_cha_mo",  298,  15, "int"),
    ("cnt_val_mo",  313,  15, "int"),
    ("cnt_wgt_mo",  328,  15, "int"),
    ("cnt_cha_mo",  343,  15, "int"),
    # Year-to-date fields
    ("cards_yr",    358,  15, "int"),
    ("con_qy1_yr",  373,  15, "int"),
    ("con_qy2_yr",  388,  15, "int"),
    ("con_val_yr",  403,  15, "int"),
    ("dut_val_yr",  418,  15, "int"),
    ("cal_dut_yr",  433,  15, "int"),
    ("con_cha_yr",  448,  15, "int"),
    ("con_cif_yr",  463,  15, "int"),
    ("gen_qy1_yr",  478,  15, "int"),
    ("gen_qy2_yr",  493,  15, "int"),
    ("gen_val_yr",  508,  15, "int"),
    ("gen_cha_yr",  523,  15, "int"),
    ("gen_cif_yr",  538,  15, "int"),
    ("air_val_yr",  553,  15, "int"),
    ("air_wgt_yr",  568,  15, "int"),
    ("air_cha_yr",  583,  15, "int"),
    ("ves_val_yr",  598,  15, "int"),
    ("ves_wgt_yr",  613,  15, "int"),
    ("ves_cha_yr",  628,  15, "int"),
    ("cnt_val_yr",  643,  15, "int"),
    ("cnt_wgt_yr",  658,  15, "int"),
    ("cnt_cha_yr",  673,  15, "int"),
]

IMPORT_COMMODITY = [
    # IMP_COMM.TXT - 732 bytes
    ("commodity",     0,  10, "str"),
    ("comm_desc",    10,  50, "str"),
    ("unit_qy1",     60,   3, "str"),
    ("unit_qy2",     63,   3, "str"),
    ("year",         66,   4, "int"),
    ("month",        70,   2, "int"),
    ("cards_mo",     72,  15, "int"),
    ("con_qy1_mo",   87,  15, "int"),
    ("con_qy2_mo",  102,  15, "int"),
    ("con_val_mo",  117,  15, "int"),
    ("dut_val_mo",  132,  15, "int"),
    ("cal_dut_mo",  147,  15, "int"),
    ("con_cha_mo",  162,  15, "int"),
    ("con_cif_mo",  177,  15, "int"),
    ("gen_qy1_mo",  192,  15, "int"),
    ("gen_qy2_mo",  207,  15, "int"),
    ("gen_val_mo",  222,  15, "int"),
    ("gen_cha_mo",  237,  15, "int"),
    ("gen_cif_mo",  252,  15, "int"),
    ("air_val_mo",  267,  15, "int"),
    ("air_wgt_mo",  282,  15, "int"),
    ("air_cha_mo",  297,  15, "int"),
    ("ves_val_mo",  312,  15, "int"),
    ("ves_wgt_mo",  327,  15, "int"),
    ("ves_cha_mo",  342,  15, "int"),
    ("cnt_val_mo",  357,  15, "int"),
    ("cnt_wgt_mo",  372,  15, "int"),
    ("cnt_cha_mo",  387,  15, "int"),
    # YTD
    ("cards_yr",    402,  15, "int"),
    ("con_qy1_yr",  417,  15, "int"),
    ("con_qy2_yr",  432,  15, "int"),
    ("con_val_yr",  447,  15, "int"),
    ("dut_val_yr",  462,  15, "int"),
    ("cal_dut_yr",  477,  15, "int"),
    ("con_cha_yr",  492,  15, "int"),
    ("con_cif_yr",  507,  15, "int"),
    ("gen_qy1_yr",  522,  15, "int"),
    ("gen_qy2_yr",  537,  15, "int"),
    ("gen_val_yr",  552,  15, "int"),
    ("gen_cha_yr",  567,  15, "int"),
    ("gen_cif_yr",  582,  15, "int"),
    ("air_val_yr",  597,  15, "int"),
    ("air_wgt_yr",  612,  15, "int"),
    ("air_cha_yr",  627,  15, "int"),
    ("ves_val_yr",  642,  15, "int"),
    ("ves_wgt_yr",  657,  15, "int"),
    ("ves_cha_yr",  672,  15, "int"),
    ("cnt_val_yr",  687,  15, "int"),
    ("cnt_wgt_yr",  702,  15, "int"),
    ("cnt_cha_yr",  717,  15, "int"),
]

IMPORT_COUNTRY = [
    # IMP_CTY.TXT - 580 bytes
    ("cty_code",      0,   4, "str"),
    ("cty_name",      4,  30, "str"),
    ("year",         34,   4, "int"),
    ("month",        38,   2, "int"),
    ("cards_mo",     40,  15, "int"),
    ("con_val_mo",   55,  15, "int"),
    ("dut_val_mo",   70,  15, "int"),
    ("cal_dut_mo",   85,  15, "int"),
    ("con_cha_mo",  100,  15, "int"),
    ("con_cif_mo",  115,  15, "int"),
    ("gen_val_mo",  130,  15, "int"),
    ("gen_cha_mo",  145,  15, "int"),
    ("gen_cif_mo",  160,  15, "int"),
    ("air_val_mo",  175,  15, "int"),
    ("air_wgt_mo",  190,  15, "int"),
    ("air_cha_mo",  205,  15, "int"),
    ("ves_val_mo",  220,  15, "int"),
    ("ves_wgt_mo",  235,  15, "int"),
    ("ves_cha_mo",  250,  15, "int"),
    ("cnt_val_mo",  265,  15, "int"),
    ("cnt_wgt_mo",  280,  15, "int"),
    ("cnt_cha_mo",  295,  15, "int"),
    # YTD
    ("cards_yr",    310,  15, "int"),
    ("con_val_yr",  325,  15, "int"),
    ("dut_val_yr",  340,  15, "int"),
    ("cal_dut_yr",  355,  15, "int"),
    ("con_cha_yr",  370,  15, "int"),
    ("con_cif_yr",  385,  15, "int"),
    ("gen_val_yr",  400,  15, "int"),
    ("gen_cha_yr",  415,  15, "int"),
    ("gen_cif_yr",  430,  15, "int"),
    ("air_val_yr",  445,  15, "int"),
    ("air_wgt_yr",  460,  15, "int"),
    ("air_cha_yr",  475,  15, "int"),
    ("ves_val_yr",  490,  15, "int"),
    ("ves_wgt_yr",  505,  15, "int"),
    ("ves_cha_yr",  520,  15, "int"),
    ("cnt_val_yr",  535,  15, "int"),
    ("cnt_wgt_yr",  550,  15, "int"),
    ("cnt_cha_yr",  565,  15, "int"),
]

IMPORT_DISTRICT_ENTRY = [
    # IMP_DE.TXT - 578 bytes
    ("dist_entry",    0,   2, "str"),
    ("dist_name",     2,  30, "str"),
    ("year",         32,   4, "int"),
    ("month",        36,   2, "int"),
    ("cards_mo",     38,  15, "int"),
    ("con_val_mo",   53,  15, "int"),
    ("dut_val_mo",   68,  15, "int"),
    ("cal_dut_mo",   83,  15, "int"),
    ("con_cha_mo",   98,  15, "int"),
    ("con_cif_mo",  113,  15, "int"),
    ("gen_val_mo",  128,  15, "int"),
    ("gen_cha_mo",  143,  15, "int"),
    ("gen_cif_mo",  158,  15, "int"),
    ("air_val_mo",  173,  15, "int"),
    ("air_wgt_mo",  188,  15, "int"),
    ("air_cha_mo",  203,  15, "int"),
    ("ves_val_mo",  218,  15, "int"),
    ("ves_wgt_mo",  233,  15, "int"),
    ("ves_cha_mo",  248,  15, "int"),
    ("cnt_val_mo",  263,  15, "int"),
    ("cnt_wgt_mo",  278,  15, "int"),
    ("cnt_cha_mo",  293,  15, "int"),
    # YTD
    ("cards_yr",    308,  15, "int"),
    ("con_val_yr",  323,  15, "int"),
    ("dut_val_yr",  338,  15, "int"),
    ("cal_dut_yr",  353,  15, "int"),
    ("con_cha_yr",  368,  15, "int"),
    ("con_cif_yr",  383,  15, "int"),
    ("gen_val_yr",  398,  15, "int"),
    ("gen_cha_yr",  413,  15, "int"),
    ("gen_cif_yr",  428,  15, "int"),
    ("air_val_yr",  443,  15, "int"),
    ("air_wgt_yr",  458,  15, "int"),
    ("air_cha_yr",  473,  15, "int"),
    ("ves_val_yr",  488,  15, "int"),
    ("ves_wgt_yr",  503,  15, "int"),
    ("ves_cha_yr",  518,  15, "int"),
    ("cnt_val_yr",  533,  15, "int"),
    ("cnt_wgt_yr",  548,  15, "int"),
    ("cnt_cha_yr",  563,  15, "int"),
]

# IMP_DU.TXT has same layout as IMP_DE.TXT but field name is dist_unlad
IMPORT_DISTRICT_UNLADING = [
    (f[0].replace("dist_entry", "dist_unlad") if f[0] == "dist_entry" else f[0], f[1], f[2], f[3])
    for f in IMPORT_DISTRICT_ENTRY
]

# ============================================================
# PORT DATA
# ============================================================

PORT_EXPORT_HS6 = [
    # DPORTHS6E - 230 bytes
    ("commodity",    0,   6, "str"),   # HS 6-digit
    ("cty_code",     6,   4, "str"),
    ("port_code",   10,   4, "str"),   # District + port
    ("year",        14,   4, "int"),
    ("month",       18,   2, "int"),
    ("value_mo",    20,  15, "int"),   # Total value monthly
    ("air_val_mo",  35,  15, "int"),
    ("air_swt_mo",  50,  15, "int"),   # Air shipping weight
    ("ves_val_mo",  65,  15, "int"),
    ("ves_swt_mo",  80,  15, "int"),
    ("cnt_val_mo",  95,  15, "int"),
    ("cnt_swt_mo", 110,  15, "int"),
    ("value_yr",   125,  15, "int"),
    ("air_val_yr", 140,  15, "int"),
    ("air_swt_yr", 155,  15, "int"),
    ("ves_val_yr", 170,  15, "int"),
    ("ves_swt_yr", 185,  15, "int"),
    ("cnt_val_yr", 200,  15, "int"),
    ("cnt_swt_yr", 215,  15, "int"),
]

PORT_IMPORT_HS6 = [
    # DPORTHS6I - 230 bytes (same structure, different semantics)
    ("commodity",    0,   6, "str"),
    ("cty_code",     6,   4, "str"),
    ("port_code",   10,   4, "str"),   # Port of unlading
    ("year",        14,   4, "int"),
    ("month",       18,   2, "int"),
    ("value_mo",    20,  15, "int"),   # General imports total value
    ("air_val_mo",  35,  15, "int"),
    ("air_swt_mo",  50,  15, "int"),
    ("ves_val_mo",  65,  15, "int"),
    ("ves_swt_mo",  80,  15, "int"),
    ("cnt_val_mo",  95,  15, "int"),
    ("cnt_swt_mo", 110,  15, "int"),
    ("value_yr",   125,  15, "int"),
    ("air_val_yr", 140,  15, "int"),
    ("air_swt_yr", 155,  15, "int"),
    ("ves_val_yr", 170,  15, "int"),
    ("ves_swt_yr", 185,  15, "int"),
    ("cnt_val_yr", 200,  15, "int"),
    ("cnt_swt_yr", 215,  15, "int"),
]

# ============================================================
# LOOKUP / CONCORDANCE FILES
# ============================================================

CONCORDANCE = [
    # CONCORD.TXT - 235 bytes (maps commodity code to all classification systems)
    ("commodity",    0,  10, "str"),  # 10-digit Schedule B / HTS code
    ("descriptn",   10, 150, "str"),  # Full description
    ("abbreviatn", 160,  50, "str"),  # Short description
    ("unit_qy1",   210,   3, "str"),
    ("unit_qy2",   213,   3, "str"),
    ("sitc",       216,   5, "str"),  # SITC code
    ("end_use",    221,   5, "str"),  # End-use code
    ("naics",      226,   6, "str"),  # NAICS code
    ("usda",       232,   1, "str"),  # USDA indicator
    ("hitech",     233,   2, "str"),  # Hi-tech category
]

COUNTRY_LOOKUP = [
    # COUNTRY.TXT - 61 bytes
    ("cty_code",     0,   4, "str"),
    ("cty_desc",     4,   7, "str"),
    ("cty_name",    11,  50, "str"),
]

DISTRICT_LOOKUP = [
    # DISTRICT.TXT - 59 bytes
    ("dist_code",    0,   2, "str"),
    ("dist_desc",    2,   7, "str"),
    ("dist_name",    9,  50, "str"),
]

ENDUSE_LOOKUP = [
    # ENDUSE.TXT - 105 bytes
    ("enduse",       0,   5, "str"),
    ("eudesc",       5, 100, "str"),
]

HITECH_LOOKUP = [
    # HITECH.TXT - 32 bytes
    ("hitech",       0,   2, "str"),
    ("hidesc",       2,  30, "str"),
]

HSDESC_LOOKUP = [
    # HSDESC.TXT - 206 bytes
    ("commodity",    0,   6, "str"),  # HS 2/4/6 digit
    ("descriptn",    6, 150, "str"),
    ("abbreviatn", 156,  50, "str"),
]

NAICS_LOOKUP = [
    # NAICS.TXT - 56 bytes
    ("naics",        0,   6, "str"),  # 2-6 digit
    ("naicdesc",     6,  50, "str"),
]

SITC_LOOKUP = [
    # SITC.TXT - 205 bytes
    ("sitc",         0,   5, "str"),  # 1-5 digit
    ("sitcdesc",     5, 150, "str"),
    ("sitcabrev",  155,  50, "str"),
]

# ============================================================
# LAYOUT REGISTRY
# ============================================================

FILE_LAYOUTS = {
    # Merchandise exports
    "EXP_DETL": EXPORT_DETAIL,
    "EXP_COMM": EXPORT_COMMODITY,
    "EXP_CTY": EXPORT_COUNTRY,
    "EXP_DIST": EXPORT_DISTRICT,
    # Merchandise imports
    "IMP_DETL": IMPORT_DETAIL,
    "IMP_COMM": IMPORT_COMMODITY,
    "IMP_CTY": IMPORT_COUNTRY,
    "IMP_DE": IMPORT_DISTRICT_ENTRY,
    "IMP_DU": IMPORT_DISTRICT_UNLADING,
    # Port data
    "DPORTHS6E": PORT_EXPORT_HS6,
    "DPORTHS6I": PORT_IMPORT_HS6,
    # Lookups
    "CONCORD": CONCORDANCE,
    "COUNTRY": COUNTRY_LOOKUP,
    "DISTRICT": DISTRICT_LOOKUP,
    "ENDUSE": ENDUSE_LOOKUP,
    "HITECH": HITECH_LOOKUP,
    "HSDESC": HSDESC_LOOKUP,
    "NAICS": NAICS_LOOKUP,
    "SITC": SITC_LOOKUP,
}


def get_layout(filename: str) -> list:
    """Get the record layout for a given filename."""
    key = filename.upper().replace(".TXT", "")
    # Handle dated filenames like DPORTHS6E2501.TXT
    for layout_key in FILE_LAYOUTS:
        if key.startswith(layout_key):
            return FILE_LAYOUTS[layout_key]
    if key in FILE_LAYOUTS:
        return FILE_LAYOUTS[key]
    raise KeyError(f"No layout found for '{filename}'. Known layouts: {list(FILE_LAYOUTS.keys())}")


def get_record_length(layout: list) -> int:
    """Calculate expected record length from a layout definition."""
    if not layout:
        return 0
    last = layout[-1]
    return last[1] + last[2]
