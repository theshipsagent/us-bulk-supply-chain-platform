"""
Generate hold_cleaning_intelligence_report.html
Comprehensive intelligence briefing — cargo hold cleaning for US bulk shipping

Run from: 02_TOOLSETS/port_expenses/11_hold_cleaning/
"""
import os
from datetime import date

TODAY = date.today().strftime("%B %d, %Y")

# ── Colour palette ─────────────────────────────────────────────────────────
RC = {
    "low":       ("#d4edda", "#155724", "LOW"),
    "medium":    ("#fff3cd", "#856404", "MEDIUM"),
    "high":      ("#f8d7da", "#721c24", "HIGH"),
    "very_high": ("#f5c6cb", "#491217", "VERY HIGH"),
}

def badge(level):
    bg, fg, lbl = RC.get(level, ("#eee", "#333", level.upper()))
    return f'<span class="badge" style="background:{bg};color:{fg};border:1px solid {fg};">{lbl}</span>'

def yes_no(v):
    v = str(v).strip().lower()
    if v == "yes":
        return '<span style="color:#155724;font-weight:700;">✓ Yes</span>'
    return '<span style="color:#888;">—</span>'

# ── Cargo compatibility matrix data ───────────────────────────────────────
import csv, io

MATRIX_CSV = open("data/cargo_compatibility_matrix.csv").read()

matrix_rows = []
reader = csv.DictReader(io.StringIO(MATRIX_CSV))
for row in reader:
    if row.get("previous_cargo"):
        matrix_rows.append(row)

# ── USACE voyage data (pre-computed) ─────────────────────────────────────
IMPORT_CARGO = [
    ("Nitrogen Fertilizers",     61,  "medium"),
    ("Finished Steel",           57,  "low"),
    ("Pig Iron",                 46,  "low"),
    ("Phosphorus Fertilizers",   30,  "medium"),
    ("Cement",                   24,  "high"),
    ("Manganese",                18,  "low"),
    ("Potassium Fertilizers",    15,  "medium"),
    ("Aggregates",               11,  "low"),
    ("Salt",                      7,  "medium"),
    ("General Cargo",             7,  "low"),
    ("Vehicles & Machinery",      7,  "low"),
    ("Pulp & Paper",              6,  "low"),
    ("Talc",                      5,  "low"),
    ("Sugar",                     2,  "low"),
    ("Barite",                    3,  "low"),
]
MAX_IMPORT = 61

LOAD_PORTS = [
    ("Zen-Noh Grain (Reserve, LA)",      327, "grain"),
    ("ADM AMA (Ama, LA)",                272, "grain"),
    ("United Bulk Terminal (Davant, LA)", 271, "grain"),
    ("Bunge Destrehan (Destrehan, LA)",   270, "grain"),
    ("Convent Marine Terminal",           214, "grain"),
    ("ADM Destrehan",                     187, "grain"),
    ("Dreyfus (Reserve, LA)",             162, "grain"),
    ("Cenex Harvest States",              155, "grain"),
    ("Burnside Terminal",                 143, "grain"),
    ("Zen-Noh Lower",                     142, "grain"),
    ("Cargill Reserve",                   127, "grain"),
    ("IMT Coal Terminal",                 123, "coal/petcoke"),
    ("ADM Reserve",                       117, "grain"),
    ("Cargill Westwego",                  108, "grain"),
    ("Drax Biomass",                       70, "biomass"),
]
MAX_LP = 327

DISCHARGE_ZONES = [
    ("Nashville Ave A Buoys",          144),
    ("Chalmette Buoys",                108),
    ("ADM Destrehan Buoys (Lower)",     99),
    ("158 Mile Buoys (Middle/Lower)",   76),
    ("ADM Destrehan Buoys (Upper)",     70),
    ("Meraux Buoys (Upper/Lower)",      68),
    ("158 Mile Buoys (Upper)",          65),
    ("Dockside Buoys (Lower)",          64),
]
MAX_DZ = 144

# ── Build matrix HTML ─────────────────────────────────────────────────────
def matrix_table():
    rows = ""
    for r in matrix_rows:
        bg, fg, _ = RC.get(r["risk_level"], ("#fff", "#222", ""))
        rows += f"""
        <tr style="background:{bg}18;">
          <td><strong>{r['previous_cargo'].replace('_',' ').title()}</strong></td>
          <td>{r['next_cargo'].replace('_',' ').title()}</td>
          <td>{badge(r['risk_level'])}</td>
          <td style="font-size:0.82em;color:#444;">{r['cleaning_requirement'].replace('_',' ')}</td>
          <td style="text-align:center;">{yes_no(r['fgis_concern'])}</td>
          <td style="text-align:center;">{yes_no(r['chemical_wash_required'])}</td>
          <td style="text-align:center;font-weight:600;">{r['days_lost_estimate']}</td>
          <td style="font-size:0.8em;color:#555;">{r['notes']}</td>
        </tr>"""
    return rows

# ── Bar helpers ───────────────────────────────────────────────────────────
def bar(n, mx, color="#1a2f4e", label=""):
    pct = int(n / mx * 100)
    return f'<div class="bar-w"><div class="bar-f" style="width:{pct}%;background:{color};"></div></div><span class="bar-n">{n}{" — "+label if label else ""}</span>'

# ── Vendor rows ───────────────────────────────────────────────────────────
VENDORS = [
    # Shore cleaning gangs
    ("shore_gang", "American Maritime Services LLC", "AMSC", "New Orleans, LA",
     "amsnola.com", "bcrouchet@amsnola.com",
     "Mississippi River grain terminals, US Gulf",
     "Cargo hold cleaning (grain/USDA standard), Standard &amp; Japanese-style cargo separations, deslopping, LADEQ wash water permits, HAZ/NONHAZ disposal, barge tank cleaning",
     "Preferred vendor at Mississippi River grain elevators. HAZWOPER 40hr certified crews. Industrial Canal facility. 13080 Chef Menteur Hwy, New Orleans LA 70129."),
    ("shore_gang", "North American Marine Inc.", "NAMI", "Houston, TX",
     "northamericanmarineinc.com", "",
     "Houston, US Gulf (rapid mobilisation)",
     "Hydro blast cleaning (3,000–25,000 PSI, 275 GPM), tank cleaning, dry cargo hold prep, sand blast, painting, gas freeing, USDA-NCB inspection support, slops disposal",
     "12 hydro blast units. Hourly or lump-sum 'No Pass No Pay' option. 20+ years experience. Crews within hours of notification."),
    ("shore_gang", "Global Marine Logistics", "GML", "New Orleans, LA",
     "gmlnola.com", "",
     "US Gulf, East &amp; West Coast, Mexico ports",
     "Cargo hold preparations, maritime operations, vessel husbandry",
     "Multi-coast coverage. Coordinates hold cleaning across US port range."),
    ("shore_gang", "Gulf Inland Marine Services", "GIMS", "New Orleans, LA",
     "gulfinland.com", "",
     "New Orleans, US Gulf",
     "Hold cleaning arrangement &amp; supervision, compliance oversight, inspections, crew changes, medical, spares",
     "Coordination/supervision only — arranges third-party cleaning gangs. Decades of experience on Lower Mississippi."),
    ("shore_gang", "BIS Construction &amp; Ship Services", "BIS NOLA", "New Orleans, LA",
     "bisnola.com", "",
     "New Orleans",
     "Hold cleaning, ship cleaning, debris removal",
     "Verify current operational status before booking."),
    # Shipyard facilities
    ("shipyard", "Bludworth Marine LLC", "Bludworth", "Galveston / Orange / Houston, TX",
     "vesselrepair.com", "",
     "Galveston, Orange TX, Houston (Texas Gulf Coast)",
     "Tank &amp; vessel cleaning, hydroblasting, ship repair, barge construction, gas freeing, full shipyard services",
     "Multiple Texas Gulf facilities. Experienced in bulk and liquid cargo vessel preparation."),
    ("shipyard", "MC Marine LLC", "MC Marine", "Chickasaw, AL",
     "mcmarinellc.com", "",
     "Chickasaw AL; New Orleans to FL Panhandle",
     "Barge cleaning, full shipyard services",
     "Covers eastern Gulf from NOLA to Florida Panhandle."),
    ("shipyard", "Patriot Construction Marine Division", "Patriot Marine", "New Iberia, LA",
     "patriot-construction.com", "",
     "Port of Iberia, South Louisiana (midway NOLA–Houston)",
     "Barge cleaning, marine construction, special marine projects",
     "Located at Port of Iberia."),
    # Marine contractors
    ("contractor", "Bertucci Contracting Company LLC", "Bertucci", "Jefferson, LA",
     "bertucciconstruction.com", "",
     "Mississippi River, US Gulf Coast",
     "Marine construction, dredging, coastal restoration — vessel cleaning TBC",
     "Operating since 1875. Leading Mississippi River marine contractor. William named as hold cleaning contact — verify scope of cleaning services directly."),
    # Robotic / technology
    ("robotic", "CLIIN Robotic Hold Cleaning (via Oldendorff)", "CLIIN", "New Orleans, LA",
     "", "",
     "Mississippi Delta / US Gulf",
     "Robotic cargo hold cleaning — no chemical agents, no wash water discharge",
     "New technology. Oldendorff partnership. Eliminates MARPOL Annex V wash water disposal issue. Best for high-frequency operators with repeat port calls. Hub opened in Mississippi Delta."),
    # Chemical suppliers
    ("chemical_supplier", "Drew Marine (Unitor CargoClean)", "Drew Marine", "Global / US ports",
     "drew-marine.com", "",
     "Global / US ports",
     "Hold cleaning chemicals: Unitor CargoClean HD (alkaline), degreasers, enzymatic odor eliminators, technical advisory",
     "NOT a cleaning gang — chemical product supply and technical guidance only. CargoClean HD is the industry standard for coal/petcoke alkaline wash at 10% concentration."),
    ("chemical_supplier", "Wilhelmsen Ships Service", "Wilhelmsen", "Global / US ports",
     "wilhelmsen.com", "",
     "Global / US ports",
     "Unitor chemical range for hold cleaning, marine chemicals supply, technical support",
     "NOT a cleaning gang. Major marine chemicals distributor. Unitor range widely specified in P&amp;I Club protocols."),
]

