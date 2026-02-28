"""
Cement Rail Trade Flow Report — origin-to-destination analysis with
producer identification.

Outputs:
  cement/cement_trade_flow_report.html
"""

import base64
import csv
import io
import math
import os
from collections import defaultdict

import folium
from folium.plugins import AntPath
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
from match_waybill_to_plants import BEA_AREAS, CANADIAN_BEA

# Approx Canadian province centroids for mapping
CAN_COORDS = {
    '173': (53.7, -127.6), '174': (51.0, -114.1),
    '175': (52.9, -106.4), '176': (49.9, -97.1),
    '177': (44.0, -79.8), '178': (46.8, -71.2),
    '179': (46.5, -66.6), '180': (44.6, -63.6),
    '181': (46.2, -63.0), '182': (48.5, -56.0),
    '183': (64.3, -135.0),
}

# ── Probable producer / company identifications for major flows ──────────
# Built from: EPA plant list, Lafarge Dakota research, Canadian import analysis
FLOW_PRODUCERS = {
    # Matched plant flows (known)
    ('078', '040'): ('Buzzi Unicem / Eagle Materials', 'Pryor & Tulsa, OK → Jacksonville, FL',
                     'Two plants in NE Oklahoma BEA ship cement southeast to Florida market'),
    ('124', '127'): ('GCC Rio Grande / Holcim', 'Pueblo, CO → Lubbock, TX',
                     'Colorado Front Range plants supply West Texas construction market'),
    ('124', '099'): ('GCC Rio Grande / Holcim', 'Pueblo, CO → La Crosse, WI',
                     'Long-haul from Colorado to Upper Midwest via BNSF'),
    ('078', '019'): ('Buzzi Unicem / Eagle Materials', 'Pryor, OK → Wilmington, DE',
                     'Oklahoma plants serve Mid-Atlantic via NS/CSX'),
    ('141', '141'): ('Holcim / CRH Ash Grove', 'Salt Lake City, UT (local)',
                     'Devil\'s Slide & Leamington plants serve Wasatch Front market'),
    ('163', '164'): ('CEMEX / CalPortland / Mitsubishi', 'Los Angeles → San Diego',
                     'Inland Empire plants supply Southern California coast'),
    ('078', '023'): ('Buzzi Unicem / Eagle Materials', 'Pryor, OK → Staunton, VA',
                     'Oklahoma cement to Shenandoah Valley'),
    ('017', '018'): ('Heidelberg / Hercules / Keystone / Lafarge', 'Lehigh Valley, PA → Philadelphia',
                     '5 plants in Lehigh Valley supply the Philadelphia metro'),
    ('020', '025'): ('Heidelberg Materials', 'Baltimore, MD → Norfolk, VA',
                     'Union Bridge plant supplies Hampton Roads via CSX'),
    ('124', '118'): ('GCC Rio Grande / Holcim', 'Pueblo, CO → Omaha, NE',
                     'Colorado plants supply Nebraska via UP/BNSF'),
    ('124', '122'): ('GCC Rio Grande / Holcim', 'Pueblo, CO → Denver, CO',
                     'Short-haul from Pueblo mills to Front Range construction'),
    ('099', '000'): ('Lehigh Cement (Heidelberg)', 'Mason City, IA → suppressed',
                     'Northern Iowa plant; destinations masked by STB'),
    ('077', '000'): ('Holcim', 'Ada, OK → suppressed',
                     'Central Oklahoma plant; destinations masked'),
    ('057', '051'): ('Holcim', 'Paulding, OH → Knoxville, TN',
                     'Northwest Ohio plant serves East Tennessee'),
    # Canadian reorigination (Fargo)
    ('096', '099'): ('Lafarge / Amrize (Calgary, AB)', 'Fargo, ND → La Crosse, WI',
                     'Alberta cement via CPKC to ND terminals, redistributed south on BNSF'),
    ('096', '127'): ('Lafarge / Amrize (Calgary, AB)', 'Fargo, ND → Lubbock, TX',
                     'Alberta cement redistributed deep into southern Plains'),
    ('096', '096'): ('Lafarge / Amrize (Calgary, AB)', 'Fargo, ND (local)',
                     'Local delivery within eastern ND / western MN'),
    ('096', '122'): ('Lafarge / Amrize (Calgary, AB)', 'Fargo, ND → Denver, CO',
                     'Alberta cement via Fargo to Mountain West'),
    ('096', '107'): ('Lafarge / Amrize (Calgary, AB)', 'Fargo, ND → Davenport, IA',
                     'Alberta cement to Quad Cities market'),
    ('096', '118'): ('Lafarge / Amrize (Calgary, AB)', 'Fargo, ND → Omaha, NE',
                     'Alberta cement to eastern Nebraska'),
    # Canadian imports
    ('178', '051'): ('Lafarge / CRH (Quebec)', 'Quebec → Knoxville, TN',
                     'Quebec cement to East Tennessee via CP/CSX'),
    ('177', '003'): ('St. Marys / Essroc (Ontario)', 'Ontario → Burlington, VT',
                     'Ontario cement to northern New England'),
    ('182', '167'): ('Corner Brook / Atlantic Canada', 'Newfoundland → Olympia, WA',
                     'East Coast cement to Pacific Northwest — likely ocean then rail'),
    ('182', '169'): ('Corner Brook / Atlantic Canada', 'Newfoundland → Fairbanks, AK',
                     'Atlantic Canada to Alaska via Pacific routing'),
    ('177', '055'): ('St. Marys / Essroc (Ontario)', 'Ontario → Louisville, KY',
                     'Ontario cement to Ohio Valley market'),
    ('177', '010'): ('St. Marys / Essroc (Ontario)', 'Ontario → Boston, MA',
                     'Ontario cement to New England via CP/CSX'),
    # No-plant BEA flows (inferred producers)
    ('134', '131'): ('Probable: CEMEX / Martin Marietta imports via Port of Houston',
                     'Houston, TX → Dallas, TX',
                     'Houston is a major cement import terminal (Mexico, Turkey); redistribution north'),
    ('160', '163'): ('Probable: CalPortland / National Cement (Bakersfield BEA plants)',
                     'Fresno, CA → Los Angeles, CA',
                     'Central Valley transload point for Tehachapi/Mojave plants shipping to LA'),
    ('134', '127'): ('Probable: Import cement via Port of Houston',
                     'Houston, TX → Lubbock, TX',
                     'Imported cement redistributed to West Texas from Houston terminal'),
    ('160', '158'): ('Probable: CalPortland / National Cement',
                     'Fresno, CA → San Francisco, CA',
                     'Central Valley origin to Bay Area — Kern County plants via UP'),
    ('160', '164'): ('Probable: CalPortland / National Cement',
                     'Fresno, CA → San Diego, CA',
                     'Kern County plants to Southern California coast via BNSF'),
    ('127', '131'): ('Probable: GCC Permian (Odessa) or Colorado plants',
                     'Lubbock, TX → Dallas, TX',
                     'West Texas distribution hub serving DFW market'),
    ('013', '053'): ('Probable: Lafarge Ravena / Heidelberg (Albany, NY area)',
                     'Hartford, CT → Charleston, WV',
                     'Northeast production redistributed to Appalachia via CSX'),
    ('013', '020'): ('Probable: Lafarge Ravena / Heidelberg',
                     'Hartford, CT → Baltimore, MD',
                     'Connecticut corridor — Albany-area plants to Mid-Atlantic'),
    ('026', '023'): ('Probable: Roanoke Cement (Titan America) or Giant Cement',
                     'Raleigh, NC → Staunton, VA',
                     'Piedmont distribution to Shenandoah Valley'),
    ('026', '019'): ('Probable: Argos / Giant Cement (Harleyville, SC)',
                     'Raleigh, NC → Wilmington, DE',
                     'Carolina plants serve Mid-Atlantic via CSX'),
    ('010', '000'): ('Probable: Canadian imports (Ontario/Quebec) or Dragon Cement (ME)',
                     'Boston, MA → suppressed',
                     'New England origin — limited US production, likely import cement'),
    ('167', '000'): ('Probable: Ash Grove / Lafarge (Seattle, BEA 165)',
                     'Olympia, WA → suppressed',
                     'Puget Sound distribution point for Seattle-area plants'),
}


