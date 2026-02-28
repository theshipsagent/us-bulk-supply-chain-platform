"""Parse CBP Appendix E (Schedule D) PDF into port code + CBP name pairs."""
import re
import csv
import sys
import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')

pdf = pdfplumber.open('data/reference/cbp_appendix_e_schedule_d.pdf')
print(f"Pages: {len(pdf.pages)}")

# Extract all text
all_text = []
for page in pdf.pages:
    text = page.extract_text()
    if text:
        all_text.append(text)
pdf.close()

full_text = '\n'.join(all_text)

# Parse port codes: 4-digit code followed by port name
# Pattern: 4 digits at start of line, followed by space and name
port_pattern = re.compile(r'^(\d{4})\s+(.+?)$', re.MULTILINE)

ports = {}
for match in port_pattern.finditer(full_text):
    code = match.group(1)
    name = match.group(2).strip()
    # Skip page numbers, dates, etc.
    if name.startswith('Appendix') or name.startswith('February') or name.startswith('April'):
        continue
    if len(name) < 3:
        continue
    ports[code] = name

print(f"CBP Appendix E port codes extracted: {len(ports)}")

# Write to CSV
outfile = 'data/reference/cbp_appendix_e_ports.csv'
with open(outfile, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['port_code', 'cbp_port_name'])
    for code in sorted(ports.keys()):
        writer.writerow([code, ports[code]])

print(f"Written: {outfile}")

# Show first 20 and last 10
print("\nFirst 20 entries:")
for code in sorted(ports.keys())[:20]:
    print(f"  {code}: {ports[code]}")

print("\nLast 10 entries:")
for code in sorted(ports.keys())[-10:]:
    print(f"  {code}: {ports[code]}")

# Compare with Census Schedule D
census_sd = {}
with open('data/reference/census_schedule_d.csv', 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        census_sd[row['port_code']] = row['port_name']

cbp_codes = set(ports.keys())
census_codes = set(census_sd.keys())

only_cbp = cbp_codes - census_codes
only_census = census_codes - cbp_codes
both = cbp_codes & census_codes

print(f"\nComparison with Census Schedule D:")
print(f"  In both:       {len(both)}")
print(f"  Only in CBP:   {len(only_cbp)}")
print(f"  Only in Census:{len(only_census)}")

if only_cbp:
    print(f"\n  CBP-only codes:")
    for code in sorted(only_cbp):
        print(f"    {code}: {ports[code]}")

if only_census:
    print(f"\n  Census-only codes:")
    for code in sorted(only_census):
        print(f"    {code}: {census_sd[code]}")

# Show name differences for shared codes
print(f"\nName differences (first 15):")
diffs = 0
for code in sorted(both):
    cbp_name = ports[code].upper().strip()
    census_name = census_sd[code].upper().strip()
    if cbp_name != census_name:
        diffs += 1
        if diffs <= 15:
            print(f"  {code}: CBP='{ports[code]}' vs Census='{census_sd[code]}'")
print(f"  Total name differences: {diffs}")
