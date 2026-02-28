import pandas as pd

def compare_files(file1, file2, zone_type):
    """Compare two files and show differences"""
    print(f"\n{'='*100}")
    print(f"Comparing {zone_type} files")
    print(f"{'='*100}")

    print(f"\nFile 1: {file1}")
    print(f"File 2: {file2}")

    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    print(f"\n{'='*50}")
    print("Basic Statistics")
    print(f"{'='*50}")
    print(f"File 1: {len(df1)} rows, {df1.shape[1]} columns")
    print(f"File 2: {len(df2)} rows, {df2.shape[1]} columns")
    print(f"Difference: {abs(len(df1) - len(df2))} rows")

    # Check if columns are the same
    if list(df1.columns) != list(df2.columns):
        print(f"\n[WARNING] Columns are different!")
        print(f"File 1 columns: {list(df1.columns)}")
        print(f"File 2 columns: {list(df2.columns)}")
    else:
        print(f"\n[OK] Both files have the same columns: {list(df1.columns)}")

    # Show sample data from each
    print(f"\n{'='*50}")
    print("Sample data from File 1 (first 5 rows)")
    print(f"{'='*50}")
    print(df1.head())

    print(f"\n{'='*50}")
    print("Sample data from File 2 (first 5 rows)")
    print(f"{'='*50}")
    print(df2.head())

    # Check date ranges
    if 'Time' in df1.columns and 'Time' in df2.columns:
        df1['Time'] = pd.to_datetime(df1['Time'])
        df2['Time'] = pd.to_datetime(df2['Time'])

        print(f"\n{'='*50}")
        print("Date Ranges")
        print(f"{'='*50}")
        print(f"File 1: {df1['Time'].min()} to {df1['Time'].max()}")
        print(f"File 2: {df2['Time'].min()} to {df2['Time'].max()}")

    # Check unique zones
    if 'Zone' in df1.columns and 'Zone' in df2.columns:
        print(f"\n{'='*50}")
        print("Unique Zones")
        print(f"{'='*50}")
        print(f"File 1 zones: {df1['Zone'].dropna().unique()}")
        print(f"File 2 zones: {df2['Zone'].dropna().unique()}")

    # Check unique actions
    if 'Action' in df1.columns and 'Action' in df2.columns:
        print(f"\n{'='*50}")
        print("Unique Actions")
        print(f"{'='*50}")
        print(f"File 1 actions: {df1['Action'].dropna().unique()}")
        print(f"File 2 actions: {df2['Action'].dropna().unique()}")

    # Try to find unique records
    print(f"\n{'='*50}")
    print("Uniqueness Check")
    print(f"{'='*50}")

    # Create a composite key to compare records
    if 'IMO' in df1.columns and 'Time' in df1.columns:
        df1['key'] = df1['IMO'].astype(str) + '_' + df1['Time'].astype(str)
        df2['key'] = df2['IMO'].astype(str) + '_' + df2['Time'].astype(str)

        in_1_not_2 = set(df1['key']) - set(df2['key'])
        in_2_not_1 = set(df2['key']) - set(df1['key'])

        print(f"Records in File 1 but not File 2: {len(in_1_not_2)}")
        print(f"Records in File 2 but not File 1: {len(in_2_not_1)}")

        if len(in_1_not_2) > 0:
            print(f"\nSample records only in File 1 (first 5):")
            sample_keys = list(in_1_not_2)[:5]
            print(df1[df1['key'].isin(sample_keys)][['IMO', 'Name', 'Action', 'Time', 'Zone']])

        if len(in_2_not_1) > 0:
            print(f"\nSample records only in File 2 (first 5):")
            sample_keys = list(in_2_not_1)[:5]
            print(df2[df2['key'].isin(sample_keys)][['IMO', 'Name', 'Action', 'Time', 'Zone']])

        if len(in_1_not_2) == 0 and len(in_2_not_1) == 0:
            print("\n[INTERESTING] Both files contain the exact same records!")
            print("The size difference may be due to formatting or whitespace.")

    print(f"\n{'='*50}")
    print("RECOMMENDATION")
    print(f"{'='*50}")

    if len(df1) > len(df2):
        print(f"File 1 has MORE records ({len(df1)} vs {len(df2)})")
        print(f"SUGGESTED ACTION: Keep File 1, delete File 2")
        print(f"Keep: {file1}")
        print(f"Delete: {file2}")
    elif len(df2) > len(df1):
        print(f"File 2 has MORE records ({len(df2)} vs {len(df1)})")
        print(f"SUGGESTED ACTION: Keep File 2, delete File 1")
        print(f"Keep: {file2}")
        print(f"Delete: {file1}")
    else:
        print(f"Both files have the SAME number of records ({len(df1)})")
        print(f"Check if the records are identical or if there are any differences in content.")

if __name__ == "__main__":
    base_dir = r"G:\My Drive\LLM\project_mrtis\00_source_files"

    # Compare 2023 ANCHORAGE files
    print("\n" + "="*100)
    print("2023 ANCHORAGE COMPARISON")
    print("="*100)
    compare_files(
        f"{base_dir}\\Zone Report 01-01-23 - 12-31-23 (1).csv",
        f"{base_dir}\\Zone Report 01-01-23 - 12-31-23 (3).csv",
        "2023 ANCHORAGE"
    )

    # Compare 2025 CROSS IN files
    print("\n\n" + "="*100)
    print("2025 CROSS IN COMPARISON")
    print("="*100)
    compare_files(
        f"{base_dir}\\Zone Report 01-01-25 - 12-31-25 (2).csv",
        f"{base_dir}\\Zone Report 01-01-25 - 12-31-25 (4).csv",
        "2025 CROSS IN"
    )

    print("\n\n" + "="*100)
    print("ANALYSIS COMPLETE")
    print("="*100)
    print("\nReview the recommendations above to decide which files to keep/delete.")
