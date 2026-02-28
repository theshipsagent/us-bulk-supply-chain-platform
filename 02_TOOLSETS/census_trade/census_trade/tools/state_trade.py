"""
State Trade Analysis Tool

High-level interface for analyzing U.S. trade at the state level.
Uses state HS6 and NAICS data products.
"""

from pathlib import Path

import pandas as pd

from ..clients.downloader import CensusDownloader
from ..parsers.fixed_width import parse_file
from ..config import record_layouts as rl
from ..config.country_codes import load_country_reference
from ..config.url_patterns import (
    STATE_EXPORTS_HS6_ORIGIN, STATE_IMPORTS_HS6,
    STATE_EXPORTS_NAICS_ORIGIN, STATE_IMPORTS_NAICS,
    build_url,
)


# State HS6 layouts (not in main record_layouts since structure varies)
STATE_EXPORT_HS6 = [
    ("state",        0,   2, "str"),   # 2-digit state FIPS code
    ("commodity",    2,   6, "str"),   # HS 6-digit
    ("cty_code",     8,   4, "str"),   # Country code
    ("year",        12,   4, "int"),
    ("month",       16,   2, "int"),
    ("value_mo",    18,  15, "int"),   # Monthly value
    ("value_yr",    33,  15, "int"),   # Year-to-date value
]

STATE_IMPORT_HS6 = [
    ("state",        0,   2, "str"),
    ("commodity",    2,   6, "str"),
    ("cty_code",     8,   4, "str"),
    ("year",        12,   4, "int"),
    ("month",       16,   2, "int"),
    ("value_mo",    18,  15, "int"),
    ("value_yr",    33,  15, "int"),
]

STATE_EXPORT_NAICS = [
    ("state",        0,   2, "str"),
    ("naics",        2,   6, "str"),   # NAICS code
    ("cty_code",     8,   4, "str"),
    ("year",        12,   4, "int"),
    ("month",       16,   2, "int"),
    ("value_mo",    18,  15, "int"),
    ("value_yr",    33,  15, "int"),
]

STATE_IMPORT_NAICS = [
    ("state",        0,   2, "str"),
    ("naics",        2,   6, "str"),
    ("cty_code",     8,   4, "str"),
    ("year",        12,   4, "int"),
    ("month",       16,   2, "int"),
    ("value_mo",    18,  15, "int"),
    ("value_yr",    33,  15, "int"),
]

# FIPS state codes to names
STATE_FIPS = {
    "01": "Alabama", "02": "Alaska", "04": "Arizona", "05": "Arkansas",
    "06": "California", "08": "Colorado", "09": "Connecticut", "10": "Delaware",
    "11": "District of Columbia", "12": "Florida", "13": "Georgia", "15": "Hawaii",
    "16": "Idaho", "17": "Illinois", "18": "Indiana", "19": "Iowa",
    "20": "Kansas", "21": "Kentucky", "22": "Louisiana", "23": "Maine",
    "24": "Maryland", "25": "Massachusetts", "26": "Michigan", "27": "Minnesota",
    "28": "Mississippi", "29": "Missouri", "30": "Montana", "31": "Nebraska",
    "32": "Nevada", "33": "New Hampshire", "34": "New Jersey", "35": "New Mexico",
    "36": "New York", "37": "North Carolina", "38": "North Dakota", "39": "Ohio",
    "40": "Oklahoma", "41": "Oregon", "42": "Pennsylvania", "44": "Rhode Island",
    "45": "South Carolina", "46": "South Dakota", "47": "Tennessee", "48": "Texas",
    "49": "Utah", "50": "Vermont", "51": "Virginia", "53": "Washington",
    "54": "West Virginia", "55": "Wisconsin", "56": "Wyoming",
    "60": "American Samoa", "66": "Guam", "69": "Northern Mariana Islands",
    "72": "Puerto Rico", "78": "U.S. Virgin Islands",
}