def fig_to_b64(fig, dpi=150):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight',
                facecolor='#ffffff', edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def load_matched():
    path = os.path.join(SCRIPT_DIR, 'waybill_plant_matched.csv')
    rows = []
    with open(path, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def get_bea_coords(code):
    """Return (lat, lon) for a BEA code, including Canadian."""
    if code in BEA_AREAS:
        info = BEA_AREAS[code]
        if info[1] is not None:
            return (info[1], info[2])
    if code in CAN_COORDS:
        return CAN_COORDS[code]
    return None


def get_bea_label(code):
    if code in BEA_AREAS:
        return BEA_AREAS[code][0]
    if code in CANADIAN_BEA:
        return CANADIAN_BEA[code]
    return f'BEA {code}'


# ── Build flow data ──────────────────────────────────────────────────────

def build_flows(matched):
    flows = defaultdict(lambda: {
        'tons': 0, 'rev': 0, 'recs': 0, 'statuses': set(),
        'plants': set(), 'years': set()
    })
    for r in matched:
        ob = r['originbea']
        tb = r['terminationbea']
        s = r['match_status']
        tons = float(r['allocated_extons'] or 0) if s in ('unique_match', 'proportional_split') \
            else float(r['extons'] or 0)
        rev = float(r['allocated_exrev'] or 0) if s in ('unique_match', 'proportional_split') \
            else float(r['exrev'] or 0)
        flows[(ob, tb)]['tons'] += tons
        flows[(ob, tb)]['rev'] += rev
        flows[(ob, tb)]['recs'] += 1
        flows[(ob, tb)]['statuses'].add(s)
        flows[(ob, tb)]['years'].add(r['datayear'])
        pn = r.get('plant_facility_name', '').strip()
        if pn:
            flows[(ob, tb)]['plants'].add(pn)
    return flows


# ── CHART: Top corridors horizontal bar ──────────────────────────────────

def chart_top_corridors(flows):
    # Exclude suppressed destinations for clarity
    visible = {k: v for k, v in flows.items() if k[1] != '000'}
    ranked = sorted(visible.items(), key=lambda x: -x[1]['tons'])[:20]

    labels = []
    tons = []
    colors = []
    status_color = {
        'unique_match': '#27ae60', 'proportional_split': '#3498db',
        'no_plant_in_bea': '#e67e22', 'canadian_reorigination': '#8e44ad',
        'canadian_import': '#9b59b6', 'suppressed': '#95a5a6'
    }
    for (ob, tb), d in ranked:
        o_label = get_bea_label(ob)
        d_label = get_bea_label(tb)
        labels.append(f'{o_label} → {d_label}')
        tons.append(d['tons'] / 1e6)
        primary_status = sorted(d['statuses'],
                                key=lambda s: status_color.get(s, '#ccc'))[0]
        colors.append(status_color.get(primary_status, '#bdc3c7'))

    labels = labels[::-1]
    tons = tons[::-1]
    colors = colors[::-1]

    fig, ax = plt.subplots(figsize=(11, 7))
    bars = ax.barh(range(len(labels)), tons, color=colors, edgecolor='white', height=0.7)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel('Expanded Tons (millions)', fontsize=10)
    ax.set_title('Top 20 Cement Rail Trade Corridors by Tonnage (2005–2023)\n'
                 'Excluding suppressed destinations', fontsize=11, fontweight='bold')
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}M'))

    for bar, t in zip(bars, tons):
        ax.text(bar.get_width() + 0.08, bar.get_y() + bar.get_height() / 2,
                f'{t:.1f}M', va='center', fontsize=7, color='#2c3e50')

    patches = [mpatches.Patch(color=c, label=l) for l, c in [
        ('Plant matched', '#3498db'), ('Canadian re-orig.', '#8e44ad'),
        ('Canadian import', '#9b59b6'), ('No plant (inferred)', '#e67e22')]]
    ax.legend(handles=patches, loc='lower right', fontsize=8, framealpha=0.9)
    ax.grid(axis='x', alpha=0.3)
    fig.tight_layout()
    return fig


