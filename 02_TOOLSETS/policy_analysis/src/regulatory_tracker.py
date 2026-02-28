"""Maritime and trade regulatory change tracker.

Tracks active and pending regulatory actions that impact US bulk
commodity supply chain operations. Provides structured lookups
for policy analysis and report generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class RegulatoryAction:
    """A tracked regulatory action or policy change."""
    action_id: str
    title: str
    agency: str                     # USTR, USCG, MARAD, EPA, STB, USACE, CBP
    status: str                     # proposed, final_rule, effective, expired, withdrawn
    category: str                   # trade, environmental, safety, economic, maritime
    effective_date: str = ""
    comment_deadline: str = ""
    federal_register_cite: str = ""
    impact_summary: str = ""
    affected_commodities: list[str] = field(default_factory=list)
    affected_modes: list[str] = field(default_factory=list)  # barge, rail, vessel, truck
    estimated_cost_impact: str = ""
    url: str = ""
    notes: str = ""


# ---------------------------------------------------------------------------
# Active regulatory actions (as of early 2026)
# ---------------------------------------------------------------------------

REGULATORY_ACTIONS: list[RegulatoryAction] = [
    RegulatoryAction(
        action_id="USTR-2025-301",
        title="Section 301 Maritime Shipping Fees on Chinese-Built Vessels",
        agency="USTR",
        status="effective",
        category="trade",
        effective_date="2025-10-01",
        impact_summary=(
            "Per-voyage or per-NRT fees on Chinese-built, -operated, or -owned vessels "
            "calling US ports. Phases in over 3 years. Bulk carriers face $500K-$1M per "
            "voyage at full implementation."
        ),
        affected_commodities=["all_imports"],
        affected_modes=["vessel"],
        estimated_cost_impact="$5-50/ton depending on vessel and cargo",
        url="https://ustr.gov/issue-areas/enforcement/section-301-investigations",
    ),
    RegulatoryAction(
        action_id="USCG-2024-BWMS",
        title="Ballast Water Management Standards — Implementation Phase",
        agency="USCG",
        status="effective",
        category="environmental",
        effective_date="2024-01-01",
        impact_summary=(
            "All vessels must install type-approved BWMS by compliance date. "
            "Increases vessel operating costs and may affect older tonnage availability."
        ),
        affected_commodities=["all"],
        affected_modes=["vessel"],
        estimated_cost_impact="$500K-2M installation per vessel (one-time)",
    ),
    RegulatoryAction(
        action_id="EPA-2025-TIER4",
        title="EPA Tier 4 Marine Engine Standards",
        agency="EPA",
        status="effective",
        category="environmental",
        effective_date="2025-01-01",
        impact_summary=(
            "New marine diesel engines must meet Tier 4 emission standards. "
            "Increases newbuild costs for towboats and harbour craft."
        ),
        affected_commodities=["all"],
        affected_modes=["barge", "vessel"],
        estimated_cost_impact="10-15% increase in new engine costs",
    ),
    RegulatoryAction(
        action_id="STB-2025-RECIPROCAL",
        title="Reciprocal Railroad Switching Access",
        agency="STB",
        status="proposed",
        category="economic",
        impact_summary=(
            "Proposed rule requiring Class I railroads to provide reciprocal "
            "switching access at certain terminals. Would increase competition "
            "and potentially lower rail rates for captive shippers."
        ),
        affected_commodities=["all_rail"],
        affected_modes=["rail"],
        estimated_cost_impact="Potential 5-15% rail rate reduction for captive shippers",
    ),
    RegulatoryAction(
        action_id="USACE-2025-LOCK",
        title="Inland Waterway Lock Modernization Funding (IIJA)",
        agency="USACE",
        status="effective",
        category="economic",
        effective_date="2022-01-01",
        impact_summary=(
            "Infrastructure Investment and Jobs Act provides $2.5B for inland "
            "waterway construction including Chickamauga Lock, Kentucky Lock, "
            "and LaGrange Lock. Will reduce delays and improve barge transit."
        ),
        affected_commodities=["all_waterway"],
        affected_modes=["barge"],
        estimated_cost_impact="Long-term reduction in lock delays (5-15%)",
    ),
    RegulatoryAction(
        action_id="CBP-2025-UFLPA",
        title="Uyghur Forced Labor Prevention Act — Cement/Building Materials",
        agency="CBP",
        status="effective",
        category="trade",
        effective_date="2022-06-21",
        impact_summary=(
            "Rebuttable presumption that goods from Xinjiang are produced with forced "
            "labor. Some building materials and industrial inputs may be detained. "
            "Importers must demonstrate supply chain due diligence."
        ),
        affected_commodities=["solar_panels", "industrial_inputs", "building_materials"],
        affected_modes=["vessel"],
        estimated_cost_impact="Compliance costs; potential delays at port of entry",
    ),
    RegulatoryAction(
        action_id="MARAD-2025-MSP",
        title="Maritime Security Program Reauthorization",
        agency="MARAD",
        status="effective",
        category="maritime",
        effective_date="2025-01-01",
        impact_summary=(
            "Continues stipend payments to US-flag vessel operators maintaining "
            "vessels in international trade. Supports ~60 vessels. Indirectly "
            "supports Jones Act fleet by maintaining US maritime workforce."
        ),
        affected_commodities=["defense_logistics"],
        affected_modes=["vessel"],
    ),
]


def get_active_actions(
    category: str | None = None,
    agency: str | None = None,
    mode: str | None = None,
    commodity: str | None = None,
) -> list[RegulatoryAction]:
    """Filter regulatory actions by criteria."""
    results = []
    for action in REGULATORY_ACTIONS:
        if action.status in ("expired", "withdrawn"):
            continue
        if category and action.category != category:
            continue
        if agency and action.agency != agency:
            continue
        if mode and mode not in action.affected_modes:
            continue
        if commodity:
            if commodity not in action.affected_commodities and "all" not in action.affected_commodities:
                matching = any(
                    commodity in ac or "all" in ac
                    for ac in action.affected_commodities
                )
                if not matching:
                    continue
        results.append(action)
    return results


def get_action_summary() -> list[dict[str, Any]]:
    """Return a summary table of all tracked actions."""
    return [
        {
            "id": a.action_id,
            "title": a.title,
            "agency": a.agency,
            "status": a.status,
            "category": a.category,
            "effective": a.effective_date,
            "modes": a.affected_modes,
            "impact": a.estimated_cost_impact,
        }
        for a in REGULATORY_ACTIONS
    ]


def assess_voyage_regulatory_exposure(
    vessel_flag: str,
    vessel_builder_country: str,
    cargo_commodity: str,
    origin_country: str,
    destination_port: str,
    transport_mode: str = "vessel",
) -> list[dict[str, Any]]:
    """Assess which regulatory actions apply to a specific voyage.

    Returns a list of applicable actions with relevance notes.
    """
    applicable = []

    for action in REGULATORY_ACTIONS:
        if action.status in ("expired", "withdrawn"):
            continue

        relevance = None

        # Section 301 — Chinese nexus
        if action.action_id == "USTR-2025-301":
            if vessel_builder_country.lower() in ("china", "prc"):
                relevance = "Vessel is Chinese-built — Section 301 fees apply"
            elif origin_country.lower() in ("china", "prc"):
                relevance = "Chinese origin cargo — monitor for vessel operator nexus"

        # BWMS — all vessels
        elif action.action_id == "USCG-2024-BWMS":
            if transport_mode == "vessel":
                relevance = "Vessel must have type-approved BWMS installed"

        # STB reciprocal switching — rail only
        elif action.action_id == "STB-2025-RECIPROCAL":
            if transport_mode == "rail":
                relevance = "Proposed rule may affect rail rate negotiations"

        # UFLPA
        elif action.action_id == "CBP-2025-UFLPA":
            if origin_country.lower() in ("china", "prc"):
                relevance = "Chinese origin — UFLPA supply chain due diligence required"

        if relevance:
            applicable.append({
                "action_id": action.action_id,
                "title": action.title,
                "agency": action.agency,
                "status": action.status,
                "relevance": relevance,
                "cost_impact": action.estimated_cost_impact,
            })

    return applicable
