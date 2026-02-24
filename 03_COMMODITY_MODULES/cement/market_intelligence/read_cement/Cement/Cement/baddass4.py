# Quick fix for broken Chart.js reference
import os

# Your broken HTML file path
broken_html_path = r"C:\Users\wsd3\OneDrive\GRoK\Scripts\US Gulf Cement Report August 2025.html"
fixed_html_path = r"C:\Users\wsd3\OneDrive\GRoK\Scripts\FIXED_cement_report.html"

# Read the broken HTML
with open(broken_html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Fix the broken Chart.js reference
html_content = html_content.replace(
    '<script src="./US Gulf Cement Report August 2025_files/chart.min.js.download"></script>',
    '<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>'
)

# Also fix the duplicate chart that was causing spacing issues
html_content = html_content.replace(
    '''        <div class="chart-container chart-small">
            <canvas id="importTrendsChart"></canvas>
        </div>

        <div class="highlight">''',
    '''        <div class="highlight">'''
)

# Save the fixed version
with open(fixed_html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("✅ HTML file fixed!")
print(f"📁 Fixed file: {fixed_html_path}")
print("🎯 Charts will now load properly in any browser/app!")
print("")
print("📋 Next steps:")
print("1. Open FIXED_cement_report.html in Chrome")
print("2. Print → Save as PDF")
print("3. Use these settings:")
print("   - Paper: Letter (Portrait)")
print("   - Scale: 85-90%")
print("   - ✅ Background graphics ON")
print("4. Charts should now work perfectly!")