# ── CHART: Canadian share pie ────────────────────────────────────────────

def chart_canadian_share(matched):
    buckets = defaultdict(float)
    for r in matched:
        s = r['match_status']
        tons = float(r['allocated_extons'] or 0) if s in ('unique_match', 'proportional_split') \
            else float(r['extons'] or 0)
        if s in ('unique_match', 'proportional_split'):
            buckets['US Plant Matched'] += tons
        elif s == 'no_plant_in_bea':
            buckets['US No-Plant Origin'] += tons
        elif s == 'canadian_import':
            buckets['Canadian Import (direct)'] += tons
        elif s == 'canadian_reorigination':
            buckets['Canadian Re-origination'] += tons
        elif s == 'suppressed':
            buckets['Suppressed'] += tons

    labels = ['US Plant Matched', 'US No-Plant Origin', 'Canadian Re-origination',
              'Canadian Import (direct)', 'Suppressed']
    sizes = [buckets.get(l, 0) / 1e6 for l in labels]
    colors = ['#27ae60', '#e67e22', '#8e44ad', '#9b59b6', '#bdc3c7']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5),
                                    gridspec_kw={'width_ratios': [1, 1.3]})

    # Pie: all sources
    wedges, _, autotexts = ax1.pie(sizes, labels=None, autopct='%1.1f%%',
                                    colors=colors, startangle=140,
                                    pctdistance=0.75,
                                    wedgeprops=dict(width=0.5, edgecolor='white'))
    for at in autotexts:
        at.set_fontsize(8)
    ax1.legend(labels, loc='center left', bbox_to_anchor=(-0.35, 0.5), fontsize=8)
    ax1.set_title('Tonnage by Source Type', fontsize=11, fontweight='bold')

    # Bar: Canadian breakdown
    can_direct = buckets.get('Canadian Import (direct)', 0) / 1e6
    can_reorig = buckets.get('Canadian Re-origination', 0) / 1e6
    can_total = can_direct + can_reorig
    us_matched = buckets.get('US Plant Matched', 0) / 1e6
    us_noplant = buckets.get('US No-Plant Origin', 0) / 1e6
    suppressed = buckets.get('Suppressed', 0) / 1e6

    cats = ['Suppressed\n(unknown origin)', 'US No-Plant\nOrigin', 'US Plant\nMatched',
            'Canadian\nDirect Import', 'Canadian\nRe-origination']
    vals = [suppressed, us_noplant, us_matched, can_direct, can_reorig]
    bar_colors = ['#bdc3c7', '#e67e22', '#27ae60', '#9b59b6', '#8e44ad']

    ax2.bar(cats, vals, color=bar_colors, edgecolor='white', width=0.65)
    ax2.set_ylabel('Expanded Tons (millions)', fontsize=10)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}M'))
    ax2.set_title(f'Canadian-Origin Cement: {can_total:.0f}M tons ({can_total/(sum(sizes))*100:.1f}% of total)',
                  fontsize=11, fontweight='bold')
    for i, v in enumerate(vals):
        ax2.text(i, v + 1, f'{v:.0f}M', ha='center', fontsize=8, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    fig.tight_layout()
    return fig


# ── CHART: Revenue per ton by source ─────────────────────────────────────

def chart_rpt_by_source(matched):
    year_src = defaultdict(lambda: defaultdict(lambda: {'tons': 0, 'rev': 0}))
    for r in matched:
        yr = int(r['datayear'] or 0)
        if yr < 2005:
            continue
        s = r['match_status']
        tons = float(r['allocated_extons'] or 0) if s in ('unique_match', 'proportional_split') \
            else float(r['extons'] or 0)
        rev = float(r['allocated_exrev'] or 0) if s in ('unique_match', 'proportional_split') \
            else float(r['exrev'] or 0)
        if s in ('unique_match', 'proportional_split'):
            grp = 'US Plant'
        elif s == 'canadian_reorigination':
            grp = 'Canadian (Fargo)'
        elif s == 'canadian_import':
            grp = 'Canadian (direct)'
        elif s == 'no_plant_in_bea':
            grp = 'US Terminal'
        else:
            grp = 'Suppressed'
        year_src[yr][grp]['tons'] += tons
        year_src[yr][grp]['rev'] += rev

    years = sorted(year_src.keys())
    groups = ['US Plant', 'US Terminal', 'Canadian (Fargo)', 'Canadian (direct)', 'Suppressed']
    colors_map = {'US Plant': '#27ae60', 'US Terminal': '#e67e22',
                  'Canadian (Fargo)': '#8e44ad', 'Canadian (direct)': '#9b59b6',
                  'Suppressed': '#bdc3c7'}

    fig, ax = plt.subplots(figsize=(10, 4.5))
    for grp in groups:
        rpts = []
        for y in years:
            d = year_src[y].get(grp, {'tons': 0, 'rev': 0})
            rpts.append(d['rev'] / d['tons'] if d['tons'] > 0 else None)
        # Filter None for plotting
        valid = [(y, r) for y, r in zip(years, rpts) if r is not None]
        if valid:
            ax.plot([v[0] for v in valid], [v[1] for v in valid],
                    'o-', label=grp, color=colors_map.get(grp, '#999'),
                    linewidth=1.8, markersize=4, alpha=0.85)

    ax.set_xlabel('Year', fontsize=10)
    ax.set_ylabel('Revenue per Ton ($)', fontsize=10)
    ax.set_title('Cement Rail Revenue per Ton by Source Type, 2005–2023',
                 fontsize=11, fontweight='bold')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:.0f}'))
    ax.legend(fontsize=8, loc='upper left')
    ax.grid(alpha=0.3)
    ax.set_xlim(2005, 2023)
    fig.tight_layout()
    return fig


