#!/usr/bin/env python3
"""
AIST 2021 Directory — Iron and Steel Plants
Master Geospatial Dataset

Source: AIST 2021 Directory of Iron and Steel Plants (free facility tables)
Tables parsed: Hot Strip Mills, Plate Mills, Galvanizing Lines, Electric Arc Furnaces
Data vintage: 2021 (ownership updated with notes for 2021+ changes)

Generates: GeoJSON, CSV, and summary statistics for all North American
flat-rolled steel production facilities.
"""

import json
import csv
import os
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


# ──────────────────────────────────────────────────────────────
# ENUMS
# ──────────────────────────────────────────────────────────────

class FacilityType(str, Enum):
    HOT_STRIP_MILL = "hot_strip_mill"
    PLATE_MILL = "plate_mill"
    COLD_REDUCTION_MILL = "cold_reduction_mill"
    GALVANIZING_LINE = "galvanizing_line"
    TEMPER_MILL = "temper_mill"
    EAF = "electric_arc_furnace"
    BOF = "basic_oxygen_furnace"
    BLAST_FURNACE = "blast_furnace"
    CONTINUOUS_CASTER = "continuous_caster"
    PIPE_TUBE_MILL = "pipe_tube_mill"
    COATING_LINE = "coating_line"
    INTEGRATED_WORKS = "integrated_works"


class Country(str, Enum):
    US = "US"
    CA = "Canada"
    MX = "Mexico"


# ──────────────────────────────────────────────────────────────
# DATA CLASS
# ──────────────────────────────────────────────────────────────

@dataclass
class SteelPlant:
    """Single production facility with geospatial and technical data."""
    name: str
    company: str
    city: str
    state: str
    country: str
    lat: float
    lon: float
    facility_types: list  # list of FacilityType values present at site
    
    # Technical specs (varies by facility type)
    capacity_kt_year: Optional[int] = None  # stated capacity, '000 mt/year
    
    # Hot strip mill specs
    hsm_finishing_stands: Optional[int] = None
    hsm_min_thickness_mm: Optional[float] = None
    hsm_max_thickness_mm: Optional[float] = None
    hsm_max_width_mm: Optional[int] = None
    hsm_mill_builder: Optional[str] = None
    hsm_startup_year: Optional[int] = None
    
    # Plate mill specs
    plate_min_thickness_mm: Optional[float] = None
    plate_max_thickness_mm: Optional[float] = None
    plate_max_width_mm: Optional[int] = None
    plate_discrete_or_coil: Optional[str] = None
    
    # Galvanizing line specs
    galv_num_lines: Optional[int] = None
    galv_coating_types: Optional[str] = None  # GI, GA, AZ, AL, EG
    galv_total_capacity_kt: Optional[int] = None
    galv_max_width_mm: Optional[int] = None
    
    # EAF specs
    eaf_num_furnaces: Optional[int] = None
    eaf_heat_size_mt: Optional[int] = None
    eaf_transformer_mva: Optional[int] = None
    eaf_capacity_kt: Optional[int] = None
    
    # Metadata
    notes: Optional[str] = None
    ownership_updated: Optional[str] = None  # post-2021 ownership changes
    port_adjacent: bool = False
    rail_served: bool = True  # virtually all mills are rail-served
    barge_access: bool = False
    water_access: bool = False


# ──────────────────────────────────────────────────────────────
# MASTER FACILITY DATABASE
# Geocoded coordinates for every facility in the AIST 2021 tables
# ──────────────────────────────────────────────────────────────

