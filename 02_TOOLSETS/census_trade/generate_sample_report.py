"""Generate a sample cargo HS6 classification report in HTML."""
import json
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

with open('data/cargo_hs6_dictionary.json') as f:
    d = json.load(f)

ref = d['hs6_lookup']

# ── Aggregate data ──

group_agg = defaultdict(lambda: {'codes': 0, 'mt': 0, 'exp': 0, 'imp': 0, 'manual': 0, 'heading': 0, 'chapter': 0})
for hs6, e in ref.items():
    g = group_agg[e['group']]
    g['codes'] += 1
    g['mt'] += e['total_mt']
    g['exp'] += e['export_ves_mt']
    g['imp'] += e['import_ves_mt']
    g[e['mapping_source']] += 1

grand_mt = sum(g['mt'] for g in group_agg.values())

commodity_agg = defaultdict(lambda: {'codes': 0, 'exp': 0, 'imp': 0, 'mt': 0, 'manual': 0, 'heading': 0, 'chapter': 0})
for hs6, e in ref.items():
    key = (e['group'], e['commodity'])
    c = commodity_agg[key]
    c['codes'] += 1
    c['exp'] += e['export_ves_mt']
    c['imp'] += e['import_ves_mt']
    c['mt'] += e['total_mt']
    c[e['mapping_source']] += 1

src_stats = defaultdict(lambda: {'codes': 0, 'mt': 0})
for hs6, e in ref.items():
    s = src_stats[e['mapping_source']]
    s['codes'] += 1
    s['mt'] += e['total_mt']

# ── Build HTML ──

GROUP_COLORS = {
    'Dry Bulk': '#4a90d9',
    'Liquid Bulk': '#d94a4a',
    'Liquid Gas': '#e8a838',
    'Containerized': '#50b050',
    'Dry': '#9b59b6',
}

SRC_BADGES = {
    'manual': '<span class="badge manual">Manual</span>',
    'heading': '<span class="badge heading">Heading</span>',
    'chapter': '<span class="badge chapter">Chapter</span>',
}


def fmt(n):
    return f"{n:,.0f}"


def pct(n, total):
    return f"{n / total * 100:.1f}%" if total else "0%"


def src_badge(source):
    return SRC_BADGES.get(source, source)


def src_summary(v):
    parts = []
    for s, label in [('manual', 'M'), ('heading', 'H'), ('chapter', 'C')]:
        if v[s] > 0:
            parts.append(f'{label}{v[s]}')
    return ' / '.join(parts)


