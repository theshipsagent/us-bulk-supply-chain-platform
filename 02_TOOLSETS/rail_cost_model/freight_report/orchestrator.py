"""
Main pipeline orchestration for the Freight Rail Analysis Report.

Usage:
    python -X utf8 -m freight_report.orchestrator          # Full pipeline
    python -X utf8 -m freight_report.orchestrator --skip-download   # Skip federal downloads
    python -X utf8 -m freight_report.orchestrator --skip-enrich     # Skip waybill enrichment
"""

import argparse
import logging
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from .config import STATES_46, OUTPUT_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Generate Freight Rail Analysis Report")
    parser.add_argument("--skip-download", action="store_true",
                        help="Skip federal report download (Phase 1)")
    parser.add_argument("--skip-enrich", action="store_true",
                        help="Skip waybill enrichment (Phase 3)")
    parser.add_argument("--states", nargs="*", default=None,
                        help="Process only specific states (e.g., IA OH PA)")
    args = parser.parse_args()

    start_time = time.time()

    print()
    print("=" * 80)
    print("  FREIGHT RAIL ANALYSIS REPORT GENERATOR")
    print("=" * 80)
    print()

    # Determine which states to process
    if args.states:
        states_to_process = {s: STATES_46[s] for s in args.states if s in STATES_46}
        if not states_to_process:
            log.error("No valid states specified. Available: %s", ", ".join(sorted(STATES_46)))
            sys.exit(1)
        log.info("Processing %d states: %s", len(states_to_process),
                 ", ".join(sorted(states_to_process)))
    else:
        states_to_process = STATES_46

    # ── Phase 1: Download Federal Reports (optional) ──────────────────────────
    if not args.skip_download:
        print("\n--- Phase 1: Download Federal Reports ---\n")
        try:
            from .download_federal import download_federal_reports
            download_federal_reports()
        except Exception as e:
            log.warning("Phase 1 failed (non-critical): %s", e)
            log.info("Continuing with existing data...")
    else:
        log.info("Skipping Phase 1 (federal downloads)")

    # ── Phase 2: Extract Topics from RAG ──────────────────────────────────────
    print("\n--- Phase 2: Extract Topics from RAG ---\n")
    from read_rail.rag_system_rail import RailRAG

    rag = RailRAG()
    rag.build_index()

    from .extract import extract_topics
    extractions = {}
    total = len(states_to_process)
    for i, (abbr, name) in enumerate(sorted(states_to_process.items()), 1):
        log.info("[%d/%d] Extracting topics for %s (%s)...", i, total, name, abbr)
        extractions[abbr] = extract_topics(rag, abbr, name)
        topic_count = sum(1 for v in extractions[abbr].values() if v)
        chunk_count = sum(len(v) for v in extractions[abbr].values())
        log.info("  -> %d topics with data, %d total chunks", topic_count, chunk_count)

    # ── Phase 3: Enrich with DuckDB Waybill Data ─────────────────────────────
    if not args.skip_enrich:
        print("\n--- Phase 3: Enrich with Waybill Data ---\n")
        from .enrich import enrich_all_states, _empty_enrichment
        import duckdb
        from .config import DB_PATH

        if DB_PATH.exists():
            con = duckdb.connect(str(DB_PATH), read_only=True)
            try:
                con.execute("SELECT 1 FROM fact_waybill LIMIT 1")
                con.close()
                # Re-open for actual queries via enrich module
                enrichments = {}
                con = duckdb.connect(str(DB_PATH), read_only=True)
                from .enrich import enrich_from_waybill
                for i, (abbr, name) in enumerate(sorted(states_to_process.items()), 1):
                    log.info("[%d/%d] Enriching %s (%s) from waybill...", i, total, name, abbr)
                    enrichments[abbr] = enrich_from_waybill(con, abbr)
                    vol = enrichments[abbr]["waybill_total_volume"]
                    log.info("  -> %s tons, %s carloads",
                             f"{vol['total_tons']:,.0f}" if vol["total_tons"] else "0",
                             f"{vol['total_carloads']:,.0f}" if vol["total_carloads"] else "0")
                con.close()
            except Exception as e:
                log.warning("Waybill table not available: %s", e)
                enrichments = {abbr: _empty_enrichment() for abbr in states_to_process}
        else:
            log.warning("DuckDB not found at %s", DB_PATH)
            from .enrich import _empty_enrichment
            enrichments = {abbr: _empty_enrichment() for abbr in states_to_process}
    else:
        log.info("Skipping Phase 3 (waybill enrichment)")
        from .enrich import _empty_enrichment
        enrichments = {abbr: _empty_enrichment() for abbr in states_to_process}

    # ── Phase 4: Compile Profiles + Generate HTML ─────────────────────────────
    print("\n--- Phase 4: Compile Profiles & Generate HTML ---\n")
    from .compile_state import compile_profile
    from .generate_html import generate_html

    profiles = []
    for abbr in sorted(states_to_process.keys()):
        name = states_to_process[abbr]
        log.info("Compiling profile for %s (%s)...", name, abbr)
        extraction = extractions.get(abbr, {})
        enrichment = enrichments.get(abbr, {
            "waybill_top_commodities": [],
            "waybill_top_od_pairs": [],
            "waybill_car_types": [],
            "waybill_total_volume": {"total_carloads": 0, "total_tons": 0, "total_revenue": 0},
        })
        profiles.append(compile_profile(abbr, extraction, enrichment))

    output_path = generate_html(profiles)

    elapsed = time.time() - start_time

    print()
    print("=" * 80)
    print(f"  REPORT COMPLETE")
    print(f"  States:   {len(profiles)}")
    print(f"  Output:   {output_path}")
    print(f"  Size:     {output_path.stat().st_size / 1024:.1f} KB")
    print(f"  Time:     {elapsed:.1f} seconds")
    print("=" * 80)


if __name__ == "__main__":
    main()
