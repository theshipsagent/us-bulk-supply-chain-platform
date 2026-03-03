# CLAUDE.md — User Notes Sub-Module
**Module:** `02_TOOLSETS/port_expenses/09_user_notes/`
**Parent:** `02_TOOLSETS/port_expenses/CLAUDE.md`
**Status:** Active — populate continuously | **Created:** 2026-03-02

---

## SESSION OBJECTIVE

This is William's working knowledge repository. When launching a session here, the goal is to capture, organize, and structure domain knowledge — not to write calculators.

---

## WHAT TO BUILD / POPULATE

### Files to create and maintain

**`port_notes.md`**
Port-by-port observations. Format:
```
## New Orleans / Baton Rouge (NOBRA district)
- [EMPIRICAL 2024] Typical Panamax towage: $28,000–$35,000 per call (2 tugs)
- [TARIFF] NOBRA pilotage billed by river segment — get current tariff at nobra.com
- Key agent: [agent name] — reliable, fair fees
- Terminal quirks: grain elevators operate 24/7; no significant overtime premium
```

**`rate_benchmarks.md`**
Empirical rate ranges from William's consulting experience:
```
| Port | Category | Low ($/ST or $) | High | Year | Notes |
|------|----------|-----------------|------|------|-------|
```

**`operator_notes.md`**
William's assessment of tug operators, agents, stevedores by port.

**`charter_party_notes.md`**
How different charter party types affect cost allocation (who pays for what):
- Voyage charter: owner pays port costs, charterer pays cargo costs
- Time charter: charterer pays most port costs
- Bareboat: operator pays everything

**`commodity_handling_notes.md`**
Commodity-specific handling notes that affect costs:
- Grain: FGIS inspection mandatory, 24-hr pre-arrival notice
- Cement: pneumatic discharge = specialized terminal required
- Steel: crane capacity constrains discharge rate

**`reference_pdas.md`**
Anonymized real PDA examples — actual port calls, actual costs, used to calibrate calculators.

---

## GUIDELINES

- No client names in file names or headers — use "Client A", "Handymax vessel", etc.
- Tag each note: `[EMPIRICAL YYYY]`, `[TARIFF YYYY]`, or `[BENCHMARK]`
- When a calculator produces a result that doesn't match experience — note the discrepancy here so the model can be adjusted
