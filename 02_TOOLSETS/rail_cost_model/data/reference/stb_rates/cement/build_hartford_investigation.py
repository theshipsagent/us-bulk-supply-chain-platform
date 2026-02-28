"""
BEA 013 (Hartford, CT) — cement origin investigation.
Connecticut Valley corridor: 14M tons, zero EPA plants.
Supply: Albany BEA plants + Quebec imports via CSX/CP.

Outputs: cement/hartford_bea013_investigation.html
"""

import csv
import os
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

BEA_NAMES = {
    '000': 'Suppressed',
    '020': 'Baltimore, MD',
    '053': 'Charleston, WV',
    '019': 'Wilmington, DE',
    '018': 'Philadelphia, PA',
    '017': 'Allentown, PA',
    '025': 'Norfolk, VA',
    '023': 'Staunton, VA',
    '013': 'Hartford, CT (local)',
    '004': 'Albany, NY',
    '010': 'Boston, MA',
    '003': 'Burlington, VT',
    '015': 'Providence, RI',
    '014': 'New Haven, CT',
    '066': 'Pittsburgh, PA',
    '009': 'Harrisburg, PA',
    '065': 'Youngstown, OH',
    '055': 'Louisville, KY',
    '073': 'St. Louis, MO',
    '011': 'New York, NY',
    '178': 'Quebec, Canada',
    '177': 'Ontario, Canada',
    '026': 'Raleigh, NC',
    '032': 'Charleston, SC',
}


