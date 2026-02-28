"""Download module for EPA FRS data sources."""

import logging
import os
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin
import zipfile

import requests
import yaml
from tqdm import tqdm

logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Load configuration from settings.yaml."""
    config_path = Path("config/settings.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def ensure_dir(directory: str) -> Path:
    """Ensure directory exists, create if not."""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def download_file(url: str, dest_path: Path, chunk_size: int = 8192) -> bool:
    """
    Download a file with progress bar.

    Args:
        url: URL to download from
        dest_path: Destination file path
        chunk_size: Download chunk size in bytes

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Downloading from {url}")
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        # Get file size if available
        total_size = int(response.headers.get('content-length', 0))

        # Download with progress bar
        with open(dest_path, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True,
                     desc=dest_path.name) as pbar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

        logger.info(f"Downloaded to {dest_path}")
        return True

    except Exception as e:
        logger.error(f"Download failed: {e}")
        if dest_path.exists():
            dest_path.unlink()
        return False


def extract_zip(zip_path: Path, extract_dir: Path) -> bool:
    """
    Extract a ZIP file with progress.

    Args:
        zip_path: Path to ZIP file
        extract_dir: Directory to extract to

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Extracting {zip_path.name}")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            members = zip_ref.namelist()

            with tqdm(total=len(members), desc="Extracting") as pbar:
                for member in members:
                    zip_ref.extract(member, extract_dir)
                    pbar.update(1)

        logger.info(f"Extracted to {extract_dir}")
        return True

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return False


def download_echo_files(force: bool = False) -> bool:
    """
    Download ECHO FRS ZIP file and extract.

    Args:
        force: Force re-download even if file exists

    Returns:
        True if download and extraction successful
    """
    config = load_config()
    raw_dir = ensure_dir(config['data']['raw_dir'])

    # ECHO provides a single ZIP file
    zip_url = "https://echo.epa.gov/files/echodownloads/frs_downloads.zip"
    zip_filename = "frs_downloads.zip"
    zip_path = raw_dir / zip_filename

    # Skip download if exists and not forcing
    if zip_path.exists() and not force:
        logger.info(f"ZIP exists, skipping download: {zip_filename}")
    else:
        if not download_file(zip_url, zip_path):
            return False

    # Extract ZIP to raw directory
    return extract_zip(zip_path, raw_dir)


def download_national_combined(force: bool = False) -> bool:
    """
    Download EPA FRS National Combined ZIP file.

    Args:
        force: Force re-download even if file exists

    Returns:
        True if download and extraction successful
    """
    config = load_config()
    raw_dir = ensure_dir(config['data']['raw_dir'])
    national_config = config['data_sources']['national']

    zip_filename = "NATIONAL_COMBINED.zip"
    zip_path = raw_dir / zip_filename

    # Skip download if exists and not forcing
    if zip_path.exists() and not force:
        logger.info(f"ZIP exists, skipping download: {zip_filename}")
    else:
        url = national_config['direct_url']
        if not download_file(url, zip_path):
            return False

    # Extract ZIP
    extract_dir = raw_dir / "national"
    ensure_dir(extract_dir)

    return extract_zip(zip_path, extract_dir)


def download_state_csv(state_abbr: str, force: bool = False) -> bool:
    """
    Download individual state CSV ZIP file.

    Args:
        state_abbr: Two-letter state abbreviation (e.g., 'VA')
        force: Force re-download even if file exists

    Returns:
        True if download and extraction successful
    """
    config = load_config()
    raw_dir = ensure_dir(config['data']['raw_dir'])

    # State files typically follow pattern: STATE_{ABBR}_COMBINED.zip
    # Note: Actual URL pattern may need adjustment based on EPA's structure
    state_upper = state_abbr.upper()
    zip_filename = f"STATE_{state_upper}_COMBINED.zip"
    zip_path = raw_dir / zip_filename

    # This URL is a placeholder - actual EPA state download URLs need verification
    base_url = "https://ofmpub.epa.gov/frs_public2"
    url = f"{base_url}/{zip_filename}"

    # Skip download if exists and not forcing
    if zip_path.exists() and not force:
        logger.info(f"ZIP exists, skipping download: {zip_filename}")
    else:
        if not download_file(url, zip_path):
            return False

    # Extract ZIP
    extract_dir = raw_dir / f"state_{state_upper.lower()}"
    ensure_dir(extract_dir)

    return extract_zip(zip_path, extract_dir)


def fetch_from_api(
    state_abbr: Optional[str] = None,
    city_name: Optional[str] = None,
    facility_name: Optional[str] = None,
    pgm_sys_acrnm: Optional[str] = None,
    output_format: str = "JSON"
) -> dict:
    """
    Fetch facility data from EPA FRS REST API.

    Args:
        state_abbr: State abbreviation filter
        city_name: City name filter
        facility_name: Facility name pattern filter
        pgm_sys_acrnm: Program system acronym filter
        output_format: Response format (JSON or XML)

    Returns:
        JSON response as dict
    """
    config = load_config()
    api_config = config['data_sources']['api']
    base_url = api_config['base_url']

    params = {
        'output': output_format
    }

    if state_abbr:
        params['state_abbr'] = state_abbr.upper()
    if city_name:
        params['city_name'] = city_name
    if facility_name:
        params['facility_name'] = facility_name
    if pgm_sys_acrnm:
        params['pgm_sys_acrnm'] = pgm_sys_acrnm

    try:
        logger.info(f"Fetching from API with params: {params}")
        response = requests.get(base_url, params=params, timeout=60)
        response.raise_for_status()

        if output_format.upper() == "JSON":
            return response.json()
        else:
            return {'xml': response.text}

    except Exception as e:
        logger.error(f"API fetch failed: {e}")
        return {}
