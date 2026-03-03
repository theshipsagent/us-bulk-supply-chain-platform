#!/usr/bin/env python3
"""
mine_exporter_analytics.py
Coal Module — Mine Portfolio + Production vs Export Analytics

Links MSHA mine production data to vessel call export data to produce
three integrated analytical tables:

  1. company_production_vs_exports.csv   Annual production (ST) vs exports (MT),
                                         corrected export totals, export fraction
  2. mine_portfolio_by_exporter.csv      Per-mine records for top exporters,
                                         enriched with coal type, basin, rail
  3. terminal_basin_routing.csv          Terminal-level routing intelligence:
                                         basin origin, shipper share, MET pct,
                                         avg vessel size

Usage:
    python src/mine_exporter_analytics.py          # full run, writes CSVs + DuckDB
    python src/mine_exporter_analytics.py --csv-only
    python src/mine_exporter_analytics.py --preview  # print tables, no write
"""

import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

try:
    import pandas as pd
    import duckdb
    import click
except ImportError:
    print("Install: pip install pandas duckdb click")
    sys.exit(1)

# ─── Paths ────────────────────────────────────────────────────────────────────
MODULE_DIR = Path(__file__).parent.parent
MSHA_DIR   = MODULE_DIR / "data" / "raw" / "msha"
PROCESSED  = MODULE_DIR / "data" / "processed"
DB_PATH    = MODULE_DIR / "data" / "coal_analytics.duckdb"

# ─── Shipper → MSHA controller mapping ───────────────────────────────────────
# Maps vessel-call shipper_norm codes to partial MSHA controller name strings.
# Each entry is (shipper_norm, [controller_keywords]).
# Keywords are OR-matched (case-insensitive) against CURRENT_CONTROLLER_NAME.
COMPANY_MAP = {
    "ALPHA":     ["Alpha Metallurgical Resources"],
    "ARCH":      ["Arch Resources", "Arch Coal"],       # pre-merger name
    "WARRIOR":   ["Warrior Met Coal"],
    "CORONADO":  ["Coronado Coal"],
    "CONSOL":    ["CONSOL Energy"],                     # Baltimore terminal era
    "CNX":       ["CONSOL Energy", "CNX Coal"],         # early era same company
    "CORE":      ["Core Natural Resources"],            # post-merger Arch+CONSOL
    "BLACKHAWK": ["Blackhawk Mining", "Iron Senergy"],  # Iron Senergy = successor
    "RAMACO":    ["Ramaco Resources"],
    "ALLIANCE":  ["Alliance Resource Partners"],
    "BLUESTONE": ["Bluestone Coal", "ACNR Holdings"],   # Bluestone = ACNR entity
}

# ─── Terminal → basin routing intelligence ───────────────────────────────────
TERMINAL_BASIN = {
    # Baltimore (Northern Appalachian, CSX rail from PA/WV)
    "CNX":             ("Northern Appalachian", "PA/WV"),
    "CONSOL":          ("Northern Appalachian", "PA/WV"),
    "CSX":             ("Northern Appalachian", "PA/WV"),  # Curtis Bay, Baltimore
    # Hampton Roads (Central/Northern Appalachian, NS/CSX from WV/VA/KY)
    "DTA":             ("Central Appalachian",  "WV/VA"),  # Dominion Terminal Assoc.
    "NS":              ("Central Appalachian",  "WV/VA"),  # Lambert's Point
    "PIER IX":         ("Central Appalachian",  "WV/VA"),  # Newport News Coal
    # Mobile (Warrior Basin, CSX from AL)
    "MCDUFFIE":        ("Warrior Basin",         "AL"),
    "CHIPCO":          ("Warrior Basin",         "AL"),
    "PASCAGOULA":      ("Warrior Basin",         "AL/MS"),
    # New Orleans / Gulf (Illinois Basin + Gulf thermal via barge)
    "CMT":             ("Illinois Basin / Gulf",  "KY/IL"),  # Burnside / Cargill Marine Terminal
    "BURNSIDE":        ("Illinois Basin / Gulf",  "KY/IL"),
    "UBT":             ("Illinois Basin / Gulf",  "KY/IL"),  # Union Barge Terminal
    "MIDSTREAM BUOYS": ("Gulf Coast Thermal",     "KY/IL/MS"),
    "DEEPWATER":       ("Gulf Coast Thermal",     "KY/IL/MS"),
    "ASCENSION":       ("Gulf Coast Thermal",     "KY/IL/MS"),
    # Houston (misc, limited coal export)
    "HOUSTON":         ("Mixed / Gulf Coast",     "TX/WY"),
}

