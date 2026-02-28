"""
Cargo Flow Analyzer — data engine for waterway tonnage analysis.

Loads BTS link-tonnage and waterway-network CSVs, joins on LINKNUM,
and provides aggregation / analysis methods for report generation.
"""

import sys
from pathlib import Path

# Add project root so we can import src.models
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np

from src.models.cargo import COMMODITY_TYPES

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent

# CSV paths (same filenames the costing tool uses)
LINK_TONS_CSV = PROJECT_ROOT / "data" / "03_bts_link_tons" / "Link_Tonnages_1612260770216529761.csv"
WATERWAY_NET_CSV = PROJECT_ROOT / "data" / "09_bts_waterway_networks" / "Waterway_Networks_7107995240912772581.csv"
LOCKS_CSV = PROJECT_ROOT / "data" / "04_bts_locks" / "Locks_-3795028687405442582.csv"
NODES_CSV = PROJECT_ROOT / "data" / "10_bts_waterway_nodes" / "Waterway_Networks_7112991831811577565.csv"

# Commodity column prefixes → standard keys (matching COMMODITY_TYPES)
COMMODITY_COLS = {
    "coal":            ("COALUP",   "COALDOWN"),
    "petroleum":       ("PETROLUP", "PETRODOWN"),
    "chemicals":       ("CHEMUP",   "CHEMDOWN"),
    "crude_materials": ("CRMATUP",  "CRMATDOWN"),
    "manufactured":    ("MANUUP",   "MANUDOWN"),
    "farm":            ("FARMUP",   "FARMDOWN"),
    "machinery":       ("MACHUP",   "MACHDOWN"),
    "waste":           ("WASTEUP",  "WASTEDOWN"),
    "unknown":         ("UNKWNUP",  "UNKWDOWN"),
}

# Display-friendly names
COMMODITY_NAMES = {
    "coal": "Coal",
    "petroleum": "Petroleum",
    "chemicals": "Chemicals",
    "crude_materials": "Crude Materials",
    "manufactured": "Manufactured Goods",
    "farm": "Farm Products",
    "machinery": "Machinery",
    "waste": "Waste",
    "unknown": "Unknown",
}

# Consistent colour palette
COMMODITY_COLORS = {
    "coal":            "#333333",
    "petroleum":       "#D35400",
    "chemicals":       "#8E44AD",
    "crude_materials": "#795548",
    "manufactured":    "#2196F3",
    "farm":            "#4CAF50",
    "machinery":       "#FFC107",
    "waste":           "#607D8B",
    "unknown":         "#BDBDBD",
}

# Value per ton (pull from COMMODITY_TYPES where available, else 0)
VALUE_PER_TON = {}
for k in COMMODITY_COLS:
    ct = COMMODITY_TYPES.get(k)
    VALUE_PER_TON[k] = ct.value_per_ton_usd if ct and ct.value_per_ton_usd else 0


# ---------------------------------------------------------------------------
# CargoFlowAnalyzer
# ---------------------------------------------------------------------------


