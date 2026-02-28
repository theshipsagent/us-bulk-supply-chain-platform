"""
Download state rail plan PDFs from verified working URLs.
Overwrites any existing HTML-error-page files from the first ingestion attempt.
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import unquote

PROJECT_ROOT = Path(__file__).parent
PDF_DIR = PROJECT_ROOT / "data" / "state_rail_plans"
LOGS_DIR = PROJECT_ROOT / "logs"

# Verified working URLs (searched 2026-02-11)
DOWNLOADS = {
    "Alabama": {
        "url": "https://www.dot.state.al.us/publications/Design/pdf/Rail/RailPlan.pdf",
        "filename": "Alabama_State_Rail_Plan.pdf",
    },
    "California": {
        "url": "https://dot.ca.gov/-/media/dot-media/programs/rail-mass-transportation/documents/california-state-rail-plan/2024-ca-state-rail-plan-a11y.pdf",
        "filename": "2024_California_State_Rail_Plan.pdf",
    },
    "Colorado": {
        "url": "https://www.codot.gov/programs/transitandrail/assets/state-freight-and-passenger-rail-plan_final_5-1-2024.pdf",
        "filename": "2024_Colorado_Freight_Passenger_Rail_Plan.pdf",
    },
    "Connecticut": {
        "url": "https://portal.ct.gov/-/media/DOT/documents/dplansprojectsstudies/plans/State_Rail_Plan/CTStateRailPlan2022-2026.pdf",
        "filename": "CT_State_Rail_Plan_2022-2026.pdf",
    },
    "Florida": {
        "url": "https://fdotwww.blob.core.windows.net/sitefinity/docs/default-source/rail/plans/rail/rail-system-plan-2023/rsp-october-version/fdot_rsp_ch-1_ada-(nov).pdf?sfvrsn=606135b_4",
        "filename": "2023_Florida_Rail_System_Plan_ExecSummary.pdf",
    },
    "Georgia": {
        "url": "https://www.dot.ga.gov/InvestSmart/Rail/StateRailPlan/Georgia%20SRP%20Final%20Draft.pdf",
        "filename": "2021_Georgia_State_Rail_Plan.pdf",
    },
    "Illinois": {
        "url": "https://idot.illinois.gov/content/dam/soi/en/web/idot/documents/transportation-system/fact-sheets/2023%20Illinois%20State%20Rail%20Plan%20Main%20Document.pdf",
        "filename": "2023_Illinois_State_Rail_Plan.pdf",
    },
    "Indiana": {
        "url": "https://www.in.gov/indot/files/INDOT_SRP_Combined_FINAL_Nov-2021-INDOT-website.pdf",
        "filename": "2021_Indiana_State_Rail_Plan.pdf",
    },
    "Iowa": {
        "url": "https://publications.iowa.gov/43128/1/IowaSRP2022.pdf",
        "filename": "2022_Iowa_State_Rail_Plan.pdf",
    },
    "Maryland": {
        "url": "https://www.mdot.maryland.gov/OPCP/MD_State_Rail_Plan.pdf",
        "filename": "Maryland_State_Rail_Plan_v2.pdf",
    },
    "North Carolina": {
        "url": "https://www.ncdot.gov/divisions/rail/Documents/state-rail-plan-executive-summary-2025.pdf",
        "filename": "2025_North_Carolina_Rail_Plan_ExecSummary.pdf",
    },
    "Ohio": {
        "url": "https://dam.assets.ohio.gov/image/upload/rail.ohio.gov/publications/rail-plan/2025DraftRailPlan.pdf",
        "filename": "2025_Ohio_Draft_Rail_Plan.pdf",
    },
    "Pennsylvania": {
        "url": "https://www.penndot.pa.gov/Doing-Business/RailFreightAndPorts/Planning/Documents/2020%20Pennsylvania%20State%20Rail%20Plan/2020%20Pennsylvania%20State%20Rail%20Plan.pdf",
        "filename": "2020_Pennsylvania_State_Rail_Plan.pdf",
    },
    "Washington": {
        "url": "https://wsdot.wa.gov/sites/default/files/2021-10/2019-2040-State-Rail-Plan.pdf",
        "filename": "2019_Washington_State_Rail_Plan.pdf",
    },
    "Wisconsin": {
        "url": "https://www.railwayage.com/wp-content/uploads/2023/02/Wisconsin-Rail-Plan-2050-Draft-January-2023.pdf",
        "filename": "2023_Wisconsin_Rail_Plan_2050_Draft.pdf",
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/pdf,*/*",
}


def download_all():
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    results = {"total": len(DOWNLOADS), "successful": 0, "failed": 0, "details": {}}

    for state, info in DOWNLOADS.items():
        url = info["url"]
        filename = info["filename"]
        dest = PDF_DIR / filename

        print(f"\n{'-'*60}")
        print(f"  {state}")
        print(f"  {url[:80]}...")

        try:
            resp = requests.get(url, headers=HEADERS, timeout=60, stream=True)
            resp.raise_for_status()

            content_type = resp.headers.get("Content-Type", "")
            size = 0
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    f.write(chunk)
                    size += len(chunk)

            size_kb = size / 1024

            # Quick validation: check PDF magic bytes
            with open(dest, "rb") as f:
                header = f.read(8)

            if header.startswith(b"%PDF"):
                print(f"  OK  {size_kb:,.1f} KB  (valid PDF)")
                results["successful"] += 1
                results["details"][state] = {
                    "url": url,
                    "success": True,
                    "message": f"Downloaded {size_kb:,.1f} KB",
                    "filepath": str(dest),
                    "is_pdf": True,
                }
            else:
                print(f"  WARN  {size_kb:,.1f} KB  (not a PDF — likely HTML redirect)")
                results["failed"] += 1
                results["details"][state] = {
                    "url": url,
                    "success": False,
                    "message": f"Downloaded {size_kb:,.1f} KB but not a valid PDF",
                    "filepath": str(dest),
                    "is_pdf": False,
                }

        except requests.exceptions.RequestException as e:
            print(f"  FAIL  {e}")
            results["failed"] += 1
            results["details"][state] = {
                "url": url,
                "success": False,
                "message": str(e),
                "filepath": None,
                "is_pdf": False,
            }

    # Save log
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOGS_DIR / f"ingestion_results_{ts}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  DONE: {results['successful']} successful, {results['failed']} failed")
    print(f"  Log: {log_path}")
    print("=" * 60)


if __name__ == "__main__":
    download_all()
