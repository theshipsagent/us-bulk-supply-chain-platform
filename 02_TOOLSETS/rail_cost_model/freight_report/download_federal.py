"""
Phase 1: Download supplemental federal reports into the data/state_rail_plans/ directory.
These get picked up by the existing process_state_rail_plans.py chunking pipeline.
"""

import json
import logging
import requests
from datetime import datetime
from pathlib import Path

from .config import FEDERAL_REPORTS, PDF_DIR, LOGS_DIR, DOWNLOAD_HEADERS

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
log = logging.getLogger(__name__)


def download_federal_reports():
    """Download federal reports. Skips gracefully on failure."""
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    results = {"total": len(FEDERAL_REPORTS), "successful": 0, "failed": 0, "skipped": 0, "details": {}}

    for report_key, info in FEDERAL_REPORTS.items():
        filename = info["filename"]
        dest = PDF_DIR / filename

        # Skip if already downloaded and valid
        if dest.exists() and dest.stat().st_size > 5000:
            with open(dest, "rb") as f:
                header = f.read(5)
            if header.startswith(b"%PDF"):
                log.info("SKIP  %-40s  (already exists, valid PDF)", filename)
                results["skipped"] += 1
                results["details"][report_key] = {"success": True, "message": "Already exists"}
                continue

        # Try each fallback URL
        downloaded = False
        for url in info.get("fallback_urls", []):
            log.info("TRY   %-40s  %s", filename, url[:70])
            try:
                resp = requests.get(url, headers=DOWNLOAD_HEADERS, timeout=60, stream=True)
                resp.raise_for_status()

                size = 0
                with open(dest, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=65536):
                        f.write(chunk)
                        size += len(chunk)

                # Validate PDF
                with open(dest, "rb") as f:
                    header = f.read(5)
                if header.startswith(b"%PDF") and size > 5000:
                    log.info("OK    %-40s  %.1f KB", filename, size / 1024)
                    results["successful"] += 1
                    results["details"][report_key] = {
                        "success": True, "url": url, "size": size,
                        "message": f"Downloaded {size / 1024:.1f} KB",
                    }
                    downloaded = True
                    break
                else:
                    log.warning("WARN  %-40s  Not a valid PDF, trying next URL", filename)
                    dest.unlink(missing_ok=True)
            except requests.exceptions.RequestException as e:
                log.warning("FAIL  %-40s  %s", filename, str(e)[:60])

        if not downloaded:
            log.warning("SKIP  %-40s  All URLs failed - not critical", filename)
            results["failed"] += 1
            results["details"][report_key] = {"success": False, "message": "All URLs failed"}

    # Save log
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOGS_DIR / f"federal_download_{ts}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    log.info("Federal downloads: %d OK, %d skipped, %d failed. Log: %s",
             results["successful"], results["skipped"], results["failed"], log_path)
    return results


if __name__ == "__main__":
    download_federal_reports()
