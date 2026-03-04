# Web Session Prompt — Post Coal Report to OceanDatum.ai
Created: 2026-03-03

## COPY THIS PROMPT INTO YOUR WEB SESSION

---

I need you to add an **unlinked blog/insights post** to the OceanDatum.ai website. This page should be accessible by direct URL only — not listed in the navigation or sitemap yet.

**The report file is attached / I am pasting it below.**

Report details:
- **Title:** US East Coast Coal Exports — 2025 Year in Review
- **Subtitle:** Hampton Roads & Baltimore
- **Author:** William S. Davis III
- **Date:** March 2026
- **Cover photo:** `coalmine1.jpeg` (Lee Dorsey "Working in the Coal Mine" album cover — already embedded as base64 in the HTML)

---

### What to do:

1. **Add the HTML page to the website** as an unlinked post at a clean URL such as:
   `/insights/usec-coal-exports-2025-year-in-review/`
   (or whatever URL structure the site currently uses for insights/blog posts)

2. **The HTML is fully self-contained** (all CSS, charts, and maps inline). You can either:
   - Embed the entire `<body>` content into the site's page template (preferred — so it inherits site nav/footer), OR
   - Host it as a standalone HTML page if the site has a pattern for that

3. **Upload the cover image** `coalmine1.jpeg` to the site's image/assets folder and update the OG tags:
   ```html
   <meta property="og:image" content="https://oceandatum.ai/assets/img/coalmine1.jpeg">
   <meta name="twitter:image" content="https://oceandatum.ai/assets/img/coalmine1.jpeg">
   ```
   (The OG title and description are already in the HTML `<head>` — just update the image URL)

4. **Do NOT add this page to the main navigation** — unlinked/unlisted only for now.

5. **Do NOT modify any other pages** on the site.

---

### File location (on William's machine):
```
/Users/wsd/Library/CloudStorage/GoogleDrive-takoradiautomations@gmail.com/
  My Drive/LLM/project_master_reporting/
  04_REPORTS/coal_export_report/output/
    usec_coal_2025_year_in_review_20260303.html   ← main report
    coalmine1.jpeg                                 ← cover photo
```

---

### Style notes:
- The report uses OceanDatum dark glassmorphism styling (self-contained, no external CSS needed)
- The nav bar inside the report reads "OceanDatum" — that's intentional
- Keep the report's internal nav links (#markets, #supply, #economics, #outlook) working

---
