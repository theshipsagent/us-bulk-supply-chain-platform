# FGIS Export Grain — Geography Column Definitions & Record Counts

**Database:** `G:\My Drive\LLM\project_mrtis\fgis\fgis_export_grain.duckdb`
**Total Records:** 580,081

---

## Column 18 — Field Office

FGIS field office that performed the inspection.

| Field Office | Records |
|-------------|---------|
| DIOO | 221,981 |
*| NEW ORLEANS | 83,437 | Miss River 
*| LEAGUE CITY | 46,643 | Houston  
| TOLEDO | 38,054 |
| CEDAR RAPIDS | 37,898 |
| OLYMPIA | 33,317 |
| PORTLAND | 21,175 |
*| LUTCHER | 17,037 | Miss River 
| WICHITA | 13,469 |
| KANSAS CITY | 9,842 |
*| DESTREHAN | 7,645 | Miss River 
*| BELLE CHASSE | 6,467 | Miss River 
| MINNEAPOLIS | 5,332 |
| OMAHA | 3,811 |
| FOSS | 3,776 |
*| PASADENA | 3,445 | Houston (make sure texas not other state)
| PACIFICNW | 3,229 |
| GRAND FORKS | 3,000 |
| BALTIMORE | 2,671 |
*| CORPUS CHRIS | 2,489 | Corpus Christi 
| PLAINVIEW | 2,395 |
| DULUTH | 2,370 |
| MONTREAL | 2,226 |
| STUTTGART | 1,429 |
*| MOBILE | 1,321 |
*| GALVESTON | 1,231 | Houston 
| MOSCOW | 1,129 |
*| LAKE CHARLES | 770 |
*| BEAUMONT | 589 |
| SACRAMENTO | 495 |
| CHICAGO | 410 |
| SEATTLE | 364 |
| PHILADELPHIA | 219 |
| PEORIA | 152 |
| INDIANAPOLIS | 149 |
| SAGINAW | 91 |
| ST. LOUIS | 18 |
| FMMS | 5 |

**Note:** DIOO = Delegated Inspection Offices & Organizations (interior/container inspections performed by state or private agencies under FGIS delegation).

---

## Column 19 — Port

Export port or geographic location where the shipment was inspected for export.

| Port | Records |
|------|---------|
| INTERIOR | 325,332 |
| MISSISSIPPI R. | 111,971 |
| COLUMBIA R. | 43,124 |
| S. ATLANTIC | 26,831 |
| N. TEXAS | 20,842 |
| PUGET SOUND | 13,792 |
| S. TEXAS | 9,123 |
| DULUTH-SUP | 7,764 |
| N. ATLANTIC | 6,865 |
| CALIFORNIA | 4,266 |
| TOLEDO | 3,383 |
| SEAWAY | 2,654 |
| EAST GULF | 2,243 |
| CHICAGO | 1,724 |
| PORT HURON | 82 |
| LAKE SUPERIOR | 49 |
| LAKE ERIE | 24 |
| LAKE ONTARIO | 12 |

**Note:** INTERIOR = inspections at inland origin points (elevators, rail, containers) before shipment to export port. MISSISSIPPI R. = Lower Mississippi River export corridor (New Orleans, Baton Rouge, Destrehan, etc.).

---

## Column 20 — AMS Reg

USDA Agricultural Marketing Service region. Top-level geographic grouping.

| AMS Region | Records | Description |
|-----------|---------|-------------|
| INTERIOR | 325,232 | Inland origin inspections (all states) |
| GULF | 144,169 | Gulf Coast export ports (TX, LA, MS, AL, FL) |
| PACIFIC | 61,182 | Pacific Coast export ports (WA, OR, CA) |
| ATLANTIC | 33,806 | Atlantic Coast export ports (MD, VA, NC, SC, NJ, NY, PA, DE) |
| LAKES | 13,038 | Great Lakes export ports (OH, MI, WI, MN, IL) |
| ST LAWR SWY | 2,654 | St. Lawrence Seaway (Montreal, Canada) |