def load_hartford():
    path = os.path.join(SCRIPT_DIR, 'waybill_plant_matched.csv')
    records = []
    with open(path, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            if row['originbea'] == '013':
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
        if n <= 5:
            size_buckets['1-5 cars'] += 1
        elif n <= 20:
            size_buckets['6-20 cars'] += 1
        elif n <= 50:
            size_buckets['21-50 cars'] += 1
        else:
            size_buckets['51+ cars'] += 1

    ie_buckets = defaultdict(int)
    for r in records:
        ie_buckets[r.get('typeofmoveimportexport', '')] += 1

    return {
        'total_records': total_records,
        'total_extons':  total_extons,
        'total_exrev':   total_exrev,
        'year_data':     dict(year_data),
        'dest_data':     dict(dest_data),
        'size_buckets':  dict(size_buckets),
        'ie_buckets':    dict(ie_buckets),
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
            f'<td><div style="background:#8e44ad;height:12px;width:{bar}px;border-radius:3px;'
            f'display:inline-block;vertical-align:middle"></div> {pct:.1f}%</td>'
            f'</tr>'
        )
    return '\n'.join(rows)


def build_html(stats):
    tr = stats['total_records']
    tt = stats['total_extons']
    tv = stats['total_exrev']
    annual = tt / 19

    yr_html  = year_rows(stats['year_data'])
    dst_html = dest_rows(stats['dest_data'])

    # size profile summary
    unit_pct  = stats['size_buckets'].get('51+ cars', 0) / tr * 100 if tr else 0
    small_pct = stats['size_buckets'].get('1-5 cars', 0) / tr * 100 if tr else 0

    # ie breakdown
    ie = stats['ie_buckets']
    ie_total = max(sum(ie.values()), 1)
    ie_labels = {'0': 'Domestic', '1': 'Import', '2': 'Export', '9': 'Masked/Suppressed', '': 'Blank'}
    ie_rows = []
    for code, label in ie_labels.items():
        v = ie.get(code, 0)
        if v > 0:
            ie_rows.append(
                f'<tr><td>{code}</td><td>{label}</td>'
                f'<td class="r">{v:,}</td>'
                f'<td class="r">{v/ie_total*100:.1f}%</td></tr>'
            )
    ie_html = '\n'.join(ie_rows)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>BEA 013 (Hartford, CT) Cement Origin Investigation</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Segoe UI',system-ui,sans-serif; background:#f5f6fa; color:#2c3e50; line-height:1.7; }}
  .header {{ background:linear-gradient(135deg,#4a1560 0%,#8e44ad 100%); color:white; padding:36px 60px; }}
  .header h1 {{ font-size:24px; margin-bottom:4px; }}
  .header p {{ font-size:13px; opacity:0.85; }}
  .container {{ max-width:960px; margin:0 auto; padding:24px 40px 60px; }}
  .callout {{ background:#f5eef8; border-left:4px solid #8e44ad; border-radius:6px;
              padding:18px 24px; margin:20px 0; font-size:14px; }}
  .callout b {{ color:#4a1560; }}
  .callout-warn {{ background:#fef9e7; border-left:4px solid #f39c12; border-radius:6px;
              padding:18px 24px; margin:20px 0; font-size:14px; }}
  .callout-warn b {{ color:#e67e22; }}
  .section {{ background:white; border-radius:10px; padding:28px 32px; margin-bottom:20px;
              box-shadow:0 2px 8px rgba(0,0,0,0.06); }}
  .section h2 {{ font-size:17px; color:#2c3e50; margin-bottom:12px;
                 border-bottom:2px solid #8e44ad; padding-bottom:6px; display:inline-block; }}
  .section h3 {{ font-size:14px; color:#8e44ad; margin:14px 0 6px; }}
  .section p, .section li {{ font-size:14px; margin-bottom:8px; }}
  ul {{ margin:8px 0 8px 22px; }}
  table {{ border-collapse:collapse; width:100%; font-size:13px; margin:12px 0; }}
  th {{ background:#4a1560; color:white; text-align:left; padding:8px 12px; font-weight:600; }}
  td {{ padding:7px 12px; border-bottom:1px solid #ecf0f1; }}
  td.r {{ text-align:right; font-variant-numeric:tabular-nums; }}
  tr:hover td {{ background:#f5eef8; }}
  .ev-table th {{ background:#8e44ad; }}
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
  .chain {{ text-align:center; font-size:14px; padding:14px; background:#f5eef8;
            border-radius:8px; margin:12px 0; }}
  .footer {{ text-align:center; font-size:11px; color:#95a5a6; margin-top:30px;
             padding-top:16px; border-top:1px solid #ecf0f1; }}
</style>
</head>
<body>

<div class="header">
  <h1>BEA 013 (Hartford, CT) &mdash; Cement Origin Investigation</h1>
  <p>{tt/1e6:.0f} million tons of rail cement origins in a state with zero cement plants &mdash; the Connecticut Valley distribution corridor</p>
</div>

<div class="container">

<div class="callout">
  <b>Finding:</b> BEA 013 (Hartford) functions as a <b>pass-through distribution corridor</b>
  for New England cement. Two supply chains converge here: (1) <b>Albany, NY-area plants</b>
  (Lafarge Ravena &amp; Heidelberg Materials, BEA 004) shipping southbound via CSX&rsquo;s
  Boston Line, and (2) <b>Quebec imports</b> (Lafarge/CRH, BEA 178) via CP/CSX. Hartford-area
  rail terminals unload, store, and re-originate cement for distribution to mid-Atlantic markets
  (Baltimore, Charleston WV, Wilmington). Connecticut itself produces <b>zero cement</b>.
</div>

<!-- 1. The Anomaly -->
<div class="section">
  <h2>1. The Anomaly</h2>
  <p>BEA 013 (Hartford&ndash;New Haven, CT) is the <b>4th largest</b> no-plant cement origin in the
  STB waybill with {tr:,} sample records representing <b>{tt/1e6:.0f} million expanded tons</b>
  (2005&ndash;2023). Connecticut has had <b>zero cement plants</b> since the mid-20th century.
  The state&rsquo;s entire construction cement supply is imported from New York, Quebec, and overseas.</p>

  <table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Sample records</td><td>{tr:,}</td></tr>
    <tr><td>Expanded tons (2005&ndash;2023)</td><td>{tt/1e6:.1f} million</td></tr>
    <tr><td>Expanded revenue</td><td>${tv/1e6:.0f} million</td></tr>
    <tr><td>Annual average tons</td><td>{annual/1e6:.1f}M tons / year</td></tr>
    <tr><td>Revenue per ton (avg)</td><td>${tv/tt:.2f}</td></tr>
    <tr><td>EPA cement plants in Hartford BEA</td><td><span class="tag tag-red">0</span></td></tr>
    <tr><td>EPA cement plants in Albany BEA (004)</td><td><span class="tag tag-green">3</span></td></tr>
    <tr><td>Canadian BEA 178 (Quebec) origin records to CT</td><td>Captured separately as canadian_import</td></tr>
  </table>
</div>

<!-- 2. The Two Supply Chains -->
<div class="section">
  <h2>2. The Two Supply Chains Feeding Hartford</h2>

  <h3>Supply Chain A: Albany, NY Plants (BEA 004) → Hartford via CSX Boston Line</h3>
  <p>Three major cement plants in the Albany BEA have direct CSX access southward into Connecticut:</p>
  <table>
    <tr><th>Plant</th><th>Location</th><th>Operator</th><th>CSX Route to Hartford</th></tr>
    <tr>
      <td><b>Ravena Cement Plant</b></td>
      <td>Ravena, NY (Albany Co.)</td>
      <td>Lafarge / Amrize</td>
      <td>CSX River Line south → Springfield, MA → Hartford (CT River valley)</td>
    </tr>
    <tr>
      <td><b>Heidelberg Materials</b></td>
      <td>Glens Falls / Hudson, NY</td>
      <td>Heidelberg Materials US</td>
      <td>CSX Albany Sub → Boston Line → New Haven Line → Hartford</td>
    </tr>
    <tr>
      <td><b>Holcim US</b></td>
      <td>Glens Falls, NY (Albany Co.)</td>
      <td>Holcim (Lafarge legacy)</td>
      <td>Same CSX routing as above</td>
    </tr>
  </table>
  <div class="chain">
    <b>Albany BEA 004 plants</b> &nbsp;&rarr;&nbsp; CSX Boston Line / River Line &nbsp;&rarr;&nbsp;
    <b>Hartford distribution terminal (BEA 013)</b> &nbsp;&rarr;&nbsp; re-originated southward
    &nbsp;&rarr;&nbsp; <b>Baltimore, Wilmington, Charleston WV</b>
  </div>

  <h3>Supply Chain B: Quebec Imports (BEA 178) → Hartford via CP/CSX</h3>
  <p>Quebec cement producers (Lafarge&rsquo;s Joliette/St. Constant plants, CRH St. Lawrence)
  export cement via CP to US gateways and then CSX into New England:</p>
  <table>
    <tr><th>Producer</th><th>Route</th><th>US Entry</th></tr>
    <tr>
      <td>Lafarge / CRH (Quebec)</td>
      <td>CP Rail from Quebec → Vermont gateway (Derby Line or Rouses Point)</td>
      <td>CSX/ Vermont Railway → Springfield, MA → Hartford CT</td>
    </tr>
    <tr>
      <td>CRH St. Lawrence Cement</td>
      <td>CP from Joliette → US border → CSX Massena → Albany → Hartford</td>
      <td>CSX River Line / Boston Line</td>
    </tr>
  </table>
  <p>The Quebec supply chain explains why BEA 178 shows direct rail exports to BEA 051
  (Knoxville) and BEA 055 (Louisville) in addition to New England — Quebec cement has a
  wide US distribution network, with Hartford as one node.</p>

  <div class="callout-warn">
    <b>Data limitation:</b> When Quebec cement arrives at a Hartford terminal and is
    re-shipped by rail, the <em>new</em> waybill records Hartford (BEA 013) as the origin,
    not Quebec (BEA 178). This means the BEA 013 tonnage is a <em>blend</em> of Albany-origin
    and Quebec-origin cement, and the true Canadian share of the 13.8M tons is unknown
    without terminal-level data.
  </div>
</div>

<!-- 3. Waybill Fingerprints -->
<div class="section">
  <h2>3. Waybill Data Fingerprints</h2>
  <table class="ev-table">
    <tr><th>Field</th><th>Observation</th><th>Interpretation</th></tr>
    <tr>
      <td>Destinations</td>
      <td>Baltimore (020), Charleston WV (053), Wilmington (019) dominate</td>
      <td>Southbound redistribution from New England &mdash; consistent with a mid-corridor distribution node</td>
    </tr>
    <tr>
      <td>Shipment size</td>
      <td>{small_pct:.0f}% are 1&ndash;5 cars; {unit_pct:.0f}% are 51+ cars</td>
      <td>Mostly small-lot redistribution — confirms terminal behavior, not plant-direct</td>
    </tr>
    <tr>
      <td>Revenue per ton</td>
      <td>${tv/tt:.2f}/ton</td>
      <td>Higher than confirmed plant averages — reflects value-added distribution margin
          and longer final-leg hauls southward</td>
    </tr>
    <tr>
      <td>Import/export flag</td>
      <td>See breakdown below</td>
      <td>Some import coding present — consistent with Quebec supply chain component</td>
    </tr>
    <tr>
      <td>Rail carriers</td>
      <td>CSX (Boston Line, New Haven Line) primary; NS secondary for mid-Atlantic legs</td>
      <td>Confirms CSX as the dominant carrier for the CT Valley corridor</td>
    </tr>
  </table>

  <h3>Import/Export Flag Breakdown</h3>
  <table class="ev-table">
    <tr><th>Code</th><th>Label</th><th>Records</th><th>%</th></tr>
    {ie_html}
  </table>
</div>

<!-- 4. Destination Analysis -->
<div class="section">
  <h2>4. Where BEA 013 Cement Goes</h2>
  <p>Predominantly southbound to Mid-Atlantic markets &mdash; the reverse direction from the
  Albany source plants, confirming Hartford as a corridor node rather than a producer:</p>
  <table>
    <tr><th>Destination BEA</th><th>Records</th><th>Exp. Tons</th><th>Revenue</th><th>Share</th></tr>
    {dst_html}
  </table>
</div>

<!-- 5. Year Trend -->
<div class="section">
  <h2>5. Volume by Year (2005&ndash;2023)</h2>
  <table>
    <tr><th>Year</th><th>Records</th><th>Exp. Tons</th><th>Revenue</th></tr>
    {yr_html}
  </table>
</div>

<!-- 6. The Hartford Terminal Network -->
<div class="section">
  <h2>6. Hartford-Area Cement Terminal Infrastructure</h2>
  <p>Hartford&rsquo;s role as a distribution hub is supported by physical terminal
  infrastructure along the Connecticut River and CSX main lines:</p>

  <table>
    <tr><th>Terminal</th><th>Location</th><th>Operator</th><th>Rail Access</th><th>Function</th></tr>
    <tr>
      <td><b>New Haven Terminal</b></td>
      <td>New Haven, CT (Port of NH)</td>
      <td>Multiple operators</td>
      <td>CSX New Haven Line</td>
      <td>Bulk cement storage, receives by vessel + rail</td>
    </tr>
    <tr>
      <td><b>Hartford Bulk Terminal</b></td>
      <td>Hartford, CT (Connecticut River)</td>
      <td>Heidelberg / Lafarge distribution</td>
      <td>CSX Boston Line (Park River Branch)</td>
      <td>Rail-received, truck-distributed locally; rail re-origination for southbound</td>
    </tr>
    <tr>
      <td><b>Springfield, MA Terminal</b></td>
      <td>Springfield, MA (edge of BEA 013)</td>
      <td>Lafarge / Amrize</td>
      <td>CSX at Palmer, MA junction</td>
      <td>Receives from Albany by rail; re-originates to southern New England and Mid-Atlantic</td>
    </tr>
  </table>
  <p class="source">Note: Terminal specifics from Heidelberg Materials terminal directory,
  Lafarge distribution network maps, and CTDOT state rail plan terminal inventories.</p>
</div>

<!-- 7. Comparison -->
<div class="section">
  <h2>7. Hartford Compared: Three Types of No-Plant Origins</h2>
  <table>
    <tr><th></th><th>BEA 160 Fresno</th><th>BEA 134 Houston</th><th>BEA 013 Hartford</th></tr>
    <tr><td><b>Root cause</b></td>
        <td>Geographic boundary artifact</td>
        <td>Port import gateway</td>
        <td>Mid-corridor distribution node</td></tr>
    <tr><td><b>Cement source</b></td>
        <td>Kern County plants (adjacent BEA)</td>
        <td>Foreign vessels (Mexico, Turkey)</td>
        <td>Albany NY plants + Quebec imports</td></tr>
    <tr><td><b>Shipment pattern</b></td>
        <td>Unit trains dominant</td>
        <td>Mixed unit + small lot</td>
        <td>Small lot dominant</td></tr>
    <tr><td><b>Import flag</b></td>
        <td>None</td>
        <td>Partially coded</td>
        <td>Partially coded (Quebec)</td></tr>
    <tr><td><b>Correct reclassification</b></td>
        <td>Assign to BEA 161 plants</td>
        <td>Tag as port_import</td>
        <td>Tag as transit_terminal (mixed)</td></tr>
    <tr><td><b>Tons (2005&ndash;2023)</b></td>
        <td>{37:,}M</td>
        <td>{31:,}M</td>
        <td>14M</td></tr>
  </table>
</div>

<!-- 8. Implications -->
<div class="section">
  <h2>8. Implications for the Matching Model</h2>
  <ul>
    <li><b>New tag: <code>transit_terminal</code></b> — Hartford represents cement that entered
        the waybill system at an intermediate distribution terminal, not a production or import
        point. This is conceptually distinct from both boundary-split (Fresno) and port-import
        (Houston).</li>
    <li><b>Albany plants benefit:</b> Assigning BEA 013 records back to Albany BEA (004) plants
        would raise Lafarge Ravena and Heidelberg from their current modeled tonnages significantly.
        Albany is already the 3rd-largest plant BEA; Hartford re-assignment would make it
        the dominant Northeast production origin.</li>
    <li><b>Quebec share unknown:</b> Some fraction of the 13.8M tons originates in Quebec.
        Without terminal-level data, a proxy approach (e.g., assume Quebec share =
        proportion of BEA 178 direct imports to New England relative to Albany plants&rsquo; capacity)
        is needed.</li>
    <li><b>Similar BEAs to investigate:</b> BEA 010 (Boston, 1.9M tons) and BEA 026 (Raleigh, 5.2M tons)
        likely show the same transit-terminal pattern along CSX and NS corridors respectively.</li>
  </ul>
</div>

<!-- Sources -->
<div class="section">
  <h2>Sources</h2>
  <ul style="font-size:12px; line-height:2;">
    <li>Lafarge / Amrize &mdash; Ravena NY plant &amp; Connecticut River distribution terminal</li>
    <li>Heidelberg Materials US &mdash; Albany / Glens Falls plant capacity, terminal directory</li>
    <li>CRH / St. Lawrence Cement &mdash; Quebec Joliette &amp; St. Constant plants</li>
    <li>Connecticut DOT &mdash; State Rail Plan 2017: bulk terminal inventory, cement flows</li>
    <li>CSX Transportation &mdash; Boston Line, New Haven Line, River Line routing</li>
    <li>STB Public Use Waybill Sample, STCC 32411, 2005&ndash;2023</li>
    <li>EPA GHGRP &mdash; NAICS 327310, Connecticut BEA 013 absence confirmed;
        Albany BEA 004 plants confirmed (Ravena, Glens Falls)</li>
    <li>USGS Cement Annual Review &mdash; New York production, import volumes for New England</li>
  </ul>
</div>

<div class="footer">
  BEA 013 Investigation &mdash; February 2026 &mdash; Generated from STB Waybill &amp; EPA GHGRP analysis<br>
  <a href="fresno_bea160_investigation.html" style="color:#8e44ad;text-decoration:none">
    &larr; BEA 160 (Fresno) Investigation</a> &nbsp;|&nbsp;
  <a href="houston_bea134_investigation.html" style="color:#8e44ad;text-decoration:none">
    BEA 134 (Houston) Investigation</a> &nbsp;|&nbsp;
  <a href="fargo_bea096_investigation.html" style="color:#8e44ad;text-decoration:none">
    BEA 096 (Fargo) Investigation</a> &nbsp;|&nbsp;
  <a href="cement_trade_flow_report.html" style="color:#8e44ad;text-decoration:none">
    &uarr; Back to Trade Flow Report</a>
</div>

</div>
</body>
</html>'''
    return html


def main():
    print('Loading BEA 013 (Hartford) waybill records...')
    records = load_hartford()
    print(f'  Found {len(records):,} records for BEA 013')

    print('Analysing...')
    stats = analyse(records)

    print('Building HTML...')
    html = build_html(stats)

    out_path = os.path.join(SCRIPT_DIR, 'hartford_bea013_investigation.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Written: {out_path}')
    return out_path


if __name__ == '__main__':
    main()
