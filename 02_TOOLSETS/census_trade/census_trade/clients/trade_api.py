"""
Census International Trade API Client

Wraps all 36 Census International Trade API endpoints.
API docs: https://www.census.gov/data/developers/data-sets/international-trade.html
Base URL: https://api.census.gov/data/timeseries/intltrade/

No API key required for basic usage.
"""

import requests
import pandas as pd


API_BASE = "https://api.census.gov/data/timeseries/intltrade"

# All available API endpoints
ENDPOINTS = {
    # Exports
    "exports_hs":         f"{API_BASE}/exports/hs",
    "exports_naics":      f"{API_BASE}/exports/naics",
    "exports_enduse":     f"{API_BASE}/exports/enduse",
    "exports_sitc":       f"{API_BASE}/exports/sitc",
    "exports_hitech":     f"{API_BASE}/exports/hitech",
    "exports_usda":       f"{API_BASE}/exports/usda",
    "exports_porths":     f"{API_BASE}/exports/porths",
    "exports_statehs":    f"{API_BASE}/exports/statehs",
    "exports_statenaics": f"{API_BASE}/exports/statenaics",
    # Imports
    "imports_hs":         f"{API_BASE}/imports/hs",
    "imports_naics":      f"{API_BASE}/imports/naics",
    "imports_enduse":     f"{API_BASE}/imports/enduse",
    "imports_sitc":       f"{API_BASE}/imports/sitc",
    "imports_hitech":     f"{API_BASE}/imports/hitech",
    "imports_usda":       f"{API_BASE}/imports/usda",
    "imports_porths":     f"{API_BASE}/imports/porths",
    "imports_statehs":    f"{API_BASE}/imports/statehs",
    "imports_statenaics": f"{API_BASE}/imports/statenaics",
}

# Common variable sets for quick queries
COMMON_EXPORT_VARS = [
    "ALL_VAL_MO", "ALL_VAL_YR",
    "AIR_VAL_MO", "VES_VAL_MO", "CNT_VAL_MO",
    "AIR_WGT_MO", "VES_WGT_MO", "CNT_WGT_MO",
    "QTY_1_MO", "QTY_2_MO",
]

COMMON_IMPORT_VARS = [
    "GEN_VAL_MO", "GEN_VAL_YR",
    "CON_VAL_MO", "CON_VAL_YR",
    "DUT_VAL_MO", "CAL_DUT_MO",
    "AIR_VAL_MO", "VES_VAL_MO", "CNT_VAL_MO",
]

# Commodity variable names differ by endpoint type
COMMODITY_VARS = {
    "hs": ("E_COMMODITY", "I_COMMODITY"),
    "naics": ("NAICS", "NAICS"),
    "enduse": ("E_ENDUSE", "I_ENDUSE"),
    "sitc": ("SITC", "SITC"),
    "hitech": ("HITECH", "HITECH"),
    "usda": ("USDA_NUM", "USDA_NUM"),
}


