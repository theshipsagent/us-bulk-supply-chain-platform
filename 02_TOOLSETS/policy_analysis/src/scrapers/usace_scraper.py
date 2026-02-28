"""
USACE Waterborne Commerce Statistics Center Scraper
Downloads vessel characteristics data from USACE
"""
import os
import re
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from playwright.sync_api import sync_playwright, Page, Browser
import requests
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class USACEScraper:
    """Scrapes vessel data from USACE Waterborne Commerce Statistics Center"""

    def __init__(self, config: dict, output_dir: str):
        """
        Initialize USACE scraper

        Args:
            config: Configuration dictionary
            output_dir: Directory to save downloaded files
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.base_url = config['data_sources']['usace']['base_url']
        self.vessel_char_url = config['data_sources']['usace']['vessel_characteristics_url']
        self.rate_limit = config['scraping']['rate_limit_seconds']
        self.max_retries = config['scraping']['max_retries']
        self.timeout = config['scraping']['timeout_seconds']

        logger.info(f"Initialized USACE scraper, output: {self.output_dir}")

    def scrape(self) -> List[Path]:
        """
        Main scraping method - downloads vessel characteristics data

        Returns:
            List of paths to downloaded files
        """
        logger.info("Starting USACE data collection")
        downloaded_files = []

        try:
            # Try with requests first for simple downloads
            files = self._scrape_with_requests()
            if files:
                downloaded_files.extend(files)
                logger.info(f"Downloaded {len(files)} files with requests")

            # Use Playwright for JavaScript-heavy pages
            if not downloaded_files:
                files = self._scrape_with_playwright()
                downloaded_files.extend(files)
                logger.info(f"Downloaded {len(files)} files with Playwright")

        except Exception as e:
            logger.error(f"Error during USACE scraping: {e}", exc_info=True)

        return downloaded_files

    def _scrape_with_requests(self) -> List[Path]:
        """
        Attempt to scrape using requests library

        Returns:
            List of downloaded file paths
        """
        downloaded = []

        try:
            logger.info(f"Fetching page: {self.vessel_char_url}")
            response = requests.get(
                self.vessel_char_url,
                timeout=self.timeout,
                headers={'User-Agent': self.config['scraping']['user_agent']}
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find download links for vessel data
            links = self._find_vessel_data_links(soup)

            for link_info in links:
                file_path = self._download_file(
                    link_info['url'],
                    link_info['filename']
                )
                if file_path:
                    downloaded.append(file_path)

                time.sleep(self.rate_limit)

        except Exception as e:
            logger.warning(f"Requests scraping failed: {e}")

        return downloaded

    def _scrape_with_playwright(self) -> List[Path]:
        """
        Scrape using Playwright for JavaScript-rendered content

        Returns:
            List of downloaded file paths
        """
        downloaded = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=self.config['scraping']['user_agent']
                )
                page = context.new_page()

                logger.info(f"Navigating to: {self.vessel_char_url}")
                page.goto(self.vessel_char_url, timeout=self.timeout * 1000)
                page.wait_for_load_state('networkidle')

                # Find and download files
                links = self._find_download_links_playwright(page)

                for link_info in links:
                    file_path = self._download_file_playwright(
                        page,
                        link_info['url'],
                        link_info['filename']
                    )
                    if file_path:
                        downloaded.append(file_path)

                    time.sleep(self.rate_limit)

                browser.close()

        except Exception as e:
            logger.error(f"Playwright scraping failed: {e}", exc_info=True)

        return downloaded

    def _find_vessel_data_links(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Parse HTML to find vessel data download links

        Args:
            soup: BeautifulSoup object

        Returns:
            List of dicts with 'url' and 'filename'
        """
        links = []

        # Look for links to Excel, CSV, or PDF files
        patterns = [
            r'vessel.*characteristics',
            r'waterborne.*commerce',
            r'fleet.*data',
            r'us.*flag',
            r'self.*propelled'
        ]

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            text = a_tag.get_text().lower()

            # Check if link matches our patterns
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                # Check if it's a data file
                if any(ext in href.lower() for ext in ['.xlsx', '.xls', '.csv', '.pdf']):
                    full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                    filename = self._generate_filename(href, text)

                    links.append({
                        'url': full_url,
                        'filename': filename,
                        'text': text
                    })
                    logger.debug(f"Found link: {text} -> {full_url}")

        logger.info(f"Found {len(links)} potential data files")
        return links

    def _find_download_links_playwright(self, page: Page) -> List[Dict]:
        """
        Find download links using Playwright

        Args:
            page: Playwright page object

        Returns:
            List of dicts with 'url' and 'filename'
        """
        links = []

        # Get all links
        link_elements = page.locator('a[href]').all()

        for element in link_elements:
            try:
                href = element.get_attribute('href')
                text = element.inner_text().lower()

                patterns = [
                    r'vessel.*characteristics',
                    r'waterborne.*commerce',
                    r'fleet.*data',
                    r'us.*flag'
                ]

                if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                    if any(ext in href.lower() for ext in ['.xlsx', '.xls', '.csv', '.pdf']):
                        full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                        filename = self._generate_filename(href, text)

                        links.append({
                            'url': full_url,
                            'filename': filename,
                            'text': text
                        })

            except Exception as e:
                logger.debug(f"Error processing link: {e}")
                continue

        logger.info(f"Found {len(links)} data file links")
        return links

    def _download_file(self, url: str, filename: str) -> Optional[Path]:
        """
        Download file using requests

        Args:
            url: File URL
            filename: Output filename

        Returns:
            Path to downloaded file or None
        """
        try:
            logger.info(f"Downloading: {url}")
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={'User-Agent': self.config['scraping']['user_agent']},
                stream=True
            )
            response.raise_for_status()

            output_path = self.output_dir / filename

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Saved: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return None

    def _download_file_playwright(self, page: Page, url: str, filename: str) -> Optional[Path]:
        """
        Download file using Playwright

        Args:
            page: Playwright page
            url: File URL
            filename: Output filename

        Returns:
            Path to downloaded file or None
        """
        try:
            logger.info(f"Downloading with Playwright: {url}")

            with page.expect_download() as download_info:
                page.goto(url)

            download = download_info.value
            output_path = self.output_dir / filename
            download.save_as(output_path)

            logger.info(f"Saved: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Playwright download failed for {url}: {e}")
            # Fallback to requests
            return self._download_file(url, filename)

    def _generate_filename(self, url: str, description: str) -> str:
        """
        Generate descriptive filename

        Args:
            url: File URL
            description: Link text description

        Returns:
            Sanitized filename
        """
        # Get extension from URL
        ext = os.path.splitext(url)[1].split('?')[0]

        # Clean description
        clean_desc = re.sub(r'[^\w\s-]', '', description)
        clean_desc = re.sub(r'[-\s]+', '_', clean_desc)
        clean_desc = clean_desc[:50]  # Limit length

        # Add timestamp
        timestamp = datetime.now().strftime('%Y%m%d')

        return f"usace_{clean_desc}_{timestamp}{ext}"

    def get_cached_files(self) -> List[Path]:
        """
        Get list of already downloaded files

        Returns:
            List of file paths
        """
        if not self.output_dir.exists():
            return []

        files = list(self.output_dir.glob('*'))
        logger.info(f"Found {len(files)} cached files")
        return files
