# More reliable PDF generator using Playwright
# Install: pip install playwright
# Then run: playwright install chromium

import asyncio
import os
from playwright.async_api import async_playwright


async def generate_perfect_pdf():
    print("🚀 Starting PDF generation with Playwright...")

    # Check if the fixed HTML file exists (now on Desktop)
    html_path = r"C:\Users\wsd3\OneDrive\Desktop\US Gulf Cement Report August 2025.html"

    if not os.path.exists(html_path):
        print("❌ US Gulf Cement Report August 2025.html not found!")
        print("🔧 Please run the HTML fixer script first")
        return

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            file_url = f"file:///{html_path.replace(chr(92), '/')}"

            print(f"📄 Loading HTML from: {file_url}")

            # Load the HTML and wait for charts
            await page.goto(file_url, wait_until='networkidle')
            print("📊 Waiting for charts to render...")
            await page.wait_for_timeout(5000)  # Wait for Chart.js to render

            # Generate perfect PDF (also on Desktop)
            output_path = r"C:\Users\wsd3\OneDrive\Desktop\PERFECT_cement_report.pdf"

            await page.pdf(
                path=output_path,
                format='Letter',
                margin={'top': '0.5in', 'right': '0.5in', 'bottom': '0.5in', 'left': '0.5in'},
                print_background=True,
                prefer_css_page_size=True
            )

            await browser.close()

            print("✅ PERFECT PDF generated!")
            print(f"📁 Saved to: {output_path}")
            print("🎉 Professional quality with perfect charts!")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Try running the HTML fixer script first, or use Firefox to print the fixed HTML")


# Run it
if __name__ == "__main__":
    asyncio.run(generate_perfect_pdf())