TYPE_LABELS = {
    "shore_gang":        ("Shore Cleaning Gangs", "#1a2f4e"),
    "shipyard":          ("Shipyard Facilities", "#2c5f2e"),
    "contractor":        ("Marine Contractors", "#5c3d2e"),
    "robotic":           ("Robotic / Technology", "#1a3a5e"),
    "chemical_supplier": ("Chemical Suppliers (not gangs)", "#555"),
}

def vendor_section():
    out = ""
    for vtype, (vlabel, vcolor) in TYPE_LABELS.items():
        rows = [v for v in VENDORS if v[0] == vtype]
        if not rows:
            continue
        out += f'<h3 style="color:{vcolor};margin:18px 0 8px;font-size:1em;border-bottom:1px solid #e0e0e0;padding-bottom:4px;">{vlabel}</h3>'
        out += '<table class="vtable"><thead><tr><th>Company</th><th>Location</th><th>Ports Covered</th><th>Services</th><th>Notes</th></tr></thead><tbody>'
        for v in rows:
            _, name, short, loc, web, email, ports, svcs, notes = v
            web_link = f'<a href="https://{web}" target="_blank">{web}</a>' if web else "—"
            out += f'<tr><td><strong>{name}</strong><br><span style="color:#888;font-size:0.82em;">{web_link}</span></td>'
            out += f'<td style="white-space:nowrap;">{loc}</td><td style="font-size:0.85em;">{ports}</td>'
            out += f'<td style="font-size:0.82em;">{svcs}</td><td style="font-size:0.82em;color:#555;">{notes}</td></tr>'
        out += '</tbody></table>'
    return out

# ── Main HTML ──────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Cargo Hold Cleaning — US Bulk Shipping Intelligence Report</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
      font-size:14px;color:#222;background:#f4f5f7;line-height:1.5;}}
.page{{max-width:1380px;margin:0 auto;padding:24px;}}

