"""
Download state rail plan PDFs - Batch 2 (remaining states).
Verified URLs from web search 2026-02-11.
"""

import json
import requests
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
PDF_DIR = PROJECT_ROOT / "data" / "state_rail_plans"
LOGS_DIR = PROJECT_ROOT / "logs"

DOWNLOADS = {
    # Previously failed - now have working URLs
    "Minnesota": {
        "url": "https://www.dot.state.mn.us/planning/railplan/files/DraftSRPFinalReport.pdf",
        "filename": "MN_State_Rail_Plan_Draft.pdf",
    },
    "Montana": {
        "url": "https://www.mdt.mt.gov/publications/docs/brochures/railways/railplan.pdf",
        "filename": "2010_Montana_State_Rail_Plan.pdf",
    },
    # New states never attempted
    "Alaska": {
        "url": "https://dot.alaska.gov/railplan/docs/Rail-Plan-Final-draft.pdf",
        "filename": "AK_State_Rail_Plan.pdf",
    },
    "Arkansas": {
        "url": "https://ardot.gov/wp-content/uploads/2025-Arkansas-State-Rail-Plan.pdf",
        "filename": "2025_Arkansas_State_Rail_Plan.pdf",
    },
    "Arizona": {
        "url": "https://azdot.gov/sites/default/files/media/2022/10/state-rail-plan-update.pdf",
        "filename": "2022_Arizona_State_Rail_Plan_Update.pdf",
    },
    "Delaware": {
        "url": "https://deldot.gov/Publications/reports/srp/pdfs/srp_final.pdf",
        "filename": "DE_State_Rail_Plan.pdf",
    },
    "Idaho": {
        "url": "https://apps.itd.idaho.gov/apps/freight/Idaho-Statewide-Rail-Plan.pdf",
        "filename": "ID_Statewide_Rail_Plan.pdf",
    },
    "Kansas": {
        "url": "https://www.ksdot.gov/Assets/wwwksdotorg/bureaus/burRail/Rail/Documents/2022/PUBLIC_COMMENT_FINAL-DRAFT-2022_Kansas_State_Rail_Plan.pdf",
        "filename": "2022_Kansas_State_Rail_Plan.pdf",
    },
    "Kentucky": {
        "url": "https://transportation.ky.gov/MultimodalFreight/Documents/2025%20Kentucky%20Statewide%20Rail%20Plan.pdf",
        "filename": "2025_Kentucky_Statewide_Rail_Plan.pdf",
    },
    "Massachusetts": {
        "url": "https://www.mass.gov/doc/final-state-rail-plan-spring-2018/download",
        "filename": "2018_Massachusetts_State_Rail_Plan.pdf",
    },
    "Maine": {
        "url": "https://www.maine.gov/dot/sites/maine.gov.dot/files/docs/ofps/docs/railplan/MaineStateRailPlan.pdf",
        "filename": "2023_Maine_State_Rail_Plan.pdf",
    },
    "Michigan": {
        "url": "https://www.michigan.gov/mdot/-/media/Project/Websites/MDOT/Programs/Planning/Michigan-Mobility/Michigan-State-Rail-Plan-Supplement.pdf",
        "filename": "MI_State_Rail_Plan_Supplement.pdf",
    },
    "Missouri": {
        "url": "https://www.transportation.gov/sites/dot.gov/files/2023-12/MO_2022_State_Freight_and_Rail_Plan.pdf",
        "filename": "2022_Missouri_Freight_Rail_Plan.pdf",
    },
    "Mississippi": {
        "url": "https://mdot.ms.gov/documents/Planning/Plan/MS%20State%20Rail%20Plan.pdf",
        "filename": "MS_State_Rail_Plan.pdf",
    },
    "North Dakota": {
        "url": "https://www.transportation.gov/sites/dot.gov/files/2023-12/NDDOT_FinalFRP_Jan2023.pdf",
        "filename": "2023_North_Dakota_Freight_Rail_Plan.pdf",
    },
    "New Hampshire": {
        "url": "https://www.merrimacknh.gov/sites/g/files/vyhlif3456/f/file/file/final_nh_state_rail_plan.pdf",
        "filename": "2012_New_Hampshire_State_Rail_Plan.pdf",
    },
    "New Jersey": {
        "url": "https://www.nj.gov/transportation/freight/rail/pdf/finaldraftnjstaterailplan122012.pdf",
        "filename": "2012_New_Jersey_State_Rail_Plan.pdf",
    },
    "New Mexico": {
        "url": "https://api.realfile.rtsclients.com/PublicFiles/f260a66b364d453e91ff9b3fedd494dc/ddfc1f9e-5a04-470e-b25a-afc5c0bb7668/State%20Rail%20Plan%20Update.pdf",
        "filename": "2018_New_Mexico_State_Rail_Plan_Update.pdf",
    },
    "Oklahoma": {
        "url": "https://oklahoma.gov/content/dam/ok/en/odot/publications/SRP%202021%20Final%20with%20FRA%20Approval.pdf",
        "filename": "2021_Oklahoma_State_Rail_Plan.pdf",
    },
    "Rhode Island": {
        "url": "https://planning.ri.gov/sites/g/files/xkgbur826/f/documents/trans/Rail/RI_State_Rail_Plan_2014.pdf",
        "filename": "2014_Rhode_Island_State_Rail_Plan.pdf",
    },
    "South Carolina": {
        "url": "https://www.scdot.org/content/dam/scdot-legacy/travel/pdf/2024%20SC%20Statewide%20Rail%20Plan%20Update.pdf",
        "filename": "2024_South_Carolina_Rail_Plan.pdf",
    },
    "South Dakota": {
        "url": "https://dot.sd.gov/media/efaec5a4/221207_SD_SRP_Final.pdf",
        "filename": "2022_South_Dakota_State_Rail_Plan.pdf",
    },
    "Tennessee": {
        "url": "https://www.tn.gov/content/dam/tn/tdot/freight-and-logistics/TDOT_RailPlan_updated_2019.pdf",
        "filename": "2019_Tennessee_State_Rail_Plan.pdf",
    },
    "Utah": {
        "url": "https://maps.udot.utah.gov/wadocuments/Apps/Region4/Storymaps/PIN21486/Utah_State_Rail_Plan_2015.pdf",
        "filename": "2015_Utah_State_Rail_Plan.pdf",
    },
    "Vermont": {
        "url": "https://vtrans.vermont.gov/sites/aot/files/planning/documents/Vermont%20Rail%20Plan%205-20-2021%20Final.pdf",
        "filename": "2021_Vermont_Rail_Plan.pdf",
    },
    "West Virginia": {
        "url": "https://transportation.wv.gov/rail/2020WVSRP/Documents/WVSRP-2020.pdf",
        "filename": "2020_West_Virginia_State_Rail_Plan.pdf",
    },
    "Wyoming": {
        "url": "https://www.dot.state.wy.us/files/live/sites/wydot/files/shared/Planning/Railroads/Wyoming%202021%20State%20Rail%20Plan.pdf",
        "filename": "2021_Wyoming_State_Rail_Plan.pdf",
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
            resp = requests.get(url, headers=HEADERS, timeout=120, stream=True,
                                allow_redirects=True)
            resp.raise_for_status()

            size = 0
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    f.write(chunk)
                    size += len(chunk)

            size_kb = size / 1024

            with open(dest, "rb") as f:
                header = f.read(8)

            if header.startswith(b"%PDF"):
                print(f"  OK  {size_kb:,.1f} KB  (valid PDF)")
                results["successful"] += 1
                results["details"][state] = {
                    "url": url, "success": True,
                    "message": f"Downloaded {size_kb:,.1f} KB",
                    "filepath": str(dest), "is_pdf": True,
                }
            else:
                print(f"  WARN  {size_kb:,.1f} KB  (not a PDF)")
                results["failed"] += 1
                results["details"][state] = {
                    "url": url, "success": False,
                    "message": f"Downloaded {size_kb:,.1f} KB but not a valid PDF",
                    "filepath": str(dest), "is_pdf": False,
                }

        except requests.exceptions.RequestException as e:
            err = str(e)[:120]
            print(f"  FAIL  {err}")
            results["failed"] += 1
            results["details"][state] = {
                "url": url, "success": False,
                "message": err, "filepath": None, "is_pdf": False,
            }

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