class CensusTradeAPI:
    """Client for the Census International Trade API.

    Usage:
        api = CensusTradeAPI()
        df = api.query("exports_hs", year=2024, month=6,
                       variables=["ALL_VAL_MO", "E_COMMODITY", "CTY_CODE"],
                       commodity="27",  # HS chapter 27 (mineral fuels)
                       country="5700")  # China
    """

    def __init__(self, api_key: str = None, timeout: int = 60):
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "CensusTradeModule/0.1 (research)"
        })

    def query(self, endpoint: str, year: int, month: int,
              variables: list[str] = None,
              commodity: str = None, country: str = None,
              state: str = None, district: str = None,
              comm_lvl: str = None,
              limit: int = None) -> pd.DataFrame:
        """Query a Census trade API endpoint.

        Args:
            endpoint: Key from ENDPOINTS dict (e.g. 'exports_hs').
            year: 4-digit year.
            month: 1-12.
            variables: List of variable names to retrieve. If None, uses common defaults.
            commodity: Commodity code filter.
            country: Country code filter (4-digit).
            state: State FIPS code filter (2-digit).
            district: District code filter.
            comm_lvl: Commodity level filter (e.g. 'HS2', 'HS4', 'HS6', 'HS10').
            limit: Max rows to return.

        Returns:
            DataFrame with query results.
        """
        url = ENDPOINTS[endpoint]

        # Default variables
        if variables is None:
            if "export" in endpoint:
                variables = COMMON_EXPORT_VARS.copy()
            else:
                variables = COMMON_IMPORT_VARS.copy()

        # Build GET params
        get_str = ",".join(variables)
        time_str = f"{year}-{month:02d}"

        params = {
            "get": get_str,
            "time": time_str,
        }

        # Filters
        predicates = []
        if commodity:
            # Determine the right commodity variable name
            ep_type = endpoint.split("_")[-1]  # e.g. 'hs', 'naics'
            if "export" in endpoint:
                comm_var = COMMODITY_VARS.get(ep_type, ("E_COMMODITY",))[0]
            else:
                comm_var = COMMODITY_VARS.get(ep_type, (None, "I_COMMODITY"))[1]
            if comm_var:
                params[comm_var] = commodity

        if country:
            params["CTY_CODE"] = country
        if state:
            params["STATE"] = state
        if district:
            params["DISTRICT"] = district
        if comm_lvl:
            params["COMM_LVL"] = comm_lvl
        if self.api_key:
            params["key"] = self.api_key

        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        if not data or len(data) < 2:
            return pd.DataFrame()

        # First row is header, rest is data
        df = pd.DataFrame(data[1:], columns=data[0])

        # Convert numeric columns
        for col in df.columns:
            if col.endswith("_MO") or col.endswith("_YR") or col in ("YEAR", "MONTH"):
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

        return df

    def exports_by_hs(self, year: int, month: int, hs_code: str = None,
                      country: str = None, level: str = "HS6") -> pd.DataFrame:
        """Shortcut: Get export data by Harmonized System code."""
        vars_ = ["E_COMMODITY", "E_COMMODITY_SDESC", "CTY_CODE", "CTY_NAME",
                  "ALL_VAL_MO", "ALL_VAL_YR", "AIR_VAL_MO", "VES_VAL_MO"]
        return self.query("exports_hs", year, month,
                          variables=vars_, commodity=hs_code,
                          country=country, comm_lvl=level)

    def imports_by_hs(self, year: int, month: int, hs_code: str = None,
                      country: str = None, level: str = "HS6") -> pd.DataFrame:
        """Shortcut: Get import data by Harmonized System code."""
        vars_ = ["I_COMMODITY", "I_COMMODITY_SDESC", "CTY_CODE", "CTY_NAME",
                  "GEN_VAL_MO", "GEN_VAL_YR", "CON_VAL_MO", "DUT_VAL_MO"]
        return self.query("imports_hs", year, month,
                          variables=vars_, commodity=hs_code,
                          country=country, comm_lvl=level)

    def exports_by_naics(self, year: int, month: int, naics: str = None,
                         country: str = None) -> pd.DataFrame:
        """Shortcut: Get export data by NAICS industry code."""
        vars_ = ["NAICS", "NAICS_SDESC", "CTY_CODE", "CTY_NAME",
                  "ALL_VAL_MO", "ALL_VAL_YR"]
        return self.query("exports_naics", year, month,
                          variables=vars_, commodity=naics, country=country)

    def imports_by_naics(self, year: int, month: int, naics: str = None,
                         country: str = None) -> pd.DataFrame:
        """Shortcut: Get import data by NAICS industry code."""
        vars_ = ["NAICS", "NAICS_SDESC", "CTY_CODE", "CTY_NAME",
                  "GEN_VAL_MO", "CON_VAL_MO", "DUT_VAL_MO"]
        return self.query("imports_naics", year, month,
                          variables=vars_, commodity=naics, country=country)

    def port_exports(self, year: int, month: int, port: str = None,
                     commodity: str = None) -> pd.DataFrame:
        """Shortcut: Get port-level export data."""
        vars_ = ["PORT", "PORT_NAME", "E_COMMODITY", "CTY_CODE",
                  "ALL_VAL_MO", "AIR_VAL_MO", "VES_VAL_MO", "CNT_VAL_MO"]
        return self.query("exports_porths", year, month,
                          variables=vars_, commodity=commodity, district=port)

    def port_imports(self, year: int, month: int, port: str = None,
                     commodity: str = None) -> pd.DataFrame:
        """Shortcut: Get port-level import data."""
        vars_ = ["PORT", "PORT_NAME", "I_COMMODITY", "CTY_CODE",
                  "GEN_VAL_MO", "AIR_VAL_MO", "VES_VAL_MO", "CNT_VAL_MO"]
        return self.query("imports_porths", year, month,
                          variables=vars_, commodity=commodity, district=port)

    def state_exports(self, year: int, month: int, state: str = None,
                      commodity: str = None) -> pd.DataFrame:
        """Shortcut: Get state-level export data by HS code."""
        vars_ = ["STATE", "E_COMMODITY", "CTY_CODE", "ALL_VAL_MO", "ALL_VAL_YR"]
        return self.query("exports_statehs", year, month,
                          variables=vars_, commodity=commodity, state=state)

    def state_imports(self, year: int, month: int, state: str = None,
                      commodity: str = None) -> pd.DataFrame:
        """Shortcut: Get state-level import data by HS code."""
        vars_ = ["STATE", "I_COMMODITY", "CTY_CODE", "GEN_VAL_MO", "CON_VAL_MO"]
        return self.query("imports_statehs", year, month,
                          variables=vars_, commodity=commodity, state=state)

    def list_endpoints(self) -> dict:
        """List all available API endpoints."""
        return ENDPOINTS.copy()

    def get_variables(self, endpoint: str) -> list[str]:
        """Fetch available variables for an endpoint from the API."""
        url = f"{ENDPOINTS[endpoint]}/variables.json"
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return list(data.get("variables", {}).keys())
