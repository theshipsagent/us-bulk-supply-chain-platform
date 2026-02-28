# Perfect PDF Generator using Puppeteer
# Install: pip install pyppeteer

import asyncio
from pyppeteer import launch
import os


async def generate_perfect_pdf():
    print("🚀 Starting PDF generation...")

    browser = await launch({
        'headless': True,
        'args': ['--no-sandbox', '--disable-setuid-sandbox']
    })

    page = await browser.newPage()

    # Use the ORIGINAL working HTML file (not the saved one)
    html_path = r"C:\Users\wsd3\OneDrive\GRoK\Scripts\beautiful_gulf_cement_report.html"
    file_url = f"file:///{html_path.replace(chr(92), '/')}"

    print(f"📄 Loading HTML from: {file_url}")

    # Load your HTML file
    await page.goto(file_url, {'waitUntil': 'networkidle0'})

    # Wait for charts to fully load
    print("📊 Waiting for charts to render...")
    await page.waitForTimeout(5000)

    # Generate PDF with perfect settings
    output_path = r"C:\Users\wsd3\OneDrive\GRoK\Scripts\PERFECT_cement_report.pdf"

    await page.pdf({
        'path': output_path,
        'format': 'Letter',
        'printBackground': True,
        'margin': {
            'top': '0.5in',
            'right': '0.5in',
            'bottom': '0.5in',
            'left': '0.5in'
        },
        'preferCSSPageSize': True,
        'displayHeaderFooter': False
    })

    await browser.close()

    print("✅ PERFECT PDF generated!")
    print(f"📁 Saved to: {output_path}")
    print("🎉 This PDF will have perfect charts, formatting, and pagination!")


# Run it
if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(generate_perfect_pdf())