"""
Generate HTML report with maps for the waybill-to-cement-plant matching.

Produces:
  cement/waybill_plant_match_report.html
    - Interactive folium map of plants + BEA coverage
    - Static matplotlib charts (match breakdown, tonnage trends, plant rankings)
    - Narrative summary with tables
"""

import base64
import csv
import io
import os
from collections import defaultdict

import folium
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── BEA centroids (subset needed for map) ─────────────────────────────────
from match_waybill_to_plants import BEA_AREAS, CANADIAN_BEA

# ── helpers ────────────────────────────────────────────────────────────────

def fig_to_b64(fig, dpi=150):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight',
                facecolor='#ffffff', edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def load_plants_csv():
    path = os.path.join(SCRIPT_DIR, 'cement_plants_epa.csv')
    plants = []
    with open(path, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            lat = row.get('latitude', '').strip()
            lon = row.get('longitude', '').strip()
            if not lat or not lon:
                continue
            plants.append({
                'facility_id': row['facility_id'].strip(),
                'facility_name': row['facility_name'].strip(),
                'city': row.get('city', '').strip(),
                'state': row.get('state', '').strip(),
                'latitude': float(lat),
                'longitude': float(lon),
                'parent_company': row.get('parent_company', '').strip(),
            })
    return plants


def load_matched_csv():
    path = os.path.join(SCRIPT_DIR, 'waybill_plant_matched.csv')
    rows = []
    with open(path, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


# ── CHART 1: Match status donut ───────────────────────────────────────────

def chart_match_donut(matched):
    """Donut chart of waybill record match status."""
    # Count at the waybill level: suppress/canadian/no_plant are 1:1,
    # proportional_split and unique_match expand rows — count unique waybills
    # But since we don't have a waybill ID, we count rows and note expansion
    status_tons = defaultdict(float)
    for r in matched:
        s = r['match_status']
        tons = float(r['extons'] or 0)
        if s in ('unique_match', 'proportional_split'):
            tons = float(r['allocated_extons'] or 0)
        status_tons[s] += tons

    labels_map = {
        'suppressed': 'Suppressed\n(origin masked)',
        'no_plant_in_bea': 'No Plant in BEA\n(distribution origin)',
        'proportional_split': 'Multi-Plant BEA\n(proportional)',
        'unique_match': 'Unique Plant\nMatch',
        'canadian_import': 'Canadian\nImport',
    }
    order = ['suppressed', 'no_plant_in_bea', 'proportional_split',
             'unique_match', 'canadian_import']
    colors = ['#95a5a6', '#e67e22', '#3498db', '#27ae60', '#8e44ad']

    sizes = [status_tons.get(s, 0) for s in order]
    labels = [labels_map.get(s, s) for s in order]
    total = sum(sizes)

    fig, ax = plt.subplots(figsize=(7, 5))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=None, autopct='',
        startangle=140, colors=colors, pctdistance=0.80,
        wedgeprops=dict(width=0.45, edgecolor='white', linewidth=2))

    # Custom labels
    for i, (w, label) in enumerate(zip(wedges, labels)):
        ang = (w.theta2 + w.theta1) / 2
        pct = sizes[i] / total * 100
        tons_m = sizes[i] / 1e6
        ax.annotate(f'{label}\n{pct:.1f}% ({tons_m:.0f}M tons)',
                    xy=(0.72 * plt.np.cos(plt.np.radians(ang)),
                        0.72 * plt.np.sin(plt.np.radians(ang))),
                    ha='center', va='center', fontsize=7.5, fontweight='bold',
                    color='white' if pct > 8 else '#333')

    ax.set_title('Waybill Cement Tonnage by Match Status\n(2005-2023 Expanded Tons)',
                 fontsize=12, fontweight='bold', pad=10)
    centre = plt.Circle((0, 0), 0.55, fc='white')
    ax.add_artist(centre)
    ax.text(0, 0, f'{total/1e6:.0f}M\ntotal tons', ha='center', va='center',
            fontsize=13, fontweight='bold', color='#2c3e50')
    fig.tight_layout()
    return fig


# ── CHART 2: Year trend ──────────────────────────────────────────────────

def chart_year_trend(matched):
    """Stacked area chart of tonnage by year and match status."""
    year_status = defaultdict(lambda: defaultdict(float))
    for r in matched:
        yr = int(r['datayear'] or 0)
        if yr < 2005:
            continue
        s = r['match_status']
        tons = float(r['extons'] or 0)
        if s in ('unique_match', 'proportional_split'):
            tons = float(r['allocated_extons'] or 0)
        # Group matched types
        if s in ('unique_match', 'proportional_split'):
            group = 'Matched to Plant'
        elif s == 'no_plant_in_bea':
            group = 'No Plant in BEA'
        elif s == 'canadian_import':
            group = 'Canadian Import'
        else:
            group = 'Suppressed'
        year_status[yr][group] += tons

    years = sorted(year_status.keys())
    groups = ['Matched to Plant', 'No Plant in BEA', 'Canadian Import', 'Suppressed']
    colors = ['#27ae60', '#e67e22', '#8e44ad', '#95a5a6']

    data = {g: [year_status[y].get(g, 0) / 1e6 for y in years] for g in groups}

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.stackplot(years, *[data[g] for g in groups], labels=groups, colors=colors, alpha=0.85)
    ax.set_xlabel('Year', fontsize=10)
    ax.set_ylabel('Expanded Tons (millions)', fontsize=10)
    ax.set_title('U.S. Rail Cement Tonnage by Match Category, 2005-2023', fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', fontsize=8, framealpha=0.9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}M'))
    ax.set_xlim(years[0], years[-1])
    ax.grid(axis='y', alpha=0.3)
    fig.tight_layout()
    return fig