PLANTS = [

    # ═══════════════════════════════════════════════════════════
    # UNITED STATES — INTEGRATED / MAJOR FLAT-ROLLED
    # ═══════════════════════════════════════════════════════════

    SteelPlant(
        name="AM/NS Calvert",
        company="ArcelorMittal/Nippon Steel (now Nippon Steel)",
        city="Calvert", state="AL", country="US",
        lat=31.0035, lon=-88.0137,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.GALVANIZING_LINE, FacilityType.COLD_REDUCTION_MILL],
        capacity_kt_year=5400,
        hsm_finishing_stands=7, hsm_min_thickness_mm=1.5, hsm_max_thickness_mm=25.4,
        hsm_max_width_mm=1860, hsm_mill_builder="SMS Siemag", hsm_startup_year=2010,
        galv_num_lines=3, galv_coating_types="GI,GA,AL", galv_total_capacity_kt=1520, galv_max_width_mm=1870,
        notes="HSM cap 5,400kt. 3 HDGL lines (500+500+520kt). Former ThyssenKrupp plant.",
        ownership_updated="Nippon Steel acquired AM share 2023. Now Nippon Steel / AM JV.",
        port_adjacent=True, barge_access=True, water_access=True,
    ),

    SteelPlant(
        name="Burns Harbor",
        company="Cleveland-Cliffs (fmr ArcelorMittal USA)",
        city="Burns Harbor", state="IN", country="US",
        lat=41.6256, lon=-87.1253,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.PLATE_MILL, FacilityType.GALVANIZING_LINE, FacilityType.BLAST_FURNACE, FacilityType.BOF],
        capacity_kt_year=4100,
        hsm_finishing_stands=7, hsm_min_thickness_mm=1.45, hsm_max_thickness_mm=12.7,
        hsm_max_width_mm=1930, hsm_mill_builder="United Engineering", hsm_startup_year=1966,
        plate_min_thickness_mm=4.75, plate_max_thickness_mm=102, plate_max_width_mm=3861,
        plate_discrete_or_coil="Discrete",
        galv_num_lines=1, galv_coating_types="GI,GA", galv_total_capacity_kt=550, galv_max_width_mm=1829,
        notes="Integrated BF/BOF. HSM 4,100kt. 110-in plate 330kt + 160-in plate 710kt. HDGL 550kt.",
        ownership_updated="Cleveland-Cliffs acquired from ArcelorMittal Dec 2020",
        port_adjacent=True, water_access=True, barge_access=False,
    ),

    SteelPlant(
        name="Cleveland Works",
        company="Cleveland-Cliffs (fmr ArcelorMittal USA)",
        city="Cleveland", state="OH", country="US",
        lat=41.4575, lon=-81.6386,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.GALVANIZING_LINE, FacilityType.BLAST_FURNACE, FacilityType.BOF],
        capacity_kt_year=3000,
        hsm_finishing_stands=7, hsm_min_thickness_mm=1.42, hsm_max_thickness_mm=19.05,
        hsm_max_width_mm=1905, hsm_mill_builder="MESTA/GE", hsm_startup_year=1971,
        galv_num_lines=1, galv_coating_types="GI,GA", galv_total_capacity_kt=650, galv_max_width_mm=1830,
        notes="Integrated. HSM 3,000kt. HDGL 650kt.",
        ownership_updated="Cleveland-Cliffs acquired from ArcelorMittal Dec 2020",
        water_access=True, port_adjacent=True,
    ),

    SteelPlant(
        name="Indiana Harbor East",
        company="Cleveland-Cliffs (fmr ArcelorMittal USA)",
        city="East Chicago", state="IN", country="US",
        lat=41.6467, lon=-87.4406,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.GALVANIZING_LINE, FacilityType.EAF, FacilityType.BLAST_FURNACE, FacilityType.BOF],
        capacity_kt_year=4900,
        hsm_finishing_stands=6, hsm_min_thickness_mm=1.93, hsm_max_thickness_mm=9.5,
        hsm_max_width_mm=1859, hsm_mill_builder="United Engineering/GE", hsm_startup_year=1965,
        eaf_num_furnaces=1, eaf_heat_size_mt=105, eaf_transformer_mva=60, eaf_capacity_kt=454,
        notes="Integrated BF/BOF + EAF (idle). HSM 4,900kt. Also IH West galv line (577kt GI/GA).",
        ownership_updated="Cleveland-Cliffs acquired from ArcelorMittal Dec 2020",
        water_access=True, port_adjacent=True,
    ),

    SteelPlant(
        name="Indiana Harbor West",
        company="Cleveland-Cliffs (fmr ArcelorMittal USA)",
        city="East Chicago", state="IN", country="US",
        lat=41.6500, lon=-87.4500,
        facility_types=[FacilityType.GALVANIZING_LINE],
        galv_num_lines=1, galv_coating_types="GI,GA", galv_total_capacity_kt=577, galv_max_width_mm=1830,
        notes="Galv line at IH West complex. 577kt GI/GA.",
        ownership_updated="Cleveland-Cliffs acquired from ArcelorMittal Dec 2020",
        water_access=True,
    ),

    SteelPlant(
        name="Riverdale (CSP)",
        company="Cleveland-Cliffs (fmr ArcelorMittal USA)",
        city="Riverdale", state="IL", country="US",
        lat=41.6328, lon=-87.6353,
        facility_types=[FacilityType.HOT_STRIP_MILL],
        capacity_kt_year=900,
        hsm_finishing_stands=7, hsm_min_thickness_mm=1.07, hsm_max_thickness_mm=17.0,
        hsm_max_width_mm=1585, hsm_mill_builder="SMS/Siemens", hsm_startup_year=1996,
        notes="Compact strip production (CSP) thin slab caster. 900kt.",
        ownership_updated="Cleveland-Cliffs acquired from ArcelorMittal Dec 2020",
    ),

    SteelPlant(
        name="Columbus (Coatesville)",
        company="Cleveland-Cliffs (fmr ArcelorMittal USA)",
        city="Coatesville", state="PA", country="US",
        lat=39.9832, lon=-75.8241,
        facility_types=[FacilityType.PLATE_MILL, FacilityType.EAF],
        capacity_kt_year=550,
        plate_min_thickness_mm=4.75, plate_max_thickness_mm=711, plate_max_width_mm=4953,
        plate_discrete_or_coil="Discrete",
        eaf_num_furnaces=1, eaf_heat_size_mt=150, eaf_transformer_mva=67, eaf_capacity_kt=798,
        notes="140-in plate (500kt) + 206-in plate (50kt). EAF 798kt. Heavy/wide plate specialist.",
        ownership_updated="Cleveland-Cliffs acquired from ArcelorMittal Dec 2020",
    ),

    SteelPlant(
        name="Conshohocken Plate",
        company="Cleveland-Cliffs (fmr ArcelorMittal USA)",
        city="Conshohocken", state="PA", country="US",
        lat=40.0804, lon=-75.3041,
        facility_types=[FacilityType.PLATE_MILL],
        capacity_kt_year=410,
        plate_min_thickness_mm=3.56, plate_max_thickness_mm=76, plate_max_width_mm=2642,
        plate_discrete_or_coil="Discrete and coil",
        notes="Steckel plate mill, 410kt. Discrete + coil plate.",
        ownership_updated="Cleveland-Cliffs acquired from ArcelorMittal Dec 2020",
    ),

    SteelPlant(
        name="Gary Works",
        company="United States Steel Corporation",
        city="Gary", state="IN", country="US",
        lat=41.6064, lon=-87.3356,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.PLATE_MILL, FacilityType.BLAST_FURNACE, FacilityType.BOF],
        capacity_kt_year=5700,
        hsm_finishing_stands=7, hsm_min_thickness_mm=1.8, hsm_max_thickness_mm=25.4,
        hsm_max_width_mm=1981, hsm_mill_builder="Blaw-Knox/GE", hsm_startup_year=1967,
        plate_min_thickness_mm=4.75, plate_max_thickness_mm=38, plate_max_width_mm=3861,
        plate_discrete_or_coil="Discrete",
        notes="Largest US Steel plant. HSM 5,700kt. Gary Plate 580kt. Integrated BF/BOF.",
        water_access=True, port_adjacent=True, barge_access=False,
    ),

    SteelPlant(
        name="Granite City Works",
        company="United States Steel Corporation",
        city="Granite City", state="IL", country="US",
        lat=38.7014, lon=-90.1487,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.GALVANIZING_LINE, FacilityType.BLAST_FURNACE, FacilityType.BOF],
        capacity_kt_year=3300,
        hsm_finishing_stands=7, hsm_min_thickness_mm=1.45, hsm_max_thickness_mm=18.08,
        hsm_max_width_mm=1991, hsm_mill_builder="MESTA/GE", hsm_startup_year=1966,
        galv_num_lines=1, galv_coating_types="GI,AZ", galv_total_capacity_kt=254, galv_max_width_mm=1245,
        notes="Integrated. HSM 3,300kt. GGG galv 254kt. Near St. Louis on Mississippi.",
        barge_access=True, water_access=True,
    ),

    SteelPlant(
        name="Great Lakes Works",
        company="United States Steel Corporation",
        city="Ecorse", state="MI", country="US",
        lat=42.2381, lon=-83.1501,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.GALVANIZING_LINE, FacilityType.BLAST_FURNACE],
        capacity_kt_year=3800,
        hsm_finishing_stands=7, hsm_min_thickness_mm=1.85, hsm_max_thickness_mm=12.7,
        hsm_max_width_mm=1861, hsm_mill_builder="Wean United/GE", hsm_startup_year=1961,
        galv_num_lines=1, galv_coating_types="GI,GA", galv_total_capacity_kt=472, galv_max_width_mm=1854,
        notes="HSM 3,800kt. CGL 472kt + EGL. BF idled 2020; hot strip idled. Some finishing active.",
        ownership_updated="Hot strip/BF permanently idled 2020. Some finishing ops continue.",
        water_access=True,
    ),

    SteelPlant(
        name="Mon Valley Works — Irvin Plant",
        company="United States Steel Corporation",
        city="West Mifflin", state="PA", country="US",
        lat=40.3614, lon=-79.9067,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.GALVANIZING_LINE],
        capacity_kt_year=2500,
        hsm_finishing_stands=6, hsm_min_thickness_mm=1.52, hsm_max_thickness_mm=10.16,
        hsm_max_width_mm=1676, hsm_mill_builder="MESTA", hsm_startup_year=1938,
        galv_num_lines=2, galv_coating_types="GI", galv_total_capacity_kt=360, galv_max_width_mm=1321,
        notes="HSM 2,500kt (oldest continuous HSM in US, 1938). GAL1 200kt + GAL2 160kt.",
        water_access=True,
    ),

    SteelPlant(
        name="Mon Valley Works — Fairless Plant",
        company="United States Steel Corporation",
        city="Fairless Hills", state="PA", country="US",
        lat=40.1751, lon=-74.8585,
        facility_types=[FacilityType.GALVANIZING_LINE],
        galv_num_lines=1, galv_coating_types="GI,GA", galv_total_capacity_kt=299, galv_max_width_mm=1626,
        notes="GAL3 galvanizing 299kt. Finishing only (no steelmaking).",
        water_access=True,
    ),

    SteelPlant(
        name="Midwest Plant (Portage)",
        company="United States Steel Corporation",
        city="Portage", state="IN", country="US",
        lat=41.5889, lon=-87.1761,
        facility_types=[FacilityType.GALVANIZING_LINE],
        galv_num_lines=2, galv_coating_types="GI,GA", galv_total_capacity_kt=699, galv_max_width_mm=1829,
        notes="72-in GACT 454kt + No.3 CL 245kt. Major galv hub near Burns Harbor.",
    ),

    SteelPlant(
        name="Fairfield Works",
        company="United States Steel Corporation",
        city="Fairfield", state="AL", country="US",
        lat=33.4890, lon=-86.9122,
        facility_types=[FacilityType.GALVANIZING_LINE, FacilityType.EAF],
        galv_num_lines=1, galv_coating_types="GI,AZ", galv_total_capacity_kt=272, galv_max_width_mm=1257,
        notes="No.5 DualLine galv 272kt. EAF steelmaking resumed 2023-24.",
        ownership_updated="EAF restart 2024 for tubular products.",
    ),

    SteelPlant(
        name="Big River Steel",
        company="United States Steel Corporation",
        city="Osceola", state="AR", country="US",
        lat=35.6870, lon=-89.9626,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.GALVANIZING_LINE, FacilityType.EAF],
        capacity_kt_year=3300,
        hsm_finishing_stands=6, hsm_min_thickness_mm=1.47, hsm_max_thickness_mm=25.4,
        hsm_max_width_mm=1980, hsm_mill_builder="SMS", hsm_startup_year=2016,
        eaf_num_furnaces=2, eaf_heat_size_mt=150, eaf_transformer_mva=123, eaf_capacity_kt=2900,
        galv_num_lines=1, galv_coating_types="GI", galv_total_capacity_kt=475, galv_max_width_mm=1850,
        notes="BRS Phase 1: HSM ~1,500kt (AIST 2021), 2 EAF 2,900kt, HDGL 475kt. Flex mill.",
        ownership_updated="U.S. Steel completed acquisition Q1 2021.",
        barge_access=True, water_access=True,
    ),

    SteelPlant(
        name="Big River Steel 2 (BR2)",
        company="United States Steel Corporation",
        city="Osceola", state="AR", country="US",
        lat=35.6890, lon=-89.9600,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.GALVANIZING_LINE, FacilityType.EAF, FacilityType.COLD_REDUCTION_MILL],
        capacity_kt_year=3000,
        hsm_finishing_stands=None, hsm_min_thickness_mm=None, hsm_max_thickness_mm=None,
        hsm_max_width_mm=1980, hsm_mill_builder="SMS", hsm_startup_year=2024,
        notes="BR2: $3.2B. Endless casting+rolling, 2 EAF, 2 coating lines (1 AHSS, 1 heavy gauge). Started 2024. Doubles USS EAF flat-rolled to 6M+ TPY.",
        ownership_updated="Commissioned Oct 2024. Pickling line + TCM Nov 2024. CGL Jan 2025.",
        barge_access=True, water_access=True,
    ),

    SteelPlant(
        name="PRO-TEC Coating",
        company="U.S. Steel / Kobe Steel JV",
        city="Leipsic", state="OH", country="US",
        lat=41.1000, lon=-83.9814,
        facility_types=[FacilityType.GALVANIZING_LINE],
        galv_num_lines=3, galv_coating_types="GI,GA", galv_total_capacity_kt=1588, galv_max_width_mm=1880,
        notes="CGL1 635kt + CGL2 499kt + CGL3 454kt = 1,588kt total. Major auto-grade galvanizer.",
    ),

    SteelPlant(
        name="UPI (Pittsburg CA)",
        company="United States Steel Corporation",
        city="Pittsburg", state="CA", country="US",
        lat=38.0047, lon=-121.8842,
        facility_types=[FacilityType.GALVANIZING_LINE],
        galv_num_lines=1, galv_coating_types="GI,GA", galv_total_capacity_kt=363, galv_max_width_mm=1410,
        notes="West Coast galvanizing. CGL 363kt.",
    ),

    # ── Cleveland-Cliffs (AK Steel legacy) ──

    SteelPlant(
        name="AK Steel — Butler Works",
        company="Cleveland-Cliffs",
        city="Butler", state="PA", country="US",
        lat=40.8612, lon=-79.8953,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.EAF],
        capacity_kt_year=600,
        hsm_finishing_stands=5, hsm_min_thickness_mm=1.7, hsm_max_thickness_mm=6.4,
        hsm_max_width_mm=1270, hsm_mill_builder="Bliss/Continental", hsm_startup_year=1957,
        eaf_num_furnaces=1, eaf_heat_size_mt=161, eaf_transformer_mva=170, eaf_capacity_kt=908,
        notes="EAF 908kt, HSM 600kt. Specialty/electrical steel. Narrow strip.",
    ),

    SteelPlant(
        name="AK Steel — Mansfield Works",
        company="Cleveland-Cliffs",
        city="Mansfield", state="OH", country="US",
        lat=40.7834, lon=-82.5154,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.EAF],
        capacity_kt_year=500,
        hsm_finishing_stands=6, hsm_min_thickness_mm=2.0, hsm_max_thickness_mm=12.7,
        hsm_max_width_mm=1270, hsm_mill_builder="United/Bliss/Siemens VAI", hsm_startup_year=1952,
        eaf_num_furnaces=2, eaf_heat_size_mt=122, eaf_transformer_mva=49, eaf_capacity_kt=545,
        notes="EAF melt shop + HSM 500kt. Narrow strip specialty.",
    ),

    SteelPlant(
        name="AK Steel — Middletown Works",
        company="Cleveland-Cliffs",
        city="Middletown", state="OH", country="US",
        lat=39.5150, lon=-84.3983,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.GALVANIZING_LINE, FacilityType.BLAST_FURNACE, FacilityType.BOF],
        capacity_kt_year=5400,
        hsm_finishing_stands=7, hsm_min_thickness_mm=1.8, hsm_max_thickness_mm=9.5,
        hsm_max_width_mm=2032, hsm_mill_builder="United/Westinghouse/Siemens", hsm_startup_year=1966,
        galv_num_lines=3, galv_coating_types="GI,EG,AL", galv_total_capacity_kt=1388, galv_max_width_mm=1900,
        notes="Integrated BF/BOF. HSM 5,400kt (widest AK mill). EG 454kt + GI 508kt + AL 426kt.",
        ownership_updated="Cliffs hydrogen injection trials on BF. Major decarbonization investment.",
        water_access=True,
    ),

    SteelPlant(
        name="AK Steel — Dearborn Works",
        company="Cleveland-Cliffs",
        city="Dearborn", state="MI", country="US",
        lat=42.3070, lon=-83.1534,
        facility_types=[FacilityType.GALVANIZING_LINE, FacilityType.BLAST_FURNACE, FacilityType.BOF],
        galv_num_lines=1, galv_coating_types="GI,GA", galv_total_capacity_kt=454, galv_max_width_mm=1829,
        notes="Integrated BF/BOF + HDGL 454kt. Automotive-grade supplier to Detroit OEMs.",
        water_access=True,
    ),

    SteelPlant(
        name="AK Steel — Rockport Works",
        company="Cleveland-Cliffs",
        city="Rockport", state="IN", country="US",
        lat=37.8831, lon=-87.0494,
        facility_types=[FacilityType.GALVANIZING_LINE],
        galv_num_lines=1, galv_coating_types="GI,GA", galv_total_capacity_kt=907, galv_max_width_mm=2032,
        notes="CGL 907kt — largest single galv line in Cliffs system. Wide strip (80-in).",
    ),

    SteelPlant(
        name="I/N Tek and I/N Kote",
        company="Cleveland-Cliffs (fmr ArcelorMittal/Nippon JV)",
        city="New Carlisle", state="IN", country="US",
        lat=41.7036, lon=-86.5097,
        facility_types=[FacilityType.COLD_REDUCTION_MILL, FacilityType.GALVANIZING_LINE],
        galv_num_lines=2, galv_coating_types="GI,EG", galv_total_capacity_kt=817, galv_max_width_mm=1829,
        notes="Cold rolling (I/N Tek) + galvanizing (I/N Kote). KCGL 454kt + EG 363kt. Auto-grade.",
        ownership_updated="Cleveland-Cliffs acquired from ArcelorMittal Dec 2020",
    ),

    SteelPlant(
        name="Weirton",
        company="Cleveland-Cliffs (fmr Weirton Steel)",
        city="Weirton", state="WV", country="US",
        lat=40.4189, lon=-80.5895,
        facility_types=[FacilityType.GALVANIZING_LINE, FacilityType.COATING_LINE],
        galv_num_lines=2, galv_coating_types="GI,GA,GF,AL,AZ", galv_total_capacity_kt=674, galv_max_width_mm=1549,
        notes="Wheeling-Nippon: AGL 375kt (GI/GA/GF/AL) + CGL 299kt (GI/AZ). Tin mill closed.",
        ownership_updated="Cliffs announced transformer manufacturing conversion 2024.",
        water_access=True,
    ),

    SteelPlant(
        name="Columbus (ArcelorMittal legacy)",
        company="Cleveland-Cliffs (fmr ArcelorMittal USA)",
        city="Columbus", state="OH", country="US",
        lat=39.9612, lon=-82.9988,
        facility_types=[FacilityType.GALVANIZING_LINE],
        galv_num_lines=1, galv_coating_types="GI,GA", galv_total_capacity_kt=400, galv_max_width_mm=1829,
        notes="HDGL 400kt. Finishing facility.",
        ownership_updated="Cleveland-Cliffs acquired from ArcelorMittal Dec 2020",
    ),

    # ── Nucor flat-rolled ──

    SteelPlant(
        name="Nucor Steel — Arkansas (Blytheville)",
        company="Nucor Corporation",
        city="Blytheville", state="AR", country="US",
        lat=35.9270, lon=-89.9190,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.GALVANIZING_LINE, FacilityType.EAF],
        capacity_kt_year=2300,
        hsm_finishing_stands=6, hsm_min_thickness_mm=1.4, hsm_max_thickness_mm=15.88,
        hsm_max_width_mm=1635, hsm_mill_builder="SMS/Siemens", hsm_startup_year=1992,
        eaf_num_furnaces=2, eaf_heat_size_mt=148, eaf_transformer_mva=81, eaf_capacity_kt=2450,
        galv_num_lines=2, galv_coating_types="GI,GA", galv_total_capacity_kt=999, galv_max_width_mm=1900,
        notes="2 EAF 2,450kt. HSM 2,300kt. GI 544kt + CAGL 455kt. Also Nucor-Yamato beam mill adjacent.",
    ),

    SteelPlant(
        name="Nucor Steel — Berkeley (Huger SC)",
        company="Nucor Corporation",
        city="Huger", state="SC", country="US",
        lat=33.0427, lon=-79.7914,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.GALVANIZING_LINE, FacilityType.EAF],
        capacity_kt_year=2300,
        hsm_finishing_stands=7, hsm_min_thickness_mm=1.4, hsm_max_thickness_mm=15.88,
        hsm_max_width_mm=1905, hsm_mill_builder="SMS/Siemens", hsm_startup_year=1996,
        eaf_num_furnaces=2, eaf_heat_size_mt=154, eaf_transformer_mva=180, eaf_capacity_kt=2956,
        galv_num_lines=1, galv_coating_types="GI,GA", galv_total_capacity_kt=635, galv_max_width_mm=1676,
        notes="2 EAF 2,956kt. HSM 2,300kt (7-stand, widest Nucor at 75-in). HDGL 635kt.",
        port_adjacent=True, water_access=True,
    ),

    SteelPlant(
        name="Nucor Steel — Decatur (Trinity AL)",
        company="Nucor Corporation",
        city="Trinity", state="AL", country="US",
        lat=34.6068, lon=-87.0886,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.GALVANIZING_LINE, FacilityType.EAF],
        capacity_kt_year=2300,
        hsm_finishing_stands=5, hsm_min_thickness_mm=1.4, hsm_max_thickness_mm=19.05,
        hsm_max_width_mm=1651, hsm_mill_builder="MHI/INNSE/Siemens", hsm_startup_year=1996,
        eaf_num_furnaces=2, eaf_heat_size_mt=150, eaf_transformer_mva=75, eaf_capacity_kt=2268,
        galv_num_lines=1, galv_coating_types="GI,GA", galv_total_capacity_kt=544, galv_max_width_mm=1829,
        notes="2 DC-EAF 2,268kt. HSM 2,300kt (5+rougher). HDGL 544kt (wide, heavy-gauge capable to 6.3mm).",
        barge_access=True, water_access=True,
    ),

    SteelPlant(
        name="Nucor Steel Gallatin (Ghent KY)",
        company="Nucor Corporation",
        city="Ghent", state="KY", country="US",
        lat=38.7380, lon=-85.0616,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.GALVANIZING_LINE, FacilityType.EAF],
        capacity_kt_year=1500,
        hsm_finishing_stands=6, hsm_min_thickness_mm=1.4, hsm_max_thickness_mm=17.4,
        hsm_max_width_mm=1626, hsm_mill_builder="SMS/Siemens/Danieli", hsm_startup_year=1995,
        eaf_num_furnaces=1, eaf_heat_size_mt=172, eaf_transformer_mva=75, eaf_capacity_kt=1452,
        galv_num_lines=1, galv_coating_types="GI,GA", galv_total_capacity_kt=454, galv_max_width_mm=1854,
        notes="EAF 1,452kt. HSM 1,500kt (added roughing stands 2020). PAGL 454kt. On Ohio River.",
        ownership_updated="2020 added 2 roughing stands. Nucor-JFE galv JV also at Ghent.",
        barge_access=True, water_access=True,
    ),

    SteelPlant(
        name="Nucor Steel — Indiana (Crawfordsville)",
        company="Nucor Corporation",
        city="Crawfordsville", state="IN", country="US",
        lat=39.9743, lon=-86.9004,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.GALVANIZING_LINE, FacilityType.EAF],
        capacity_kt_year=1900,
        hsm_finishing_stands=6, hsm_min_thickness_mm=1.47, hsm_max_thickness_mm=15.88,
        hsm_max_width_mm=1397, hsm_mill_builder="SMS/Westinghouse/Siemens", hsm_startup_year=1989,
        eaf_num_furnaces=2, eaf_heat_size_mt=118, eaf_transformer_mva=90, eaf_capacity_kt=2304,
        galv_num_lines=1, galv_coating_types="GI", galv_total_capacity_kt=318, galv_max_width_mm=1346,
        notes="First Nucor thin-slab flat mill (1989). 2 EAF 2,304kt. HSM 1,900kt. GI 318kt. Narrower strip.",
    ),

    SteelPlant(
        name="Nucor Steel — Hertford County (Cofield NC)",
        company="Nucor Corporation",
        city="Cofield", state="NC", country="US",
        lat=36.3452, lon=-76.9019,
        facility_types=[FacilityType.PLATE_MILL, FacilityType.EAF],
        capacity_kt_year=1000,
        plate_min_thickness_mm=7.94, plate_max_thickness_mm=76, plate_max_width_mm=3175,
        plate_discrete_or_coil="Discrete",
        eaf_num_furnaces=1, eaf_heat_size_mt=150, eaf_transformer_mva=88, eaf_capacity_kt=1542,
        notes="EAF 1,542kt. 4-hi plate 1,000kt (wide: 125-in). Discrete plate. Near Norfolk/Hampton Roads.",
    ),

    SteelPlant(
        name="Nucor Steel Tuscaloosa",
        company="Nucor Corporation",
        city="Tuscaloosa", state="AL", country="US",
        lat=33.2098, lon=-87.5692,
        facility_types=[FacilityType.PLATE_MILL, FacilityType.EAF],
        capacity_kt_year=1090,
        plate_min_thickness_mm=19.05, plate_max_thickness_mm=64, plate_max_width_mm=2540,
        plate_discrete_or_coil="Discrete and coil",
        eaf_num_furnaces=1, eaf_heat_size_mt=122, eaf_transformer_mva=96, eaf_capacity_kt=1200,
        notes="Steckel plate 1,090kt. EAF 1,200kt. Discrete + coil plate.",
    ),

    SteelPlant(
        name="Nucor Steel Longview",
        company="Nucor Corporation",
        city="Longview", state="TX", country="US",
        lat=32.5007, lon=-94.7405,
        facility_types=[FacilityType.PLATE_MILL, FacilityType.EAF],
        capacity_kt_year=160,
        plate_min_thickness_mm=19.05, plate_max_thickness_mm=311, plate_max_width_mm=3048,
        plate_discrete_or_coil="Discrete",
        eaf_num_furnaces=2, eaf_heat_size_mt=23, eaf_transformer_mva=10, eaf_capacity_kt=110,
        notes="Heavy plate from ingot casting. 160kt. Niche heavy/wide plate.",
    ),

    SteelPlant(
        name="Nucor Steel West Virginia (Formerly CSI Flat Products)",
        company="Nucor Corporation",
        city="Apple Grove", state="WV", country="US",
        lat=38.6667, lon=-82.1167,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.EAF],
        capacity_kt_year=3000,
        notes="$3.1B greenfield. 2 EAF + endless casting/rolling. 3M TPY capacity. Under construction 2024-2026. Nucor's largest single investment.",
        ownership_updated="Construction ~40% complete as of Feb 2025. Commissioning target 2026.",
        barge_access=True, water_access=True,
    ),

    # ── Steel Dynamics Inc. (SDI) ──

    SteelPlant(
        name="SDI — Butler (Flat Roll Div.)",
        company="Steel Dynamics Inc.",
        city="Butler", state="IN", country="US",
        lat=41.4289, lon=-84.8713,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.GALVANIZING_LINE, FacilityType.EAF],
        capacity_kt_year=2700,
        hsm_finishing_stands=7, hsm_min_thickness_mm=1.09, hsm_max_thickness_mm=12.7,
        hsm_max_width_mm=1588, hsm_mill_builder="SMS/Siemens", hsm_startup_year=1996,
        eaf_num_furnaces=2, eaf_heat_size_mt=150, eaf_transformer_mva=120, eaf_capacity_kt=2900,
        galv_num_lines=2, galv_coating_types="GI,GA", galv_total_capacity_kt=871, galv_max_width_mm=1575,
        notes="2 EAF 2,900kt. HSM 2,700kt (7-stand, thinnest at 1.09mm). 2 HDGL 544+327=871kt.",
    ),

    SteelPlant(
        name="SDI — Columbus (Flat Roll Div.)",
        company="Steel Dynamics Inc.",
        city="Columbus", state="MS", country="US",
        lat=33.4957, lon=-88.4272,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.GALVANIZING_LINE, FacilityType.EAF],
        capacity_kt_year=3100,
        hsm_finishing_stands=6, hsm_min_thickness_mm=1.5, hsm_max_thickness_mm=19.2,
        hsm_max_width_mm=1930, hsm_mill_builder="SMS/TMEIC", hsm_startup_year=2007,
        eaf_num_furnaces=2, eaf_heat_size_mt=158, eaf_transformer_mva=160, eaf_capacity_kt=3100,
        galv_num_lines=3, galv_coating_types="GI,GA,AZ,AL", galv_total_capacity_kt=1120, galv_max_width_mm=1829,
        notes="2 EAF 3,100kt. HSM 3,100kt (widest SDI at 76-in). 3 galv lines: GI/GA 408 + AZ 349 + AL 363 = 1,120kt.",
    ),

    SteelPlant(
        name="SDI — Sinton (Flat Roll Div.)",
        company="Steel Dynamics Inc.",
        city="Sinton", state="TX", country="US",
        lat=28.0364, lon=-97.5092,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.GALVANIZING_LINE, FacilityType.EAF, FacilityType.COATING_LINE],
        capacity_kt_year=3000,
        galv_num_lines=1, galv_coating_types="GI,GA,AZ", galv_total_capacity_kt=500, galv_max_width_mm=1930,
        notes="Greenfield 2021. 2 EAF + HSM ~3M TPY. CGL 500kt (GI/GA/AZ). Paint line. Near Corpus Christi port.",
        ownership_updated="Started up 2021-2022. Full production 2023.",
        port_adjacent=True, water_access=True,
    ),

    SteelPlant(
        name="SDI — Heartland (Terre Haute)",
        company="Steel Dynamics Inc.",
        city="Terre Haute", state="IN", country="US",
        lat=39.4667, lon=-87.4139,
        facility_types=[FacilityType.GALVANIZING_LINE],
        galv_num_lines=1, galv_coating_types="GI", galv_total_capacity_kt=435, galv_max_width_mm=1854,
        notes="GI galvanizing 435kt. Flat roll finishing.",
    ),

    SteelPlant(
        name="SDI — Jeffersonville",
        company="Steel Dynamics Inc.",
        city="Jeffersonville", state="IN", country="US",
        lat=38.2892, lon=-85.7372,
        facility_types=[FacilityType.GALVANIZING_LINE],
        galv_num_lines=1, galv_coating_types="GI,AZ", galv_total_capacity_kt=272, galv_max_width_mm=1524,
        notes="Butler Div. satellite. GI/AZ 272kt. Near Louisville.",
    ),

    SteelPlant(
        name="SDI — GalvTech (Pittsburgh)",
        company="Steel Dynamics Inc.",
        city="Pittsburgh", state="PA", country="US",
        lat=40.4406, lon=-79.9959,
        facility_types=[FacilityType.GALVANIZING_LINE],
        galv_num_lines=1, galv_coating_types="GI,GF", galv_total_capacity_kt=417, galv_max_width_mm=1524,
        notes="GI/GF 417kt. Pittsburgh finishing.",
    ),

    SteelPlant(
        name="SDI — MetalTech (Pittsburgh)",
        company="Steel Dynamics Inc.",
        city="Pittsburgh", state="PA", country="US",
        lat=40.4406, lon=-80.0000,
        facility_types=[FacilityType.GALVANIZING_LINE],
        galv_num_lines=1, galv_coating_types="GI,GF", galv_total_capacity_kt=318, galv_max_width_mm=1219,
        notes="Heavy-gauge GI/GF 318kt.",
    ),

    SteelPlant(
        name="SDI — NexTech (Turtle Creek PA)",
        company="Steel Dynamics Inc.",
        city="Turtle Creek", state="PA", country="US",
        lat=40.4061, lon=-79.8256,
        facility_types=[FacilityType.GALVANIZING_LINE],
        galv_num_lines=1, galv_coating_types="GI", galv_total_capacity_kt=154, galv_max_width_mm=1067,
        notes="Narrow GI 154kt.",
    ),

    # ── NLMK ──

    SteelPlant(
        name="NLMK Indiana",
        company="NLMK USA",
        city="Portage", state="IN", country="US",
        lat=41.5889, lon=-87.1761,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.EAF],
        capacity_kt_year=1000,
        hsm_finishing_stands=5, hsm_min_thickness_mm=1.78, hsm_max_thickness_mm=19.0,
        hsm_max_width_mm=1549, hsm_mill_builder="Sack/MESTA/Danieli", hsm_startup_year=1992,
        eaf_num_furnaces=1, eaf_heat_size_mt=118, eaf_transformer_mva=120, eaf_capacity_kt=680,
        notes="EAF 680kt. HSM 1,000kt (5-stand). Russian-owned (NLMK Group).",
    ),

    SteelPlant(
        name="NLMK Pennsylvania (Sharon Coating)",
        company="NLMK USA",
        city="Farrell", state="PA", country="US",
        lat=41.2120, lon=-80.4965,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.GALVANIZING_LINE],
        capacity_kt_year=1800,
        hsm_finishing_stands=6, hsm_min_thickness_mm=1.5, hsm_max_thickness_mm=16.46,
        hsm_max_width_mm=1359, hsm_mill_builder="United Engineering", hsm_startup_year=1966,
        galv_num_lines=2, galv_coating_types="GI,GA", galv_total_capacity_kt=704, galv_max_width_mm=1829,
        notes="HSM 1,800kt. Sharon Coating: GI 250kt + GI/GA 454kt = 704kt.",
    ),

    # ── Other flat-rolled ──

    SteelPlant(
        name="California Steel Industries",
        company="California Steel Industries (JFE/Vale JV)",
        city="Fontana", state="CA", country="US",
        lat=34.0922, lon=-117.4350,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.GALVANIZING_LINE],
        capacity_kt_year=2700,
        hsm_finishing_stands=6, hsm_min_thickness_mm=1.37, hsm_max_thickness_mm=15.88,
        hsm_max_width_mm=1880, hsm_mill_builder="Kaiser Engineering/GE", hsm_startup_year=1958,
        galv_num_lines=2, galv_coating_types="GI,GA", galv_total_capacity_kt=730, galv_max_width_mm=1524,
        notes="HSM 2,700kt (from imported slabs). 2 galv: 430 + 300 = 730kt. Only major flat-rolled in SoCal.",
    ),

    SteelPlant(
        name="North Star BlueScope Steel",
        company="BlueScope Steel (Australia)",
        city="Delta", state="OH", country="US",
        lat=41.5722, lon=-84.0053,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.EAF],
        capacity_kt_year=2700,
        hsm_finishing_stands=6, hsm_min_thickness_mm=1.3, hsm_max_thickness_mm=12.7,
        hsm_max_width_mm=None, hsm_mill_builder="Danieli", hsm_startup_year=1997,
        eaf_num_furnaces=1, eaf_heat_size_mt=171, eaf_transformer_mva=140, eaf_capacity_kt=1905,
        notes="EAF 1,905kt (largest single-furnace EAF in AIST 2021 data). HSM 2,700kt.",
    ),

    SteelPlant(
        name="JSW Steel USA — Mingo Junction",
        company="JSW Steel USA (India)",
        city="Mingo Junction", state="OH", country="US",
        lat=40.3225, lon=-80.6070,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.EAF],
        capacity_kt_year=2800,
        hsm_finishing_stands=6, hsm_min_thickness_mm=1.5, hsm_max_thickness_mm=9.5,
        hsm_max_width_mm=1930, hsm_mill_builder="Blaw-Knox/United/GE", hsm_startup_year=1965,
        eaf_num_furnaces=1, eaf_heat_size_mt=250, eaf_transformer_mva=157, eaf_capacity_kt=1500,
        notes="EAF 1,500kt (250mt heat, large). HSM 2,800kt. Indian-owned. On Ohio River.",
        water_access=True,
    ),

    SteelPlant(
        name="JSW Steel USA — Baytown Plate",
        company="JSW Steel USA (India)",
        city="Baytown", state="TX", country="US",
        lat=29.7355, lon=-94.9774,
        facility_types=[FacilityType.PLATE_MILL],
        capacity_kt_year=710,
        plate_min_thickness_mm=7.94, plate_max_thickness_mm=152, plate_max_width_mm=3861,
        plate_discrete_or_coil="Discrete",
        notes="4-hi reversing plate 710kt. Wide heavy plate (152-in). Near Houston Ship Channel.",
        port_adjacent=True, water_access=True,
    ),

    SteelPlant(
        name="ATI Specialty Rolled Products",
        company="ATI Inc.",
        city="Brackenridge", state="PA", country="US",
        lat=40.6068, lon=-79.7402,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.EAF],
        capacity_kt_year=None,
        hsm_finishing_stands=7, hsm_min_thickness_mm=1.78, hsm_max_thickness_mm=21.0,
        hsm_max_width_mm=2083, hsm_mill_builder="Siemens VAI", hsm_startup_year=2014,
        eaf_num_furnaces=1, eaf_heat_size_mt=100, eaf_transformer_mva=55, eaf_capacity_kt=360,
        notes="Specialty/stainless hot rolling. 7-stand HSM (2014 new build). EAF 360kt.",
    ),

    SteelPlant(
        name="EVRAZ Portland",
        company="EVRAZ North America",
        city="Portland", state="OR", country="US",
        lat=45.5666, lon=-122.7019,
        facility_types=[FacilityType.PLATE_MILL],
        capacity_kt_year=1090,
        plate_min_thickness_mm=4.75, plate_max_thickness_mm=203, plate_max_width_mm=3505,
        plate_discrete_or_coil="Discrete and coil",
        notes="2 Steckel plate mills 1,090kt. Widest plate in US West (138-in). Discrete + coil.",
        ownership_updated="EVRAZ divested NA assets; now under new ownership structure.",
        water_access=True, port_adjacent=True,
    ),

    SteelPlant(
        name="EVRAZ Rocky Mountain Steel",
        company="EVRAZ North America",
        city="Pueblo", state="CO", country="US",
        lat=38.2544, lon=-104.6091,
        facility_types=[FacilityType.EAF],
        eaf_num_furnaces=1, eaf_heat_size_mt=127, eaf_transformer_mva=67, eaf_capacity_kt=1100,
        notes="EAF 1,100kt. Rail and plate/structural. Colorado's only steel mill.",
        ownership_updated="EVRAZ divested NA assets.",
    ),

    # ── SSAB Americas ──

    SteelPlant(
        name="SSAB Alabama (Axis)",
        company="SSAB Americas",
        city="Axis", state="AL", country="US",
        lat=30.7885, lon=-88.0323,
        facility_types=[FacilityType.PLATE_MILL, FacilityType.EAF],
        capacity_kt_year=1130,
        plate_min_thickness_mm=4.57, plate_max_thickness_mm=76, plate_max_width_mm=3099,
        plate_discrete_or_coil="Discrete and coil",
        eaf_num_furnaces=1, eaf_heat_size_mt=159, eaf_transformer_mva=140, eaf_capacity_kt=1270,
        notes="EAF 1,270kt. Steckel plate 1,130kt. Discrete + coil. SSAB HardOx/Strenx specialty.",
        port_adjacent=True, water_access=True, barge_access=True,
    ),

    SteelPlant(
        name="SSAB Iowa (Muscatine)",
        company="SSAB Americas",
        city="Muscatine", state="IA", country="US",
        lat=41.4245, lon=-91.0432,
        facility_types=[FacilityType.PLATE_MILL, FacilityType.EAF],
        capacity_kt_year=1130,
        plate_min_thickness_mm=4.57, plate_max_thickness_mm=76, plate_max_width_mm=3099,
        plate_discrete_or_coil="Discrete and coil",
        eaf_num_furnaces=1, eaf_heat_size_mt=141, eaf_transformer_mva=140, eaf_capacity_kt=1194,
        notes="EAF 1,194kt. Steckel plate 1,130kt. First SSAB Zero fossil-free steel shipped 2023.",
        ownership_updated="AIST lists as Muscatine IA. Previously referenced as Montpelier (nearby).",
        barge_access=True, water_access=True,
    ),

    # ── Stainless ──

    SteelPlant(
        name="Outokumpu Stainless USA",
        company="Outokumpu Oyj (Finland)",
        city="Calvert", state="AL", country="US",
        lat=31.0050, lon=-88.0100,
        facility_types=[FacilityType.EAF, FacilityType.HOT_STRIP_MILL, FacilityType.COLD_REDUCTION_MILL],
        eaf_num_furnaces=1, eaf_heat_size_mt=160, eaf_transformer_mva=155, eaf_capacity_kt=1000,
        notes="Fully integrated stainless: EAF 1,000kt + hot rolling + cold finishing. Adjacent to AM/NS Calvert.",
        port_adjacent=True, water_access=True,
    ),

    SteelPlant(
        name="North American Stainless (NAS)",
        company="Acerinox S.A. (Spain)",
        city="Ghent", state="KY", country="US",
        lat=38.7380, lon=-85.0616,
        facility_types=[FacilityType.EAF, FacilityType.HOT_STRIP_MILL, FacilityType.COLD_REDUCTION_MILL],
        eaf_num_furnaces=2, eaf_heat_size_mt=140, eaf_transformer_mva=155, eaf_capacity_kt=1600,
        notes="Largest US stainless flat mill. 2 EAF 1,600kt combined. Hot+cold rolling. Acquired Haynes International 2024.",
        ownership_updated="Completed Haynes International acquisition Nov 2024.",
    ),

    # ── Other galvanizers / coaters ──

    SteelPlant(
        name="Double G Coatings",
        company="Cleveland-Cliffs (fmr ArcelorMittal)",
        city="Jackson", state="MS", country="US",
        lat=32.2988, lon=-90.1848,
        facility_types=[FacilityType.GALVANIZING_LINE],
        galv_num_lines=1, galv_coating_types="GI,AZ", galv_total_capacity_kt=272, galv_max_width_mm=1245,
        notes="GI/AZ 272kt. Finishing only.",
    ),

    SteelPlant(
        name="Gregory Industries",
        company="Gregory Industries Inc.",
        city="Canton", state="OH", country="US",
        lat=40.7989, lon=-81.3784,
        facility_types=[FacilityType.GALVANIZING_LINE],
        galv_num_lines=1, galv_coating_types="GI,GA", galv_total_capacity_kt=132, galv_max_width_mm=495,
        notes="Narrow strip galvanizer 132kt.",
    ),

    SteelPlant(
        name="National Galvanizing",
        company="National Galvanizing L.P.",
        city="Monroe", state="MI", country="US",
        lat=41.9164, lon=-83.3977,
        facility_types=[FacilityType.GALVANIZING_LINE],
        galv_num_lines=1, galv_coating_types="GI,GA", galv_total_capacity_kt=204, galv_max_width_mm=1219,
        notes="Heavy-gauge galvanizing 204kt (1.52-6.4mm).",
    ),

    SteelPlant(
        name="Spartan Steel Coating",
        company="Worthington Industries / Cleveland-Cliffs JV",
        city="Monroe", state="MI", country="US",
        lat=41.9200, lon=-83.4000,
        facility_types=[FacilityType.GALVANIZING_LINE],
        galv_num_lines=1, galv_coating_types="GI,GA", galv_total_capacity_kt=544, galv_max_width_mm=1575,
        notes="Worthington/Cliffs JV. GI/GA 544kt. Auto-grade.",
    ),

    SteelPlant(
        name="Worthington Industries (Delta OH)",
        company="Worthington Enterprises (fmr Worthington Industries)",
        city="Delta", state="OH", country="US",
        lat=41.5739, lon=-84.0050,
        facility_types=[FacilityType.GALVANIZING_LINE],
        galv_num_lines=1, galv_coating_types="GI,GA", galv_total_capacity_kt=363, galv_max_width_mm=1575,
        notes="GI/GA 363kt. Adjacent to North Star BlueScope.",
        ownership_updated="Worthington split into Worthington Enterprises + Worthington Steel 2023.",
    ),

    SteelPlant(
        name="Ternium USA (Shreveport)",
        company="Ternium S.A. (Argentina/Luxembourg)",
        city="Shreveport", state="LA", country="US",
        lat=32.5252, lon=-93.7502,
        facility_types=[FacilityType.GALVANIZING_LINE, FacilityType.COATING_LINE],
        galv_num_lines=1, galv_coating_types="GI,AZ", galv_total_capacity_kt=236, galv_max_width_mm=1372,
        notes="GI/AZ 236kt + 2nd paint line (120kt, started ~2025). Latin American steel in US South.",
        ownership_updated="2nd paint line $98M, commissioned ~2025.",
    ),

    SteelPlant(
        name="Steelscape — Kalama WA",
        company="BlueScope Steel (Australia)",
        city="Kalama", state="WA", country="US",
        lat=46.0131, lon=-122.8412,
        facility_types=[FacilityType.GALVANIZING_LINE],
        galv_num_lines=1, galv_coating_types="GI", galv_total_capacity_kt=191, galv_max_width_mm=1321,
        notes="West Coast galvanizer. GI 191kt. BlueScope subsidiary.",
        water_access=True,
    ),

    SteelPlant(
        name="Steelscape — Rancho Cucamonga CA",
        company="BlueScope Steel (Australia)",
        city="Rancho Cucamonga", state="CA", country="US",
        lat=34.1064, lon=-117.5931,
        facility_types=[FacilityType.GALVANIZING_LINE],
        galv_num_lines=1, galv_coating_types="AZ", galv_total_capacity_kt=200, galv_max_width_mm=1270,
        notes="Galvalume (AZ) 200kt. SoCal.",
        ownership_updated="CMC previously had a plant at this location (closed). BlueScope Steelscape separate.",
    ),


    # ═══════════════════════════════════════════════════════════
    # CANADA — FLAT-ROLLED
    # ═══════════════════════════════════════════════════════════

    SteelPlant(
        name="Algoma Steel",
        company="Algoma Steel Group Inc.",
        city="Sault Ste. Marie", state="ON", country="CA",
        lat=46.5136, lon=-84.3358,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.PLATE_MILL, FacilityType.BLAST_FURNACE, FacilityType.BOF],
        capacity_kt_year=680,
        hsm_finishing_stands=6, hsm_min_thickness_mm=1.5, hsm_max_thickness_mm=12.7,
        hsm_max_width_mm=2540, hsm_mill_builder="Dominion Engineering", hsm_startup_year=1982,
        plate_min_thickness_mm=6.35, plate_max_thickness_mm=76, plate_max_width_mm=3810,
        plate_discrete_or_coil="Discrete and coil",
        notes="HSM 680kt strip + 410kt plate (combined mill). DSPC CSP line: 2,000kt. BF→EAF conversion underway.",
        ownership_updated="CA$825-875M decarbonization: replacing BF/BOF with EAF. Target ~2025-2026.",
        water_access=True, port_adjacent=True,
    ),

    SteelPlant(
        name="ArcelorMittal Dofasco",
        company="ArcelorMittal (Luxembourg)",
        city="Hamilton", state="ON", country="CA",
        lat=43.2557, lon=-79.8711,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.GALVANIZING_LINE, FacilityType.EAF, FacilityType.BLAST_FURNACE, FacilityType.BOF],
        capacity_kt_year=4700,
        hsm_finishing_stands=7, hsm_min_thickness_mm=1.52, hsm_max_thickness_mm=12.7,
        hsm_max_width_mm=1600, hsm_mill_builder="Dominion Eng/Hitachi/GE/Primetals", hsm_startup_year=1983,
        eaf_num_furnaces=1, eaf_heat_size_mt=167, eaf_transformer_mva=120, eaf_capacity_kt=1350,
        galv_num_lines=6, galv_coating_types="GI,GA,AZ", galv_total_capacity_kt=2266,
        notes="HSM 4,700kt. EAF 1,350kt. 6 galv lines totaling ~2,266kt (Hamilton + Côteau-du-Lac + Windsor).",
        water_access=True, port_adjacent=True,
    ),

    SteelPlant(
        name="Stelco — Lake Erie Works",
        company="Stelco Holdings Inc.",
        city="Nanticoke", state="ON", country="CA",
        lat=42.7904, lon=-80.0485,
        facility_types=[FacilityType.HOT_STRIP_MILL, FacilityType.GALVANIZING_LINE, FacilityType.BLAST_FURNACE, FacilityType.BOF],
        capacity_kt_year=2300,
        hsm_finishing_stands=6, hsm_min_thickness_mm=2.03, hsm_max_thickness_mm=15.88,
        hsm_max_width_mm=1880, hsm_mill_builder="Wean United/Dominion Eng", hsm_startup_year=1983,
        galv_num_lines=1, galv_coating_types="GI,GA", galv_total_capacity_kt=454,
        notes="Integrated BF/BOF. HSM 2,300kt. Z-Line galv 454kt + Hamilton galv 181kt.",
        water_access=True, port_adjacent=True,
    ),

]


