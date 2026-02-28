import pandas as pd
import os
from pathlib import Path
from collections import defaultdict
import hashlib

def identify_zone(file_path):
    """Identify the zone type based on file contents"""
    try:
        df = pd.read_csv(file_path)

        if 'Zone' not in df.columns or 'Action' not in df.columns:
            return "UNKNOWN - Missing columns"

        # Get unique zones and actions
        zones = df['Zone'].dropna().unique()
        actions = df['Action'].dropna().unique()

        # Check for SWP Cross first (CROSS IN/OUT)
        if any('SWP Cross' in str(z) for z in zones):
            if 'Enter' in actions and 'Exit' not in actions:
                return "CROSS IN"
            elif 'Exit' in actions and 'Enter' not in actions:
                return "CROSS OUT"
            else:
                return "CROSS (Mixed Enter/Exit)"

        # Now check if it's ANCHORAGE vs TERMINAL
        # Both have Arrive/Depart, but ANCHORAGE has "Anch" in zone names
        # TERMINAL has "Buoys" or dock/terminal names

        # Count how many zones contain "Anch"
        anch_count = sum(1 for z in zones if 'Anch' in str(z))
        buoys_count = sum(1 for z in zones if 'Buoys' in str(z))

        # If most/all zones contain "Anch", it's ANCHORAGE
        if anch_count > 0 and anch_count >= len(zones) * 0.8:  # 80%+ contain "Anch"
            return "ANCHORAGE"
        # If zones contain "Buoys", it's TERMINAL
        elif buoys_count > 0:
            return "TERMINAL"
        # If has Arrive/Depart but no "Anch" in most zones, likely TERMINAL
        elif ('Arrive' in actions or 'Depart' in actions) and anch_count < len(zones) * 0.5:
            return "TERMINAL"
        else:
            return f"UNKNOWN - Zones: {list(zones[:5])}, Actions: {list(actions)}"
    except Exception as e:
        return f"ERROR: {str(e)}"

def get_file_hash(file_path):
    """Get MD5 hash of file to detect exact duplicates"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def analyze_source_files(source_dir):
    """Analyze all zone report files"""
    files = sorted(Path(source_dir).glob("Zone Report *.csv"))

    # Group files by year
    files_by_year = defaultdict(list)

    print("=" * 100)
    print("ZONE REPORT FILE ANALYSIS")
    print("=" * 100)
    print()

    for file_path in files:
        file_name = file_path.name
        file_size = file_path.stat().st_size

        # Extract year from filename (format: "Zone Report MM-DD-YY - MM-DD-YY.csv" or with " (N)")
        import re
        match = re.search(r'(\d{2})-(\d{2})-(\d{2})(?:\s*\(\d+\))?\.csv', file_name)
        if match:
            year = f"20{match.group(3)}"
        else:
            year = "UNKNOWN"

        # Identify zone
        zone_type = identify_zone(file_path)

        # Get file hash for duplicate detection
        file_hash = get_file_hash(file_path)

        files_by_year[year].append({
            'filename': file_name,
            'zone': zone_type,
            'size': file_size,
            'hash': file_hash,
            'path': str(file_path)
        })

    # Print analysis by year
    for year in sorted(files_by_year.keys()):
        print(f"\n{'='*100}")
        print(f"YEAR: {year}")
        print(f"{'='*100}")

        year_files = files_by_year[year]
        print(f"Total files: {len(year_files)}")
        print()

        # Count zones
        zone_counts = defaultdict(int)
        for f in year_files:
            zone_counts[f['zone']] += 1

        print("Zone distribution:")
        for zone, count in sorted(zone_counts.items()):
            status = "[OK]" if count == 1 else f"[WARNING] DUPLICATE ({count} files)"
            print(f"  {zone:20s}: {count} file(s) {status}")

        print("\nFile details:")
        print(f"{'Filename':<50s} {'Zone':<20s} {'Size':>10s}")
        print("-" * 100)

        for f in sorted(year_files, key=lambda x: x['zone']):
            size_kb = f['size'] / 1024
            print(f"{f['filename']:<50s} {f['zone']:<20s} {size_kb:>9.1f}K")

        # Check for exact duplicate files (same hash)
        hashes = defaultdict(list)
        for f in year_files:
            hashes[f['hash']].append(f['filename'])

        duplicates = {h: files for h, files in hashes.items() if len(files) > 1}
        if duplicates:
            print(f"\n[WARNING] EXACT DUPLICATE FILES DETECTED (same content):")
            for hash_val, dup_files in duplicates.items():
                print(f"  Hash: {hash_val[:12]}...")
                for dup_file in dup_files:
                    print(f"    - {dup_file}")

    # Summary
    print(f"\n\n{'='*100}")
    print("SUMMARY")
    print(f"{'='*100}")

    issues = []
    for year in sorted(files_by_year.keys()):
        year_files = files_by_year[year]
        zone_counts = defaultdict(int)
        for f in year_files:
            zone_counts[f['zone']] += 1

        expected_zones = {"ANCHORAGE", "CROSS IN", "CROSS OUT", "TERMINAL"}
        actual_zones = set(zone_counts.keys())

        if len(year_files) != 4:
            issues.append(f"  {year}: Has {len(year_files)} files (expected 4)")

        if actual_zones != expected_zones:
            missing = expected_zones - actual_zones
            extra = actual_zones - expected_zones
            if missing:
                issues.append(f"  {year}: Missing zones: {missing}")
            if extra:
                issues.append(f"  {year}: Unexpected zones: {extra}")

        for zone, count in zone_counts.items():
            if count > 1:
                issues.append(f"  {year}: Duplicate {zone} ({count} files)")

    if issues:
        print("\n[WARNING] ISSUES FOUND:")
        for issue in issues:
            print(issue)
    else:
        print("\n[OK] All years have exactly 4 unique zone files!")

    print(f"\n{'='*100}\n")

if __name__ == "__main__":
    source_dir = r"G:\My Drive\LLM\project_mrtis\00_source_files"
    analyze_source_files(source_dir)