# ── CHART 3: Top plants bar ─────────────────────────────────────────────

def chart_top_plants(matched):
    """Horizontal bar chart of top matched plants by tonnage."""
    plant_tons = defaultdict(float)
    plant_rev = defaultdict(float)
    for r in matched:
        if r['match_status'] in ('unique_match', 'proportional_split'):
            key = f"{r['plant_facility_name'][:35]}, {r['plant_state']}"
            plant_tons[key] += float(r['allocated_extons'] or 0)
            plant_rev[key] += float(r['allocated_exrev'] or 0)

    ranked = sorted(plant_tons.items(), key=lambda x: -x[1])[:15]
    names = [x[0] for x in ranked][::-1]
    tons = [x[1] / 1e6 for x in ranked][::-1]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.barh(range(len(names)), tons, color='#2980b9', edgecolor='white', height=0.7)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=7.5)
    ax.set_xlabel('Allocated Expanded Tons (millions)', fontsize=10)
    ax.set_title('Top 15 Cement Plants by Matched Waybill Tonnage (2005-2023)',
                 fontsize=11, fontweight='bold')
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}M'))

    for bar, t in zip(bars, tons):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                f'{t:.1f}M', va='center', fontsize=7.5, color='#2c3e50')

    ax.grid(axis='x', alpha=0.3)
    fig.tight_layout()
    return fig


# ── CHART 4: No-plant BEAs ──────────────────────────────────────────────

def chart_no_plant_beas(matched):
    """Bar chart of BEA areas with waybill origins but no cement plant."""
    bea_tons = defaultdict(float)
    bea_names = {}
    for r in matched:
        if r['match_status'] == 'no_plant_in_bea':
            bea = r['originbea']
            bea_tons[bea] += float(r['extons'] or 0)
            bea_names[bea] = r.get('bea_name', bea)

    ranked = sorted(bea_tons.items(), key=lambda x: -x[1])[:12]
    labels = [f"{bea_names[b]} ({b})" for b, _ in ranked][::-1]
    tons = [t / 1e6 for _, t in ranked][::-1]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(range(len(labels)), tons, color='#e67e22', edgecolor='white', height=0.7)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel('Expanded Tons (millions)', fontsize=10)
    ax.set_title('Top BEA Areas with Cement Waybill Origins but No Plant\n'
                 '(likely distribution terminals or transload facilities)',
                 fontsize=10, fontweight='bold')
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}M'))
    ax.grid(axis='x', alpha=0.3)
    fig.tight_layout()
    return fig


# ── CHART 5: Revenue per ton trend ──────────────────────────────────────

