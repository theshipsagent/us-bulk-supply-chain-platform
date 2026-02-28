#!/usr/bin/env python3
"""
US & North American Aluminum Facilities Geospatial Database
=============================================================
Consumers of unwrought aluminum: ingots, sows, T-bars, billets, rolling slab

Data Sources:
  - USGS Mineral Commodity Summaries 2024-2025 (Aluminum)
  - The Aluminum Association member directories & white papers
  - Aluminum Extruders Council (AEC) Buyers' Guide references
  - Recycling Today Secondary Aluminum Producers directory (2015)
  - Light Metal Age facility reports (2016-2025)
  - Company websites, SEC filings, press releases
  - CRS Report R47294: U.S. Aluminum Manufacturing
  - EPI Section 232 aluminum report (2021)

Coordinate System: WGS84 (EPSG:4326)
Data Vintage: Current as of February 2026
Capacity Units: kt/year (thousand metric tons per year)

Facility Categories:
  PRIMARY_SMELTER    - Electrolytic reduction of alumina to primary aluminum
  ROLLING_MILL       - Hot/cold rolling of slab to sheet, plate, foil
  SECONDARY_SMELTER  - Remelt/recycle scrap into alloy ingot or billet
  BILLET_CASTER      - Remelt scrap/prime into extrusion billet & forging stock
  INTEGRATED_MILL    - Combined secondary smelting + rolling (e.g. Novelis, Constellium)

Author: Built for William Davis III supply chain analysis
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional
import json
import csv
import io


class FacilityType(str, Enum):
    PRIMARY_SMELTER = "primary_smelter"
    ROLLING_MILL = "rolling_mill"
    SECONDARY_SMELTER = "secondary_smelter"
    BILLET_CASTER = "billet_caster"
    INTEGRATED_MILL = "integrated_mill"


class Country(str, Enum):
    US = "US"
    CA = "Canada"
    MX = "Mexico"


@dataclass
class AluminumFacility:
    """Single aluminum production/processing facility."""
    name: str
    company: str
    facility_types: list  # list of FacilityType values
    city: str
    state: str
    country: Country
    lat: float
    lon: float

    # Capacity
    capacity_kt: Optional[float] = None  # total annual capacity kt/year
    capacity_notes: str = ""

    # Products & Markets
    products: str = ""  # sheet, plate, can_stock, auto_body_sheet, billet, ingot, slab, foil
    markets: str = ""   # packaging, automotive, aerospace, construction, industrial, defense
    alloys: str = ""    # 1xxx, 3xxx, 5xxx, 6xxx, 7xxx series

    # Technical
    has_hot_mill: bool = False
    has_cold_mill: bool = False
    has_casthouse: bool = False
    has_recycling: bool = False
    num_potlines: Optional[int] = None  # primary smelters only
    num_presses: Optional[int] = None   # extrusion capability

    # Logistics
    port_adjacent: bool = False
    water_access: bool = False
    barge_access: bool = False
    rail_served: bool = True  # most are

    # Status
    status: str = "operating"  # operating, reduced, idled, construction, planned, closed
    startup_year: Optional[int] = None
    employees: Optional[int] = None
    notes: str = ""


# =============================================================================
# PRIMARY SMELTERS (electrolytic aluminum production)
# =============================================================================

PRIMARY_SMELTERS = [
    # ── CENTURY ALUMINUM ──
    AluminumFacility(
        name="Century Sebree Smelter",
        company="Century Aluminum",
        facility_types=[FacilityType.PRIMARY_SMELTER],
        city="Sebree", state="KY", country=Country.US,
        lat=37.6061, lon=-87.5286,
        capacity_kt=220, capacity_notes="Full capacity; 100% owned",
        products="primary ingot, T-bar, sow",
        markets="industrial, automotive, packaging",
        alloys="P1020 (99.7% purity)",
        has_casthouse=True, num_potlines=3,
        barge_access=True, water_access=True,
        status="operating", startup_year=1973, employees=600,
        notes="Largest operating US smelter. Ohio River barge access. Owned by Century since 2003."
    ),
    AluminumFacility(
        name="Century Mt. Holly Smelter",
        company="Century Aluminum",
        facility_types=[FacilityType.PRIMARY_SMELTER],
        city="Goose Creek", state="SC", country=Country.US,
        lat=32.9810, lon=-80.0326,
        capacity_kt=229, capacity_notes="Nameplate 229kt; operating at ~75% (172kt in 2023); $50M restart to full capacity by June 2026",
        products="high-purity ingot, T-bar",
        markets="aerospace, defense, electrical",
        alloys="99.9% high-purity aluminum",
        has_casthouse=True, num_potlines=2,
        port_adjacent=True, water_access=True,
        status="reduced", startup_year=1980, employees=465,
        notes="Only US smelter producing high-purity (99.9%) aluminum for military/aerospace. 2 potlines, 360 cells, Alcoa A697 tech at 228kA. Santee Cooper 3yr power contract through 2026. Century announced $50M to restore full capacity by mid-2026."
    ),
    AluminumFacility(
        name="Century Hawesville Smelter",
        company="Century Aluminum",
        facility_types=[FacilityType.PRIMARY_SMELTER],
        city="Hawesville", state="KY", country=Country.US,
        lat=37.9000, lon=-86.7553,
        capacity_kt=252, capacity_notes="Nameplate 252kt; temporarily shut down since 2022",
        products="primary ingot",
        markets="industrial",
        alloys="P1020",
        has_casthouse=True, num_potlines=5,
        barge_access=True, water_access=True,
        status="idled", startup_year=1969, employees=0,
        notes="5 potlines, 560 cells, Kaiser P69 tech at 170kA. Ohio River adjacent. Idled since 2022 due to high power costs. Restart depends on competitive long-term energy contract."
    ),

    # ── ALCOA ──
    AluminumFacility(
        name="Alcoa Warrick Smelter",
        company="Alcoa Corporation",
        facility_types=[FacilityType.PRIMARY_SMELTER],
        city="Newburgh", state="IN", country=Country.US,
        lat=37.9447, lon=-87.4053,
        capacity_kt=269, capacity_notes="3 operating potlines; up to 156kt actual production",
        products="primary ingot, molten metal (to adjacent Kaiser rolling mill)",
        markets="packaging, industrial",
        alloys="P1020",
        has_casthouse=True, num_potlines=3,
        water_access=True,
        status="operating", startup_year=1960, employees=600,
        notes="Co-located with Kaiser Warrick rolling mill (sold to Kaiser 2021). Alcoa retained smelter + 800MW coal power plant. 3 potlines of 150 pots each. Supplies molten metal directly to Kaiser casthouse."
    ),
    AluminumFacility(
        name="Alcoa Massena Smelter",
        company="Alcoa Corporation",
        facility_types=[FacilityType.PRIMARY_SMELTER],
        city="Massena", state="NY", country=Country.US,
        lat=44.9281, lon=-74.8916,
        capacity_kt=130, capacity_notes="Reduced capacity operations",
        products="primary ingot, billet",
        markets="industrial, aerospace",
        alloys="P1020, specialty alloys",
        has_casthouse=True, num_potlines=2,
        water_access=True,
        status="reduced", startup_year=1903, employees=400,
        notes="Oldest continuously operating aluminum smelter site in US. St. Lawrence River hydropower. Massena East plant uses older Söderberg technology. 3yr labor agreement ratified 2023."
    ),

    # ── MAGNITUDE 7 METALS ──
    AluminumFacility(
        name="Magnitude 7 New Madrid Smelter",
        company="Magnitude 7 Metals",
        facility_types=[FacilityType.PRIMARY_SMELTER],
        city="New Madrid", state="MO", country=Country.US,
        lat=36.5864, lon=-89.5279,
        capacity_kt=263, capacity_notes="Nameplate 263kt; fully shut down Jan 2024",
        products="primary ingot",
        markets="industrial",
        alloys="P1020",
        has_casthouse=True, num_potlines=3,
        barge_access=True, water_access=True,
        status="idled", startup_year=1971, employees=0,
        notes="Mississippi River barge access. Originally Noranda, acquired by ARG International 2016. Full shutdown Jan 2024 with no scheduled restart. Previously produced ~250kt/yr."
    ),

    # ── PLANNED NEW SMELTERS ──
    AluminumFacility(
        name="Century Green Aluminum Smelter",
        company="Century Aluminum",
        facility_types=[FacilityType.PRIMARY_SMELTER],
        city="Inola", state="OK", country=Country.US,
        lat=36.1518, lon=-95.5096,
        capacity_kt=500, capacity_notes="Planned 500kt/yr; $5B investment; DOE $500M grant",
        products="primary ingot",
        markets="industrial, defense, packaging",
        alloys="P1020, high-purity",
        has_casthouse=True,
        status="planned", startup_year=2031,
        notes="First new US smelter in ~45 years. DOE Office of Clean Energy Demonstrations $500M grant. 100% renewable/nuclear power target. 75% less carbon-intensive. Site selection Feb 2026 (Inola, OK). 5-6yr build timeline."
    ),
]


# =============================================================================
# FLAT-ROLLED MILLS (rolling slab/ingot → sheet, plate, coil, foil)
# =============================================================================

ROLLING_MILLS = [
    # ── NOVELIS ──
    AluminumFacility(
        name="Novelis Oswego",
        company="Novelis (Hindalco)",
        facility_types=[FacilityType.INTEGRATED_MILL],
        city="Oswego", state="NY", country=Country.US,
        lat=43.4553, lon=-76.5105,
        capacity_kt=360, capacity_notes="Largest Novelis NA plant; ~360kt/yr; hot mill fire Sep 2025, restarted Dec 2025",
        products="can stock, auto body sheet, industrial sheet",
        markets="packaging, automotive, industrial",
        alloys="3xxx, 5xxx, 6xxx",
        has_hot_mill=True, has_cold_mill=True, has_casthouse=True, has_recycling=True,
        water_access=True, port_adjacent=True,
        status="operating", startup_year=1963, employees=1100,
        notes="Novelis's largest wholly-owned NA fabrication facility. Full scrap remelting/recycling, ingot casting, hot and cold rolling, finishing. Major fire Sep 2025 damaged hot mill; restarted Dec 2025. Lake Ontario water access."
    ),
    AluminumFacility(
        name="Novelis Bay Minette",
        company="Novelis (Hindalco)",
        facility_types=[FacilityType.INTEGRATED_MILL],
        city="Bay Minette", state="AL", country=Country.US,
        lat=30.8830, lon=-87.7741,
        capacity_kt=600, capacity_notes="Initial 600kt finished goods; expandable to 1,000kt (Danieli 1+4 HSM)",
        products="can stock, auto body sheet",
        markets="packaging, automotive",
        alloys="3xxx, 5xxx, 6xxx",
        has_hot_mill=True, has_cold_mill=True, has_casthouse=True, has_recycling=True,
        rail_served=True,
        status="construction", startup_year=2026, employees=1000,
        notes="$2.5B investment. First fully integrated aluminum mill built in US in 40+ years. South Alabama Mega Site at I-65/Hwy 287. 51km from Port of Mobile. Danieli 1+4 HSM. Commissioning H2 2026. UBC recycling center adds 15B cans/yr capacity. Railroad-served for low-carbon logistics."
    ),
    AluminumFacility(
        name="Novelis Terre Haute (Logan Aluminum)",
        company="Novelis (Hindalco) / Tri-Arrows JV",
        facility_types=[FacilityType.INTEGRATED_MILL],
        city="Russellville", state="KY", country=Country.US,
        lat=36.8453, lon=-86.8872,
        capacity_kt=400, capacity_notes="~400kt can stock",
        products="can stock (body, end, tab)",
        markets="packaging",
        alloys="3xxx, 5xxx",
        has_hot_mill=True, has_cold_mill=True, has_casthouse=True, has_recycling=True,
        status="operating", startup_year=1985,
        notes="Logan Aluminum joint venture. Major can stock producer supplying Ball, Crown, Ardagh. Large UBC recycling operation."
    ),
    AluminumFacility(
        name="Novelis Berea",
        company="Novelis (Hindalco)",
        facility_types=[FacilityType.ROLLING_MILL],
        city="Berea", state="KY", country=Country.US,
        lat=37.5687, lon=-84.2963,
        capacity_kt=100, capacity_notes="Cold mill and finishing",
        products="auto body sheet, industrial sheet",
        markets="automotive, industrial",
        alloys="5xxx, 6xxx",
        has_cold_mill=True,
        status="operating",
        notes="Cold rolling and finishing operations. Automotive sheet focus."
    ),
    AluminumFacility(
        name="Novelis Greensboro",
        company="Novelis (Hindalco)",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Greensboro", state="GA", country=Country.US,
        lat=33.5726, lon=-83.2793,
        capacity_kt=80, capacity_notes="Recycling and casting",
        products="recycled ingot, UBC processing",
        markets="packaging",
        has_casthouse=True, has_recycling=True,
        status="operating",
        notes="Aluminum recycling facility. $36M expansion 2019. UBC processing for can stock supply chain."
    ),
    AluminumFacility(
        name="Novelis Guthrie (formerly Aleris)",
        company="Novelis (Hindalco)",
        facility_types=[FacilityType.ROLLING_MILL],
        city="Guthrie", state="KY", country=Country.US,
        lat=36.6486, lon=-86.8872,
        capacity_kt=100,
        products="auto body sheet",
        markets="automotive",
        alloys="5xxx, 6xxx",
        has_cold_mill=True,
        status="operating",
        notes="Acquired via Aleris acquisition 2020. Automotive sheet finishing. $500M+ expansion ongoing."
    ),

    # ── ARCONIC ──
    AluminumFacility(
        name="Arconic Davenport Works",
        company="Arconic Corporation",
        facility_types=[FacilityType.INTEGRATED_MILL],
        city="Bettendorf", state="IA", country=Country.US,
        lat=41.5379, lon=-90.4654,
        capacity_kt=500, capacity_notes="One of world's largest aluminum rolling mills",
        products="sheet, plate, coil",
        markets="aerospace, automotive, industrial",
        alloys="2xxx, 5xxx, 6xxx, 7xxx",
        has_hot_mill=True, has_cold_mill=True, has_casthouse=True,
        water_access=True, barge_access=True,
        status="operating", startup_year=1948, employees=2400,
        notes="Flagship Arconic rolling mill. Mississippi River barge access. Produces aerospace plate (2xxx, 7xxx), automotive sheet, and industrial products. One of the largest aluminum rolling complexes in the world."
    ),
    AluminumFacility(
        name="Arconic Tennessee Operations",
        company="Arconic Corporation",
        facility_types=[FacilityType.INTEGRATED_MILL],
        city="Alcoa", state="TN", country=Country.US,
        lat=35.7898, lon=-83.9738,
        capacity_kt=750, capacity_notes="~750kt hot+cold rolled products",
        products="sheet, coil",
        markets="automotive, industrial, commercial transportation",
        alloys="3xxx, 5xxx, 6xxx",
        has_hot_mill=True, has_cold_mill=True, has_casthouse=True, has_recycling=True,
        status="operating", startup_year=1919, employees=1500,
        notes="Originally Alcoa's historic Tennessee Works. Now Arconic rolled products. Major automotive sheet producer. $100M+ hot mill expansion completed ~2020. City of Alcoa named after the company."
    ),
    AluminumFacility(
        name="Arconic Lancaster",
        company="Arconic Corporation",
        facility_types=[FacilityType.ROLLING_MILL],
        city="Lancaster", state="PA", country=Country.US,
        lat=40.0614, lon=-76.3114,
        capacity_kt=150,
        products="sheet, plate",
        markets="aerospace, industrial, building products",
        alloys="2xxx, 5xxx, 6xxx, 7xxx",
        has_cold_mill=True,
        status="operating",
        notes="Cold rolling, finishing, and heat treatment for aerospace and industrial applications."
    ),
    AluminumFacility(
        name="Arconic Danville",
        company="Arconic Corporation",
        facility_types=[FacilityType.ROLLING_MILL],
        city="Danville", state="IL", country=Country.US,
        lat=40.1245, lon=-87.6300,
        capacity_kt=100,
        products="sheet, plate",
        markets="aerospace, industrial",
        has_cold_mill=True,
        status="operating",
        notes="Cold rolling and finishing operations."
    ),
    AluminumFacility(
        name="Arconic Hutchinson Aerospace Center",
        company="Arconic Corporation",
        facility_types=[FacilityType.ROLLING_MILL],
        city="Hutchinson", state="KS", country=Country.US,
        lat=38.0834, lon=-97.8915,
        capacity_kt=50,
        products="aerospace plate, sheet",
        markets="aerospace, defense",
        alloys="2xxx, 7xxx",
        status="operating",
        notes="Aerospace-focused plate and sheet finishing center."
    ),

    # ── CONSTELLIUM ──
    AluminumFacility(
        name="Constellium Muscle Shoals",
        company="Constellium SE",
        facility_types=[FacilityType.INTEGRATED_MILL],
        city="Muscle Shoals", state="AL", country=Country.US,
        lat=34.7462, lon=-87.6675,
        capacity_kt=450, capacity_notes=">1B lbs/yr finished coils; widest strip mill in US; 340kt recycling capacity",
        products="can stock (body, end, tab), auto body sheet",
        markets="packaging, automotive",
        alloys="3xxx, 5xxx, 6xxx",
        has_hot_mill=True, has_cold_mill=True, has_casthouse=True, has_recycling=True,
        status="operating", employees=1250,
        notes="100+ acres under roof. 5 casting units. Widest strip mill in US. Element 13 recycling center processes 20B+ cans/yr. DoD $23M DPA grant for new DC casting center adding 136kt (300M lbs) annual casting capacity. $65M total expansion. Formerly Wise Metals/Wise Alloys."
    ),
    AluminumFacility(
        name="Constellium Ravenswood",
        company="Constellium SE",
        facility_types=[FacilityType.INTEGRATED_MILL],
        city="Ravenswood", state="WV", country=Country.US,
        lat=38.9487, lon=-81.7610,
        capacity_kt=200, capacity_notes="Major plate facility",
        products="plate, sheet, coil",
        markets="aerospace, defense, transportation, marine",
        alloys="2xxx, 5xxx, 6xxx, 7xxx",
        has_hot_mill=True, has_cold_mill=True, has_casthouse=True,
        water_access=True, barge_access=True,
        status="operating", employees=1000,
        notes="One of world's largest rolled products facilities. World's most powerful plate stretchers. Ohio River barge access. DOE $75M grant for low/zero-carbon casthouse using clean hydrogen. Major defense/aerospace plate supplier."
    ),
    AluminumFacility(
        name="Constellium Bowling Green",
        company="Constellium SE",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Bowling Green", state="KY", country=Country.US,
        lat=36.9685, lon=-86.4808,
        capacity_kt=50,
        products="automotive structural parts, crash management systems",
        markets="automotive",
        alloys="6xxx",
        has_casthouse=True,
        status="operating",
        notes="Automotive Structures & Industry division. Produces structural parts and crash management systems for OEMs."
    ),

    # ── KAISER ALUMINUM ──
    AluminumFacility(
        name="Kaiser Warrick Rolling Mill",
        company="Kaiser Aluminum",
        facility_types=[FacilityType.INTEGRATED_MILL],
        city="Newburgh", state="IN", country=Country.US,
        lat=37.9440, lon=-87.4060,
        capacity_kt=300, capacity_notes="Cast house, hot mill, cold mills, finishing/coating lines, slitters",
        products="can stock, food packaging coil",
        markets="packaging (beverage, food)",
        alloys="3xxx, 5xxx",
        has_hot_mill=True, has_cold_mill=True, has_casthouse=True,
        water_access=True,
        status="operating", startup_year=1960,
        notes="Acquired from Alcoa 2021. Co-located with Alcoa smelter which supplies molten metal. $150M roll coating line addition (operational 2024). Major can stock producer."
    ),
    AluminumFacility(
        name="Kaiser Trentwood Rolling Mill",
        company="Kaiser Aluminum",
        facility_types=[FacilityType.ROLLING_MILL],
        city="Spokane Valley", state="WA", country=Country.US,
        lat=47.6588, lon=-117.3531,
        capacity_kt=200, capacity_notes="Plate and sheet for aerospace/general engineering",
        products="plate, sheet, strip, coil",
        markets="aerospace, defense, general engineering",
        alloys="2xxx, 5xxx, 6xxx, 7xxx",
        has_hot_mill=True, has_cold_mill=True, has_casthouse=True,
        status="operating", startup_year=1942,
        notes="Historic Kaiser aluminum plant. Major aerospace plate producer including KaiserSelect AA7099. Originally government war plant, purchased by Kaiser 1946."
    ),

    # ── JW ALUMINUM ──
    AluminumFacility(
        name="JW Aluminum Russellville",
        company="JW Aluminum",
        facility_types=[FacilityType.ROLLING_MILL],
        city="Russellville", state="AR", country=Country.US,
        lat=35.2784, lon=-93.1338,
        capacity_kt=100,
        products="sheet, coil, foil stock",
        markets="building products, HVAC, industrial",
        alloys="1xxx, 3xxx",
        has_cold_mill=True, has_casthouse=True,
        status="operating",
        notes="Continuous cast and cold rolling. Building products focus."
    ),
    AluminumFacility(
        name="JW Aluminum Mount Holly",
        company="JW Aluminum",
        facility_types=[FacilityType.ROLLING_MILL],
        city="Mount Holly", state="SC", country=Country.US,
        lat=35.2982, lon=-81.0159,
        capacity_kt=80,
        products="sheet, coil",
        markets="building products, industrial",
        alloys="1xxx, 3xxx",
        has_cold_mill=True, has_casthouse=True,
        status="operating",
        notes="Continuous cast sheet production for building products."
    ),
    AluminumFacility(
        name="JW Aluminum St. Louis",
        company="JW Aluminum",
        facility_types=[FacilityType.ROLLING_MILL],
        city="St. Louis", state="MO", country=Country.US,
        lat=38.6270, lon=-90.1994,
        capacity_kt=60,
        products="foil, sheet",
        markets="packaging, industrial",
        alloys="1xxx, 8xxx",
        has_cold_mill=True,
        status="operating",
        notes="Foil and light-gauge sheet production."
    ),

    # ── GOLDEN ALUMINUM ──
    AluminumFacility(
        name="Golden Aluminum",
        company="Golden Aluminum Inc.",
        facility_types=[FacilityType.INTEGRATED_MILL],
        city="Fort Lupton", state="CO", country=Country.US,
        lat=40.0847, lon=-104.8133,
        capacity_kt=120,
        products="can stock, sheet",
        markets="packaging",
        alloys="3xxx, 5xxx",
        has_hot_mill=True, has_cold_mill=True, has_casthouse=True, has_recycling=True,
        status="operating",
        notes="Continuous cast can stock producer. DOE $22.3M grant to upgrade casting and rolling equipment. Scrap-based production."
    ),

    # ── GRANGES ──
    AluminumFacility(
        name="Granges Huntingdon",
        company="Granges AB",
        facility_types=[FacilityType.ROLLING_MILL],
        city="Huntingdon", state="TN", country=Country.US,
        lat=36.0006, lon=-88.4284,
        capacity_kt=80,
        products="clad sheet, brazing sheet, fin stock",
        markets="HVAC, automotive heat exchangers",
        alloys="1xxx, 3xxx, 4xxx",
        has_cold_mill=True, has_casthouse=True,
        status="operating",
        notes="Formerly Noranda rolled products. Acquired by Granges 2016. Specialty clad/brazing sheet for heat exchangers."
    ),
    AluminumFacility(
        name="Granges Newport",
        company="Granges AB",
        facility_types=[FacilityType.ROLLING_MILL],
        city="Newport", state="AR", country=Country.US,
        lat=35.6048, lon=-91.2168,
        capacity_kt=50,
        products="fin stock, clad sheet",
        markets="HVAC, automotive",
        alloys="1xxx, 3xxx",
        has_cold_mill=True,
        status="operating",
        notes="Formerly Noranda. Thin-gauge rolling for HVAC applications."
    ),
    AluminumFacility(
        name="Granges Salisbury",
        company="Granges AB",
        facility_types=[FacilityType.ROLLING_MILL],
        city="Salisbury", state="NC", country=Country.US,
        lat=35.6710, lon=-80.4742,
        capacity_kt=60,
        products="sheet, strip",
        markets="HVAC, industrial",
        alloys="1xxx, 3xxx",
        has_cold_mill=True,
        status="operating",
        notes="Formerly Noranda. Strip and sheet products."
    ),

    # ── TRI-ARROWS ALUMINUM ──
    AluminumFacility(
        name="Tri-Arrows Aluminum Louisville",
        company="Tri-Arrows Aluminum Inc.",
        facility_types=[FacilityType.INTEGRATED_MILL],
        city="Louisville", state="KY", country=Country.US,
        lat=38.2527, lon=-85.7585,
        capacity_kt=300, capacity_notes="Major can stock producer",
        products="can stock (body, end, tab)",
        markets="packaging",
        alloys="3xxx, 5xxx",
        has_hot_mill=True, has_cold_mill=True, has_casthouse=True, has_recycling=True,
        water_access=True, barge_access=True,
        status="operating",
        notes="Formerly ARCO Aluminum/IMCO Recycling. JV of Japanese interests. Ohio River barge access. Major UBC recycling and can stock production."
    ),

    # ── ALUMINUM DYNAMICS (SDI) ──
    AluminumFacility(
        name="Aluminum Dynamics Columbus",
        company="Aluminum Dynamics LLC (Steel Dynamics)",
        facility_types=[FacilityType.INTEGRATED_MILL],
        city="Columbus", state="MS", country=Country.US,
        lat=33.4957, lon=-88.4273,
        capacity_kt=650, capacity_notes="650kt finished products; SMS 1+4 HSM; $1.9B+ investment",
        products="can stock, auto body sheet, common alloy sheet",
        markets="packaging, automotive, industrial",
        alloys="3xxx, 5xxx, 6xxx",
        has_hot_mill=True, has_cold_mill=True, has_casthouse=True, has_recycling=True,
        barge_access=True, water_access=True,
        status="construction", startup_year=2025, employees=700,
        notes="SDI's first aluminum mill. $1.9B+. Adjacent to SDI Columbus steel mill. SMS 1+4 hot strip mill, 2 tandem cold mills, CASH lines, coating. Tenn-Tom Waterway barge access. Class I railroad. 2 satellite UBC recycling/casting facilities (AZ and San Luis Potosi MX). Construction started Jul 2023; operations mid-2025."
    ),

    # ── ALERIS (now Novelis) ──
    AluminumFacility(
        name="Novelis Lewisport (formerly Aleris)",
        company="American Industrial Partners",
        facility_types=[FacilityType.ROLLING_MILL],
        city="Lewisport", state="KY", country=Country.US,
        lat=37.9369, lon=-86.9021,
        capacity_kt=120,
        products="auto body sheet",
        markets="automotive",
        alloys="5xxx, 6xxx",
        has_cold_mill=True, has_casthouse=True,
        barge_access=True, water_access=True,
        status="operating",
        notes="Formerly Aleris, acquired by Novelis 2020, then divested to American Industrial Partners per DOJ requirement. Ohio River access. Automotive body sheet."
    ),
    AluminumFacility(
        name="Aleris Uhrichsville",
        company="Novelis (Hindalco)",
        facility_types=[FacilityType.ROLLING_MILL],
        city="Uhrichsville", state="OH", country=Country.US,
        lat=40.3903, lon=-81.3468,
        capacity_kt=80,
        products="sheet, plate",
        markets="industrial, building products",
        alloys="3xxx, 5xxx",
        has_cold_mill=True, has_casthouse=True,
        status="operating",
        notes="Continuous cast sheet producer. Industrial and building product focus."
    ),
    AluminumFacility(
        name="Aleris Richmond",
        company="Novelis (Hindalco)",
        facility_types=[FacilityType.ROLLING_MILL],
        city="Richmond", state="VA", country=Country.US,
        lat=37.5407, lon=-77.4360,
        capacity_kt=50,
        products="sheet",
        markets="building products, industrial",
        has_cold_mill=True,
        status="operating",
        notes="Formerly Aleris rolled products. Sheet finishing."
    ),

    # ── COMMONWEALTH ROLLED PRODUCTS ──
    AluminumFacility(
        name="Commonwealth Rolled Products Lewisport",
        company="Commonwealth Rolled Products (Lexington, KY)",
        facility_types=[FacilityType.ROLLING_MILL],
        city="Lewisport", state="KY", country=Country.US,
        lat=37.9380, lon=-86.9000,
        capacity_kt=100,
        products="can stock, sheet",
        markets="packaging, industrial",
        alloys="3xxx, 5xxx",
        has_hot_mill=True, has_cold_mill=True, has_casthouse=True,
        barge_access=True, water_access=True,
        status="operating",
        notes="Ohio River access. Can stock and common alloy sheet production."
    ),
]


# =============================================================================
# SECONDARY SMELTERS & BILLET CASTERS
# =============================================================================

SECONDARY_FACILITIES = [
    # ── MATALCO (Giampaolo Group / Rio Tinto JV) ──
    AluminumFacility(
        name="Matalco Lordstown",
        company="Matalco Inc. (Giampaolo/Rio Tinto JV)",
        facility_types=[FacilityType.BILLET_CASTER],
        city="Lordstown", state="OH", country=Country.US,
        lat=41.1658, lon=-80.8673,
        capacity_kt=159, capacity_notes="350M lbs/yr; largest Matalco plant",
        products="extrusion billet, forging stock",
        markets="construction, automotive, industrial",
        alloys="6xxx, 7xxx",
        has_casthouse=True, has_recycling=True,
        status="operating", startup_year=2016,
        notes="North America's largest independent billet remelter. Wagstaff Air-Slip casting. 75% scrap / 25% prime ratio. Triple M Metal scrap processing on-site. Billet 7-16 inch diameter."
    ),
    AluminumFacility(
        name="Matalco Canton",
        company="Matalco Inc. (Giampaolo/Rio Tinto JV)",
        facility_types=[FacilityType.BILLET_CASTER],
        city="Canton", state="OH", country=Country.US,
        lat=40.8059, lon=-81.3784,
        capacity_kt=82, capacity_notes="180M lbs/yr",
        products="extrusion billet",
        markets="construction, industrial",
        alloys="6xxx",
        has_casthouse=True, has_recycling=True,
        status="operating", startup_year=2010,
        notes="Acquired as Thakar Aluminum 2010. 7-12 inch billet. Upgraded systems 2011."
    ),
    AluminumFacility(
        name="Matalco Bluffton",
        company="Matalco Inc. (Giampaolo/Rio Tinto JV)",
        facility_types=[FacilityType.BILLET_CASTER],
        city="Bluffton", state="IN", country=Country.US,
        lat=40.7381, lon=-85.1719,
        capacity_kt=104, capacity_notes="230M lbs/yr",
        products="extrusion billet, forging stock",
        markets="construction, automotive",
        alloys="6xxx",
        has_casthouse=True, has_recycling=True,
        status="operating",
        notes="95,000 sq ft facility. Scrap-based billet production."
    ),
    AluminumFacility(
        name="Matalco Wisconsin Rapids",
        company="Matalco Inc. (Giampaolo/Rio Tinto JV)",
        facility_types=[FacilityType.BILLET_CASTER],
        city="Wisconsin Rapids", state="WI", country=Country.US,
        lat=44.3836, lon=-89.8171,
        capacity_kt=109, capacity_notes="240M lbs/yr; expandable",
        products="extrusion billet, rolling ingot, RSI sows",
        markets="construction, automotive, industrial",
        alloys="5xxx, 6xxx",
        has_casthouse=True, has_recycling=True,
        status="operating", startup_year=2020,
        notes="$80M greenfield. 110,000 sq ft. Started Nov 2020. Wagstaff ShurCast DC casting. Billet + rolling slab capability. Serves upper Midwest extruders."
    ),
    AluminumFacility(
        name="Matalco Shelbyville",
        company="Matalco Inc. (Giampaolo/Rio Tinto JV)",
        facility_types=[FacilityType.BILLET_CASTER],
        city="Shelbyville", state="KY", country=Country.US,
        lat=38.2120, lon=-85.2237,
        capacity_kt=159, capacity_notes="350M lbs/yr",
        products="extrusion billet, forging stock",
        markets="construction, automotive",
        alloys="3xxx, 5xxx, 6xxx",
        has_casthouse=True, has_recycling=True,
        status="operating",
        notes="140,000 sq ft. Acquired Ohio Valley Aluminum. 2 melting furnaces, 4 batch homogenization furnaces."
    ),
    AluminumFacility(
        name="Matalco Franklin",
        company="Matalco Inc. (Giampaolo/Rio Tinto JV)",
        facility_types=[FacilityType.BILLET_CASTER],
        city="Franklin", state="KY", country=Country.US,
        lat=36.7222, lon=-86.5769,
        capacity_kt=122, capacity_notes="270M lbs/yr; $53.5M investment",
        products="extrusion billet, rolling slab",
        markets="construction, automotive",
        alloys="6xxx",
        has_casthouse=True, has_recycling=True,
        status="operating", startup_year=2022,
        notes="$53.5M greenfield. 461,000 sq ft. Matalco Kentucky LLC. Billet and slab from recycled aluminum."
    ),
    AluminumFacility(
        name="Matalco Brampton",
        company="Matalco Inc. (Giampaolo/Rio Tinto JV)",
        facility_types=[FacilityType.BILLET_CASTER],
        city="Brampton", state="ON", country=Country.CA,
        lat=43.7315, lon=-79.7624,
        capacity_kt=113, capacity_notes="250M lbs/yr; HQ facility",
        products="extrusion billet",
        markets="construction, industrial",
        alloys="6xxx",
        has_casthouse=True, has_recycling=True,
        status="operating", startup_year=2005,
        notes="Matalco headquarters and original plant. Triple M Metal scrap processing adjacent."
    ),

    # ── REAL ALLOY ──
    AluminumFacility(
        name="Real Alloy Elyria",
        company="Real Alloy (Recycling Holdings International)",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Elyria", state="OH", country=Country.US,
        lat=41.3684, lon=-82.1076,
        capacity_kt=50,
        products="secondary alloy ingot, sow",
        markets="automotive, industrial casting",
        alloys="A356, A380, secondary casting alloys",
        has_casthouse=True, has_recycling=True,
        status="operating",
        notes="Major secondary smelter. Produces specification alloy ingot for die casters and foundries."
    ),
    AluminumFacility(
        name="Real Alloy Rock Creek",
        company="Real Alloy",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Rock Creek", state="OH", country=Country.US,
        lat=41.6598, lon=-80.8559,
        capacity_kt=40,
        products="secondary alloy ingot",
        markets="automotive, industrial",
        has_casthouse=True, has_recycling=True,
        status="operating",
    ),
    AluminumFacility(
        name="Real Alloy Chicago Heights",
        company="Real Alloy",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Chicago Heights", state="IL", country=Country.US,
        lat=41.5062, lon=-87.6356,
        capacity_kt=40,
        products="secondary alloy ingot",
        markets="automotive, industrial",
        has_casthouse=True, has_recycling=True,
        status="operating",
    ),
    AluminumFacility(
        name="Real Alloy Wabash",
        company="Real Alloy",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Wabash", state="IN", country=Country.US,
        lat=40.7978, lon=-85.8205,
        capacity_kt=35,
        products="secondary alloy ingot",
        markets="automotive, industrial",
        has_casthouse=True, has_recycling=True,
        status="operating",
        notes="DOE $67.3M grant for low-waste recycling facility in Wabash."
    ),
    AluminumFacility(
        name="Real Alloy Coldwater",
        company="Real Alloy",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Coldwater", state="MI", country=Country.US,
        lat=41.9403, lon=-85.0005,
        capacity_kt=30,
        products="secondary alloy ingot",
        markets="automotive",
        has_casthouse=True, has_recycling=True,
        status="operating",
    ),
    AluminumFacility(
        name="Real Alloy Steele",
        company="Real Alloy",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Steele", state="AL", country=Country.US,
        lat=33.9395, lon=-86.2036,
        capacity_kt=35,
        products="secondary alloy ingot",
        markets="automotive",
        has_casthouse=True, has_recycling=True,
        status="operating",
    ),
    AluminumFacility(
        name="Real Alloy Goodyear",
        company="Real Alloy",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Goodyear", state="AZ", country=Country.US,
        lat=33.4353, lon=-112.3585,
        capacity_kt=30,
        products="secondary alloy ingot",
        markets="automotive, industrial",
        has_casthouse=True, has_recycling=True,
        status="operating",
    ),
    AluminumFacility(
        name="Real Alloy Sapulpa",
        company="Real Alloy",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Sapulpa", state="OK", country=Country.US,
        lat=35.9987, lon=-96.1142,
        capacity_kt=25,
        products="secondary alloy ingot",
        markets="industrial",
        has_casthouse=True, has_recycling=True,
        status="operating",
    ),
    AluminumFacility(
        name="Real Alloy Post Falls",
        company="Real Alloy",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Post Falls", state="ID", country=Country.US,
        lat=47.7177, lon=-116.9516,
        capacity_kt=25,
        products="secondary alloy ingot",
        markets="industrial",
        has_casthouse=True, has_recycling=True,
        status="operating",
    ),
    AluminumFacility(
        name="Real Alloy Morgantown",
        company="Real Alloy",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Morgantown", state="KY", country=Country.US,
        lat=37.2292, lon=-86.6836,
        capacity_kt=30,
        products="secondary alloy ingot",
        markets="automotive, industrial",
        has_casthouse=True, has_recycling=True,
        status="operating",
    ),
    AluminumFacility(
        name="Real Alloy Loudon",
        company="Real Alloy",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Loudon", state="TN", country=Country.US,
        lat=35.7330, lon=-84.3338,
        capacity_kt=30,
        products="secondary alloy ingot",
        markets="automotive",
        has_casthouse=True, has_recycling=True,
        status="operating",
    ),
    AluminumFacility(
        name="Real Alloy Friendly",
        company="Real Alloy",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Friendly", state="WV", country=Country.US,
        lat=39.5098, lon=-81.0610,
        capacity_kt=25,
        products="secondary alloy ingot",
        markets="industrial",
        has_casthouse=True, has_recycling=True,
        water_access=True,
        status="operating",
    ),

    # ── SPECTRO ALLOYS ──
    AluminumFacility(
        name="Spectro Alloys Rosemount",
        company="Spectro Alloys Corp.",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Rosemount", state="MN", country=Country.US,
        lat=44.7369, lon=-93.1258,
        capacity_kt=80, capacity_notes="Acquired by UAE's EGA affiliate Sep 2024 (110kt/yr)",
        products="secondary alloy ingot, sow",
        markets="automotive, industrial",
        has_casthouse=True, has_recycling=True,
        status="operating",
        notes="Acquired by UAE-based aluminum producer (EGA affiliate) Sep 2024. 110kt/yr secondary production. Major Midwest secondary smelter."
    ),

    # ── SCEPTER INDUSTRIES ──
    AluminumFacility(
        name="Scepter Greeneville",
        company="Scepter Inc.",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Greeneville", state="TN", country=Country.US,
        lat=36.1629, lon=-82.8310,
        capacity_kt=40,
        products="secondary alloy ingot, sow",
        markets="automotive die casting, foundry",
        has_casthouse=True, has_recycling=True,
        status="operating",
    ),
    AluminumFacility(
        name="Scepter Waverly",
        company="Scepter Inc.",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Waverly", state="TN", country=Country.US,
        lat=36.0839, lon=-87.7877,
        capacity_kt=35,
        products="secondary alloy ingot",
        markets="automotive",
        has_casthouse=True, has_recycling=True,
        status="operating",
    ),
    AluminumFacility(
        name="Scepter Bicknell",
        company="Scepter Inc.",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Bicknell", state="IN", country=Country.US,
        lat=38.7742, lon=-87.3078,
        capacity_kt=30,
        products="secondary alloy ingot",
        markets="industrial",
        has_casthouse=True, has_recycling=True,
        status="operating",
    ),
    AluminumFacility(
        name="Scepter Seneca Falls",
        company="Scepter Inc.",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Seneca Falls", state="NY", country=Country.US,
        lat=42.9106, lon=-76.7966,
        capacity_kt=25,
        products="secondary alloy ingot",
        markets="industrial",
        has_casthouse=True, has_recycling=True,
        status="operating",
    ),

    # ── JUPITER ALUMINUM ──
    AluminumFacility(
        name="Jupiter Aluminum Hammond",
        company="Jupiter Aluminum Corp.",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Hammond", state="IN", country=Country.US,
        lat=41.5834, lon=-87.5001,
        capacity_kt=50,
        products="secondary alloy ingot, sow",
        markets="automotive, industrial",
        has_casthouse=True, has_recycling=True,
        status="operating",
        notes="Major secondary smelter in NW Indiana industrial corridor."
    ),

    # ── SMELTER SERVICE CORP / TENNESSEE ALUMINUM ──
    AluminumFacility(
        name="Smelter Service Mount Pleasant",
        company="Smelter Service Corp.",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Mount Pleasant", state="TN", country=Country.US,
        lat=35.5345, lon=-87.2067,
        capacity_kt=35,
        products="secondary alloy ingot",
        markets="automotive, industrial",
        has_casthouse=True, has_recycling=True,
        status="operating",
    ),

    # ── PENNEX ALUMINUM ──
    AluminumFacility(
        name="Pennex Aluminum Wellsville",
        company="Pennex Aluminum Co.",
        facility_types=[FacilityType.BILLET_CASTER, FacilityType.SECONDARY_SMELTER],
        city="Wellsville", state="PA", country=Country.US,
        lat=40.0530, lon=-76.9412,
        capacity_kt=40,
        products="extrusion billet, secondary ingot",
        markets="construction, industrial",
        alloys="6xxx",
        has_casthouse=True, has_recycling=True,
        status="operating",
        notes="Billet casting and secondary smelting. Serves East Coast extruders."
    ),

    # ── OWL'S HEAD ALLOYS ──
    AluminumFacility(
        name="Owl's Head Alloys Bowling Green",
        company="Owl's Head Alloys Inc.",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Bowling Green", state="KY", country=Country.US,
        lat=36.9685, lon=-86.4388,
        capacity_kt=30,
        products="secondary alloy ingot",
        markets="automotive, industrial",
        has_casthouse=True, has_recycling=True,
        status="operating",
        notes="Expanding operations in Bowling Green."
    ),

    # ── AUDUBON METALS ──
    AluminumFacility(
        name="Audubon Metals Henderson",
        company="Audubon Metals LLC",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Henderson", state="KY", country=Country.US,
        lat=37.8362, lon=-87.5900,
        capacity_kt=40,
        products="secondary alloy ingot, sow",
        markets="automotive die casting",
        has_casthouse=True, has_recycling=True,
        barge_access=True, water_access=True,
        status="operating",
        notes="Ohio River access. Produces specification alloys for automotive die casting."
    ),

    # ── COLONIAL METALS ──
    AluminumFacility(
        name="Colonial Metals Columbia",
        company="Colonial Metals",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Columbia", state="PA", country=Country.US,
        lat=40.0335, lon=-76.5025,
        capacity_kt=25,
        products="secondary alloy ingot",
        markets="industrial",
        has_casthouse=True, has_recycling=True,
        status="operating",
    ),

    # ── BECK ALUMINUM ──
    AluminumFacility(
        name="Beck Aluminum Lebanon",
        company="Beck Aluminum Alloys (Real Alloy)",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Lebanon", state="PA", country=Country.US,
        lat=40.3409, lon=-76.4114,
        capacity_kt=20,
        products="secondary alloy ingot",
        markets="industrial",
        has_casthouse=True, has_recycling=True,
        status="operating",
        notes="Acquired by Real Alloy 2016."
    ),

    # ── ALLIED METAL ──
    AluminumFacility(
        name="Allied Metal Chicago",
        company="Allied Metal Co.",
        facility_types=[FacilityType.SECONDARY_SMELTER],
        city="Chicago", state="IL", country=Country.US,
        lat=41.8354, lon=-87.6517,
        capacity_kt=30,
        products="secondary alloy ingot",
        markets="industrial",
        has_casthouse=True, has_recycling=True,
        status="operating",
    ),
]


# =============================================================================
# COMBINE ALL FACILITIES
# =============================================================================

ALL_FACILITIES = PRIMARY_SMELTERS + ROLLING_MILLS + SECONDARY_FACILITIES


# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

def to_geojson(facilities=None):
    """Export facilities as GeoJSON FeatureCollection."""
    if facilities is None:
        facilities = ALL_FACILITIES

    features = []
    for f in facilities:
        props = {
            "name": f.name,
            "company": f.company,
            "facility_types": "|".join(ft if isinstance(ft, str) else ft.value for ft in f.facility_types),
            "city": f.city,
            "state": f.state,
            "country": f.country if isinstance(f.country, str) else f.country.value,
            "capacity_kt": f.capacity_kt,
            "capacity_notes": f.capacity_notes,
            "products": f.products,
            "markets": f.markets,
            "alloys": f.alloys,
            "has_hot_mill": f.has_hot_mill,
            "has_cold_mill": f.has_cold_mill,
            "has_casthouse": f.has_casthouse,
            "has_recycling": f.has_recycling,
            "num_potlines": f.num_potlines,
            "port_adjacent": f.port_adjacent,
            "water_access": f.water_access,
            "barge_access": f.barge_access,
            "rail_served": f.rail_served,
            "status": f.status,
            "startup_year": f.startup_year,
            "employees": f.employees,
            "notes": f.notes,
        }
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [f.lon, f.lat]
            },
            "properties": props
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features
    }


def to_csv(facilities=None):
    """Export facilities as CSV string."""
    if facilities is None:
        facilities = ALL_FACILITIES

    output = io.StringIO()
    fieldnames = [
        "name", "company", "facility_types", "city", "state", "country",
        "lat", "lon", "capacity_kt", "capacity_notes",
        "products", "markets", "alloys",
        "has_hot_mill", "has_cold_mill", "has_casthouse", "has_recycling",
        "num_potlines", "port_adjacent", "water_access", "barge_access", "rail_served",
        "status", "startup_year", "employees", "notes"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for f in facilities:
        row = {
            "name": f.name,
            "company": f.company,
            "facility_types": "|".join(ft if isinstance(ft, str) else ft.value for ft in f.facility_types),
            "city": f.city,
            "state": f.state,
            "country": f.country if isinstance(f.country, str) else f.country.value,
            "lat": f.lat,
            "lon": f.lon,
            "capacity_kt": f.capacity_kt or "",
            "capacity_notes": f.capacity_notes,
            "products": f.products,
            "markets": f.markets,
            "alloys": f.alloys,
            "has_hot_mill": f.has_hot_mill,
            "has_cold_mill": f.has_cold_mill,
            "has_casthouse": f.has_casthouse,
            "has_recycling": f.has_recycling,
            "num_potlines": f.num_potlines or "",
            "port_adjacent": f.port_adjacent,
            "water_access": f.water_access,
            "barge_access": f.barge_access,
            "rail_served": f.rail_served,
            "status": f.status,
            "startup_year": f.startup_year or "",
            "employees": f.employees or "",
            "notes": f.notes,
        }
        writer.writerow(row)
    return output.getvalue()


def summary_stats(facilities=None):
    """Print summary statistics."""
    if facilities is None:
        facilities = ALL_FACILITIES

    print(f"\n{'='*70}")
    print("US & NORTH AMERICAN ALUMINUM FACILITIES - SUMMARY")
    print(f"{'='*70}")
    print(f"Total facilities: {len(facilities)}")

    # By country
    by_country = {}
    for f in facilities:
        c = f.country if isinstance(f.country, str) else f.country.value
        by_country[c] = by_country.get(c, 0) + 1
    print(f"\nBy country:")
    for c, n in sorted(by_country.items()):
        print(f"  {c}: {n}")

    # By type
    type_counts = {}
    for f in facilities:
        for ft in f.facility_types:
            key = ft if isinstance(ft, str) else ft.value
            type_counts[key] = type_counts.get(key, 0) + 1
    print(f"\nBy facility type:")
    for t, n in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {n}")

    # By status
    status_counts = {}
    for f in facilities:
        status_counts[f.status] = status_counts.get(f.status, 0) + 1
    print(f"\nBy status:")
    for s, n in sorted(status_counts.items(), key=lambda x: -x[1]):
        print(f"  {s}: {n}")

    # Capacity by type
    print(f"\nCapacity by type (operating + reduced only):")
    type_cap = {}
    for f in facilities:
        if f.status in ("operating", "reduced") and f.capacity_kt:
            for ft in f.facility_types:
                key = ft if isinstance(ft, str) else ft.value
                type_cap[key] = type_cap.get(key, 0) + f.capacity_kt
    for t, c in sorted(type_cap.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c:,.0f} kt/yr")

    # Top companies by capacity
    print(f"\nTop companies by total capacity (all types, operating/reduced):")
    co_cap = {}
    for f in facilities:
        if f.status in ("operating", "reduced") and f.capacity_kt:
            co = f.company.split("(")[0].strip()
            co_cap[co] = co_cap.get(co, 0) + f.capacity_kt
    for co, c in sorted(co_cap.items(), key=lambda x: -x[1])[:15]:
        print(f"  {co}: {c:,.0f} kt/yr")

    # Logistics
    port_adj = sum(1 for f in facilities if f.port_adjacent)
    water = sum(1 for f in facilities if f.water_access)
    barge = sum(1 for f in facilities if f.barge_access)
    print(f"\nLogistics access:")
    print(f"  Port-adjacent: {port_adj}")
    print(f"  Water access: {water}")
    print(f"  Barge access: {barge}")

    # States with most facilities
    state_counts = {}
    for f in facilities:
        state_counts[f.state] = state_counts.get(f.state, 0) + 1
    print(f"\nTop states:")
    for s, n in sorted(state_counts.items(), key=lambda x: -x[1])[:12]:
        print(f"  {s}: {n}")

    print(f"\n{'='*70}\n")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "geojson":
            print(json.dumps(to_geojson(), indent=2))
        elif cmd == "csv":
            print(to_csv())
        elif cmd == "stats":
            summary_stats()
        else:
            print(f"Usage: {sys.argv[0]} [geojson|csv|stats]")
    else:
        summary_stats()

        # Export files
        with open("us_aluminum_facilities.geojson", "w") as f:
            json.dump(to_geojson(), f, indent=2)
        print("Wrote us_aluminum_facilities.geojson")

        with open("us_aluminum_facilities.csv", "w") as f:
            f.write(to_csv())
        print("Wrote us_aluminum_facilities.csv")
