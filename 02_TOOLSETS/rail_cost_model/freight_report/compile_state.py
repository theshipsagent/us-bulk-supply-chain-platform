"""
Phase 4a: Compile per-state profile dicts from extracted RAG chunks + waybill enrichment.
Synthesizes raw chunks into narrative text sections for each topic.
"""

import logging
import re

from .config import STATES_46, TOPICS

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
log = logging.getLogger(__name__)

# Max chars of extracted text to include per topic
MAX_EXCERPT_CHARS = 2000


def _clean_excerpt(text):
    """Clean up chunk text for report inclusion."""
    # Remove page markers
    text = re.sub(r'---\s*Page\s*\d+\s*---', '', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Trim broken start: chunks from overlapping windows often begin mid-sentence.
    # Find the LAST sentence boundary within the first ~150 chars and skip to it.
    # Using the last boundary (not first) avoids stopping at abbreviations mid-fragment.
    boundaries = list(re.finditer(r'[.!?]\s+([A-Z])', text[:200]))
    if boundaries:
        # Use the last boundary within the first 150 chars
        trim_candidates = [m for m in boundaries if m.start() < 150]
        if trim_candidates:
            best = trim_candidates[-1]
            text = text[best.end() - 1:]  # start from the capital letter
    elif text and not text[0].isupper():
        # Starts lowercase / mid-word with no boundary in first 200 chars:
        # look further for any boundary
        match = re.search(r'[.!?]\s+([A-Z])', text)
        if match and match.start() < len(text) // 2:
            text = text[match.end() - 1:]

    return text.strip()


def _format_number(val):
    """Format a number with commas, handling None/0."""
    if val is None or val == 0:
        return "N/A"
    try:
        return f"{float(val):,.0f}"
    except (ValueError, TypeError):
        return str(val)


def _synthesize_topic(topic_key, chunks, state_name):
    """
    Synthesize extracted chunks into a topic narrative.
    Returns a string with 1-3 paragraphs of content.
    """
    if not chunks:
        return f"No specific data on {TOPICS[topic_key]['title'].lower()} was identified in available sources for {state_name}."

    # Combine excerpts, preferring state-source chunks
    paragraphs = []
    chars_used = 0

    for chunk in chunks:
        excerpt = _clean_excerpt(chunk["text"])
        if not excerpt:
            continue

        # Truncate individual excerpts to end at a sentence boundary
        if len(excerpt) > 500:
            cutoff = excerpt[:500].rfind('. ')
            if cutoff > 200:
                excerpt = excerpt[:cutoff + 1]
            else:
                excerpt = excerpt[:500] + "..."
        else:
            # Even short excerpts: trim to last complete sentence
            last_period = excerpt.rfind('. ')
            if last_period > len(excerpt) // 3:
                excerpt = excerpt[:last_period + 1]

        if chars_used + len(excerpt) > MAX_EXCERPT_CHARS:
            break

        paragraphs.append(excerpt)
        chars_used += len(excerpt)

    if not paragraphs:
        return f"No specific data on {TOPICS[topic_key]['title'].lower()} was identified in available sources for {state_name}."

    return "\n\n".join(paragraphs)


def _format_waybill_section(enrichment, state_name):
    """Format waybill enrichment data as a text section."""
    vol = enrichment.get("waybill_total_volume", {})
    total_tons = vol.get("total_tons", 0)
    total_carloads = vol.get("total_carloads", 0)
    total_revenue = vol.get("total_revenue", 0)

    if not total_tons and not total_carloads:
        return "Waybill data for this state was not available or had insufficient coverage in the STB Public Use Waybill Sample."

    lines = []

    # Volume summary
    lines.append(f"According to the STB Public Use Waybill Sample, {state_name} originating "
                 f"rail freight totaled approximately {_format_number(total_tons)} expanded tons "
                 f"across {_format_number(total_carloads)} expanded carloads"
                 + (f", generating approximately ${_format_number(total_revenue)} in freight revenue."
                    if total_revenue else "."))

    # Top commodities
    commodities = enrichment.get("waybill_top_commodities", [])
    if commodities:
        lines.append("")
        lines.append("Top Commodities by Tonnage (Origin):")
        for c in commodities[:5]:
            lines.append(f"  - {c['commodity']}: {_format_number(c['tons'])} tons "
                        f"({_format_number(c['carloads'])} carloads)")

    # Top O-D pairs
    od_pairs = enrichment.get("waybill_top_od_pairs", [])
    if od_pairs:
        lines.append("")
        lines.append("Top Origin-Destination Pairs:")
        for od in od_pairs[:3]:
            lines.append(f"  - {od['origin']} -> {od['destination']}: "
                        f"{_format_number(od['tons'])} tons")

    # Car types
    car_types = enrichment.get("waybill_car_types", [])
    if car_types:
        lines.append("")
        lines.append("Primary Car Types:")
        for ct in car_types[:5]:
            lines.append(f"  - {ct['car_type']}: {_format_number(ct['carloads'])} carloads")

    return "\n".join(lines)


def _get_plan_year(state_abbr):
    """Attempt to determine the plan year from the chunk metadata."""
    # These are approximate years from filenames in download_state_rail_plans.py
    plan_years = {
        "AL": None, "AK": None, "AZ": 2022, "AR": 2025, "CA": 2024, "CO": 2024,
        "CT": 2022, "DE": None, "FL": 2023, "GA": 2021, "IA": 2022, "ID": None,
        "IL": 2023, "IN": 2021, "KS": 2022, "KY": 2025, "LA": None, "MA": 2018,
        "MD": None, "ME": 2023, "MI": None, "MN": None, "MO": 2022, "MS": None,
        "MT": 2010, "NC": 2025, "ND": 2023, "NH": 2012, "NJ": 2012, "NM": 2018,
        "NV": None, "OH": 2025, "OK": 2021, "OR": None, "PA": 2020, "RI": 2014,
        "SC": 2024, "SD": 2022, "TN": 2019, "TX": None, "UT": 2015, "VT": 2021,
        "WA": 2019, "WV": 2020, "WI": 2023, "WY": 2021,
    }
    return plan_years.get(state_abbr)


def _classify_tier(extraction):
    """Classify state into reporting tier based on data richness."""
    total_chunks = sum(len(v) for v in extraction.values())
    topics_with_data = sum(1 for v in extraction.values() if v)

    if total_chunks >= 20 and topics_with_data >= 7:
        return 1  # Full coverage: 2-3 pages
    elif total_chunks >= 10 and topics_with_data >= 4:
        return 2  # Moderate: 1-2 pages
    else:
        return 3  # Minimal: 1 page


def compile_profile(state_abbr, extraction, enrichment):
    """
    Assemble a complete state profile dict from extraction + enrichment.

    Args:
        state_abbr: e.g. "IA"
        extraction: {topic_key: [chunk_dicts]} from extract.py
        enrichment: waybill data dict from enrich.py

    Returns:
        Complete state profile dict.
    """
    state_name = STATES_46[state_abbr]
    tier = _classify_tier(extraction)

    profile = {
        "state_name": state_name,
        "state_abbr": state_abbr,
        "plan_year": _get_plan_year(state_abbr),
        "tier": tier,
    }

    # Synthesize each topic from RAG chunks
    for topic_key in TOPICS:
        chunks = extraction.get(topic_key, [])
        profile[topic_key] = _synthesize_topic(topic_key, chunks, state_name)

    # Format waybill data
    profile["waybill_summary"] = _format_waybill_section(enrichment, state_name)

    # Store raw enrichment for PDF table formatting
    profile["waybill_top_commodities"] = enrichment.get("waybill_top_commodities", [])
    profile["waybill_top_od_pairs"] = enrichment.get("waybill_top_od_pairs", [])
    profile["waybill_car_types"] = enrichment.get("waybill_car_types", [])
    profile["waybill_total_volume"] = enrichment.get("waybill_total_volume", {})

    return profile


def compile_all_profiles(extractions, enrichments):
    """
    Compile profiles for all states, sorted alphabetically.
    Returns list of profile dicts.
    """
    profiles = []
    for abbr in sorted(STATES_46.keys()):
        state_name = STATES_46[abbr]
        log.info("Compiling profile for %s (%s)...", state_name, abbr)
        extraction = extractions.get(abbr, {})
        enrichment = enrichments.get(abbr, {
            "waybill_top_commodities": [],
            "waybill_top_od_pairs": [],
            "waybill_car_types": [],
            "waybill_total_volume": {"total_carloads": 0, "total_tons": 0, "total_revenue": 0},
        })
        profiles.append(compile_profile(abbr, extraction, enrichment))

    tier_counts = {1: 0, 2: 0, 3: 0}
    for p in profiles:
        tier_counts[p["tier"]] += 1
    log.info("Profile tiers: Tier 1 (full): %d, Tier 2 (moderate): %d, Tier 3 (minimal): %d",
             tier_counts[1], tier_counts[2], tier_counts[3])

    return profiles