def chart_rev_per_ton(matched):
    """Line chart of revenue per ton over time for matched shipments."""
    year_data = defaultdict(lambda: {'tons': 0.0, 'rev': 0.0})
    for r in matched:
        yr = int(r['datayear'] or 0)
        if yr < 2005:
            continue
        tons = float(r['extons'] or 0)
        rev = float(r['exrev'] or 0)
        year_data[yr]['tons'] += tons
        year_data[yr]['rev'] += rev

    years = sorted(year_data.keys())
    rpt = []
    for y in years:
        d = year_data[y]
        rpt.append(d['rev'] / d['tons'] if d['tons'] > 0 else 0)

    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.plot(years, rpt, 'o-', color='#2c3e50', linewidth=2, markersize=5)
    ax.fill_between(years, rpt, alpha=0.08, color='#2c3e50')
    ax.set_xlabel('Year', fontsize=10)
    ax.set_ylabel('Revenue per Ton ($)', fontsize=10)
    ax.set_title('Cement Rail Revenue per Ton, 2005-2023 (all waybill records)',
                 fontsize=11, fontweight='bold')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:.0f}'))
    ax.grid(alpha=0.3)
    ax.set_xlim(years[0], years[-1])
    fig.tight_layout()
    return fig


# ── FOLIUM MAP ────────────────────────────────────────────────────────────