class CargoFlowAnalyzer:
    """Loads, joins, and analyses inland-waterway cargo-flow data."""

    def __init__(self):
        self.links: pd.DataFrame = pd.DataFrame()   # joined tonnage + network
        self.locks: pd.DataFrame = pd.DataFrame()
        self.nodes: pd.DataFrame = pd.DataFrame()
        self._loaded = False

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def load_data(self) -> dict:
        """Read CSVs, join tonnage with waterway networks, compute derived columns.

        Returns a status dict with record counts and any warnings.
        """
        status: dict = {"ok": True, "warnings": []}

        # --- Link Tonnages ---
        tons = pd.read_csv(LINK_TONS_CSV)
        tons.columns = tons.columns.str.strip()
        status["tonnage_records"] = len(tons)

        # --- Waterway Networks ---
        net = pd.read_csv(WATERWAY_NET_CSV, low_memory=False)
        net.columns = net.columns.str.strip()
        status["network_records"] = len(net)

        # --- Join on LINKNUM ---
        merged = tons.merge(net, on="LINKNUM", how="inner", suffixes=("_ton", "_net"))
        status["joined_records"] = len(merged)
        if len(merged) < len(tons):
            status["warnings"].append(
                f"Only {len(merged)}/{len(tons)} tonnage links matched a network record."
            )

        # --- Derived columns ---
        merged["total"] = merged["TOTALUP"] + merged["TOTALDOWN"]
        merged["net_flow"] = merged["TOTALDOWN"] - merged["TOTALUP"]

        # Per-commodity totals
        for key, (up_col, dn_col) in COMMODITY_COLS.items():
            merged[f"{key}_total"] = merged[up_col] + merged[dn_col]

        # Primary commodity per link
        commodity_total_cols = [f"{k}_total" for k in COMMODITY_COLS]
        merged["primary_commodity"] = (
            merged[commodity_total_cols]
            .idxmax(axis=1)
            .str.replace("_total", "", regex=False)
        )
        # If all zeros, mark as "none"
        merged.loc[merged[commodity_total_cols].sum(axis=1) == 0, "primary_commodity"] = "none"

        # Estimated cargo value
        for key in COMMODITY_COLS:
            merged[f"{key}_value"] = merged[f"{key}_total"] * VALUE_PER_TON.get(key, 0)
        value_cols = [f"{k}_value" for k in COMMODITY_COLS]
        merged["total_value"] = merged[value_cols].sum(axis=1)

        self.links = merged

        # --- Locks ---
        self.locks = pd.read_csv(LOCKS_CSV, low_memory=False)
        self.locks.columns = self.locks.columns.str.strip()
        status["lock_records"] = len(self.locks)

        # --- Nodes ---
        self.nodes = pd.read_csv(NODES_CSV, low_memory=False)
        self.nodes.columns = self.nodes.columns.str.strip()
        status["node_records"] = len(self.nodes)

        self._loaded = True
        return status

    def _check_loaded(self):
        if not self._loaded:
            raise RuntimeError("Call load_data() first.")

    # ------------------------------------------------------------------
    # Analysis methods
    # ------------------------------------------------------------------

    def get_tonnage_by_river(self, top_n: int = 20) -> pd.DataFrame:
        """Aggregate tonnage by RIVERNAME.

        Returns DataFrame with columns:
            RIVERNAME, total_up, total_down, total, net_flow, link_count,
            plus per-commodity total columns.
        """
        self._check_loaded()
        df = self.links

        agg_dict = {
            "TOTALUP": "sum",
            "TOTALDOWN": "sum",
            "total": "sum",
            "net_flow": "sum",
            "LINKNUM": "count",
            "total_value": "sum",
        }
        for key in COMMODITY_COLS:
            agg_dict[f"{key}_total"] = "sum"

        grouped = df.groupby("RIVERNAME", as_index=False).agg(agg_dict)
        grouped.rename(columns={
            "TOTALUP": "total_up",
            "TOTALDOWN": "total_down",
            "LINKNUM": "link_count",
        }, inplace=True)
        grouped.sort_values("total", ascending=False, inplace=True)

        if top_n:
            grouped = grouped.head(top_n)
        return grouped.reset_index(drop=True)

    def get_national_commodity_mix(self) -> pd.DataFrame:
        """System-wide breakdown by commodity type.

        Returns DataFrame: commodity, display_name, total_tons, pct, upstream, downstream, value.
        """
        self._check_loaded()
        df = self.links
        rows = []
        for key, (up_col, dn_col) in COMMODITY_COLS.items():
            up = df[up_col].sum()
            dn = df[dn_col].sum()
            total = up + dn
            val = total * VALUE_PER_TON.get(key, 0)
            rows.append({
                "commodity": key,
                "display_name": COMMODITY_NAMES[key],
                "total_tons": int(total),
                "upstream": int(up),
                "downstream": int(dn),
                "value_usd": float(val),
            })
        result = pd.DataFrame(rows)
        grand = result["total_tons"].sum()
        result["pct"] = (result["total_tons"] / grand * 100).round(2) if grand else 0
        result.sort_values("total_tons", ascending=False, inplace=True)
        return result.reset_index(drop=True)

    def get_tonnage_by_state(self) -> pd.DataFrame:
        """Aggregate tonnage by STATE code."""
        self._check_loaded()
        df = self.links
        agg = df.groupby("STATE", as_index=False).agg(
            total=("total", "sum"),
            total_up=("TOTALUP", "sum"),
            total_down=("TOTALDOWN", "sum"),
            link_count=("LINKNUM", "count"),
            total_value=("total_value", "sum"),
        )
        agg.sort_values("total", ascending=False, inplace=True)
        return agg.reset_index(drop=True)

    def get_top_corridors(self, top_n: int = 25) -> pd.DataFrame:
        """Highest-traffic individual links with river/mile context."""
        self._check_loaded()
        cols = [
            "LINKNUM", "RIVERNAME", "LINKNAME", "AMILE", "BMILE",
            "STATE", "TOTALUP", "TOTALDOWN", "total", "net_flow",
            "primary_commodity", "total_value",
        ]
        result = self.links[cols].sort_values("total", ascending=False).head(top_n)
        return result.reset_index(drop=True)

    def get_directional_flow_by_river(self, top_n: int = 20) -> pd.DataFrame:
        """Upstream vs downstream by river — net flow analysis."""
        self._check_loaded()
        df = self.links
        grouped = df.groupby("RIVERNAME", as_index=False).agg(
            total_up=("TOTALUP", "sum"),
            total_down=("TOTALDOWN", "sum"),
            total=("total", "sum"),
            net_flow=("net_flow", "sum"),
        )
        grouped["direction_label"] = grouped["net_flow"].apply(
            lambda x: "Downstream dominant" if x > 0 else ("Upstream dominant" if x < 0 else "Balanced")
        )
        grouped["abs_net"] = grouped["net_flow"].abs()
        grouped.sort_values("total", ascending=False, inplace=True)
        if top_n:
            grouped = grouped.head(top_n)
        return grouped.reset_index(drop=True)

    def get_directional_flow_by_commodity(self) -> pd.DataFrame:
        """Which commodities move upstream vs downstream."""
        self._check_loaded()
        df = self.links
        rows = []
        for key, (up_col, dn_col) in COMMODITY_COLS.items():
            up = int(df[up_col].sum())
            dn = int(df[dn_col].sum())
            net = dn - up
            rows.append({
                "commodity": key,
                "display_name": COMMODITY_NAMES[key],
                "upstream": up,
                "downstream": dn,
                "net_flow": net,
                "direction": "Downstream" if net > 0 else ("Upstream" if net < 0 else "Balanced"),
            })
        result = pd.DataFrame(rows)
        result.sort_values("net_flow", key=abs, ascending=False, inplace=True)
        return result.reset_index(drop=True)

    def get_lock_traffic_overlay(self) -> pd.DataFrame:
        """Match locks to nearby link tonnage; compute bottleneck score.

        Strategy: match locks to links sharing the same RIVER name, with the
        lock's river-mile falling within the link's AMILE–BMILE range.
        Falls back to nearest link on the same river when exact range match fails.
        """
        self._check_loaded()

        locks = self.locks.copy()
        links = self.links.copy()

        # Normalise river names for matching
        locks["_river"] = locks["RIVER"].str.strip().str.upper()
        links["_river"] = links["RIVERNAME"].str.strip().str.upper()

        # For each link compute mile-range bounds (AMILE/BMILE may be reversed)
        links["mile_lo"] = links[["AMILE", "BMILE"]].min(axis=1)
        links["mile_hi"] = links[["AMILE", "BMILE"]].max(axis=1)

        results = []
        for _, lock in locks.iterrows():
            river = lock["_river"]
            mile = lock.get("RIVERMI", None)
            if pd.isna(mile) or pd.isna(river):
                continue

            river_links = links[links["_river"] == river]
            if river_links.empty:
                # Try partial match (lock river may be shorter, e.g. "OHIO" vs "OHIO RIVER")
                river_links = links[links["_river"].str.contains(river, na=False)]
            if river_links.empty:
                continue

            # Exact range match
            exact = river_links[
                (river_links["mile_lo"] <= mile) & (river_links["mile_hi"] >= mile)
            ]
            if not exact.empty:
                matched = exact.sort_values("total", ascending=False).iloc[0]
            else:
                # Nearest by midpoint
                river_links = river_links.copy()
                river_links["_mid"] = (river_links["mile_lo"] + river_links["mile_hi"]) / 2
                river_links["_dist"] = (river_links["_mid"] - mile).abs()
                matched = river_links.sort_values("_dist").iloc[0]

            tonnage = matched["total"]
            length = lock.get("LENGTH", 0) or 0
            width = lock.get("WIDTH", 0) or 0
            chamber_area = length * width if (length and width) else 1
            bottleneck_score = tonnage / chamber_area if chamber_area else 0

            results.append({
                "lock_name": lock.get("PMSNAME", lock.get("NAVSTR", "")),
                "river": lock["RIVER"],
                "river_mile": mile,
                "state": lock.get("STATE", ""),
                "chamber_length": length,
                "chamber_width": width,
                "year_open": lock.get("YEAROPEN", None),
                "adjacent_tonnage": int(tonnage),
                "bottleneck_score": round(bottleneck_score, 2),
                "is_600ft": length <= 600 if length else False,
                "lock_x": lock.get("x", None),
                "lock_y": lock.get("y", None),
            })

        result = pd.DataFrame(results)
        if not result.empty:
            result.sort_values("bottleneck_score", ascending=False, inplace=True)
            result.reset_index(drop=True, inplace=True)
        return result

    def get_link_geometries(self) -> pd.DataFrame:
        """Join links → nodes for lat/lon coordinates (ANODE → node x,y / BNODE → node x,y).

        Returns DataFrame with link info plus anode_x, anode_y, bnode_x, bnode_y columns.
        """
        self._check_loaded()

        nodes = self.nodes[["NODENUM", "x", "y"]].drop_duplicates(subset="NODENUM")

        geo = self.links.merge(
            nodes.rename(columns={"NODENUM": "ANODE", "x": "anode_x", "y": "anode_y"}),
            on="ANODE",
            how="left",
        )
        geo = geo.merge(
            nodes.rename(columns={"NODENUM": "BNODE", "x": "bnode_x", "y": "bnode_y"}),
            on="BNODE",
            how="left",
        )
        # Midpoint for simple marker placement
        geo["mid_x"] = (geo["anode_x"] + geo["bnode_x"]) / 2
        geo["mid_y"] = (geo["anode_y"] + geo["bnode_y"]) / 2

        return geo

    def estimate_cargo_value(self) -> pd.DataFrame:
        """Per-commodity value summary using $/ton from COMMODITY_TYPES."""
        self._check_loaded()
        rows = []
        for key, (up_col, dn_col) in COMMODITY_COLS.items():
            total_tons = int(self.links[f"{key}_total"].sum())
            vpt = VALUE_PER_TON.get(key, 0)
            rows.append({
                "commodity": key,
                "display_name": COMMODITY_NAMES[key],
                "total_tons": total_tons,
                "value_per_ton": vpt,
                "estimated_value": total_tons * vpt,
            })
        result = pd.DataFrame(rows)
        result.sort_values("estimated_value", ascending=False, inplace=True)
        return result.reset_index(drop=True)

    # ------------------------------------------------------------------
    # Filtered helper
    # ------------------------------------------------------------------

    def filter_links(
        self,
        rivers: list[str] | None = None,
        commodities: list[str] | None = None,
    ) -> pd.DataFrame:
        """Return a filtered copy of self.links."""
        self._check_loaded()
        df = self.links.copy()
        if rivers:
            df = df[df["RIVERNAME"].isin(rivers)]
        if commodities:
            df = df[df["primary_commodity"].isin(commodities)]
        return df