# ──────────────────────────────────────────────────────────────
# EXPORT FUNCTIONS
# ──────────────────────────────────────────────────────────────

def to_geojson(plants: list, output_path: str):
    """Export plants to GeoJSON FeatureCollection."""
    features = []
    for p in plants:
        props = {
            "name": p.name,
            "company": p.company,
            "city": p.city,
            "state": p.state,
            "country": p.country,
            "facility_types": ", ".join(p.facility_types),
            "capacity_kt_year": p.capacity_kt_year,
            "hsm_finishing_stands": p.hsm_finishing_stands,
            "hsm_max_width_mm": p.hsm_max_width_mm,
            "hsm_startup_year": p.hsm_startup_year,
            "galv_num_lines": p.galv_num_lines,
            "galv_coating_types": p.galv_coating_types,
            "galv_total_capacity_kt": p.galv_total_capacity_kt,
            "eaf_num_furnaces": p.eaf_num_furnaces,
            "eaf_capacity_kt": p.eaf_capacity_kt,
            "plate_max_width_mm": p.plate_max_width_mm,
            "notes": p.notes,
            "ownership_updated": p.ownership_updated,
            "port_adjacent": p.port_adjacent,
            "barge_access": p.barge_access,
            "water_access": p.water_access,
        }
        # Remove None values
        props = {k: v for k, v in props.items() if v is not None}
        
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [p.lon, p.lat]
            },
            "properties": props
        }
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(output_path, 'w') as f:
        json.dump(geojson, f, indent=2)
    print(f"GeoJSON written: {output_path} ({len(features)} features)")


