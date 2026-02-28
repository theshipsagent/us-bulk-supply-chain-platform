"""
End-to-end test: Domestic Supply Chain data via Census EITS API.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from census_trade.clients.econ_indicators import EconIndicatorsAPI
from census_trade.tools.supply_chain import SupplyChainTool
from census_trade.config.eits_codes import PROGRAMS, DATA_TYPES, SUPPLY_CHAIN_PROGRAMS


def test_eits_api_basic():
    """Test basic EITS API connectivity and response format."""
    print("=" * 60)
    print("TEST: EITS API - Basic Connectivity")
    print("=" * 60)

    api = EconIndicatorsAPI()

    print(f"  Available programs: {len(PROGRAMS)}")
    print(f"  Supply chain programs: {len(SUPPLY_CHAIN_PROGRAMS)}")
    for k, v in SUPPLY_CHAIN_PROGRAMS.items():
        print(f"    {k:10s} -> {v['name']}")

    # Test M3 single-month query
    df = api.query("m3", data_type="VS", category="MTM", year=2024, month=6)
    print(f"\n  M3 Total Mfg Shipments (2024-06):")
    print(f"    Rows: {len(df)}")
    print(f"    Value: ${df['cell_value'].iloc[0]:,.0f} million")
    assert len(df) > 0
    assert df["cell_value"].iloc[0] > 0

    print("  PASSED\n")


def test_manufacturing_data():
    """Test manufacturing data retrieval."""
    print("=" * 60)
    print("TEST: Manufacturing Data (M3)")
    print("=" * 60)

    api = EconIndicatorsAPI()

    # Shipments time series
    ship = api.manufacturing_shipments(start_year=2024, end_year=2024)
    print(f"  Mfg Shipments 2024: {len(ship)} months")
    if not ship.empty:
        print(f"    Range: ${ship['cell_value'].min():,.0f}M - ${ship['cell_value'].max():,.0f}M")

    # New Orders
    orders = api.manufacturing_new_orders(start_year=2024, end_year=2024)
    print(f"  Mfg New Orders 2024: {len(orders)} months")

    # Inventories
    inv = api.manufacturing_inventories(start_year=2024, end_year=2024)
    print(f"  Mfg Inventories 2024: {len(inv)} months")

    # Unfilled Orders (backlog)
    backlog = api.manufacturing_unfilled_orders(start_year=2024, end_year=2024)
    print(f"  Mfg Unfilled Orders 2024: {len(backlog)} months")

    assert len(ship) >= 10, f"Expected >=10 months, got {len(ship)}"
    print("  PASSED\n")


def test_wholesale_data():
    """Test wholesale trade data retrieval."""
    print("=" * 60)
    print("TEST: Wholesale Trade Data (MWTS)")
    print("=" * 60)

    api = EconIndicatorsAPI()

    sales = api.wholesale_sales(start_year=2024, end_year=2024)
    print(f"  Wholesale Sales 2024: {len(sales)} months")
    if not sales.empty:
        print(f"    Range: ${sales['cell_value'].min():,.0f}M - ${sales['cell_value'].max():,.0f}M")

    inv = api.wholesale_inventories(start_year=2024, end_year=2024)
    print(f"  Wholesale Inventories 2024: {len(inv)} months")

    assert len(sales) >= 10
    print("  PASSED\n")


def test_retail_data():
    """Test retail trade data retrieval."""
    print("=" * 60)
    print("TEST: Retail Trade Data (MRTS)")
    print("=" * 60)

    api = EconIndicatorsAPI()

    sales = api.retail_sales(start_year=2024, end_year=2024)
    print(f"  Retail Sales 2024: {len(sales)} months")
    if not sales.empty:
        print(f"    Range: ${sales['cell_value'].min():,.0f}M - ${sales['cell_value'].max():,.0f}M")

    inv = api.retail_inventories(start_year=2024, end_year=2024)
    print(f"  Retail Inventories 2024: {len(inv)} months")

    assert len(sales) >= 10
    print("  PASSED\n")


def test_supply_chain_pipeline():
    """Test the full supply chain pipeline snapshot."""
    print("=" * 60)
    print("TEST: Supply Chain Pipeline Snapshot")
    print("=" * 60)

    tool = SupplyChainTool()

    snapshot = tool.pipeline_snapshot(2024, 6)
    print("  Pipeline Snapshot (2024-06):")
    print(snapshot.to_string(index=False))

    assert len(snapshot) == 3
    assert snapshot["sales_shipments"].sum() > 0
    print("  PASSED\n")


def test_manufacturing_overview():
    """Test manufacturing comprehensive overview."""
    print("=" * 60)
    print("TEST: Manufacturing Overview")
    print("=" * 60)

    tool = SupplyChainTool()

    overview = tool.manufacturing_overview(2024, 6)
    print("  Manufacturing Metrics (2024-06):")
    print(overview.to_string(index=False))

    assert len(overview) == 8
    print("  PASSED\n")


def test_inventory_breakdown():
    """Test manufacturing inventory breakdown."""
    print("=" * 60)
    print("TEST: Manufacturing Inventory Breakdown")
    print("=" * 60)

    tool = SupplyChainTool()

    breakdown = tool.inventory_breakdown(2024, 6)
    print("  Inventory Breakdown (2024-06):")
    print(breakdown.to_string(index=False))

    assert len(breakdown) == 4
    print("  PASSED\n")


def test_is_ratio_trend():
    """Test inventory-to-sales ratio time series."""
    print("=" * 60)
    print("TEST: I/S Ratio Trend (2023-2024)")
    print("=" * 60)

    tool = SupplyChainTool()

    trend = tool.is_ratio_trend(start_year=2023, end_year=2024)
    print(f"  I/S Ratio data points: {len(trend)}")
    if not trend.empty:
        print(f"  Latest values:")
        print(trend.tail(3).to_string(index=False))

    assert len(trend) >= 20
    print("  PASSED\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DOMESTIC SUPPLY CHAIN - END-TO-END TESTS")
    print("=" * 60 + "\n")

    test_eits_api_basic()
    test_manufacturing_data()
    test_wholesale_data()
    test_retail_data()
    test_supply_chain_pipeline()
    test_manufacturing_overview()
    test_inventory_breakdown()
    test_is_ratio_trend()

    print("\n" + "=" * 60)
    print("ALL SUPPLY CHAIN TESTS PASSED")
    print("=" * 60)