# ---------------------------------------------------------------------------
# CLI quick-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Cargo Flow Analyzer — Quick Test")
    print("=" * 60)

    analyzer = CargoFlowAnalyzer()
    status = analyzer.load_data()

    print(f"\nLoad status: {status}")
    print(f"  Tonnage records:  {status['tonnage_records']:,}")
    print(f"  Network records:  {status['network_records']:,}")
    print(f"  Joined records:   {status['joined_records']:,}")
    print(f"  Lock records:     {status['lock_records']:,}")
    print(f"  Node records:     {status['node_records']:,}")
    if status["warnings"]:
        for w in status["warnings"]:
            print(f"  WARNING: {w}")

    total_tons = analyzer.links["total"].sum()
    print(f"\nSystem-wide total tonnage: {total_tons:,.0f} tons")

    print(f"\n--- Top 10 Rivers by Tonnage ---")
    rivers = analyzer.get_tonnage_by_river(top_n=10)
    for _, r in rivers.iterrows():
        print(f"  {r['RIVERNAME']:<35s} {r['total']:>15,.0f} tons  ({r['link_count']} links)")

    print(f"\n--- National Commodity Mix ---")
    mix = analyzer.get_national_commodity_mix()
    for _, c in mix.iterrows():
        print(f"  {c['display_name']:<22s} {c['total_tons']:>15,} tons  ({c['pct']:5.1f}%)")

    print(f"\n--- Top 10 Corridors ---")
    corridors = analyzer.get_top_corridors(top_n=10)
    for _, c in corridors.iterrows():
        print(f"  Link {c['LINKNUM']:>7}  {c['RIVERNAME']:<30s}  {c['total']:>12,.0f} tons")

    print(f"\n--- Directional Flow by Commodity ---")
    dfc = analyzer.get_directional_flow_by_commodity()
    for _, row in dfc.iterrows():
        print(f"  {row['display_name']:<22s} net={row['net_flow']:>+15,}  ({row['direction']})")

    print(f"\n--- Lock Bottleneck Scores (top 10) ---")
    locks_overlay = analyzer.get_lock_traffic_overlay()
    if not locks_overlay.empty:
        for _, lk in locks_overlay.head(10).iterrows():
            flag = " [600ft]" if lk["is_600ft"] else ""
            print(f"  {lk['lock_name']:<40s} score={lk['bottleneck_score']:>10,.1f}  tonnage={lk['adjacent_tonnage']:>12,}{flag}")

    print(f"\n--- Cargo Value Estimates ---")
    vals = analyzer.estimate_cargo_value()
    for _, v in vals.iterrows():
        print(f"  {v['display_name']:<22s} ${v['estimated_value']:>18,.0f}  (@ ${v['value_per_ton']:,.0f}/ton)")

    print(f"\n{'=' * 60}")
    print("Done.")
