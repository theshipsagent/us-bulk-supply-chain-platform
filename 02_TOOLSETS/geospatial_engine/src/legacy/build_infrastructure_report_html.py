"""
Convert the Lower Mississippi River Industrial Infrastructure Report
from Markdown to a styled HTML document.
"""
import re
import html as html_module
import os

INPUT = r"G:\My Drive\LLM\sources_data_maps\Lower_Mississippi_River_Industrial_Infrastructure_Report.md"
OUTPUT = r"G:\My Drive\LLM\sources_data_maps\_html_web_files\Lower_Mississippi_Industrial_Infrastructure_Report.html"

with open(INPUT, "r", encoding="utf-8") as f:
    md = f.read()

# --- Markdown to HTML conversion (simplified, tailored to this report) ---

lines = md.split("\n")
html_parts = []
in_table = False
in_list = False
in_code = False
toc_entries = []
section_id_counter = 0

def make_id(text):
    """Generate HTML id from heading text."""
    s = text.lower().strip()
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'\s+', '-', s)
    return s

def process_inline(text):
    """Process inline markdown: bold, italic, links, code."""
    # Escape HTML entities first (but preserve our tags)
    # Actually, don't escape - we need to handle links

    # Links: [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', text)

    # Bold: **text**
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)

    # Italic: *text*
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)

    # Inline code: `text`
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    return text

i = 0
while i < len(lines):
    line = lines[i]

    # Code blocks
    if line.strip().startswith("```"):
        if in_code:
            html_parts.append("</pre>")
            in_code = False
        else:
            html_parts.append("<pre>")
            in_code = True
        i += 1
        continue

    if in_code:
        html_parts.append(html_module.escape(line))
        i += 1
        continue

    # Close list if needed
    if in_list and not line.strip().startswith("- ") and not line.strip().startswith("* ") and line.strip() != "":
        html_parts.append("</ul>")
        in_list = False

    # Tables
    if "|" in line and line.strip().startswith("|"):
        cells = [c.strip() for c in line.strip().split("|")[1:-1]]

        if not in_table:
            # Check if next line is separator
            if i + 1 < len(lines) and re.match(r'^\|[\s\-:|]+\|', lines[i+1].strip()):
                html_parts.append('<div class="table-wrap"><table>')
                html_parts.append("<thead><tr>")
                for cell in cells:
                    html_parts.append(f"<th>{process_inline(cell)}</th>")
                html_parts.append("</tr></thead><tbody>")
                in_table = True
                i += 2  # skip header and separator
                continue
            else:
                # Regular table row without header
                if not in_table:
                    html_parts.append('<div class="table-wrap"><table><tbody>')
                    in_table = True

        # Check if this is a separator line
        if re.match(r'^\|[\s\-:|]+\|', line.strip()):
            i += 1
            continue

        html_parts.append("<tr>")
        for cell in cells:
            html_parts.append(f"<td>{process_inline(cell)}</td>")
        html_parts.append("</tr>")
        i += 1
        continue
    elif in_table:
        html_parts.append("</tbody></table></div>")
        in_table = False

    # Headings
    heading_match = re.match(r'^(#{1,6})\s+(.+)', line)
    if heading_match:
        level = len(heading_match.group(1))
        text = heading_match.group(2).strip()
        hid = make_id(text)

        if level <= 2:
            toc_entries.append((level, text, hid))

        html_parts.append(f'<h{level} id="{hid}">{process_inline(text)}</h{level}>')
        i += 1
        continue

    # Horizontal rule
    if re.match(r'^---+\s*$', line.strip()):
        html_parts.append("<hr>")
        i += 1
        continue

    # Unordered list
    list_match = re.match(r'^(\s*)[-*]\s+(.+)', line)
    if list_match:
        if not in_list:
            html_parts.append("<ul>")
            in_list = True
        html_parts.append(f"<li>{process_inline(list_match.group(2))}</li>")
        i += 1
        continue

    # Empty line
    if line.strip() == "":
        if in_list:
            html_parts.append("</ul>")
            in_list = False
        i += 1
        continue

    # Regular paragraph
    html_parts.append(f"<p>{process_inline(line)}</p>")
    i += 1

# Close any open elements
if in_table:
    html_parts.append("</tbody></table></div>")
