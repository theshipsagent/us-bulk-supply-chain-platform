# Data Dictionary - Pipeline Infrastructure

## Natural Gas Pipeline Data Fields

| Field | Description | Units | Notes |
|-------|-------------|-------|-------|
| Pipeline Name | Official system name | - | May differ from operational name |
| Operator | Current operating company | - | Subject to change via M&A |
| Owner(s) | Ownership structure | - | May differ from operator |
| Diameter | Pipe diameter | inches | Typically 24"-42" for transmission |
| Capacity | Throughput capacity | Bcf/d or MMcf/d | Design capacity, may vary operationally |
| Origin | Starting point/interconnection | - | Basin or supply point |
| Destination | Terminus/delivery points | - | Market area or facility |
| Products | Commodity transported | - | Natural gas, processed gas, etc. |
| Status | Operational status | - | Operating, under construction, proposed, idle |
| FERC Docket | FERC certificate number | - | If interstate transmission |
| Year Built | Construction date | Year | Historical context |
| Proposed ISD | In-service date | Date | For proposed/under construction |

## Crude Oil Pipeline Data Fields

| Field | Description | Units | Notes |
|-------|-------------|-------|-------|
| Pipeline Name | Official name | - | - |
| Operator | Operating company | - | - |
| Diameter | Size | inches | - |
| Capacity | Throughput capacity | BPD (barrels per day) | Design capacity |
| Crude Type | Oil grade | - | Light, medium, heavy, sour/sweet |
| Origin/Destination | Route | - | Supply to demand points |
| Connected Facilities | Terminal infrastructure | - | Refineries, terminals, LOOP |

## Refined Products Pipeline Data Fields

| Field | Description | Units | Notes |
|-------|-------------|-------|-------|
| Pipeline Name | System name | - | - |
| Operator | Operating company | - | - |
| Products | Commodities transported | - | Gasoline, diesel, jet fuel, etc. |
| Capacity | Throughput capacity | BPD | Design capacity |
| Route | Origin to destination | - | Major terminals/delivery points |

## NGL/Petrochemical Pipeline Data Fields

| Field | Description | Units | Notes |
|-------|-------------|-------|-------|
| Pipeline Name | System name | - | - |
| Operator | Operating company | - | - |
| Products | Commodities transported | - | Y-grade, purity NGLs, ethylene, etc. |
| Capacity | Throughput capacity | BPD | Design capacity |
| Key Interconnects | Connected facilities | - | Processing plants, fractionators |

## LNG Facility Data Fields

| Field | Description | Units | Notes |
|-------|-------------|-------|-------|
| Facility Name | Official facility name | - | - |
| Location | Parish/County, State | - | - |
| Capacity | Liquefaction capacity | Bcf/d | Design capacity |
| Operator | Operating company | - | - |
| Owner(s) | Ownership structure | - | May differ from operator |
| Status | Operational status | - | Operating, under construction, proposed |
| Expected ISD | In-service date | Date | For proposed/under construction |
| Feed Pipelines | Connected gas transmission | - | Supply infrastructure |

## Glossary of Terms

- **Bcf/d**: Billion cubic feet per day (natural gas volume)
- **MMcf/d**: Million cubic feet per day (natural gas volume)
- **BPD**: Barrels per day (liquid volume)
- **ISD**: In-service date (project commissioning date)
- **FID**: Final investment decision
- **FERC**: Federal Energy Regulatory Commission
- **EIA**: Energy Information Administration
- **AHP**: Above Head of Passes (Mississippi River mile marker reference)
- **LNG**: Liquefied natural gas
- **NGL**: Natural gas liquids (ethane, propane, butane, etc.)
- **Y-grade**: Mixed natural gas liquids prior to fractionation
- **Haynesville**: Haynesville Shale gas formation (LA/TX)
- **Permian**: Permian Basin (West TX/SE NM)
- **PADD 3**: Petroleum Administration for Defense District 3 (Gulf Coast)
- **LOOP**: Louisiana Offshore Oil Port
- **Transmission**: Long-distance interstate pipeline system
- **Gathering**: Local collection system from wellhead to processing
- **Intrastate**: Pipeline operating within single state
- **Interstate**: Pipeline crossing state boundaries (FERC regulated)

## Data Quality Notes

- Pipeline capacity figures represent design capacity; actual throughput varies
- Operator names current as of 2024; M&A activity ongoing
- FERC docket numbers apply to interstate transmission pipelines only
- Proposed project timelines subject to regulatory approval and market conditions
- Geographic coordinates approximate; use GIS data for precise routing

**Last Updated:** 2026-02-04
