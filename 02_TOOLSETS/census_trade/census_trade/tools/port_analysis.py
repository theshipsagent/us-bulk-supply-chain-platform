"""
Port Trade Analysis Tool

High-level interface for analyzing trade at the U.S. port level.
Uses HS6 commodity-level data with transport mode breakdowns.
"""

from pathlib import Path

import pandas as pd

from ..clients.downloader import CensusDownloader
from ..parsers.ports import PortParser
from ..config.country_codes import load_country_reference


class PortAnalysisTool:
    """Analyze U.S. trade at the port level."""

    def __init__(self, cache_dir: str = None):
        self.downloader = CensusDownloader(cache_dir)
        self._country_ref = None

    @property
    def country_ref(self) -> dict:
        """Lazy-load canonical country reference."""
        if self._country_ref is None:
            self._country_ref = load_country_reference()
        return self._country_ref

    def get_port_exports(self, year: int, month: int) -> pd.DataFrame:
        """Download and parse port-level export data."""
        extract_dir = self.downloader.fetch_port_exports(year, month)
        parser = PortParser(extract_dir)
        return parser.parse_exports()

    def get_port_imports(self, year: int, month: int) -> pd.DataFrame:
        """Download and parse port-level import data."""
        extract_dir = self.downloader.fetch_port_imports(year, month)
        parser = PortParser(extract_dir)
        return parser.parse_imports()

    def top_ports(self, year: int, month: int, direction: str = "export",
                  n: int = 20) -> pd.DataFrame:
        """Rank ports by total trade value.

        Args:
            year, month: Time period.
            direction: 'export' or 'import'.
            n: Number of top ports.

        Returns:
            DataFrame with port_code, total_value, air_value, vessel_value,
            container_value, air_pct, vessel_pct, container_pct.
        """
        if direction == "export":
            df = self.get_port_exports(year, month)
        else:
            df = self.get_port_imports(year, month)

        grouped = df.groupby("port_code").agg({
            "value_mo": "sum",
            "air_val_mo": "sum",
            "ves_val_mo": "sum",
            "cnt_val_mo": "sum",
        }).reset_index()

        total = grouped["value_mo"].replace(0, 1)
        grouped["air_pct"] = (grouped["air_val_mo"] / total * 100).round(1)
        grouped["vessel_pct"] = (grouped["ves_val_mo"] / total * 100).round(1)
        grouped["container_pct"] = (grouped["cnt_val_mo"] / total * 100).round(1)

        return grouped.nlargest(n, "value_mo").reset_index(drop=True)

    def port_commodity_breakdown(self, year: int, month: int, port_code: str,
                                  direction: str = "export", n: int = 25) -> pd.DataFrame:
        """Get top commodities traded through a specific port.

        Args:
            year, month: Time period.
            port_code: 4-digit port code.
            direction: 'export' or 'import'.
            n: Number of top commodities.

        Returns:
            DataFrame with commodity, value_mo, and transport mode breakdown.
        """
        if direction == "export":
            df = self.get_port_exports(year, month)
        else:
            df = self.get_port_imports(year, month)

        port_df = df[df["port_code"] == port_code]
        grouped = port_df.groupby("commodity").agg({
            "value_mo": "sum",
            "air_val_mo": "sum",
            "ves_val_mo": "sum",
            "cnt_val_mo": "sum",
            "air_swt_mo": "sum",
            "ves_swt_mo": "sum",
        }).reset_index()

        return grouped.nlargest(n, "value_mo").reset_index(drop=True)

    def port_country_breakdown(self, year: int, month: int, port_code: str,
                                direction: str = "export", n: int = 25) -> pd.DataFrame:
        """Get top trading partner countries for a specific port.

        Args:
            year, month: Time period.
            port_code: 4-digit port code.
            direction: 'export' or 'import'.
            n: Number of top countries.
        """
        if direction == "export":
            df = self.get_port_exports(year, month)
        else:
            df = self.get_port_imports(year, month)

        port_df = df[df["port_code"] == port_code]
        grouped = port_df.groupby("cty_code").agg({
            "value_mo": "sum",
            "air_val_mo": "sum",
            "ves_val_mo": "sum",
        }).reset_index()

        # Enrich with country name and region from canonical reference
        ref = self.country_ref
        grouped["cty_name"] = grouped["cty_code"].map(
            lambda c: ref[c]["cty_name"] if c in ref else "")
        grouped["region"] = grouped["cty_code"].map(
            lambda c: ref[c]["region"] if c in ref else "")

        return grouped.nlargest(n, "value_mo").reset_index(drop=True)

    def commodity_port_flow(self, year: int, month: int, commodity: str,
                             direction: str = "export") -> pd.DataFrame:
        """Find which ports handle a specific commodity.

        Args:
            year, month: Time period.
            commodity: HS6 code (6 digits) or prefix.
            direction: 'export' or 'import'.

        Returns:
            DataFrame showing port distribution for that commodity.
        """
        if direction == "export":
            df = self.get_port_exports(year, month)
        else:
            df = self.get_port_imports(year, month)

        mask = df["commodity"].str.startswith(commodity)
        filtered = df[mask]

        grouped = filtered.groupby("port_code").agg({
            "value_mo": "sum",
            "air_val_mo": "sum",
            "ves_val_mo": "sum",
            "cnt_val_mo": "sum",
        }).reset_index()

        total_val = grouped["value_mo"].sum()
        if total_val > 0:
            grouped["share_pct"] = (grouped["value_mo"] / total_val * 100).round(1)

        return grouped.sort_values("value_mo", ascending=False).reset_index(drop=True)

    def compare_ports(self, year: int, month: int, port_codes: list[str],
                      direction: str = "export") -> pd.DataFrame:
        """Compare multiple ports side by side.

        Args:
            year, month: Time period.
            port_codes: List of 4-digit port codes.
            direction: 'export' or 'import'.

        Returns:
            DataFrame with one row per port, showing total values and mode split.
        """
        if direction == "export":
            df = self.get_port_exports(year, month)
        else:
            df = self.get_port_imports(year, month)

        filtered = df[df["port_code"].isin(port_codes)]
        grouped = filtered.groupby("port_code").agg({
            "value_mo": "sum",
            "value_yr": "sum",
            "air_val_mo": "sum",
            "ves_val_mo": "sum",
            "cnt_val_mo": "sum",
        }).reset_index()

        grouped["commodity_count"] = filtered.groupby("port_code")["commodity"].nunique().values
        grouped["country_count"] = filtered.groupby("port_code")["cty_code"].nunique().values

        return grouped.sort_values("value_mo", ascending=False).reset_index(drop=True)
