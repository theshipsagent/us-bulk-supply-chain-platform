# Chapter 1: Executive Overview — US Bulk Supply Chain Infrastructure

## Executive Summary

The United States operates the world's most extensive inland waterway system, moving over 600 million tons of cargo annually through 12,000 miles of commercially navigable channels, complemented by a 140,000-mile Class I railroad network and 300+ deep-water port facilities. This report provides a comprehensive, commodity-agnostic assessment of the nation's bulk commodity supply chain infrastructure — the interconnected waterway, port, rail, and pipeline networks that underpin the movement of raw materials, agricultural products, energy commodities, and manufactured goods across the continental United States and to global markets.

## Purpose and Scope

This report serves as the foundational reference for commodity-specific analysis modules. By documenting the infrastructure backbone independently of any single commodity vertical, it enables rapid deployment of focused commodity studies — beginning with cement and cementitious materials, with planned extensions to grain, fertilizer, petroleum, and metals.

### Coverage

| Domain | Scope | Primary Data Sources |
|---|---|---|
| Inland Waterways | Mississippi River System, Ohio, Illinois, Gulf ICW, Columbia | USACE WCSC, MRTIS, NDC/LPMS |
| Ports | US Gulf, Atlantic, Pacific deep-water bulk terminals | Port authority tariffs, USACE entrance/clearance |
| Rail | Class I network, URCS cost methodology, intermodal connections | STB economic data, NTAD/NARN, public waybill |
| Pipeline | Petroleum and natural gas trunk lines, terminal infrastructure | EIA, PHMSA |
| Vessel Fleet | Jones Act domestic, foreign-flag import fleet | MARAD, USCG, Panjiva manifests |
| Regulatory | Section 301, Jones Act, environmental compliance | USTR, USCG, EPA, STB |

## Key Findings

### 1. Infrastructure Capacity Under Pressure

The inland waterway system's lock infrastructure is aging — 54% of USACE-maintained locks are beyond their 50-year design life. The Infrastructure Investment and Jobs Act (IIJA) allocated $2.5 billion for inland waterway construction, targeting critical bottlenecks at Chickamauga, Kentucky, and LaGrange locks, but the full modernization backlog exceeds $12 billion.

### 2. Modal Cost Differentials Drive Commodity Routing

Barge transport remains the lowest-cost mode for bulk commodities at $0.008–0.015 per ton-mile, compared to rail at $0.025–0.045 per ton-mile and truck at $0.10–0.25 per ton-mile. For commodities where waterway access exists, the barge-versus-rail cost differential of 40–65% is a decisive factor in supply chain design.

### 3. Regulatory Disruption Reshaping Trade Flows

Section 301 maritime shipping fees targeting Chinese-built vessels (effective October 2025) impose $500,000–$1,000,000 per voyage on bulk carriers, adding $16–33 per ton to delivered costs. This fundamentally alters the economics of bulk import supply chains, particularly for commodities historically sourced from Asia via Chinese-built tonnage.

### 4. Port Infrastructure Concentrated in Gulf Region

The US Gulf Coast handles 65% of waterborne bulk commodity throughput, with the Lower Mississippi River complex (Baton Rouge to Head of Passes) serving as the primary gateway for both import and export bulk flows. Port Houston, New Orleans, and the South Louisiana port complex collectively process over 500 million tons annually.

### 5. Rail Network Consolidation Limits Competition

Seven Class I railroads control 94% of US freight rail revenue. Captive shipper concerns have prompted the Surface Transportation Board to propose reciprocal switching access rules, which could reduce rail rates 5–15% for bulk shippers currently served by a single carrier.

## Report Structure

| Chapter | Title | Focus |
|---|---|---|
| 01 | Executive Overview | This chapter |
| 02 | US Inland Waterway System | Mississippi River System, locks, traffic patterns |
| 03 | Port Infrastructure | Gulf, Atlantic, Pacific bulk terminals |
| 04 | Railroad Network | Class I operations, URCS cost methodology |
| 05 | Intermodal Connectivity | Barge-rail-truck transfer points |
| 06 | US Vessel Fleet | Jones Act, domestic and import fleet profiles |
| 07 | Trade Flow Analysis | Import/export patterns, Panjiva data analysis |
| 08 | Regulatory Environment | Section 301, Jones Act, environmental compliance |
| 09 | Cost Benchmarking | Modal cost comparison framework |
| 10 | Infrastructure Outlook | Investment pipeline, capacity constraints |

## Data Sources and Methodology

All quantitative analysis in this report is produced by the US Bulk Supply Chain Reporting Platform toolsets:

- **Barge Cost Model** — USDA GTR-based rate engine with VAR/SpVAR forecasting (see `02_TOOLSETS/barge_cost_model/METHODOLOGY.md`)
- **Rail Cost Model** — NTAD/NARN network graph with URCS costing (see `02_TOOLSETS/rail_cost_model/METHODOLOGY.md`)
- **Port Cost Model** — Multi-component proforma estimation (see `02_TOOLSETS/port_cost_model/METHODOLOGY.md`)
- **Facility Registry** — EPA FRS with 4M+ facility records in DuckDB (see `02_TOOLSETS/facility_registry/`)
- **Vessel Intelligence** — 7-phase Panjiva classification pipeline (see `02_TOOLSETS/vessel_intelligence/`)
- **Policy Analysis** — Section 301, Jones Act, tariff impact modeling (see `02_TOOLSETS/policy_analysis/`)

Data currency: All statistics are the most recent available as of Q1 2026 unless otherwise noted.

## Implications for Commodity Analysis

This infrastructure assessment provides the commodity-agnostic foundation upon which all commodity modules are built. Each commodity vertical — cement, grain, fertilizer, petroleum, metals — shares the same waterway locks, port berths, rail corridors, and regulatory constraints documented here. The supply chain cost models parameterised in this report are designed to accept commodity-specific inputs (tonnage, density, handling requirements) and return freight cost estimates for any commodity routed through the US bulk supply chain.

---

*Source: US Bulk Supply Chain Reporting Platform v1.0.0 | Data current as of Q1 2026*