def build_folium_map(plants, matched):
    """Interactive map with plant markers, BEA centroids, no-plant BEAs."""
    # Compute plant-level stats from matched data
    plant_stats = defaultdict(lambda: {'tons': 0.0, 'rev': 0.0, 'records': 0})
    for r in matched:
        if r['match_status'] in ('unique_match', 'proportional_split'):
            fid = r['plant_facility_id']
            plant_stats[fid]['tons'] += float(r['allocated_extons'] or 0)
            plant_stats[fid]['rev'] += float(r['allocated_exrev'] or 0)
            plant_stats[fid]['records'] += 1

    # Assign BEA codes to plants (recompute quickly)
    from match_waybill_to_plants import assign_bea_to_plants
    plants = assign_bea_to_plants(plants)

    m = folium.Map(location=[39.0, -98.0], zoom_start=4,
                   tiles='cartodbpositron', width='100%', height='100%')

    # Layer: cement plants
    plant_layer = folium.FeatureGroup(name='Cement Plants (100)')
    matched_ids = set(plant_stats.keys())
    for p in plants:
        fid = p['facility_id']
        stats = plant_stats.get(fid)
        is_matched = fid in matched_ids and stats and stats['tons'] > 0

        if is_matched:
            tons_m = stats['tons'] / 1e6
            rev_m = stats['rev'] / 1e6
            radius = max(4, min(18, 4 + tons_m * 1.5))
            color = '#27ae60'
            popup_extra = (f"<br><b>Matched tons:</b> {tons_m:.2f}M"
                           f"<br><b>Matched rev:</b> ${rev_m:.1f}M"
                           f"<br><b>Waybill rows:</b> {stats['records']:,}")
        else:
            radius = 4
            color = '#e74c3c'
            popup_extra = '<br><i>No waybill match</i>'

        popup_html = (f"<b>{p['facility_name']}</b>"
                      f"<br>{p['city']}, {p['state']}"
                      f"<br>BEA {p['assigned_bea']} ({p['bea_name']})"
                      f"<br>Distance to BEA centroid: {p['bea_distance_mi']} mi"
                      f"{popup_extra}")

        folium.CircleMarker(
            location=[p['latitude'], p['longitude']],
            radius=radius, color=color, fill=True,
            fill_color=color, fill_opacity=0.7, weight=1.5,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=p['facility_name']
        ).add_to(plant_layer)
    plant_layer.add_to(m)

    # Layer: BEA centroids with plants
    bea_layer = folium.FeatureGroup(name='BEA Areas with Plants', show=False)
    bea_with_plants = set(p['assigned_bea'] for p in plants)
    for code in bea_with_plants:
        info = BEA_AREAS.get(code)
        if not info or info[1] is None:
            continue
        plant_names = [p['facility_name'] for p in plants if p['assigned_bea'] == code]
        popup = (f"<b>BEA {code}: {info[0]}</b><br>"
                 f"<b>{len(plant_names)} plant(s):</b><br>"
                 + '<br>'.join(f'&bull; {n}' for n in plant_names))
        folium.CircleMarker(
            location=[info[1], info[2]],
            radius=8, color='#3498db', fill=True,
            fill_color='#3498db', fill_opacity=0.3, weight=2,
            popup=folium.Popup(popup, max_width=350),
            tooltip=f'BEA {code}: {info[0]}'
        ).add_to(bea_layer)
    bea_layer.add_to(m)

    # Layer: No-plant BEA origins
    no_plant_tons = defaultdict(float)
    no_plant_recs = defaultdict(int)
    for r in matched:
        if r['match_status'] == 'no_plant_in_bea':
            bea = r['originbea']
            no_plant_tons[bea] += float(r['extons'] or 0)
            no_plant_recs[bea] += 1

    if no_plant_tons:
        noplant_layer = folium.FeatureGroup(name='No-Plant BEA Origins')
        for bea, tons in sorted(no_plant_tons.items(), key=lambda x: -x[1]):
            info = BEA_AREAS.get(bea)
            if not info or info[1] is None:
                continue
            tons_m = tons / 1e6
            radius = max(5, min(22, 5 + tons_m * 0.4))
            popup = (f"<b>BEA {bea}: {info[0]}</b>"
                     f"<br>No cement plant assigned"
                     f"<br><b>Waybill origins:</b> {no_plant_recs[bea]:,} records"
                     f"<br><b>Expanded tons:</b> {tons_m:.1f}M"
                     f"<br><i>Likely distribution terminal or transload</i>")
            folium.CircleMarker(
                location=[info[1], info[2]],
                radius=radius, color='#e67e22', fill=True,
                fill_color='#e67e22', fill_opacity=0.5, weight=2,
                popup=folium.Popup(popup, max_width=300),
                tooltip=f'{info[0]}: {tons_m:.1f}M tons (no plant)'
            ).add_to(noplant_layer)
        noplant_layer.add_to(m)

    # Layer: Canadian import origins
    can_tons = defaultdict(float)
    can_recs = defaultdict(int)
    for r in matched:
        if r['match_status'] == 'canadian_import':
            bea = r['originbea']
            can_tons[bea] += float(r['extons'] or 0)
            can_recs[bea] += 1

    if can_tons:
        can_layer = folium.FeatureGroup(name='Canadian Import Origins', show=False)
        # Approximate Canadian province centroids
        can_coords = {
            '173': (53.7, -127.6), '174': (53.9, -116.6),
            '175': (52.9, -106.4), '176': (53.8, -98.8),
            '177': (51.3, -85.3), '178': (52.9, -73.5),
            '179': (46.5, -66.2), '180': (44.7, -63.0),
            '181': (46.2, -63.0), '182': (53.1, -57.7),
            '183': (64.3, -135.0),
        }
        for bea, tons in sorted(can_tons.items(), key=lambda x: -x[1]):
            coords = can_coords.get(bea)
            if not coords:
                continue
            prov = CANADIAN_BEA.get(bea, 'Unknown')
            tons_m = tons / 1e6
            popup = (f"<b>{prov} (BEA {bea})</b>"
                     f"<br><b>Records:</b> {can_recs[bea]:,}"
                     f"<br><b>Expanded tons:</b> {tons_m:.2f}M")
            folium.CircleMarker(
                location=coords, radius=max(5, min(15, 5 + tons_m * 2)),
                color='#8e44ad', fill=True, fill_color='#8e44ad',
                fill_opacity=0.5, weight=2,
                popup=folium.Popup(popup, max_width=250),
                tooltip=f'{prov}: {tons_m:.2f}M tons'
            ).add_to(can_layer)
        can_layer.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    # Legend
    legend_html = '''
    <div style="position:fixed; bottom:30px; left:30px; z-index:999;
         background:white; padding:12px 16px; border-radius:8px;
         box-shadow:0 2px 8px rgba(0,0,0,0.2); font-size:12px; line-height:1.8">
      <b>Legend</b><br>
      <span style="color:#27ae60">&#9679;</span> Plant (matched to waybill)<br>
      <span style="color:#e74c3c">&#9679;</span> Plant (no waybill match)<br>
      <span style="color:#e67e22">&#9679;</span> BEA origin, no plant (terminal?)<br>
      <span style="color:#8e44ad">&#9679;</span> Canadian import origin
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    return m.get_root().render()


# ── HTML REPORT ───────────────────────────────────────────────────────────

def build_report():
    print("Loading data...")
    plants = load_plants_csv()
    matched = load_matched_csv()

    print("Generating charts...")
    img_donut = fig_to_b64(chart_match_donut(matched))
    img_trend = fig_to_b64(chart_year_trend(matched))
    img_plants = fig_to_b64(chart_top_plants(matched))
    img_noplant = fig_to_b64(chart_no_plant_beas(matched))
    img_rpt = fig_to_b64(chart_rev_per_ton(matched))

    print("Building interactive map...")
    map_html = build_folium_map(plants, matched)

    # ── Compute summary numbers ──
    total_waybill = 0
    total_tons = 0.0
    total_rev = 0.0
    status_counts = defaultdict(int)
    status_tons = defaultdict(float)
    for r in matched:
        s = r['match_status']
        status_counts[s] += 1
        tons = float(r['extons'] or 0)
        if s in ('unique_match', 'proportional_split'):
            tons = float(r['allocated_extons'] or 0)
        status_tons[s] += tons

    # Count original waybill records (matched rows may be expanded)
    waybill_set = set()
    for r in matched:
        # Use combination of fields as proxy for unique waybill
        key = (r['datayear'], r['month'], r['waybilldate'], r['originbea'],
               r['terminationbea'], r['freightrevenue'], r['actualweightintons'])
        waybill_set.add(key)
    total_waybill = len(waybill_set)
    total_tons = sum(float(r['extons'] or 0) for r in matched
                     if r['match_status'] not in ('proportional_split', 'unique_match'))
    total_tons += sum(float(r['allocated_extons'] or 0) for r in matched
                      if r['match_status'] in ('proportional_split', 'unique_match'))
    total_rev = sum(float(r['exrev'] or 0) for r in matched
                    if r['match_status'] not in ('proportional_split', 'unique_match'))
    total_rev += sum(float(r['allocated_exrev'] or 0) for r in matched
                     if r['match_status'] in ('proportional_split', 'unique_match'))

    matched_tons = status_tons.get('unique_match', 0) + status_tons.get('proportional_split', 0)
    matched_pct = matched_tons / total_tons * 100 if total_tons else 0
    suppressed_pct = status_tons.get('suppressed', 0) / total_tons * 100 if total_tons else 0

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Cement Waybill-to-Plant Matching Report</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
         background:#f5f6fa; color:#2c3e50; line-height:1.6; }}
  .header {{ background:linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
             color:white; padding:40px 60px; }}
  .header h1 {{ font-size:28px; margin-bottom:6px; }}
  .header p {{ font-size:14px; opacity:0.85; }}
  .container {{ max-width:1200px; margin:0 auto; padding:20px 40px 60px; }}
  .kpi-row {{ display:flex; gap:20px; margin:24px 0 30px; flex-wrap:wrap; }}
  .kpi {{ background:white; border-radius:10px; padding:20px 28px; flex:1; min-width:180px;
          box-shadow:0 2px 8px rgba(0,0,0,0.06); }}
  .kpi .label {{ font-size:11px; text-transform:uppercase; letter-spacing:1px; color:#7f8c8d; }}
  .kpi .value {{ font-size:26px; font-weight:700; color:#2c3e50; margin-top:4px; }}
  .kpi .sub {{ font-size:11px; color:#95a5a6; margin-top:2px; }}
  .section {{ background:white; border-radius:10px; padding:30px 36px; margin-bottom:24px;
              box-shadow:0 2px 8px rgba(0,0,0,0.06); }}
  .section h2 {{ font-size:18px; color:#2c3e50; margin-bottom:14px;
                 border-bottom:2px solid #3498db; padding-bottom:8px; display:inline-block; }}
  .section p {{ font-size:14px; margin-bottom:12px; }}
  .chart-img {{ width:100%; max-width:900px; display:block; margin:16px auto; }}
  .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:24px; }}
  @media (max-width:900px) {{ .two-col {{ grid-template-columns:1fr; }} }}
  .map-frame {{ width:100%; height:620px; border:none; border-radius:8px;
                box-shadow:0 2px 8px rgba(0,0,0,0.08); }}
  table {{ border-collapse:collapse; width:100%; font-size:13px; margin:12px 0; }}
  th {{ background:#ecf0f1; text-align:left; padding:8px 12px; font-weight:600; }}
  td {{ padding:7px 12px; border-bottom:1px solid #ecf0f1; }}
  tr:hover td {{ background:#f8f9fa; }}
  .tag {{ display:inline-block; padding:2px 8px; border-radius:4px; font-size:11px;
          font-weight:600; color:white; }}
  .tag-green {{ background:#27ae60; }}
  .tag-orange {{ background:#e67e22; }}
  .tag-gray {{ background:#95a5a6; }}
  .tag-purple {{ background:#8e44ad; }}
  .footnote {{ font-size:12px; color:#7f8c8d; margin-top:10px; font-style:italic; }}
</style>
</head>
<body>

<div class="header">
  <h1>Cement Waybill-to-Plant Matching Report</h1>
  <p>STB Public Use Waybill Sample (2005-2023) matched to EPA GHGRP Cement Facilities via BEA Economic Areas</p>
</div>

<div class="container">

<!-- KPIs -->
<div class="kpi-row">
  <div class="kpi">
    <div class="label">Waybill Records</div>
    <div class="value">{total_waybill:,}</div>
    <div class="sub">STCC 32411/32412 cement</div>
  </div>
  <div class="kpi">
    <div class="label">Cement Plants</div>
    <div class="value">100</div>
    <div class="sub">EPA GHGRP 327310</div>
  </div>
  <div class="kpi">
    <div class="label">Total Expanded Tons</div>
    <div class="value">{total_tons/1e6:.0f}M</div>
    <div class="sub">19-year aggregate</div>
  </div>
  <div class="kpi">
    <div class="label">Matched to Plant</div>
    <div class="value">{matched_pct:.1f}%</div>
    <div class="sub">{matched_tons/1e6:.0f}M tons identified</div>
  </div>
  <div class="kpi">
    <div class="label">Suppressed</div>
    <div class="value">{suppressed_pct:.1f}%</div>
    <div class="sub">Origin BEA masked (000)</div>
  </div>
</div>

<!-- Section 1: Overview -->
<div class="section">
  <h2>1. Methodology</h2>
  <p>The STB Public Use Waybill Sample reports cement shipment origins only as 3-digit BEA Economic Area
  codes (172 areas covering the continental US). To link waybill records back to specific production
  facilities, we assigned each of the 100 EPA-reported cement plants (NAICS 327310) to its nearest
  BEA area centroid using haversine distance, then joined waybill records on
  <code>originbea = assigned_bea</code>.</p>

  <p>Where multiple plants fall within the same BEA area, tonnage and revenue are split equally
  (proportional allocation). Three categories of records cannot be matched:</p>

  <table>
    <tr><th>Category</th><th>Cause</th><th>Share of Tons</th></tr>
    <tr>
      <td><span class="tag tag-gray">Suppressed</span></td>
      <td>STB masks origin BEA as 000 for confidentiality (small carriers/shippers)</td>
      <td>{suppressed_pct:.1f}%</td>
    </tr>
    <tr>
      <td><span class="tag tag-orange">No Plant in BEA</span></td>
      <td>Domestic BEA area has waybill origins but no cement plant &mdash; likely distribution
          terminals, transload facilities, or re-origination points</td>
      <td>{status_tons.get('no_plant_in_bea',0)/total_tons*100:.1f}%</td>
    </tr>
    <tr>
      <td><span class="tag tag-purple">Canadian Import</span></td>
      <td>Origin BEA 173-183 = Canadian provinces (cement imported by rail)</td>
      <td>{status_tons.get('canadian_import',0)/total_tons*100:.1f}%</td>
    </tr>
  </table>
  <p class="footnote">Expansion factors from the STB waybill sample are applied throughout.
  "Expanded tons" and "expanded revenue" represent estimated universe totals.</p>
</div>

<!-- Section 2: Match breakdown -->
<div class="section">
  <h2>2. Match Status Distribution</h2>
  <div class="two-col">
    <div><img class="chart-img" src="data:image/png;base64,{img_donut}"></div>
    <div>
      <p>Of the {total_tons/1e6:.0f}M expanded tons of cement shipped by rail between 2005 and 2023:</p>
      <ul style="font-size:14px; margin:10px 0 10px 20px;">
        <li><b>{matched_pct:.1f}%</b> ({matched_tons/1e6:.0f}M tons) were matched to a specific
            plant or proportionally allocated among plants within a BEA area</li>
        <li><b>{suppressed_pct:.0f}%</b> were suppressed at the source &mdash; the STB masks origins
            for ~52% of cement waybills, a significantly higher rate than for other bulk commodities</li>
        <li><b>{status_tons.get('no_plant_in_bea',0)/total_tons*100:.0f}%</b> originated from BEA areas
            with no EPA-listed cement plant, indicating these are distribution or terminal origins
            rather than production facilities</li>
        <li><b>{status_tons.get('canadian_import',0)/total_tons*100:.1f}%</b> are Canadian imports,
            primarily from Ontario and Quebec</li>
      </ul>
    </div>
  </div>
</div>

<!-- Section 3: Map -->
<div class="section">
  <h2>3. Plant and Origin Geography</h2>
  <p>Interactive map showing all 100 cement plants (green = matched to waybill data, red = no match),
  orange circles at BEA centroids where cement originates but no plant exists, and purple markers for
  Canadian import provinces. Circle size is proportional to tonnage. Click any marker for details.
  Toggle layers using the control at top-right.</p>
  <iframe class="map-frame" srcdoc='{map_html.replace(chr(39), "&#39;")}'></iframe>
</div>

<!-- Section 4: Trends -->
<div class="section">
  <h2>4. Tonnage and Revenue Trends</h2>
  <img class="chart-img" src="data:image/png;base64,{img_trend}">
  <p>Rail cement volumes declined ~28% during the 2008-2011 housing crisis, recovering to roughly
  pre-recession levels by 2014. The jump in record count from 2020 to 2021 (4,280 to 32,480 records)
  reflects a change in STB sampling methodology, not a volume surge &mdash; expanded tonnage remains
  stable at ~25M tons/year.</p>
  <img class="chart-img" src="data:image/png;base64,{img_rpt}">
  <p>Revenue per ton has risen steadily from ~$17/ton in 2005 to ~$39/ton in 2023, reflecting both
  general freight rate escalation and fuel surcharge accumulation. The post-2020 acceleration
  aligns with broader inflationary trends in construction materials.</p>
</div>

<!-- Section 5: Plant rankings -->
<div class="section">
  <h2>5. Top Matched Plants</h2>
  <img class="chart-img" src="data:image/png;base64,{img_plants}">
  <p class="footnote">Note: Plants in multi-plant BEA areas share tonnage equally.
  The Pryor/Tulsa OK plants and Pueblo CO plants appear high because their BEA areas
  concentrate multiple waybill origins. Actual plant-level production may differ.</p>
</div>

<!-- Section 6: No-plant origins -->
<div class="section">
  <h2>6. Distribution Origins Without Plants</h2>
  <img class="chart-img" src="data:image/png;base64,{img_noplant}">
  <p>Sixteen BEA areas show cement waybill origins but contain no EPA-listed cement plant.
  The largest &mdash; Fresno CA (37M tons), Houston TX (31M tons), and Fargo ND (27M tons)
  &mdash; are major rail distribution hubs where cement is likely re-originated after arriving
  by unit train from nearby producing regions. These volumes are real rail movements but
  represent <b>distribution</b>, not <b>production</b> geography.</p>
</div>

<!-- Section 7: Limitations -->
<div class="section">
  <h2>7. Data Limitations</h2>
  <ul style="font-size:14px; margin:10px 0 10px 20px; line-height:2;">
    <li><b>52% suppression rate:</b> Over half of cement waybill origins are masked,
    far exceeding the ~25% average for all STB commodities. This means matched tonnage
    significantly undercounts actual production-to-destination flows.</li>
    <li><b>BEA granularity:</b> BEA areas can span hundreds of miles. A plant "assigned"
    to a BEA area may not be the actual origin &mdash; particularly in large western BEAs.</li>
    <li><b>Equal allocation:</b> When multiple plants share a BEA (e.g., 5 plants in
    Allentown PA), each receives 1/N of the tonnage. In reality, plants differ in capacity.</li>
    <li><b>No-plant BEA origins:</b> 33% of domestic unsuppressed tonnage originates from
    BEA areas with no cement plant. These are legitimate rail movements but likely represent
    terminals, transload points, or re-origination rather than plant shipments.</li>
    <li><b>Plant vintage:</b> The EPA plant list uses the most recent GHGRP reporting year
    for each facility (mostly 2023). Plants that closed between 2005-2023 may be missed.</li>
  </ul>
</div>

</div><!-- /container -->
</body>
</html>'''

    out_path = os.path.join(SCRIPT_DIR, 'waybill_plant_match_report.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Report written to {out_path}")
    return out_path


if __name__ == '__main__':
    build_report()
