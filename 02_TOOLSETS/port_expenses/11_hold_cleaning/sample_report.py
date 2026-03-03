"""
Generate sample_report.html for 11_hold_cleaning module.
Run from: 02_TOOLSETS/port_expenses/11_hold_cleaning/
"""
import sys, os, json
from datetime import date

sys.path.insert(0, 'src')
from hold_cleaning_calculator import calculate_hold_cleaning

# ── Scenarios ──────────────────────────────────────────────────────────────
scenarios = [
    ('Steel Products → Grain',         'New Orleans', 5, 'grain',  'steel_products',       61000, True),
    ('Pig Iron → Grain',               'New Orleans', 5, 'grain',  'iron_ore',             61000, True),
    ('Nitrogen Fertilizer → Grain',    'New Orleans', 5, 'grain',  'fertilizer',           61000, True),
    ('Phosphorus Fertilizer → Grain',  'New Orleans', 5, 'grain',  'fertilizer',           61000, True),
    ('Salt → Grain',                   'New Orleans', 5, 'grain',  'salt_sodium_chloride', 61000, True),
    ('Cement → Grain',                 'New Orleans', 5, 'grain',  'cement',               61000, True),
    ('Coal → Grain',                   'New Orleans', 5, 'grain',  'coal',                 61000, True),
    ('Grain → Grain (same commodity)', 'New Orleans', 5, 'grain',  'grain',                61000, True),
    ('Grain → Petcoke',                'Houston',     5, 'petcoke','grain',                61000, False),
    ('Coal → Petcoke',                 'Houston',     5, 'petcoke','coal',                 61000, False),
]

RISK_COLOR = {
    'low':       ('#d4edda', '#155724'),
    'medium':    ('#fff3cd', '#856404'),
    'high':      ('#f8d7da', '#721c24'),
    'very_high': ('#f5c6cb', '#491217'),
}

RISK_LABEL = {
    'low': 'LOW', 'medium': 'MEDIUM', 'high': 'HIGH', 'very_high': 'VERY HIGH'
}

def risk_badge(level):
    bg, fg = RISK_COLOR.get(level, ('#eee','#333'))
    label  = RISK_LABEL.get(level, level.upper())
    return f'<span class="badge" style="background:{bg};color:{fg};border:1px solid {fg};">{label}</span>'

def fmt_usd(v):
    return f'${v:,.0f}' if v else '—'

# ── Cargo pattern data (from USACE analysis) ────────────────────────────────
cargo_pattern_rows = [
    ('Pig Iron',               15, 'Low',    'sweep_alkaline_wash'),
    ('Finished Steel',         10, 'Low',    'sweep_freshwater_rinse'),
    ('Nitrogen Fertilizers',   11, 'Medium', 'seawater_freshwater_rinse + MARPOL HME check'),
    ('Potassium Fertilizers',   7, 'Medium', 'seawater_freshwater_rinse + MARPOL HME check'),
    ('Phosphorus Fertilizers',  3, 'Medium', 'seawater_freshwater_rinse + MARPOL HME check'),
    ('Cement',                  5, 'High',   'dry_sweep + portable pump + freshwater — NO bilge pump'),
    ('Salt',                    3, 'Medium', 'seawater_freshwater_rinse + limewash if rust'),
]

load_port_rows = [
    ('Zen-Noh Grain',          25),
    ('Burnside Terminal',      22),
    ('ADM AMA',                19),
    ('ADM Destrehan',          18),
    ('United Bulk',            17),
    ('Bunge Destrehan',        16),
    ('Convent Marine Terminal',15),
    ('Cenex Harvest States',   14),
    ('Zen-Noh Lower',          14),
    ('IMT Coal',               12),
]

max_lp = load_port_rows[0][1]

# ── Build HTML ───────────────────────────────────────────────────────────────
rows_html = ''
for label, port, r in [(s[0], s[1], calculate_hold_cleaning(
        port=s[1], hold_count=s[2], commodity_loading=s[3],
        previous_cargo=s[4], vessel_dwt=s[5], include_fgis_inspection=s[6]))
    for s in scenarios]:

    risk    = r.get('hold_cleaning_risk_level','low')
    total   = r.get('hold_cleaning_total', 0)
    days    = r.get('hold_cleaning_days_lost', 0)
    sweep   = r.get('hold_cleaning_sweep', 0)
    wash    = r.get('hold_cleaning_wash', 0)
    fgis_v  = r.get('hold_cleaning_fgis_inspection', 0)
    warns   = r.get('hold_cleaning_warnings', [])
    ops     = r.get('hold_cleaning_operations', [])
    bg, _   = RISK_COLOR.get(risk, ('#fff','#000'))

    warn_html = ''
    for w in warns[:2]:
        warn_html += f'<div class="warn">⚠ {w}</div>'

    ops_html = ''.join(f'<li>{o}</li>' for o in ops)

    rows_html += f'''
    <tr style="background:{bg}08;">
      <td class="scenario">{label}</td>
      <td>{port}</td>
      <td>{risk_badge(risk)}</td>
      <td class="num">{days:.1f}</td>
      <td class="num">{fmt_usd(sweep)}</td>
      <td class="num">{fmt_usd(wash)}</td>
      <td class="num">{fmt_usd(fgis_v) if fgis_v else "—"}</td>
      <td class="num total">{fmt_usd(total)}</td>
      <td class="notes">{warn_html}<ul class="ops">{ops_html}</ul></td>
    </tr>'''

