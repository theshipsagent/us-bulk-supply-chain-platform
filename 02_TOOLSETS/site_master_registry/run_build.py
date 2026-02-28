#!/usr/bin/env python3
"""Run the Site Master Registry build pipeline.

Usage:
    python run_build.py                          # Phase 1 (default)
    python run_build.py --phase 1                # Explicit phase 1
    python run_build.py --frs-local /tmp/frs.db  # Use local FRS copy (faster)

Note: If the FRS database is on Google Drive, copy it locally first:
    cp 02_TOOLSETS/facility_registry/data/frs.duckdb /tmp/frs_local.duckdb
    python run_build.py --frs-local /tmp/frs_local.duckdb
"""

import argparse
import logging
import sys
from pathlib import Path

# Ensure the package is importable
sys.path.insert(0, str(Path(__file__).parent))

from src.registry.builder import RegistryBuilder


def main():
    parser = argparse.ArgumentParser(description="Site Master Registry Builder")
    parser.add_argument("--phase", type=int, default=1, help="Build phase (1-4)")
    parser.add_argument("--max-tier", type=int, default=1,
                        help="NAICS tier filter for Phase 2 (1=strategic, 2=all)")
    parser.add_argument("--frs-local", type=str, default=None,
                        help="Path to local FRS DuckDB copy (avoids Google Drive I/O)")
    parser.add_argument("--project-root", type=str, default=".",
                        help="Project root directory")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s %(levelname)s: %(message)s",
    )

    builder = RegistryBuilder(args.project_root, frs_db_override=args.frs_local)

    if args.phase == 1:
        builder.build_phase_1()
    elif args.phase == 2:
        builder.build_phase_2(max_tier=args.max_tier)
    elif args.phase == 3:
        builder.build_phase_3()
    else:
        print(f"Phase {args.phase} not yet implemented")
        sys.exit(1)


if __name__ == "__main__":
    main()
