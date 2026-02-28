# Reports

Master report generation pipeline. Generated as Markdown (for review) and DOCX (for publication).

## Master Reports

### US Bulk Supply Chain Report (`us_bulk_supply_chain/`)
10 chapters + annexes. Commodity-agnostic infrastructure analysis.

### Cement Commodity Report (`cement_commodity_report/`)
10 chapters. References and extends the core report for cement/SCM markets.

## Templates (`templates/`)
- `executive_briefing.md` — 1-2 page executive summary
- `market_report.md` — Full market report
- `technical_methodology.md` — White paper / methodology
- `data_appendix.md` — Data tables and source documentation

## Report Generation

```bash
report-platform report generate --report us_bulk_supply_chain --format docx
report-platform report generate --report cement_commodity --format docx
```