# ─── Basin → coal type inference (where MSHA data lacks explicit rank) ────────
BASIN_COAL_TYPE = {
    "Central Appalachian":  "Metallurgical",
    "Northern Appalachian": "Met/Thermal",
    "Warrior Basin":        "Metallurgical (Low-vol)",
    "Illinois Basin":       "Thermal (bituminous)",
    "Powder River Basin":   "Thermal (sub-bituminous)",
    "Gulf Coast Lignite":   "Thermal (lignite)",
    "Uinta-Piceance Basin": "Thermal / Met",
}

# ─── Load MSHA quarterly production ──────────────────────────────────────────

def load_msha_production(year_min: int = 2021, year_max: int = 2025) -> pd.DataFrame:
    """
    Load MSHA MinesProdQuarterly.txt + Mines.txt.
    Returns annual production by company (CURRENT_CONTROLLER_NAME) and year.
    Only coal mines (COAL_METAL_IND == 'C').
    """
    mines_path = MSHA_DIR / "Mines.txt"
    prod_path  = MSHA_DIR / "MinesProdQuarterly.txt"

    print("Loading MSHA mine master...")
    dfm = pd.read_csv(mines_path, sep="|", encoding="latin-1", low_memory=False)
    coal_ids = set(dfm[dfm["COAL_METAL_IND"] == "C"]["MINE_ID"].tolist())

    print(f"Loading MSHA quarterly production ({prod_path.stat().st_size / 1e6:.0f} MB)...")
    dfq = pd.read_csv(prod_path, sep="|", encoding="latin-1", low_memory=False)

    # Filter to coal mines and target years
    dfq = dfq[dfq["MINE_ID"].isin(coal_ids)].copy()
    dfq = dfq[(dfq["CAL_YR"] >= year_min) & (dfq["CAL_YR"] <= year_max)]

    # Merge in company name and location from mine master.
    # NOTE: MinesProdQuarterly already has STATE — exclude from dfm merge to avoid _x/_y collision.
    keep_cols = [
        "MINE_ID", "CURRENT_MINE_NAME", "CURRENT_OPERATOR_NAME",
        "CURRENT_CONTROLLER_NAME", "FIPS_CNTY_NM",
        "CURRENT_MINE_TYPE", "CURRENT_MINE_STATUS",
        "LATITUDE", "LONGITUDE", "DISTRICT",
    ]
    # Only keep columns that exist in dfm
    keep_cols = [c for c in keep_cols if c in dfm.columns]
    merged = dfq.merge(dfm[keep_cols], on="MINE_ID", how="left")

    # Annual total per mine per company
    annual = (
        merged.groupby(["MINE_ID", "CURRENT_MINE_NAME", "CURRENT_CONTROLLER_NAME",
                        "STATE", "CURRENT_MINE_STATUS", "CAL_YR"])
        ["COAL_PRODUCTION"].sum()
        .reset_index()
        .rename(columns={"CAL_YR": "year", "COAL_PRODUCTION": "production_st"})
    )
    print(f"  MSHA: {annual['MINE_ID'].nunique():,} coal mines, {year_min}–{year_max}")
    return annual


