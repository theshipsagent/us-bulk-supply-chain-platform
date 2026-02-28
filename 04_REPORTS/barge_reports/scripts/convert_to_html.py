import re

# Read the markdown file
md_path = r"G:\My Drive\LLM\project_barge\report_output\INDUSTRY_BRIEFING_PROFESSIONAL.md"
html_path = r"G:\My Drive\LLM\project_barge\report_output\INDUSTRY_BRIEFING_PROFESSIONAL.html"

with open(md_path, 'r', encoding='utf-8') as f:
    md_content = f.read()

# Simple markdown to HTML conversion
html_body = md_content

# Convert headers
html_body = re.sub(r'^### (.*?)$', r'<h3 id="\1">\1</h3>', html_body, flags=re.MULTILINE)
html_body = re.sub(r'^## (.*?)$', r'<h2 id="\1">\1</h2>', html_body, flags=re.MULTILINE)
html_body = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html_body, flags=re.MULTILINE)

# Convert bold
html_body = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_body)

# Convert citations
html_body = re.sub(r'\[SOURCE:(.*?)\]', r'<span class="citation" title="Source: \1">[📚 \1]</span>', html_body)

# Convert line breaks to paragraphs
html_body = html_body.replace('\n\n', '</p><p>')
html_body = '<p>' + html_body + '</p>'

# Clean up artifacts
html_body = html_body.replace('<p><h', '<h')
html_body = html_body.replace('</h1></p>', '</h1>')
html_body = html_body.replace('</h2></p>', '</h2>')
html_body = html_body.replace('</h3></p>', '</h3>')
html_body = html_body.replace('<p>---</p>', '<hr>')
html_body = html_body.replace('<p></p>', '')

# Create full HTML
html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Mississippi River Barge Transportation - Industry Briefing</title>
    <style>
        body {{
            font-family: Georgia, serif;
            line-height: 1.8;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
            color: #333;
            background: #f9f9f9;
        }}

        .container {{
            background: white;
            padding: 60px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}

        h1 {{
            color: #2c3e50;
            font-size: 32px;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
            margin: 30px 0 20px 0;
        }}

        h2 {{
            color: #34495e;
            font-size: 24px;
            margin: 30px 0 15px 0;
            border-left: 5px solid #3498db;
            padding-left: 15px;
        }}

        h3 {{
            color: #555;
            font-size: 20px;
            margin: 20px 0 10px 0;
        }}

        p {{
            margin: 15px 0;
            text-align: justify;
        }}

        .citation {{
            background: #fff3cd;
            color: #856404;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            font-family: 'Courier New', monospace;
            cursor: help;
        }}

        .citation:hover {{
            background: #ffc107;
        }}

        strong {{
            color: #2c3e50;
        }}

        hr {{
            border: none;
            border-top: 2px solid #eee;
            margin: 40px 0;
        }}

        @media print {{
            body {{
                background: white;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_body}
    </div>
</body>
</html>'''

# Write HTML file
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"[OK] HTML created: {html_path}")
print(f"[OK] File size: {len(html):,} characters")
