"""
OceanDatum — Hold Cleaning Intelligence Reporting Module
hold_cleaning_module.py

Integrates with the OceanDatum reporting system to generate:
  - Hold Cleaning Readiness Reports
  - MARPOL Wash Water Compliance Summaries
  - Cargo Transition Analysis (previous → next cargo risk scoring)
  - Pre-Loading Survey Preparation Sheets
  - Source/Reference Digest Reports

Usage (standalone):
    from hold_cleaning_module import HoldCleaningModule
    mod = HoldCleaningModule()
    report = mod.cargo_transition_report("coal", "grain", vessel_type="Panamax")
    print(report.text_summary())

Or integrate into existing reporting pipeline:
    from hold_cleaning_module import HoldCleaningModule
    hcm = HoldCleaningModule()
    hcm.attach_to_reporter(your_reporter_instance)
"""

import json
import os
import textwrap
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CleaningTransition:
    """Represents a cargo transition cleaning scenario."""
    previous_cargo: str
    next_cargo: str
    vessel_type: str = "Panamax"
    load_port: str = ""
    ballast_days_available: Optional[float] = None
    vessel_dwt: Optional[int] = None

@dataclass
class HoldCleaningReport:
    """Output container for a hold cleaning analysis."""
    transition: CleaningTransition
    required_standard: str = ""
    standard_rank: int = 0
    challenge_level: str = ""       # LOW / MEDIUM / HIGH / CRITICAL
    challenge_notes: list = field(default_factory=list)
    cleaning_phases: list = field(default_factory=list)
    regulatory_items: list = field(default_factory=list)
    marpol_notes: list = field(default_factory=list)
    survey_risks: list = field(default_factory=list)
    references: list = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def text_summary(self, width: int = 76) -> str:
        """Return formatted text report."""
        t = self.transition
        lines = []
        bar = "═" * width

        lines.append(bar)
        lines.append(f"  HOLD CLEANING INTELLIGENCE REPORT — OceanDatum")
        lines.append(bar)
        lines.append(f"  Generated:      {self.generated_at[:19]}")
        lines.append(f"  Previous Cargo: {t.previous_cargo.upper()}")
        lines.append(f"  Next Cargo:     {t.next_cargo.upper()}")
        lines.append(f"  Vessel Type:    {t.vessel_type}")
        if t.load_port:
            lines.append(f"  Loading Port:   {t.load_port}")
        if t.ballast_days_available:
            lines.append(f"  Time Available: {t.ballast_days_available} days ballast voyage")
        lines.append("")

        lines.append(f"  TARGET CLEANLINESS STANDARD: {self.required_standard.upper()}")
        lines.append(f"  CHALLENGE LEVEL:             {self.challenge_level}")
        lines.append("")

        if self.challenge_notes:
            lines.append("─" * width)
            lines.append("  CHALLENGE ASSESSMENT")
            lines.append("─" * width)
            for n in self.challenge_notes:
                for l in textwrap.wrap(f"  • {n}", width - 2):
                    lines.append(l)

        if self.cleaning_phases:
            lines.append("")
            lines.append("─" * width)
            lines.append("  CLEANING SEQUENCE")
            lines.append("─" * width)
            for phase in self.cleaning_phases:
                lines.append(f"\n  [{phase['name']}]")
                for step in phase.get("steps", []):
                    for l in textwrap.wrap(f"    • {step}", width - 2):
                        lines.append(l)

        if self.regulatory_items:
            lines.append("")
            lines.append("─" * width)
            lines.append("  REGULATORY COMPLIANCE")
            lines.append("─" * width)
            for item in self.regulatory_items:
                lines.append(f"  [ ] {item}")

        if self.marpol_notes:
            lines.append("")
            lines.append("─" * width)
            lines.append("  MARPOL ANNEX V — WASH WATER")
            lines.append("─" * width)
            for n in self.marpol_notes:
                for l in textwrap.wrap(f"  • {n}", width - 2):
                    lines.append(l)

        if self.survey_risks:
            lines.append("")
            lines.append("─" * width)
            lines.append("  TOP SURVEY FAILURE RISKS")
            lines.append("─" * width)
            for r in self.survey_risks[:8]:
                lines.append(f"  ⚠  {r}")

        if self.references:
            lines.append("")
            lines.append("─" * width)
            lines.append("  KEY REFERENCES")
            lines.append("─" * width)
            for ref in self.references:
                lines.append(f"  • {ref['name']}")
                if "url" in ref:
                    lines.append(f"    {ref['url']}")

        lines.append("")
        lines.append(bar)
        lines.append("  OceanDatum Hold Cleaning Intelligence Module v1.0")
        lines.append(f"  {bar}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON export or DB storage."""
        return {
            "report_type": "hold_cleaning_analysis",
            "generated_at": self.generated_at,
            "transition": {
                "previous_cargo": self.transition.previous_cargo,
                "next_cargo": self.transition.next_cargo,
                "vessel_type": self.transition.vessel_type,
                "load_port": self.transition.load_port,
                "ballast_days_available": self.transition.ballast_days_available,
                "vessel_dwt": self.transition.vessel_dwt,
            },
            "required_standard": self.required_standard,
            "standard_rank": self.standard_rank,
            "challenge_level": self.challenge_level,
            "challenge_notes": self.challenge_notes,
            "regulatory_items": self.regulatory_items,
            "marpol_notes": self.marpol_notes,
            "survey_risks": self.survey_risks,
            "references": self.references,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Main Module
# ─────────────────────────────────────────────────────────────────────────────

class HoldCleaningModule:
    """
    OceanDatum Hold Cleaning Intelligence Module.

    Provides structured analysis of bulk carrier hold cleaning requirements
    for cargo transitions, MARPOL compliance, and survey preparation.

    Knowledge base sourced from:
    - UK P&I Club, Skuld, West of England, Swedish Club, Japan P&I
    - IMO (MARPOL Annex V, IMSBC Code, International Grain Code)
    - USCG (NVIC 5-94, 3-97, FFVE Manual)
    - NCB (National Cargo Bureau)
    - Wilhelmsen Ships Service (Unitor/Navadan product guidance)
    - Bulkcarrierguide.com, Safety4Sea, HandyBulk
    """

    # Cleanliness standard hierarchy (rank 1 = strictest)
    STANDARDS = {
        "hospital clean":  {"rank": 1, "aliases": ["hospital", "stringent", "white glove"]},
        "grain clean":     {"rank": 2, "aliases": ["grain", "grain-clean", "food grade"]},
        "normal clean":    {"rank": 3, "aliases": ["normal", "standard clean"]},
        "shovel clean":    {"rank": 4, "aliases": ["shovel", "grab clean"]},
        "load on top":     {"rank": 5, "aliases": ["lot", "load-on-top"]},
    }

    # Cargo → required cleanliness standard
    CARGO_STANDARD_MAP = {
        "grain":            "grain clean",
        "wheat":            "grain clean",
        "corn":             "grain clean",
        "maize":            "grain clean",
        "barley":           "grain clean",
        "oats":             "grain clean",
        "rye":              "grain clean",
        "soybeans":         "grain clean",
        "soya meal":        "grain clean",
        "rapeseed":         "grain clean",
        "alumina":          "grain clean",
        "sulphur":          "grain clean",
        "cement":           "grain clean",
        "fertilizer":       "grain clean",
        "fertiliser":       "grain clean",
        "bauxite":          "grain clean",
        "concentrates":     "grain clean",
        "soda ash":         "hospital clean",
        "sodium carbonate": "hospital clean",
        "kaolin":           "hospital clean",
        "china clay":       "hospital clean",
        "mineral sands":    "hospital clean",
        "zircon":           "hospital clean",
        "rutile":           "hospital clean",
        "ilmenite":         "hospital clean",
        "barytes":          "hospital clean",
        "fluorspar":        "hospital clean",
        "chrome ore":       "hospital clean",
        "rice":             "hospital clean",
        "wood pulp":        "hospital clean",
        "coal":             "shovel clean",
        "iron ore":         "shovel clean",
        "petcoke":          "shovel clean",
        "pet coke":         "shovel clean",
        "ore":              "shovel clean",
    }

    # Cleaning challenge matrix (previous_cargo → challenge data)
    CHALLENGE_MAP = {
        "coal": {
            "level": "HIGH",
            "notes": [
                "Black dust + oily smear films contaminate all surfaces",
                "Staining on ledges and frame knees is persistent",
                "Going to grain: requires full chemical alkaline wash + fresh water rinse",
                "Unitor CargoClean HD (10% concentration) is industry standard for coal removal",
                "Apply foam with Panamax Kit; leave 10-15 min wet; rinse from bottom up",
                "MARPOL: CargoClean HD is NOT HME - can be discharged to sea with wash water",
            ],
            "time_estimate": "48-72 hours for post-Panamax vessel to grain clean",
        },
        "petcoke": {
            "level": "HIGH",
            "notes": [
                "High-sulfur, very oily residues - similar challenge to coal but harder staining",
                "Heavy-duty alkaline degreaser required at higher concentration",
                "Multiple wash cycles may be necessary",
                "Check MARPOL HME status of petcoke residues - may vary by grade",
            ],
            "time_estimate": "60-96 hours for grain clean on Panamax",
        },
        "pet coke": {
            "level": "HIGH",
            "notes": ["See petcoke entry above."],
            "time_estimate": "60-96 hours",
        },
        "cement": {
            "level": "HIGH",
            "notes": [
                "CRITICAL: DO NOT use bilge pump during cement washing - hardens in pipes",
                "Use portable salvage pump for all wash water removal",
                "Dry sweep thoroughly BEFORE any water contact",
                "Any moisture contact with cement creates concrete in bilge lines",
                "Full fresh water rinse required for grain clean after cement",
            ],
            "time_estimate": "36-60 hours (with portable pump setup)",
        },
        "cement clinker": {
            "level": "HIGH",
            "notes": [
                "Same precautions as cement - portable pump mandatory",
                "Clinker grinding into bilge creates significant concrete clog risk",
            ],
            "time_estimate": "36-60 hours",
        },
        "sulphur": {
            "level": "MEDIUM",
            "notes": [
                "⛔ PPE CRITICAL: sulphur dust + water = sulphurous acid (corrosive to lungs and steel)",
                "Full PPE: coveralls, goggles, respiratory protection for entire operation",
                "Thorough drying absolutely required - wet sulphur residues continue corrosion",
                "IMSBC Code: holds must be clean, dry, washed with fresh water after discharge",
                "Do NOT apply Unitor Slip-Coat before sulphur - moisture deteriorates film",
                "Use Navadan BarrierHold instead if protective barrier needed for sulphur",
            ],
            "time_estimate": "24-48 hours",
        },
        "fertilizer": {
            "level": "MEDIUM",
            "notes": [
                "Verify HME status of specific fertilizer grade for MARPOL wash water compliance",
                "Ammonium nitrate: oxidizing hazard during cleaning - keep away from organics/fuel",
                "Potash (MOP/SOP): typically non-HME but verify grade",
                "Thorough fresh water rinse required",
            ],
            "time_estimate": "24-36 hours",
        },
        "fertiliser": {
            "level": "MEDIUM",
            "notes": ["See fertilizer entry."],
            "time_estimate": "24-36 hours",
        },
        "fishmeal": {
            "level": "HIGH",
            "notes": [
                "Odor elimination is the primary challenge - penetrates coating",
                "Enzymatic cleaner required (protease/amylase + surfactant)",
                "Dwell time is critical - minimum 30 min contact time",
                "Warm water significantly improves enzymatic performance",
                "Maximum ventilation during and after cleaning",
                "Surveyor will often reject on odor alone - be aggressive with ventilation",
            ],
            "time_estimate": "48-72 hours including deodorization cycle",
        },
        "iron ore": {
            "level": "LOW",
            "notes": [
                "Iron ore residues relatively easy to clean for grain transition",
                "Standard alkaline wash + seawater wash + fresh water rinse",
                "Check for ore fines in bilge wells and pipe guards",
                "Rust staining from ore may require acid descaler on some surfaces",
            ],
            "time_estimate": "24-36 hours to grain clean",
        },
        "ore": {
            "level": "LOW",
            "notes": ["See iron ore entry."],
            "time_estimate": "24-36 hours",
        },
        "bauxite": {
            "level": "LOW",
            "notes": [
                "Relatively easy to clean - non-staining",
                "Check for packed bauxite dust in frames and behind ladders",
                "Standard wash procedure adequate for grain clean",
            ],
            "time_estimate": "18-30 hours",
        },
        "grain": {
            "level": "LOW",
            "notes": [
                "Clean transition from previous grain (same grade)",
                "Standard grain-clean protocol - sweep, wash, fresh water rinse",
                "Check for insect infestation from previous grain cargo",
                "Inspect for any moisture damage that could harbor mold/odor",
            ],
            "time_estimate": "12-24 hours",
        },
        "alumina": {
            "level": "MEDIUM",
            "notes": [
                "Fine white powder - penetrates into all crevices",
                "Compressed air blowing most effective if local regulations permit",
                "Thorough high-pressure wash required",
                "Check silver nitrate - alumina can mask chloride detection",
            ],
            "time_estimate": "24-36 hours",
        },
    }

    # Regulatory requirements by next cargo
    REGULATORY_MAP = {
        "grain": [
            "Document of Authorization (Grain Code) onboard and valid",
            "NCB Grain Certificate of Readiness (required all US ports)",
            "USDA cleanliness certificate (US load ports)",
            "Grain Loading Manual / Stability Booklet (NCB-stamped for US exports)",
            "Survey by independent surveyor (last 3 cargoes required)",
            "Fumigation certificate if infestation detected",
            "USCG NVIC 5-94 compliance (US flag / US port loading)",
            "IMSBC Code compliance for grain group",
        ],
        "soda ash": [
            "Hospital clean standard — surveyor inspection mandatory",
            "Confirm NO chemical cleaning agents used — fresh water ONLY",
            "IMSBC Code Group C compliance (soda ash schedule)",
            "Dust protection measures for crew and equipment",
        ],
        "coal": [
            "IMSBC Code schedule for specific coal type",
            "Determine Group A/B/C classification of specific coal",
            "If Group A: moisture content and TML testing required",
            "If Group B: gas detection and ventilation requirements",
            "Self-heating assessment for voyage route/duration",
            "MARPOL: verify HME status of coal residues before wash water discharge",
        ],
    }

    # MARPOL special areas
    MARPOL_SPECIAL_AREAS = [
        "Mediterranean Sea",
        "Baltic Sea",
        "Black Sea",
        "Red Sea",
        "Gulfs Area (Persian Gulf / Gulf of Oman / Gulf of Aden)",
        "North Sea",
        "Antarctic Area",
        "Wider Caribbean Region (including Gulf of Mexico)",
    ]

    # Known references
    REFERENCES = [
        {"name": "UK P&I Club — FAQ Hold Preparation and Cleaning (2021)",
         "url": "https://www.ukpandi.com/news-and-resources/articles/2021/faq-hold-preparation-and-cleaning/",
         "type": "pi_club"},
        {"name": "UK P&I Club — Carefully to Carry 2023 Ch.17",
         "url": "https://www.ukpandi.com/fileadmin/uploads/ukpandi/Documents/uk-p-i-club/carefully-to-carry/2023/UKPI_Carefully_to_Carry_2023_17.pdf",
         "type": "pi_club"},
        {"name": "Skuld P&I — Preparing Cargo Holds and Loading Solid Bulk Cargoes",
         "url": "https://www.skuld.com/contentassets/e2d486e683a84d7582fa1b867d18f8ac/preparing-cargo-holds_-loading-solid-bulk-cargoes.pdf",
         "type": "pi_club"},
        {"name": "Skuld P&I — Guidance on Disposal of Cargo Residues (MARPOL Annex V)",
         "url": "https://www.skuld.com/contentassets/ec787ec7bd6c49d99a5878b1d0769cfd/guidance_on_disposal_of_cargo_residues_in_line_with_marpol_annex_v-version2-2017october.pdf",
         "type": "pi_club"},
        {"name": "West of England P&I — Cargo Hold Cleaning LP Bulletin",
         "url": "https://www.westpandi.com/news-and-resources/loss-prevention-bulletins/cargo-hold-cleaning/",
         "type": "pi_club"},
        {"name": "Swedish Club — Practical Guide: Hold Cleaning of Bulk Vessels (2023)",
         "url": "https://www.swedishclub.com/uploads/2023/12/Cargo-Advice-Hold-cleaning-guide.pdf",
         "type": "pi_club"},
        {"name": "Japan P&I Club — Discharge of Cargo Residues under MARPOL Annex V",
         "url": "https://www.piclub.or.jp/en/news/11587",
         "type": "pi_club"},
        {"name": "USCG NVIC 5-94 — Grain Code Requirements for US Vessels",
         "url": "https://www.dco.uscg.mil/Portals/9/DCO%20Documents/5p/5ps/NVIC/1994/n5-94.pdf",
         "type": "regulatory"},
        {"name": "USCG NVIC 3-97 — ABS Authorization for Grain Stability",
         "url": "https://www.dco.uscg.mil/Portals/9/DCO%20Documents/5p/5ps/NVIC/1997/n3-97.pdf",
         "type": "regulatory"},
        {"name": "NCB — Grain Certificate of Readiness",
         "url": "https://natcargo.org/service/cgvs-grain-certificate-of-readiness/",
         "type": "regulatory"},
        {"name": "IMO — MARPOL Annex V Garbage Prevention",
         "url": "https://www.imo.org/en/ourwork/environment/pages/garbage-default.aspx",
         "type": "regulatory"},
        {"name": "Wilhelmsen — Preventing Cross-Contamination Between Cargoes",
         "url": "https://www.wilhelmsen.com/ships-service/tank-hold-cleaning/preventing-cross-contamination-between-cargoes/",
         "type": "technical"},
        {"name": "Bulkcarrierguide.com — Hold Cleaning Procedures",
         "url": "https://bulkcarrierguide.com/hold-cleaning.html",
         "type": "technical"},
        {"name": "Bulkcarrierguide.com — Soda Ash Handling",
         "url": "https://bulkcarrierguide.com/soda-ash-carrying.html",
         "type": "technical"},
        {"name": "BulkersGuide — MARPOL Annex V Cargo Residues Disposal",
         "url": "https://bulkersguide.com/section-5-4-disposal-of-cargo-residues-and-wash-water-marpol-annex-v/",
         "type": "technical"},
        {"name": "Safety4Sea — Hold Cleaning Guidance (Swedish Club)",
         "url": "https://safety4sea.com/guidance-published-for-hold-cleaning-of-bulk-vessels/",
         "type": "reference"},
        {"name": "ITOPF — How to Comply with MARPOL Annex V",
         "url": "https://www.itopf.org/fileadmin/uploads/itopf/data/Documents/TIPS%20TAPS/UK_CLUB_PRINT_MARPOL_July_2013_online_version.pdf",
         "type": "reference"},
        {"name": "CARGOWARD — Cargo Hold Cleaning Procedure for Bulk Carriers",
         "url": "https://www.cargoward.com/newsroom/cargo-hold-cleaning-procedure-for-bulk-carriers",
         "type": "reference"},
    ]

    SURVEY_FAILURE_RISKS = [
        "Loose rust scale exceeding USDA limits (>25 sq ft single area or >100 sq ft aggregate)",
        "Previous cargo residues trapped in frames, pipe guards, or behind ladders",
        "Salt residues from seawater wash without fresh water rinse (silver nitrate positive)",
        "Odour or taint from previous cargo or paint/chemicals",
        "Insect infestation (eggs, larvae, live insects anywhere in holds)",
        "Wet or damp holds — even partial moisture causes rejection",
        "Bilge covers missing, damaged, or not grain-tight",
        "Non-operational bilge suction system",
        "Loose paint flakes anywhere in hold interior",
        "Contamination in hatch cover drain channels or around seals",
        "High underdeck frame areas not cleaned (inaccessible without scaffold)",
        "Hatch cover undersides with residues (often missed)",
    ]

    def __init__(self, kb_path: Optional[Path] = None):
        """Initialize module. Optionally load extended knowledge base from file."""
        self._kb = None
        if kb_path and Path(kb_path).exists():
            with open(kb_path) as f:
                self._kb = json.load(f)

    def _normalize_cargo(self, cargo: str) -> str:
        return cargo.lower().strip()

    def _get_standard(self, cargo: str) -> tuple[str, int]:
        """Return (standard_name, rank) for a given cargo."""
        nc = self._normalize_cargo(cargo)
        # Direct match
        if nc in self.CARGO_STANDARD_MAP:
            std = self.CARGO_STANDARD_MAP[nc]
            return std, self.STANDARDS[std]["rank"]
        # Partial match
        for key, std in self.CARGO_STANDARD_MAP.items():
            if key in nc or nc in key:
                return std, self.STANDARDS[std]["rank"]
        # Default
        return "grain clean", 2

    def _get_challenge(self, previous_cargo: str) -> dict:
        nc = self._normalize_cargo(previous_cargo)
        if nc in self.CHALLENGE_MAP:
            return self.CHALLENGE_MAP[nc]
        # Partial match
        for key, data in self.CHALLENGE_MAP.items():
            if key in nc or nc in key:
                return data
        return {
            "level": "MEDIUM",
            "notes": [f"No specific protocol for '{previous_cargo}'. Apply standard cleaning. Verify with P&I club or technical manager."],
            "time_estimate": "24-48 hours estimated"
        }

    def cargo_transition_report(
        self,
        previous_cargo: str,
        next_cargo: str,
        vessel_type: str = "Panamax",
        load_port: str = "",
        ballast_days: Optional[float] = None,
        vessel_dwt: Optional[int] = None,
        include_all_phases: bool = True,
    ) -> HoldCleaningReport:
        """Generate a complete hold cleaning analysis for a cargo transition."""

        transition = CleaningTransition(
            previous_cargo=previous_cargo,
            next_cargo=next_cargo,
            vessel_type=vessel_type,
            load_port=load_port,
            ballast_days_available=ballast_days,
            vessel_dwt=vessel_dwt,
        )

        std_name, std_rank = self._get_standard(next_cargo)
        challenge = self._get_challenge(previous_cargo)

        # Build cleaning phases
        phases = self._build_cleaning_phases(
            previous_cargo=previous_cargo,
            next_cargo=next_cargo,
            std_name=std_name,
            include_all=include_all_phases,
        )

        # Regulatory items
        nc_next = self._normalize_cargo(next_cargo)
        reg_items = []
        for key, items in self.REGULATORY_MAP.items():
            if key in nc_next or nc_next in key:
                reg_items = items
                break
        if not reg_items:
            reg_items = [
                "Review charterparty cleanliness clause",
                f"Verify IMSBC Code schedule for {next_cargo}",
                "Determine HME status for MARPOL wash water compliance",
                f"Confirm surveyor requirements at {load_port or 'load port'}",
                "Log all hold cleaning activities with dates and methods",
                "Photograph cleaned holds before survey",
            ]

        # MARPOL notes
        marpol_notes = self._marpol_notes(previous_cargo)

        # Get relevant references
        refs = self._relevant_references(next_cargo, previous_cargo)

        report = HoldCleaningReport(
            transition=transition,
            required_standard=std_name,
            standard_rank=std_rank,
            challenge_level=challenge.get("level", "MEDIUM"),
            challenge_notes=challenge.get("notes", []),
            cleaning_phases=phases,
            regulatory_items=reg_items,
            marpol_notes=marpol_notes,
            survey_risks=self.SURVEY_FAILURE_RISKS,
            references=refs,
        )

        return report

    def _build_cleaning_phases(
        self, previous_cargo: str, next_cargo: str, std_name: str, include_all: bool = True
    ) -> list:
        """Construct ordered cleaning phases appropriate to transition."""
        phases = []
        nc_prev = self._normalize_cargo(previous_cargo)

        phases.append({
            "name": "Phase 1 — Immediate Post-Discharge",
            "steps": [
                "Protest to stevedores if cargo not discharged thoroughly — document with photos",
                "Remove all dunnage, lashing materials, timber immediately",
                "Initial dry sweep while hatches still open",
                "Open bilge covers, clean bilge wells of previous cargo",
                "Photograph all holds before departing discharge port",
            ]
        })

        phases.append({
            "name": "Phase 2 — Dry Cleaning",
            "steps": [
                "Mechanical sweep all surfaces: tank top, frames, hoppers, bulkheads",
                "Air blowing where local regulations permit (most effective for dust cargoes)",
                "Scrape frame knees, tripping brackets, pipe guards, behind ladders",
                "Clean underdeck frames and coaming frames (use scaffold on large vessels)",
                "Sweep hatch cover undersides thoroughly",
                "Collect all residues — dispose per MARPOL Annex V (bag for shore if HME)",
            ]
        })

        # Chemical phase - only if not a clean-to-clean transition
        nc_challenges_needing_chem = ["coal", "petcoke", "pet coke", "cement", "fishmeal", "fertilizer", "fertiliser", "sulphur"]
        needs_chem = any(c in nc_prev for c in nc_challenges_needing_chem)

        if needs_chem:
            chem_data = self.CHALLENGE_MAP.get(nc_prev, {})
            phases.append({
                "name": "Phase 3 — Chemical Wash",
                "steps": chem_data.get("notes", ["Apply appropriate chemical cleaner per cargo type"]) + [
                    "Apply chemical from top of hold walls downward",
                    "Leave 10-15 minutes — keep surfaces wet during contact time",
                    "High-pressure washdown from bottom upward",
                ]
            })

        # Seawater wash
        phases.append({
            "name": "Phase 4 — Seawater Wash",
            "steps": [
                "High-pressure seawater wash all surfaces — bottom to top",
                "Keep bilge strainers in place throughout — never remove during washing",
                "Pump bilge water ONLY if MARPOL-compliant (position, HME status, distance from land)",
                "Record all discharge in Garbage Record Book Part II",
            ]
        })

        # Fresh water rinse - always
        fw_qty = "~30 tonnes per hatch (110,000 DWT reference)" if "panamax" in self._normalize_cargo("panamax") else "consult vessel specs"
        phases.append({
            "name": "Phase 5 — Fresh Water Rinse  ★ CRITICAL",
            "steps": [
                f"Fresh water final rinse of all surfaces before holds dry — {fw_qty}",
                "Rinse while still wet from seawater wash — easier salt removal",
                "Flush fire main with fresh water first to clear salt from piping",
                "Silver nitrate test after rinse — confirms chloride removal",
                "No salt residues: prevents cargo contamination, corrosion, surveyor rejection",
            ]
        })

        # Drying
        phases.append({
            "name": "Phase 6 — Drying & Ventilation",
            "steps": [
                "Maximum forced ventilation until holds completely dry",
                "Check daily — all moisture must be eliminated before survey",
                "Hold must be odour-free before loading (ventilate aggressively)",
            ]
        })

        # Hospital clean extra step for soda ash / hospital-clean cargoes
        if "hospital" in std_name:
            phases.append({
                "name": "Phase 7 — Hospital Clean Verification",
                "steps": [
                    "Inspect ALL paint coating surfaces — 100% intact required",
                    "Check ladder rungs, pipe fittings, underside of hatch covers",
                    "Zero rust tolerance — no loose rust anywhere",
                    "Zero paint flake tolerance anywhere",
                    "Surveyor check will be more stringent than grain clean",
                    "For soda ash: no chemical cleaning agents — fresh water ONLY",
                ]
            })

        # Pre-survey checks
        phases.append({
            "name": "Phase 8 — Pre-Survey Close-Out",
            "steps": [
                "Inspect ALL bilge wells: open, clean, dry, grain-tight covers",
                "Bilge suction test: dry suck ONLY — do not introduce water before survey",
                "Hatch cover inspection: rubbers, drain channels, seals, compression",
                "White glove / cloth wipe test across representative surfaces",
                "Check for insect infestation in all areas",
                "Photograph all holds from hatch opening",
                "Brief crew to stand by for immediate remediation during survey",
            ]
        })

        return phases

    def _marpol_notes(self, previous_cargo: str) -> list:
        nc = self._normalize_cargo(previous_cargo)
        notes = [
            "MARPOL Annex V (amended Jan 1, 2013): Default PROHIBITION on all garbage discharge at sea.",
            "Cargo residues entrained in wash water treated as cargo residues — subject to same rules.",
            "Determine HME (Harmful to Marine Environment) status of cargo residues before any discharge.",
        ]

        # Cargo-specific notes
        if "coal" in nc or "petcoke" in nc or "pet coke" in nc:
            notes.append("Coal/petcoke: Typically non-HME for most grades. Verify with shipper declaration. Unitor CargoClean HD confirmed non-HME.")
        elif "fertilizer" in nc or "fertiliser" in nc:
            notes.append("Fertilizers: HME status varies by type. Ammonium nitrate solutions may be HME. Request shipper classification.")
        elif "fishmeal" in nc:
            notes.append("Fishmeal: Verify HME status. Enzymatic cleaners must also be verified non-HME before sea discharge.")

        notes += [
            "Non-HME discharge outside Special Areas: ship must be EN ROUTE, minimum 12nm from nearest land/ice shelf.",
            "Inside MARPOL Special Areas (Med, Baltic, Caribbean, etc.): discharge generally PROHIBITED.",
            "Cleaning agents/additives: may be discharged only if confirmed NOT harmful to marine environment.",
            "Record all discharge in Garbage Record Book Part II (Category 4) with start/stop positions.",
            "US enforcement: criminal liability for officers. Some ports require lab analysis of wash water.",
        ]
        return notes

    def _relevant_references(self, next_cargo: str, previous_cargo: str) -> list:
        """Return most relevant references for this transition."""
        nc_next = self._normalize_cargo(next_cargo)
        selected = []

        # Always include key P&I and regulatory
        priority = ["UK P&I Club", "Skuld P&I", "Swedish Club", "West of England", "NCB", "USCG"]
        for ref in self.REFERENCES:
            if any(p.lower() in ref["name"].lower() for p in priority):
                selected.append(ref)

        # Add cargo-specific
        if "soda ash" in nc_next or "sodium carbonate" in nc_next:
            for ref in self.REFERENCES:
                if "soda ash" in ref["name"].lower():
                    selected.append(ref)

        if "grain" in nc_next:
            for ref in self.REFERENCES:
                if "grain" in ref["url"].lower() or "grain" in ref["name"].lower():
                    if ref not in selected:
                        selected.append(ref)

        # MARPOL always
        for ref in self.REFERENCES:
            if "marpol" in ref["name"].lower() and ref not in selected:
                selected.append(ref)

        # Deduplicate
        seen = set()
        out = []
        for ref in selected:
            if ref["url"] not in seen:
                seen.add(ref["url"])
                out.append(ref)

        return out[:12]  # Cap at 12

    def get_standard_for_cargo(self, cargo: str) -> dict:
        """Return cleanliness standard info for a cargo."""
        std_name, rank = self._get_standard(cargo)
        return {
            "cargo": cargo,
            "required_standard": std_name,
            "rank": rank,
            "description": self._standard_description(std_name),
        }

    def _standard_description(self, std_name: str) -> str:
        descs = {
            "hospital clean": "100% intact paint on ALL surfaces. Zero rust tolerance. Zero paint flakes. Strictest standard; normally only achievable by dedicated clean-cargo vessels.",
            "grain clean": "Clean, swept, washed with fresh water. Free from insects, odour, cargo residues, loose rust scale, paint flakes. Dried and ventilated. Most common standard.",
            "normal clean": "Residues removed, double swept, seawater washed, fresh water rinsed, dried.",
            "shovel clean": "Mechanically cleaned, cargo residues removed by grab/shovel. Minimum standard for dirty cargo trades.",
            "load on top": "Cargo loaded directly on residues from identical previous cargo. COA trades only.",
        }
        return descs.get(std_name, "See knowledge base for full specification.")

    def marpol_quick_check(self, cargo: str, inside_special_area: bool = False) -> dict:
        """Quick MARPOL Annex V compliance determination."""
        nc = self._normalize_cargo(cargo)
        # Simple HME inference (not definitive - always verify with shipper)
        hme_indicators = ["fertilizer", "fertiliser", "ammonium", "phosphate", "chemical"]
        likely_hme = any(h in nc for h in hme_indicators)

        result = {
            "cargo": cargo,
            "likely_hme": likely_hme,
            "inside_special_area": inside_special_area,
            "discharge_permitted": False,
            "conditions": [],
            "warning": "",
        }

        if likely_hme:
            result["discharge_permitted"] = False
            result["warning"] = "Likely HME cargo — discharge of residues at sea PROHIBITED. Must use port reception facility."
        elif inside_special_area:
            result["discharge_permitted"] = False
            result["warning"] = "Inside MARPOL Special Area — discharge of cargo residues generally PROHIBITED."
        else:
            result["discharge_permitted"] = True
            result["conditions"] = [
                "Ship must be EN ROUTE (underway)",
                "Minimum 12nm from nearest land or ice shelf",
                "Residues non-recoverable by commonly available methods",
                "Cleaning agents must also be non-HME",
                "Record in Garbage Record Book Part II",
            ]

        result["important_caveat"] = "This is a preliminary check only. Always verify HME status with shipper declaration, IMSBC Code, and P&I club before discharging."
        return result

    def all_sources(self, source_type: Optional[str] = None) -> list:
        """Return filtered list of all authoritative sources."""
        if source_type:
            return [r for r in self.REFERENCES if r.get("type") == source_type]
        return self.REFERENCES

    def attach_to_reporter(self, reporter_instance):
        """
        Attach this module to an existing OceanDatum reporter.
        
        Expected interface:
            reporter.register_module(name, module)
            reporter.add_report_type(name, generator_fn)
        """
        try:
            reporter_instance.register_module("hold_cleaning", self)
            reporter_instance.add_report_type(
                "hold_cleaning_analysis",
                lambda prev, nxt, **kwargs: self.cargo_transition_report(prev, nxt, **kwargs).to_dict()
            )
            print("[HoldCleaningModule] Attached to reporter successfully.")
        except AttributeError as e:
            print(f"[HoldCleaningModule] Could not attach to reporter: {e}")
            print("  Ensure reporter has register_module() and add_report_type() methods.")


# ─────────────────────────────────────────────────────────────────────────────
# Standalone demo
# ─────────────────────────────────────────────────────────────────────────────

def _demo():
    print("\n" + "="*76)
    print("  OceanDatum Hold Cleaning Module — Demo")
    print("="*76)

    mod = HoldCleaningModule()

    # Demo 1: Coal to Grain (most common challenging transition)
    print("\n[Demo 1] Coal → Grain transition (Panamax, Hampton Roads VA)")
    report = mod.cargo_transition_report(
        previous_cargo="coal",
        next_cargo="grain",
        vessel_type="Panamax",
        load_port="Hampton Roads, VA",
        ballast_days=3.5,
        vessel_dwt=75000,
    )
    print(report.text_summary())

    # Demo 2: Soda ash lookup
    print("\n[Demo 2] Soda Ash standard lookup")
    info = mod.get_standard_for_cargo("soda ash")
    print(f"  Cargo:     {info['cargo']}")
    print(f"  Standard:  {info['required_standard']}")
    print(f"  Rank:      {info['rank']} (1=strictest)")
    print(f"  Desc:      {info['description']}")

    # Demo 3: MARPOL quick check
    print("\n[Demo 3] MARPOL quick check — fertilizer cargo residues")
    marpol = mod.marpol_quick_check("fertilizer", inside_special_area=False)
    print(f"  Cargo:    {marpol['cargo']}")
    print(f"  Likely HME: {marpol['likely_hme']}")
    print(f"  Discharge OK: {marpol['discharge_permitted']}")
    print(f"  Warning:  {marpol['warning']}")
    print(f"  Caveat:   {marpol['important_caveat']}")

    print("\n" + "="*76)
    print("  Demo complete. Import HoldCleaningModule for full integration.")
    print("="*76 + "\n")


if __name__ == "__main__":
    _demo()
