"""
Merge USACE Entrance and Clearance Records into Complete Port Calls v1.0.0

Matches entrance (arrival) and clearance (departure) records to create
complete port call records with origin, US port, and destination.

TYPEDOC values:
- 0 = Entrance only (no matching clearance)
- 1 = Clearance only (no matching entrance)
- 2 = Complete port call (entrance + clearance matched)

Author: WSD3 / Claude Code
Date: 2026-02-06
Version: 1.0.0
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

def parse_ecdate(ecdate_str):
    """Parse MMYDD format to YYYY-MM-DD"""
    s = str(ecdate_str).strip()

    if len(s) == 5:  # MMYDD
        mm = s[0:2]
        y = s[2]
        dd = s[3:5]
        year = f'202{y}'
    elif len(s) == 4:  # MYDD
        mm = s[0:1].zfill(2)
        y = s[1]
        dd = s[2:4]
        year = f'202{y}'
    else:
        return None

    try:
        date_obj = datetime.strptime(f'{year}-{mm}-{dd}', '%Y-%m-%d')
        return date_obj.strftime('%Y-%m-%d')
    except:
        return None

def convert_draft_to_meters(draft_ft, draft_in):
    """Convert draft from feet+inches to meters"""
    try:
        ft = float(draft_ft) if draft_ft and str(draft_ft).strip() else 0
        inches = float(draft_in) if draft_in and str(draft_in).strip() else 0
        total_feet = ft + (inches / 12)
        meters = total_feet * 0.3048
        return round(meters, 2)
    except:
        return None

def merge_port_calls(entrance_file, clearance_file, output_dir):
    """Merge entrance and clearance records into complete port calls"""

    print("=" * 80)
    print("USACE Port Call Merge v1.0.0")
    print("=" * 80)
    print()

    # Read entrance and clearance data
    print(f"Reading entrance data: {entrance_file.name}")
    df_ent = pd.read_csv(entrance_file, dtype=str)
    print(f"  Loaded {len(df_ent):,} entrance records")
    print()

    print(f"Reading clearance data: {clearance_file.name}")
    df_clr = pd.read_csv(clearance_file, dtype=str)
    print(f"  Loaded {len(df_clr):,} clearance records")
    print()

    # Parse dates
    print("Parsing dates (MMYDD format)...")
    df_ent['Arrival_Date_Parsed'] = df_ent['Arrival_Date'].apply(parse_ecdate)
    df_clr['Clearance_Date_Parsed'] = df_clr['Clearance_Date'].apply(parse_ecdate)

    # Convert to datetime for calculations
    df_ent['Arrival_Date_dt'] = pd.to_datetime(df_ent['Arrival_Date_Parsed'])
    df_clr['Clearance_Date_dt'] = pd.to_datetime(df_clr['Clearance_Date_Parsed'])

    print(f"  Entrance dates parsed: {df_ent['Arrival_Date_dt'].notna().sum():,}")
    print(f"  Clearance dates parsed: {df_clr['Clearance_Date_dt'].notna().sum():,}")
    print()

    # Calculate draft in meters for both
    print("Converting draft measurements to meters...")
    df_ent['Arrival_Draft_Meters'] = df_ent.apply(
        lambda row: convert_draft_to_meters(row['DRAFT_FT'], row['DRAFT_IN']), axis=1
    )
    df_clr['Clearance_Draft_Meters'] = df_clr.apply(
        lambda row: convert_draft_to_meters(row['DRAFT_FT'], row['DRAFT_IN']), axis=1
    )
    print()

    # Matching process
    print("=" * 80)
    print("MATCHING ENTRANCE + CLEARANCE BY IMO + PORT")
    print("=" * 80)
    print()

    merged_records = []
    entrance_only = []
    clearance_only = []

    matched_ent_indices = set()
    matched_clr_indices = set()

    # Filter out records with missing IMO or PORT (cannot match)
    df_ent_valid = df_ent[(df_ent['IMO'].notna()) & (df_ent['IMO'] != '') &
                           (df_ent['PORT'].notna()) & (df_ent['PORT'] != '')].copy()
    df_clr_valid = df_clr[(df_clr['IMO'].notna()) & (df_clr['IMO'] != '') &
                           (df_clr['PORT'].notna()) & (df_clr['PORT'] != '')].copy()

    print(f"Records with valid IMO+PORT:")
    print(f"  Entrance: {len(df_ent_valid):,} ({len(df_ent_valid)/len(df_ent)*100:.1f}%)")
    print(f"  Clearance: {len(df_clr_valid):,} ({len(df_clr_valid)/len(df_clr)*100:.1f}%)")
    print()

    # Group by IMO + PORT
    ent_groups = df_ent_valid.groupby(['IMO', 'PORT'])
    clr_groups = df_clr_valid.groupby(['IMO', 'PORT'])

    ent_keys = set(ent_groups.groups.keys())
    clr_keys = set(clr_groups.groups.keys())

    # Match where both entrance and clearance exist
    matched_keys = ent_keys & clr_keys
    print(f"IMO+PORT combinations:")
    print(f"  Both entrance and clearance: {len(matched_keys):,}")
    print(f"  Entrance only: {len(ent_keys - clr_keys):,}")
    print(f"  Clearance only: {len(clr_keys - ent_keys):,}")
    print()

    print("Matching records...")
    match_count = 0

    for key in matched_keys:
        imo, port = key

        # Get all entrances and clearances for this IMO+PORT
        ent_indices = ent_groups.get_group(key).index.tolist()
        clr_indices = clr_groups.get_group(key).index.tolist()

        # Sort by date
        ent_sorted = sorted(ent_indices, key=lambda i: df_ent.loc[i, 'Arrival_Date_dt'])
        clr_sorted = sorted(clr_indices, key=lambda i: df_clr.loc[i, 'Clearance_Date_dt'])

        # Match each entrance to next clearance
        for ent_idx in ent_sorted:
            if ent_idx in matched_ent_indices:
                continue

            ent_date = df_ent.loc[ent_idx, 'Arrival_Date_dt']
            ent_row = df_ent.loc[ent_idx]

            # Find next clearance after this entrance
            for clr_idx in clr_sorted:
                if clr_idx in matched_clr_indices:
                    continue

                clr_date = df_clr.loc[clr_idx, 'Clearance_Date_dt']
                clr_row = df_clr.loc[clr_idx]

                # Match if clearance is after entrance
                if pd.notna(clr_date) and pd.notna(ent_date) and clr_date > ent_date:
                    # Create merged record
                    merged = create_merged_record(ent_row, clr_row)
                    merged_records.append(merged)

                    matched_ent_indices.add(ent_idx)
                    matched_clr_indices.add(clr_idx)
                    match_count += 1
                    break

    print(f"  Complete port calls matched: {match_count:,}")
    print()

    # Collect unmatched entrances (includes invalid IMO/PORT records)
    print("Processing unmatched entrances...")
    for idx in df_ent.index:
        if idx not in matched_ent_indices:
            ent_only = create_entrance_only_record(df_ent.loc[idx])
            entrance_only.append(ent_only)
    print(f"  Entrance-only records: {len(entrance_only):,}")

    invalid_ent = len(df_ent) - len(df_ent_valid)
    if invalid_ent > 0:
        print(f"    (includes {invalid_ent:,} with missing IMO/PORT)")
    print()

    # Collect unmatched clearances (includes invalid IMO/PORT records)
    print("Processing unmatched clearances...")
    for idx in df_clr.index:
        if idx not in matched_clr_indices:
            clr_only = create_clearance_only_record(df_clr.loc[idx])
            clearance_only.append(clr_only)
    print(f"  Clearance-only records: {len(clearance_only):,}")

    invalid_clr = len(df_clr) - len(df_clr_valid)
    if invalid_clr > 0:
        print(f"    (includes {invalid_clr:,} with missing IMO/PORT)")
    print()

    # Create dataframes
    df_complete = pd.DataFrame(merged_records)
    df_ent_only = pd.DataFrame(entrance_only)
    df_clr_only = pd.DataFrame(clearance_only)

    # Add Port_Call_ID
    if len(df_complete) > 0:
        df_complete['Port_Call_ID'] = range(1, len(df_complete) + 1)
    if len(df_ent_only) > 0:
        df_ent_only['Port_Call_ID'] = range(len(df_complete) + 1, len(df_complete) + len(df_ent_only) + 1)
    if len(df_clr_only) > 0:
        df_clr_only['Port_Call_ID'] = range(len(df_complete) + len(df_ent_only) + 1,
                                              len(df_complete) + len(df_ent_only) + len(df_clr_only) + 1)

    # Summary statistics
    print("=" * 80)
    print("MERGE SUMMARY")
    print("=" * 80)
    print()

    total_records = len(df_ent) + len(df_clr)
    print(f"Total input records: {total_records:,}")
    print(f"  Entrance records: {len(df_ent):,}")
    print(f"  Clearance records: {len(df_clr):,}")
    print()

    print(f"Output port calls: {len(df_complete) + len(df_ent_only) + len(df_clr_only):,}")
    print(f"  Complete (TYPEDOC=2): {len(df_complete):,} ({len(df_complete)/(len(df_ent))*100:.1f}% of entrances)")
    print(f"  Entrance only (TYPEDOC=0): {len(df_ent_only):,} ({len(df_ent_only)/len(df_ent)*100:.1f}% of entrances)")
    print(f"  Clearance only (TYPEDOC=1): {len(df_clr_only):,} ({len(df_clr_only)/len(df_clr)*100:.1f}% of clearances)")
    print()

    # Days in port statistics
    if len(df_complete) > 0:
        days_in_port = df_complete['Days_in_Port'].dropna()
        if len(days_in_port) > 0:
            print("Days in port statistics (complete port calls):")
            print(f"  Average: {days_in_port.mean():.1f} days")
            print(f"  Median: {days_in_port.median():.1f} days")
            print(f"  Min: {days_in_port.min():.1f} days")
            print(f"  Max: {days_in_port.max():.1f} days")
            print()

    # Draft change statistics
    if len(df_complete) > 0:
        draft_change = df_complete['Draft_Change_Meters'].dropna()
        if len(draft_change) > 0:
            loaded = (draft_change > 2.0).sum()
            discharged = (draft_change < -2.0).sum()
            neutral = ((draft_change >= -2.0) & (draft_change <= 2.0)).sum()

            print("Draft change statistics (complete port calls):")
            print(f"  Loaded (draft increased >2.0m): {loaded:,} ({loaded/len(draft_change)*100:.1f}%)")
            print(f"  Discharged (draft decreased >2.0m): {discharged:,} ({discharged/len(draft_change)*100:.1f}%)")
            print(f"  Neutral (±2.0m): {neutral:,} ({neutral/len(draft_change)*100:.1f}%)")
            print(f"  Average draft change: {draft_change.mean():.2f} meters")
            print()

    # Save files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_version = "v4.0.0"

    print("Saving output files...")
    print()

    if len(df_complete) > 0:
        complete_file = output_dir / f"usace_2023_port_calls_COMPLETE_{base_version}_{timestamp}.csv"
        df_complete.to_csv(complete_file, index=False)
        print(f"[1] COMPLETE: {complete_file.name}")
        print(f"    {len(df_complete):,} records")
        print()

    if len(df_ent_only) > 0:
        ent_only_file = output_dir / f"usace_2023_port_calls_ENTRANCE_ONLY_{base_version}_{timestamp}.csv"
        df_ent_only.to_csv(ent_only_file, index=False)
        print(f"[2] ENTRANCE ONLY: {ent_only_file.name}")
        print(f"    {len(df_ent_only):,} records")
        print()

    if len(df_clr_only) > 0:
        clr_only_file = output_dir / f"usace_2023_port_calls_CLEARANCE_ONLY_{base_version}_{timestamp}.csv"
        df_clr_only.to_csv(clr_only_file, index=False)
        print(f"[3] CLEARANCE ONLY: {clr_only_file.name}")
        print(f"    {len(df_clr_only):,} records")
        print()

    print("=" * 80)
    print()

    return df_complete, df_ent_only, df_clr_only

def create_merged_record(ent_row, clr_row):
    """Create a complete port call record (TYPEDOC=2)"""

    # Calculate days in port
    try:
        arrival = pd.to_datetime(ent_row['Arrival_Date_Parsed'])
        clearance = pd.to_datetime(clr_row['Clearance_Date_Parsed'])
        days_in_port = (clearance - arrival).days
    except:
        days_in_port = None

    # Calculate draft change
    try:
        arrival_draft = float(ent_row['Arrival_Draft_Meters'])
        clearance_draft = float(clr_row['Clearance_Draft_Meters'])
        draft_change = round(clearance_draft - arrival_draft, 2)
    except:
        draft_change = None
        arrival_draft = ent_row.get('Arrival_Draft_Meters')
        clearance_draft = clr_row.get('Clearance_Draft_Meters')

    merged = {
        # Port Call Identification
        'TYPEDOC': '2',  # Complete port call
        'Entrance_RECID': ent_row['RECID'],
        'Clearance_RECID': clr_row['RECID'],

        # Timing
        'Arrival_Date': ent_row['Arrival_Date_Parsed'],
        'Clearance_Date': clr_row['Clearance_Date_Parsed'],
        'Days_in_Port': days_in_port,

        # US Port (from entrance)
        'PORT': ent_row['PORT'],
        'US_Port_USACE': ent_row['US_Port_USACE'],
        'Port_Consolidated': ent_row['Port_Consolidated'],
        'Port_Coast': ent_row['Port_Coast'],
        'Port_Region': ent_row['Port_Region'],
        'PWW_IND': ent_row['PWW_IND'],

        # Vessel (from entrance)
        'Vessel': ent_row['Vessel'],
        'IMO': ent_row['IMO'],
        'FLAG_CTRY': ent_row['FLAG_CTRY'],
        'RIG_DESC': ent_row['RIG_DESC'],
        'ICST_DESC': ent_row['ICST_DESC'],

        # Vessel tonnage (from entrance)
        'NRT': ent_row['NRT'],
        'GRT': ent_row['GRT'],
        'Ships_GT': ent_row['Ships_GT'],

        # Vessel dimensions (from entrance)
        'Ships_LOA': ent_row['Ships_LOA'],
        'Ships_Beam': ent_row['Ships_Beam'],
        'Ships_Draft': ent_row['Ships_Draft'],
        'Vessel_Dwt_Draft_ft': ent_row['Vessel_Dwt_Draft_ft'],

        # Vessel capacity (from entrance)
        'Ships_DWT': ent_row['Ships_DWT'],
        'Ships_Grain': ent_row['Ships_Grain'],
        'Ships_TPC': ent_row['Ships_TPC'],

        # Draft at arrival (from entrance)
        'DRAFT_FT': ent_row['DRAFT_FT'],
        'DRAFT_IN': ent_row['DRAFT_IN'],
        'Draft_Pct_of_Max': ent_row['Draft_Pct_of_Max'],
        'Forecasted_Activity': ent_row['Forecasted_Activity'],

        # Draft analysis
        'Arrival_Draft_Meters': arrival_draft,
        'Clearance_Draft_Meters': clearance_draft,
        'Draft_Change_Meters': draft_change,

        # Vessel type detail (from entrance)
        'Ships_Type': ent_row['Ships_Type'],
        'Ships_Vessel': ent_row['Ships_Vessel'],
        'Ships_Match': ent_row['Ships_Match'],
        'Vessel_Match_Method': ent_row['Vessel_Match_Method'],

        # Origin port (from entrance WHERE_*)
        'Origin_IND': ent_row['WHERE_IND'],
        'Origin_PORT': ent_row['WHERE_PORT'],
        'Origin_SCHEDK': ent_row['WHERE_SCHEDK'],
        'Origin_Name': ent_row['WHERE_NAME'],
        'Origin_Country': ent_row['WHERE_CTRY'],
        'Origin_US_Port_USACE': ent_row['Previous_US_Port_USACE'],
        'Origin_Foreign_Port': ent_row['Previous_Foreign_Port'],
        'Origin_Foreign_Country': ent_row['Previous_Foreign_Country'],

        # Destination port (from clearance WHERE_*)
        'Destination_IND': clr_row['WHERE_IND'],
        'Destination_PORT': clr_row['WHERE_PORT'],
        'Destination_SCHEDK': clr_row['WHERE_SCHEDK'],
        'Destination_Name': clr_row['WHERE_NAME'],
        'Destination_Country': clr_row['WHERE_CTRY'],
        'Destination_US_Port_USACE': clr_row['Previous_US_Port_USACE'],
        'Destination_Foreign_Port': clr_row['Previous_Foreign_Port'],
        'Destination_Foreign_Country': clr_row['Previous_Foreign_Country'],

        # Cargo (from entrance)
        'Group': ent_row['Group'],
        'Commodity': ent_row['Commodity'],
        'Carrier_Name': ent_row['Carrier_Name'],
        'Tons': ent_row['Tons'],
        'CONTAINER': ent_row['CONTAINER'],

        # Fees (from entrance - ONE per port call)
        'Fee_Base': ent_row['Fee_Base'],
        'Fee_Adj': ent_row['Fee_Adj'],
        'Fee_Class': ent_row['Fee_Class'],
        'Agency_Fee': ent_row['Agency_Fee'],
        'Agency_Fee_Adj': ent_row['Agency_Fee_Adj'],

        # Administrative
        'Count': '1',
    }

    return merged

def create_entrance_only_record(ent_row):
    """Create entrance-only record (TYPEDOC=0)"""

    record = {
        # Port Call Identification
        'TYPEDOC': '0',  # Entrance only
        'Entrance_RECID': ent_row['RECID'],
        'Clearance_RECID': '',

        # Timing
        'Arrival_Date': ent_row['Arrival_Date_Parsed'],
        'Clearance_Date': '',
        'Days_in_Port': '',

        # US Port
        'PORT': ent_row['PORT'],
        'US_Port_USACE': ent_row['US_Port_USACE'],
        'Port_Consolidated': ent_row['Port_Consolidated'],
        'Port_Coast': ent_row['Port_Coast'],
        'Port_Region': ent_row['Port_Region'],
        'PWW_IND': ent_row['PWW_IND'],

        # Vessel
        'Vessel': ent_row['Vessel'],
        'IMO': ent_row['IMO'],
        'FLAG_CTRY': ent_row['FLAG_CTRY'],
        'RIG_DESC': ent_row['RIG_DESC'],
        'ICST_DESC': ent_row['ICST_DESC'],

        # Vessel tonnage
        'NRT': ent_row['NRT'],
        'GRT': ent_row['GRT'],
        'Ships_GT': ent_row['Ships_GT'],

        # Vessel dimensions
        'Ships_LOA': ent_row['Ships_LOA'],
        'Ships_Beam': ent_row['Ships_Beam'],
        'Ships_Draft': ent_row['Ships_Draft'],
        'Vessel_Dwt_Draft_ft': ent_row['Vessel_Dwt_Draft_ft'],

        # Vessel capacity
        'Ships_DWT': ent_row['Ships_DWT'],
        'Ships_Grain': ent_row['Ships_Grain'],
        'Ships_TPC': ent_row['Ships_TPC'],

        # Draft at arrival
        'DRAFT_FT': ent_row['DRAFT_FT'],
        'DRAFT_IN': ent_row['DRAFT_IN'],
        'Draft_Pct_of_Max': ent_row['Draft_Pct_of_Max'],
        'Forecasted_Activity': ent_row['Forecasted_Activity'],

        # Draft analysis
        'Arrival_Draft_Meters': ent_row.get('Arrival_Draft_Meters', ''),
        'Clearance_Draft_Meters': '',
        'Draft_Change_Meters': '',

        # Vessel type detail
        'Ships_Type': ent_row['Ships_Type'],
        'Ships_Vessel': ent_row['Ships_Vessel'],
        'Ships_Match': ent_row['Ships_Match'],
        'Vessel_Match_Method': ent_row['Vessel_Match_Method'],

        # Origin port
        'Origin_IND': ent_row['WHERE_IND'],
        'Origin_PORT': ent_row['WHERE_PORT'],
        'Origin_SCHEDK': ent_row['WHERE_SCHEDK'],
        'Origin_Name': ent_row['WHERE_NAME'],
        'Origin_Country': ent_row['WHERE_CTRY'],
        'Origin_US_Port_USACE': ent_row['Previous_US_Port_USACE'],
        'Origin_Foreign_Port': ent_row['Previous_Foreign_Port'],
        'Origin_Foreign_Country': ent_row['Previous_Foreign_Country'],

        # Destination port (empty)
        'Destination_IND': '',
        'Destination_PORT': '',
        'Destination_SCHEDK': '',
        'Destination_Name': '',
        'Destination_Country': '',
        'Destination_US_Port_USACE': '',
        'Destination_Foreign_Port': '',
        'Destination_Foreign_Country': '',

        # Cargo
        'Group': ent_row['Group'],
        'Commodity': ent_row['Commodity'],
        'Carrier_Name': ent_row['Carrier_Name'],
        'Tons': ent_row['Tons'],
        'CONTAINER': ent_row['CONTAINER'],

        # Fees
        'Fee_Base': ent_row['Fee_Base'],
        'Fee_Adj': ent_row['Fee_Adj'],
        'Fee_Class': ent_row['Fee_Class'],
        'Agency_Fee': ent_row['Agency_Fee'],
        'Agency_Fee_Adj': ent_row['Agency_Fee_Adj'],

        # Administrative
        'Count': '1',
    }

    return record

def create_clearance_only_record(clr_row):
    """Create clearance-only record (TYPEDOC=1)"""

    record = {
        # Port Call Identification
        'TYPEDOC': '1',  # Clearance only
        'Entrance_RECID': '',
        'Clearance_RECID': clr_row['RECID'],

        # Timing
        'Arrival_Date': '',
        'Clearance_Date': clr_row['Clearance_Date_Parsed'],
        'Days_in_Port': '',

        # US Port
        'PORT': clr_row['PORT'],
        'US_Port_USACE': clr_row['US_Port_USACE'],
        'Port_Consolidated': clr_row['Port_Consolidated'],
        'Port_Coast': clr_row['Port_Coast'],
        'Port_Region': clr_row['Port_Region'],
        'PWW_IND': clr_row['PWW_IND'],

        # Vessel
        'Vessel': clr_row['Vessel'],
        'IMO': clr_row['IMO'],
        'FLAG_CTRY': clr_row['FLAG_CTRY'],
        'RIG_DESC': clr_row['RIG_DESC'],
        'ICST_DESC': clr_row['ICST_DESC'],

        # Vessel tonnage
        'NRT': clr_row['NRT'],
        'GRT': clr_row['GRT'],
        'Ships_GT': clr_row['Ships_GT'],

        # Vessel dimensions
        'Ships_LOA': clr_row['Ships_LOA'],
        'Ships_Beam': clr_row['Ships_Beam'],
        'Ships_Draft': clr_row['Ships_Draft'],
        'Vessel_Dwt_Draft_ft': clr_row['Vessel_Dwt_Draft_ft'],

        # Vessel capacity
        'Ships_DWT': clr_row['Ships_DWT'],
        'Ships_Grain': clr_row['Ships_Grain'],
        'Ships_TPC': clr_row['Ships_TPC'],

        # Draft at clearance
        'DRAFT_FT': clr_row['DRAFT_FT'],
        'DRAFT_IN': clr_row['DRAFT_IN'],
        'Draft_Pct_of_Max': clr_row['Draft_Pct_of_Max'],
        'Forecasted_Activity': clr_row['Forecasted_Activity'],

        # Draft analysis
        'Arrival_Draft_Meters': '',
        'Clearance_Draft_Meters': clr_row.get('Clearance_Draft_Meters', ''),
        'Draft_Change_Meters': '',

        # Vessel type detail
        'Ships_Type': clr_row['Ships_Type'],
        'Ships_Vessel': clr_row['Ships_Vessel'],
        'Ships_Match': clr_row['Ships_Match'],
        'Vessel_Match_Method': clr_row['Vessel_Match_Method'],

        # Origin port (empty)
        'Origin_IND': '',
        'Origin_PORT': '',
        'Origin_SCHEDK': '',
        'Origin_Name': '',
        'Origin_Country': '',
        'Origin_US_Port_USACE': '',
        'Origin_Foreign_Port': '',
        'Origin_Foreign_Country': '',

        # Destination port
        'Destination_IND': clr_row['WHERE_IND'],
        'Destination_PORT': clr_row['WHERE_PORT'],
        'Destination_SCHEDK': clr_row['WHERE_SCHEDK'],
        'Destination_Name': clr_row['WHERE_NAME'],
        'Destination_Country': clr_row['WHERE_CTRY'],
        'Destination_US_Port_USACE': clr_row['Previous_US_Port_USACE'],
        'Destination_Foreign_Port': clr_row['Previous_Foreign_Port'],
        'Destination_Foreign_Country': clr_row['Previous_Foreign_Country'],

        # Cargo
        'Group': clr_row['Group'],
        'Commodity': clr_row['Commodity'],
        'Carrier_Name': clr_row['Carrier_Name'],
        'Tons': clr_row['Tons'],
        'CONTAINER': clr_row['CONTAINER'],

        # Fees (from clearance, but ideally should be from entrance)
        'Fee_Base': clr_row['Fee_Base'],
        'Fee_Adj': clr_row['Fee_Adj'],
        'Fee_Class': clr_row['Fee_Class'],
        'Agency_Fee': clr_row['Agency_Fee'],
        'Agency_Fee_Adj': clr_row['Agency_Fee_Adj'],

        # Administrative
        'Count': '1',
    }

    return record

def main():
    """Main execution"""

    # Get project root directory
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "00_DATA" / "00.02_PROCESSED"

    print("\n\n")
    print("#" * 80)
    print("# MERGE ENTRANCE + CLEARANCE -> PORT CALLS")
    print("#" * 80)
    print("\n")

    # Find most recent enriched files
    entrance_files = sorted(data_dir.glob("*entrance_enriched*.csv"), reverse=True)
    clearance_files = sorted(data_dir.glob("*clearance_enriched*.csv"), reverse=True)

    if not entrance_files:
        print("ERROR: No entrance enriched files found")
        return

    if not clearance_files:
        print("ERROR: No clearance enriched files found")
        return

    entrance_file = entrance_files[0]
    clearance_file = clearance_files[0]

    print(f"Input files:")
    print(f"  Entrance: {entrance_file.name}")
    print(f"  Clearance: {clearance_file.name}")
    print()

    # Merge
    df_complete, df_ent_only, df_clr_only = merge_port_calls(
        entrance_file,
        clearance_file,
        data_dir
    )

    print("=" * 80)
    print("PORT CALL MERGE COMPLETE")
    print("=" * 80)
    print()
    print("Output files created with v4.0.0 versioning")
    print()

if __name__ == "__main__":
    main()
