"""
Concordance and lookup file loader.

Census bulk data ZIPs include lookup tables (CONCORD.TXT, COUNTRY.TXT, etc.)
that map codes to descriptions and cross-reference classification systems.
This loader parses them into reusable lookup DataFrames and dictionaries.
"""

from pathlib import Path

import pandas as pd

from .fixed_width import parse_file
from ..config import record_layouts as rl
from ..config.country_codes import load_country_reference


class ConcordanceLoader:
    """Loads and caches all lookup/concordance tables from a Census data extract."""

    def __init__(self, extract_dir: str | Path):
        self.extract_dir = Path(extract_dir)
        self._cache = {}
        self._country_ref = None

    def _find_file(self, prefix: str) -> Path | None:
        """Find a TXT file matching a prefix in the extract directory."""
        for f in self.extract_dir.iterdir():
            if f.stem.upper().startswith(prefix.upper()) and f.suffix.upper() == ".TXT":
                return f
        return None

    def _load(self, prefix: str, layout: list) -> pd.DataFrame:
        """Load and cache a lookup file."""
        if prefix in self._cache:
            return self._cache[prefix]
        filepath = self._find_file(prefix)
        if filepath is None:
            return pd.DataFrame()
        df = parse_file(filepath, layout)
        self._cache[prefix] = df
        return df

    @property
    def concordance(self) -> pd.DataFrame:
        """CONCORD.TXT - Maps 10-digit commodity to all classification systems."""
        return self._load("CONCORD", rl.CONCORDANCE)

    @property
    def countries(self) -> pd.DataFrame:
        """COUNTRY.TXT - Country code to name mapping."""
        return self._load("COUNTRY", rl.COUNTRY_LOOKUP)

    @property
    def districts(self) -> pd.DataFrame:
        """DISTRICT.TXT - Customs district code to name."""
        return self._load("DISTRICT", rl.DISTRICT_LOOKUP)

    @property
    def enduse(self) -> pd.DataFrame:
        """ENDUSE.TXT - End-use category codes and descriptions."""
        return self._load("ENDUSE", rl.ENDUSE_LOOKUP)

    @property
    def hitech(self) -> pd.DataFrame:
        """HITECH.TXT - Advanced technology product categories."""
        return self._load("HITECH", rl.HITECH_LOOKUP)

    @property
    def hs_descriptions(self) -> pd.DataFrame:
        """HSDESC.TXT - Harmonized System code descriptions."""
        return self._load("HSDESC", rl.HSDESC_LOOKUP)

    @property
    def naics(self) -> pd.DataFrame:
        """NAICS.TXT - NAICS industry code descriptions."""
        return self._load("NAICS", rl.NAICS_LOOKUP)

    @property
    def sitc(self) -> pd.DataFrame:
        """SITC.TXT - SITC code descriptions."""
        return self._load("SITC", rl.SITC_LOOKUP)

    @property
    def country_reference(self) -> dict:
        """Canonical country reference (243 codes with ISO, region, sub_region).

        Falls back to this when the ZIP's COUNTRY.TXT lacks a code or
        when richer metadata (ISO, region) is needed.
        """
        if self._country_ref is None:
            self._country_ref = load_country_reference()
        return self._country_ref

    def country_name(self, code: str) -> str:
        """Look up a country name by 4-digit code.

        Tries the ZIP's COUNTRY.TXT first, then falls back to country_reference.csv.
        """
        df = self.countries
        match = df[df["cty_code"] == code]
        if len(match) > 0:
            return match.iloc[0]["cty_name"]
        # Fall back to canonical reference
        ref = self.country_reference
        if code in ref:
            return ref[code]["cty_name"]
        return code

    def country_region(self, code: str) -> str:
        """Look up region for a country code from country_reference.csv."""
        ref = self.country_reference
        return ref[code]["region"] if code in ref else ""

    def country_iso(self, code: str) -> str:
        """Look up ISO alpha-2 code from country_reference.csv."""
        ref = self.country_reference
        return ref[code]["iso_alpha2"] if code in ref else ""

    def district_name(self, code: str) -> str:
        """Look up a district name by 2-digit code."""
        df = self.districts
        match = df[df["dist_code"] == code]
        return match.iloc[0]["dist_name"] if len(match) > 0 else code

    def commodity_description(self, code: str) -> str:
        """Look up commodity description from concordance."""
        df = self.concordance
        match = df[df["commodity"] == code]
        if len(match) > 0:
            return match.iloc[0]["abbreviatn"] or match.iloc[0]["descriptn"]
        # Try HS descriptions
        df_hs = self.hs_descriptions
        hs6 = code[:6]
        match = df_hs[df_hs["commodity"] == hs6]
        return match.iloc[0]["abbreviatn"] if len(match) > 0 else code

    def commodity_to_naics(self, commodity_code: str) -> str:
        """Get NAICS code for a commodity code via concordance."""
        df = self.concordance
        match = df[df["commodity"] == commodity_code]
        return match.iloc[0]["naics"] if len(match) > 0 else ""

    def commodity_to_sitc(self, commodity_code: str) -> str:
        """Get SITC code for a commodity code via concordance."""
        df = self.concordance
        match = df[df["commodity"] == commodity_code]
        return match.iloc[0]["sitc"] if len(match) > 0 else ""

    def commodity_to_enduse(self, commodity_code: str) -> str:
        """Get End-Use code for a commodity code via concordance."""
        df = self.concordance
        match = df[df["commodity"] == commodity_code]
        return match.iloc[0]["end_use"] if len(match) > 0 else ""
