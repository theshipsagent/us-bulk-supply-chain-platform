"""
File-based caching for downloaded Census data products.
"""

import os
import hashlib
from pathlib import Path


class DataCache:
    """Simple file-system cache for downloaded ZIP files and extracted data."""

    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
        self.cache_dir = Path(cache_dir).resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.zip_dir = self.cache_dir / "zips"
        self.zip_dir.mkdir(exist_ok=True)
        self.extracted_dir = self.cache_dir / "extracted"
        self.extracted_dir.mkdir(exist_ok=True)

    def _url_to_key(self, url: str) -> str:
        """Convert a URL to a safe filesystem key."""
        # Use the filename from the URL as the cache key
        filename = url.split("/")[-1]
        return filename

    def get_zip_path(self, url: str) -> Path:
        """Get the local path where a ZIP would be cached."""
        return self.zip_dir / self._url_to_key(url)

    def get_extract_dir(self, url: str) -> Path:
        """Get the directory where a ZIP's contents would be extracted."""
        key = self._url_to_key(url).replace(".ZIP", "").replace(".zip", "")
        extract_path = self.extracted_dir / key
        extract_path.mkdir(exist_ok=True)
        return extract_path

    def has_zip(self, url: str) -> bool:
        """Check if a ZIP file is already cached."""
        return self.get_zip_path(url).exists()

    def has_extracted(self, url: str) -> bool:
        """Check if a ZIP has been extracted."""
        extract_dir = self.get_extract_dir(url)
        return extract_dir.exists() and any(extract_dir.iterdir())

    def list_cached(self) -> list[str]:
        """List all cached ZIP filenames."""
        return [f.name for f in self.zip_dir.iterdir() if f.is_file()]

    def clear(self):
        """Remove all cached files."""
        import shutil
        shutil.rmtree(self.zip_dir, ignore_errors=True)
        shutil.rmtree(self.extracted_dir, ignore_errors=True)
        self.zip_dir.mkdir(exist_ok=True)
        self.extracted_dir.mkdir(exist_ok=True)