html = []
html.append("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cargo HS6 Classification Report</title>
<style>
  :root {
    --bg: #0d1117; --surface: #161b22; --border: #30363d;
    --text: #e6edf3; --text-dim: #8b949e; --accent: #58a6ff;
    --green: #3fb950; --red: #f85149; --yellow: #d29922; --purple: #bc8cff;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
         background: var(--bg); color: var(--text); line-height: 1.5; padding: 24px; }
  .container { max-width: 1400px; margin: 0 auto; }
  h1 { font-size: 28px; margin-bottom: 4px; }
  .subtitle { color: var(--text-dim); font-size: 14px; margin-bottom: 32px; }
  h2 { font-size: 20px; margin: 40px 0 16px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
  h3 { font-size: 16px; margin: 24px 0 12px; color: var(--text-dim); }

  /* Summary cards */
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 32px; }
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 20px; }
  .card .label { font-size: 12px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; }
  .card .value { font-size: 28px; font-weight: 600; margin-top: 4px; }
  .card .detail { font-size: 12px; color: var(--text-dim); margin-top: 4px; }

  /* Tables */
  table { width: 100%; border-collapse: collapse; margin: 12px 0 24px; font-size: 13px; }
  th { background: var(--surface); color: var(--text-dim); font-weight: 600; text-transform: uppercase;
       font-size: 11px; letter-spacing: 0.5px; padding: 10px 12px; text-align: left;
       border-bottom: 2px solid var(--border); position: sticky; top: 0; }
  td { padding: 8px 12px; border-bottom: 1px solid var(--border); }
  tr:hover td { background: rgba(88, 166, 255, 0.04); }
  .right { text-align: right; }
  .mono { font-family: 'SF Mono', 'Consolas', monospace; font-size: 12px; }
  .total-row td { font-weight: 700; border-top: 2px solid var(--border); background: var(--surface); }
  .group-header td { background: var(--surface); font-weight: 700; font-size: 14px;
                     padding: 14px 12px 10px; border-bottom: 2px solid var(--border); }

  /* Badges */
  .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
  .badge.manual { background: rgba(63, 185, 80, 0.15); color: var(--green); }
  .badge.heading { background: rgba(88, 166, 255, 0.15); color: var(--accent); }
  .badge.chapter { background: rgba(210, 153, 34, 0.15); color: var(--yellow); }

  /* Group color dots */
  .gdot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }

  /* Bar chart (CSS only) */
  .bar-container { display: flex; height: 32px; border-radius: 6px; overflow: hidden; margin: 12px 0 24px; }
  .bar-segment { display: flex; align-items: center; justify-content: center;
                 font-size: 11px; font-weight: 600; color: #fff; min-width: 40px; }
  .bar-legend { display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 24px; font-size: 13px; }
  .bar-legend .swatch { display: inline-block; width: 12px; height: 12px; border-radius: 3px; margin-right: 6px; vertical-align: middle; }

  /* Propagation section */
  .prop-block { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px 20px; margin: 12px 0; }
  .prop-heading { font-weight: 700; font-size: 14px; margin-bottom: 8px; }
  .prop-row { display: flex; gap: 12px; align-items: baseline; padding: 3px 0; font-size: 13px; }
  .prop-row .hs6 { font-family: 'SF Mono', 'Consolas', monospace; min-width: 65px; }
  .prop-row .desc { flex: 1; color: var(--text-dim); }
  .prop-row .cargo { min-width: 150px; }
  .prop-row .vol { min-width: 100px; text-align: right; }
  .prop-auto { background: rgba(88, 166, 255, 0.06); border-radius: 4px; padding: 3px 8px; }

  /* Coverage donut placeholder */
  .coverage-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin: 16px 0; }
  .coverage-bar { height: 8px; background: var(--border); border-radius: 4px; overflow: hidden; margin: 4px 0 2px; }
  .coverage-fill { height: 100%; border-radius: 4px; }

  @media (max-width: 768px) {
    .cards { grid-template-columns: 1fr 1fr; }
    .coverage-grid { grid-template-columns: 1fr; }
    body { padding: 12px; }
  }
