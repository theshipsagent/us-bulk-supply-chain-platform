"""
build_voyage_portcall_summary_v1.0.0.py
========================================
Roll up individual cargo records into single-line voyage/port call summaries.

Groups records by (Vessel, Arrival Date, Port_Consolidated) and produces:
  1. Voyage summary table - one row per port call
  2. Source records with Voyage_ID - for drill-down traceability

Test scope: Q1 2024 (Jan 1 - Mar 31, 2024), excluding EXCLUDED group
and Refrigerated/Excluded Carrier commodities.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

BASE = Path(r"G:\My Drive\LLM\project_manifest")
SOURCE = BASE / "00_DATA" / "00.04_FINAL" / "panjiva_MASTER_ENRICHED_20260210_022259.csv"
OUT_DIR = BASE / "03_DOCUMENTATION" / "03.04_summaries"

# Date filter for Q1 2024 test
DATE_START = "2024-01-01"
DATE_END = "2024-03-31"

# Groups to keep (production cargo only)
KEEP_GROUPS = {"Dry Bulk", "Liquid Bulk", "Liquid Gas", "Break Bulk"}

# Vessel types to exclude
EXCLUDE_VESSEL_TYPES = {"RoRo", "Reefer"}

# Commodities to exclude (RoRo carrier cargo + misspelled refrigerated)
EXCLUDE_COMMODITIES = {"Excluded Carrier", "Refiridgerated"}

# Port abbreviation mapping for Voyage_ID generation
PORT_ABBREV = {
    "Houston": "HOU",
    "New York": "NYK",
    "South Texas": "STX",
    "Georgia Ports": "GAP",
    "Seattle-Tacoma": "SEA",
    "Columbia River": "CLR",
    "LA-Long Beach": "LAX",
    "Delaware River": "DEL",
    "New Orleans": "NOL",
    "Mobile": "MOB",
    "Sabine River": "SAB",
    "Hampton Roads": "HRD",
    "Land Ports": "LND",
    "North Florida": "NFL",
    "Boston": "BOS",
    "Great Lakes": "GLK",
    "San Juan": "SJU",
    "South Florida": "SFL",
    "Tampa": "TPA",
    "North Carolina Ports": "NCP",
    "Baltimore": "BAL",
    "Sacramento River": "SAC",
    "Alaska": "AKA",
    "Central California": "CCA",
    "Honolulu": "HNL",
    "Guam": "GUM",
    "South Carolina Ports": "SCP",
    "Connecticut": "CTN",
    "Virgin Islands": "VIS",
    "Portland ME": "PME",
    "Rhode Island": "RHI",
    "American Samoa": "ASM",
    "San Diego": "SDG",
    "Saipan": "SAI",
}


def make_port_abbrev(port_name):
    """Generate a short abbreviation for a port name."""
    name = str(port_name).strip()
    if name in PORT_ABBREV:
        return PORT_ABBREV[name]
    # Fallback: first 3 uppercase letters from alphanumeric chars
    alpha = "".join(c for c in name if c.isalpha()).upper()
    return alpha[:3] if alpha else "UNK"


# =============================================================================
# STEP 1: Load & Filter
# =============================================================================

def load_and_filter(path, date_start, date_end):
    """Load master enriched data and apply filters for Q1 2024 test."""
    print(f"Loading: {path.name}")
    df = pd.read_csv(path, low_memory=False)
    print(f"  Raw records: {len(df):,}")

    # Strip whitespace from Port_Consolidated
    df["Port_Consolidated"] = df["Port_Consolidated"].astype(str).str.strip()

    # Parse arrival date
    df["Arrival_Date_Parsed"] = pd.to_datetime(df["Arrival Date"], errors="coerce")

    # Filter: date range
    mask_date = (df["Arrival_Date_Parsed"] >= date_start) & (df["Arrival_Date_Parsed"] <= date_end)
    df = df[mask_date].copy()
    print(f"  After date filter ({date_start} to {date_end}): {len(df):,}")

    # Filter: exclude EXCLUDED group
    df = df[df["Group"] != "EXCLUDED"].copy()
    print(f"  After excluding EXCLUDED group: {len(df):,}")

    # Filter: keep only production groups
    df = df[df["Group"].isin(KEEP_GROUPS)].copy()
    print(f"  After keeping {KEEP_GROUPS}: {len(df):,}")

    # Filter: exclude RoRo and Reefer vessel types
    df = df[~df["Vessel_Type_Simple"].isin(EXCLUDE_VESSEL_TYPES)].copy()
    print(f"  After excluding {EXCLUDE_VESSEL_TYPES} vessel types: {len(df):,}")

    # Filter: exclude Refrigerated and Excluded Carrier commodities
    df = df[~df["Commodity"].isin(EXCLUDE_COMMODITIES)].copy()
    print(f"  After excluding {EXCLUDE_COMMODITIES} commodities: {len(df):,}")

    return df


# =============================================================================
# STEP 2 & 3: Group and Generate Voyage_IDs
# =============================================================================

def assign_voyage_ids(df):
    """Assign Voyage_ID based on (Vessel, Arrival Date, Port_Consolidated) grouping."""
    # Create grouping key
    df["_arrival_str"] = df["Arrival_Date_Parsed"].dt.strftime("%Y%m%d")
    df["_group_key"] = (
        df["Vessel"].fillna("UNKNOWN").str.strip() + "|" +
        df["_arrival_str"].fillna("") + "|" +
        df["Port_Consolidated"].fillna("UNKNOWN")
    )

    # Sort for consistent ordering
    df = df.sort_values(["Arrival_Date_Parsed", "Port_Consolidated", "Vessel", "REC_ID"]).copy()

    # Assign Voyage_IDs: VPC_YYYYMMDD_PORTABBREV_NNN
    # Sequential counter within each port+date combination
    voyage_ids = {}
    port_date_counters = {}

    for idx, row in df.iterrows():
        gk = row["_group_key"]
        if gk in voyage_ids:
            df.at[idx, "Voyage_ID"] = voyage_ids[gk]
        else:
            port_date_key = row["_arrival_str"] + "|" + row["Port_Consolidated"]
            if port_date_key not in port_date_counters:
                port_date_counters[port_date_key] = 0
            port_date_counters[port_date_key] += 1
            counter = port_date_counters[port_date_key]

            port_abbrev = make_port_abbrev(row["Port_Consolidated"])
            vid = f"VPC_{row['_arrival_str']}_{port_abbrev}_{counter:03d}"
            voyage_ids[gk] = vid
            df.at[idx, "Voyage_ID"] = vid

    # Clean up temp columns
    df.drop(columns=["_arrival_str", "_group_key"], inplace=True)

    n_voyages = df["Voyage_ID"].nunique()
    print(f"\n  Unique port calls generated: {n_voyages:,}")
    print(f"  Records assigned Voyage_IDs: {len(df):,}")

    return df


# =============================================================================
# STEP 4: Build Summary Table
# =============================================================================

def build_summary(df):
    """Aggregate records into one row per port call."""

    def concat_sorted_unique(series):
        vals = series.dropna().unique()
        vals = [str(v).strip() for v in vals if str(v).strip() and str(v).strip().lower() != "nan"]
        return ", ".join(sorted(set(vals)))

    def pipe_join(series):
        return "|".join(series.astype(str))

    def first_non_null(series):
        valid = series.dropna()
        return valid.iloc[0] if len(valid) > 0 else np.nan

    agg = df.groupby("Voyage_ID", sort=False).agg(
        Arrival_Date=("Arrival_Date_Parsed", "first"),
        Port=("Port_Consolidated", "first"),
        Vessel=("Vessel", "first"),
        Voyage_Num=("Voyage", first_non_null),
        Vessel_Type=("Vessel_Type_Simple", first_non_null),
        IMO=("IMO", first_non_null),
        Groups=("Group", concat_sorted_unique),
        Commodities=("Commodity", concat_sorted_unique),
        Origin_Ports=("Origin_Port_Clean", concat_sorted_unique),
        Origin_Countries=("Country of Origin (F)", concat_sorted_unique),
        Total_Tons=("Tons_Numeric", "sum"),
        Record_Count=("REC_ID", "count"),
        REC_IDs=("REC_ID", pipe_join),
    ).reset_index()

    # Format arrival date
    agg["Arrival_Date"] = agg["Arrival_Date"].dt.strftime("%Y-%m-%d")

    # Format IMO as integer where possible
    agg["IMO"] = agg["IMO"].apply(lambda x: int(x) if pd.notna(x) else "")

    # Round tonnage
    agg["Total_Tons"] = agg["Total_Tons"].round(2)

    # Sort by date, port, vessel
    agg = agg.sort_values(["Arrival_Date", "Port", "Vessel"]).reset_index(drop=True)

    print(f"\n  Summary rows (port calls): {len(agg):,}")
    return agg


# =============================================================================
# STEP 5: Statistics
# =============================================================================

def print_statistics(summary, source_df):
    """Print console statistics for validation."""
    print("\n" + "=" * 70)
    print("VOYAGE PORT CALL SUMMARY — STATISTICS")
    print("=" * 70)

    print(f"\n  Total port calls:       {len(summary):,}")
    print(f"  Total source records:   {summary['Record_Count'].sum():,}")
    print(f"  Total tonnage:          {summary['Total_Tons'].sum():,.0f}")

    # Record count distribution
    rc = summary["Record_Count"]
    print(f"\n  Records per port call:")
    print(f"    Min:    {rc.min()}")
    print(f"    Max:    {rc.max()}")
    print(f"    Mean:   {rc.mean():.1f}")
    print(f"    Median: {rc.median():.0f}")

    single = (rc == 1).sum()
    multi = (rc > 1).sum()
    print(f"\n  Single-record port calls: {single:,} ({100*single/len(summary):.1f}%)")
    print(f"  Multi-record port calls:  {multi:,} ({100*multi/len(summary):.1f}%)")

    # Top 10 largest port calls
    print(f"\n  Top 10 largest port calls by record count:")
    top10 = summary.nlargest(10, "Record_Count")[
        ["Voyage_ID", "Arrival_Date", "Port", "Vessel", "Record_Count", "Total_Tons", "Commodities"]
    ]
    for _, row in top10.iterrows():
        commodities_short = row["Commodities"][:50] + ("..." if len(str(row["Commodities"])) > 50 else "")
        print(f"    {row['Voyage_ID']}  {row['Arrival_Date']}  {row['Port']:<20s}  "
              f"{row['Vessel']:<25s}  {row['Record_Count']:>4d} recs  "
              f"{row['Total_Tons']:>12,.0f} tons  {commodities_short}")

    # Commodity distribution
    print(f"\n  Commodity frequency across port calls:")
    all_commodities = []
    for c in summary["Commodities"]:
        all_commodities.extend([x.strip() for x in str(c).split(",") if x.strip()])
    comm_counts = pd.Series(all_commodities).value_counts().head(15)
    for comm, count in comm_counts.items():
        print(f"    {comm:<30s}  {count:>5,} port calls")

    # Vessel type distribution
    print(f"\n  Vessel type distribution:")
    vt = summary["Vessel_Type"].value_counts()
    for vtype, count in vt.items():
        print(f"    {str(vtype):<25s}  {count:>5,} port calls")

    # Port distribution (top 10)
    print(f"\n  Top 10 ports by port call count:")
    ports = summary["Port"].value_counts().head(10)
    for port, count in ports.items():
        print(f"    {port:<25s}  {count:>5,} port calls")

    # Validation checks
    print("\n" + "-" * 70)
    print("VALIDATION CHECKS")
    print("-" * 70)

    # Check 1: Record count matches
    summary_total = summary["Record_Count"].sum()
    source_total = len(source_df)
    match = "PASS" if summary_total == source_total else "FAIL"
    print(f"  [{'PASS' if match == 'PASS' else 'FAIL'}] Record count: summary={summary_total:,}, source={source_total:,}")

    # Check 2: All source records have Voyage_ID
    has_vid = source_df["Voyage_ID"].notna().sum()
    match2 = "PASS" if has_vid == source_total else "FAIL"
    print(f"  [{match2}] All source records have Voyage_ID: {has_vid:,}/{source_total:,}")

    # Check 3: No duplicate Voyage_IDs
    n_unique = summary["Voyage_ID"].nunique()
    n_rows = len(summary)
    match3 = "PASS" if n_unique == n_rows else "FAIL"
    print(f"  [{match3}] Unique Voyage_IDs: {n_unique:,}/{n_rows:,}")

    # Check 4: No excluded groups or commodities
    excluded_check = source_df["Group"].isin(["EXCLUDED"]).sum()
    comm_check = source_df["Commodity"].isin(EXCLUDE_COMMODITIES).sum()
    match4 = "PASS" if excluded_check == 0 and comm_check == 0 else "FAIL"
    print(f"  [{match4}] No EXCLUDED group or skipped commodities: excluded={excluded_check}, skipped_comm={comm_check}")

    print("=" * 70)


# =============================================================================
# MAIN
# =============================================================================

def main():
    start_time = datetime.now()
    print(f"Voyage Port Call Summary Builder v1.0.0")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Step 1: Load and filter
    df = load_and_filter(SOURCE, DATE_START, DATE_END)

    if len(df) == 0:
        print("\nNo records found after filtering. Check date range and filters.")
        return

    # Step 2-3: Assign Voyage_IDs
    df = assign_voyage_ids(df)

    # Step 4: Build summary
    summary = build_summary(df)

    # Step 5: Statistics
    print_statistics(summary, df)

    # Write outputs
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    out_summary = OUT_DIR / "voyage_portcall_summary_Q1_2024_v1.0.0.csv"
    summary.to_csv(out_summary, index=False)
    print(f"\n  Summary written: {out_summary.name} ({len(summary):,} rows)")

    out_source = OUT_DIR / "voyage_portcall_source_records_Q1_2024_v1.0.0.csv"
    # Drop the parsed date helper column before saving
    source_out = df.drop(columns=["Arrival_Date_Parsed"], errors="ignore")
    source_out.to_csv(out_source, index=False)
    print(f"  Source records written: {out_source.name} ({len(source_out):,} rows)")

    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\nCompleted in {elapsed:.1f} seconds")


if __name__ == "__main__":
    main()
