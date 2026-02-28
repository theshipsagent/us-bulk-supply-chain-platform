"""
generate_pdfs.py — Convert all SCM dossier HTML files to print-quality PDFs
Uses Playwright (headless Chromium) for pixel-perfect Chrome rendering.

Install once:
    pip install playwright
    playwright install chromium

Run:
    python generate_pdfs.py
"""

from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = Path(__file__).parent

DOSSIERS = [
    (
        BASE / "slag/market_intelligence/dossier/SLAG_COMPREHENSIVE_DOSSIER.html",
        BASE / "slag/market_intelligence/dossier/SLAG_COMPREHENSIVE_DOSSIER.pdf",
    ),
    (
        BASE / "flyash/market_intelligence/dossier/FLY_ASH_COMPREHENSIVE_DOSSIER_v3.html",
        BASE / "flyash/market_intelligence/dossier/FLY_ASH_COMPREHENSIVE_DOSSIER_v3.pdf",
    ),
    (
        BASE / "aggregates/market_intelligence/dossier/AGGREGATES_COMPREHENSIVE_DOSSIER.html",
        BASE / "aggregates/market_intelligence/dossier/AGGREGATES_COMPREHENSIVE_DOSSIER.pdf",
    ),
    (
        BASE / "natural_pozzolan/market_intelligence/dossier/NATURAL_POZZOLAN_COMPREHENSIVE_DOSSIER.html",
        BASE / "natural_pozzolan/market_intelligence/dossier/NATURAL_POZZOLAN_COMPREHENSIVE_DOSSIER.pdf",
    ),
]


def generate():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for html_path, pdf_path in DOSSIERS:
            if not html_path.exists():
                print(f"  SKIP (not found): {html_path.name}")
                continue

            print(f"  Generating: {pdf_path.name} ...", end=" ", flush=True)
            page.goto(html_path.as_uri(), wait_until="networkidle")

            page.pdf(
                path=str(pdf_path),
                format="Letter",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            print(f"done  ->  {pdf_path}")

        browser.close()


if __name__ == "__main__":
    print("SCM Dossier PDF Generator")
    print("=" * 50)
    generate()
    print("\nAll PDFs written.")