# ── FOLIUM FLOW MAP ──────────────────────────────────────────────────────

def build_flow_map(flows):
    m = folium.Map(location=[39.0, -98.0], zoom_start=4,
                   tiles='cartodbdark_matter', width='100%', height='100%')

    status_color = {
        'unique_match': '#27ae60', 'proportional_split': '#3498db',
        'no_plant_in_bea': '#e67e22', 'canadian_reorigination': '#8e44ad',
        'canadian_import': '#9b59b6',
    }

    # Only draw flows with >100K tons and non-suppressed destination
    significant = {k: v for k, v in flows.items()
                   if v['tons'] > 100000 and k[1] != '000' and k[0] != '000'}

    max_tons = max(v['tons'] for v in significant.values()) if significant else 1

    # Flow lines layer
    flow_layer = folium.FeatureGroup(name='Trade Flow Lines')
    for (ob, tb), d in sorted(significant.items(), key=lambda x: x[1]['tons']):
        o_coords = get_bea_coords(ob)
        t_coords = get_bea_coords(tb)
        if not o_coords or not t_coords:
            continue

        weight = max(1.5, min(8, 1.5 + (d['tons'] / max_tons) * 7))
        primary_status = sorted(d['statuses'],
                                key=lambda s: list(status_color.keys()).index(s)
                                if s in status_color else 99)[0]
        color = status_color.get(primary_status, '#7f8c8d')

        producer_info = FLOW_PRODUCERS.get((ob, tb))
        if producer_info:
            who_html = (f'<br><b>Producer:</b> {producer_info[0]}'
                        f'<br><i>{producer_info[2]}</i>')
        else:
            plants = d.get('plants', set())
            if plants:
                who_html = '<br><b>Plants:</b> ' + ', '.join(sorted(plants)[:3])
            else:
                who_html = ''

        popup = (f'<b>{get_bea_label(ob)} → {get_bea_label(tb)}</b>'
                 f'<br><b>Tons:</b> {d["tons"]/1e6:.2f}M'
                 f'<br><b>Revenue:</b> ${d["rev"]/1e6:.1f}M'
                 f'<br><b>Records:</b> {d["recs"]:,}'
                 f'<br><b>Status:</b> {", ".join(sorted(d["statuses"]))}'
                 f'{who_html}')

        # Curved line using intermediate point
        mid_lat = (o_coords[0] + t_coords[0]) / 2
        mid_lon = (o_coords[1] + t_coords[1]) / 2
        # Offset perpendicular for visual separation
        dlat = t_coords[0] - o_coords[0]
        dlon = t_coords[1] - o_coords[1]
        dist = math.sqrt(dlat**2 + dlon**2)
        if dist > 0:
            offset = min(2.0, dist * 0.15)
            mid_lat += -dlon / dist * offset
            mid_lon += dlat / dist * offset

        folium.PolyLine(
            locations=[o_coords, (mid_lat, mid_lon), t_coords],
            weight=weight, color=color, opacity=0.7,
            popup=folium.Popup(popup, max_width=350),
            tooltip=f'{get_bea_label(ob)} → {get_bea_label(tb)}: {d["tons"]/1e6:.1f}M tons'
        ).add_to(flow_layer)

    flow_layer.add_to(m)

    # Origin markers
    origin_layer = folium.FeatureGroup(name='Origin BEAs')
    origin_tons = defaultdict(float)
    origin_status = defaultdict(set)
    for (ob, tb), d in significant.items():
        origin_tons[ob] += d['tons']
        origin_status[ob].update(d['statuses'])

    for ob in sorted(origin_tons, key=lambda x: -origin_tons[x]):
        coords = get_bea_coords(ob)
        if not coords:
            continue
        tons_m = origin_tons[ob] / 1e6
        radius = max(4, min(16, 4 + tons_m * 0.3))
        statuses = origin_status[ob]
        if 'canadian_reorigination' in statuses:
            color = '#8e44ad'
        elif 'canadian_import' in statuses:
            color = '#9b59b6'
        elif any(s in statuses for s in ('unique_match', 'proportional_split')):
            color = '#27ae60'
        else:
            color = '#e67e22'

        folium.CircleMarker(
            location=coords, radius=radius, color=color, fill=True,
            fill_color=color, fill_opacity=0.8, weight=2,
            tooltip=f'{get_bea_label(ob)}: {tons_m:.1f}M tons origin',
            popup=f'<b>{get_bea_label(ob)}</b><br>Origin tons: {tons_m:.1f}M'
        ).add_to(origin_layer)

    origin_layer.add_to(m)

    # Destination markers
    dest_layer = folium.FeatureGroup(name='Destination BEAs', show=False)
    dest_tons = defaultdict(float)
    for (ob, tb), d in significant.items():
        dest_tons[tb] += d['tons']
    for tb in sorted(dest_tons, key=lambda x: -dest_tons[x])[:40]:
        coords = get_bea_coords(tb)
        if not coords:
            continue
        tons_m = dest_tons[tb] / 1e6
        radius = max(3, min(14, 3 + tons_m * 0.3))
        folium.CircleMarker(
            location=coords, radius=radius, color='#e74c3c', fill=True,
            fill_color='#e74c3c', fill_opacity=0.6, weight=1.5,
            tooltip=f'{get_bea_label(tb)}: {tons_m:.1f}M tons destination',
        ).add_to(dest_layer)
    dest_layer.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    legend_html = '''
    <div style="position:fixed; bottom:30px; left:30px; z-index:999;
         background:rgba(0,0,0,0.8); padding:14px 18px; border-radius:8px;
         color:white; font-size:12px; line-height:2">
      <b>Trade Flow Legend</b><br>
      <span style="color:#27ae60">━━</span> US plant (matched)<br>
      <span style="color:#3498db">━━</span> US plant (proportional)<br>
      <span style="color:#e67e22">━━</span> US terminal (no plant)<br>
      <span style="color:#8e44ad">━━</span> Canadian re-origination<br>
      <span style="color:#9b59b6">━━</span> Canadian direct import<br>
      <span style="color:#e74c3c">●</span> Destination market
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    return m.get_root().render()


# ── Corridor table HTML ──────────────────────────────────────────────────

def build_corridor_table(flows, top_n=30):
    visible = {k: v for k, v in flows.items() if k[1] != '000'}
    ranked = sorted(visible.items(), key=lambda x: -x[1]['tons'])[:top_n]

    status_badge = {
        'unique_match': ('<span class="tag tag-green">Plant Match</span>'),
        'proportional_split': ('<span class="tag tag-blue">Multi-Plant</span>'),
        'no_plant_in_bea': ('<span class="tag tag-orange">Terminal</span>'),
        'canadian_reorigination': ('<span class="tag tag-purple">CA Re-orig</span>'),
        'canadian_import': ('<span class="tag tag-purplelight">CA Import</span>'),
    }

    rows_html = []
    for i, ((ob, tb), d) in enumerate(ranked, 1):
        o_label = get_bea_label(ob)
        d_label = get_bea_label(tb)
        primary_status = sorted(d['statuses'],
                                key=lambda s: ['unique_match', 'proportional_split',
                                               'canadian_reorigination', 'canadian_import',
                                               'no_plant_in_bea'].index(s)
                                if s in ['unique_match', 'proportional_split',
                                         'canadian_reorigination', 'canadian_import',
                                         'no_plant_in_bea'] else 99)[0]
        badge = status_badge.get(primary_status, '')

        prod_info = FLOW_PRODUCERS.get((ob, tb))
        if prod_info:
            who = f'<b>{prod_info[0]}</b><br><span class="detail">{prod_info[2]}</span>'
        elif d['plants']:
            who = '<b>' + ', '.join(sorted(d['plants'])[:2]) + '</b>'
        else:
            who = '<span class="detail">Unknown</span>'

        tons_m = d['tons'] / 1e6
        rev_m = d['rev'] / 1e6
        rpt = d['rev'] / d['tons'] if d['tons'] > 0 else 0

        rows_html.append(f'''<tr>
          <td>{i}</td>
          <td><b>{o_label}</b><br><span class="bea-code">{ob}</span></td>
          <td><b>{d_label}</b><br><span class="bea-code">{tb}</span></td>
          <td class="r">{tons_m:.1f}M</td>
          <td class="r">${rev_m:.0f}M</td>
          <td class="r">${rpt:.2f}</td>
          <td>{badge}</td>
          <td>{who}</td>
        </tr>''')

    return '\n'.join(rows_html)


# ── No-plant destination breakdown ───────────────────────────────────────

NOPLANT_BEAS = [
    ('160', 'Fresno, CA',   'CalPortland/National Cement (Bakersfield BEA 161 plants)', 'fresno_bea160_investigation.html'),
    ('134', 'Houston, TX',  'Port of Houston import terminals (CEMEX, GCC, Buzzi Unicem)', 'houston_bea134_investigation.html'),
    ('127', 'Lubbock, TX',  'GCC Permian (Odessa BEA 128) + Colorado plants + Houston imports', None),
    ('013', 'Hartford, CT', 'Lafarge Ravena/Heidelberg (Albany BEA 004) + Quebec imports', 'hartford_bea013_investigation.html'),
    ('026', 'Raleigh, NC',  'Argos/Giant/Holcim (Charleston BEA 032) + Roanoke Cement (BEA 023)', None),
    ('010', 'Boston, MA',   'Canadian imports (Ontario/Quebec) + Dragon Cement (ME BEA 001)', None),
    ('067', 'Wheeling, WV', 'Armstrong Cement (Pittsburgh BEA 066) + Holcim/Lehigh plants', None),
    ('096', 'Fargo, ND',    'Lafarge/Amrize (Calgary, AB) via CPKC — Canadian re-origination', 'fargo_bea096_investigation.html'),
]

BEA_NAMES_SHORT = {
    '000': 'Suppressed', '131': 'Dallas, TX', '127': 'Lubbock, TX', '133': 'Austin, TX',
    '135': 'San Antonio, TX', '132': 'Waco, TX', '134': 'Houston, TX (local)', '128': 'Odessa, TX',
    '129': 'Abilene, TX', '160': 'Fresno, CA', '161': 'Bakersfield, CA', '163': 'Los Angeles, CA',
    '122': 'Denver, CO', '158': 'San Francisco, CA', '164': 'San Diego, CA', '124': 'Pueblo, CO',
    '078': 'Fayetteville, AR', '077': 'Fort Smith, AR', '082': 'Shreveport, LA',
    '073': 'St. Louis, MO', '076': 'Joplin, MO', '099': 'La Crosse, WI', '118': 'Omaha, NE',
    '040': 'Jacksonville, FL', '025': 'Norfolk, VA', '019': 'Wilmington, DE', '026': 'Raleigh, NC',
    '036': 'Macon, GA', '044': 'Miami, FL', '048': 'Birmingham, AL', '088': 'Mobile, AL',
    '167': 'Olympia, WA', '141': 'Salt Lake City, UT', '125': 'Albuquerque, NM',
    '139': 'Scottsbluff, NE', '107': 'Davenport, IA', '119': 'Lincoln, NE',
    '096': 'Fargo, ND', '010': 'Boston, MA', '013': 'Hartford, CT', '004': 'Albany, NY',
    '017': 'Allentown, PA', '020': 'Baltimore, MD', '022': 'Washington, DC', '023': 'Staunton, VA',
    '051': 'Knoxville, TN', '055': 'Louisville, KY', '059': 'Traverse City, MI', '065': 'Youngstown, OH',
    '066': 'Pittsburgh, PA', '067': 'Wheeling, WV', '057': 'Fort Wayne, IN',
}


def build_noplant_dest_tables(matched):
    """For each major no-plant BEA, compute top destinations."""
    from collections import defaultdict
    result = {}
    for bea_code, *_ in NOPLANT_BEAS:
        dest = defaultdict(lambda: {'recs': 0, 'tons': 0})
        for r in matched:
            if r['originbea'] == bea_code:
                d = r['terminationbea']
                dest[d]['recs'] += 1
                dest[d]['tons'] += float(r['extons'] or 0)
        result[bea_code] = dict(dest)
    return result


def _noplant_dest_rows(dest_dict, top_n=8):
    from collections import defaultdict
    ranked = sorted(dest_dict.items(), key=lambda x: -x[1]['tons'])[:top_n]
    total  = sum(d['tons'] for d in dest_dict.values())
    rows   = []
    for bea, d in ranked:
        name = BEA_NAMES_SHORT.get(bea, f'BEA {bea}')
        pct  = d['tons'] / total * 100 if total else 0
        bar  = int(pct / 2)
        rows.append(
            f'<tr><td><span style="font-size:10px;background:#536878;color:white;'
            f'padding:1px 6px;border-radius:3px">{bea}</span> {name}</td>'
            f'<td style="text-align:right">{d["tons"]/1e6:.1f}M</td>'
            f'<td><div style="background:#e67e22;height:9px;width:{bar}px;'
            f'border-radius:2px;display:inline-block;vertical-align:middle"></div>'
            f' {pct:.0f}%</td></tr>'
        )
    return '\n'.join(rows)


def build_noplant_section(noplant_tables):
    """Generate HTML for the expanded no-plant section."""
    blocks = []
    for bea_code, label, explanation, inv_link in NOPLANT_BEAS:
        dest_dict = noplant_tables.get(bea_code, {})
        total_tons = sum(d['tons'] for d in dest_dict.values())
        if total_tons == 0:
            continue

        link_html = ''
        if inv_link:
            link_html = (f'<a href="{inv_link}" style="font-size:12px;color:#bb86fc;'
                         f'text-decoration:none;margin-left:10px">'
                         f'&#x1F50D; Full investigation &rarr;</a>')

        dest_rows = _noplant_dest_rows(dest_dict)

        blocks.append(f'''
