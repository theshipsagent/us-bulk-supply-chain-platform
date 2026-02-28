#!/usr/bin/env python3
"""
Rail Plans Ingestion Script

Downloads state rail plan PDFs from the state_rail_plan_manifest.json file
and saves them to the data/state_rail_plans/ directory with proper logging.

Includes 2-second delays between downloads to respect server resources.
"""

import json
import os
import time
import logging
from pathlib import Path
from datetime import datetime
import requests
from urllib.parse import urlparse

# Configure logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f"rail_plans_ingestion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Set up paths
BASE_DIR = Path(__file__).parent
MANIFEST_FILE = BASE_DIR / "state_rail_plan_manifest.json"
OUTPUT_DIR = BASE_DIR / "data" / "state_rail_plans"

# Create output directory if it doesn't exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logger.info(f"Starting rail plans ingestion process")
logger.info(f"Manifest file: {MANIFEST_FILE}")
logger.info(f"Output directory: {OUTPUT_DIR}")


def sanitize_filename(filename):
    """Remove or replace invalid filename characters."""
    invalid_chars = '<>:"|?*\\'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def get_filename_from_url(state_name, url):
    """Generate a descriptive filename for the PDF."""
    # Parse URL to get the filename
    parsed_url = urlparse(url)
    url_filename = parsed_url.path.split('/')[-1]

    # If URL filename is not a PDF, use state name
    if not url_filename.lower().endswith('.pdf'):
        url_filename = f"{state_name}_State_Rail_Plan.pdf"
    else:
        url_filename = sanitize_filename(url_filename)

    return url_filename


def download_pdf(state_name, url):
    """
    Download a PDF from the given URL.

    Args:
        state_name (str): Name of the state (for logging)
        url (str): URL of the PDF to download

    Returns:
        tuple: (success: bool, message: str, filepath: Path or None)
    """
    try:
        logger.info(f"Downloading {state_name}...")

        # Get filename
        filename = get_filename_from_url(state_name, url)
        filepath = OUTPUT_DIR / filename

        # Check if file already exists
        if filepath.exists():
            logger.warning(f"{state_name}: File already exists at {filepath}")
            return True, f"File already exists", filepath

        # Set headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # Download with timeout
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Verify content is PDF
        content_type = response.headers.get('content-type', '').lower()
        if 'pdf' not in content_type and len(response.content) > 0:
            # Still save if it has content, might be mislabeled
            logger.warning(f"{state_name}: Content-Type is {content_type}, but proceeding with download")

        # Write to file
        with open(filepath, 'wb') as f:
            f.write(response.content)

        file_size = filepath.stat().st_size / 1024  # Size in KB
        logger.info(f"SUCCESS: {state_name} - Downloaded {file_size:.1f} KB to {filename}")

        return True, f"Downloaded {file_size:.1f} KB", filepath

    except requests.exceptions.Timeout:
        msg = f"TIMEOUT: {state_name} - Request timed out after 30 seconds"
        logger.error(msg)
        return False, msg, None
    except requests.exceptions.ConnectionError as e:
        msg = f"CONNECTION ERROR: {state_name} - {str(e)}"
        logger.error(msg)
        return False, msg, None
    except requests.exceptions.HTTPError as e:
        msg = f"HTTP ERROR: {state_name} - {e.response.status_code} {e.response.reason}"
        logger.error(msg)
        return False, msg, None
    except Exception as e:
        msg = f"ERROR: {state_name} - {type(e).__name__}: {str(e)}"
        logger.error(msg)
        return False, msg, None


def main():
    """Main ingestion function."""
    try:
        # Load manifest
        with open(MANIFEST_FILE, 'r') as f:
            manifest = json.load(f)

        logger.info(f"Loaded manifest with {len(manifest)} states")

        # Track results
        results = {
            'total': len(manifest),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'details': {}
        }

        # Download each PDF
        for state_name, url in sorted(manifest.items()):
            success, message, filepath = download_pdf(state_name, url)

            results['details'][state_name] = {
                'url': url,
                'success': success,
                'message': message,
                'filepath': str(filepath) if filepath else None
            }

            if success:
                if "already exists" in message:
                    results['skipped'] += 1
                else:
                    results['successful'] += 1
            else:
                results['failed'] += 1

            # 2-second delay between downloads
            time.sleep(2)

        # Log summary
        logger.info("=" * 80)
        logger.info("INGESTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total states: {results['total']}")
        logger.info(f"Successfully downloaded: {results['successful']}")
        logger.info(f"Failed: {results['failed']}")
        logger.info(f"Skipped (already exist): {results['skipped']}")
        logger.info("=" * 80)

        # Log failed downloads
        failed_states = [state for state, detail in results['details'].items() if not detail['success']]
        if failed_states:
            logger.warning("Failed downloads:")
            for state in failed_states:
                logger.warning(f"  - {state}: {results['details'][state]['message']}")

        # Save results to JSON
        results_file = log_dir / f"ingestion_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {results_file}")

        # List downloaded files
        downloaded_files = list(OUTPUT_DIR.glob("*.pdf"))
        logger.info(f"Total files in output directory: {len(downloaded_files)}")
        logger.info("Downloaded files:")
        for pdf_file in sorted(downloaded_files):
            file_size = pdf_file.stat().st_size / 1024  # Size in KB
            logger.info(f"  - {pdf_file.name} ({file_size:.1f} KB)")

    except FileNotFoundError:
        logger.error(f"Manifest file not found: {MANIFEST_FILE}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in manifest file: {MANIFEST_FILE}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {str(e)}")
        raise


if __name__ == "__main__":
    main()
