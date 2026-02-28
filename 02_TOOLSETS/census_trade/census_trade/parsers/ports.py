"""
Port Trade Data Parser

Parses port-level HS6 export and import data.
Port data gives trade flows at the individual port level with
HS 6-digit commodity detail and transport mode breakdown.
"""

from pathlib import Path

import pandas as pd

from .fixed_width import parse_file
from ..config import record_layouts as rl


class PortParser:
    """Parse port-level HS6 trade data from extracted ZIP directories."""

    def __init__(self, extract_dir: str | Path):
        self.extract_dir = Path(extract_dir)

    # Map ZIP filename patterns to the layout prefix they correspond to
    _EXPORT_PATTERNS = ["DPORTHS6E", "PORTHS6XM", "PORTHS6X"]
    _IMPORT_PATTERNS = ["DPORTHS6I", "PORTHS6MM", "PORTHS6M"]

    def parse_exports(self) -> pd.DataFrame:
        """Parse port export HS6 data.

        Returns DataFrame with columns:
            commodity (HS6), cty_code, port_code, year, month,
            value_mo, air_val_mo, air_swt_mo, ves_val_mo, ves_swt_mo,
            cnt_val_mo, cnt_swt_mo, + YR variants
        """
        return self._parse(self._EXPORT_PATTERNS, rl.PORT_EXPORT_HS6)

    def parse_imports(self) -> pd.DataFrame:
        """Parse port import HS6 data.

        Same structure as exports but values represent general imports.
        """
        return self._parse(self._IMPORT_PATTERNS, rl.PORT_IMPORT_HS6)

    def _parse(self, prefixes: list[str], layout: list) -> pd.DataFrame:
        """Find and parse a file matching any of the prefixes."""
        for f in self.extract_dir.iterdir():
            if f.suffix.upper() != ".TXT":
                continue
            stem = f.stem.upper()
            for prefix in prefixes:
                if stem.startswith(prefix):
                    return parse_file(f, layout)
        # Fallback: if only one TXT file, just parse it
        txt_files = [f for f in self.extract_dir.iterdir() if f.suffix.upper() == ".TXT"]
        if len(txt_files) == 1:
            return parse_file(txt_files[0], layout)
        raise FileNotFoundError(
            f"No file matching {prefixes} in {self.extract_dir}. "
            f"Found: {[f.name for f in txt_files]}"
        )

    def top_ports(self, df: pd.DataFrame, n: int = 20, value_col: str = "value_mo") -> pd.DataFrame:
        """Get top ports by trade value.

        Args:
            df: Parsed port DataFrame (from parse_exports or parse_imports).
            n: Number of top ports to return.
            value_col: Column to rank by.

        Returns:
            Aggregated DataFrame sorted by descending value.
        """
        grouped = df.groupby("port_code")[value_col].sum().reset_index()
        return grouped.nlargest(n, value_col)

    def by_port_and_commodity(self, df: pd.DataFrame, port_code: str = None) -> pd.DataFrame:
        """Break down trade by commodity for a specific port or all ports.

        Args:
            df: Parsed port DataFrame.
            port_code: Optional 4-digit port code to filter.

        Returns:
            Aggregated DataFrame of commodity trade at port level.
        """
        if port_code:
            df = df[df["port_code"] == port_code]
        return df.groupby(["port_code", "commodity"]).agg({
            "value_mo": "sum",
            "air_val_mo": "sum",
            "ves_val_mo": "sum",
            "cnt_val_mo": "sum",
        }).reset_index().sort_values("value_mo", ascending=False)

    def transport_mode_split(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate transport mode percentages (air vs vessel vs container).

        Returns:
            DataFrame with port_code, air_pct, vessel_pct, container_pct.
        """
        grouped = df.groupby("port_code").agg({
            "value_mo": "sum",
            "air_val_mo": "sum",
            "ves_val_mo": "sum",
            "cnt_val_mo": "sum",
        }).reset_index()

        total = grouped["value_mo"].replace(0, 1)  # avoid div by zero
        grouped["air_pct"] = (grouped["air_val_mo"] / total * 100).round(1)
        grouped["vessel_pct"] = (grouped["ves_val_mo"] / total * 100).round(1)
        grouped["container_pct"] = (grouped["cnt_val_mo"] / total * 100).round(1)

        return grouped.sort_values("value_mo", ascending=False)
