"""
End-to-end test: Download real Census data and validate parsers.

Downloads a small port data ZIP (~7-10MB) and a merchandise export ZIP,
parses them, and verifies the data looks correct.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from census_trade.config.url_patterns import build_url, PORT_EXPORTS_HS6, MERCHANDISE_EXPORTS, ALL_BULK_PRODUCTS
from census_trade.config.record_layouts import get_layout, get_record_length, FILE_LAYOUTS
from census_trade.clients.downloader import CensusDownloader
from census_trade.parsers.fixed_width import parse_file, parse_directory
from census_trade.parsers.ports import PortParser
from census_trade.parsers.merchandise import MerchandiseParser
from census_trade.parsers.concordance import ConcordanceLoader


def test_url_builder():
    """Test URL generation."""
    print("=" * 60)
    print("TEST: URL Builder")
    print("=" * 60)

    url = build_url(MERCHANDISE_EXPORTS, 2025, month=6)
    expected = "https://www.census.gov/trade/downloads/2025/Merch/ex_m/EXDB2506.ZIP"
    assert url == expected, f"Expected {expected}, got {url}"
    print(f"  Merchandise exports 2025-06: {url}")

    url = build_url(PORT_EXPORTS_HS6, 2025, month=1)
    expected = "https://www.census.gov/trade/downloads/2025/Port/ex_hs6_m/PORTHS6XM2501.ZIP"
    assert url == expected, f"Expected {expected}, got {url}"
    print(f"  Port exports HS6 2025-01:    {url}")

    print(f"  All bulk products registered: {len(ALL_BULK_PRODUCTS)}")
    print("  PASSED\n")


def test_record_layouts():
    """Verify record layout definitions."""
    print("=" * 60)
    print("TEST: Record Layouts")
    print("=" * 60)

    for name, layout in FILE_LAYOUTS.items():
        rec_len = get_record_length(layout)
        field_count = len(layout)
        print(f"  {name:15s} -> {field_count:3d} fields, {rec_len:4d} bytes")

    # Spot check some known lengths
    assert get_record_length(FILE_LAYOUTS["EXP_DETL"]) == 323
    assert get_record_length(FILE_LAYOUTS["IMP_DETL"]) == 688
    assert get_record_length(FILE_LAYOUTS["DPORTHS6E"]) == 230
    assert get_record_length(FILE_LAYOUTS["CONCORD"]) == 235
    assert get_record_length(FILE_LAYOUTS["IMP_COMM"]) == 732
    print("  PASSED\n")


def test_port_data_download():
    """Download and parse real port export data."""
    print("=" * 60)
    print("TEST: Port Exports HS6 - Real Data Download & Parse")
    print("=" * 60)

    dl = CensusDownloader()
    extract_dir = dl.fetch_port_exports(2025, 1)

    parser = PortParser(extract_dir)
    df = parser.parse_exports()

    print(f"  Rows:    {len(df):,}")
    print(f"  Columns: {list(df.columns)}")
    print(f"  Dtypes:\n{df.dtypes.to_string()}")
    print(f"\n  Sample (first 5 rows):")
    print(df.head().to_string())

    # Validate data
    assert len(df) > 1000, f"Expected >1000 rows, got {len(df)}"
    assert "commodity" in df.columns
    assert "port_code" in df.columns
    assert "value_mo" in df.columns
    assert df["value_mo"].sum() > 0, "Total value should be > 0"

    # Top ports
    top = parser.top_ports(df, n=10)
    print(f"\n  Top 10 export ports by value:")
    print(top.to_string())

    # Transport mode split
    transport = parser.transport_mode_split(df)
    print(f"\n  Transport mode split (top 5 ports):")
    print(transport.head().to_string())

    print("  PASSED\n")


def test_merchandise_export_download():
    """Download and parse real merchandise export data."""
    print("=" * 60)
    print("TEST: Merchandise Exports - Real Data Download & Parse")
    print("=" * 60)

    dl = CensusDownloader()
    extract_dir = dl.fetch_merchandise_exports(2025, 1)

    # List what's in the ZIP
    files = {f.stem.upper(): f for f in extract_dir.iterdir()}
    print(f"  Extracted files: {list(files.keys())}")

    parser = MerchandiseParser(extract_dir)

    # Test concordance
    print(f"\n  Concordance:")
    print(f"    Countries: {len(parser.lookups.countries)}")
    print(f"    Districts: {len(parser.lookups.districts)}")
    print(f"    Concordance: {len(parser.lookups.concordance)}")
    print(f"    HS Descriptions: {len(parser.lookups.hs_descriptions)}")
    print(f"    NAICS: {len(parser.lookups.naics)}")

    # Parse country-level exports
    cty = parser.parse_export_country()
    print(f"\n  Export by country: {len(cty)} rows")
    top_cty = cty.nlargest(10, "all_val_mo")[["cty_code", "cty_name", "all_val_mo"]]
    print(f"  Top 10 export destinations:")
    print(top_cty.to_string())

    # Parse commodity-level
    comm = parser.parse_export_commodity()
    print(f"\n  Export by commodity: {len(comm)} rows")
    top_comm = comm.nlargest(10, "all_val_mo")[["commodity", "comm_desc", "all_val_mo"]]
    print(f"  Top 10 export commodities:")
    print(top_comm.to_string())

    # Parse detail (this is the big one)
    detl = parser.parse_export_detail()
    print(f"\n  Export detail: {len(detl):,} rows")
    print(f"  Total export value (monthly): ${detl['all_val_mo'].sum():,.0f}")

    # Enrich with descriptions
    detl_enriched = parser.enrich_with_descriptions(detl.head(100))
    print(f"\n  Enriched detail sample (first 5):")
    cols = ["commodity", "commodity_desc", "cty_code", "cty_name", "all_val_mo"]
    available_cols = [c for c in cols if c in detl_enriched.columns]
    print(detl_enriched[available_cols].head().to_string())

    print("  PASSED\n")


def test_parse_directory():
    """Test parsing all files in a directory at once."""
    print("=" * 60)
    print("TEST: Parse Directory (all files)")
    print("=" * 60)

    dl = CensusDownloader()
    extract_dir = dl.fetch_merchandise_exports(2025, 1)

    results = parse_directory(extract_dir)
    print(f"  Parsed {len(results)} files:")
    for name, df in results.items():
        print(f"    {name:15s} -> {len(df):>8,} rows x {len(df.columns)} cols")

    print("  PASSED\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CENSUS TRADE MODULE - END-TO-END TESTS")
    print("=" * 60 + "\n")

    test_url_builder()
    test_record_layouts()
    test_port_data_download()
    test_merchandise_export_download()
    test_parse_directory()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
