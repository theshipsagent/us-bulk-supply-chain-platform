"""Import tariff cost-through model.

Calculates the impact of US import tariffs on landed cost for bulk
commodities. Handles HTS-specific duty rates, anti-dumping duties (ADD),
countervailing duties (CVD), and trade preference programs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TariffRate:
    """Tariff rate structure for an HTS code."""
    hts_code: str
    description: str
    general_duty_pct: float         # MFN (Column 1 General) rate
    special_programs: dict[str, float] = field(default_factory=dict)  # e.g. {"GSP": 0.0}
    column2_rate_pct: float = 0.0   # Column 2 rate (Cuba, North Korea)
    unit: str = "ad_valorem"        # "ad_valorem", "specific", "compound"
    specific_rate: float = 0.0      # $/ton for specific duties
    notes: str = ""


@dataclass
class ADDCVDRate:
    """Anti-dumping / countervailing duty rate for a country-product pair."""
    hts_code: str
    country: str
    add_pct: float = 0.0            # anti-dumping duty %
    cvd_pct: float = 0.0            # countervailing duty %
    effective_date: str = ""
    case_number: str = ""
    notes: str = ""


# ---------------------------------------------------------------------------
# Reference tariff data: Cement & cementitious materials
# ---------------------------------------------------------------------------

CEMENT_TARIFFS: dict[str, TariffRate] = {
    "2523.10": TariffRate(
        hts_code="2523.10",
        description="Cement clinkers",
        general_duty_pct=0.0,
        notes="Duty free MFN",
    ),
    "2523.21": TariffRate(
        hts_code="2523.21",
        description="White portland cement",
        general_duty_pct=0.0,
        notes="Duty free MFN",
    ),
    "2523.29": TariffRate(
        hts_code="2523.29",
        description="Other portland cement",
        general_duty_pct=0.0,
        notes="Duty free MFN — the main import category",
    ),
    "2523.30": TariffRate(
        hts_code="2523.30",
        description="Aluminous cement",
        general_duty_pct=0.0,
    ),
    "2523.90": TariffRate(
        hts_code="2523.90",
        description="Other hydraulic cements",
        general_duty_pct=0.0,
    ),
    "2618.00": TariffRate(
        hts_code="2618.00",
        description="Granulated slag (slag sand)",
        general_duty_pct=0.0,
        notes="Duty free — used as GGBFS/slag cement",
    ),
    "2621.00": TariffRate(
        hts_code="2621.00",
        description="Other slag and ash (including fly ash)",
        general_duty_pct=0.0,
        notes="Duty free — fly ash, bottom ash",
    ),
    "6810.11": TariffRate(
        hts_code="6810.11",
        description="Concrete blocks and bricks",
        general_duty_pct=3.2,
    ),
    "6810.19": TariffRate(
        hts_code="6810.19",
        description="Concrete tiles, flagstones, etc.",
        general_duty_pct=3.2,
    ),
}


# ADD/CVD orders relevant to cement sector
CEMENT_ADD_CVD: list[ADDCVDRate] = [
    # Note: As of 2025, no active ADD/CVD orders on cement from major origins.
    # Turkey, Egypt, Vietnam are primary import sources — currently no duties.
    # This is a monitoring list for potential future actions.
]


# ---------------------------------------------------------------------------
# Common commodity tariff summaries
# ---------------------------------------------------------------------------

COMMODITY_TARIFF_SUMMARY: dict[str, dict[str, Any]] = {
    "cement": {
        "hts_chapter": "2523",
        "general_duty": "Free",
        "add_cvd": "None active",
        "section_301": "N/A (not Chinese origin dominated)",
        "major_origins": ["Turkey", "Egypt", "Vietnam", "Greece", "China"],
    },
    "steel": {
        "hts_chapter": "72-73",
        "general_duty": "0-6.5%",
        "add_cvd": "Active on many origins",
        "section_232": "25% tariff on most steel",
        "major_origins": ["Canada", "Mexico", "Brazil", "South Korea", "Japan"],
    },
    "aluminum": {
        "hts_chapter": "76",
        "general_duty": "0-6.5%",
        "section_232": "10% tariff",
        "major_origins": ["Canada", "UAE", "Russia", "China", "India"],
    },
}


@dataclass
class LandedCostBreakdown:
    """Complete landed cost breakdown including tariffs."""
    commodity: str
    hts_code: str
    origin_country: str
    cargo_tons: float

    # Cost components ($/ton)
    fob_price_per_ton: float
    ocean_freight_per_ton: float
    insurance_per_ton: float
    cif_per_ton: float

    # Duty components
    general_duty_pct: float
    general_duty_per_ton: float
    add_pct: float
    add_per_ton: float
    cvd_pct: float
    cvd_per_ton: float
    section_301_per_ton: float
    section_232_per_ton: float
    total_duty_per_ton: float

    # Port and delivery
    port_charges_per_ton: float
    inland_freight_per_ton: float

    # Totals
    total_landed_per_ton: float
    total_landed_cost: float
    duty_as_pct_of_landed: float


def calculate_landed_cost(
    commodity: str,
    hts_code: str,
    origin_country: str,
    cargo_tons: float,
    fob_price_per_ton: float,
    ocean_freight_per_ton: float,
    insurance_pct: float = 0.5,
    port_charges_per_ton: float = 8.00,
    inland_freight_per_ton: float = 15.00,
    section_301_per_ton: float = 0.0,
    section_232_pct: float = 0.0,
) -> LandedCostBreakdown:
    """Calculate full landed cost including all tariff components.

    Parameters
    ----------
    commodity : str
        Commodity type for tariff lookup.
    hts_code : str
        HTS code (e.g. "2523.29").
    origin_country : str
        Country of origin.
    cargo_tons : float
        Shipment quantity in metric tons.
    fob_price_per_ton : float
        FOB (Free on Board) price at origin.
    ocean_freight_per_ton : float
        Ocean freight rate.
    insurance_pct : float
        Marine cargo insurance as % of FOB+freight.
    port_charges_per_ton : float
        Destination port charges per ton.
    inland_freight_per_ton : float
        Inland delivery cost per ton.
    section_301_per_ton : float
        Section 301 fee allocated per ton.
    section_232_pct : float
        Section 232 tariff percentage (0 if not applicable).
    """
    # CIF calculation
    insurance_per_ton = (fob_price_per_ton + ocean_freight_per_ton) * (insurance_pct / 100)
    cif = fob_price_per_ton + ocean_freight_per_ton + insurance_per_ton

    # Tariff lookup
    tariff = CEMENT_TARIFFS.get(hts_code)
    general_duty_pct = tariff.general_duty_pct if tariff else 0.0
    general_duty = cif * (general_duty_pct / 100)

    # ADD/CVD lookup
    add_pct = 0.0
    cvd_pct = 0.0
    for order in CEMENT_ADD_CVD:
        if order.hts_code == hts_code and order.country.lower() == origin_country.lower():
            add_pct = order.add_pct
            cvd_pct = order.cvd_pct

    add_per_ton = cif * (add_pct / 100)
    cvd_per_ton = cif * (cvd_pct / 100)

    # Section 232
    s232_per_ton = cif * (section_232_pct / 100)

    total_duty = general_duty + add_per_ton + cvd_per_ton + section_301_per_ton + s232_per_ton

    total_landed = cif + total_duty + port_charges_per_ton + inland_freight_per_ton
    total_cost = total_landed * cargo_tons
    duty_pct = (total_duty / total_landed * 100) if total_landed > 0 else 0

    return LandedCostBreakdown(
        commodity=commodity,
        hts_code=hts_code,
        origin_country=origin_country,
        cargo_tons=cargo_tons,
        fob_price_per_ton=round(fob_price_per_ton, 2),
        ocean_freight_per_ton=round(ocean_freight_per_ton, 2),
        insurance_per_ton=round(insurance_per_ton, 2),
        cif_per_ton=round(cif, 2),
        general_duty_pct=general_duty_pct,
        general_duty_per_ton=round(general_duty, 2),
        add_pct=add_pct,
        add_per_ton=round(add_per_ton, 2),
        cvd_pct=cvd_pct,
        cvd_per_ton=round(cvd_per_ton, 2),
        section_301_per_ton=round(section_301_per_ton, 2),
        section_232_per_ton=round(s232_per_ton, 2),
        total_duty_per_ton=round(total_duty, 2),
        port_charges_per_ton=round(port_charges_per_ton, 2),
        inland_freight_per_ton=round(inland_freight_per_ton, 2),
        total_landed_per_ton=round(total_landed, 2),
        total_landed_cost=round(total_cost, 2),
        duty_as_pct_of_landed=round(duty_pct, 1),
    )


def compare_origins(
    hts_code: str,
    cargo_tons: float,
    fob_price_per_ton: float,
    origins: list[dict[str, Any]],
) -> list[LandedCostBreakdown]:
    """Compare landed cost across multiple origin countries.

    Each origin dict should have: country, ocean_freight_per_ton,
    and optionally section_301_per_ton, section_232_pct.
    """
    results = []
    for origin in origins:
        lc = calculate_landed_cost(
            commodity="cement",
            hts_code=hts_code,
            origin_country=origin["country"],
            cargo_tons=cargo_tons,
            fob_price_per_ton=fob_price_per_ton,
            ocean_freight_per_ton=origin.get("ocean_freight_per_ton", 25.0),
            port_charges_per_ton=origin.get("port_charges_per_ton", 8.0),
            inland_freight_per_ton=origin.get("inland_freight_per_ton", 15.0),
            section_301_per_ton=origin.get("section_301_per_ton", 0.0),
            section_232_pct=origin.get("section_232_pct", 0.0),
        )
        results.append(lc)
    results.sort(key=lambda x: x.total_landed_per_ton)
    return results