class StateTradeTool:
    """Analyze U.S. trade at the state level."""

    def __init__(self, cache_dir: str = None):
        self.downloader = CensusDownloader(cache_dir)
        self._country_ref = None

    @property
    def country_ref(self) -> dict:
        """Lazy-load canonical country reference."""
        if self._country_ref is None:
            self._country_ref = load_country_reference()
        return self._country_ref

    def get_state_exports_hs6(self, year: int, month: int) -> pd.DataFrame:
        """Download and parse state-level HS6 export data."""
        extract_dir = self.downloader.fetch_product(
            "state_exports_hs6_origin", year, month=month
        )
        df = self._parse_first_txt(extract_dir, STATE_EXPORT_HS6)
        df["state_name"] = df["state"].map(STATE_FIPS).fillna("")
        return df

    def get_state_imports_hs6(self, year: int, month: int) -> pd.DataFrame:
        """Download and parse state-level HS6 import data."""
        extract_dir = self.downloader.fetch_product(
            "state_imports_hs6", year, month=month
        )
        df = self._parse_first_txt(extract_dir, STATE_IMPORT_HS6)
        df["state_name"] = df["state"].map(STATE_FIPS).fillna("")
        return df

    def get_state_exports_naics(self, year: int, month: int) -> pd.DataFrame:
        """Download and parse state-level NAICS export data."""
        extract_dir = self.downloader.fetch_product(
            "state_exports_naics_origin", year, month=month
        )
        df = self._parse_first_txt(extract_dir, STATE_EXPORT_NAICS)
        df["state_name"] = df["state"].map(STATE_FIPS).fillna("")
        return df

    def get_state_imports_naics(self, year: int, month: int) -> pd.DataFrame:
        """Download and parse state-level NAICS import data."""
        extract_dir = self.downloader.fetch_product(
            "state_imports_naics", year, month=month
        )
        df = self._parse_first_txt(extract_dir, STATE_IMPORT_NAICS)
        df["state_name"] = df["state"].map(STATE_FIPS).fillna("")
        return df

    def top_exporting_states(self, year: int, month: int, n: int = 20) -> pd.DataFrame:
        """Rank states by total export value."""
        df = self.get_state_exports_hs6(year, month)
        grouped = df.groupby(["state", "state_name"]).agg({
            "value_mo": "sum",
            "value_yr": "sum",
        }).reset_index()
        return grouped.nlargest(n, "value_mo").reset_index(drop=True)

    def top_importing_states(self, year: int, month: int, n: int = 20) -> pd.DataFrame:
        """Rank states by total import value."""
        df = self.get_state_imports_hs6(year, month)
        grouped = df.groupby(["state", "state_name"]).agg({
            "value_mo": "sum",
            "value_yr": "sum",
        }).reset_index()
        return grouped.nlargest(n, "value_mo").reset_index(drop=True)

    def state_trade_profile(self, year: int, month: int, state_fips: str) -> dict:
        """Get a comprehensive trade profile for a single state.

        Args:
            year, month: Time period.
            state_fips: 2-digit FIPS code (e.g. '06' for California).

        Returns:
            Dict with 'exports', 'imports', 'top_export_commodities',
            'top_import_commodities', 'top_export_partners', 'top_import_partners'.
        """
        exports = self.get_state_exports_hs6(year, month)
        imports = self.get_state_imports_hs6(year, month)

        exp_state = exports[exports["state"] == state_fips]
        imp_state = imports[imports["state"] == state_fips]

        top_exp_comm = (exp_state.groupby("commodity")["value_mo"].sum()
                        .nlargest(10).reset_index())
        top_imp_comm = (imp_state.groupby("commodity")["value_mo"].sum()
                        .nlargest(10).reset_index())

        top_exp_cty = (exp_state.groupby("cty_code")["value_mo"].sum()
                       .nlargest(10).reset_index())
        top_imp_cty = (imp_state.groupby("cty_code")["value_mo"].sum()
                       .nlargest(10).reset_index())

        # Enrich country partner tables with names and regions
        ref = self.country_ref
        for cty_df in (top_exp_cty, top_imp_cty):
            cty_df["cty_name"] = cty_df["cty_code"].map(
                lambda c: ref[c]["cty_name"] if c in ref else "")
            cty_df["region"] = cty_df["cty_code"].map(
                lambda c: ref[c]["region"] if c in ref else "")

        return {
            "state": state_fips,
            "state_name": STATE_FIPS.get(state_fips, ""),
            "total_exports_mo": int(exp_state["value_mo"].sum()),
            "total_imports_mo": int(imp_state["value_mo"].sum()),
            "balance_mo": int(exp_state["value_mo"].sum() - imp_state["value_mo"].sum()),
            "top_export_commodities": top_exp_comm,
            "top_import_commodities": top_imp_comm,
            "top_export_partners": top_exp_cty,
            "top_import_partners": top_imp_cty,
        }

    def state_commodity_detail(self, year: int, month: int, state_fips: str,
                                commodity: str, direction: str = "export") -> pd.DataFrame:
        """Get country breakdown for a commodity in a specific state.

        Args:
            year, month: Time period.
            state_fips: 2-digit state FIPS code.
            commodity: HS6 code or prefix.
            direction: 'export' or 'import'.
        """
        if direction == "export":
            df = self.get_state_exports_hs6(year, month)
        else:
            df = self.get_state_imports_hs6(year, month)

        mask = (df["state"] == state_fips) & df["commodity"].str.startswith(commodity)
        return df[mask].sort_values("value_mo", ascending=False).reset_index(drop=True)

    def _parse_first_txt(self, extract_dir: Path, layout: list) -> pd.DataFrame:
        """Parse the first .TXT file found in an extract directory."""
        for f in sorted(extract_dir.iterdir()):
            if f.suffix.upper() == ".TXT":
                return parse_file(f, layout)
        raise FileNotFoundError(f"No .TXT files in {extract_dir}")