cargo_rows_html = ''
for cargo, n, risk_str, protocol in cargo_pattern_rows:
    risk_key = risk_str.lower()
    bg, fg = RISK_COLOR.get(risk_key, ('#eee','#333'))
    bar_pct = int(n / 15 * 100)
    cargo_rows_html += f'''
    <tr>
      <td>{cargo}</td>
      <td><div class="bar-outer"><div class="bar-inner" style="width:{bar_pct}%;background:{fg};"></div></div> {n}</td>
      <td><span class="badge" style="background:{bg};color:{fg};border:1px solid {fg};">{risk_str.upper()}</span></td>
      <td style="font-size:0.85em;color:#555;">{protocol}</td>
    </tr>'''

lp_rows_html = ''
for lp, n in load_port_rows:
    bar_pct = int(n / max_lp * 100)
    lp_rows_html += f'''
    <tr>
      <td>{lp}</td>
      <td><div class="bar-outer"><div class="bar-inner" style="width:{bar_pct}%;background:#2c6e49;"></div></div> {n}</td>
    </tr>'''

today = date.today().strftime('%B %d, %Y')

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hold Cleaning PDA Report — US Gulf Ports</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          font-size: 14px; color: #222; background: #f5f5f5; }}

  .page {{ max-width: 1300px; margin: 0 auto; padding: 24px; }}

  /* Header */
  .header {{ background: #1a2f4e; color: white; padding: 28px 32px; border-radius: 8px;
             margin-bottom: 24px; }}
  .header h1 {{ font-size: 1.6em; font-weight: 700; margin-bottom: 6px; }}
  .header .sub {{ font-size: 0.95em; color: #a8c4e0; }}
  .header .meta {{ margin-top: 14px; display: flex; gap: 32px; flex-wrap: wrap; }}
  .header .meta-item {{ font-size: 0.85em; }}
  .header .meta-item .label {{ color: #7fb3d3; font-size: 0.9em; display: block; }}
  .header .meta-item .value {{ font-weight: 600; }}

  /* Section */
  .section {{ background: white; border-radius: 8px; padding: 24px;
              margin-bottom: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
  .section h2 {{ font-size: 1.1em; font-weight: 700; color: #1a2f4e;
                 border-bottom: 2px solid #e8ecf0; padding-bottom: 10px; margin-bottom: 16px; }}
  .section h3 {{ font-size: 0.95em; font-weight: 700; color: #444; margin: 14px 0 8px; }}

  /* Main PDA table */
  table.pda {{ width: 100%; border-collapse: collapse; font-size: 0.88em; }}
  table.pda th {{ background: #1a2f4e; color: white; padding: 8px 10px;
                  text-align: left; white-space: nowrap; }}
  table.pda th.num {{ text-align: right; }}
  table.pda td {{ padding: 8px 10px; border-bottom: 1px solid #eee; vertical-align: top; }}
  table.pda td.num {{ text-align: right; white-space: nowrap; }}
  table.pda td.total {{ font-weight: 700; font-size: 1.05em; }}
  table.pda td.scenario {{ font-weight: 600; white-space: nowrap; }}
  table.pda tr:hover td {{ background: #f0f4f8 !important; }}

  .warn {{ color: #856404; font-size: 0.82em; margin-bottom: 3px; }}
  ul.ops {{ padding-left: 14px; margin: 4px 0 0; color: #555; font-size: 0.82em; }}
  ul.ops li {{ margin-bottom: 2px; }}

  /* Badge */
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px;
            font-size: 0.78em; font-weight: 700; letter-spacing: 0.5px; white-space: nowrap; }}

  /* Two-column grid */
  .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}

  /* Cargo / port tables */
  table.data {{ width: 100%; border-collapse: collapse; font-size: 0.88em; }}
  table.data th {{ background: #2c3e50; color: white; padding: 7px 10px; text-align: left; }}
  table.data td {{ padding: 7px 10px; border-bottom: 1px solid #eee; vertical-align: middle; }}
  table.data tr:hover td {{ background: #f7f9fc; }}

  .bar-outer {{ display: inline-block; width: 90px; height: 10px;
                background: #e0e0e0; border-radius: 3px; vertical-align: middle;
                margin-right: 6px; }}
  .bar-inner {{ height: 100%; border-radius: 3px; }}

  /* Key findings box */
  .findings {{ background: #eaf4fb; border-left: 4px solid #2196f3;
               padding: 14px 18px; border-radius: 0 6px 6px 0; margin-bottom: 14px; }}
  .findings p {{ margin: 4px 0; font-size: 0.9em; line-height: 1.5; }}

  /* Cost range card */
  .cost-cards {{ display: flex; gap: 14px; flex-wrap: wrap; margin-top: 4px; }}
  .cost-card {{ flex: 1; min-width: 160px; background: #f8f9fa; border: 1px solid #dee2e6;
                border-radius: 6px; padding: 14px 16px; text-align: center; }}
  .cost-card .amount {{ font-size: 1.5em; font-weight: 700; color: #1a2f4e; }}
  .cost-card .desc {{ font-size: 0.8em; color: #666; margin-top: 4px; }}

  .footer {{ text-align: center; color: #999; font-size: 0.78em; margin-top: 24px; padding: 12px; }}
</style>
</head>
<body>
<div class="page">

<!-- HEADER -->
<div class="header">
  <h1>Hold Cleaning PDA Report — US Gulf Ports</h1>
  <div class="sub">Proforma Disbursement Account · Hold Cleaning Cost Estimates</div>
  <div class="meta">
    <div class="meta-item">
      <span class="label">Prepared by</span>
      <span class="value">William S. Davis III</span>
    </div>
    <div class="meta-item">
      <span class="label">Report date</span>
      <span class="value">{today}</span>
    </div>
    <div class="meta-item">
      <span class="label">Vessel basis</span>
      <span class="value">Supramax/Ultramax · 61,000 DWT · 5 Holds</span>
    </div>
    <div class="meta-item">
      <span class="label">Ports</span>
      <span class="value">New Orleans (Mississippi River) / Houston</span>
    </div>
    <div class="meta-item">
      <span class="label">Module version</span>
      <span class="value">Hold Cleaning Intelligence v1.1.0</span>
    </div>
  </div>
</div>

<!-- KEY FINDINGS -->
<div class="section">
  <h2>Key Findings</h2>
  <div class="findings">
    <p><strong>PDA range for a 5-hold Supramax loading grain at a Mississippi River elevator:</strong>
    $10,127 (steel/grain previously) → $15,927 (coal previously).
    The FGIS/NCB mandatory inspection ($3,127–$4,177) is the fixed floor on every US grain export PDA.</p>
    <p><strong>Cargo pattern insight (41,156 USACE voyage records):</strong>
    Supramaxes in the US Gulf predominantly import pig iron, finished steel, and fertilizers before
    cleaning and loading grain for export. Median turnaround: 4–18 days between discharge and next grain load.
    All major grain load terminals are on the Lower Mississippi (Zen-Noh, Burnside, ADM, United Bulk, Bunge).</p>
    <p><strong>Critical protocol alert:</strong> Cement → Grain requires portable salvage pump (DO NOT use bilge pump).
    Coal → Grain requires alkaline chemical wash (Unitor CargoClean HD 10%) with 48–72 hr minimum.</p>
  </div>
  <div class="cost-cards">
    <div class="cost-card">
      <div class="amount">$6,625</div>
      <div class="desc">Minimum<br>(grain→petcoke, Houston, no FGIS)</div>
    </div>
    <div class="cost-card">
      <div class="amount">$10,127</div>
      <div class="desc">Typical floor<br>(steel or grain → grain, NOLA)</div>
    </div>
    <div class="cost-card">
      <div class="amount">$11,177</div>
      <div class="desc">Elevated<br>(cement → grain, NOLA)</div>
    </div>
    <div class="cost-card">
      <div class="amount">$15,927</div>
      <div class="desc">High (coal → grain)<br>+ 2.5 days delay</div>
    </div>
  </div>
</div>

<!-- PDA TABLE -->
<div class="section">
  <h2>PDA Cost Scenarios — 10 Cargo Transitions</h2>
  <div style="overflow-x:auto;">
  <table class="pda">
    <thead>
      <tr>
        <th>Scenario (Prev → Next)</th>
        <th>Port</th>
        <th>Risk</th>
        <th class="num">Days Lost</th>
        <th class="num">Sweep</th>
        <th class="num">Wash</th>
        <th class="num">FGIS/NCB</th>
        <th class="num">Total</th>
        <th>Notes / Warnings</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
  </div>
  <p style="font-size:0.78em;color:#888;margin-top:8px;">
    Rates basis: New Orleans $350/hold sweep, $1,050/hold wash (seawater+freshwater); Houston $325/$1,000.
    FGIS/NCB: USDA 7 CFR Part 800 regulated fee schedule (2024), DWT-banded. Reinspection reserve $250 for high-risk.
    Days lost = field-estimated cleaning time (Isbester benchmarks + P&I circular guidance). Source: hold_cleaning_rates.csv, cargo_compatibility_matrix.csv, fgis_inspection_fees.csv.
  </p>
</div>

<!-- CARGO PATTERN + LOAD PORTS -->
<div class="two-col">
  <div class="section">
    <h2>Supramax Import Cargo Patterns (US Gulf)</h2>
    <h3>Previous Cargoes Before Grain Loading — ≤14 Day Turnarounds</h3>
    <p style="font-size:0.82em;color:#666;margin-bottom:10px;">
      Source: 41,156 USACE MRTIS voyage records · Supramax/Ultramax segment only
    </p>
    <table class="data">
      <thead><tr><th>Previous Cargo (Discharged)</th><th>Transitions</th><th>Risk</th><th>Protocol</th></tr></thead>
      <tbody>{cargo_rows_html}</tbody>
    </table>
    <p style="font-size:0.78em;color:#888;margin-top:8px;">
      Steel and pig iron dominate (25 of 54 identified transitions = 46%) — LOW risk, standard sweep + wash.
      Fertilizers (combined 21 transitions = 39%) — MEDIUM risk, MARPOL HME wash water check required.
      Cement (5 = 9%) — HIGH risk, portable pump mandatory.
    </p>
  </div>

  <div class="section">
    <h2>Top Grain Load Terminals — Mississippi River</h2>
    <h3>Where Supramaxes Load After Cleaning (Quick-Turnaround)</h3>
    <p style="font-size:0.82em;color:#666;margin-bottom:10px;">
      All terminals are Lower Mississippi River grain elevators requiring FGIS/NCB certification
    </p>
    <table class="data">
      <thead><tr><th>Terminal</th><th>Voyages</th></tr></thead>
      <tbody>{lp_rows_html}</tbody>
    </table>
    <p style="font-size:0.78em;color:#888;margin-top:8px;">
      Discharge anchorages: Nashville Ave buoys, Chalmette, Mile 133/158/175 — Mississippi River stream berths.
      Vessels clean at anchor or at buoy berth before dropping downriver to grain elevator.
    </p>
  </div>
</div>

<!-- VENDOR TABLE -->
<div class="section">
  <h2>US Gulf Hold Cleaning Vendors</h2>
  <p style="font-size:0.82em;color:#666;margin-bottom:12px;">
    Source: vendor web research 2026. File: <code>data/vendors_us_gulf.csv</code>
    (To be expanded with chemical suppliers and launch hire services.)
  </p>
  <table class="data">
    <thead>
      <tr>
        <th>#</th><th>Company</th><th>Short Name</th><th>Location</th><th>Services / Notes</th>
      </tr>
    </thead>
    <tbody>
      <tr><td>1</td><td><strong>American Maritime Services LLC</strong></td><td>AMSC</td><td>New Orleans, LA</td>
          <td>Preferred vendor at Mississippi River grain terminals. USDA-certified hold cleaning, Standard &amp; Japanese-style cargo separations, LADEQ wash water permits, HAZ/NONHAZ disposal. HAZWOPER 40hr certified crews.</td></tr>
      <tr><td>2</td><td>North American Marine Inc.</td><td>NAMI</td><td>Houston, TX</td>
          <td>Hydro blast specialist. 12 units, 3,000–25,000 PSI / 275 GPM. Hourly or lump-sum "No Pass No Pay". USDA-NCB inspection support. 20+ yrs experience. Rapid mobilisation.</td></tr>
      <tr><td>3</td><td>Global Marine Logistics</td><td>GML</td><td>New Orleans, LA</td>
          <td>Maritime operations + cargo hold preparations. US Gulf, East/West coast, Mexico.</td></tr>
      <tr><td>4</td><td>Gulf Inland Marine Services</td><td>GIMS</td><td>New Orleans, LA</td>
          <td>Coordination and supervision of hold cleaning. Arranges and supervises third-party cleaning gangs. Compliance, inspections, crew changes, surveys.</td></tr>
      <tr><td>5</td><td>BIS Construction and Ship Services</td><td>BIS NOLA</td><td>New Orleans, LA</td>
          <td>Hold cleaning, ship cleaning, debris removal. Verify current status.</td></tr>
      <tr><td>6</td><td>Bludworth Marine LLC</td><td>Bludworth</td><td>Galveston / Orange / Houston, TX</td>
          <td>Full-service shipyard cleaning. Hydroblasting, tank cleaning, vessel repair. Texas Gulf coast.</td></tr>
      <tr><td>7</td><td>MC Marine LLC</td><td>MC Marine</td><td>Chickasaw, AL</td>
          <td>Barge cleaning, full shipyard services. Coverage: New Orleans to FL Panhandle.</td></tr>
      <tr><td>8</td><td>Patriot Construction Marine Division</td><td>Patriot Marine</td><td>New Iberia, LA</td>
          <td>Barge cleaning, marine construction. Port of Iberia (midway NOLA–Houston).</td></tr>
      <tr><td>9</td><td>Bertucci Contracting Company LLC</td><td>Bertucci</td><td>Jefferson, LA</td>
          <td>Mississippi River marine construction/dredging since 1875. Verify if vessel hold cleaning offered directly.</td></tr>
      <tr><td>10</td><td>CLIIN Robotic Hold Cleaning (via Oldendorff)</td><td>CLIIN</td><td>New Orleans, LA</td>
          <td>Robotic cleaning — no chemical agents. Mississippi Delta hub. Eliminates MARPOL wash water disposal issues. Best for high-frequency fleet operators.</td></tr>
      <tr style="background:#f8f9fa;"><td>11</td><td>Drew Marine</td><td>Drew Marine</td><td>Global / US ports</td>
          <td><em>Chemical supplier only.</em> Unitor CargoClean HD, degreaser, enzymatic products. Not a cleaning gang.</td></tr>
      <tr style="background:#f8f9fa;"><td>12</td><td>Wilhelmsen Ships Service</td><td>Wilhelmsen</td><td>Global / US ports</td>
          <td><em>Chemical supplier only.</em> Unitor range (CargoClean HD standard for alkaline coal/petcoke wash). Not a cleaning gang.</td></tr>
    </tbody>
  </table>
</div>

<!-- REGULATORY FLAGS -->
<div class="section">
  <h2>Regulatory Reference — US Gulf</h2>
  <div class="two-col" style="gap:16px;">
    <div>
      <h3>USDA FGIS / NCB — Mandatory for All US Grain Exports</h3>
      <ul style="padding-left:18px;font-size:0.88em;line-height:1.7;color:#444;">
        <li>USDA FGIS Stowage Examination — vessel cleanliness certification ($417–$1,067 by DWT)</li>
        <li>NCB Grain Certificate of Readiness — structure, bilges, stability ($750–$1,850 by DWT)</li>
        <li>USDA Per-Hold Cleanliness Certificate — $260/hold</li>
        <li>Reinspection reserve for high-risk previous cargoes (+$250)</li>
        <li>Authority: 7 CFR Part 800 / USDA FGIS / NCB tariff schedule (2024)</li>
      </ul>
    </div>
    <div>
      <h3>MARPOL Annex V — Wash Water Discharge</h3>
      <ul style="padding-left:18px;font-size:0.88em;line-height:1.7;color:#444;">
        <li><strong>HME cargoes</strong> (fertilizers, petcoke, coal): discharge PROHIBITED — port reception facility mandatory</li>
        <li>Non-HME outside Special Areas: en route, min. 12 nm from land</li>
        <li>Gulf of Mexico / Caribbean: MARPOL Special Area — stricter rules apply</li>
        <li>Chemical wash water always treated as HME regardless of cargo</li>
        <li>Copper concentrate: DO NOT WASH — compressed air and sweep only</li>
      </ul>
    </div>
  </div>
</div>

<div class="footer">
  Hold Cleaning Intelligence Module v1.1.0 &nbsp;|&nbsp;
  William S. Davis III, Maritime &amp; Supply Chain Consulting &nbsp;|&nbsp;
  Data: USDA FGIS, USACE MRTIS, UK P&amp;I Club, Skuld, Swedish Club, IMSBC Code, Isbester (Nautical Institute 1993) &nbsp;|&nbsp;
  Generated: {today}
</div>

</div>
</body>
</html>'''

output_path = 'sample_report.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Written: {os.path.abspath(output_path)}')
print(f'Size: {os.path.getsize(output_path):,} bytes')
