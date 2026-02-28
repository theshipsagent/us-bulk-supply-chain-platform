"""
Domestic Supply Chain Analysis Tool

Combines manufacturing, wholesale, and retail data from Census EITS
to provide a full view of the U.S. domestic supply chain pipeline.

Supply chain layers:
  Manufacturing (M3) -> Wholesale (MWTS) -> Retail (MRTS)

Key metrics:
  - Shipments/Sales flow through the chain
  - Inventory levels at each stage
  - Inventory-to-sales ratios (pipeline health)
  - New orders and backlogs (demand signals)
  - Bullwhip effect detection (inventory amplification)
"""

import pandas as pd

from ..clients.econ_indicators import EconIndicatorsAPI
from ..config.eits_codes import M3_CATEGORIES, MWTS_CATEGORIES, MRTS_CATEGORIES


class SupplyChainTool:
    """Analyze the U.S. domestic supply chain using Census economic data."""

    def __init__(self, api_key: str = None):
        self.api = EconIndicatorsAPI(api_key)

    # ================================================================
    # PIPELINE OVERVIEW
    # ================================================================

    def pipeline_snapshot(self, year: int, month: int) -> pd.DataFrame:
        """Get a single-month snapshot of the full supply chain pipeline.

        Returns a DataFrame with one row per layer showing:
        sales/shipments, inventories, and I/S ratio.
        """
        rows = []

        # Manufacturing
        mfg_ship = self.api.query("m3", data_type="VS", category="MTM",
                                   year=year, month=month)
        mfg_inv = self.api.query("m3", data_type="TI", category="MTM",
                                  year=year, month=month)
        mfg_is = self.api.query("m3", data_type="IS", category="MTM",
                                 year=year, month=month)
        rows.append({
            "layer": "Manufacturing",
            "program": "m3",
            "sales_shipments": _val(mfg_ship),
            "inventories": _val(mfg_inv),
            "is_ratio": _val(mfg_is),
        })

        # Wholesale
        whl_sales = self.api.query("mwts", data_type="SM", category="42",
                                    year=year, month=month)
        whl_inv = self.api.query("mwts", data_type="IM", category="42",
                                  year=year, month=month)
        whl_is = self.api.query("mwts", data_type="IR", category="42",
                                 year=year, month=month)
        rows.append({
            "layer": "Wholesale",
            "program": "mwts",
            "sales_shipments": _val(whl_sales),
            "inventories": _val(whl_inv),
            "is_ratio": _val(whl_is),
        })

        # Retail
        ret_sales = self.api.query("mrts", data_type="SM", category="44000",
                                    year=year, month=month)
        ret_inv = self.api.query("mrts", data_type="IM", category="44000",
                                  year=year, month=month)
        ret_is = self.api.query("mrts", data_type="IR", category="44000",
                                 year=year, month=month)
        rows.append({
            "layer": "Retail",
            "program": "mrts",
            "sales_shipments": _val(ret_sales),
            "inventories": _val(ret_inv),
            "is_ratio": _val(ret_is),
        })

        return pd.DataFrame(rows)

    def pipeline_timeseries(self, start_year: int = 2020, end_year: int = 2025,
                             metric: str = "inventories") -> pd.DataFrame:
        """Get a time series comparing all three supply chain layers.

        Args:
            start_year, end_year: Date range.
            metric: One of 'sales', 'inventories', 'is_ratio'.

        Returns:
            DataFrame with time, manufacturing, wholesale, retail columns.
        """
        type_map = {
            "sales": ("VS", "SM", "SM"),
            "inventories": ("TI", "IM", "IM"),
            "is_ratio": ("IS", "IR", "IR"),
        }
        mfg_type, whl_type, ret_type = type_map[metric]

        mfg = self.api.query_range("m3", mfg_type, "MTM", start_year, end_year)
        whl = self.api.query_range("mwts", whl_type, "42", start_year, end_year)
        ret = self.api.query_range("mrts", ret_type, "44000", start_year, end_year)

        result = pd.DataFrame()
        if not mfg.empty:
            result["time"] = mfg["time"]
            result["manufacturing"] = mfg["cell_value"].values
        if not whl.empty:
            whl_aligned = whl.set_index("time").reindex(result["time"]).reset_index()
            result["wholesale"] = whl_aligned["cell_value"].values
        if not ret.empty:
            ret_aligned = ret.set_index("time").reindex(result["time"]).reset_index()
            result["retail"] = ret_aligned["cell_value"].values

        return result

    # ================================================================
    # MANUFACTURING DEEP DIVE
    # ================================================================

    def manufacturing_overview(self, year: int, month: int) -> pd.DataFrame:
        """Comprehensive manufacturing snapshot: shipments, orders, inventories.

        Returns one row per metric for total manufacturing.
        """
        metrics = [
            ("VS", "Value of Shipments"),
            ("NO", "New Orders"),
            ("UO", "Unfilled Orders (Backlog)"),
            ("TI", "Total Inventories"),
            ("FI", "Finished Goods Inventories"),
            ("WI", "Work-in-Process Inventories"),
            ("MI", "Materials & Supplies Inventories"),
            ("IS", "Inventory/Shipments Ratio"),
        ]
        rows = []
        for code, name in metrics:
            df = self.api.query("m3", data_type=code, category="MTM",
                                year=year, month=month)
            rows.append({"metric": name, "code": code, "value": _val(df)})

        return pd.DataFrame(rows)

    def manufacturing_by_industry(self, year: int, month: int,
                                   data_type: str = "VS") -> pd.DataFrame:
        """Get manufacturing data broken down by industry.

        Args:
            year, month: Time period.
            data_type: 'VS' (shipments), 'NO' (orders), 'TI' (inventories).

        Returns:
            DataFrame with category_code, industry_name, value.
        """
        # Query major categories
        categories = ["MTM", "MDM", "MNM", "33E", "33G", "33H", "33M",
                       "34S", "34A", "34D", "11S", "23S", "24S", "25S"]
        rows = []
        for cat in categories:
            df = self.api.query("m3", data_type=data_type, category=cat,
                                year=year, month=month)
            rows.append({
                "category_code": cat,
                "industry": M3_CATEGORIES.get(cat, cat),
                "value": _val(df),
            })

        return pd.DataFrame(rows).sort_values("value", ascending=False).reset_index(drop=True)

    def orders_backlog_trend(self, start_year: int = 2020, end_year: int = 2025,
                              category: str = "MTM") -> pd.DataFrame:
        """Track new orders vs unfilled orders (backlog) over time.

        Useful for detecting demand acceleration/deceleration.
        """
        orders = self.api.query_range("m3", "NO", category, start_year, end_year)
        backlog = self.api.query_range("m3", "UO", category, start_year, end_year)

        result = pd.DataFrame()
        if not orders.empty:
            result["time"] = orders["time"]
            result["new_orders"] = orders["cell_value"].values
        if not backlog.empty and not result.empty:
            bl_aligned = backlog.set_index("time").reindex(result["time"]).reset_index()
            result["unfilled_orders"] = bl_aligned["cell_value"].values

        return result

    # ================================================================
    # INVENTORY ANALYSIS
    # ================================================================

    def inventory_breakdown(self, year: int, month: int,
                             category: str = "MTM") -> pd.DataFrame:
        """Break down manufacturing inventories by stage.

        Returns finished goods, work-in-process, and materials inventories.
        """
        stages = [
            ("TI", "Total Inventories"),
            ("FI", "Finished Goods"),
            ("WI", "Work-in-Process"),
            ("MI", "Materials & Supplies"),
        ]
        rows = []
        for code, name in stages:
            df = self.api.query("m3", data_type=code, category=category,
                                year=year, month=month)
            rows.append({"stage": name, "code": code, "value": _val(df)})

        result = pd.DataFrame(rows)
        total = result.loc[result["code"] == "TI", "value"].iloc[0] if len(result) > 0 else 1
        if total > 0:
            result["pct"] = (result["value"] / total * 100).round(1)
        return result

    def is_ratio_trend(self, start_year: int = 2020, end_year: int = 2025) -> pd.DataFrame:
        """Track inventory-to-sales ratios across all layers.

        Rising I/S ratio = inventory building / demand weakening
        Falling I/S ratio = inventory depletion / demand strengthening
        """
        mfg = self.api.query_range("m3", "IS", "MTM", start_year, end_year)
        whl = self.api.query_range("mwts", "IR", "42", start_year, end_year)
        ret = self.api.query_range("mrts", "IR", "44000", start_year, end_year)

        result = pd.DataFrame()
        if not mfg.empty:
            result["time"] = mfg["time"]
            result["mfg_is_ratio"] = mfg["cell_value"].values
        if not whl.empty and not result.empty:
            w = whl.set_index("time").reindex(result["time"]).reset_index()
            result["whl_is_ratio"] = w["cell_value"].values
        if not ret.empty and not result.empty:
            r = ret.set_index("time").reindex(result["time"]).reset_index()
            result["ret_is_ratio"] = r["cell_value"].values

        return result

    # ================================================================
    # WHOLESALE ANALYSIS
    # ================================================================

    def wholesale_by_industry(self, year: int, month: int,
                               data_type: str = "SM") -> pd.DataFrame:
        """Get wholesale data broken down by industry."""
        categories = [k for k in MWTS_CATEGORIES.keys() if k != "42"][:10]
        rows = []
        for cat in categories:
            df = self.api.query("mwts", data_type=data_type, category=cat,
                                year=year, month=month)
            rows.append({
                "category_code": cat,
                "industry": MWTS_CATEGORIES.get(cat, cat),
                "value": _val(df),
            })
        return pd.DataFrame(rows).sort_values("value", ascending=False).reset_index(drop=True)

    # ================================================================
    # RETAIL ANALYSIS
    # ================================================================

    def retail_by_industry(self, year: int, month: int,
                            data_type: str = "SM") -> pd.DataFrame:
        """Get retail sales broken down by store type."""
        categories = [k for k in MRTS_CATEGORIES.keys()
                       if k not in ("44X72", "44000", "4400A", "4400C")][:12]
        rows = []
        for cat in categories:
            df = self.api.query("mrts", data_type=data_type, category=cat,
                                year=year, month=month)
            rows.append({
                "category_code": cat,
                "store_type": MRTS_CATEGORIES.get(cat, cat),
                "value": _val(df),
            })
        return pd.DataFrame(rows).sort_values("value", ascending=False).reset_index(drop=True)

    # ================================================================
    # COMBINED ANALYSIS
    # ================================================================

    def business_inventories_trend(self, start_year: int = 2020,
                                    end_year: int = 2025) -> pd.DataFrame:
        """Track total business inventories (MTIS) by sector over time."""
        total = self.api.query_range("mtis", "IM", "TOTBUS", start_year, end_year)
        mfg = self.api.query_range("mtis", "IM", "MNFCTR", start_year, end_year)
        whl = self.api.query_range("mtis", "IM", "WHLSLR", start_year, end_year)
        ret = self.api.query_range("mtis", "IM", "RETAIL", start_year, end_year)

        result = pd.DataFrame()
        if not total.empty:
            result["time"] = total["time"]
            result["total"] = total["cell_value"].values
        for label, src in [("manufacturing", mfg), ("wholesale", whl), ("retail", ret)]:
            if not src.empty and not result.empty:
                aligned = src.set_index("time").reindex(result["time"]).reset_index()
                result[label] = aligned["cell_value"].values

        return result


def _val(df: pd.DataFrame) -> float:
    """Extract the first cell_value from an API response DataFrame."""
    if df is None or df.empty or "cell_value" not in df.columns:
        return 0.0
    val = df["cell_value"].iloc[0]
    return float(val) if pd.notna(val) else 0.0