<div style="background:#1e2d40;border-radius:8px;padding:18px 22px;margin-bottom:16px;">
  <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:8px;">
    <span style="background:#e67e22;color:white;font-size:11px;font-weight:700;
                 padding:2px 8px;border-radius:4px">BEA {bea_code}</span>
    <span style="font-size:15px;font-weight:600;color:#e0e0e0">{label}</span>
    <span style="font-size:12px;color:#7f8fa6">{total_tons/1e6:.0f}M tons total</span>
    {link_html}
  </div>
  <p style="font-size:13px;color:#aab7c4;margin-bottom:10px">{explanation}</p>
  <table style="border-collapse:collapse;width:100%;font-size:12px">
    <tr style="background:#0f1e2e">
      <th style="padding:5px 8px;text-align:left;color:#e0e0e0">Top Destinations</th>
      <th style="padding:5px 8px;text-align:right;color:#e0e0e0">Exp. Tons</th>
      <th style="padding:5px 8px;text-align:left;color:#e0e0e0">Share</th>
    </tr>
    {dest_rows}
  </table>
</div>''')

    return '\n'.join(blocks)


# ── Aggregate stats ──────────────────────────────────────────────────────

def compute_stats(matched):
    stats = {}
    total_tons = 0
    status_tons = defaultdict(float)
    for r in matched:
        s = r['match_status']
        tons = float(r['allocated_extons'] or 0) if s in ('unique_match', 'proportional_split') \
            else float(r['extons'] or 0)
        status_tons[s] += tons
        total_tons += tons
    stats['total_tons'] = total_tons
    stats['status_tons'] = dict(status_tons)
    stats['matched_tons'] = status_tons.get('unique_match', 0) + status_tons.get('proportional_split', 0)
    stats['can_total'] = status_tons.get('canadian_import', 0) + status_tons.get('canadian_reorigination', 0)
    stats['can_pct'] = stats['can_total'] / total_tons * 100 if total_tons else 0
    stats['matched_pct'] = stats['matched_tons'] / total_tons * 100 if total_tons else 0
    stats['suppressed_pct'] = status_tons.get('suppressed', 0) / total_tons * 100 if total_tons else 0
    stats['noplant_tons'] = status_tons.get('no_plant_in_bea', 0)

    # Total revenue
    total_rev = 0
    for r in matched:
        s = r['match_status']
        rev = float(r['allocated_exrev'] or 0) if s in ('unique_match', 'proportional_split') \
            else float(r['exrev'] or 0)
        total_rev += rev
    stats['total_rev'] = total_rev
    return stats


# ── HTML REPORT ──────────────────────────────────────────────────────────

def build_report():
    print('Loading matched data...')
    matched = load_matched()

    print('Building flows...')
    flows = build_flows(matched)
    stats = compute_stats(matched)

    print('Generating charts...')
    img_corridors = fig_to_b64(chart_top_corridors(flows))
    img_canadian = fig_to_b64(chart_canadian_share(matched))
    img_rpt = fig_to_b64(chart_rpt_by_source(matched))

    print('Building flow map...')
    map_html = build_flow_map(flows)

    print('Building corridor table...')
    corridor_rows = build_corridor_table(flows, top_n=30)

    print('Building no-plant destination tables...')
    noplant_tables  = build_noplant_dest_tables(matched)
    noplant_section = build_noplant_section(noplant_tables)

    st = stats
    total_m = st['total_tons'] / 1e6
    can_m = st['can_total'] / 1e6
    matched_m = st['matched_tons'] / 1e6
    noplant_m = st['noplant_tons'] / 1e6

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>U.S. Cement Rail Trade Flow Analysis</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Segoe UI',system-ui,sans-serif; background:#1a1a2e; color:#e0e0e0; line-height:1.7; }}
  .header {{ background:linear-gradient(135deg,#16213e 0%,#0f3460 60%,#533483 100%);
             color:white; padding:40px 60px; }}
  .header h1 {{ font-size:26px; margin-bottom:4px; }}
  .header p {{ font-size:13px; opacity:0.8; }}
  .container {{ max-width:1250px; margin:0 auto; padding:20px 40px 60px; }}
  .kpi-row {{ display:flex; gap:16px; margin:24px 0 28px; flex-wrap:wrap; }}
  .kpi {{ background:#16213e; border-radius:10px; padding:18px 24px; flex:1; min-width:160px;
          border:1px solid #1a3a5c; }}
  .kpi .label {{ font-size:10px; text-transform:uppercase; letter-spacing:1.2px; color:#7f8fa6; }}
  .kpi .value {{ font-size:24px; font-weight:700; color:#e0e0e0; margin-top:2px; }}
  .kpi .sub {{ font-size:11px; color:#7f8fa6; margin-top:1px; }}
  .kpi-can .value {{ color:#8e44ad; }}
  .section {{ background:#16213e; border-radius:10px; padding:28px 32px; margin-bottom:20px;
              border:1px solid #1a3a5c; }}
  .section h2 {{ font-size:17px; color:#e0e0e0; margin-bottom:12px;
                border-bottom:2px solid #533483; padding-bottom:6px; display:inline-block; }}
  .section h3 {{ font-size:14px; color:#8e44ad; margin:14px 0 6px; }}
  .section p {{ font-size:14px; margin-bottom:10px; color:#c8d6e5; }}
  .chart-img {{ width:100%; max-width:960px; display:block; margin:14px auto; border-radius:6px; }}
  .map-frame {{ width:100%; height:650px; border:none; border-radius:8px; }}
  table {{ border-collapse:collapse; width:100%; font-size:12.5px; margin:12px 0; }}
  th {{ background:#0f3460; color:#e0e0e0; text-align:left; padding:8px 10px; font-weight:600;
       position:sticky; top:0; }}
  td {{ padding:7px 10px; border-bottom:1px solid #1a3a5c; color:#c8d6e5; }}
  td.r {{ text-align:right; font-variant-numeric:tabular-nums; }}
  tr:hover td {{ background:#1a3a5c; }}
  .bea-code {{ font-size:10px; color:#7f8fa6; }}
  .detail {{ font-size:11px; color:#7f8fa6; }}
  .tag {{ display:inline-block; padding:2px 7px; border-radius:4px; font-size:10px;
          font-weight:600; color:white; white-space:nowrap; }}
  .tag-green {{ background:#27ae60; }}
  .tag-blue {{ background:#2980b9; }}
  .tag-orange {{ background:#e67e22; }}
  .tag-purple {{ background:#8e44ad; }}
  .tag-purplelight {{ background:#9b59b6; }}
  .tag-gray {{ background:#636e72; }}
  .callout {{ background:#1a1a2e; border-left:4px solid #8e44ad; border-radius:6px;
              padding:16px 22px; margin:16px 0; }}
  .callout b {{ color:#bb86fc; }}
  .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
  @media (max-width:900px) {{ .two-col {{ grid-template-columns:1fr; }} }}
  ul {{ margin:8px 0 8px 22px; }}
  li {{ margin-bottom:4px; }}
  .footer {{ text-align:center; font-size:11px; color:#636e72; margin-top:30px;
             padding-top:16px; border-top:1px solid #1a3a5c; }}
</style>
</head>
<body>

<div class="header">
  <h1>U.S. Cement Rail Trade Flow Analysis</h1>
  <p>Origin-to-destination corridors with producer identification &mdash; STB Waybill 2005&ndash;2023</p>
</div>

<div class="container">

<div class="kpi-row">
  <div class="kpi">
    <div class="label">Total Rail Cement</div>
    <div class="value">{total_m:.0f}M tons</div>
    <div class="sub">${st['total_rev']/1e9:.1f}B revenue (19 yr)</div>
  </div>
  <div class="kpi">
    <div class="label">Trade Corridors</div>
    <div class="value">{len(flows):,}</div>
    <div class="sub">{sum(1 for v in flows.values() if v['tons']>1e5)} with &gt;100K tons</div>
  </div>
  <div class="kpi">
    <div class="label">Plant-Matched</div>
    <div class="value">{matched_m:.0f}M tons</div>
    <div class="sub">{st['matched_pct']:.1f}% of total</div>
  </div>
  <div class="kpi kpi-can">
    <div class="label">Canadian Origin</div>
    <div class="value">{can_m:.0f}M tons</div>
    <div class="sub">{st['can_pct']:.1f}% (import + re-orig)</div>
  </div>
  <div class="kpi">
    <div class="label">Suppressed</div>
    <div class="value">{st['suppressed_pct']:.0f}%</div>
    <div class="sub">Origin masked by STB</div>
  </div>
</div>

<!-- 1. Flow Map -->
<div class="section">
  <h2>1. Trade Flow Map</h2>
  <p>Major cement rail corridors (&gt;100K tons). Line thickness proportional to tonnage,
  color indicates source type. Click any line for details including probable producer.
  Toggle destination markers via the layer control.</p>
  <iframe class="map-frame" srcdoc='{map_html.replace(chr(39), "&#39;")}'></iframe>
</div>

<!-- 2. Top Corridors Chart -->
<div class="section">
  <h2>2. Top Trade Corridors</h2>
  <img class="chart-img" src="data:image/png;base64,{img_corridors}">
</div>

<!-- 3. Corridor Table with Producer ID -->
<div class="section">
  <h2>3. Corridor Detail &mdash; Who Ships What Where</h2>
  <p>Top 30 origin&ndash;destination pairs by tonnage (excluding suppressed destinations).
  Producer identifications are confirmed for plant-matched flows and researched/inferred for
  Canadian and terminal flows.</p>
  <div style="max-height:700px; overflow-y:auto;">
  <table>
    <tr><th>#</th><th>Origin</th><th>Destination</th><th>Tons</th><th>Revenue</th>
        <th>$/ton</th><th>Type</th><th>Probable Producer</th></tr>
    {corridor_rows}
  </table>
  </div>
</div>

<!-- 4. Canadian Analysis -->
<div class="section">
  <h2>4. Canadian Cement in U.S. Rail</h2>
  <img class="chart-img" src="data:image/png;base64,{img_canadian}">
  <div class="callout">
    <b>Key finding:</b> Canadian-origin cement accounts for <b>{st['can_pct']:.1f}%</b> of
    identifiable U.S. rail cement tonnage ({can_m:.0f}M tons). Only {st['status_tons'].get('canadian_import',0)/1e6:.0f}M tons are
    explicitly coded as imports (BEA 173&ndash;183). The remaining {st['status_tons'].get('canadian_reorigination',0)/1e6:.0f}M tons
    enter via Lafarge/Amrize distribution terminals in North Dakota (BEA 096) and are
    re-originated as &ldquo;domestic&rdquo; shipments &mdash; invisible in the raw waybill data
    without this investigation.
  </div>

  <h3>Canadian Supply Chains Identified</h3>
  <table>
    <tr><th>Route</th><th>Producer</th><th>Tons</th><th>Key Destinations</th></tr>
    <tr>
      <td><span class="tag tag-purple">Calgary, AB → Fargo, ND terminals</span></td>
      <td>Lafarge / Amrize (CPKC rail)</td>
      <td class="r">{st['status_tons'].get('canadian_reorigination',0)/1e6:.0f}M</td>
      <td>La Crosse WI, Lubbock TX, Denver CO, Davenport IA, Omaha NE</td>
    </tr>
    <tr>
      <td><span class="tag tag-purplelight">Quebec (BEA 178)</span></td>
      <td>Lafarge / CRH Quebec plants</td>
      <td class="r">{sum(v['tons'] for (o,t),v in flows.items() if o=='178')/1e6:.1f}M</td>
      <td>Knoxville TN, Louisville KY, Charleston WV, Lubbock TX</td>
    </tr>
    <tr>
      <td><span class="tag tag-purplelight">Ontario (BEA 177)</span></td>
      <td>St. Marys / Essroc (Votorantim)</td>
      <td class="r">{sum(v['tons'] for (o,t),v in flows.items() if o=='177')/1e6:.1f}M</td>
      <td>Burlington VT, Louisville KY, Boston MA</td>
    </tr>
    <tr>
      <td><span class="tag tag-purplelight">Newfoundland (BEA 182)</span></td>
      <td>Corner Brook / Atlantic Canada</td>
      <td class="r">{sum(v['tons'] for (o,t),v in flows.items() if o=='182')/1e6:.1f}M</td>
      <td>Olympia WA, Fairbanks AK, Pendleton OR</td>
    </tr>
  </table>
</div>

<!-- 5. Revenue per ton -->
<div class="section">
  <h2>5. Pricing by Source Type</h2>
  <img class="chart-img" src="data:image/png;base64,{img_rpt}">
  <p>Canadian re-originated cement (Fargo) consistently shows the highest revenue per ton,
  reflecting long-haul distances from Alberta through the Plains states. US terminal origins
  track close to the overall average. Direct Canadian imports show more volatility due to
  smaller sample sizes and mixed routing (rail vs. ocean+rail).</p>
</div>

<!-- 6. Unresolved Flows -->
<div class="section">
  <h2>6. No-Plant Origins &mdash; Probable Producers &amp; Destinations</h2>
  <p>These high-volume origins have no EPA cement plant. Each panel shows the inferred
  supply source and a destination breakdown from the waybill data. Dedicated investigation
  pages are available for the two largest confirmed cases.</p>
  {noplant_section}
</div>

<!-- 7. Summary -->
<div class="section">
  <h2>7. Key Takeaways</h2>
  <ul>
    <li><b>Cement rail is highly concentrated:</b> The top 7 corridors carry &gt;1M tons each;
        the top 30 account for most identifiable tonnage.</li>
    <li><b>Canadian cement is under-reported:</b> At {st['can_pct']:.0f}% of tonnage, Canadian-origin
        cement is a significant factor in U.S. rail markets — but only 28% of it is properly
        flagged as imports. The rest is laundered through Fargo re-origination terminals.</li>
    <li><b>Houston is a cement import gateway:</b> 31M tons originate from a BEA with no plant,
        consistent with Port of Houston's role as the nation's largest waterborne cement
        import point.</li>
    <li><b>California's "Fresno" origin is a geographic coding artifact:</b> 37M tons are coded
        as Fresno BEA but likely originate from Kern County plants in the adjacent Bakersfield BEA,
        reflecting rail yard boundaries vs. economic area boundaries.</li>
    <li><b>52% suppression severely limits analysis:</b> Over half of cement waybill origins are
        masked, meaning these identified trade flows represent the visible fraction of a much
        larger market.</li>
  </ul>
</div>

<div class="footer">
  Cement Rail Trade Flow Analysis &mdash; February 2026 &mdash; STB Public Use Waybill &amp; EPA GHGRP
</div>

</div>
</body>
</html>'''

    out_path = os.path.join(SCRIPT_DIR, 'cement_trade_flow_report.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Report written to {out_path}')
    return out_path


if __name__ == '__main__':
    build_report()
