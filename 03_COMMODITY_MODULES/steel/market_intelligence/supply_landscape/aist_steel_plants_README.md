# AIST 2021 Directory — Steel Plants Geospatial Database

## Source Data

Parsed from the **AIST 2021 Directory of Iron and Steel Plants** ("the Black Book") free facility tables:

| Table | PDF | Records Parsed |
|-------|-----|----------------|
| Hot Strip Mills | 2021-Hot-Strip-Mills.pdf | All US/CA flat-rolled HSMs |
| Plate Mills | 2021-Plate-Mills.pdf | All US/CA plate mills |
| Galvanizing Lines | 2021-Galvanizing-Lines.pdf | All US/CA/MX galv lines |
| Electric Arc Furnaces | 2021-Electric-Arc-Furnaces.pdf | Flat-rolled-relevant EAFs |

**Note:** 2021 data vintage. Ownership and operational status updated with notes where significant changes occurred (Cleveland-Cliffs/ArcelorMittal acquisition, Big River Steel 2 startup, Nucor West Virginia greenfield, etc.)

## Database Summary

| Metric | Value |
|--------|-------|
| Total facilities | 68 |
| United States | 65 |
| Canada | 3 |
| Hot strip mill capacity | 87,180 kt/year (31 mills) |
| Galvanizing capacity | 26,052 kt/year (65 lines at 44 sites) |
| EAF capacity (flat-rolled) | 37,846 kt/year (25 facilities) |
| Plate mill capacity | 17,750 kt/year (12 mills) |
| Port-adjacent facilities | 14 |
| Water access | 30 |
| Barge access | 9 |

## Top Companies by HSM Capacity (US)

| Company | HSM Capacity (kt) | Key Plants |
|---------|--------------------|------------|
| United States Steel | 21,600 | Gary IN, Granite City IL, Big River AR (x2), Mon Valley PA, Great Lakes MI |
| Cleveland-Cliffs | 19,400 | Burns Harbor IN, Cleveland OH, Indiana Harbor IN, Middletown OH, Riverdale IL |
| Nucor Corporation | 13,300 | Arkansas, Berkeley SC, Decatur AL, Gallatin KY, Indiana, WV (greenfield) |
| Steel Dynamics Inc. | 8,800 | Butler IN, Columbus MS, Sinton TX |
| AM/NS Calvert | 5,400 | Calvert AL |
| NLMK USA | 2,800 | Indiana (Portage), Pennsylvania (Farrell) |
| JSW Steel USA | 2,800 | Mingo Junction OH |

## Output Files

| File | Format | Description |
|------|--------|-------------|
| `aist_steel_plants.geojson` | GeoJSON | Point features for all 68 facilities, full properties |
| `aist_steel_plants.csv` | CSV | Flat table, pipe-delimited facility types |
| `aist_steel_plants_geospatial.py` | Python | Source module with dataclasses, enums, export functions |

## Field Definitions

### Core Fields
- **name** — Plant/facility name
- **company** — Current operating company
- **city/state/country** — Location
- **lat/lon** — WGS84 coordinates (geocoded)
- **facility_types** — Pipe-delimited list of facility types present

### Hot Strip Mill Fields
- **hsm_finishing_stands** — Number of finishing stands
- **hsm_min/max_thickness_mm** — Gauge range capability
- **hsm_max_width_mm** — Maximum strip width
- **hsm_mill_builder** — Original equipment manufacturer
- **hsm_startup_year** — Year commissioned (or last major modernization)

### Galvanizing Fields
- **galv_num_lines** — Number of galvanizing lines at facility
- **galv_coating_types** — GI (galvanized), GA (galvanneal), AZ (Galvalume), AL (aluminized), EG (electrogalvanized), GF (galvanized-free)
- **galv_total_capacity_kt** — Combined capacity of all lines
- **galv_max_width_mm** — Widest line capability

### Plate Mill Fields
- **plate_min/max_thickness_mm** — Gauge range
- **plate_max_width_mm** — Maximum width capability
- **plate_discrete_or_coil** — Output format

### EAF Fields
- **eaf_num_furnaces** — Number of electric arc furnaces
- **eaf_heat_size_mt** — Heat size in metric tons
- **eaf_transformer_mva** — Transformer capacity (MVA)
- **eaf_capacity_kt** — Stated EAF capacity

### Logistics Fields
- **port_adjacent** — Within 5 miles of an ocean/Great Lakes port
- **water_access** — On navigable waterway
- **barge_access** — Accessible by inland barge (river/ICW)
- **rail_served** — Rail-served (virtually all mills)

## Integration Notes for Claude Code

This dataset is designed to integrate with:

1. **Panjiva import records** — Match HS 7208-7212 consignees to mill/galv locations
2. **Service center database** — From the prior end-user mapping session (53 facilities)
3. **MCN Top 50 directory** — When subscription data is available
4. **USGS Mineral Commodity data** — Steel production/consumption statistics
5. **EPA FRS registry** — Environmental compliance data by facility

### Key Relationships
```
Import vessel → Port → [Service Center OR Toll Processor] → End User
                  ↓
            Domestic Mill → [Service Center OR Direct] → End User
```

The domestic mill data in this dataset maps the "Domestic Mill" node. Combined with the service center/end-user data from the prior session, this gives complete coverage of the US flat-rolled steel value chain from production through consumption.
