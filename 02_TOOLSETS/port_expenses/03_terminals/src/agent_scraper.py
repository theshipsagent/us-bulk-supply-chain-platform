"""
Ship Agent & Port Authority Web Scraper
=========================================
Scrapes terminal tariff data from ship agent websites (Bluewater, Norton Lilly,
GAC) and port authority tariff schedule pages.

Run this from a session with internet access (e.g. claude.ai browser, or locally
with requests + beautifulsoup4 installed).

    pip install requests beautifulsoup4 lxml
    python agent_scraper.py --output ../data/scraped_tariffs.json

Targets
-------
Bluewater Shipping:     https://www.bluewater.com
Norton Lilly:          https://www.nortonlilly.com
GAC:                   https://www.gac.com
Port Houston:          https://porthouston.com/tariff
Port NOLA:             https://portno.com/tariffs
Georgia Ports (GPA):   https://gaports.com/tariffs
Virginia Port Auth:    https://portofvirginia.com/tariffs
Maryland Port Admin:   https://marylandports.com/tariffs
Alabama State Docks:   https://asdd.com/tariffs
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = 20
DELAY = 1.5  # polite delay between requests

# ---------------------------------------------------------------------------
# Target registry
# ---------------------------------------------------------------------------

TARGETS = [
    # ---- Ship Agents -------------------------------------------------------
    {
        "id": "bluewater",
        "name": "Bluewater Shipping",
        "type": "ship_agent",
        "urls": [
            "https://www.bluewater.com",
            "https://www.bluewater.com/port-services",
            "https://www.bluewater.com/port-costs",
            "https://www.bluewater.com/disbursements",
            "https://www.bluewater.com/port-information",
        ],
        "keywords": ["tariff", "disbursement", "wharfage", "dockage", "stevedoring",
                     "port cost", "PDA", "proforma"],
        "pdf_patterns": [r"tariff", r"disbursement", r"port.cost", r"PDA"],
    },
    {
        "id": "norton_lilly",
        "name": "Norton Lilly International",
        "type": "ship_agent",
        "urls": [
            "https://www.nortonlilly.com",
            "https://www.nortonlilly.com/port-information",
            "https://www.nortonlilly.com/services",
        ],
        "keywords": ["tariff", "port costs", "wharfage", "dockage", "stevedoring"],
        "pdf_patterns": [r"tariff", r"port.cost"],
    },
    {
        "id": "gac",
        "name": "GAC (Gulf Agency Company)",
        "type": "ship_agent",
        "urls": [
            "https://www.gac.com/en/ports-services/port-information",
            "https://www.gac.com/en/shipping",
        ],
        "keywords": ["tariff", "port costs", "disbursement"],
        "pdf_patterns": [r"tariff", r"port.cost"],
    },
    {
        "id": "inchcape",
        "name": "Inchcape Shipping Services",
        "type": "ship_agent",
        "urls": [
            "https://www.iss-shipping.com",
            "https://www.iss-shipping.com/port-services",
        ],
        "keywords": ["tariff", "port costs", "wharfage"],
        "pdf_patterns": [r"tariff"],
    },

    # ---- Port Authorities --------------------------------------------------
    {
        "id": "port_nola",
        "name": "Port of New Orleans (Port NOLA)",
        "type": "port_authority",
        "urls": [
            "https://portno.com/tariffs",
            "https://portnola.com/tariffs",
            "https://www.portno.com/rates",
        ],
        "keywords": ["tariff", "schedule", "dockage", "wharfage", "harbour dues"],
        "pdf_patterns": [r"tariff", r"rate.schedule", r"wharfage"],
    },
    {
        "id": "port_houston",
        "name": "Port Houston Authority",
        "type": "port_authority",
        "urls": [
            "https://porthouston.com/tariff",
            "https://porthouston.com/doing-business/tariff",
            "https://www.porthouston.com/tariff",
        ],
        "keywords": ["tariff", "dockage", "wharfage"],
        "pdf_patterns": [r"tariff"],
    },
    {
        "id": "georgia_ports",
        "name": "Georgia Ports Authority (GPA)",
        "type": "port_authority",
        "urls": [
            "https://www.gaports.com/tariffs",
            "https://gaports.com/doing-business/tariffs",
        ],
        "keywords": ["tariff", "dockage", "wharfage", "schedule"],
        "pdf_patterns": [r"tariff", r"schedule"],
    },
    {
        "id": "virginia_port",
        "name": "Virginia Port Authority",
        "type": "port_authority",
        "urls": [
            "https://www.portofvirginia.com/tariffs",
            "https://portofvirginia.com/doing-business",
        ],
        "keywords": ["tariff", "dockage", "wharfage"],
        "pdf_patterns": [r"tariff"],
    },
    {
        "id": "maryland_port",
        "name": "Maryland Port Administration",
        "type": "port_authority",
        "urls": [
            "https://marylandports.com/tariffs",
            "https://www.marylandports.com/tariff-and-schedules",
        ],
        "keywords": ["tariff", "dockage", "wharfage"],
        "pdf_patterns": [r"tariff"],
    },
    {
        "id": "alabama_port",
        "name": "Alabama State Port Authority (ASPA)",
        "type": "port_authority",
        "urls": [
            "https://www.asdd.com/tariffs",
            "https://asdd.com/doing-business/tariffs",
            "https://www.alabama-port.com/tariffs",
        ],
        "keywords": ["tariff", "dockage", "wharfage"],
        "pdf_patterns": [r"tariff"],
    },
    {
        "id": "tampa_port",
        "name": "Port Tampa Bay",
        "type": "port_authority",
        "urls": [
            "https://www.tampaport.com/tariffs",
            "https://tampaport.com/doing-business",
        ],
        "keywords": ["tariff", "dockage", "wharfage"],
        "pdf_patterns": [r"tariff"],
    },
    {
        "id": "port_portland",
        "name": "Port of Portland (Columbia River)",
        "type": "port_authority",
        "urls": [
            "https://www.portofportland.com/tariffs",
            "https://portofportland.com/maritime/tariff",
        ],
        "keywords": ["tariff", "dockage", "wharfage"],
        "pdf_patterns": [r"tariff"],
    },
]


# ---------------------------------------------------------------------------
# Scraper
# ---------------------------------------------------------------------------

class TariffScraper:
    def __init__(self):
        try:
            import requests
            from bs4 import BeautifulSoup
            self.requests = requests
            self.BeautifulSoup = BeautifulSoup
            self.session = requests.Session()
            self.session.headers.update(HEADERS)
        except ImportError as e:
            raise ImportError(
                f"Missing dependency: {e}\n"
                "Install with: pip install requests beautifulsoup4 lxml"
            )

    def _get(self, url: str) -> Optional[str]:
        """Fetch a URL, return HTML text or None."""
        try:
            time.sleep(DELAY)
            resp = self.session.get(url, timeout=TIMEOUT, allow_redirects=True)
            if resp.status_code == 200:
                return resp.text
            logger.info("HTTP %d for %s", resp.status_code, url)
        except Exception as e:
            logger.warning("Failed to fetch %s: %s", url, e)
        return None

    def _extract_text(self, html: str) -> str:
        """Extract readable text from HTML."""
        soup = self.BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return " ".join(soup.get_text().split())

    def _find_pdf_links(self, html: str, base_url: str, patterns: list[str]) -> list[str]:
        """Find PDF links matching given regex patterns."""
        soup = self.BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not href.lower().endswith(".pdf"):
                continue
            full = urljoin(base_url, href)
            link_text = (a.get_text() + " " + href).lower()
            if any(re.search(p, link_text, re.I) for p in patterns):
                links.append(full)
        return links

    def _extract_rates(self, text: str) -> dict:
        """
        Attempt to extract rate figures from page text.
        Looks for patterns like '$8.50/ton', '$9.50 per foot', etc.
        Returns dict of found values — to be reviewed manually.
        """
        found = {}

        # Dollar amounts with context
        matches = re.findall(
            r'\$\s*(\d+(?:\.\d+)?)\s*(?:per|/)\s*(\w+(?:\s+\w+)?)',
            text, re.I
        )
        for amount, unit in matches:
            unit_clean = unit.strip().lower()
            key = f"rate_{unit_clean.replace(' ', '_')}"
            found[key] = float(amount)

        # Dockage: X.XX per foot per day
        m = re.search(r'dockage[^$]*\$\s*(\d+(?:\.\d+)?)', text, re.I)
        if m:
            found["dockage_per_ft_day"] = float(m.group(1))

        # Wharfage: X.XX per ton
        m = re.search(r'wharfage[^$]*\$\s*(\d+(?:\.\d+)?)', text, re.I)
        if m:
            found["wharfage_per_ton"] = float(m.group(1))

        return found

    def scrape_target(self, target: dict) -> dict:
        """Scrape all URLs for a target, return findings dict."""
        result = {
            "id": target["id"],
            "name": target["name"],
            "type": target["type"],
            "urls_tried": [],
            "urls_accessible": [],
            "pdf_links_found": [],
            "extracted_rates": {},
            "page_snippets": [],
            "data_found": False,
            "notes": [],
        }

        for url in target["urls"]:
            result["urls_tried"].append(url)
            html = self._get(url)
            if html is None:
                continue

            result["urls_accessible"].append(url)
            result["data_found"] = True

            # Find PDF links
            pdfs = self._find_pdf_links(html, url, target.get("pdf_patterns", []))
            result["pdf_links_found"].extend(pdfs)

            # Extract text and look for rates
            text = self._extract_text(html)
            rates = self._extract_rates(text)
            if rates:
                result["extracted_rates"].update(rates)

            # Save a snippet of relevant text (first 1000 chars with keywords)
            kws = target.get("keywords", [])
            for kw in kws:
                idx = text.lower().find(kw.lower())
                if idx >= 0:
                    snippet = text[max(0, idx-100):idx+400]
                    result["page_snippets"].append({
                        "keyword": kw,
                        "url": url,
                        "snippet": snippet,
                    })
                    break  # One snippet per URL

        if not result["data_found"]:
            result["notes"].append("All URLs inaccessible — try manually or check URL patterns")

        return result

    def run(self, output_path: Path) -> dict:
        """Scrape all targets and write JSON output."""
        output = {
            "metadata": {
                "scrape_date": str(__import__("datetime").datetime.utcnow().isoformat()),
                "targets_count": len(TARGETS),
                "note": "Output requires manual review — extracted rates are pattern-matched approximations",
            },
            "results": [],
            "pdf_links_all": [],
            "summary": {},
        }

        for target in TARGETS:
            logger.info("Scraping: %s", target["name"])
            result = self.scrape_target(target)
            output["results"].append(result)
            output["pdf_links_all"].extend(result["pdf_links_found"])
            print(
                f"  {'✓' if result['data_found'] else '✗'} {target['name']:<40} "
                f"PDFs:{len(result['pdf_links_found'])}  "
                f"Rates:{len(result['extracted_rates'])}"
            )

        # Summary
        accessible = sum(1 for r in output["results"] if r["data_found"])
        output["summary"] = {
            "targets_total": len(TARGETS),
            "targets_accessible": accessible,
            "pdf_links_found": len(output["pdf_links_all"]),
            "targets_with_rates": sum(1 for r in output["results"] if r["extracted_rates"]),
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        logger.info("Output written to %s", output_path)
        return output


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(
        description="Scrape ship agent and port authority websites for terminal tariff data"
    )
    parser.add_argument(
        "--output", "-o",
        default="../data/scraped_tariffs.json",
        help="Output JSON file path",
    )
    parser.add_argument(
        "--target", "-t",
        help="Scrape a single target by ID (e.g. 'bluewater'). Default: all targets.",
    )
    args = parser.parse_args()

    output_path = Path(args.output)

    scraper = TariffScraper()

    if args.target:
        targets_to_run = [t for t in TARGETS if t["id"] == args.target]
        if not targets_to_run:
            ids = [t["id"] for t in TARGETS]
            print(f"Target '{args.target}' not found. Available: {', '.join(ids)}")
            return
    else:
        targets_to_run = TARGETS

    print(f"\nScraping {len(targets_to_run)} target(s)...\n")
    for target in targets_to_run:
        result = scraper.scrape_target(target)
        print(
            f"  {'✓' if result['data_found'] else '✗'} {target['name']:<40} "
            f"PDFs: {result['pdf_links_found']}  "
            f"Rates: {result['extracted_rates']}"
        )
        if result["pdf_links_found"]:
            print("    PDF links found:")
            for pdf in result["pdf_links_found"]:
                print(f"      {pdf}")

    print(f"\nDone. Results logged to console (full output requires --output flag).")


if __name__ == "__main__":
    main()