</style>
</head>
<body>
<div class="container">
""")

# ── Header ──
html.append("""
<h1>Cargo HS6 Classification Report</h1>
<div class="subtitle">Source: cargo_hs6_dictionary.json &nbsp;|&nbsp; Period: Sep&ndash;Nov 2025 &nbsp;|&nbsp; Vessel-Borne US Trade &nbsp;|&nbsp; Built by build_cargo_dict.py</div>
""")

# ── Summary cards ──
manual_v = src_stats['manual']
heading_v = src_stats['heading']
chapter_v = src_stats['chapter']

html.append('<div class="cards">')
html.append(f'<div class="card"><div class="label">Total HS6 Codes</div><div class="value">{len(ref):,}</div><div class="detail">100% classified</div></div>')
html.append(f'<div class="card"><div class="label">Total Volume</div><div class="value">{grand_mt/1e6:,.1f}M MT</div><div class="detail">Exports + Imports</div></div>')
html.append(f'<div class="card"><div class="label">Manual Mappings</div><div class="value" style="color:var(--green)">{manual_v["codes"]:,}</div><div class="detail">{pct(manual_v["mt"], grand_mt)} of volume</div></div>')
html.append(f'<div class="card"><div class="label">Auto-Classified</div><div class="value" style="color:var(--accent)">{heading_v["codes"] + chapter_v["codes"]:,}</div><div class="detail">{heading_v["codes"]} heading + {chapter_v["codes"]} chapter</div></div>')
html.append('</div>')

# ── Volume bar chart by group ──
html.append('<h2>Volume by Cargo Group</h2>')
html.append('<div class="bar-container">')
for grp, v in sorted(group_agg.items(), key=lambda x: -x[1]['mt']):
    w = v['mt'] / grand_mt * 100
    color = GROUP_COLORS.get(grp, '#666')
    label = f"{grp} {w:.0f}%" if w > 5 else ""
    html.append(f'<div class="bar-segment" style="width:{w}%;background:{color}">{label}</div>')
html.append('</div>')
html.append('<div class="bar-legend">')
for grp in ['Dry Bulk', 'Liquid Bulk', 'Liquid Gas', 'Dry', 'Containerized']:
    color = GROUP_COLORS[grp]
    v = group_agg[grp]
    html.append(f'<span><span class="swatch" style="background:{color}"></span>{grp}: {fmt(v["mt"])} MT ({pct(v["mt"], grand_mt)})</span>')
html.append('</div>')

# ── Section 1: Group Overview Table ──
html.append('<h2>Section 1: Group Overview</h2>')
html.append("""<table>
<tr><th>Group</th><th class="right">Codes</th><th class="right">Manual</th><th class="right">Heading</th>
<th class="right">Chapter</th><th class="right">Exports MT</th><th class="right">Imports MT</th>
<th class="right">Total MT</th><th class="right">Share</th></tr>""")
for grp, v in sorted(group_agg.items(), key=lambda x: -x[1]['mt']):
    color = GROUP_COLORS.get(grp, '#666')
    html.append(f'<tr><td><span class="gdot" style="background:{color}"></span>{grp}</td>'
                f'<td class="right">{v["codes"]:,}</td><td class="right">{v["manual"]:,}</td>'
                f'<td class="right">{v["heading"]:,}</td><td class="right">{v["chapter"]:,}</td>'
                f'<td class="right mono">{fmt(v["exp"])}</td><td class="right mono">{fmt(v["imp"])}</td>'
                f'<td class="right mono"><b>{fmt(v["mt"])}</b></td><td class="right">{pct(v["mt"], grand_mt)}</td></tr>')

gm = sum(g['manual'] for g in group_agg.values())
gh = sum(g['heading'] for g in group_agg.values())
gc = sum(g['chapter'] for g in group_agg.values())
ge = sum(g['exp'] for g in group_agg.values())
gi = sum(g['imp'] for g in group_agg.values())
html.append(f'<tr class="total-row"><td>TOTAL</td><td class="right">{len(ref):,}</td><td class="right">{gm:,}</td>'
            f'<td class="right">{gh:,}</td><td class="right">{gc:,}</td>'
            f'<td class="right mono">{fmt(ge)}</td><td class="right mono">{fmt(gi)}</td>'
            f'<td class="right mono"><b>{fmt(grand_mt)}</b></td><td class="right">100%</td></tr>')
html.append('</table>')

# ── Section 2: Commodity Breakdown by Group ──
html.append('<h2>Section 2: Commodity Breakdown by Group</h2>')

for grp in ['Dry Bulk', 'Liquid Bulk', 'Liquid Gas', 'Dry', 'Containerized']:
    grp_items = {k: v for k, v in commodity_agg.items() if k[0] == grp}
    grp_mt = sum(v['mt'] for v in grp_items.values())
    grp_codes = sum(v['codes'] for v in grp_items.values())
    color = GROUP_COLORS.get(grp, '#666')

    html.append(f'<h3><span class="gdot" style="background:{color}"></span>{grp} &mdash; {grp_codes:,} codes, {fmt(grp_mt)} MT</h3>')
    html.append("""<table>
    <tr><th>Commodity</th><th class="right">Codes</th><th>Source Mix</th>
    <th class="right">Exports MT</th><th class="right">Imports MT</th>
    <th class="right">Total MT</th><th class="right">Share</th></tr>""")
    for (g, co), v in sorted(grp_items.items(), key=lambda x: -x[1]['mt']):
        share = pct(v['mt'], grp_mt)
        html.append(f'<tr><td>{co}</td><td class="right">{v["codes"]}</td><td>{src_summary(v)}</td>'
                    f'<td class="right mono">{fmt(v["exp"])}</td><td class="right mono">{fmt(v["imp"])}</td>'
                    f'<td class="right mono"><b>{fmt(v["mt"])}</b></td><td class="right">{share}</td></tr>')
    html.append('</table>')


# ── Section 3: Agricultural Deep Dive ──
GROUP_DD = 'Dry Bulk'
COMMODITY_DD = 'Agricultural'
codes_dd = {hs6: e for hs6, e in ref.items() if e['group'] == GROUP_DD and e['commodity'] == COMMODITY_DD}

total_dd = sum(e['total_mt'] for e in codes_dd.values())
exp_dd = sum(e['export_ves_mt'] for e in codes_dd.values())
imp_dd = sum(e['import_ves_mt'] for e in codes_dd.values())

html.append(f'<h2>Section 3: Deep Dive &mdash; {GROUP_DD} / {COMMODITY_DD}</h2>')
html.append('<div class="cards">')
html.append(f'<div class="card"><div class="label">HS6 Codes</div><div class="value">{len(codes_dd)}</div></div>')
html.append(f'<div class="card"><div class="label">Total Volume</div><div class="value">{total_dd/1e6:,.1f}M MT</div></div>')
html.append(f'<div class="card"><div class="label">Exports</div><div class="value">{exp_dd/1e6:,.1f}M MT</div><div class="detail">{pct(exp_dd, total_dd)} of total</div></div>')
html.append(f'<div class="card"><div class="label">Imports</div><div class="value">{imp_dd/1e6:,.1f}M MT</div><div class="detail">{pct(imp_dd, total_dd)} of total</div></div>')
html.append('</div>')

cargo_dd = defaultdict(lambda: {'exp': 0, 'imp': 0, 'total': 0, 'codes': 0, 'sources': defaultdict(int)})
for hs6, e in codes_dd.items():
    c = cargo_dd[e['cargo']]
    c['exp'] += e['export_ves_mt']
    c['imp'] += e['import_ves_mt']
    c['total'] += e['total_mt']
    c['codes'] += 1
    c['sources'][e['mapping_source']] += 1

html.append("""<table>
<tr><th>Cargo Type</th><th class="right">Codes</th><th>Source</th>
<th class="right">Exports MT</th><th class="right">Imports MT</th>
<th class="right">Total MT</th><th class="right">Share</th></tr>""")
for cargo, v in sorted(cargo_dd.items(), key=lambda x: -x[1]['total']):
    badges = ' '.join(src_badge(s) for s in ['manual', 'heading', 'chapter'] if v['sources'][s] > 0)
    html.append(f'<tr><td><b>{cargo}</b></td><td class="right">{v["codes"]}</td><td>{badges}</td>'
                f'<td class="right mono">{fmt(v["exp"])}</td><td class="right mono">{fmt(v["imp"])}</td>'
                f'<td class="right mono"><b>{fmt(v["total"])}</b></td><td class="right">{pct(v["total"], total_dd)}</td></tr>')
html.append('</table>')

html.append('<h3>Top 30 HS6 Codes by Volume</h3>')
html.append("""<table>
<tr><th>HS6</th><th>Description</th><th>Cargo</th><th>Source</th>
<th class="right">Exports MT</th><th class="right">Imports MT</th><th class="right">Total MT</th></tr>""")
for hs6, e in sorted(codes_dd.items(), key=lambda x: -x[1]['total_mt'])[:30]:
    html.append(f'<tr><td class="mono">{hs6}</td><td>{e["description"][:65]}</td><td>{e["cargo"]}</td>'
                f'<td>{src_badge(e["mapping_source"])}</td>'
                f'<td class="right mono">{fmt(e["export_ves_mt"])}</td>'
                f'<td class="right mono">{fmt(e["import_ves_mt"])}</td>'
                f'<td class="right mono"><b>{fmt(e["total_mt"])}</b></td></tr>')
html.append('</table>')


# ── Section 4: Petroleum Deep Dive ──
codes_pet = {hs6: e for hs6, e in ref.items() if e['group'] == 'Liquid Bulk' and e['commodity'] == 'Petroleum Products'}
total_pet = sum(e['total_mt'] for e in codes_pet.values())
exp_pet = sum(e['export_ves_mt'] for e in codes_pet.values())
imp_pet = sum(e['import_ves_mt'] for e in codes_pet.values())

html.append('<h2>Section 4: Deep Dive &mdash; Liquid Bulk / Petroleum Products</h2>')
html.append('<div class="cards">')
html.append(f'<div class="card"><div class="label">HS6 Codes</div><div class="value">{len(codes_pet)}</div><div class="detail">All manual</div></div>')
html.append(f'<div class="card"><div class="label">Total Volume</div><div class="value">{total_pet/1e6:,.1f}M MT</div></div>')
html.append(f'<div class="card"><div class="label">Exports</div><div class="value">{exp_pet/1e6:,.1f}M MT</div><div class="detail">{pct(exp_pet, total_pet)}</div></div>')
html.append(f'<div class="card"><div class="label">Imports</div><div class="value">{imp_pet/1e6:,.1f}M MT</div><div class="detail">{pct(imp_pet, total_pet)}</div></div>')
html.append('</div>')

html.append("""<table>
<tr><th>HS6</th><th>Description</th><th>Cargo</th>
<th class="right">Exports MT</th><th class="right">Imports MT</th><th class="right">Total MT</th></tr>""")
for hs6, e in sorted(codes_pet.items(), key=lambda x: -x[1]['total_mt']):
    html.append(f'<tr><td class="mono">{hs6}</td><td>{e["description"][:65]}</td><td><b>{e["cargo"]}</b></td>'
                f'<td class="right mono">{fmt(e["export_ves_mt"])}</td>'
                f'<td class="right mono">{fmt(e["import_ves_mt"])}</td>'
                f'<td class="right mono"><b>{fmt(e["total_mt"])}</b></td></tr>')
html.append('</table>')


# ── Section 5: Heading Propagation Examples ──
html.append('<h2>Section 5: Heading Propagation Examples</h2>')
html.append('<p style="color:var(--text-dim);margin-bottom:16px">Unmapped HS6 codes automatically inherit the classification of manually-mapped codes in the same 4-digit HS heading. <span class="badge heading">Heading</span> rows were auto-classified.</p>')

heading_examples = defaultdict(list)
for hs6, e in ref.items():
    if e['mapping_source'] in ('manual', 'heading'):
        heading_examples[hs6[:4]].append((hs6, e))

shown = 0
for heading, items in sorted(heading_examples.items()):
    has_manual = any(e['mapping_source'] == 'manual' for _, e in items)
    has_heading = any(e['mapping_source'] == 'heading' for _, e in items)
    if has_manual and has_heading and len(items) >= 3:
        manual_item = next((hs6, e) for hs6, e in items if e['mapping_source'] == 'manual')
        html.append(f'<div class="prop-block">')
        html.append(f'<div class="prop-heading">Heading {heading} &rarr; {manual_item[1]["cargo"]}</div>')
        for hs6, e in sorted(items, key=lambda x: (0 if x[1]['mapping_source'] == 'manual' else 1, x[0])):
            is_auto = e['mapping_source'] == 'heading'
            cls = ' prop-auto' if is_auto else ''
            badge = src_badge(e['mapping_source'])
            html.append(f'<div class="prop-row{cls}">'
                        f'<span class="hs6">{hs6}</span>'
                        f'<span class="desc">{e["description"][:55]}</span>'
                        f'<span class="cargo">{badge} {e["cargo"]}</span>'
                        f'<span class="vol">{fmt(e["total_mt"])} MT</span>'
                        f'</div>')
        html.append('</div>')
        shown += 1
        if shown >= 6:
            break


# ── Section 6: Chapter Default Examples ──
html.append('<h2>Section 6: Chapter Default Examples</h2>')
html.append('<p style="color:var(--text-dim);margin-bottom:16px">For HS headings with no manual mappings at all, codes receive a broad default classification by HS chapter.</p>')

ch_codes = defaultdict(list)
for hs6, e in ref.items():
    if e['mapping_source'] == 'chapter':
        ch_codes[int(hs6[:2])].append((hs6, e))

html.append("""<table>
<tr><th>Chapter</th><th class="right">Codes</th><th>Default Group</th><th>Default Commodity</th>
<th class="right">Total MT</th><th>Top Code</th></tr>""")
for ch in sorted(ch_codes.keys()):
    items = ch_codes[ch]
    total = sum(e['total_mt'] for _, e in items)
    top = sorted(items, key=lambda x: -x[1]['total_mt'])[0]
    grp_color = GROUP_COLORS.get(top[1]['group'], '#666')
    html.append(f'<tr><td class="mono">Ch.{ch:02d}</td><td class="right">{len(items)}</td>'
                f'<td><span class="gdot" style="background:{grp_color}"></span>{top[1]["group"]}</td>'
                f'<td>{top[1]["commodity"]}</td>'
                f'<td class="right mono">{fmt(total)}</td>'
                f'<td class="mono" style="color:var(--text-dim)">{top[0]} {top[1]["description"][:40]}</td></tr>')
html.append('</table>')


# ── Section 7: Mapping Coverage Summary ──
html.append('<h2>Section 7: Mapping Coverage Summary</h2>')

html.append('<div class="coverage-grid">')

# By code count
html.append('<div class="card">')
html.append('<div class="label">Coverage by Code Count</div>')
for src, color, label in [('manual', 'var(--green)', 'Manual'), ('heading', 'var(--accent)', 'Heading'), ('chapter', 'var(--yellow)', 'Chapter')]:
    v = src_stats[src]
    w = v['codes'] / len(ref) * 100
    html.append(f'<div style="margin-top:12px"><b>{label}</b> &mdash; {v["codes"]:,} codes ({w:.1f}%)</div>')
    html.append(f'<div class="coverage-bar"><div class="coverage-fill" style="width:{w}%;background:{color}"></div></div>')
html.append('</div>')

# By volume
html.append('<div class="card">')
html.append('<div class="label">Coverage by Volume</div>')
for src, color, label in [('manual', 'var(--green)', 'Manual'), ('heading', 'var(--accent)', 'Heading'), ('chapter', 'var(--yellow)', 'Chapter')]:
    v = src_stats[src]
    w = v['mt'] / grand_mt * 100
    html.append(f'<div style="margin-top:12px"><b>{label}</b> &mdash; {fmt(v["mt"])} MT ({w:.1f}%)</div>')
    html.append(f'<div class="coverage-bar"><div class="coverage-fill" style="width:{w}%;background:{color}"></div></div>')
html.append('</div>')

html.append('</div>')  # coverage-grid

html.append("""<table>
<tr><th>Source</th><th class="right">Codes</th><th class="right">% Codes</th>
<th class="right">Volume MT</th><th class="right">% Volume</th></tr>""")
for src in ['manual', 'heading', 'chapter']:
    v = src_stats[src]
    html.append(f'<tr><td>{src_badge(src)} {src.title()}</td><td class="right">{v["codes"]:,}</td>'
                f'<td class="right">{pct(v["codes"], len(ref))}</td>'
                f'<td class="right mono">{fmt(v["mt"])}</td>'
                f'<td class="right">{pct(v["mt"], grand_mt)}</td></tr>')
total_codes = sum(src_stats[s]['codes'] for s in ['manual', 'heading', 'chapter'])
html.append(f'<tr class="total-row"><td>Total</td><td class="right">{total_codes:,}</td>'
            f'<td class="right">100%</td><td class="right mono">{fmt(grand_mt)}</td><td class="right">100%</td></tr>')
html.append('</table>')

html.append('<p style="color:var(--green);font-size:16px;margin-top:16px;font-weight:600">Unmapped codes: 0</p>')

html.append("""
</div>
</body>
</html>
""")

# ── Write ──
outpath = 'data/sample_cargo_report.html'
with open(outpath, 'w', encoding='utf-8') as f:
    f.write('\n'.join(html))

print(f"Wrote: {outpath}")