if in_list:
    html_parts.append("</ul>")
if in_code:
    html_parts.append("</pre>")

body_html = "\n".join(html_parts)

# --- Build full HTML document ---

html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lower Mississippi River Industrial Infrastructure Report</title>
<style>
  :root {{
    --bg: #1a1a2e;
    --bg2: #16213e;
    --bg3: #0f3460;
    --text: #e0e0e0;
    --text2: #b0b0b0;
    --accent: #e94560;
    --accent2: #0ea5e9;
    --accent3: #22c55e;
    --border: #2a2a4a;
    --card: #1e1e3a;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.7;
    padding: 0;
  }}

  /* Header */
  .report-header {{
    background: linear-gradient(135deg, var(--bg2) 0%, var(--bg3) 100%);
    padding: 40px 60px;
    border-bottom: 3px solid var(--accent);
    position: sticky;
    top: 0;
    z-index: 100;
  }}
  .report-header h1 {{
    font-size: 1.8em;
    color: #fff;
    margin-bottom: 4px;
  }}
  .report-header .subtitle {{
    color: var(--accent2);
    font-size: 0.95em;
  }}

  /* Navigation */
  .nav-bar {{
    background: var(--bg2);
    padding: 10px 60px;
    border-bottom: 1px solid var(--border);
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    position: sticky;
    top: 95px;
    z-index: 99;
  }}
  .nav-bar a {{
    color: var(--text2);
    text-decoration: none;
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 0.82em;
    background: var(--bg);
    border: 1px solid var(--border);
    transition: all 0.2s;
    white-space: nowrap;
  }}
  .nav-bar a:hover {{
    background: var(--bg3);
    color: #fff;
    border-color: var(--accent2);
  }}

  /* Main content */
  .content {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 30px 60px 80px;
  }}

  /* Headings */
  h1 {{ font-size: 1.8em; color: #fff; margin: 40px 0 16px; padding-top: 20px; }}
  h2 {{ font-size: 1.4em; color: var(--accent); margin: 36px 0 12px; padding-top: 16px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }}
  h3 {{ font-size: 1.15em; color: var(--accent2); margin: 28px 0 10px; }}
  h4 {{ font-size: 1.0em; color: var(--accent3); margin: 20px 0 8px; }}

  /* Paragraphs */
  p {{ margin: 8px 0; color: var(--text); font-size: 0.92em; }}

  /* Links */
  a {{ color: var(--accent2); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}

  /* Strong / emphasis */
  strong {{ color: #fff; }}
  em {{ color: var(--text2); font-style: italic; }}
  code {{ background: var(--bg2); padding: 1px 5px; border-radius: 3px; font-size: 0.88em; color: var(--accent3); }}
  pre {{ background: var(--bg2); padding: 12px 16px; border-radius: 6px; overflow-x: auto; font-size: 0.85em; margin: 10px 0; border: 1px solid var(--border); color: var(--text2); }}

  /* Lists */
  ul {{ margin: 8px 0 8px 24px; }}
  li {{ margin: 3px 0; font-size: 0.92em; color: var(--text); }}

  /* Tables */
  .table-wrap {{ overflow-x: auto; margin: 12px 0; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.85em; }}
  th {{ background: var(--bg3); color: #fff; padding: 8px 12px; text-align: left; border: 1px solid var(--border); font-weight: 600; position: sticky; top: 0; }}
  td {{ padding: 6px 12px; border: 1px solid var(--border); color: var(--text); }}
  tr:nth-child(even) {{ background: rgba(255,255,255,0.02); }}
  tr:hover {{ background: rgba(14,165,233,0.08); }}

  /* HR */
  hr {{ border: none; border-top: 1px solid var(--border); margin: 24px 0; }}

  /* Facility cards - bold paragraphs that start with known patterns */
  p:has(strong:first-child) {{
    background: var(--card);
    padding: 6px 12px;
    border-left: 3px solid var(--accent2);
    border-radius: 0 4px 4px 0;
    margin: 4px 0;
  }}

  /* Search */
  .search-box {{
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 200;
  }}
  .search-box input {{
    background: var(--bg2);
    border: 1px solid var(--border);
    color: #fff;
    padding: 8px 14px;
    border-radius: 20px;
    font-size: 0.9em;
    width: 260px;
    outline: none;
  }}
  .search-box input:focus {{
    border-color: var(--accent2);
    box-shadow: 0 0 10px rgba(14,165,233,0.3);
  }}

  /* Back to top */
  .back-top {{
    position: fixed;
    bottom: 20px;
    left: 20px;
    background: var(--bg3);
    color: #fff;
    border: 1px solid var(--border);
    padding: 8px 14px;
    border-radius: 20px;
    cursor: pointer;
    font-size: 0.85em;
    z-index: 200;
    text-decoration: none;
  }}
  .back-top:hover {{ background: var(--accent); border-color: var(--accent); text-decoration: none; }}

  /* Print */
  @media print {{
    body {{ background: #fff; color: #000; }}
    .report-header, .nav-bar {{ position: static; background: #fff; border-color: #ccc; }}
    .report-header h1 {{ color: #000; }}
    .search-box, .back-top {{ display: none; }}
    h2 {{ color: #c00; }}
    h3 {{ color: #006; }}
    td, th {{ border-color: #ccc; }}
    th {{ background: #eee; color: #000; }}
    a {{ color: #006; }}
  }}
</style>
</head>
<body>

<div class="report-header">
  <h1>Lower Mississippi River Industrial Infrastructure Report</h1>
  <div class="subtitle">Comprehensive Survey of Facilities from Head of Passes to Baton Rouge (Mile 0 to Mile 232) | February 2026</div>
</div>

<div class="nav-bar">
  <a href="#section-1-refineries-7-facilities">Refineries</a>
  <a href="#section-2-chemical-plants-17-facilities">Chemical Plants</a>
  <a href="#section-3-tank-storage-terminals-29-facilities">Tank Storage</a>
  <a href="#section-4-export-grain-elevators-9-facilities--mgmt">Grain Elevators</a>
  <a href="#section-5-bulk-terminals-and-plants-13-facilities">Bulk Terminals</a>
  <a href="#section-6-midstream-transfer-points-13-operators">Midstream</a>
  <a href="#section-7-general-cargo-and-port-wharves-19-facilities">General Cargo</a>
  <a href="#appendix-master-summary-table">Master Table</a>
</div>

<div class="content">
{body_html}
</div>

<a href="#" class="back-top">Top</a>

<div class="search-box">
  <input type="text" id="searchInput" placeholder="Search facilities..." oninput="doSearch(this.value)">
</div>

<script>
function doSearch(q) {{
  if (!q || q.length < 2) {{
    // Remove all highlights
    document.querySelectorAll('mark.hl').forEach(m => {{
      m.outerHTML = m.textContent;
    }});
    return;
  }}
  // Remove old highlights first
  document.querySelectorAll('mark.hl').forEach(m => {{
    m.outerHTML = m.textContent;
  }});

  // Search through content
  const content = document.querySelector('.content');
  const walker = document.createTreeWalker(content, NodeFilter.SHOW_TEXT, null, false);
  const matches = [];
  const re = new RegExp('(' + q.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&') + ')', 'gi');

  while (walker.nextNode()) {{
    const node = walker.currentNode;
    if (node.parentElement.tagName === 'SCRIPT' || node.parentElement.tagName === 'STYLE') continue;
    if (re.test(node.textContent)) {{
      matches.push(node);
    }}
  }}

  matches.forEach(node => {{
    const span = document.createElement('span');
    span.innerHTML = node.textContent.replace(re, '<mark class="hl" style="background:#e94560;color:#fff;padding:1px 2px;border-radius:2px;">$1</mark>');
    node.parentNode.replaceChild(span, node);
  }});

  // Scroll to first match
  const first = document.querySelector('mark.hl');
  if (first) first.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
}}

// Ctrl+F override
document.addEventListener('keydown', function(e) {{
  if ((e.ctrlKey || e.metaKey) && e.key === 'f') {{
    e.preventDefault();
    document.getElementById('searchInput').focus();
  }}
}});
</script>

</body>
</html>"""

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(html_doc)

size_kb = os.path.getsize(OUTPUT) / 1024
print(f"HTML report written: {OUTPUT}")
print(f"Size: {size_kb:.0f} KB")
