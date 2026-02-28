#!/usr/bin/env python3
"""
Port Master Plan Downloader CLI
================================
Downloads publicly available port master plan, strategic plan, and vision plan
documents from US ports. Focused on Florida, Louisiana, inland rivers, and
major competitor ports.

Usage:
    python port_master_plans.py                  # Download all
    python port_master_plans.py --region FL       # Download Florida only
    python port_master_plans.py --region LA       # Download Louisiana only
    python port_master_plans.py --region INLAND   # Download inland river ports
    python port_master_plans.py --region OTHER    # Download other US ports
    python port_master_plans.py --list            # List all entries without downloading
    python port_master_plans.py --manifest        # Export manifest as JSON
    python port_master_plans.py --dry-run         # Show what would be downloaded

Requires: requests (pip install requests)
"""

import os
import sys
import json
import time
import argparse
import hashlib
from pathlib import Path
from datetime import datetime

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. Install with: pip install requests")
    sys.exit(1)

# ============================================================================
# PORT MASTER PLAN MANIFEST
# ============================================================================
# Each entry: {port, state, region, year, doc_type, title, url, filename, size_note}
# Curated from public records research - Feb 2026
# ============================================================================

MANIFEST = [
    # ========================================================================
    # FLORIDA
    # ========================================================================
    {
        "port": "Florida Ports Council (Statewide)",
        "state": "FL",
        "region": "FL",
        "year": 2024,
        "doc_type": "Mission Plan",
        "title": "Five-Year Florida Seaport Mission Plan 2024-2028",
        "url": "https://ftp.fdot.gov/public/file/yl_zzycenee1ltnsl84dna/2024_2028_5-Year_Florida_Seaport_Mission_Plan.pdf",
        "filename": "FL_Statewide_Seaport_Mission_Plan_2024-2028.pdf",
        "size_note": "~80 MB"
    },
    {
        "port": "Florida Ports Council (Statewide)",
        "state": "FL",
        "region": "FL",
        "year": 2023,
        "doc_type": "Mission Plan",
        "title": "Five-Year Florida Seaport Mission Plan 2023-2027",
        "url": "https://flaports.org/wp-content/uploads/Florida-Seaports-Mission-Plan-2023_FINAL-2-27_web.pdf",
        "filename": "FL_Statewide_Seaport_Mission_Plan_2023-2027.pdf",
        "size_note": "~29 MB"
    },
    {
        "port": "FDOT (Statewide)",
        "state": "FL",
        "region": "FL",
        "year": 2022,
        "doc_type": "System Plan",
        "title": "Florida Seaport and Waterways System Plan 2020 (Updated Aug 2022)",
        "url": "https://fdotwww.blob.core.windows.net/sitefinity/docs/default-source/seaport/publications/2020-seaport-waterways-system-plan/2020-florida-seaport-system-plan-update-august-2022.pdf",
        "filename": "FL_Seaport_Waterways_System_Plan_2022_Update.pdf",
        "size_note": "~4 MB"
    },
    {
        "port": "PortMiami",
        "state": "FL",
        "region": "FL",
        "year": 2020,
        "doc_type": "Master Plan",
        "title": "PortMiami 2035 Master Plan - Complete",
        "url": "https://www.miamidade.gov/portmiami/library/2035-master-plan/complete-master-plan.pdf",
        "filename": "FL_PortMiami_2035_Master_Plan_Complete.pdf",
        "size_note": "Large file"
    },
    {
        "port": "PortMiami",
        "state": "FL",
        "region": "FL",
        "year": 2020,
        "doc_type": "Master Plan",
        "title": "PortMiami 2035 Master Plan - Executive Summary",
        "url": "https://www.miamidade.gov/portmiami/library/2035-master-plan/executive-summary.pdf",
        "filename": "FL_PortMiami_2035_Master_Plan_Exec_Summary.pdf",
        "size_note": "~5 MB"
    },
    {
        "port": "Port Everglades",
        "state": "FL",
        "region": "FL",
        "year": 2024,
        "doc_type": "Master/Vision Plan",
        "title": "Port Everglades 2024 M/VP Update - Executive Summary",
        "url": "https://assets.simpleviewinc.com/simpleview/image/upload/v1/clients/porteverglades/REVISED_10_29_2025_PEV_RPT_2024_MVP_Element_5_Final_ADA_522a83aa-2321-4e2a-9b43-6b897a0be440.pdf",
        "filename": "FL_Port_Everglades_2024_MVP_Exec_Summary.pdf",
        "size_note": "~15 MB"
    },
    {
        "port": "Port Everglades",
        "state": "FL",
        "region": "FL",
        "year": 2024,
        "doc_type": "Master/Vision Plan",
        "title": "Port Everglades 2024 M/VP Update - Element 2 Market Assessment",
        "url": "https://assets.simpleviewinc.com/simpleview/image/upload/v1/clients/porteverglades/PEV_2024_MVP_Element_2_ADA_accessible_report_revised_final_5038cc0e-6620-46d9-a4e2-32787a1e386f.pdf",
        "filename": "FL_Port_Everglades_2024_MVP_Market_Assessment.pdf",
        "size_note": "~7 MB"
    },
    {
        "port": "Port Everglades",
        "state": "FL",
        "region": "FL",
        "year": 2024,
        "doc_type": "Master/Vision Plan",
        "title": "Port Everglades 2024 M/VP Update - Element 3 Plan Development",
        "url": "https://assets.simpleviewinc.com/simpleview/image/upload/v1/clients/porteverglades/PEV_RPT_2024_MVP_Element_3_FINAL_ADA_0b243576-de41-4868-bfb5-acca1f387ef5.pdf",
        "filename": "FL_Port_Everglades_2024_MVP_Plan_Development.pdf",
        "size_note": "~40 MB"
    },
    {
        "port": "Port Everglades",
        "state": "FL",
        "region": "FL",
        "year": 2020,
        "doc_type": "Master/Vision Plan",
        "title": "Port Everglades 20-Year Master/Vision Plan (2020)",
        "url": "https://assets.simpleviewinc.com/simpleview/image/upload/v1/clients/porteverglades/Port_Everglades_Master_Vision_Plan_Update_FINAL_ADA_21_10_2020_cbef0685-731f-4bcd-9fce-5e5c051bccda.pdf",
        "filename": "FL_Port_Everglades_2020_Master_Vision_Plan.pdf",
        "size_note": "~40 MB"
    },
    {
        "port": "Port Everglades",
        "state": "FL",
        "region": "FL",
        "year": 2023,
        "doc_type": "Shore Power Master Plan",
        "title": "Port Everglades Shore Power and Electrification Master Plan",
        "url": "https://assets.simpleviewinc.com/simpleview/image/upload/v1/clients/porteverglades/210699_07_PortEverglades_Shore_Power_Study_FINAL_c0e9d563-eede-4b00-9b47-22f9da909e74.pdf",
        "filename": "FL_Port_Everglades_Shore_Power_Master_Plan_2023.pdf",
        "size_note": "~5 MB"
    },
    {
        "port": "SeaPort Manatee",
        "state": "FL",
        "region": "FL",
        "year": 2022,
        "doc_type": "Master Plan",
        "title": "SeaPort Manatee Master Plan Update 2022 (Draft)",
        "url": "https://www.seaportmanatee.com/wp-content/uploads/2023/02/SeaPort-Manatee-DRAFT-2023-02-09-Master-Plan-Update-202263.pdf",
        "filename": "FL_SeaPort_Manatee_Master_Plan_Update_2022.pdf",
        "size_note": "~20 MB"
    },
    {
        "port": "Port Tampa Bay",
        "state": "FL",
        "region": "FL",
        "year": 2016,
        "doc_type": "Master Plan",
        "title": "Port Tampa Bay Vision 2030 Master Plan Executive Summary",
        "url": "https://www.porttb.com/PortTB/media/Port-Tampa-Bay/Information-Center/Port-Department/Planning%20and%20Development/Port-Tampa-Bay-Master-Plan-Vision-2030-Executive-Summary.pdf",
        "filename": "FL_Port_Tampa_Bay_Vision_2030_Exec_Summary.pdf",
        "size_note": "~30 MB"
    },
    {
        "port": "Port Canaveral",
        "state": "FL",
        "region": "FL",
        "year": 2020,
        "doc_type": "Vision Plan",
        "title": "Port Canaveral 30-Year Strategic Vision Plan",
        "url": "https://www.portcanaveral.com/PortCanaveral/media/Recreation/JPC/PORT-CANAVERAL-30-YEAR-VISION-PLAN_1.pdf",
        "filename": "FL_Port_Canaveral_30_Year_Vision_Plan.pdf",
        "size_note": "~10 MB"
    },
    {
        "port": "Port of Palm Beach",
        "state": "FL",
        "region": "FL",
        "year": 2023,
        "doc_type": "Master Plan",
        "title": "Port of Palm Beach Master Plan (2023 Update - Staff Report)",
        "url": "https://discover.pbcgov.org/pzb/planning/PCPDF/2024/April/III-B-1-Port-Palm-Beach-MP-PLC-rpt.pdf",
        "filename": "FL_Port_Palm_Beach_Master_Plan_2023_Staff_Report.pdf",
        "size_note": "~2 MB"
    },

    # ========================================================================
    # LOUISIANA
    # ========================================================================
    {
        "port": "Port of New Orleans (Port NOLA)",
        "state": "LA",
        "region": "LA",
        "year": 2018,
        "doc_type": "Strategic Master Plan",
        "title": "Port NOLA Forward - Strategic Master Plan",
        "url": "https://portnola.com/assets/pdf/Port-NOLA-Forward-Strategic-Master-Plan.pdf",
        "filename": "LA_Port_NOLA_Forward_Strategic_Master_Plan_2018.pdf",
        "size_note": "~15 MB"
    },
    {
        "port": "Port of New Orleans (Port NOLA)",
        "state": "LA",
        "region": "LA",
        "year": 2020,
        "doc_type": "Revitalization Plan",
        "title": "Port NOLA Inner Harbor Economic Revitalization Plan (PIER Plan)",
        "url": "https://portnola.com/assets/pdf/PIER-Plan-Document.pdf",
        "filename": "LA_Port_NOLA_PIER_Plan_2020.pdf",
        "size_note": "~10 MB"
    },
    {
        "port": "Port of New Orleans (Port NOLA)",
        "state": "LA",
        "region": "LA",
        "year": 2022,
        "doc_type": "Environmental Report",
        "title": "Port NOLA Green Supply Chain Report 2022",
        "url": "https://portnola.com/assets/img/Port-NOLAs-Green-Supply-Chain-Report-July-2022.pdf",
        "filename": "LA_Port_NOLA_Green_Supply_Chain_Report_2022.pdf",
        "size_note": "~5 MB"
    },
    {
        "port": "Louisiana Gateway Port (Plaquemines)",
        "state": "LA",
        "region": "LA",
        "year": 2024,
        "doc_type": "Master Plan",
        "title": "Louisiana Gateway Port Master Plan 2024 (30-Year Roadmap)",
        "url": "https://louisianagatewayport.com/wp-content/uploads/2025/02/Master_Plan_2024_Louisiana_Gateway_Plaquemines_Port.pdf",
        "filename": "LA_Plaquemines_Gateway_Port_Master_Plan_2024.pdf",
        "size_note": "~20 MB"
    },
    {
        "port": "Louisiana Legislative Auditor",
        "state": "LA",
        "region": "LA",
        "year": 2024,
        "doc_type": "Audit/Comparison",
        "title": "Louisiana Public Ports System Comparison to Southern Coastal States",
        "url": "https://dotd.la.gov/media/cy1gyp2o/2024-lla-louisianas-public-port-system.pdf",
        "filename": "LA_Public_Ports_System_Comparison_2024.pdf",
        "size_note": "~5 MB"
    },
    {
        "port": "Louisiana DOTD (Statewide)",
        "state": "LA",
        "region": "LA",
        "year": 2025,
        "doc_type": "Status Report",
        "title": "LA Port Construction & Development Priority Program Annual Report 2025",
        "url": "https://dotd.la.gov/media/il4mbcha/port-annual-report-2025-final.pdf",
        "filename": "LA_Port_Construction_Development_Annual_Report_2025.pdf",
        "size_note": "~5 MB"
    },
    {
        "port": "Louisiana CPRA (Statewide)",
        "state": "LA",
        "region": "LA",
        "year": 2023,
        "doc_type": "Coastal Master Plan",
        "title": "Louisiana Comprehensive Master Plan for a Sustainable Coast (4th Ed) - Exec Summary",
        "url": "https://coastal.la.gov/wp-content/uploads/2023/05/230418_CPRA_Executive-Summary_final.pdf",
        "filename": "LA_Coastal_Master_Plan_2023_Exec_Summary.pdf",
        "size_note": "~10 MB"
    },

    # ========================================================================
    # INLAND RIVERS / MISSISSIPPI SYSTEM
    # ========================================================================
    {
        "port": "USACE St. Louis District",
        "state": "IL/MO",
        "region": "INLAND",
        "year": 2025,
        "doc_type": "Master Plan",
        "title": "Rivers Project Master Plan Update (Mississippi/Illinois Rivers) - Public Review Draft",
        "url": "https://www.mvs.usace.army.mil/Portals/54/docs/recreation/rivers/MasterPlan/2024%20RPO%20Master%20Plan/Rivers%20Project%20MP%20Update%20-%20Public%20Review%20Draft%20Jan%202025.pdf",
        "filename": "INLAND_USACE_Rivers_Project_Master_Plan_2025_Draft.pdf",
        "size_note": "~20 MB"
    },
    {
        "port": "USACE Upper Mississippi River",
        "state": "MN/WI/IA/IL",
        "region": "INLAND",
        "year": 2022,
        "doc_type": "Master Plan",
        "title": "Upper Mississippi River Master Plan for Resource Management",
        "url": "https://www.mvp.usace.army.mil/Portals/57/UMRProject_MasterPlan_Main_Report_Final_01April2022.pdf",
        "filename": "INLAND_Upper_Mississippi_River_Master_Plan_2022.pdf",
        "size_note": "~15 MB"
    },
    {
        "port": "Havana Regional Port District",
        "state": "IL",
        "region": "INLAND",
        "year": 2023,
        "doc_type": "Master Plan",
        "title": "Havana Regional Port District Master Plan Study",
        "url": "https://idot.illinois.gov/content/dam/soi/en/web/idot/documents/transportation-system/reports/marine-studies/2023-havana-port-master-plan.pdf",
        "filename": "INLAND_IL_Havana_Port_Master_Plan_2023.pdf",
        "size_note": "~5 MB"
    },
    {
        "port": "Americas Central Port (Granite City)",
        "state": "IL",
        "region": "INLAND",
        "year": 2021,
        "doc_type": "Strategic Plan",
        "title": "Illinois Marine Transportation System Studies (Portal Page)",
        "url": "https://idot.illinois.gov/transportation-system/transportation-management/planning/marine-transportation/statewide-and-local-marine-planning-studies.html",
        "filename": "INLAND_IL_Marine_Studies_Portal.html",
        "size_note": "Portal page - follow links"
    },

    # ========================================================================
    # OTHER US PORTS (Major Competitors)
    # ========================================================================
    {
        "port": "Port Houston",
        "state": "TX",
        "region": "OTHER",
        "year": 2025,
        "doc_type": "Strategic Plan",
        "title": "Port Houston Strategic Plan 2025 Update",
        "url": "https://porthouston.com/wp-content/uploads/2024/11/Strategic_Plan_2025Update_Final_2024.10.28.pdf",
        "filename": "TX_Port_Houston_Strategic_Plan_2025_Update.pdf",
        "size_note": "~10 MB"
    },
    {
        "port": "Port Houston",
        "state": "TX",
        "region": "OTHER",
        "year": 2020,
        "doc_type": "Strategic Plan",
        "title": "Port Houston Strategic Plan 2020",
        "url": "https://www.porthouston.com/wp-content/uploads/2023/01/2020-STRATEGIC-PLAN-FINAL.pdf",
        "filename": "TX_Port_Houston_Strategic_Plan_2020.pdf",
        "size_note": "~10 MB"
    },
    {
        "port": "Port Houston",
        "state": "TX",
        "region": "OTHER",
        "year": 2022,
        "doc_type": "2040 Plan",
        "title": "Port Houston 2040 Plan",
        "url": "https://www.porthouston.com/wp-content/uploads/2022/11/Port-Houston-2040-Plan.pdf",
        "filename": "TX_Port_Houston_2040_Plan.pdf",
        "size_note": "~15 MB"
    },
    {
        "port": "Port of San Diego",
        "state": "CA",
        "region": "OTHER",
        "year": 2024,
        "doc_type": "Master Plan Update",
        "title": "Port of San Diego Master Plan Update (Final Draft PMPU 2024)",
        "url": "https://pantheonstorage.blob.core.windows.net/waterfront-development/Port-Master-Plan.pdf",
        "filename": "CA_Port_San_Diego_Master_Plan_2024.pdf",
        "size_note": "Large file"
    },
]

