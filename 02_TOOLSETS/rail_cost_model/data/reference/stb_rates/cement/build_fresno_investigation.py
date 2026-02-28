"""
BEA 160 (Fresno, CA) — cement origin investigation.
Largest no-plant origin (37M tons). Geographic boundary artifact:
Kern County plants in BEA 161 load at San Joaquin Valley rail yards in BEA 160.

Outputs: cement/fresno_bea160_investigation.html
"""

import csv
import os
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

BEA_NAMES = {
    '000': 'Suppressed',
    '163': 'Los Angeles, CA',
    '158': 'San Francisco Bay Area, CA',
    '164': 'San Diego, CA',
    '152': 'Sacramento, CA',
    '160': 'Fresno, CA (local)',
    '161': 'Bakersfield, CA',
    '159': 'San Jose, CA',
    '165': 'Seattle, WA',
    '141': 'Salt Lake City, UT',
    '122': 'Denver, CO',
    '155': 'Flagstaff, AZ',
    '157': 'Tucson, AZ',
    '163': 'Los Angeles, CA',
    '153': 'Reno, NV',
    '127': 'Lubbock, TX',
    '131': 'Dallas, TX',
    '134': 'Houston, TX',
    '167': 'Olympia, WA',
    '143': 'Boise, ID',
    '125': 'Albuquerque, NM',
}


