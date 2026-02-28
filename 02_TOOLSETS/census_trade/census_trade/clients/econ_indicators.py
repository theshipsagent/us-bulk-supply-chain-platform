"""
Census Economic Indicators Time Series (EITS) API Client

Wraps all 21 EITS endpoints with a unified interface.
API Base: https://api.census.gov/data/timeseries/eits/{program}

All endpoints share the same variable structure (cell_value,
data_type_code, category_code, time_slot_id, seasonally_adj).
"""

import requests
import pandas as pd

from ..config.eits_codes import (
    EITS_API_BASE, PROGRAMS, DATA_TYPES,
    PROGRAM_CATEGORIES, SUPPLY_CHAIN_PROGRAMS,
)


class EconIndicatorsAPI:
    """Client for the Census Economic Indicators Time Series (EITS) API.

    Usage:
        api = EconIndicatorsAPI()

        # Manufacturing shipments
        df = api.query("m3", data_type="VS", category="MTM",
                       start_year=2023, end_year=2025)

        # Wholesale inventories
        df = api.query("mwts", data_type="TI", category="TOTAL",
                       start_year=2024, end_year=2025)

        # Retail sales
        df = api.query("mrts", data_type="SM", category="TOTAL",
                       start_year=2024, end_year=2025)
    """

    def __init__(self, api_key: str = None, timeout: int = 60):
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "CensusTradeModule/0.1 (research)"
        })

    def query(self, program: str, data_type: str = None, category: str = None,
              start_year: int = None, end_year: int = None,
              month: int = None, year: int = None,
              seasonally_adjusted: bool = True) -> pd.DataFrame:
        """Query an EITS endpoint.

        Args:
            program: Program code (e.g. 'm3', 'mwts', 'mrts', 'mtis').
            data_type: Data type code (e.g. 'VS', 'TI', 'NO', 'SM').
            category: Industry category code (e.g. 'MTM', 'TOTAL').
            start_year: Start of date range.
            end_year: End of date range.
            month: Specific month (1-12). If set with year, queries single month.
            year: Specific year. If set with month, queries single month.
            seasonally_adjusted: Whether to get SA or NSA data.

        Returns:
            DataFrame with columns: time, category_code, data_type_code,
            cell_value, seasonally_adj, time_slot_id.
        """
        url = f"{EITS_API_BASE}/{program}"

        params = {
            "get": "cell_value,data_type_code,category_code,time_slot_id,time_slot_name",
            "for": "us:*",
            "seasonally_adj": "yes" if seasonally_adjusted else "no",
        }

        # Time selection
        if year and month:
            params["time"] = f"{year}-{month:02d}"
        elif start_year and end_year:
            params["time"] = f"from {start_year} to {end_year}"
        elif year:
            params["time"] = f"from {year}-01 to {year}-12"

        if data_type:
            params["data_type_code"] = data_type
        if category:
            params["category_code"] = category
        if self.api_key:
            params["key"] = self.api_key

        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()

        if resp.status_code == 204 or not resp.text:
            return pd.DataFrame()

        data = resp.json()

        if not data or len(data) < 2:
            return pd.DataFrame()

        df = pd.DataFrame(data[1:], columns=data[0])

        # Clean up: deduplicate columns that appear in both GET and predicates
        df = df.loc[:, ~df.columns.duplicated()]

        # Convert cell_value to numeric
        df["cell_value"] = pd.to_numeric(df["cell_value"], errors="coerce")

        # Parse time column
        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"], format="mixed", errors="coerce")

        return df

    def query_range(self, program: str, data_type: str, category: str,
                    start_year: int, end_year: int,
                    seasonally_adjusted: bool = True) -> pd.DataFrame:
        """Query a date range, handling API pagination if needed.

        The EITS API sometimes limits responses. This method queries
        year-by-year if needed.
        """
        # Try full range first
        df = self.query(program, data_type=data_type, category=category,
                        start_year=start_year, end_year=end_year,
                        seasonally_adjusted=seasonally_adjusted)
        if not df.empty:
            return df.sort_values("time").reset_index(drop=True)

        # Fallback: year-by-year
        frames = []
        for yr in range(start_year, end_year + 1):
            try:
                chunk = self.query(program, data_type=data_type, category=category,
                                   year=yr, seasonally_adjusted=seasonally_adjusted)
                if not chunk.empty:
                    frames.append(chunk)
            except Exception as e:
                print(f"  [warn] {program}/{yr}: {e}")

        if frames:
            return pd.concat(frames, ignore_index=True).sort_values("time").reset_index(drop=True)
        return pd.DataFrame()

    # ================================================================
    # MANUFACTURING SHORTCUTS
    # ================================================================

    def manufacturing_shipments(self, start_year: int = 2020, end_year: int = 2025,
                                 category: str = "MTM", sa: bool = True) -> pd.DataFrame:
        """Get manufacturing value of shipments time series."""
        return self.query_range("m3", "VS", category, start_year, end_year, sa)

    def manufacturing_new_orders(self, start_year: int = 2020, end_year: int = 2025,
                                  category: str = "MTM", sa: bool = True) -> pd.DataFrame:
        """Get manufacturing new orders time series."""
        return self.query_range("m3", "NO", category, start_year, end_year, sa)

    def manufacturing_inventories(self, start_year: int = 2020, end_year: int = 2025,
                                   category: str = "MTM", sa: bool = True) -> pd.DataFrame:
        """Get manufacturing total inventories time series."""
        return self.query_range("m3", "TI", category, start_year, end_year, sa)

    def manufacturing_unfilled_orders(self, start_year: int = 2020, end_year: int = 2025,
                                       category: str = "MTM", sa: bool = True) -> pd.DataFrame:
        """Get manufacturing unfilled orders (backlog) time series."""
        return self.query_range("m3", "UO", category, start_year, end_year, sa)

    def durable_goods(self, start_year: int = 2020, end_year: int = 2025,
                      data_type: str = "VS", sa: bool = True) -> pd.DataFrame:
        """Get durable goods data (advance report)."""
        return self.query_range("advm3", data_type, "MDM", start_year, end_year, sa)

    # ================================================================
    # WHOLESALE SHORTCUTS
    # ================================================================

    def wholesale_sales(self, start_year: int = 2020, end_year: int = 2025,
                        category: str = "42", sa: bool = True) -> pd.DataFrame:
        """Get wholesale merchant sales time series."""
        return self.query_range("mwts", "SM", category, start_year, end_year, sa)

    def wholesale_inventories(self, start_year: int = 2020, end_year: int = 2025,
                               category: str = "42", sa: bool = True) -> pd.DataFrame:
        """Get wholesale inventories time series."""
        return self.query_range("mwts", "IM", category, start_year, end_year, sa)

    # ================================================================
    # RETAIL SHORTCUTS
    # ================================================================

    def retail_sales(self, start_year: int = 2020, end_year: int = 2025,
                     category: str = "44X72", sa: bool = True) -> pd.DataFrame:
        """Get retail and food services sales time series."""
        return self.query_range("mrts", "SM", category, start_year, end_year, sa)

    def retail_inventories(self, start_year: int = 2020, end_year: int = 2025,
                            category: str = "44000", sa: bool = True) -> pd.DataFrame:
        """Get retail inventories time series (retail trade only, excl food services)."""
        return self.query_range("mrts", "IM", category, start_year, end_year, sa)

    # ================================================================
    # COMBINED (MTIS)
    # ================================================================

    def business_inventories(self, start_year: int = 2020, end_year: int = 2025,
                              category: str = "TOTBUS", sa: bool = True) -> pd.DataFrame:
        """Get combined manufacturing + wholesale + retail inventories."""
        return self.query_range("mtis", "IM", category, start_year, end_year, sa)

    def business_sales(self, start_year: int = 2020, end_year: int = 2025,
                        category: str = "TOTBUS", sa: bool = True) -> pd.DataFrame:
        """Get combined business sales."""
        return self.query_range("mtis", "SM", category, start_year, end_year, sa)

    # ================================================================
    # UTILITIES
    # ================================================================

    def list_programs(self) -> dict:
        """List all available EITS programs."""
        return {k: v["name"] for k, v in PROGRAMS.items()}

    def list_supply_chain_programs(self) -> dict:
        """List programs relevant to supply chain analysis."""
        return {k: v["name"] for k, v in SUPPLY_CHAIN_PROGRAMS.items()}

    def list_categories(self, program: str) -> dict:
        """List available industry categories for a program."""
        return PROGRAM_CATEGORIES.get(program, {})

    def list_data_types(self) -> dict:
        """List all data type codes and their meanings."""
        return DATA_TYPES.copy()

    def describe_value(self, data_type_code: str) -> str:
        """Get human-readable description of a data type code."""
        return DATA_TYPES.get(data_type_code, data_type_code)
