"""
Merchandise Trade Data Parser

Parses the full merchandise export/import ZIP extracts into
structured DataFrames with optional concordance enrichment.
"""

from pathlib import Path

import pandas as pd

from .fixed_width import parse_file, parse_directory
from .concordance import ConcordanceLoader
from ..config import record_layouts as rl


class MerchandiseParser:
    """Parse merchandise trade exports and imports from extracted ZIP directories."""

    def __init__(self, extract_dir: str | Path):
        self.extract_dir = Path(extract_dir)
        self.lookups = ConcordanceLoader(extract_dir)

    def parse_export_detail(self) -> pd.DataFrame:
        """Parse EXP_DETL.TXT - full export detail records.

        Returns DataFrame with columns:
            df, commodity, cty_code, district, year, month,
            all_val_mo, air_val_mo, ves_val_mo, cnt_val_mo, (weights), (YTD variants)
        """
        return self._parse("EXP_DETL", rl.EXPORT_DETAIL)

    def parse_export_commodity(self) -> pd.DataFrame:
        """Parse EXP_COMM.TXT - exports aggregated by commodity."""
        return self._parse("EXP_COMM", rl.EXPORT_COMMODITY)

    def parse_export_country(self) -> pd.DataFrame:
        """Parse EXP_CTY.TXT - exports aggregated by country."""
        return self._parse("EXP_CTY", rl.EXPORT_COUNTRY)

    def parse_export_district(self) -> pd.DataFrame:
        """Parse EXP_DIST.TXT - exports aggregated by customs district."""
        return self._parse("EXP_DIST", rl.EXPORT_DISTRICT)

    def parse_import_detail(self) -> pd.DataFrame:
        """Parse IMP_DETL.TXT - full import detail records.

        Returns DataFrame with columns:
            commodity, cty_code, cty_subco, dist_entry, dist_unlad, rate_prov,
            year, month, con_val_mo, gen_val_mo, dut_val_mo, cal_dut_mo,
            con_cif_mo, (transport breakdowns), (YTD variants)
        """
        return self._parse("IMP_DETL", rl.IMPORT_DETAIL)

    def parse_import_commodity(self) -> pd.DataFrame:
        """Parse IMP_COMM.TXT - imports aggregated by commodity."""
        return self._parse("IMP_COMM", rl.IMPORT_COMMODITY)

    def parse_import_country(self) -> pd.DataFrame:
        """Parse IMP_CTY.TXT - imports aggregated by country."""
        return self._parse("IMP_CTY", rl.IMPORT_COUNTRY)

    def parse_import_district_entry(self) -> pd.DataFrame:
        """Parse IMP_DE.TXT - imports by district of entry."""
        return self._parse("IMP_DE", rl.IMPORT_DISTRICT_ENTRY)

    def parse_import_district_unlading(self) -> pd.DataFrame:
        """Parse IMP_DU.TXT - imports by district of unlading."""
        return self._parse("IMP_DU", rl.IMPORT_DISTRICT_UNLADING)

    def enrich_with_descriptions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add human-readable descriptions to a parsed DataFrame.

        Adds columns: cty_name, dist_name, commodity_desc, naics, sitc, end_use
        based on code columns present in the DataFrame.
        """
        df = df.copy()

        if "cty_code" in df.columns:
            # Use canonical country_reference.csv for richer metadata
            ref = self.lookups.country_reference
            if ref:
                df["cty_name"] = df["cty_code"].map(
                    lambda c: ref[c]["cty_name"] if c in ref else "").fillna("")
                df["iso_alpha2"] = df["cty_code"].map(
                    lambda c: ref[c]["iso_alpha2"] if c in ref else "").fillna("")
                df["region"] = df["cty_code"].map(
                    lambda c: ref[c]["region"] if c in ref else "").fillna("")
                df["sub_region"] = df["cty_code"].map(
                    lambda c: ref[c]["sub_region"] if c in ref else "").fillna("")
            else:
                # Fall back to ZIP's COUNTRY.TXT if reference unavailable
                countries = self.lookups.countries
                if not countries.empty:
                    country_map = dict(zip(countries["cty_code"], countries["cty_name"]))
                    df["cty_name"] = df["cty_code"].map(country_map).fillna("")

        if "district" in df.columns:
            districts = self.lookups.districts
            if not districts.empty:
                dist_map = dict(zip(districts["dist_code"], districts["dist_name"]))
                df["dist_name"] = df["district"].map(dist_map).fillna("")

        if "dist_entry" in df.columns:
            districts = self.lookups.districts
            if not districts.empty:
                dist_map = dict(zip(districts["dist_code"], districts["dist_name"]))
                df["dist_entry_name"] = df["dist_entry"].map(dist_map).fillna("")

        if "commodity" in df.columns:
            conc = self.lookups.concordance
            if not conc.empty:
                desc_map = dict(zip(conc["commodity"], conc["abbreviatn"]))
                naics_map = dict(zip(conc["commodity"], conc["naics"]))
                sitc_map = dict(zip(conc["commodity"], conc["sitc"]))
                enduse_map = dict(zip(conc["commodity"], conc["end_use"]))
                df["commodity_desc"] = df["commodity"].map(desc_map).fillna("")
                df["naics"] = df["commodity"].map(naics_map).fillna("")
                df["sitc"] = df["commodity"].map(sitc_map).fillna("")
                df["end_use"] = df["commodity"].map(enduse_map).fillna("")

        return df

    def _parse(self, file_prefix: str, layout: list) -> pd.DataFrame:
        """Find and parse a file matching the prefix."""
        for f in self.extract_dir.iterdir():
            if f.stem.upper().startswith(file_prefix) and f.suffix.upper() == ".TXT":
                return parse_file(f, layout)
        raise FileNotFoundError(f"No file matching '{file_prefix}*.TXT' in {self.extract_dir}")

    def summary(self) -> dict:
        """Quick summary of what's in this extract."""
        files = {f.stem.upper(): f for f in self.extract_dir.iterdir() if f.suffix.upper() == ".TXT"}
        return {
            "directory": str(self.extract_dir),
            "files": list(files.keys()),
            "has_exports": any(k.startswith("EXP") for k in files),
            "has_imports": any(k.startswith("IMP") for k in files),
            "has_concordance": "CONCORD" in files,
            "country_count": len(self.lookups.countries) if "COUNTRY" in files else 0,
        }
