"""
Additional Government Sources Scraper
MSC, Navy, and other government maritime data sources
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


class GovSourcesScraper:
    """Scrapes data from MSC, Navy, and other government sources"""

    def __init__(self, config: dict, output_dir: str):
        """
        Initialize government sources scraper

        Args:
            config: Configuration dictionary
            output_dir: Directory to save downloaded files
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.msc_base_url = config['data_sources']['msc']['base_url']
        self.msc_fleet_url = config['data_sources']['msc']['fleet_url']
        self.navy_base_url = config['data_sources']['navy']['base_url']

        self.rate_limit = config['scraping']['rate_limit_seconds']
        self.timeout = config['scraping']['timeout_seconds']

        logger.info(f"Initialized gov sources scraper, output: {self.output_dir}")

    def scrape(self) -> List[Path]:
        """
        Main scraping method

        Returns:
            List of paths to downloaded files
        """
        logger.info("Starting government sources data collection")
        downloaded_files = []

        try:
            # Scrape MSC data
            files = self._scrape_msc()
            downloaded_files.extend(files)

            # Scrape Navy data
            files = self._scrape_navy()
            downloaded_files.extend(files)

            # Scrape transportation.gov
            files = self._scrape_transportation_gov()
            downloaded_files.extend(files)

        except Exception as e:
            logger.error(f"Error during gov sources scraping: {e}", exc_info=True)

        logger.info(f"Gov sources scraping complete: {len(downloaded_files)} files")
        return downloaded_files

    def _scrape_msc(self) -> List[Path]:
        """
        Scrape Military Sealift Command data

        Returns:
            List of downloaded files
        """
        downloaded = []

        try:
            logger.info("Scraping MSC fleet data")

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=self.config['scraping']['user_agent']
                )
                page = context.new_page()

                # MSC Ships page
                try:
                    page.goto(self.msc_fleet_url, timeout=self.timeout * 1000)
                    page.wait_for_load_state('networkidle')

                    # Save the page content
                    content = page.content()
                    output_path = self.output_dir / f"msc_ships_page_{datetime.now().strftime('%Y%m%d')}.html"
                    output_path.write_text(content, encoding='utf-8')
                    downloaded.append(output_path)
                    logger.info(f"Saved MSC ships page: {output_path}")

                    # Look for downloadable data files
                    links = self._find_data_links_playwright(page, [
                        r'fleet',
                        r'vessel',
                        r'ship.*list',
                        r'inventory'
                    ])

                    for link_info in links:
                        file_path = self._download_file(
                            link_info['url'],
                            f"msc_{link_info['filename']}"
                        )
                        if file_path:
                            downloaded.append(file_path)
                        time.sleep(self.rate_limit)

                except Exception as e:
                    logger.warning(f"Failed to scrape MSC fleet page: {e}")

                # Try searching for specific MSC data
                msc_pages = [
                    f"{self.msc_base_url}/About/",
                    f"{self.msc_base_url}/Ships/Ship-Inventory/",
                    f"{self.msc_base_url}/Operations/"
                ]

                for url in msc_pages:
                    try:
                        page.goto(url, timeout=self.timeout * 1000)
                        page.wait_for_load_state('networkidle')

                        links = self._find_data_links_playwright(page, [
                            r'vessel',
                            r'ship',
                            r'operator',
                            r'civilian'
                        ])

                        for link_info in links:
                            file_path = self._download_file(
                                link_info['url'],
                                f"msc_{link_info['filename']}"
                            )
                            if file_path:
                                downloaded.append(file_path)
                            time.sleep(self.rate_limit)

                    except Exception as e:
                        logger.debug(f"Could not access {url}: {e}")
                        continue

                browser.close()

        except Exception as e:
            logger.warning(f"MSC scraping failed: {e}")

        return downloaded

    def _scrape_navy(self) -> List[Path]:
        """
        Scrape Navy.mil for fleet status information

        Returns:
            List of downloaded files
        """
        downloaded = []

        try:
            logger.info("Scraping Navy.mil data")

            # Try common Navy data pages
            navy_pages = [
                f"{self.navy_base_url}/Resources/Fleet-Status/",
                f"{self.navy_base_url}/Resources/",
                f"{self.navy_base_url}/About/"
            ]

            for url in navy_pages:
                try:
                    response = requests.get(
                        url,
                        timeout=self.timeout,
                        headers={'User-Agent': self.config['scraping']['user_agent']}
                    )

                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')

                        # Look for MSC or sealift related content
                        links = self._find_data_links(soup, [
                            r'sealift',
                            r'msc',
                            r'auxiliary',
                            r'fleet.*status'
                        ])

                        for link_info in links:
                            file_path = self._download_file(
                                link_info['url'],
                                f"navy_{link_info['filename']}"
                            )
                            if file_path:
                                downloaded.append(file_path)
                            time.sleep(self.rate_limit)

                except Exception as e:
                    logger.debug(f"Could not scrape {url}: {e}")
                    continue

        except Exception as e:
            logger.warning(f"Navy scraping failed: {e}")

        return downloaded

    def _scrape_transportation_gov(self) -> List[Path]:
        """
        Scrape transportation.gov for maritime data

        Returns:
            List of downloaded files
        """
        downloaded = []

        try:
            logger.info("Scraping transportation.gov")

            base_url = "https://www.transportation.gov"
            pages = [
                f"{base_url}/maritime",
                f"{base_url}/policy-initiatives/maritime-security"
            ]

            for url in pages:
                try:
                    response = requests.get(
                        url,
                        timeout=self.timeout,
                        headers={'User-Agent': self.config['scraping']['user_agent']}
                    )

                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')

                        links = self._find_data_links(soup, [
                            r'maritime',
                            r'vessel',
                            r'fleet',
                            r'sealift'
                        ])

                        for link_info in links:
                            file_path = self._download_file(
                                link_info['url'],
                                f"dot_{link_info['filename']}"
                            )
                            if file_path:
                                downloaded.append(file_path)
                            time.sleep(self.rate_limit)

                except Exception as e:
                    logger.debug(f"Could not scrape {url}: {e}")
                    continue

        except Exception as e:
            logger.warning(f"Transportation.gov scraping failed: {e}")

        return downloaded

    def _find_data_links(self, soup: BeautifulSoup, patterns: List[str]) -> List[Dict]:
        """Find data file links matching patterns"""
        links = []

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            text = a_tag.get_text().lower()

            if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                if any(ext in href.lower() for ext in ['.xlsx', '.xls', '.csv', '.pdf', '.zip']):
                    full_url = href if href.startswith('http') else f"{self.navy_base_url}{href}"
                    filename = self._generate_filename(href, text)

                    links.append({
                        'url': full_url,
                        'filename': filename,
                        'text': text
                    })

        return links

    def _find_data_links_playwright(self, page: Page, patterns: List[str]) -> List[Dict]:
        """Find data file links using Playwright"""
        links = []

        link_elements = page.locator('a[href]').all()

        for element in link_elements:
            try:
                href = element.get_attribute('href')
                text = element.inner_text().lower()

                if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                    if any(ext in href.lower() for ext in ['.xlsx', '.xls', '.csv', '.pdf', '.zip']):
                        full_url = href if href.startswith('http') else self.msc_base_url + href
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
        """Download file"""
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
        """Generate descriptive filename"""
        ext = os.path.splitext(url.split('?')[0])[1]

        clean_desc = re.sub(r'[^\w\s-]', '', description)
        clean_desc = re.sub(r'[-\s]+', '_', clean_desc)
        clean_desc = clean_desc[:50]

        timestamp = datetime.now().strftime('%Y%m%d')

        return f"{clean_desc}_{timestamp}{ext}"

    def get_cached_files(self) -> List[Path]:
        """Get list of cached files"""
        if not self.output_dir.exists():
            return []
        return list(self.output_dir.glob('*'))