def msha_annual_by_company(msha_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate annual production by controller name and year."""
    return (
        msha_df.groupby(["CURRENT_CONTROLLER_NAME", "year"])["production_st"]
        .sum()
        .reset_index()
        .rename(columns={"CURRENT_CONTROLLER_NAME": "msha_controller"})
    )


# ─── Build company → MSHA linkage ────────────────────────────────────────────

def assign_shipper_to_controller(msha_annual: pd.DataFrame) -> pd.DataFrame:
    """
    Add shipper_norm column to MSHA annual table by matching controller names
    to COMPANY_MAP keywords. Controllers matching multiple companies keep all
    (rare edge case for CONSOL/CNX pre-merger).
    """
    rows = []
    for shipper, keywords in COMPANY_MAP.items():
        pattern = "|".join(keywords)
        mask = msha_annual["msha_controller"].str.contains(pattern, case=False, na=False, regex=True)
        matches = msha_annual[mask].copy()
        if not matches.empty:
            matches["shipper_norm"] = shipper
            rows.append(matches)
    if not rows:
        return pd.DataFrame()
    linked = pd.concat(rows, ignore_index=True)
    # For CNX/CONSOL: both map to same controller "CONSOL Energy"
    # If same controller appears twice (CNX + CONSOL), keep one row per year
    linked = linked.drop_duplicates(subset=["msha_controller", "year"])
    return linked


# ─── Vessel call export aggregation + correction ─────────────────────────────

def load_vessel_exports() -> pd.DataFrame:
    """Load vessel calls and compute raw annual exports by shipper_norm."""
    vc = pd.read_csv(PROCESSED / "coal_vessel_calls.csv")
    vc["report_date"] = pd.to_datetime(vc["report_date"])
    vc["year"] = vc["report_date"].dt.year

    raw = (
        vc.groupby(["shipper_norm", "year"])
        .agg(
            vessel_calls_n=("vessel_name", "count"),
            raw_exports_mt=("metric_tons", "sum"),
            calls_with_tons=("metric_tons", lambda x: x.notna().sum()),
        )
        .reset_index()
    )
    raw["raw_exports_mt"] = raw["raw_exports_mt"].fillna(0)
    return raw


def load_monthly_correction_factors() -> pd.DataFrame:
    """
    Compute per-month tonnage correction factor using destination flows as ground truth.

    Format 1 PDFs (2021–2024) have ~42% NULL metric_tons due to two-column layout.
    Destination flows capture TOTAL monthly exports (complete, from page text).
    correction_factor = flows_total_mt / vc_sum_mt_with_tons

    Returns DataFrame with [report_month_dt, correction_factor, total_flow_mt, vc_sum_mt].
    """
    vc = pd.read_csv(PROCESSED / "coal_vessel_calls.csv")
    vc["report_date"] = pd.to_datetime(vc["report_date"])
    vc_monthly = (
        vc.groupby("report_date")["metric_tons"]
        .sum()
        .reset_index()
        .rename(columns={"metric_tons": "vc_sum_mt"})
    )

    flows = pd.read_csv(PROCESSED / "coal_destination_flows.csv")
    flows["report_date"] = pd.to_datetime(flows["report_date"])
    flows_monthly = (
        flows.groupby("report_date")["metric_tons"]
        .sum()
        .reset_index()
        .rename(columns={"metric_tons": "total_flow_mt"})
    )

    merged = vc_monthly.merge(flows_monthly, on="report_date", how="inner")
    # Correction factor: how much to scale up vc_sum to match flows total
    # Floor at 1.0 (don't shrink) and cap at 3.0 (anomalies)
    merged["correction_factor"] = (
        (merged["total_flow_mt"] / merged["vc_sum_mt"])
        .clip(lower=1.0, upper=3.0)
        .fillna(1.0)
    )
    merged["year"] = merged["report_date"].dt.year
    return merged


def apply_correction(
    raw_exports: pd.DataFrame,
    correction_monthly: pd.DataFrame,
) -> pd.DataFrame:
    """
    Apply monthly correction factor to raw shipper exports.

    Strategy: the correction factor (flows_total / vc_sum) is global for the month.
    We assume each shipper's NULL rate equals the overall NULL rate.
    Apply: corrected_exports = raw_exports × mean(correction_factor for that year).
    """
    # Annual mean correction factor by year
    annual_cf = (
        correction_monthly.groupby("year")["correction_factor"]
        .mean()
        .reset_index()
        .rename(columns={"correction_factor": "annual_corr_factor"})
    )
    # For reference: coverage of correction months
    coverage = correction_monthly.groupby("year").agg(
        months_with_flows=("report_date", "count"),
        mean_cf=("correction_factor", "mean"),
    )
    print("\nTonnage correction factors by year (flows / vc_sum):")
    print(coverage.round(3).to_string())

    result = raw_exports.merge(annual_cf, on="year", how="left")
    result["annual_corr_factor"] = result["annual_corr_factor"].fillna(1.0)
    result["corrected_exports_mt"] = (
        result["raw_exports_mt"] * result["annual_corr_factor"]
    ).round(0)
    return result


# ─── Table 1: Company production vs exports ──────────────────────────────────

def build_production_vs_exports(
    msha_annual: pd.DataFrame,
    vessel_exports: pd.DataFrame,
) -> pd.DataFrame:
    """
    Join MSHA annual production (ST) with vessel call exports (MT, corrected).
    Compute export fraction: corrected_exports_mt / (production_st × 0.9072).
    """
    # Aggregate MSHA by shipper_norm (some shippers map to 1 controller)
    prod = (
        msha_annual.groupby(["shipper_norm", "year"])["production_st"]
        .sum()
        .reset_index()
    )

    merged = prod.merge(
        vessel_exports[["shipper_norm", "year", "vessel_calls_n",
                         "raw_exports_mt", "corrected_exports_mt",
                         "calls_with_tons", "annual_corr_factor"]],
        on=["shipper_norm", "year"],
        how="outer",
    )
    merged["year"] = merged["year"].astype("Int64")
    merged["production_st"] = merged["production_st"].fillna(0)
    merged["corrected_exports_mt"] = merged["corrected_exports_mt"].fillna(0)

    # Convert ST to MT for comparison (1 ST = 0.9072 MT)
    merged["production_mt_equiv"] = (merged["production_st"] * 0.9072).round(0)

    # Export fraction (corrected)
    import numpy as np
    merged["export_fraction_pct"] = (
        (merged["corrected_exports_mt"] / merged["production_mt_equiv"] * 100)
        .replace([float("inf"), -float("inf")], np.nan)
        .clip(upper=100)
        .round(1)
    )

    # Sort: company then year
    merged = merged.sort_values(["shipper_norm", "year"]).reset_index(drop=True)

    out_cols = [
        "shipper_norm", "year",
        "production_st", "production_mt_equiv",
        "vessel_calls_n", "calls_with_tons",
        "raw_exports_mt", "annual_corr_factor", "corrected_exports_mt",
        "export_fraction_pct",
    ]
    out_cols = [c for c in out_cols if c in merged.columns]
    return merged[out_cols]


# ─── Table 2: Mine portfolio by exporter ─────────────────────────────────────

def build_mine_portfolio(msha_df: pd.DataFrame) -> pd.DataFrame:
    """
    For each export-relevant shipper, build a per-mine record showing:
    mine identity, location, production trend, status, inferred coal type.
    """
    # Load top_us_coal_mines for railroad and export_relevant flag
    top_mines_path = PROCESSED / "top_us_coal_mines.csv"
    top_mines = pd.read_csv(top_mines_path) if top_mines_path.exists() else pd.DataFrame()

    # Assign shippers to MSHA production data (mine-level)
    rows = []
    for shipper, keywords in COMPANY_MAP.items():
        pattern = "|".join(keywords)
        mask = msha_df["CURRENT_CONTROLLER_NAME"].str.contains(
            pattern, case=False, na=False, regex=True
        )
        matches = msha_df[mask].copy()
        if not matches.empty:
            matches["shipper_norm"] = shipper
            rows.append(matches)

    if not rows:
        return pd.DataFrame()

    mines = pd.concat(rows, ignore_index=True)

    # Pivot production years wide: prod_2021, prod_2022, etc.
    prod_wide = (
        mines.pivot_table(
            index=["MINE_ID", "CURRENT_MINE_NAME", "CURRENT_CONTROLLER_NAME",
                   "STATE", "CURRENT_MINE_STATUS", "shipper_norm"],
            columns="year",
            values="production_st",
            aggfunc="sum",
        )
        .reset_index()
    )
    prod_wide.columns.name = None
    # Rename year columns
    year_cols = [c for c in prod_wide.columns if isinstance(c, (int, float)) and 2000 < c < 2030]
    for yr in year_cols:
        prod_wide.rename(columns={yr: f"prod_{int(yr)}_st"}, inplace=True)

    # Annual average and total production across all years
    prod_yr_cols = [f"prod_{int(yr)}_st" for yr in year_cols]
    prod_wide["prod_avg_annual_st"] = prod_wide[prod_yr_cols].mean(axis=1).round(0)
    prod_wide["prod_total_st"]      = prod_wide[prod_yr_cols].sum(axis=1).round(0)

    # Basin assignment from state
    STATE_BASIN = {
        "WV": "Central/Northern Appalachian", "VA": "Central Appalachian",
        "KY": "Central/Northern Appalachian", "PA": "Northern Appalachian",
        "OH": "Northern Appalachian",          "AL": "Warrior Basin",
        "WY": "Powder River Basin",            "MT": "Powder River Basin",
        "IL": "Illinois Basin",                "IN": "Illinois Basin",
        "UT": "Uinta-Piceance Basin",          "CO": "Uinta-Piceance Basin",
        "TX": "Gulf Coast Lignite",            "ND": "Lignite (Williston)",
        "MS": "Gulf Coast Lignite",
    }
    prod_wide["basin"] = prod_wide["STATE"].map(STATE_BASIN).fillna("Other")
    prod_wide["inferred_coal_type"] = prod_wide["basin"].map(BASIN_COAL_TYPE).fillna("Unknown")

    # Merge lat/lon and railroad from top_us_coal_mines if available
    if not top_mines.empty and "msha_id" in top_mines.columns:
        top_mines = top_mines.rename(columns={
            "msha_id": "MINE_ID",
            "lon": "longitude",
            "lat": "latitude",
            "railroad_served": "railroad",
            "export_relevant": "export_relevant",
            "coal_type": "coal_type_curated",
        })
        # msha_id loaded as str from CSV — coerce to int to match MSHA DataFrame
        top_mines["MINE_ID"] = pd.to_numeric(top_mines["MINE_ID"], errors="coerce").astype("Int64")
        prod_wide["MINE_ID"]  = prod_wide["MINE_ID"].astype("Int64")
        merge_cols = ["MINE_ID", "longitude", "latitude", "railroad",
                      "export_relevant", "coal_type_curated"]
        merge_cols = [c for c in merge_cols if c in top_mines.columns]
        prod_wide = prod_wide.merge(
            top_mines[merge_cols], on="MINE_ID", how="left"
        )

    # Sort: shipper → production descending
    prod_wide = prod_wide.sort_values(
        ["shipper_norm", "prod_avg_annual_st"], ascending=[True, False]
    ).reset_index(drop=True)

    # Active-mine flag (CURRENT_MINE_STATUS)
    prod_wide["is_active"] = (
        prod_wide["CURRENT_MINE_STATUS"].str.lower() == "active"
    ).astype(int)

    return prod_wide


# ─── Table 3: Terminal-basin routing matrix ───────────────────────────────────

def build_terminal_routing(year_min: int = 2021, year_max: int = 2025) -> pd.DataFrame:
    """
    From vessel call data, build a terminal-level routing intelligence table.
    Per terminal: port, basin, top shippers, MET pct, avg vessel size,
    total volume (corrected), vessel calls count.
    """
    vc = pd.read_csv(PROCESSED / "coal_vessel_calls.csv")
    vc["report_date"] = pd.to_datetime(vc["report_date"])
    vc = vc[(vc["report_date"].dt.year >= year_min) &
            (vc["report_date"].dt.year <= year_max)].copy()

    # Normalize terminal to uppercase
    vc["terminal"] = vc["terminal"].str.upper().str.strip()

    # Base aggregation per port + terminal
    def top_shippers(series, n=3):
        counts = series.dropna().value_counts()
        top = counts.head(n).index.tolist()
        return " / ".join(top) if top else ""

    def pct_met(series):
        total = len(series)
        if total == 0:
            return None
        met = (series == "MET").sum()
        return round(met / total * 100, 1)

    grouped = vc.groupby(["port", "terminal"]).agg(
        vessel_calls         = ("vessel_name", "count"),
        calls_with_tons      = ("metric_tons", lambda x: x.notna().sum()),
        raw_mt_sum           = ("metric_tons", "sum"),
        avg_vessel_mt        = ("metric_tons", "mean"),
        met_pct              = ("coal_type", pct_met),
        top_shippers_str     = ("shipper_norm", lambda x: top_shippers(x)),
        top_countries_str    = ("destination_country", lambda x: top_shippers(x)),
        unique_shippers      = ("shipper_norm", "nunique"),
    ).reset_index()

    # Add basin from lookup
    grouped["basin_origin"] = grouped["terminal"].map(
        {k: v[0] for k, v in TERMINAL_BASIN.items()}
    ).fillna("Unknown")
    grouped["states_origin"] = grouped["terminal"].map(
        {k: v[1] for k, v in TERMINAL_BASIN.items()}
    ).fillna("?")

    # Round numeric cols
    grouped["avg_vessel_mt"] = grouped["avg_vessel_mt"].round(0)
    grouped["raw_mt_sum"]    = grouped["raw_mt_sum"].round(0)

    # Coverage note
    grouped["tonnage_completeness_pct"] = (
        grouped["calls_with_tons"] / grouped["vessel_calls"] * 100
    ).round(1)

    # Sort by raw_mt_sum descending
    grouped = grouped.sort_values("raw_mt_sum", ascending=False).reset_index(drop=True)

    return grouped


# ─── Load to DuckDB ───────────────────────────────────────────────────────────

def load_tables_to_duckdb(tables: dict[str, pd.DataFrame], db_path: Path) -> None:
    """Add/replace analytics tables in coal_analytics.duckdb."""
    conn = duckdb.connect(str(db_path))
    for table_name, df in tables.items():
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.register("_df", df)
        conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM _df")
        conn.unregister("_df")
        n = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"  {table_name}: {n:,} rows loaded to DuckDB")
    conn.close()


# ─── Print summary ────────────────────────────────────────────────────────────

def print_production_vs_exports_summary(df: pd.DataFrame) -> None:
    """Print a readable production vs exports summary table."""
    print("\n" + "="*80)
    print("COMPANY PRODUCTION vs EXPORTS  (Production in Million ST | Exports in Million MT)")
    print("="*80)
    print(f"{'Company':12s}  {'Year':4s}  {'Prod MST':>9s}  {'VC Exports MT':>14s}  {'Corrected MT':>13s}  {'Export %':>8s}")
    print("-"*80)
    for _, row in df.iterrows():
        if pd.isna(row.get("year")):
            continue
        prod    = row.get("production_st", 0) / 1e6
        raw_exp = row.get("raw_exports_mt", 0) / 1e6
        cor_exp = row.get("corrected_exports_mt", 0) / 1e6
        ex_pct  = row.get("export_fraction_pct")
        ex_str  = f"{ex_pct:.1f}%" if pd.notna(ex_pct) and ex_pct > 0 else " --"
        print(
            f"{str(row['shipper_norm']):12s}  "
            f"{int(row['year']):4d}  "
            f"{prod:>9.2f}  "
            f"{raw_exp:>14.2f}  "
            f"{cor_exp:>13.2f}  "
            f"{ex_str:>8s}"
        )


def print_terminal_routing_summary(df: pd.DataFrame) -> None:
    """Print terminal routing matrix."""
    print("\n" + "="*100)
    print("TERMINAL-BASIN ROUTING INTELLIGENCE")
    print("="*100)
    print(f"{'Port':12s}  {'Terminal':18s}  {'Basin Origin':30s}  "
          f"{'Calls':6s}  {'MET%':6s}  {'Avg MT':8s}  {'Top Shippers'}")
    print("-"*100)
    for _, row in df.iterrows():
        calls = int(row.get("vessel_calls", 0))
        if calls < 3:
            continue
        met_pct = f"{row['met_pct']:.0f}%" if pd.notna(row["met_pct"]) else "--"
        avg_mt  = f"{row['avg_vessel_mt']:,.0f}" if pd.notna(row["avg_vessel_mt"]) else "--"
        print(
            f"{str(row.get('port', '')):12s}  "
            f"{str(row.get('terminal', '')):18s}  "
            f"{str(row.get('basin_origin', '')):30s}  "
            f"{calls:6d}  "
            f"{met_pct:6s}  "
            f"{avg_mt:>8s}  "
            f"{str(row.get('top_shippers_str', ''))}"
        )


# ─── CLI ──────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--csv-only",  is_flag=True, help="Write CSVs only, skip DuckDB")
@click.option("--preview",   is_flag=True, help="Print tables, don't write anything")
@click.option("--year-min",  default=2021, show_default=True, help="First year")
@click.option("--year-max",  default=2025, show_default=True, help="Last year")
def main(csv_only, preview, year_min, year_max):
    """
    Build mine portfolio + production vs export analytics for US coal exporters.

    Integrates MSHA quarterly mine production with vessel call export records.
    """
    print("\nCoal Mine-to-Exporter Analytics")
    print(f"Period: {year_min}–{year_max}\n")

    # ── Step 1: MSHA production ───────────────────────────────────────────────
    print("Step 1: Loading MSHA mine production data...")
    msha_mine_level = load_msha_production(year_min, year_max)
    msha_annual     = msha_annual_by_company(msha_mine_level)
    msha_with_shipper = assign_shipper_to_controller(msha_annual)

    print(f"\nExport-relevant company-year rows: {len(msha_with_shipper)}")
    print("Companies matched:", sorted(msha_with_shipper["shipper_norm"].unique().tolist()))

    # ── Step 2: Vessel call exports + correction ──────────────────────────────
    print("\nStep 2: Loading vessel call exports...")
    raw_exports = load_vessel_exports()

    print("\nStep 3: Computing tonnage correction factors...")
    correction_monthly = load_monthly_correction_factors()
    vessel_exports = apply_correction(raw_exports, correction_monthly)

    # ── Step 3: Table 1 — Production vs Exports ───────────────────────────────
    print("\nStep 4: Building production vs exports table...")
    prod_vs_exp = build_production_vs_exports(msha_with_shipper, vessel_exports)
    print_production_vs_exports_summary(prod_vs_exp)

    # ── Step 4: Table 2 — Mine portfolio ─────────────────────────────────────
    print("\nStep 5: Building mine portfolio table...")
    mine_portfolio = build_mine_portfolio(msha_mine_level)
    total_mines = mine_portfolio["MINE_ID"].nunique() if not mine_portfolio.empty else 0
    print(f"  Mines in portfolio: {total_mines}")
    if not mine_portfolio.empty:
        print("\nActive mines by shipper (count × avg annual prod):")
        summary = (
            mine_portfolio[mine_portfolio["is_active"] == 1]
            .groupby("shipper_norm")
            .agg(
                active_mines=("MINE_ID", "nunique"),
                avg_annual_st=("prod_avg_annual_st", "sum"),
                states=("STATE", lambda x: "/".join(sorted(x.unique()))),
                basin=("basin", lambda x: x.mode().iloc[0] if len(x) else "--"),
            )
            .sort_values("avg_annual_st", ascending=False)
        )
        summary["avg_annual_mst"] = (summary["avg_annual_st"] / 1e6).round(2)
        print(summary[["active_mines", "avg_annual_mst", "states", "basin"]].to_string())

    # ── Step 5: Table 3 — Terminal routing ────────────────────────────────────
    print("\nStep 6: Building terminal routing table...")
    terminal_routing = build_terminal_routing(year_min, year_max)
    print_terminal_routing_summary(terminal_routing)

    # ── Write outputs ─────────────────────────────────────────────────────────
    if preview:
        print("\n(preview mode — no files written)")
        return

    print("\nWriting CSVs...")
    PROCESSED.mkdir(parents=True, exist_ok=True)

    out_files = {
        "company_production_vs_exports": prod_vs_exp,
        "mine_portfolio_by_exporter":    mine_portfolio,
        "terminal_basin_routing":        terminal_routing,
    }
    for fname, df in out_files.items():
        path = PROCESSED / f"{fname}.csv"
        df.to_csv(path, index=False)
        print(f"  Saved: {path} ({len(df):,} rows)")

    if not csv_only and DB_PATH.exists():
        print("\nLoading to DuckDB...")
        load_tables_to_duckdb(
            {f"coal_{k}": v for k, v in out_files.items()},
            DB_PATH,
        )
    elif not csv_only:
        print("(DuckDB not found — run extract_coal_reports.py first)")

    print("\nDone.")


if __name__ == "__main__":
    main()
