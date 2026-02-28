"""
Census Foreign Trade Data Downloader

Downloads and extracts bulk data product ZIP files from Census.gov.
Handles caching to avoid redundant downloads.
"""

import zipfile
import io
import os
from pathlib import Path

import requests

from ..utils.cache import DataCache
from ..config.url_patterns import build_url, ALL_BULK_PRODUCTS


class CensusDownloader:
    """Downloads and extracts Census foreign trade bulk data products."""

    def __init__(self, cache_dir: str = None, timeout: int = 120):
        self.cache = DataCache(cache_dir)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "CensusTradeModule/0.1 (research)"
        })

    def download_zip(self, url: str, force: bool = False) -> Path:
        """Download a ZIP file from Census.gov.

        Args:
            url: Full URL to the ZIP file.
            force: Re-download even if cached.

        Returns:
            Path to the local ZIP file.
        """
        zip_path = self.cache.get_zip_path(url)

        if zip_path.exists() and not force:
            print(f"  [cached] {zip_path.name}")
            return zip_path

        print(f"  [downloading] {url}")
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()

        zip_path.write_bytes(resp.content)
        print(f"  [saved] {zip_path.name} ({len(resp.content) / 1024 / 1024:.1f} MB)")
        return zip_path

    def extract_zip(self, url: str, force: bool = False) -> Path:
        """Download (if needed) and extract a ZIP file.

        Args:
            url: Full URL to the ZIP file.
            force: Re-download and re-extract even if cached.

        Returns:
            Path to the extraction directory containing .TXT files.
        """
        zip_path = self.download_zip(url, force=force)
        extract_dir = self.cache.get_extract_dir(url)

        if self.cache.has_extracted(url) and not force:
            print(f"  [extracted] {extract_dir.name}/ ({len(list(extract_dir.iterdir()))} files)")
            return extract_dir

        print(f"  [extracting] {zip_path.name}")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        files = list(extract_dir.iterdir())
        print(f"  [done] {len(files)} files: {[f.name for f in files]}")
        return extract_dir

    def fetch_product(self, product_key: str, year: int,
                      month: int = None, quarter: int = None,
                      force: bool = False) -> Path:
        """Download and extract a named product by key.

        Args:
            product_key: Key from ALL_BULK_PRODUCTS (e.g. 'merchandise_exports').
            year: 4-digit year.
            month: Month (1-12) for monthly products.
            quarter: Quarter (1-4) for quarterly products.
            force: Re-download even if cached.

        Returns:
            Path to the extraction directory.
        """
        product = ALL_BULK_PRODUCTS[product_key]
        url = build_url(product, year, month=month, quarter=quarter)
        return self.extract_zip(url, force=force)

    def fetch_merchandise_exports(self, year: int, month: int, force: bool = False) -> Path:
        """Shortcut: download merchandise export data."""
        return self.fetch_product("merchandise_exports", year, month=month, force=force)

    def fetch_merchandise_imports(self, year: int, month: int, force: bool = False) -> Path:
        """Shortcut: download merchandise import data."""
        return self.fetch_product("merchandise_imports", year, month=month, force=force)

    def fetch_port_exports(self, year: int, month: int, force: bool = False) -> Path:
        """Shortcut: download port export data."""
        return self.fetch_product("port_exports_hs6", year, month=month, force=force)

    def fetch_port_imports(self, year: int, month: int, force: bool = False) -> Path:
        """Shortcut: download port import data."""
        return self.fetch_product("port_imports_hs6", year, month=month, force=force)

    def fetch_range(self, product_key: str, start_year: int, start_month: int,
                    end_year: int, end_month: int, force: bool = False) -> list[Path]:
        """Download a range of monthly data products.

        Returns:
            List of extraction directory paths.
        """
        paths = []
        for year in range(start_year, end_year + 1):
            sm = start_month if year == start_year else 1
            em = end_month if year == end_year else 12
            for month in range(sm, em + 1):
                try:
                    path = self.fetch_product(product_key, year, month=month, force=force)
                    paths.append(path)
                except requests.HTTPError as e:
                    print(f"  [skip] {year}-{month:02d}: {e}")
        return paths

    def list_files(self, extract_dir: Path) -> dict[str, Path]:
        """List all extracted files in a directory, keyed by stem.

        Returns:
            Dict mapping filename stem (e.g. 'EXP_DETL') to full Path.
        """
        return {
            f.stem.upper(): f
            for f in extract_dir.iterdir()
            if f.is_file()
        }