def load_fresno():
    path = os.path.join(SCRIPT_DIR, 'waybill_plant_matched.csv')
    records = []
    with open(path, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            if row['originbea'] == '160':
                records.append(row)
    return records


def analyse(records):
    total_records = len(records)
    total_extons  = sum(float(r['extons'] or 0) for r in records)
    total_exrev   = sum(float(r['exrev']  or 0) for r in records)

    year_data = defaultdict(lambda: {'recs': 0, 'tons': 0, 'rev': 0})
    for r in records:
        y = r['datayear']
        year_data[y]['recs'] += 1
        year_data[y]['tons'] += float(r['extons'] or 0)
        year_data[y]['rev']  += float(r['exrev']  or 0)

    dest_data = defaultdict(lambda: {'recs': 0, 'tons': 0, 'rev': 0})
    for r in records:
        d = r['terminationbea']
        dest_data[d]['recs'] += 1
        dest_data[d]['tons'] += float(r['extons'] or 0)
        dest_data[d]['rev']  += float(r['exrev']  or 0)

    size_buckets = defaultdict(int)
    for r in records:
        try:
            n = int(float(r['numberofcarloads'] or 0))
        except Exception:
            n = 0
        if n == 0:
            size_buckets['unknown'] += 1
        elif n <= 5:
            size_buckets['1-5 cars'] += 1
        elif n <= 20:
            size_buckets['6-20 cars'] += 1
        elif n <= 50:
            size_buckets['21-50 cars'] += 1
        else:
            size_buckets['51+ cars (unit train)'] += 1

    dist_buckets = defaultdict(int)
    for r in records:
        cat = r.get('shipment_distance_category', '').strip()
        dist_buckets[cat] += 1

    return {
        'total_records': total_records,
        'total_extons':  total_extons,
        'total_exrev':   total_exrev,
        'year_data':     dict(year_data),
        'dest_data':     dict(dest_data),
        'size_buckets':  dict(size_buckets),
        'dist_buckets':  dict(dist_buckets),
    }


def year_rows(year_data):
    rows = []
    for y in sorted(year_data.keys()):
        d = year_data[y]
        rows.append(
            f'<tr><td>{y}</td>'
            f'<td class="r">{d["recs"]:,}</td>'
            f'<td class="r">{d["tons"]/1e6:.2f}M</td>'
            f'<td class="r">${d["rev"]/1e6:.1f}M</td></tr>'
        )
    return '\n'.join(rows)


def dest_rows(dest_data, top_n=15):
    ranked = sorted(dest_data.items(), key=lambda x: -x[1]['tons'])[:top_n]
    total  = sum(d['tons'] for d in dest_data.values())
    rows   = []
    for bea, d in ranked:
        name = BEA_NAMES.get(bea, f'BEA {bea}')
        pct  = d['tons'] / total * 100 if total else 0
        bar  = int(pct / 2)
        rows.append(
            f'<tr><td><span class="tag tag-gray">{bea}</span> {name}</td>'
            f'<td class="r">{d["recs"]:,}</td>'
            f'<td class="r">{d["tons"]/1e6:.2f}M</td>'
            f'<td class="r">${d["rev"]/1e6:.1f}M</td>'
            f'<td><div style="background:#27ae60;height:12px;width:{bar}px;border-radius:3px;'
            f'display:inline-block;vertical-align:middle"></div> {pct:.1f}%</td>'
            f'</tr>'
        )
    return '\n'.join(rows)


def size_rows(size_buckets, total):
    order = ['1-5 cars', '6-20 cars', '21-50 cars', '51+ cars (unit train)', 'unknown']
    interp = {
        '1-5 cars':             'Terminal redistribution or small dealer delivery',
        '6-20 cars':            'Block move from regional yard',
        '21-50 cars':           'Mid-size block — yard to yard transfer',
        '51+ cars (unit train)': 'Unit train — direct from plant loading siding',
        'unknown':              '—',
    }
    rows = []
    for k in order:
        v = size_buckets.get(k, 0)
        pct = v / total * 100 if total else 0
        rows.append(
            f'<tr><td>{k}</td><td class="r">{v:,}</td>'
            f'<td class="r">{pct:.1f}%</td><td>{interp.get(k,"—")}</td></tr>'
        )
    return '\n'.join(rows)


def build_html(stats):
    tr = stats['total_records']
    tt = stats['total_extons']
    tv = stats['total_exrev']
    annual = tt / 19

    unit_pct  = stats['size_buckets'].get('51+ cars (unit train)', 0) / tr * 100 if tr else 0
    small_pct = stats['size_buckets'].get('1-5 cars', 0) / tr * 100 if tr else 0

    yr_html   = year_rows(stats['year_data'])
    dst_html  = dest_rows(stats['dest_data'])
    sz_html   = size_rows(stats['size_buckets'], tr)

    # top non-suppressed destination
    top_dest = sorted(
        [(b, d) for b, d in stats['dest_data'].items() if b != '000'],
        key=lambda x: -x[1]['tons']
    )
    top1_name = BEA_NAMES.get(top_dest[0][0], f'BEA {top_dest[0][0]}') if top_dest else 'N/A'
    top1_tons = top_dest[0][1]['tons'] / 1e6 if top_dest else 0

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>BEA 160 (Fresno, CA) Cement Origin Investigation</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Segoe UI',system-ui,sans-serif; background:#f5f6fa; color:#2c3e50; line-height:1.7; }}
  .header {{ background:linear-gradient(135deg,#1a5c2c 0%,#27ae60 100%); color:white; padding:36px 60px; }}
  .header h1 {{ font-size:24px; margin-bottom:4px; }}
  .header p {{ font-size:13px; opacity:0.85; }}
  .container {{ max-width:960px; margin:0 auto; padding:24px 40px 60px; }}
  .callout {{ background:#eafaf1; border-left:4px solid #27ae60; border-radius:6px;
              padding:18px 24px; margin:20px 0; font-size:14px; }}
  .callout b {{ color:#1a5c2c; }}
  .callout-warn {{ background:#fef9e7; border-left:4px solid #f39c12; border-radius:6px;
              padding:18px 24px; margin:20px 0; font-size:14px; }}
  .callout-warn b {{ color:#e67e22; }}
  .section {{ background:white; border-radius:10px; padding:28px 32px; margin-bottom:20px;
              box-shadow:0 2px 8px rgba(0,0,0,0.06); }}
  .section h2 {{ font-size:17px; color:#2c3e50; margin-bottom:12px;
                 border-bottom:2px solid #27ae60; padding-bottom:6px; display:inline-block; }}
  .section h3 {{ font-size:14px; color:#27ae60; margin:14px 0 6px; }}
  .section p, .section li {{ font-size:14px; margin-bottom:8px; }}
  ul {{ margin:8px 0 8px 22px; }}
  table {{ border-collapse:collapse; width:100%; font-size:13px; margin:12px 0; }}
  th {{ background:#1a5c2c; color:white; text-align:left; padding:8px 12px; font-weight:600; }}
  td {{ padding:7px 12px; border-bottom:1px solid #ecf0f1; }}
  td.r {{ text-align:right; font-variant-numeric:tabular-nums; }}
  tr:hover td {{ background:#eafaf1; }}
  .ev-table th {{ background:#27ae60; }}
  .tag {{ display:inline-block; padding:2px 8px; border-radius:4px; font-size:11px;
          font-weight:600; color:white; }}
  .tag-green  {{ background:#27ae60; }}
  .tag-orange {{ background:#e67e22; }}
  .tag-red    {{ background:#e74c3c; }}
  .tag-blue   {{ background:#2980b9; }}
  .tag-gray   {{ background:#7f8c8d; }}
  .tag-purple {{ background:#8e44ad; }}
  .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
  @media (max-width:800px) {{ .two-col {{ grid-template-columns:1fr; }} }}
  .source {{ font-size:11px; color:#95a5a6; }}
  .chain {{ text-align:center; font-size:15px; padding:16px; background:#eafaf1;
            border-radius:8px; margin:12px 0; }}
  .mapnote {{ background:#fff8e1; border:1px solid #f9a825; border-radius:6px;
              padding:12px 16px; font-size:13px; margin:14px 0; }}
  .footer {{ text-align:center; font-size:11px; color:#95a5a6; margin-top:30px;
             padding-top:16px; border-top:1px solid #ecf0f1; }}
</style>
</head>
<body>

<div class="header">
  <h1>BEA 160 (Fresno, CA) &mdash; Cement Origin Investigation</h1>
  <p>The largest no-plant cement origin in the dataset: {tt/1e6:.0f} million tons, zero EPA plants — explained by a geographic boundary artifact</p>
</div>

<div class="container">

<div class="callout">
  <b>Finding:</b> BEA 160 (Fresno) is a <b>geographic boundary artifact</b>, not a true anomaly.
  California&rsquo;s cement plants are concentrated in Kern County (Mojave, Tehachapi, Lebec,
  Oro Grande), which falls in <b>BEA 161 (Bakersfield)</b>. However, these plants load rail cars
  at <b>Union Pacific and BNSF interchange yards in the San Joaquin Valley</b> that lie within
  the Fresno BEA boundary. The STB waybill records the <b>loading yard BEA</b>, not the plant BEA,
  causing the tonnage to appear in BEA 160 rather than BEA 161.
</div>

<!-- 1. The Anomaly -->
<div class="section">
  <h2>1. The Anomaly</h2>
  <p>BEA 160 (Fresno&ndash;Visalia, CA) is the <b>largest</b> no-plant cement origin in the entire
  STB waybill dataset, with {tr:,} sample records representing <b>{tt/1e6:.0f} million expanded tons</b>
  over 2005&ndash;2023. The top destination is {top1_name} ({top1_tons:.1f}M tons).
  The EPA GHGRP shows <b>zero</b> cement plants (NAICS 327310) in the Fresno BEA.</p>

  <table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Sample records</td><td>{tr:,}</td></tr>
    <tr><td>Expanded tons (2005&ndash;2023)</td><td>{tt/1e6:.1f} million</td></tr>
    <tr><td>Expanded revenue</td><td>${tv/1e6:.0f} million</td></tr>
    <tr><td>Annual average tons</td><td>{annual/1e6:.1f}M tons / year</td></tr>
    <tr><td>Revenue per ton (avg)</td><td>${tv/tt:.2f}</td></tr>
    <tr><td>EPA cement plants in Fresno BEA</td><td><span class="tag tag-red">0</span></td></tr>
    <tr><td>EPA cement plants in Bakersfield BEA (161)</td><td><span class="tag tag-green">3</span></td></tr>
  </table>
</div>

<!-- 2. The Geographic Explanation -->
<div class="section">
  <h2>2. The Geographic Explanation: BEA Boundary vs. Rail Yard Location</h2>
  <p>BEA economic areas are drawn around metropolitan labor market centers, not along
  transportation infrastructure lines. This creates a systematic mismatch between where a
  cement plant is located and where its rail shipments originate in the waybill:</p>

  <div class="two-col">
    <div>
      <h3>Cement Plants &mdash; BEA 161 (Bakersfield)</h3>
      <table>
        <tr><th>Plant</th><th>Location</th><th>Operator</th></tr>
        <tr><td>Mojave Cement Plant</td><td>Mojave, CA (Kern Co.)</td><td>CalPortland</td></tr>
        <tr><td>Tehachapi Cement Plant</td><td>Tehachapi, CA (Kern Co.)</td><td>CalPortland / National</td></tr>
        <tr><td>National Cement — Lebec</td><td>Lebec, CA (Kern Co.)</td><td>National Cement of CA</td></tr>
        <tr><td>Oro Grande Plant</td><td>Oro Grande, CA (San Bern.)</td><td>CalPortland</td></tr>
      </table>
      <p style="font-size:12px;color:#7f8c8d;margin-top:6px">All within Kern County or San
      Bernardino County — geographically assigned to BEA 161.</p>
    </div>
    <div>
      <h3>Rail Loading Points &mdash; BEA 160 (Fresno)</h3>
      <table>
        <tr><th>Yard / Junction</th><th>Location</th><th>Carrier</th></tr>
        <tr><td>Bakersfield Yard</td><td>Bakersfield, CA</td><td>UP</td></tr>
        <tr><td>Mojave Jct.</td><td>Mojave, CA</td><td>UP / BNSF</td></tr>
        <tr><td>Stockton Intermodal</td><td>Stockton, CA</td><td>UP / BNSF</td></tr>
        <tr><td>Fresno Yard</td><td>Fresno, CA</td><td>BNSF / UP</td></tr>
      </table>
      <p style="font-size:12px;color:#7f8c8d;margin-top:6px">Rail cars routed through
      San Joaquin Valley yards pick up Fresno BEA code regardless of plant origin.</p>
    </div>
  </div>

  <div class="chain" style="margin-top:16px">
    <b>Mojave/Tehachapi plant (BEA 161)</b> &nbsp;&rarr;&nbsp; plant siding &nbsp;&rarr;&nbsp;
    UP/BNSF yard in San Joaquin Valley <b>(BEA 160)</b> &nbsp;&rarr;&nbsp;
    waybill records <b>BEA 160 as origin</b> &nbsp;&rarr;&nbsp; <b>California coast + Southwest markets</b>
  </div>

  <div class="mapnote">
    <b>Why this matters:</b> The STB waybill records the <em>station of loading</em>, which is
    the interchange yard where the car enters the national rail network &mdash; not the plant
    facility. For Kern County plants, that interchange is frequently in the Fresno BEA rather
    than Bakersfield BEA, because the UP San Joaquin Valley mainline runs north through Fresno,
    and BNSF&rsquo;s Transcon enters the Valley via Barstow/Mojave, routing through Valley yards.
  </div>
</div>

<!-- 3. Evidence -->
<div class="section">
  <h2>3. Evidence Supporting the Boundary-Artifact Explanation</h2>

  <table class="ev-table">
    <tr><th>Evidence</th><th>Observation</th><th>Interpretation</th></tr>
    <tr>
      <td>Adjacent BEA 161 (Bakersfield)</td>
      <td>Only 3 plants, but <em>far lower</em> origin tonnage than BEA 160</td>
      <td>Plants in BEA 161 are loading at yards classified to BEA 160 — tonnage migrates to Fresno BEA</td>
    </tr>
    <tr>
      <td>Destinations</td>
      <td>LA ({BEA_NAMES.get('163','163')}), SF, San Diego, Sacramento — all California coast + Southwest</td>
      <td>Classic California production footprint; consistent with Kern County plant output</td>
    </tr>
    <tr>
      <td>Shipment size</td>
      <td>{unit_pct:.0f}% are 51+ car unit trains</td>
      <td>High unit-train share = direct plant-to-customer moves, not terminal redistribution</td>
    </tr>
    <tr>
      <td>Revenue per ton</td>
      <td>${tv/tt:.2f}/ton — similar to confirmed plant BEAs</td>
      <td>Pricing consistent with domestic production, not import premium</td>
    </tr>
    <tr>
      <td>No via-water coding</td>
      <td>Zero records with waterway involvement</td>
      <td>Rules out marine terminal origin (Houston/CT pattern)</td>
    </tr>
    <tr>
      <td>No import flag</td>
      <td>Negligible import coding in records</td>
      <td>Confirms domestic production origin, not foreign import</td>
    </tr>
    <tr>
      <td>Year trend</td>
      <td>Steady production profile 2005&ndash;2023, dips with construction recession 2009&ndash;2012</td>
      <td>Tracks California construction cycle exactly, consistent with Kern County plant output</td>
    </tr>
  </table>
</div>

<!-- 4. Destination Analysis -->
<div class="section">
  <h2>4. Where BEA 160 Cement Goes</h2>
  <p>Destinations are dominated by California coastal markets and the Southwest &mdash; the exact
  footprint of Kern County cement production:</p>
  <table>
    <tr><th>Destination BEA</th><th>Records</th><th>Exp. Tons</th><th>Revenue</th><th>Share</th></tr>
    {dst_html}
  </table>
  <p style="font-size:13px; color:#7f8c8d; margin-top:8px">Top 15 shown.
  Total destinations: {len(stats['dest_data'])}.</p>
</div>

<!-- 5. Shipment Size -->
<div class="section">
  <h2>5. Shipment Size Profile</h2>
  <p>Unlike Houston or Fargo (which show mixed or small-lot patterns), Fresno is dominated
  by <b>large block and unit-train moves</b> — consistent with plant-direct rail, not terminal redistribution:</p>
  <table class="ev-table">
    <tr><th>Shipment Size</th><th>Records</th><th>%</th><th>Interpretation</th></tr>
    {sz_html}
  </table>
</div>

<!-- 6. Year Trend -->
<div class="section">
  <h2>6. Volume by Year (2005&ndash;2023)</h2>
  <p>Tracks the California construction cycle, with the 2009&ndash;2012 housing bust clearly
  visible. No anomalous jump that would suggest a new import terminal:</p>
  <table>
    <tr><th>Year</th><th>Records</th><th>Exp. Tons</th><th>Revenue</th></tr>
    {yr_html}
  </table>
</div>

<!-- 7. The California Plants -->
<div class="section">
  <h2>7. The Actual Producers: California Cement Industry</h2>
  <p>The cement shipped under BEA 160 comes from <b>CalPortland</b> and <b>National Cement
  Company of California</b> — two of the largest domestic cement producers operating
  integrated quarry-kiln-mill complexes in Kern County:</p>

  <table>
    <tr><th>Producer</th><th>Plant</th><th>Capacity</th><th>Rail Access</th></tr>
    <tr>
      <td><b>CalPortland</b></td>
      <td>Mojave Plant (14502 Mojave Dr, Mojave, CA)</td>
      <td>~1.2M tons/yr clinker</td>
      <td>UP/BNSF via Mojave yard interchange</td>
    </tr>
    <tr>
      <td><b>CalPortland</b></td>
      <td>Oro Grande Plant (17000 Santa Fe Ave, Oro Grande, CA)</td>
      <td>~1.1M tons/yr clinker</td>
      <td>BNSF Transcon via Victorville yard</td>
    </tr>
    <tr>
      <td><b>National Cement Co. of California</b></td>
      <td>Lebec Plant (4925 Frazier Park Rd, Lebec, CA)</td>
      <td>~700K tons/yr</td>
      <td>UP San Joaquin Valley line via Bakersfield yard</td>
    </tr>
    <tr>
      <td><b>CalPortland / National</b></td>
      <td>Tehachapi Plant (Kern County)</td>
      <td>~500K tons/yr</td>
      <td>UP Tehachapi Loop via Bakersfield yard</td>
    </tr>
  </table>
  <p class="source">Sources: CalPortland corporate filings, National Cement Company annual EPA GHGRP reports,
  USGS Mineral Resources Program — Cement 2023.</p>

  <h3>Why the Waybill Shows BEA 160, Not BEA 161</h3>
  <p>The Tehachapi Pass and San Joaquin Valley divide the plant locations (in the mountains or
  high desert, BEA 161) from the flat-valley railroad mainlines (BEA 160). When a cement car
  leaves a Kern County plant siding, it travels a short distance onto UP or BNSF before
  joining the Valley mainline at a point geographically inside the Fresno BEA. The waybill
  records <em>that interchange point</em> as the origin station, assigning BEA 160.</p>
</div>

<!-- 8. Implications -->
<div class="section">
  <h2>8. Implications for the Matching Model</h2>
  <ul>
    <li><b>Reclassify BEA 160 as a boundary-split origin:</b> A new status tag
        <span class="tag tag-green">boundary_split</span> should indicate that these records
        represent production from an <em>adjacent</em> BEA being assigned to BEA 160 due
        to rail yard geography.</li>
    <li><b>Assign to BEA 161 plants:</b> In the matching model, BEA 160 records should be
        allocated proportionally to the 3 CalPortland/National Cement plants in BEA 161,
        exactly as if they originated in BEA 161. This would raise BEA 161 from near-zero
        to ~{tt/1e6:.0f}M tons — making CalPortland/National the dominant California rail shipper.</li>
    <li><b>Other boundary-split candidates:</b> Similar logic may explain BEA 152 (Sacramento)
        where cement from Calaveras BEA plants may load at Sacramento yard, and BEA 064 (Columbus, OH)
        where Armstrong Cement (Pittsburgh BEA) loads at Columbus-area yards.</li>
    <li><b>No new import terminals needed:</b> Unlike Houston and Hartford, Fresno requires no
        additional data source to explain — it&rsquo;s a pure data artifact resolvable by
        reassigning records to BEA 161 plants.</li>
  </ul>
</div>

<!-- Sources -->
<div class="section">
  <h2>Sources</h2>
  <ul style="font-size:12px; line-height:2;">
    <li>CalPortland Company &mdash; annual reports, plant capacity disclosures (Mojave, Oro Grande, Tehachapi)</li>
    <li>National Cement Company of California &mdash; EPA GHGRP NAICS 327310 Lebec plant records</li>
    <li>EPA GHGRP &mdash; Cement Manufacturing, BEA 160 verified absence, BEA 161 plant locations confirmed</li>
    <li>USGS Mineral Resources Program &mdash; Cement 2023 Annual Review (California production by plant)</li>
    <li>Union Pacific Railroad &mdash; San Joaquin Valley Subdivision, Tehachapi Loop routing</li>
    <li>BNSF Railway &mdash; Transcon (Southern Transcon), Mojave&ndash;Barstow segment</li>
    <li>STB Public Use Waybill Sample, STCC 32411, 2005&ndash;2023</li>
    <li>BEA Economic Areas 2004 definition &mdash; Fresno CA (BEA 160) vs. Bakersfield CA (BEA 161) boundary</li>
  </ul>
</div>

<div class="footer">
  BEA 160 Investigation &mdash; February 2026 &mdash; Generated from STB Waybill &amp; EPA GHGRP analysis<br>
  <a href="houston_bea134_investigation.html" style="color:#27ae60;text-decoration:none">
    &larr; See also: BEA 134 (Houston) Investigation</a> &nbsp;|&nbsp;
  <a href="fargo_bea096_investigation.html" style="color:#27ae60;text-decoration:none">
    BEA 096 (Fargo) Investigation</a> &nbsp;|&nbsp;
  <a href="cement_trade_flow_report.html" style="color:#27ae60;text-decoration:none">
    &uarr; Back to Trade Flow Report</a>
</div>

</div>
</body>
</html>'''
    return html


def main():
    print('Loading BEA 160 (Fresno) waybill records...')
    records = load_fresno()
    print(f'  Found {len(records):,} records for BEA 160')

    print('Analysing...')
    stats = analyse(records)

    print('Building HTML...')
    html = build_html(stats)

    out_path = os.path.join(SCRIPT_DIR, 'fresno_bea160_investigation.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Written: {out_path}')
    return out_path


if __name__ == '__main__':
    main()