# ============================================================================
# DOWNLOAD ENGINE
# ============================================================================

HEADERS = {
    "User-Agent": "PortMasterPlanResearchTool/1.0 (Academic/Consulting Research)"
}

def sanitize_filename(name):
    """Remove/replace characters that are problematic in filenames."""
    for ch in ['<', '>', ':', '"', '|', '?', '*']:
        name = name.replace(ch, '_')
    return name

def download_file(url, dest_path, timeout=120, max_retries=3):
    """Download a file with progress reporting and retry logic."""
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, stream=True, timeout=timeout, allow_redirects=True)
            resp.raise_for_status()

            total = int(resp.headers.get('content-length', 0))
            downloaded = 0

            with open(dest_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = (downloaded / total) * 100
                            bar_len = 30
                            filled = int(bar_len * downloaded / total)
                            bar = '█' * filled + '░' * (bar_len - filled)
                            size_mb = downloaded / (1024 * 1024)
                            total_mb = total / (1024 * 1024)
                            print(f"\r    [{bar}] {pct:5.1f}% ({size_mb:.1f}/{total_mb:.1f} MB)", end='', flush=True)

            if total > 0:
                print()  # newline after progress bar
            else:
                size_mb = os.path.getsize(dest_path) / (1024 * 1024)
                print(f"    Downloaded {size_mb:.1f} MB (no content-length header)")

            return True

        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                wait = attempt * 5
                print(f"\n    ⚠ Attempt {attempt} failed: {e}")
                print(f"    Retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"\n    ✗ FAILED after {max_retries} attempts: {e}")
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                return False

    return False

def get_region_dir(region, base_dir):
    """Map region codes to folder names."""
    region_map = {
        "FL": "01_Florida",
        "LA": "02_Louisiana",
        "INLAND": "03_Inland_Rivers",
        "OTHER": "04_Other_US_Ports"
    }
    return os.path.join(base_dir, region_map.get(region, "99_Uncategorized"))

# ============================================================================
# CLI COMMANDS
# ============================================================================

def list_manifest(region_filter=None):
    """Print the manifest as a formatted table."""
    filtered = MANIFEST if not region_filter else [e for e in MANIFEST if e["region"] == region_filter]

    print(f"\n{'='*100}")
    print(f" PORT MASTER PLAN MANIFEST — {len(filtered)} documents")
    print(f"{'='*100}")

    current_region = None
    for i, entry in enumerate(filtered, 1):
        if entry["region"] != current_region:
            current_region = entry["region"]
            region_names = {"FL": "FLORIDA", "LA": "LOUISIANA", "INLAND": "INLAND RIVERS", "OTHER": "OTHER US PORTS"}
            print(f"\n  ── {region_names.get(current_region, current_region)} {'─'*60}")

        print(f"  {i:3d}. [{entry['year']}] {entry['port']}")
        print(f"       {entry['title']}")
        print(f"       Type: {entry['doc_type']}  |  Size: {entry['size_note']}")
        print(f"       URL: {entry['url'][:90]}...")
        print()

    print(f"{'='*100}")
    print(f" Total: {len(filtered)} documents across {len(set(e['region'] for e in filtered))} regions")
    print(f"{'='*100}\n")


def export_manifest_json(output_path="port_master_plans_manifest.json"):
    """Export the manifest as a JSON file."""
    data = {
        "generated": datetime.now().isoformat(),
        "description": "Port Master Plan URLs - US Ports (FL, LA, Inland Rivers, Other)",
        "total_documents": len(MANIFEST),
        "documents": MANIFEST
    }
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✓ Manifest exported to: {output_path}")
    return output_path


def download_all(base_dir="port_master_plans", region_filter=None, dry_run=False, skip_large=False):
    """Download all documents in the manifest."""
    filtered = MANIFEST if not region_filter else [e for e in MANIFEST if e["region"] == region_filter]

    if not filtered:
        print(f"No documents found for region filter: {region_filter}")
        return

    print(f"\n{'='*80}")
    print(f" PORT MASTER PLAN DOWNLOADER")
    print(f" Target: {base_dir}/")
    print(f" Documents: {len(filtered)}")
    if region_filter:
        print(f" Region filter: {region_filter}")
    if dry_run:
        print(f" MODE: DRY RUN (no downloads)")
    print(f"{'='*80}\n")

    # Create directory structure
    if not dry_run:
        for region in set(e["region"] for e in filtered):
            region_dir = get_region_dir(region, base_dir)
            os.makedirs(region_dir, exist_ok=True)

    success = 0
    failed = 0
    skipped = 0

    for i, entry in enumerate(filtered, 1):
        region_dir = get_region_dir(entry["region"], base_dir)
        filename = sanitize_filename(entry["filename"])
        dest_path = os.path.join(region_dir, filename)

        print(f"[{i}/{len(filtered)}] {entry['port']} ({entry['year']})")
        print(f"  → {entry['title']}")
        print(f"  → {dest_path}")

        if dry_run:
            print(f"  → [DRY RUN] Would download from: {entry['url'][:80]}...")
            print()
            continue

        # Skip if already downloaded
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
            size_mb = os.path.getsize(dest_path) / (1024 * 1024)
            print(f"  → Already exists ({size_mb:.1f} MB) — SKIPPING")
            skipped += 1
            print()
            continue

        # Skip HTML portal pages
        if entry["url"].endswith(".html"):
            print(f"  → Portal/HTML page — saving URL reference only")
            with open(dest_path.replace('.html', '_URL.txt'), 'w') as f:
                f.write(f"Portal: {entry['title']}\nURL: {entry['url']}\nAccessed: {datetime.now().isoformat()}\n")
            success += 1
            print()
            continue

        # Download
        result = download_file(entry["url"], dest_path)
        if result:
            success += 1
            print(f"  ✓ SUCCESS")
        else:
            failed += 1
            # Write a stub with the URL so user can manually download
            stub_path = dest_path.replace('.pdf', '_FAILED_URL.txt')
            with open(stub_path, 'w') as f:
                f.write(f"DOWNLOAD FAILED\n{'='*40}\n")
                f.write(f"Title: {entry['title']}\n")
                f.write(f"URL: {entry['url']}\n")
                f.write(f"Date: {datetime.now().isoformat()}\n")
                f.write(f"\nManually download from the URL above.\n")

        print()
        time.sleep(1)  # Be respectful

    # Summary
    print(f"\n{'='*80}")
    print(f" DOWNLOAD SUMMARY")
    print(f"{'='*80}")
    print(f"  ✓ Downloaded: {success}")
    print(f"  ⊘ Skipped (existing): {skipped}")
    print(f"  ✗ Failed: {failed}")
    print(f"  Total: {len(filtered)}")
    print(f"\n  Files saved to: {os.path.abspath(base_dir)}/")

    if failed > 0:
        print(f"\n  NOTE: {failed} downloads failed. Check *_FAILED_URL.txt files")
        print(f"  for manual download links.")

    print(f"{'='*80}\n")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Port Master Plan Downloader - Downloads publicly available port planning documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Regions:
  FL      Florida ports
  LA      Louisiana ports  
  INLAND  Inland river ports (Mississippi/Ohio/Illinois)
  OTHER   Other US ports (Houston, San Diego, etc.)

Examples:
  python port_master_plans.py                     # Download everything
  python port_master_plans.py --region FL         # Florida only
  python port_master_plans.py --region LA         # Louisiana only
  python port_master_plans.py --list              # Show all entries
  python port_master_plans.py --list --region FL  # Show Florida entries
  python port_master_plans.py --manifest          # Export JSON manifest
  python port_master_plans.py --dry-run           # Preview without downloading
  python port_master_plans.py -o ~/Documents/ports  # Custom output directory
        """
    )

    parser.add_argument("--region", "-r", choices=["FL", "LA", "INLAND", "OTHER"],
                        help="Filter by region")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List all manifest entries without downloading")
    parser.add_argument("--manifest", "-m", action="store_true",
                        help="Export manifest as JSON file")
    parser.add_argument("--dry-run", "-d", action="store_true",
                        help="Show what would be downloaded without actually downloading")
    parser.add_argument("--output", "-o", default="port_master_plans",
                        help="Output directory (default: ./port_master_plans)")

    args = parser.parse_args()

    if args.list:
        list_manifest(args.region)
    elif args.manifest:
        path = export_manifest_json(os.path.join(args.output, "manifest.json") 
                                     if args.output != "port_master_plans" 
                                     else "port_master_plans_manifest.json")
    else:
        download_all(
            base_dir=args.output,
            region_filter=args.region,
            dry_run=args.dry_run
        )


if __name__ == "__main__":
    main()