---

## Column 21 — FGIS Reg

FGIS inspection region. More granular than AMS Reg — splits Gulf into East/West and Coast into East/West.

| FGIS Region | Records | Description |
|------------|---------|-------------|
| INTERIOR | 325,211 | Inland origin inspections |
| EAST GULF | 114,214 | Eastern Gulf ports (LA — Mississippi River corridor, New Orleans, Destrehan, Lutcher, Belle Chasse) |
| WEST COAST | 61,193 | Pacific ports (Columbia R., Puget Sound, California) |
| EAST COAST | 33,806 | Atlantic ports (Baltimore, Norfolk, Savannah, Charleston, etc.) |
| WEST GULF | 29,965 | Western Gulf ports (TX — Houston, Galveston, Corpus Christi, Beaumont) |
| LAKES | 13,038 | Great Lakes ports (Toledo, Duluth-Superior, Chicago) |
| CANADA | 2,654 | St. Lawrence Seaway / Montreal |

---

## Column 22 — City

City of inspection. **This column is entirely NULL across all 580,081 records.** Not populated in the export grain dataset.

---

## Column 23 — State

U.S. state where inspection occurred (2-letter abbreviation). Populated primarily for INTERIOR shipments (container, rail, truck inspections at origin).

| State | Records |
|-------|---------|
| IL | 130,737 |
| TX | 32,796 |
| KS | 30,662 |
| OH | 28,693 |
| NE | 21,685 |
| IA | 14,979 |
| MO | 11,167 |
| WI | 9,785 |
| ND | 9,568 |
| NJ | 4,546 |
| VA | 3,478 |
| OK | 3,406 |
| MN | 3,143 |
| NC | 3,072 |
| IN | 2,901 |
| MI | 2,825 |
| SC | 1,874 |
| MD | 1,836 |
| ID | 1,656 |
| TN | 1,305 |
| LA | 1,290 |
| SD | 856 |
| PA | 754 |
| CA | 628 |
| MT | 438 |
| UT | 417 |
| CO | 314 |
| DE | 166 |
| AR | 166 |
| MS | 63 |
| NY | 52 |
| LS | 21 |
| KY | 16 |
| AZ | 15 |
| GA | 15 |
| WA | 5 |
| OR | 2 |

**Note:** State is NULL for most port-based (non-INTERIOR) inspections. 37 distinct states represented. "LS" appears to be a data entry error (likely LA).

---

## Column 16 — Destination (bonus — included for reference)

Export destination country.

| Destination | Records |
|------------|---------|
| MEXICO | 125,724 |
| TAIWAN | 98,279 |
| INDONESIA | 56,880 |
| JAPAN | 51,329 |
| CHINA | 38,098 |
| VIETNAM | 23,294 |
| KOREA REP | 21,539 |
| MALAYSIA | 18,752 |
| THAILAND | 17,845 |
| PHILIPPINES | 11,205 |
| COLOMBIA | 7,719 |
| CANADA | 5,893 |
| EGYPT | 5,729 |
| VENEZUELA | 5,256 |
| DOMINICN REP | 4,218 |
| HONG KONG | 4,205 |
| NIGERIA | 4,182 |
| NETHERLANDS | 3,920 |
| USSR | 3,839 |
| COSTA RICA | 3,409 |
| HONDURAS | 3,201 |
| ALGERIA | 2,891 |
| SPAIN | 2,756 |
| ITALY | 2,708 |
| ISRAEL | 2,704 |
| GUATEMALA | 2,673 |
| JAMAICA | 2,671 |
| EL SALVADOR | 2,364 |
| PERU | 2,325 |
| MOROCCO | 2,032 |

*Top 30 shown. Country codes per U.S. Census Bureau Schedule C.*
