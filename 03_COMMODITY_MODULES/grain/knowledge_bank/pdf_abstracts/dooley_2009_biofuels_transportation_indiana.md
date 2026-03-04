# Dooley et al. (2009) — Biofuels Impacts on Transportation and Logistics in Indiana

**Last Updated:** 2026-03-01
**Citation:** Dooley, F., Tyner, W., Sinha, K., Quear, J., Cox, L., Cox, M. (July 2009). *The Impacts of Biofuels on Transportation and Logistics in Indiana.* FHWA/IN/JTRP-2009/16. Purdue University, Joint Transportation Research Program. Conducted in cooperation with Indiana DOT, Indiana Department of Agriculture, and FHWA.
**File:** `fulltext.pdf`
**Type:** FHWA-funded academic research report, 90 pages

---

## Overview

This report quantifies how the rapid expansion of ethanol and biodiesel production in Indiana from 2006 to 2010 reshapes the inbound and outbound transportation flows of corn, soybeans, DDGS, and ethanol at the county level. It models the transportation requirements under the scenario of 12 new ethanol plants + 2 new biodiesel plants entering production.

**Key finding:** Adding these biofuels plants increases total annual truckloads by only 8%, but vehicle miles traveled (VMT) by **39%**. The reason: short local hauls from farms to country elevators are replaced by longer hauls to ethanol plants that are not co-located with existing elevator networks.

---

## Policy / Legislative Context

Ethanol industry expansion was driven by a series of federal acts (1978-2008):

| Act | Key Provision |
|---|---|
| Energy Tax Act of 1978 | $0.40/gallon ethanol tax exemption |
| Energy Policy Act of 2005 | Renewable Fuel Standard — 4B gal in 2006 rising to 7.5B by 2012 |
| Energy Independence and Security Act of 2007 | RFS raised to 36B gal by 2022 (15B corn ethanol, 1B biodiesel, 20B advanced) |
| Food, Conservation and Energy Act of 2008 | Starch ethanol subsidy cut to $0.45/gal; cellulosic subsidy = $1.01/gal |

---

## Indiana Ethanol Industry Facts

- **2006:** 1 ethanol plant operating in Indiana
- **Projected 2010:** 13 ethanol + 2 biodiesel plants
- Ethanol plant size distribution: mostly 50-100 million gallon/year
- Plants clustered in high corn-density counties

---

## Transportation Model Structure (8 Steps)

| Step | Component |
|---|---|
| 1 | Grain Production (county-level) |
| 2 | Livestock Feed Demand for DDGS |
| 3 | Livestock Feed Demand for Corn |
| 4 | Livestock Transportation Requirements |
| 5 | Corn for Food Processing and Ethanol |
| 6 | Soybeans for Crushing and Biodiesel |
| 7 | Transportation Requirements for Ethanol to Blenders |
| 8 | Grain Shipped from Grain Elevators |

---

## Key Quantitative Results

### Statewide Impact (2006 → 2010)

| Metric | Change |
|---|---|
| Annual truckloads (all commodities) | +8% |
| Annual VMT (all commodities) | +39% |
| Reason for VMT >> truckload growth | Longer average haul distances to ethanol plants vs. local elevators |

### Modal Flows by Commodity (2002 Indiana baseline)

**Table 2.9 — Distribution of Outbound Shipments by Mode and Bushels Shipped, 2002:**
- Mode split for Indiana outbound grain: truck-dominant for short hauls; rail for longer export movements

### DDGS Movement
- DDGS movement is largely by truck
- Outbound rail movements of ethanol and DDGS partially offset truck growth

### Counties with Biofuels Plants
- Show the most concentrated truck traffic increases
- Adjacent counties also show spillover impacts on road infrastructure

---

## Corn Utilization Framework

Key utilization categories modeled:
1. **Livestock feed** — local truck delivery
2. **Food processing** — truck delivery to processing plants
3. **Ethanol plants** — truck (longer haul) + some rail receiving
4. **Grain elevators** — truck to elevator → rail or barge for export

**Figure 1-12 (referenced):** Corn Utilization for Feed, Food, Exports, and Ethanol, 2001 to 2018 — shows ethanol's rising share of corn demand over the period.

---

## Soybean Utilization Framework

**Figure 1-13 (referenced):** Soybean Utilization for Crush, Seed, Biodiesel and Exports, 2001 to 2018

- Crush (soybean meal + oil) is the dominant domestic use
- Export remains significant
- Biodiesel (soy-based) grows from 2005 forward

---

## Road Infrastructure Implications

The report identifies counties where truck traffic increases are most severe:
- Road maintenance budget requirements will need to shift to high-ethanol counties
- Bridge weight limits become a constraint for heavy corn trucks (286,000-lb railcars are being replaced by heavier trucks making more trips)
- Transportation planners can use county-level VMT projections to anticipate maintenance needs

---

## Key Value for Platform

**Primary use:** Ethanol/biofuel demand modeling for corn; inland transportation flow shifts; county-level modal impact analysis

**Relevance to grain module:**
- Corn demand split (feed vs. food vs. ethanol vs. export) for `market_intelligence/demand_analysis/`
- DDGS as co-product of ethanol; relevant to DDGS export flows in `market_intelligence/trade_flows/`
- Transportation flow modeling methodology for `supply_chain_models/rail_routes/` and barge routes
- Biofuels policy timeline for historical context

---

## Notes

- Study is 2009 vintage — ethanol industry has continued to evolve significantly
- Indiana ethanol capacity has grown well beyond the 2010 projections
- Core methodology (county-level grain flow modeling) remains valid as an analytical framework
- DDGS now a major U.S. export commodity — China is the dominant buyer — updating these findings with current USDA NASS/FAS data is warranted
