"""
Merchandise Trade Analysis Tool

High-level interface for querying U.S. merchandise trade data.
Combines downloader + parsers + concordance for end-to-end analysis.
"""

from pathlib import Path

import pandas as pd

from ..clients.downloader import CensusDownloader
from ..parsers.merchandise import MerchandiseParser
from ..parsers.concordance import ConcordanceLoader
from ..config.country_codes import load_country_reference


class MerchandiseTradeTool:
    """Query and analyze U.S. merchandise trade (exports and imports)."""

    def __init__(self, cache_dir: str = None):
        self.downloader = CensusDownloader(cache_dir)

    def get_exports(self, year: int, month: int, enrich: bool = True) -> dict[str, pd.DataFrame]:
        """Download and parse all export data for a given month.

        Args:
            year: 4-digit year.
            month: 1-12.
            enrich: Add human-readable descriptions.

        Returns:
            Dict with keys: 'detail', 'commodity', 'country', 'district'
        """
        extract_dir = self.downloader.fetch_merchandise_exports(year, month)
        parser = MerchandiseParser(extract_dir)

        result = {
            "detail": parser.parse_export_detail(),
            "commodity": parser.parse_export_commodity(),
            "country": parser.parse_export_country(),
            "district": parser.parse_export_district(),
        }

        if enrich:
            for key in result:
                result[key] = parser.enrich_with_descriptions(result[key])

        return result

    def get_imports(self, year: int, month: int, enrich: bool = True) -> dict[str, pd.DataFrame]:
        """Download and parse all import data for a given month.

        Returns:
            Dict with keys: 'detail', 'commodity', 'country',
                            'district_entry', 'district_unlading'
        """
        extract_dir = self.downloader.fetch_merchandise_imports(year, month)
        parser = MerchandiseParser(extract_dir)

        result = {
            "detail": parser.parse_import_detail(),
            "commodity": parser.parse_import_commodity(),
            "country": parser.parse_import_country(),
            "district_entry": parser.parse_import_district_entry(),
            "district_unlading": parser.parse_import_district_unlading(),
        }

        if enrich:
            for key in result:
                result[key] = parser.enrich_with_descriptions(result[key])

        return result

    def top_export_commodities(self, year: int, month: int, n: int = 25) -> pd.DataFrame:
        """Get top exported commodities by value for a month."""
        data = self.get_exports(year, month)
        df = data["commodity"]
        return df.nlargest(n, "all_val_mo")[
            ["commodity", "comm_desc", "all_val_mo", "all_val_yr"]
        ].reset_index(drop=True)

    def top_import_commodities(self, year: int, month: int, n: int = 25) -> pd.DataFrame:
        """Get top imported commodities by consumption value for a month."""
        data = self.get_imports(year, month)
        df = data["commodity"]
        return df.nlargest(n, "con_val_mo")[
            ["commodity", "comm_desc", "con_val_mo", "con_val_yr"]
        ].reset_index(drop=True)

    def top_export_partners(self, year: int, month: int, n: int = 25) -> pd.DataFrame:
        """Get top export destination countries by value."""
        data = self.get_exports(year, month)
        df = data["country"]
        return df.nlargest(n, "all_val_mo")[
            ["cty_code", "cty_name", "all_val_mo", "all_val_yr"]
        ].reset_index(drop=True)

    def top_import_partners(self, year: int, month: int, n: int = 25) -> pd.DataFrame:
        """Get top import source countries by consumption value."""
        data = self.get_imports(year, month)
        df = data["country"]
        return df.nlargest(n, "con_val_mo")[
            ["cty_code", "cty_name", "con_val_mo", "con_val_yr"]
        ].reset_index(drop=True)

    def trade_balance_by_country(self, year: int, month: int) -> pd.DataFrame:
        """Calculate trade balance (exports - imports) by country.

        Returns:
            DataFrame with cty_code, cty_name, exports_mo, imports_mo, balance_mo,
            exports_yr, imports_yr, balance_yr.
        """
        exports = self.get_exports(year, month)["country"]
        imports = self.get_imports(year, month)["country"]

        # Merge on country code
        merged = exports[["cty_code", "cty_name", "all_val_mo", "all_val_yr"]].merge(
            imports[["cty_code", "con_val_mo", "con_val_yr"]],
            on="cty_code",
            how="outer",
        ).fillna(0)

        merged = merged.rename(columns={
            "all_val_mo": "exports_mo",
            "all_val_yr": "exports_yr",
            "con_val_mo": "imports_mo",
            "con_val_yr": "imports_yr",
        })

        merged["balance_mo"] = merged["exports_mo"] - merged["imports_mo"]
        merged["balance_yr"] = merged["exports_yr"] - merged["imports_yr"]

        return merged.sort_values("balance_mo").reset_index(drop=True)

    def commodity_by_country(self, year: int, month: int, commodity: str,
                             direction: str = "export") -> pd.DataFrame:
        """Get country breakdown for a specific commodity.

        Args:
            year, month: Time period.
            commodity: 10-digit commodity code (or prefix for partial match).
            direction: 'export' or 'import'.

        Returns:
            DataFrame filtered to that commodity, with country detail.
        """
        if direction == "export":
            data = self.get_exports(year, month)["detail"]
            val_col = "all_val_mo"
        else:
            data = self.get_imports(year, month)["detail"]
            val_col = "con_val_mo" if "con_val_mo" in data.columns else "gen_val_mo"

        mask = data["commodity"].str.startswith(commodity)
        filtered = data[mask].copy()

        if "cty_name" not in filtered.columns:
            ref = load_country_reference()
            filtered["cty_name"] = filtered["cty_code"].map(
                lambda c: ref[c]["cty_name"] if c in ref else "").fillna("")
            filtered["region"] = filtered["cty_code"].map(
                lambda c: ref[c]["region"] if c in ref else "").fillna("")

        return filtered.sort_values(val_col, ascending=False).reset_index(drop=True)

    def transport_mode_summary(self, year: int, month: int,
                               direction: str = "export") -> pd.DataFrame:
        """Summarize trade by transport mode (air, vessel, container).

        Returns:
            DataFrame with mode, value_mo, value_yr, pct.
        """
        if direction == "export":
            data = self.get_exports(year, month)["district"]
            prefix = ""
        else:
            data = self.get_imports(year, month)["district_entry"]
            prefix = ""

        air_mo = data["air_val_mo"].sum()
        ves_mo = data["ves_val_mo"].sum()
        cnt_mo = data["cnt_val_mo"].sum()
        total = air_mo + ves_mo
        if total == 0:
            total = 1

        rows = [
            {"mode": "Air", "value_mo": air_mo, "pct": round(air_mo / total * 100, 1)},
            {"mode": "Vessel (total)", "value_mo": ves_mo, "pct": round(ves_mo / total * 100, 1)},
            {"mode": "  Containerized", "value_mo": cnt_mo, "pct": round(cnt_mo / total * 100, 1)},
        ]
        return pd.DataFrame(rows)