def to_csv(plants: list, output_path: str):
    """Export plants to CSV."""
    fieldnames = [
        'name', 'company', 'city', 'state', 'country', 'lat', 'lon',
        'facility_types', 'capacity_kt_year',
        'hsm_finishing_stands', 'hsm_min_thickness_mm', 'hsm_max_thickness_mm',
        'hsm_max_width_mm', 'hsm_mill_builder', 'hsm_startup_year',
        'plate_min_thickness_mm', 'plate_max_thickness_mm', 'plate_max_width_mm',
        'plate_discrete_or_coil',
        'galv_num_lines', 'galv_coating_types', 'galv_total_capacity_kt', 'galv_max_width_mm',
        'eaf_num_furnaces', 'eaf_heat_size_mt', 'eaf_transformer_mva', 'eaf_capacity_kt',
        'port_adjacent', 'rail_served', 'barge_access', 'water_access',
        'notes', 'ownership_updated'
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in plants:
            row = {}
            for fn in fieldnames:
                val = getattr(p, fn, None)
                if fn == 'facility_types':
                    val = "|".join(val) if val else ""
                row[fn] = val if val is not None else ""
            writer.writerow(row)
    print(f"CSV written: {output_path} ({len(plants)} rows)")


def summary_stats(plants: list):
    """Print summary statistics."""
    print("\n" + "="*70)
    print("AIST 2021 DIRECTORY — STEEL PLANTS GEOSPATIAL DATABASE")
    print("="*70)
    
    us = [p for p in plants if p.country == "US"]
    ca = [p for p in plants if p.country == "CA"]
    mx = [p for p in plants if p.country == "MX"]
    
    print(f"\nTotal facilities: {len(plants)}")
    print(f"  United States:  {len(us)}")
    print(f"  Canada:         {len(ca)}")
    print(f"  Mexico:         {len(mx)}")
    
    # By facility type
    print("\nFacilities by type (a plant may have multiple types):")
    type_counts = {}
    for p in plants:
        for ft in p.facility_types:
            type_counts[ft] = type_counts.get(ft, 0) + 1
    for ft, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {ft:30s} {count:3d}")
    
    # Hot strip mill capacity
    hsm_plants = [p for p in plants if FacilityType.HOT_STRIP_MILL in p.facility_types and p.capacity_kt_year]
    total_hsm = sum(p.capacity_kt_year for p in hsm_plants)
    print(f"\nHot Strip Mill capacity (stated): {total_hsm:,} kt/year across {len(hsm_plants)} mills")
    
    # Galvanizing capacity
    galv_plants = [p for p in plants if p.galv_total_capacity_kt]
    total_galv = sum(p.galv_total_capacity_kt for p in galv_plants)
    total_galv_lines = sum(p.galv_num_lines for p in galv_plants if p.galv_num_lines)
    print(f"Galvanizing capacity: {total_galv:,} kt/year across {total_galv_lines} lines at {len(galv_plants)} sites")
    
    # EAF capacity
    eaf_plants = [p for p in plants if p.eaf_capacity_kt]
    total_eaf = sum(p.eaf_capacity_kt for p in eaf_plants)
    print(f"EAF capacity (flat-rolled sites): {total_eaf:,} kt/year across {len(eaf_plants)} facilities")
    
    # Plate capacity
    plate_plants = [p for p in plants if FacilityType.PLATE_MILL in p.facility_types and p.capacity_kt_year]
    total_plate = sum(p.capacity_kt_year for p in plate_plants)
    print(f"Plate mill capacity: {total_plate:,} kt/year across {len(plate_plants)} mills")
    
    # Port/water access
    port = [p for p in plants if p.port_adjacent]
    water = [p for p in plants if p.water_access]
    barge = [p for p in plants if p.barge_access]
    print(f"\nLogistics access:")
    print(f"  Port-adjacent:  {len(port)}")
    print(f"  Water access:   {len(water)}")
    print(f"  Barge access:   {len(barge)}")
    
    # Top companies by HSM capacity
    print("\nTop companies by HSM capacity (US only):")
    company_cap = {}
    for p in us:
        if FacilityType.HOT_STRIP_MILL in p.facility_types and p.capacity_kt_year:
            co = p.company.split("(")[0].strip()
            company_cap[co] = company_cap.get(co, 0) + p.capacity_kt_year
    for co, cap in sorted(company_cap.items(), key=lambda x: -x[1]):
        print(f"  {co:45s} {cap:>7,} kt")
    
    print("\n" + "="*70)


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    summary_stats(PLANTS)
    
    # Export
    os.makedirs("/mnt/user-data/outputs", exist_ok=True)
    to_geojson(PLANTS, "/mnt/user-data/outputs/aist_steel_plants.geojson")
    to_csv(PLANTS, "/mnt/user-data/outputs/aist_steel_plants.csv")
    
    # Also export the Python module for CLI handover
    print("\nDone. Files ready for mapping and Claude Code integration.")