/* ── Header ── */
.hdr{{background:linear-gradient(135deg,#0d1f3c 0%,#1a3a6e 100%);
      color:#fff;padding:32px 36px;border-radius:10px;margin-bottom:20px;}}
.hdr h1{{font-size:1.75em;font-weight:800;letter-spacing:-0.5px;}}
.hdr .sub{{font-size:1em;color:#9bb8d9;margin-top:4px;}}
.hdr .meta{{display:flex;flex-wrap:wrap;gap:28px;margin-top:20px;}}
.hdr .mi .lbl{{font-size:0.78em;color:#7fb3d3;display:block;}}
.hdr .mi .val{{font-weight:700;font-size:0.95em;}}

/* ── Nav pills ── */
.nav{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:20px;}}
.nav a{{padding:5px 14px;background:#fff;border:1px solid #cdd3db;border-radius:20px;
         font-size:0.8em;color:#1a2f4e;text-decoration:none;transition:all .15s;}}
.nav a:hover{{background:#1a2f4e;color:#fff;border-color:#1a2f4e;}}

/* ── Cards ── */
.card{{background:#fff;border-radius:8px;padding:24px;margin-bottom:18px;
       box-shadow:0 1px 4px rgba(0,0,0,.07);}}
.card h2{{font-size:1.1em;font-weight:800;color:#0d1f3c;
           border-bottom:3px solid #e8ecf2;padding-bottom:8px;margin-bottom:16px;
           display:flex;align-items:center;gap:8px;}}
.card h2 .num{{background:#1a2f4e;color:#fff;font-size:0.7em;
               padding:2px 8px;border-radius:10px;font-weight:700;}}
.card h3{{font-size:0.95em;font-weight:700;color:#1a2f4e;margin:16px 0 8px;}}

/* ── Two/three-col grids ── */
.g2{{display:grid;grid-template-columns:1fr 1fr;gap:18px;}}
.g3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px;}}
.g14{{display:grid;grid-template-columns:1fr 4fr;gap:18px;}}

/* ── Standard hierarchy boxes ── */
.std-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;}}
.std-box{{padding:14px;border-radius:7px;text-align:center;}}
.std-box .rank{{font-size:1.8em;font-weight:900;}}
.std-box .name{{font-size:0.9em;font-weight:700;margin:4px 0;}}
.std-box .desc{{font-size:0.75em;color:#555;}}

/* ── Badge ── */
.badge{{display:inline-block;padding:2px 8px;border-radius:4px;
        font-size:0.76em;font-weight:700;letter-spacing:.4px;white-space:nowrap;}}

/* ── Tables ── */
table.mt,table.vtable{{width:100%;border-collapse:collapse;font-size:0.85em;}}
table.mt th,table.vtable th{{background:#1a2f4e;color:#fff;padding:8px 10px;
                              text-align:left;white-space:nowrap;font-size:0.82em;}}
table.mt td,table.vtable td{{padding:7px 10px;border-bottom:1px solid #eef0f3;vertical-align:top;}}
table.mt tr:hover td,table.vtable tr:hover td{{background:#f7f9fc;}}

/* ── Bar charts ── */
.bar-row{{display:flex;align-items:center;gap:8px;margin:4px 0;}}
.bar-lbl{{width:220px;font-size:0.83em;color:#333;flex-shrink:0;text-align:right;}}
.bar-w{{width:200px;height:12px;background:#e8eaed;border-radius:3px;flex-shrink:0;}}
.bar-f{{height:100%;border-radius:3px;}}
.bar-n{{font-size:0.82em;color:#555;}}

/* ── Info boxes ── */
.info{{background:#eef4fb;border-left:4px solid #1a6dd4;padding:12px 16px;
        border-radius:0 6px 6px 0;margin:10px 0;font-size:0.88em;}}
.warn-box{{background:#fff8e1;border-left:4px solid #f59e0b;padding:12px 16px;
            border-radius:0 6px 6px 0;margin:10px 0;font-size:0.88em;}}
.crit-box{{background:#fde8e8;border-left:4px solid #dc2626;padding:14px 16px;
            border-radius:0 6px 6px 0;margin:10px 0;}}
.crit-box strong{{color:#991b1b;}}

/* ── Phase steps ── */
.phases{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:10px 0;}}
.phase{{background:#f8f9fb;border:1px solid #e0e4ea;border-radius:7px;padding:12px;}}
.phase .ph-num{{font-size:1.5em;font-weight:900;color:#1a2f4e;}}
.phase .ph-name{{font-weight:700;color:#1a2f4e;font-size:0.85em;margin:3px 0;}}
.phase .ph-body{{font-size:0.78em;color:#555;}}

/* ── Concern cards ── */
.concern-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;}}
.concern{{border-radius:7px;padding:14px;border:1px solid #ddd;}}

/* ── Rate mini-table ── */
table.rt{{width:100%;border-collapse:collapse;font-size:0.82em;}}
table.rt th{{background:#2c3e50;color:#fff;padding:6px 10px;text-align:left;}}
table.rt td{{padding:6px 10px;border-bottom:1px solid #eee;}}
table.rt .num{{text-align:right;}}

/* ── Source list ── */
.src-grid{{display:grid;grid-template-columns:1fr 1fr;gap:6px;}}
.src-item{{background:#f8f9fb;border:1px solid #e4e8ec;border-radius:5px;
           padding:8px 12px;font-size:0.82em;}}
.src-item .src-type{{color:#888;font-size:0.85em;}}

/* ── Footer ── */
.footer{{text-align:center;color:#aaa;font-size:0.75em;margin-top:24px;padding:12px;
         border-top:1px solid #e0e0e0;}}
</style>
</head>
<body>
<div class="page">

<!-- ═══ HEADER ═══ -->
<div class="hdr">
  <h1>Cargo Hold Cleaning — US Bulk Shipping Intelligence Report</h1>
  <div class="sub">Comprehensive briefing: vessel types, cargo patterns, cleaning standards, protocols, regulatory compliance, and vendor directory</div>
  <div class="meta">
    <div class="mi"><span class="lbl">Prepared by</span><span class="val">William S. Davis III</span></div>
    <div class="mi"><span class="lbl">Report date</span><span class="val">{TODAY}</span></div>
    <div class="mi"><span class="lbl">Module version</span><span class="val">Hold Cleaning Intelligence v1.1.0</span></div>
    <div class="mi"><span class="lbl">Knowledge base</span><span class="val">50+ authoritative sources (P&I clubs, IMO, USDA, Isbester, MARPOL)</span></div>
    <div class="mi"><span class="lbl">Voyage data</span><span class="val">41,156 USACE MRTIS records — Supramax/Ultramax US Gulf segment</span></div>
  </div>
</div>

<!-- ═══ NAV ═══ -->
<div class="nav">
  <a href="#fleet">Fleet Profile</a>
  <a href="#patterns">Cargo Patterns</a>
  <a href="#standards">Cleanliness Standards</a>
  <a href="#matrix">Compatibility Matrix</a>
  <a href="#methods">Cleaning Methods</a>
  <a href="#location">Where to Clean</a>
  <a href="#fgis">FGIS / NCB</a>
  <a href="#marpol">MARPOL Compliance</a>
  <a href="#concerns">Critical Concerns</a>
  <a href="#vendors">Vendor Directory</a>
  <a href="#rates">Rate Reference</a>
  <a href="#sources">Sources</a>
</div>


<!-- ═══ 1. FLEET PROFILE ═══ -->
<div class="card" id="fleet">
  <h2><span class="num">1</span> Vessel Fleet Profile — Supramax &amp; Ultramax</h2>
  <div class="g2">
    <div>
      <h3>Supramax (Standard)</h3>
      <table class="rt">
        <tr><td>DWT range</td><td class="num">52,000 – 58,000 DWT</td></tr>
        <tr><td>LOA</td><td class="num">~185 – 196 m</td></tr>
        <tr><td>Holds</td><td class="num">5 holds, 5 hatches</td></tr>
        <tr><td>Gear</td><td class="num">4 × 30t cranes typical</td></tr>
        <tr><td>DWT (dataset median)</td><td class="num">~57,000 DWT</td></tr>
      </table>
      <p style="font-size:0.82em;color:#666;margin-top:6px;">
        Geared for self-discharge at unequipped terminals. Dominant size for US Gulf fertilizer imports
        and grain exports. Can transit Panama Canal (beam constraint). 5 holds = 5 FGIS per-hold inspections.
      </p>
    </div>
    <div>
      <h3>Ultramax (Modern Supramax)</h3>
      <table class="rt">
        <tr><td>DWT range</td><td class="num">60,000 – 67,000 DWT</td></tr>
        <tr><td>LOA</td><td class="num">~199 – 200 m</td></tr>
        <tr><td>Holds</td><td class="num">5 holds, 5 hatches</td></tr>
        <tr><td>Gear</td><td class="num">4 × 36t cranes typical</td></tr>
        <tr><td>DWT (dataset median)</td><td class="num">~61,000 – 63,000 DWT</td></tr>
      </table>
      <p style="font-size:0.82em;color:#666;margin-top:6px;">
        Wider beam (32.26 m), larger hold volume than classic Supramax. Increasing share of US Gulf
        grain book since 2018. Both types share the same FGIS/NCB inspection regime and cleaning protocols.
      </p>
    </div>
  </div>
  <div class="info" style="margin-top:14px;">
    <strong>Dataset basis:</strong> 7,701 voyage records for Supramax/Ultramax vessels in the USACE MRTIS movement dataset.
    DWT range 50,169 – 66,832 DWT; median 60,481 DWT. Ship register: 3,662 Supramax/Ultramax vessels identified from 52,034-vessel Lloyd's-style register.
  </div>

  <h3>Typical US Gulf Trade Patterns</h3>
  <div class="g3" style="margin-top:8px;">
    <div style="background:#f0f4f9;border-radius:7px;padding:14px;">
      <div style="font-weight:700;color:#1a2f4e;margin-bottom:6px;">Inbound (Import) Trades</div>
      <ul style="padding-left:16px;font-size:0.85em;line-height:1.9;color:#444;">
        <li>Steel products / pig iron (Brazil, Turkey, CIS)</li>
        <li>Nitrogen fertilizers — urea, UAN (Middle East, Russia)</li>
        <li>Phosphate fertilizers — DAP, MAP (Morocco, Russia)</li>
        <li>Potassium fertilizers — MOP (Canada, Belarus)</li>
        <li>Cement (Mexico, Europe)</li>
        <li>Manganese ore (Gabon, South Africa)</li>
        <li>Aggregates, salt, sugar, talc</li>
      </ul>
    </div>
    <div style="background:#f0f8f4;border-radius:7px;padding:14px;">
      <div style="font-weight:700;color:#2c5f2e;margin-bottom:6px;">Outbound (Export) Trades</div>
      <ul style="padding-left:16px;font-size:0.85em;line-height:1.9;color:#444;">
        <li><strong>Grain</strong> — #1 export. Corn, soybeans, wheat, sorghum</li>
        <li><strong>Petcoke</strong> — refinery by-product, Gulf Coast refineries</li>
        <li><strong>Coal</strong> — steam and met coal (IMT Coal Terminal)</li>
        <li><strong>Biomass</strong> — wood pellets (Drax, Enviva)</li>
        <li>Fertilizers (export, less common for this size)</li>
      </ul>
    </div>
    <div style="background:#fdf6ee;border-radius:7px;padding:14px;">
      <div style="font-weight:700;color:#856404;margin-bottom:6px;">The Cleaning Trigger</div>
      <ul style="padding-left:16px;font-size:0.85em;line-height:1.9;color:#444;">
        <li>Vessel discharges import cargo at river buoy anchorage</li>
        <li>Goes to cleaning anchorage (or commences en route)</li>
        <li>FGIS/NCB inspection at US grain port</li>
        <li>Loads grain at elevator terminal</li>
        <li>Grain = highest cleanliness standard of all bulk cargoes</li>
        <li>Gap between discharge and grain load: <strong>4–18 days typical</strong></li>
      </ul>
    </div>
  </div>
</div>


<!-- ═══ 2. CARGO PATTERNS ═══ -->
<div class="card" id="patterns">
  <h2><span class="num">2</span> Cargo Patterns — USACE Voyage Data Analysis</h2>
  <p style="font-size:0.85em;color:#666;margin-bottom:14px;">
    Source: 41,156 USACE MRTIS voyage records filtered to Supramax/Ultramax vessel segment.
    1,413 discharge operations and 3,374 loading operations identified.
  </p>

  <div class="g2">
    <div>
      <h3>What Supramaxes Discharge (Import Cargo) — Top 15</h3>
      <p style="font-size:0.8em;color:#777;margin-bottom:8px;">
        These are the cargoes that must be cleaned out before grain can be loaded.
      </p>
"""

for cargo, n, risk in IMPORT_CARGO:
    bg, fg, _ = RC.get(risk, ("#eee","#333",""))
    pct = int(n / MAX_IMPORT * 100)
    html += f"""      <div class="bar-row">
        <div class="bar-lbl">{cargo}</div>
        <div class="bar-w"><div class="bar-f" style="width:{pct}%;background:{fg};"></div></div>
        <span class="bar-n">{n} &nbsp;{badge(risk)}</span>
      </div>
"""

html += """      <p style="font-size:0.78em;color:#888;margin-top:8px;">
        <strong>Steel &amp; pig iron dominate</strong> (103 records combined = 35% of identified discharges) — LOW risk to clean.
        <strong>All fertilizer grades combined</strong> (106 = 36%) — MEDIUM risk, MARPOL HME wash water concern.
        <strong>Cement</strong> (24 = 8%) — HIGH risk, portable pump mandatory.
      </p>
    </div>

    <div>
      <h3>Where Supramaxes Load (Grain Export Terminals)</h3>
      <p style="font-size:0.8em;color:#777;margin-bottom:8px;">
        Virtually all loading is at Lower Mississippi River grain elevators — every one requires FGIS/NCB certification.
      </p>
"""

for lp, n, cargo_type in LOAD_PORTS:
    color = "#2c5f2e" if cargo_type == "grain" else ("#5c3d2e" if "coal" in cargo_type else "#1a5e7a")
    pct = int(n / MAX_LP * 100)
    html += f"""      <div class="bar-row">
        <div class="bar-lbl" style="font-size:0.8em;">{lp}</div>
        <div class="bar-w"><div class="bar-f" style="width:{pct}%;background:{color};"></div></div>
        <span class="bar-n">{n}</span>
      </div>
"""

html += """      <p style="font-size:0.78em;color:#888;margin-top:8px;">
        <strong>Grain elevators</strong> (Zen-Noh, ADM, Bunge, United Bulk, Cargill, etc.) account for ~85% of loads.
        IMT Coal (123) = coal/petcoke exports. Drax Biomass (70) = wood pellets. All grain terminals require USDA FGIS stowage exam.
      </p>
    </div>
  </div>

  <h3>Where Supramaxes Discharge on the Lower Mississippi</h3>
  <p style="font-size:0.82em;color:#666;margin-bottom:8px;">
    Import cargoes are discharged at river anchorage buoy berths — vessels then proceed upriver or to nearby port for cleaning.
  </p>
  <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px;">
"""

for dz, n in DISCHARGE_ZONES:
    pct = int(n / MAX_DZ * 100)
    html += f"""    <div style="background:#f0f4f9;border-radius:6px;padding:10px 14px;min-width:180px;flex:1;">
      <div style="font-size:0.82em;font-weight:700;color:#1a2f4e;margin-bottom:4px;">{dz}</div>
      <div class="bar-w" style="width:100%;"><div class="bar-f" style="width:{pct}%;background:#1a2f4e;"></div></div>
      <div style="font-size:0.78em;color:#666;margin-top:3px;">{n} discharge operations</div>
    </div>
"""

html += """  </div>
  <div class="info">
    <strong>Operational pattern:</strong> Vessel arrives laden at Lower Mississippi River entrance (Southwest Pass),
    crosses bar, proceeds upriver to anchorage/buoy berth for discharge. After discharge the vessel is either cleaned
    at anchor (en route cleaning) or dropped to a shipyard/cleaning berth before proceeding to the grain elevator.
    Total turnaround gap 25th percentile: ~4 days; median: ~18 days.
  </div>
</div>


<!-- ═══ 3. CLEANLINESS STANDARDS ═══ -->
<div class="card" id="standards">
  <h2><span class="num">3</span> Cargo Hold Cleanliness Standards</h2>
  <div class="std-grid">
    <div class="std-box" style="background:#fde8e8;border:2px solid #991b1b;">
      <div class="rank" style="color:#991b1b;">1</div>
      <div class="name" style="color:#991b1b;">HOSPITAL CLEAN</div>
      <div class="desc">White-glove standard. No dust, stain, odor, rust scale, or any trace of previous cargo.<br><br>
        <strong>Required for:</strong> Soda ash (sodium carbonate), kaolin, mineral sands, rice (premium),
        high-grade wood pulp, titanium dioxide, food-grade cargo.<br><br>
        Surveyor inspection is very stringent. Shore gang almost always required.
      </div>
    </div>
    <div class="std-box" style="background:#fff3cd;border:2px solid #856404;">
      <div class="rank" style="color:#856404;">2</div>
      <div class="name" style="color:#856404;">GRAIN CLEAN</div>
      <div class="desc">The most common standard in US Gulf. Mandatory for all US grain exports.<br><br>
        <strong>Required for:</strong> All grains and oilseeds (corn, soybeans, wheat, sorghum), alumina,
        sulphur, cement clinker, fertilizers, animal feeds.<br><br>
        FGIS/NCB inspection is mandatory and legally required under US law (7 CFR Part 800).
      </div>
    </div>
    <div class="std-box" style="background:#d4edda;border:2px solid #155724;">
      <div class="rank" style="color:#155724;">3</div>
      <div class="name" style="color:#155724;">NORMAL CLEAN</div>
      <div class="desc">Standard commercial cleanliness. Previous cargo residues removed, no significant contamination risk.<br><br>
        <strong>Required for:</strong> Most general bulk cargoes where CP does not specify higher standard.<br><br>
        Suitable for coal, iron ore, ores when no commodity sensitivity.
      </div>
    </div>
    <div class="std-box" style="background:#e8f4fd;border:2px solid #1a6dd4;">
      <div class="rank" style="color:#1a6dd4;">4</div>
      <div class="name" style="color:#1a6dd4;">SHOVEL CLEAN</div>
      <div class="desc">Bulk of cargo removed by shovel/bulldozer. Residues remaining acceptable.<br><br>
        <strong>Used for:</strong> Coal, iron ore, ores in repeat COA trades where
        contamination standard is low.<br><br>
        Not suitable before any grain, fertilizer, or white cargo.
      </div>
    </div>
    <div class="std-box" style="background:#f0f0f0;border:2px solid #888;">
      <div class="rank" style="color:#888;">5</div>
      <div class="name" style="color:#888;">LOAD ON TOP</div>
      <div class="desc">Same commodity COA trade. New cargo loaded directly over residue of previous cargo without cleaning.<br><br>
        <strong>Permitted only when:</strong> Same commodity, same shipper, same trade, charterer accepts.<br><br>
        Common in coal and iron ore COA trades. Never permitted for grain.
      </div>
    </div>
  </div>
  <div class="warn-box" style="margin-top:14px;">
    <strong>Key principle:</strong> The required cleanliness standard is determined by the NEXT cargo to be loaded, not the previous cargo.
    However, the previous cargo determines how difficult (and expensive) it is to achieve that standard.
    The cargo compatibility matrix at Section 4 links these two dimensions.
  </div>
</div>


<!-- ═══ 4. COMPATIBILITY MATRIX ═══ -->
<div class="card" id="matrix">
  <h2><span class="num">4</span> Cargo Compatibility Matrix — Previous → Next Cargo</h2>
  <p style="font-size:0.85em;color:#666;margin-bottom:12px;">
    All 55 transition pairs. Source: UK P&amp;I Club, Skuld P&amp;I, Swedish Club, IMSBC Code, USDA FGIS, Isbester <em>Bulk Carrier Practice</em> (Nautical Institute, 1993).
    Risk level reflects difficulty of achieving required cleanliness standard, not contamination risk to next cargo per se.
  </p>
  <div style="overflow-x:auto;">
  <table class="mt">
    <thead>
      <tr>
        <th>Previous Cargo</th>
        <th>Next Cargo</th>
        <th>Risk</th>
        <th>Cleaning Requirement</th>
        <th>FGIS?</th>
        <th>Chemical Wash?</th>
        <th>Days Lost</th>
        <th>Notes</th>
      </tr>
    </thead>
    <tbody>
""" + matrix_table() + """    </tbody>
  </table>
  </div>
  <p style="font-size:0.78em;color:#888;margin-top:8px;">
    Days lost = estimated cleaning duration from field benchmarks (Isbester 1993, P&I Club circulars).
    Excludes FGIS inspection scheduling time (typically add 0.5–1.0 day at US grain ports).
    FGIS = USDA Federal Grain Inspection Service / NCB mandatory for all US grain export voyages.
  </p>
</div>


<!-- ═══ 5. CLEANING METHODS ═══ -->
<div class="card" id="methods">
  <h2><span class="num">5</span> Cleaning Methods &amp; Protocols</h2>

  <h3>The Five-Phase Cleaning Sequence</h3>
  <div class="phases">
    <div class="phase">
      <div class="ph-num">1</div>
      <div class="ph-name">Sweeping &amp; Mucking Out</div>
      <div class="ph-body">Remove all loose residue, debris, dunnage. Manual brooms + shovel gangs. Start at top (coaming) and work down. Check behind frames, ladders, pipe guards. Bilge wells critical — remove all fines.
        <br><br><em>Time: 2–8 hrs per hold depending on cargo type and hold condition.</em>
      </div>
    </div>
    <div class="phase">
      <div class="ph-num">2</div>
      <div class="ph-name">Seawater Wash</div>
      <div class="ph-body">High-pressure seawater applied top-to-bottom. Dislodges attached residue and flushes bilge wells. Most effective method for dusty cargoes (fertilizer, alumina, bauxite).
        <br><br><em>Seawater use: ~30–50 tonnes per hold. En route preferred (MARPOL position compliance).</em>
      </div>
    </div>
    <div class="phase">
      <div class="ph-num">3</div>
      <div class="ph-name">Chemical Wash<br><small>(when required)</small></div>
      <div class="ph-body">Alkaline cleaner (Unitor CargoClean HD or equivalent) at 5–10% concentration. Applied after seawater pre-wash. Let dwell 30–60 min. Scrub stubborn patches. Required for coal, petcoke, fishmeal.
        <br><br><em>All chemical wash water = HME under MARPOL. Discharge to port reception facility.</em>
      </div>
    </div>
    <div class="phase">
      <div class="ph-num">4</div>
      <div class="ph-name">Fresh Water Rinse</div>
      <div class="ph-body">Final rinse with fresh water to remove all chemical residue and salinity. Mandatory before grain and hospital-clean cargoes. ~30t fresh water per hold.
        <br><br><em>CP clause: 'Hold Washing — For Charterer's Account' covers fresh water use.</em>
      </div>
    </div>
    <div class="phase">
      <div class="ph-num">5</div>
      <div class="ph-name">Drying &amp; Ventilation</div>
      <div class="ph-body">Holds must be dry before grain loading — moisture causes heating and spoilage. Open hatches + ventilators. In humid conditions, fan ventilation required. Sulphur cargo especially: thorough drying mandatory.
        <br><br><em>Allow 12–24 hrs drying in hot Gulf conditions.</em>
      </div>
    </div>
  </div>

  <div class="g2" style="margin-top:16px;">
    <div>
      <h3>Three Physical Washing Methods (Isbester, 1993)</h3>
      <div style="background:#f8f9fb;border:1px solid #e0e4ea;border-radius:7px;padding:14px;font-size:0.88em;">
        <p style="margin-bottom:8px;"><strong>Method 1 — Handheld Hose</strong><br>
        Two men with hoses wash top-to-bottom. Slowest but most thorough for difficult corners.
        Standard on most tramps. 40–80 PSI seawater. Good for grain-to-grain trades.</p>
        <p style="margin-bottom:8px;"><strong>Method 2 — Water Cannon / Combi-Gun</strong><br>
        High-pressure gun (Combi-gun or equivalent) operated from hatch coaming.
        Rapid coverage of large flat surfaces. Less effective in bilge wells and corners.
        Best for coal, ore, bauxite. 500–1,000 PSI.</p>
        <p><strong>Method 3 — Permanent Deck Washing Installation</strong><br>
        Factory-fitted spray nozzles on hold frames (less common on older Supramaxes).
        Fastest but relies on nozzle coverage — supplementary manual work still needed at corners and bilges.</p>
      </div>
    </div>
    <div>
      <h3>Time Benchmarks (Isbester; P&I Club data)</h3>
      <table class="rt">
        <thead><tr><th>Vessel / Scenario</th><th>Crew</th><th>Time</th></tr></thead>
        <tbody>
          <tr><td>Handy/Panamax to normal standard</td><td>3–4 men</td><td>1 day/hold</td></tr>
          <tr><td>Mini-bulker to grain standard</td><td>2–3 men</td><td>4–5 hrs/hold</td></tr>
          <tr><td>Supramax coal → grain (5 holds)</td><td>Shore gang</td><td>48–72 hrs total</td></tr>
          <tr><td>Supramax petcoke → grain (5 holds)</td><td>Shore gang</td><td>60–96 hrs total</td></tr>
          <tr><td>Cement → grain (portable pump)</td><td>Shore gang</td><td>36–60 hrs total</td></tr>
          <tr><td>Fishmeal → grain (enzymatic)</td><td>Shore gang</td><td>48–72 hrs + ventilation</td></tr>
          <tr><td>Steel/fertilizer → grain (crew)</td><td>Crew</td><td>12–24 hrs total</td></tr>
        </tbody>
      </table>
      <div class="info" style="margin-top:10px;">
        <strong>Note on Regina Oldendorff benchmark (Isbester, p.70):</strong>
        Full fresh water rinse of a Panamax consumed approximately 50 tonnes of fresh water total across all holds.
        At ~30t/hold for a 5-hold Supramax = 150t total for full fresh water rinse.
      </div>
    </div>
  </div>

  <h3>Limewash Application</h3>
  <div class="g2">
    <div class="warn-box">
      <strong>Recipe (Isbester, Ch.5):</strong> 1 part Ca(OH)₂ (slaked lime) : 3 parts fresh water.<br>
      <strong>Apply before:</strong> Salt, sulphur, and repeated use of same corrosive cargo.<br>
      <strong>Method:</strong> Paint onto hold steel surfaces with brush or spray after cleaning;
      forms a protective calcium carbonate coating that prevents rust staining and cargo discolouration.<br>
      <strong>Note:</strong> Must be applied to clean, dry holds. Wash off before next inert cargo.
    </div>
    <div class="info">
      <strong>When required in US Gulf context:</strong><br>
      Salt sodium chloride → any cargo: if hold steel showing rust discolouration from salt corrosion, limewash protects the hold AND prevents calcium-white staining on the next cargo.
      Particularly important before grain loading after a salt discharge if hold has corrosion damage.
    </div>
  </div>
</div>


<!-- ═══ 6. WHERE TO CLEAN ═══ -->
<div class="card" id="location">
  <h2><span class="num">6</span> Where Cleaning Happens — Location &amp; MARPOL Constraints</h2>
  <div class="g3">
    <div style="background:#f0f8f4;border-radius:7px;padding:14px;border:1px solid #b7dfbf;">
      <strong style="color:#2c5f2e;">✓ En Route (At Sea)</strong>
      <p style="font-size:0.85em;margin-top:6px;color:#333;">
        Preferred option. Vessel cleans during ballast voyage before arriving at load port.
        MARPOL non-HME wash water can be discharged at &gt;12 nm from land.
        Maximises time at load berth. Requires adequate ballast passage time (typically ≥3 days).
      </p>
    </div>
    <div style="background:#fff8e1;border-radius:7px;padding:14px;border:1px solid #ffe08a;">
      <strong style="color:#856404;">⚠ At Anchorage (In Port)</strong>
      <p style="font-size:0.85em;margin-top:6px;color:#333;">
        Common at Mississippi River anchorage buoys. Vessel cleans at anchor while awaiting
        FGIS inspection or berth availability. Seawater wash water may need to be pumped to
        port reception facility depending on cargo type.
        <strong>Increasing number of ports require written permission before washing.</strong>
      </p>
    </div>
    <div style="background:#fde8e8;border-radius:7px;padding:14px;border:1px solid #f5a0a0;">
      <strong style="color:#991b1b;">⚡ At Shipyard / Cleaning Berth</strong>
      <p style="font-size:0.85em;margin-top:6px;color:#333;">
        Required for coal → grain, petcoke → grain, fishmeal → grain, cement → grain.
        Shore gang mobilised. All wash water pumped to port reception (HME classification).
        Higher cost but necessary when hold condition cannot be achieved by crew alone.
      </p>
    </div>
  </div>

  <h3>MARPOL Position Requirements for Wash Water Discharge</h3>
  <table class="rt" style="margin-top:8px;">
    <thead>
      <tr><th>Cargo Type</th><th>MARPOL Category</th><th>Discharge Rules</th><th>Gulf of Mexico Special Area</th></tr>
    </thead>
    <tbody>
      <tr><td>Coal, petcoke, fertilizers (HME)</td><td>HME (Harmful to Marine Environment)</td>
          <td style="color:#991b1b;font-weight:600;">PROHIBITED — port reception facility mandatory</td>
          <td>Same — no at-sea discharge regardless of position</td></tr>
      <tr><td>Grain, steel, iron ore (non-HME)</td><td>Non-HME</td>
          <td>Permitted at sea: &gt;12 nm from nearest land, en route, minimum 4 knots</td>
          <td style="color:#856404;">Gulf of Mexico = MARPOL Special Area — stricter; check with agent before discharge</td></tr>
      <tr><td>Chemical wash water (any cargo)</td><td>Always treated as HME</td>
          <td style="color:#991b1b;">PROHIBITED at sea — port reception facility mandatory regardless of position</td>
          <td>Same restriction applies</td></tr>
      <tr><td>Sulphur (HME)</td><td>HME</td>
          <td style="color:#991b1b;">PROHIBITED — port reception facility mandatory</td>
          <td>Same</td></tr>
    </tbody>
  </table>
  <div class="info" style="margin-top:10px;">
    <strong>Authority:</strong> MARPOL Annex V, 2013 amendment (in force 1 Jan 2013, 2022 consolidated edition).
    The Gulf of Mexico and Caribbean Sea are designated MARPOL Special Areas under Annex V.
    Always verify current Special Area boundaries and exceptions with port agent before departure.
  </div>
</div>


<!-- ═══ 7. FGIS/NCB ═══ -->
<div class="card" id="fgis">
  <h2><span class="num">7</span> FGIS / NCB Mandatory Inspection — US Grain Exports</h2>
  <div class="crit-box">
    <strong>MANDATORY LEGAL REQUIREMENT:</strong> All vessels loading grain for US export are subject to
    USDA Federal Grain Inspection Service (FGIS) stowage examination under 7 CFR Part 800.
    No US grain elevator will load a vessel without a valid FGIS Stowage Examination Certificate.
    There is no waiver or exception.
  </div>
  <div class="g2" style="margin-top:14px;">
    <div>
      <h3>Four Mandatory FGIS/NCB Line Items</h3>
      <table class="rt">
        <thead><tr><th>Service</th><th>Basis</th><th>Typical Fee (Panamax/Supra)</th></tr></thead>
        <tbody>
          <tr><td>USDA FGIS Stowage Examination<br><small>Vessel cleanliness certification</small></td>
              <td>Per vessel by DWT</td><td>$417 – $1,067</td></tr>
          <tr><td>NCB Certificate of Readiness<br><small>Structure, bilges, stability, gear</small></td>
              <td>Per vessel by DWT</td><td>$750 – $1,850</td></tr>
          <tr><td>USDA Per-Hold Cleanliness Certificate<br><small>Each hold inspected individually</small></td>
              <td>Per hold</td><td>$260/hold (5 holds = $1,300)</td></tr>
          <tr><td>Reinspection Reserve<br><small>High-risk previous cargo</small></td>
              <td>Per inspection event</td><td>$250 (coal, petcoke, cement)</td></tr>
          <tr style="font-weight:700;background:#f0f4f9;"><td colspan="2">TOTAL — 5-hold Supramax</td>
              <td>$2,727 – $4,467</td></tr>
        </tbody>
      </table>
    </div>
    <div>
      <h3>FGIS Inspection Process</h3>
      <ol style="padding-left:18px;font-size:0.88em;line-height:1.9;color:#444;">
        <li>Vessel notifies agent of hold cleaning completion</li>
        <li>Agent schedules FGIS inspector (typically 0.5–1.0 day wait)</li>
        <li>FGIS inspector boards and examines ALL holds:
          <ul style="padding-left:16px;margin:4px 0;">
            <li>Visual inspection: residue, staining, loose scale, odor</li>
            <li>Bilge wells: must be clean and dry</li>
            <li>Hold structure: no loose paint, scale, or contamination</li>
            <li>Dunnage and separation materials removed</li>
          </ul>
        </li>
        <li>If holds PASS → Certificate issued → vessel proceeds to berth</li>
        <li>If holds FAIL → additional cleaning required → re-inspection (extra fee)</li>
      </ol>
      <div class="warn-box" style="margin-top:8px;">
        <strong>Failure consequence:</strong> Vessel cannot berth at US grain terminal until FGIS certificate is obtained.
        Detention at anchor. Off-hire risk under charter party.
        Coal/petcoke previous cargoes have highest re-inspection rates — budget accordingly.
      </div>
    </div>
  </div>
  <h3>Who Is NCB?</h3>
  <p style="font-size:0.88em;color:#444;margin-top:6px;">
    The <strong>National Cargo Bureau (NCB)</strong> is a non-profit maritime safety organization designated by the USCG
    to conduct grain stowage plan reviews and issue Certificates of Readiness. The NCB inspection covers stability
    calculations (grain loading plan), bilge pumping systems, ventilation, and structural adequacy for grain stowage.
    NCB has representatives at all major US grain export ports.
  </p>
</div>


<!-- ═══ 8. MARPOL ═══ -->
<div class="card" id="marpol">
  <h2><span class="num">8</span> MARPOL Annex V Compliance</h2>
  <div class="g2">
    <div>
      <h3>HME Classification — The Critical Test</h3>
      <p style="font-size:0.87em;color:#444;margin-bottom:10px;">
        Under MARPOL Annex V (2013 amendment), all solid bulk cargo residues and washings are classified
        as either <strong>HME (Harmful to Marine Environment)</strong> or non-HME. This determines whether
        wash water can be discharged at sea or must go to port reception facility.
      </p>
      <table class="rt">
        <thead><tr><th>Cargo</th><th>HME Status</th><th>Action</th></tr></thead>
        <tbody>
          <tr><td>Coal</td><td style="color:#991b1b;font-weight:700;">HME</td><td>Port reception ONLY</td></tr>
          <tr><td>Petroleum coke (petcoke)</td><td style="color:#991b1b;font-weight:700;">HME</td><td>Port reception ONLY</td></tr>
          <tr><td>Fertilizers (urea, DAP, MAP, MOP)</td><td style="color:#991b1b;font-weight:700;">HME</td><td>Port reception ONLY</td></tr>
          <tr><td>Sulphur</td><td style="color:#991b1b;font-weight:700;">HME</td><td>Port reception ONLY</td></tr>
          <tr><td>Phosphate rock</td><td style="color:#991b1b;font-weight:700;">HME (verify grade)</td><td>Port reception ONLY</td></tr>
          <tr><td>Iron ore / steel</td><td style="color:#155724;font-weight:700;">Non-HME</td><td>At sea permitted (&gt;12 nm)</td></tr>
          <tr><td>Grain</td><td style="color:#155724;font-weight:700;">Non-HME</td><td>At sea permitted (&gt;12 nm)</td></tr>
          <tr><td>Bauxite</td><td style="color:#155724;font-weight:700;">Non-HME</td><td>At sea permitted (&gt;12 nm)</td></tr>
          <tr><td>Cement / clinker</td><td style="color:#155724;font-weight:700;">Non-HME</td><td>At sea permitted (&gt;12 nm)</td></tr>
          <tr><td>Chemical wash water</td><td style="color:#991b1b;font-weight:700;">Always HME</td><td>Port reception ONLY</td></tr>
        </tbody>
      </table>
    </div>
    <div>
      <h3>Record-Keeping Requirements</h3>
      <p style="font-size:0.87em;color:#444;margin-bottom:8px;">
        MARPOL Annex V requires entries in the <strong>Garbage Record Book (GRB)</strong> for all cargo residue
        and cleaning water discharges. Failure to maintain records = USCG violation.
      </p>
      <div class="info">
        <strong>Required GRB entries:</strong><br>
        — Date, time, position of discharge<br>
        — Cargo residue type (HME / non-HME)<br>
        — Approximate quantity discharged<br>
        — Port reception facility receipts (for HME discharges)
      </div>
      <h3 style="margin-top:14px;">Ammonium Nitrate — Special Concern</h3>
      <div class="crit-box">
        <strong>Ammonium nitrate-grade fertilizers</strong> may be classified as Hazardous Materials for Emergency
        Response (HME) under MARPOL AND as <strong>dangerous goods under IMSBC</strong>.
        Verify grade with shipper before accepting cargo.
        Technical-grade AN (fertilizer) is IMSBC Group B. High-density AN (HDAN) is more restricted.
        Wash water from AN-grade fertilizer: treat as HME — port reception facility mandatory.
      </div>
      <h3 style="margin-top:14px;">Gulf of Mexico Special Area</h3>
      <div class="warn-box">
        The Gulf of Mexico is a MARPOL Annex V Special Area. Even for non-HME cargoes,
        additional restrictions may apply. <strong>Always verify current rules with port agent
        before discharging any cargo residue washings in the Gulf.</strong>
      </div>
    </div>
  </div>
</div>


<!-- ═══ 9. CRITICAL CONCERNS ═══ -->
<div class="card" id="concerns">
  <h2><span class="num">9</span> Critical Operational Concerns &amp; Safety Hazards</h2>
  <div class="concern-grid">

    <div class="concern" style="background:#fde8e8;border-color:#f5a0a0;">
      <strong style="color:#991b1b;">🚨 COPPER CONCENTRATE — DO NOT WASH</strong>
      <p style="font-size:0.85em;margin-top:6px;color:#333;">
        <strong>Isbester (Ch.5, p.71) CRITICAL WARNING:</strong> If copper concentrate is wetted and
        then dries, it forms a concrete-like layer on hold sides and floors that is virtually impossible to remove without
        abrasive disc grinding. <strong>DO NOT apply any water or seawater wash.</strong><br><br>
        <strong>Correct procedure:</strong> Compressed air blow-out + sweep only. Shore gang with abrasive disc
        grinders mandatory if water contact has occurred. Allow extra 3+ days for removal of hardened deposits.
      </p>
    </div>

    <div class="concern" style="background:#fde8e8;border-color:#f5a0a0;">
      <strong style="color:#991b1b;">🚨 CEMENT / CEMENT CLINKER — NO BILGE PUMP</strong>
      <p style="font-size:0.85em;margin-top:6px;color:#333;">
        <strong>CRITICAL:</strong> When cement or clinker dust contacts water it sets into concrete.
        Pumping cement slurry through the bilge pump will destroy the pump impeller and may block
        bilge lines completely. <strong>A portable salvage pump must be used to remove wash water
        from cement holds.</strong><br><br>
        Procedure: Dry sweep first (mandatory). Then water wash. Pump all wash water out with portable
        pump only. Never activate bilge pump.
      </p>
    </div>

    <div class="concern" style="background:#fff8e1;border-color:#ffe08a;">
      <strong style="color:#856404;">⚠ SULPHUR — PPE MANDATORY</strong>
      <p style="font-size:0.85em;margin-top:6px;color:#333;">
        When sulphur is washed with water it forms dilute <strong>sulphurous acid (H₂SO₃)</strong>,
        which is corrosive to skin, eyes, and respiratory tract. Full PPE is mandatory throughout
        the cleaning operation: respirator, chemical splash goggles, gloves, coveralls.<br><br>
        Hold must be thoroughly dried after washing. Residual acid accelerates hold corrosion.
      </p>
    </div>

    <div class="concern" style="background:#fff8e1;border-color:#ffe08a;">
      <strong style="color:#856404;">⚠ COAL FINE — DUAL IMSBC HAZARD</strong>
      <p style="font-size:0.85em;margin-top:6px;color:#333;">
        Coal with ≥75% particles &lt;5mm is classified as BOTH IMSBC Group A (liquefaction risk)
        AND Group B (chemical hazard — self-heating, methane emission). Cleaning is more aggressive
        than standard coal: same alkaline chemical protocol but with additional time allowance for
        complete removal of all fines from bilge wells and frames.<br><br>
        <strong>Check cargo description carefully</strong> — shipper must specify whether coal is fine or coarse.
      </p>
    </div>

    <div class="concern" style="background:#fff8e1;border-color:#ffe08a;">
      <strong style="color:#856404;">⚠ FISHMEAL — ODOR PENETRATION</strong>
      <p style="font-size:0.85em;margin-top:6px;color:#333;">
        Fishmeal oils penetrate steel and dunnage material. Odor cannot be removed by water wash alone.
        <strong>Enzymatic cleaner is mandatory</strong> (e.g., Unitor Biobor or equivalent).
        Apply concentrated enzymatic solution, allow 4–6 hour dwell time, then wash.
        Ventilate thoroughly — allow 24–48 hrs ventilation in addition to wash time.
        Shore gang almost always required for grain-clean standard.
      </p>
    </div>

    <div class="concern" style="background:#fff8e1;border-color:#ffe08a;">
      <strong style="color:#856404;">⚠ PORT WASHING RESTRICTIONS</strong>
      <p style="font-size:0.85em;margin-top:6px;color:#333;">
        An increasing number of US and international ports <strong>prohibit cargo hold washing
        within port limits</strong> without prior written permission from the port authority (obtained
        via ship's agent). Violations result in fines and possible vessel detention.<br><br>
        <strong>Best practice:</strong> Always confirm with port agent whether hold washing is permitted
        at anchorage before commencing. Mississippi River anchorage restrictions have tightened post-2020.
      </p>
    </div>

    <div class="concern" style="background:#f0f4f9;border-color:#b0c4de;">
      <strong style="color:#1a2f4e;">ℹ PETCOKE vs. COAL</strong>
      <p style="font-size:0.85em;margin-top:6px;color:#333;">
        Petroleum coke (petcoke) is harder to clean than coal. High-sulfur residues with oily
        binding agents resist alkaline wash more than coal dust. Multiple wash cycles required (60–96 hrs).
        If petcoke previously carried, budget for more cleaning time and higher chemical consumption
        than coal.<br><br>
        Petcoke is an HME cargo — all wash water to port reception facility.
      </p>
    </div>

    <div class="concern" style="background:#f0f4f9;border-color:#b0c4de;">
      <strong style="color:#1a2f4e;">ℹ BILGE WELL MANAGEMENT</strong>
      <p style="font-size:0.85em;margin-top:6px;color:#333;">
        Bilge wells are the most common FGIS inspection failure point. Any residue in bilge wells =
        inspection failure. For all cargo types: after sweep, manually remove bilge covers and
        clean wells by hand. For iron ore, pay particular attention to fines packed behind
        stringers and frames. For cement, pump bilge wells dry with portable pump before inspection.<br><br>
        <em>Source: US grain elevator operators report bilge wells as #1 cause of hold rejection.</em>
      </p>
    </div>

  </div>
</div>


<!-- ═══ 10. VENDOR DIRECTORY ═══ -->
<div class="card" id="vendors">
  <h2><span class="num">10</span> Vendor Directory — US Gulf Hold Cleaning</h2>
  <p style="font-size:0.85em;color:#666;margin-bottom:4px;">
    Source: web research March 2026. Data verified against company websites.
    File: <code>data/vendors_us_gulf.csv</code>
    <br><em>Pending additions: cleaning material/chemical suppliers (specific US distributors), launch hire companies.
    Note: Intership is a Cyprus-based ship management company — no US Gulf hold cleaning vendor match found for this name.</em>
  </p>
""" + vendor_section() + """
</div>


<!-- ═══ 11. RATE REFERENCE ═══ -->
<div class="card" id="rates">
  <h2><span class="num">11</span> Rate Reference — US Gulf &amp; East Coast Ports</h2>
  <p style="font-size:0.85em;color:#666;margin-bottom:12px;">
    All rates per hold per operation. Source: industry benchmarks, William S. Davis III empirical data, 2024.
    Crew rates = vessel's own crew performing cleaning. Shore gang = contracted cleaning gang mobilised from port.
  </p>
  <div class="g2">
    <div>
      <h3>New Orleans (Mississippi River)</h3>
      <table class="rt">
        <thead><tr><th>Operation</th><th>Crew ($/hold)</th><th>Shore Gang ($/hold)</th></tr></thead>
        <tbody>
          <tr><td>Sweep per hold</td><td>$200–$500</td><td>—</td></tr>
          <tr><td>Seawater wash</td><td>$300–$650</td><td>$800–$1,800</td></tr>
          <tr><td>Fresh water wash</td><td>$400–$900</td><td>$1,000–$2,200</td></tr>
          <tr><td>Chemical wash (alkaline)</td><td>$600–$1,400</td><td>$1,200–$2,800</td></tr>
          <tr><td>Enzymatic wash (fishmeal)</td><td>$800–$1,800</td><td>$1,500–$3,200</td></tr>
          <tr><td>Scale removal</td><td>—</td><td>$800–$2,500</td></tr>
          <tr><td>Fumigation</td><td colspan="2">$800–$2,000 (certified contractor)</td></tr>
        </tbody>
      </table>
    </div>
    <div>
      <h3>Houston / Hampton Roads / Other Ports</h3>
      <table class="rt">
        <thead><tr><th>Port</th><th>Sweep</th><th>Seawater Wash</th><th>Chemical Wash</th></tr></thead>
        <tbody>
          <tr><td>Houston</td><td>$200–$480</td><td>$300–$600</td><td>$600–$1,350</td></tr>
          <tr><td>Corpus Christi</td><td>$175–$450</td><td>$275–$575</td><td>$550–$1,250</td></tr>
          <tr><td>Hampton Roads</td><td>$225–$550</td><td>$325–$700</td><td>$650–$1,500</td></tr>
          <tr><td>Baltimore</td><td>$250–$575</td><td>$350–$750</td><td>$700–$1,550</td></tr>
          <tr><td>Savannah</td><td>$200–$500</td><td>$300–$650</td><td>$600–$1,400</td></tr>
          <tr><td>Portland OR</td><td>$225–$550</td><td>$325–$700</td><td>$675–$1,525</td></tr>
          <tr><td>Duluth</td><td>$200–$500</td><td>$275–$625</td><td>$575–$1,325</td></tr>
        </tbody>
      </table>
    </div>
  </div>
  <div class="info" style="margin-top:10px;">
    Rates are indicative benchmarks. Actual rates vary by: (1) volume of work, (2) vessel schedule flexibility,
    (3) chemical consumption (not included in chemical wash rate), (4) season and labor availability,
    (5) whether portable pump is required. Shore gang rates include equipment and supervision.
  </div>
</div>


<!-- ═══ 12. SOURCES ═══ -->
<div class="card" id="sources">
  <h2><span class="num">12</span> Sources &amp; Knowledge Base</h2>
  <div class="g2">
    <div>
      <h3>Primary Reference Textbooks</h3>
      <div class="src-grid">
        <div class="src-item"><strong>Bulk Carrier Practice</strong><br>J. Isbester, Nautical Institute, 1993<br><span class="src-type">Chapter 5: Hold Preparation (pp.69–85). Primary operational reference for washing methods, time benchmarks, copper concentrate warning, limewash recipe, hold preparation checklist.</span></div>
        <div class="src-item"><strong>Marine Cargo Operations</strong><br>Meurn &amp; Sauerbier, Cornell Maritime Press, 2004 (3rd ed.)<br><span class="src-type">Chapter 4: Cargo space preparation. Appendix 3: bulk grain stowage by NCB President McNamara.</span></div>
      </div>
      <h3 style="margin-top:12px;">IMO Publications</h3>
      <div class="src-grid">
        <div class="src-item"><strong>MARPOL Consolidated Edition 2022</strong><br>IMO, London (in force 1 Nov 2022)<br><span class="src-type">Annex V: Prevention of pollution by garbage. Hold wash water discharge rules, HME classification, Special Areas.</span></div>
        <div class="src-item"><strong>IMSBC Code</strong><br>IMO MSC.268(85), amend. MSC.318(89), MSC.354(92)<br><span class="src-type">Mandatory under SOLAS since 1 Jan 2011. Groups A, B, C. Hold cleanliness requirements Sections 2.2.1–2.2.3. Grain carriage covered by International Grain Code separately.</span></div>
        <div class="src-item"><strong>Carrying Solid Bulk Cargoes Safely</strong><br>IMO, London<br><span class="src-type">Practical guidance on cargo preparation and hold cleaning.</span></div>
      </div>
    </div>
    <div>
      <h3>P&amp;I Club Circulars &amp; Industry Guidance</h3>
      <div class="src-grid">
        <div class="src-item"><strong>UK P&I Club</strong><br>Cargo Hold Cleanliness Circular<br><span class="src-type">Standard of cleanliness, surveyor expectations, cargo-specific advice.</span></div>
        <div class="src-item"><strong>Skuld P&I</strong><br>Hold Cleanliness &amp; Cargo Claims<br><span class="src-type">Claim prevention focus. Coal, petcoke, fertilizer transition guidance.</span></div>
        <div class="src-item"><strong>Swedish Club</strong><br>Cargo Hold Preparation Guide<br><span class="src-type">Washing protocols, chemical agents, surveyor standards.</span></div>
        <div class="src-item"><strong>Gard P&I</strong><br>Hold Cleanliness Recommendations<br><span class="src-type">FGIS process, NCB inspections, common claim scenarios.</span></div>
        <div class="src-item"><strong>West of England P&I</strong><br>Cargo Hold Cleaning Guidance<br><span class="src-type">US grain port specific advice, HME compliance.</span></div>
        <div class="src-item"><strong>North of England P&I</strong><br>Hold Cleanliness Circular<br><span class="src-type">Practical guidance, case studies.</span></div>
      </div>
      <h3 style="margin-top:12px;">Regulatory / Government</h3>
      <div class="src-grid">
        <div class="src-item"><strong>USDA FGIS — 7 CFR Part 800</strong><br>Federal Grain Inspection Service<br><span class="src-type">Stowage examination regulations. Fee schedule (2024). Mandatory inspection requirements for US grain exports.</span></div>
        <div class="src-item"><strong>National Cargo Bureau (NCB)</strong><br>Certificate of Readiness Process<br><span class="src-type">Grain stowage plan review, stability approval, hold structure inspection.</span></div>
        <div class="src-item"><strong>USCG NVIC 01-01</strong><br>US Coast Guard<br><span class="src-type">Cargo residue discharge regulations in US waters.</span></div>
      </div>
    </div>
  </div>
  <div class="info" style="margin-top:14px;">
    <strong>Knowledge base:</strong> 50+ authoritative sources catalogued in <code>knowledge_base/hold_cleaning_kb.json</code> (v1.1.0).
    Voyage data: 41,156 USACE MRTIS records processed via <code>02_TOOLSETS/vessel_voyage_analysis/</code>.
    Rate data: <code>data/hold_cleaning_rates.csv</code> (6 ports, crew + shore gang).
    Compatibility matrix: <code>data/cargo_compatibility_matrix.csv</code> (55 transitions).
    Vendor directory: <code>data/vendors_us_gulf.csv</code> (12 entries, pending expansion).
  </div>
</div>

<div class="footer">
  Cargo Hold Cleaning Intelligence Report — Hold Cleaning Module v1.1.0 &nbsp;|&nbsp;
  William S. Davis III, Maritime &amp; Supply Chain Consulting &nbsp;|&nbsp;
  Generated: {TODAY} &nbsp;|&nbsp;
  Sources: UK P&I Club · Skuld · Swedish Club · Gard · West of England · IMO MARPOL 2022 · IMSBC Code · USDA FGIS 7 CFR Part 800 · NCB · Isbester (Nautical Institute 1993) · USACE MRTIS 41,156 voyage records
</div>

</div>
</body>
</html>"""

output = "hold_cleaning_intelligence_report.html"
with open(output, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Written: {os.path.abspath(output)}")
print(f"Size: {os.path.getsize(output):,} bytes")
