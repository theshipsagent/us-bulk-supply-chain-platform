"""
Maritime Administration (MARAD) Scraper
Downloads fleet statistics and MSC operator data from MARAD
"""
import os
import re
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from playwright.sync_api import sync_playwright, Page
import requests
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class MARADScraper:
    """Scrapes vessel and operator data from MARAD"""

    def __init__(self, config: dict, output_dir: str):
        """
        Initialize MARAD scraper

        Args:
            config: Configuration dictionary
            output_dir: Directory to save downloaded files
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.base_url = config['data_sources']['marad']['base_url']
        self.fleet_url = config['data_sources']['marad']['fleet_statistics_url']
        self.rate_limit = config['scraping']['rate_limit_seconds']
        self.timeout = config['scraping']['timeout_seconds']

        logger.info(f"Initialized MARAD scraper, output: {self.output_dir}")

    def scrape(self) -> List[Path]:
        """
        Main scraping method

        Returns:
            List of paths to downloaded files
        """
        logger.info("Starting MARAD data collection")
        downloaded_files = []

        try:
            # Search for fleet statistics
            files = self._scrape_fleet_statistics()
            downloaded_files.extend(files)

            # Search for MSC operator information
            files = self._scrape_msc_operators()
            downloaded_files.extend(files)

            # Search for vessel databases
            files = self._scrape_vessel_databases()
            downloaded_files.extend(files)

        except Exception as e:
            logger.error(f"Error during MARAD scraping: {e}", exc_info=True)

        logger.info(f"MARAD scraping complete: {len(downloaded_files)} files")
        return downloaded_files

    def _scrape_fleet_statistics(self) -> List[Path]:
        """
        Scrape fleet statistics and data

        Returns:
            List of downloaded files
        """
        downloaded = []

        try:
            logger.info(f"Fetching MARAD fleet statistics: {self.fleet_url}")
            response = requests.get(
                self.fleet_url,
                timeout=self.timeout,
                headers={'User-Agent': self.config['scraping']['user_agent']}
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find data files related to fleet statistics
            links = self._find_data_links(soup, [
                r'fleet.*statistics',
                r'vessel.*inventory',
                r'merchant.*fleet',
                r'us.*flag.*vessels'
            ])

            for link_info in links:
                file_path = self._download_file(link_info['url'], link_info['filename'])
                if file_path:
                    downloaded.append(file_path)
                time.sleep(self.rate_limit)

        except Exception as e:
            logger.warning(f"Fleet statistics scraping failed: {e}")

        return downloaded

    def _scrape_msc_operators(self) -> List[Path]:
        """
        Search for MSC operator and contractor information

        Returns:
            List of downloaded files
        """
        downloaded = []

        search_terms = [
            "military sealift command contractors",
            "MSC civilian operators",
            "sealift operators",
            "maritime contract operators"
        ]

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=self.config['scraping']['user_agent']
                )
                page = context.new_page()

                for term in search_terms:
                    logger.info(f"Searching MARAD for: {term}")

                    # Use site search
                    search_url = f"{self.base_url}/search?query={term.replace(' ', '+')}"

                    try:
                        page.goto(search_url, timeout=self.timeout * 1000)
                        page.wait_for_load_state('networkidle')

                        # Find relevant data files
                        links = self._find_data_links_playwright(page, [
                            r'operator',
                            r'contractor',
                            r'msc',
                            r'sealift'
                        ])

                        for link_info in links:
                            file_path = self._download_file(
                                link_info['url'],
                                link_info['filename']
                            )
                            if file_path:
                                downloaded.append(file_path)
                            time.sleep(self.rate_limit)

                    except Exception as e:
                        logger.debug(f"Search for '{term}' failed: {e}")
                        continue

                browser.close()

        except Exception as e:
            logger.warning(f"MSC operator scraping failed: {e}")

        return downloaded

    def _scrape_vessel_databases(self) -> List[Path]:
        """
        Search for vessel database files

        Returns:
            List of downloaded files
        """
        downloaded = []

        # Try common MARAD data pages
        data_pages = [
            f"{self.base_url}/data-and-statistics/data-statistics/",
            f"{self.base_url}/ships-and-shipping/",
            f"{self.base_url}/strategic-sealift/"
        ]

        for url in data_pages:
            try:
                logger.info(f"Checking: {url}")
                response = requests.get(
                    url,
                    timeout=self.timeout,
                    headers={'User-Agent': self.config['scraping']['user_agent']}
                )

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    links = self._find_data_links(soup, [
                        r'vessel',
                        r'ship',
                        r'fleet',
                        r'database'
                    ])

                    for link_info in links:
                        file_path = self._download_file(
                            link_info['url'],
                            link_info['filename']
                        )
                        if file_path:
                            downloaded.append(file_path)
                        time.sleep(self.rate_limit)

            except Exception as e:
                logger.debug(f"Failed to scrape {url}: {e}")
                continue

        return downloaded

    def _find_data_links(self, soup: BeautifulSoup, patterns: List[str]) -> List[Dict]:
        """
        Find data file links matching patterns

        Args:
            soup: BeautifulSoup object
            patterns: List of regex patterns to match

        Returns:
            List of link info dicts
        """
        links = []

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            text = a_tag.get_text().lower()

            # Check if link matches patterns
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                # Check for data file extensions
                if any(ext in href.lower() for ext in ['.xlsx', '.xls', '.csv', '.pdf', '.zip']):
                    full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                    filename = self._generate_filename(href, text)

                    links.append({
                        'url': full_url,
                        'filename': filename,
                        'text': text
                    })
                    logger.debug(f"Found MARAD link: {text} -> {full_url}")

        return links

    def _find_data_links_playwright(self, page: Page, patterns: List[str]) -> List[Dict]:
        """
        Find data file links using Playwright

        Args:
            page: Playwright page
            patterns: List of regex patterns

        Returns:
            List of link info dicts
        """
        links = []

        link_elements = page.locator('a[href]').all()

        for element in link_elements:
            try:
                href = element.get_attribute('href')
                text = element.inner_text().lower()

                if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                    if any(ext in href.lower() for ext in ['.xlsx', '.xls', '.csv', '.pdf', '.zip']):
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

        return links

    def _download_file(self, url: str, filename: str) -> Optional[Path]:
        """
        Download file

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
                stream=True,
                allow_redirects=True
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

    def _generate_filename(self, url: str, description: str) -> str:
        """
        Generate descriptive filename

        Args:
            url: File URL
            description: Link description

        Returns:
            Sanitized filename
        """
        ext = os.path.splitext(url.split('?')[0])[1]

        clean_desc = re.sub(r'[^\w\s-]', '', description)
        clean_desc = re.sub(r'[-\s]+', '_', clean_desc)
        clean_desc = clean_desc[:50]

        timestamp = datetime.now().strftime('%Y%m%d')

        return f"marad_{clean_desc}_{timestamp}{ext}"

    def get_cached_files(self) -> List[Path]:
        """Get list of cached files"""
        if not self.output_dir.exists():
            return []
        return list(self.output_dir.glob('*'))
