"""Master CLI for the US Bulk Supply Chain Reporting Platform.

Usage:
    report-platform data status
    report-platform data download --source epa_frs
    report-platform data ingest --source epa_frs
    report-platform barge-cost --origin Houston --destination Memphis
    report-platform barge-cost --origin-river "MISSISSIPPI RIVER" --origin-mile 800 \
                               --dest-river "MISSISSIPPI RIVER" --dest-mile 100
    report-platform barge-cost --list-rivers
    report-platform barge-cost forecast --weeks 4
    report-platform rail-cost --miles 600 --tons 500 --cars 5
    report-platform port-cost --port "New Orleans" --cargo cement --tons 30000 --draft 38.5
    report-platform port-cost --list-ports
    report-platform facility-search --state LA --naics 327310
    report-platform facility-search --state LA --naics 327310 --lat 30.0 --lon -90.0 --radius 50
    report-platform policy section-301 --vessel-type bulk --nrt 20000 --category chinese_built
    report-platform policy landed-cost --hts 2523.29 --origin Turkey --fob 55 --freight 25
    report-platform policy regulatory --commodity cement
    report-platform report generate --report us_bulk_supply_chain --format docx
    report-platform commodity list
    report-platform commodity init --name grain
    report-platform db status
    report-platform db init
"""

import sys
from pathlib import Path

import click

from report_platform import __version__
from report_platform.config import get_project_root

# Add toolsets to path so their modules are importable
_toolsets_dir = get_project_root() / "02_TOOLSETS"
if str(_toolsets_dir) not in sys.path:
    sys.path.insert(0, str(_toolsets_dir))


# ---------------------------------------------------------------------------
# Well-known barge locations: friendly name -> (river, mile)
# Upper Mississippi: Mile 0 = Cairo/Ohio confluence, miles increase north
# Ohio River: Mile 0 = Pittsburgh, miles increase downstream/west
# Illinois River: Mile 0 = confluence w/ Mississippi, miles increase north
# ---------------------------------------------------------------------------
_BARGE_LOCATIONS: dict[str, tuple[str, float]] = {
    "minneapolis":  ("MISSISSIPPI RIVER", 858.0),
    "st paul":      ("MISSISSIPPI RIVER", 840.0),
    "la crosse":    ("MISSISSIPPI RIVER", 700.0),
    "dubuque":      ("MISSISSIPPI RIVER", 580.0),
    "davenport":    ("MISSISSIPPI RIVER", 480.0),
    "st louis":     ("MISSISSIPPI RIVER", 185.0),
    "cairo":        ("MISSISSIPPI RIVER", 0.0),
    "chicago":      ("ILLINOIS RIVER", 327.0),
    "peoria":       ("ILLINOIS RIVER", 162.0),
    "pittsburgh":   ("OHIO RIVER", 0.0),
    "wheeling":     ("OHIO RIVER", 91.0),
    "huntington":   ("OHIO RIVER", 306.0),
    "cincinnati":   ("OHIO RIVER", 470.0),
    "louisville":   ("OHIO RIVER", 604.0),
    "evansville":   ("OHIO RIVER", 792.0),
    "paducah":      ("OHIO RIVER", 918.0),
}


def _normalize_loc(name: str) -> str:
    """Normalize a location name for lookup."""
    return name.lower().strip().replace("_", " ").replace("-", " ").replace(".", "")


def _resolve_location(name: str) -> tuple[str, float] | None:
    """Resolve a friendly location name to (river, mile)."""
    key = _normalize_loc(name)
    for loc_key, val in _BARGE_LOCATIONS.items():
        if key == loc_key or key == loc_key.replace(" ", ""):
            return val
    return None


@click.group()
@click.version_option(version=__version__, prog_name="report-platform")
def cli():
    """US Bulk Supply Chain Reporting Platform.

    Unified toolset for inland waterway, port, rail, pipeline, and vessel
    infrastructure analysis with pluggable commodity modules.
    """


# ---------------------------------------------------------------------------
# DATA commands
# ---------------------------------------------------------------------------
@cli.group()
def data():
    """Data source management — download, ingest, and status tracking."""


@data.command("status")
@click.option("--source", default=None, help="Check a specific source (default: all).")
@click.option("--verbose", "-v", is_flag=True, help="Show file-level detail.")
def data_status(source: str | None, verbose: bool):
    """Show freshness status of all configured data sources."""
    from report_platform.data_tracker import show_data_status
    show_data_status(source=source, verbose=verbose)


@data.command("download")
@click.option("--source", required=True, help="Data source key from config.yaml.")
@click.option("--force", is_flag=True, help="Re-download even if fresh.")
def data_download(source: str, force: bool):
    """Download raw data for a configured source."""
    click.echo(f"Downloading source: {source} (force={force})")
    click.echo("Not yet implemented — will integrate per-source downloaders.")


@data.command("ingest")
@click.option("--source", required=True, help="Data source key from config.yaml.")
def data_ingest(source: str):
    """Ingest downloaded data into DuckDB analytics database."""
    click.echo(f"Ingesting source: {source}")
    click.echo("Not yet implemented — will build ETL pipelines.")


# ---------------------------------------------------------------------------
# PORT-COST command (wired to port_cost_model toolset)
# ---------------------------------------------------------------------------
@cli.command("port-cost")
@click.option("--port", default=None, help="Port name (e.g., 'New Orleans', 'Houston').")
@click.option("--cargo", default="general", help="Cargo type (cement, steel, grain, bulk_dry, etc.).")
@click.option("--tons", default=30000.0, type=float, help="Cargo tonnage.")
@click.option("--draft", default=35.0, type=float, help="Vessel draft in feet.")
@click.option("--loa", default=590.0, type=float, help="Vessel LOA in feet.")
@click.option("--gt", default=32000, type=int, help="Vessel gross tonnage.")
@click.option("--dwt", default=55000, type=int, help="Vessel deadweight tonnage.")
@click.option("--days", default=3, type=int, help="Days alongside.")
@click.option("--vessel-name", default="TBN", help="Vessel name.")
@click.option("--list-ports", is_flag=True, help="List known ports with pilotage routes.")
@click.option("--list-routes", is_flag=True, help="List available pilotage route templates.")
def port_cost(port: str | None, cargo: str, tons: float, draft: float, loa: float,
              gt: int, dwt: int, days: int, vessel_name: str,
              list_ports: bool, list_routes: bool):
    """Generate a proforma port cost estimate."""
    if list_ports or list_routes:
        from port_cost_model.src.pilotage_calculator import PILOTAGE_ZONES, ROUTE_TEMPLATES
        from port_cost_model.src.proforma_generator import _PORT_PILOTAGE_MAP

        if list_ports:
            click.echo("\nKnown ports and default pilotage routes:")
            click.echo(f"  {'Port':<25} {'Default Route':<25}")
            click.echo("  " + "-" * 50)
            for port_key, route in sorted(_PORT_PILOTAGE_MAP.items()):
                click.echo(f"  {port_key:<25} {route:<25}")

        if list_routes:
            click.echo("\nPilotage route templates:")
            click.echo(f"  {'Route':<25} Zones")
            click.echo("  " + "-" * 60)
            for route_name, zones in sorted(ROUTE_TEMPLATES.items()):
                zone_names = [PILOTAGE_ZONES[z].name for z in zones if z in PILOTAGE_ZONES]
                click.echo(f"  {route_name:<25} {' -> '.join(zone_names)}")
        return

    if not port:
        click.echo("Error: --port is required (or use --list-ports to see options).")
        return

    from port_cost_model.src.proforma_generator import generate_proforma, format_proforma_text
    pf = generate_proforma(
        vessel_name=vessel_name,
        port=port,
        cargo_type=cargo,
        cargo_tons=tons,
        vessel_loa_feet=loa,
        vessel_draft_feet=draft,
        vessel_gt=gt,
        vessel_dwt=dwt,
        days_alongside=days,
    )
    click.echo(format_proforma_text(pf))


# ---------------------------------------------------------------------------
# BARGE-COST commands
# ---------------------------------------------------------------------------
@cli.group("barge-cost", invoke_without_command=True)
@click.option("--origin", default=None, help="Origin city name (see --list-locations).")
@click.option("--destination", default=None, help="Destination city name.")
@click.option("--origin-river", default=None, help="Origin river name (exact match from data).")
@click.option("--origin-mile", default=None, type=float, help="Origin mile marker.")
@click.option("--dest-river", default=None, help="Destination river name (exact match from data).")
@click.option("--dest-mile", default=None, type=float, help="Destination mile marker.")
@click.option("--tons", default=22500, type=int,
              help="Total cargo tonnage (default: 22,500 for 15-barge tow).")
@click.option("--tow-config", default="15-barge",
              help="Tow configuration (15-barge, 6-barge).")
@click.option("--speed", default=None, type=float, help="Override average speed in mph.")
@click.option("--list-rivers", is_flag=True, help="List available rivers with mile ranges.")
@click.option("--list-locations", is_flag=True, help="List well-known location aliases.")
@click.pass_context
def barge_cost(ctx, origin, destination, origin_river, origin_mile, dest_river,
               dest_mile, tons, tow_config, speed, list_rivers, list_locations):
    """Calculate barge freight cost between two waterway locations.

    \b
    Two input modes:
      1. Named locations:  --origin Minneapolis --destination "St Louis"
      2. River + mile:     --origin-river "MISSISSIPPI RIVER" --origin-mile 800
                           --dest-river "MISSISSIPPI RIVER" --dest-mile 100

    Use --list-rivers to see available rivers from loaded network data.
    Use --list-locations to see the built-in name-to-river lookup table.
    """
    if ctx.invoked_subcommand is not None:
        return

    # --list-locations requires no data load
    if list_locations:
        click.echo("\nWell-known barge locations:")
        click.echo(f"  {'Name':<20} {'River':<25} {'Mile':>8}")
        click.echo("  " + "-" * 55)
        for name, (river, mile) in sorted(_BARGE_LOCATIONS.items()):
            click.echo(f"  {name.title():<20} {river:<25} {mile:>8.1f}")
        click.echo("\nUse --list-rivers for all rivers from the waterway network data.")
        return

    # Everything below needs the calculator
    try:
        from barge_cost_model.barge_cost_calculator import BargeCostCalculator
    except ImportError:
        click.echo("Error: barge_cost_model not importable.")
        click.echo(f"  Checked: {_toolsets_dir}")
        return

    calc = BargeCostCalculator()
    click.echo("Loading barge cost data...")
    status = calc.load_data()
    for k, v in status.items():
        click.echo(f"  {k}: {v}")

    # --list-rivers
    if list_rivers:
        click.echo(f"\n{'River':<35} {'Min Mile':>10} {'Max Mile':>10} {'Locks':>6}")
        click.echo("-" * 65)
        for river in calc.get_rivers():
            lo, hi = calc.get_mile_range(river)
            n_locks = len(calc.get_locks_on_river(river))
            click.echo(f"  {river:<33} {lo:>10.1f} {hi:>10.1f} {n_locks:>6}")
        return

    # Resolve origin
    o_river, o_mile = origin_river, origin_mile
    if origin and not o_river:
        resolved = _resolve_location(origin)
        if resolved is None:
            click.echo(f"Error: Unknown location '{origin}'.")
            click.echo("Use --list-locations to see aliases, or specify --origin-river and --origin-mile.")
            return
        o_river, o_mile = resolved

    # Resolve destination
    d_river, d_mile = dest_river, dest_mile
    if destination and not d_river:
        resolved = _resolve_location(destination)
        if resolved is None:
            click.echo(f"Error: Unknown location '{destination}'.")
            click.echo("Use --list-locations to see aliases, or specify --dest-river and --dest-mile.")
            return
        d_river, d_mile = resolved

    # Validate we have everything
    if not all([o_river, o_mile is not None, d_river, d_mile is not None]):
        click.echo("Error: Provide --origin/--destination (named) or "
                    "--origin-river/--origin-mile and --dest-river/--dest-mile.")
        click.echo("Run: report-platform barge-cost --help")
        return

    try:
        result = calc.calculate_route_cost(
            origin_river=o_river,
            origin_mile=o_mile,
            dest_river=d_river,
            dest_mile=d_mile,
            cargo_tons=tons,
            tow_config=tow_config,
            speed_mph=speed,
        )
        click.echo(calc.get_route_summary(result))
    except Exception as e:
        click.echo(f"Error calculating route: {e}")


@barge_cost.command("forecast")
@click.option("--weeks", default=4, type=int, help="Weeks ahead to forecast (default: 4).")
def barge_cost_forecast(weeks: int):
    """Show USDA barge rate forecast by segment."""
    try:
        from barge_cost_model.barge_cost_calculator import BargeCostCalculator
    except ImportError:
        click.echo("Error: barge_cost_model not importable.")
        return

    calc = BargeCostCalculator()
    click.echo("Loading rate data...")
    status = calc.load_data()
    if "FAILED" in str(status.get("rates", "")):
        click.echo(f"  rates: {status['rates']}")
        click.echo("Cannot generate forecast without rate data.")
        return

    df = calc.get_rate_forecast(weeks_ahead=weeks)
    if df.empty:
        click.echo("No rate data available for forecasting.")
        return

    click.echo(f"\nBarge Rate Forecast ({weeks} weeks)")
    click.echo("=" * 70)
    click.echo(df.to_string())


# ---------------------------------------------------------------------------
# RAIL-COST command
# ---------------------------------------------------------------------------
@cli.command("rail-cost")
@click.option("--miles", required=True, type=float, help="Route distance in miles.")
@click.option("--tons", required=True, type=float, help="Commodity tonnage (net tons).")
@click.option("--cars", default=1, type=int, help="Number of rail cars (default: 1).")
@click.option("--interchanges", default=0, type=int, help="Number of carrier interchanges.")
@click.option("--classifications", default=1, type=int, help="Yard classification events (default: 1).")
@click.option("--transit-days", default=None, type=float,
              help="Transit days (auto-estimated from miles if omitted).")
@click.option("--commodity", default=None, help="Commodity label (for display only).")
def rail_cost(miles: float, tons: float, cars: int, interchanges: int,
              classifications: int, transit_days: float | None, commodity: str | None):
    """Calculate rail freight cost using URCS variable cost methodology.

    Accepts route miles and tonnage directly. For full graph-based routing
    from city names, use the rail_cost_model notebooks/Streamlit app.
    """
    try:
        from rail_cost_model.src.costing.route_costing import RouteCostCalculator
    except ImportError:
        click.echo("Error: rail_cost_model not importable.")
        click.echo(f"  Checked: {_toolsets_dir}")
        return

    calc = RouteCostCalculator()
    result = calc.calculate_route_cost(
        route_miles=miles,
        commodity_tons=tons,
        num_cars=cars,
        num_interchanges=interchanges,
        num_classifications=classifications,
        transit_days=transit_days,
    )

    # Format output
    params = result['parameters']
    bd = result['breakdown']

    click.echo("\n" + "=" * 60)
    click.echo("RAIL COST ESTIMATE (URCS Variable Cost Method)")
    click.echo("=" * 60)
    if commodity:
        click.echo(f"  Commodity:       {commodity}")
    click.echo(f"\n  Route Miles:     {params['route_miles']:,.1f}")
    click.echo(f"  Commodity Tons:  {params['commodity_tons']:,.1f}")
    click.echo(f"  Cars:            {params['num_cars']}")
    click.echo(f"  Gross Tons:      {params['gross_tons']:,.1f}")
    click.echo(f"  Transit Days:    {params['transit_days']:.1f}")

    click.echo(f"\n  LINE HAUL COSTS")
    click.echo(f"    Car-mile:        ${bd['line_haul']['car_mile']:>12,.2f}")
    click.echo(f"    Gross ton-mile:  ${bd['line_haul']['gross_ton_mile']:>12,.2f}")
    click.echo(f"    Train-mile:      ${bd['line_haul']['train_mile']:>12,.2f}")

    click.echo(f"\n  TERMINAL COSTS")
    click.echo(f"    Switching:       ${bd['terminal']['switching']:>12,.2f}")
    click.echo(f"    Interchange:     ${bd['terminal']['interchange']:>12,.2f}")

    click.echo(f"\n  EQUIPMENT COSTS")
    click.echo(f"    Car-days:        ${bd['equipment']:>12,.2f}")

    click.echo(f"\n  " + "-" * 40)
    click.echo(f"  TOTAL COST:        ${result['total_variable_cost']:>12,.2f}")
    click.echo(f"  Cost per ton:      ${result['cost_per_ton']:>12.4f}")
    click.echo(f"  Cost per car:      ${result['cost_per_car']:>12,.2f}")
    click.echo(f"  Cost per mile:     ${result['cost_per_mile']:>12.4f}")
    click.echo("=" * 60)


# ---------------------------------------------------------------------------
# FACILITY-SEARCH command (wired to facility_registry toolset)
# ---------------------------------------------------------------------------
@cli.command("facility-search")
@click.option("--state", required=True, help="Two-letter state code.")
@click.option("--naics", required=True, help="NAICS code prefix to filter.")
@click.option("--radius", default=50, type=int, help="Search radius in miles (with --lat/--lon).")
@click.option("--lat", default=None, type=float, help="Center latitude for radius search.")
@click.option("--lon", default=None, type=float, help="Center longitude for radius search.")
@click.option("--limit", default=25, type=int, help="Max results to display.")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "csv"]),
              help="Output format (default: table).")
def facility_search(state: str, naics: str, radius: int,
                    lat: float | None, lon: float | None, limit: int, fmt: str):
    """Search EPA FRS facilities by NAICS code and location."""
    if lat is not None and lon is not None:
        # Radius search via spatial_analysis (resolves DB path correctly)
        from facility_registry.src.analyze.spatial_analysis import radius_search
        results = radius_search(
            center_lat=lat, center_lon=lon,
            radius_miles=radius,
            naics_filter=naics,
            state_filter=state,
            limit=limit,
        )

        if fmt == "csv":
            if results:
                import csv
                import io
                buf = io.StringIO()
                writer = csv.DictWriter(buf, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
                click.echo(buf.getvalue())
            else:
                click.echo("No results found.")
            return

        click.echo(f"\nFacilities within {radius}mi of ({lat}, {lon}), "
                    f"state={state}, NAICS={naics}:")
        click.echo(f"{'#':<4} {'Name':<45} {'City':<20} {'Dist (mi)':<10}")
        click.echo("-" * 80)
        for i, fac in enumerate(results, 1):
            click.echo(
                f"{i:<4} {fac.get('fac_name', '')[:44]:<45} "
                f"{fac.get('fac_city', '')[:19]:<20} "
                f"{fac.get('distance_miles', 0):>8.1f}"
            )
        click.echo(f"\n{len(results)} facilities found.")
    else:
        # State-wide search — connect to FRS DuckDB directly to bypass
        # query_engine's broken relative-path config loader
        try:
            import duckdb

            db_path = (get_project_root() / "02_TOOLSETS" / "facility_registry"
                       / "data" / "frs.duckdb")
            if not db_path.exists():
                click.echo(f"Error: FRS database not found at {db_path}")
                click.echo("Run: report-platform data download --source epa_frs")
                return

            conn = duckdb.connect(str(db_path), read_only=True)
            query = """
                SELECT DISTINCT
                    f.registry_id,
                    f.fac_name,
                    f.fac_street,
                    f.fac_city,
                    f.fac_state,
                    f.fac_zip,
                    f.fac_county
                FROM facilities f
                WHERE f.fac_state = ?
                  AND f.registry_id IN (
                      SELECT DISTINCT registry_id
                      FROM naics_codes
                      WHERE naics_code LIKE ?
                  )
                LIMIT ?
            """
            df = conn.execute(query, [state.upper(), f"{naics}%", limit]).df()
            conn.close()

            click.echo(f"\nFacilities in {state} with NAICS prefix {naics}:")

            if fmt == "csv":
                click.echo(df.to_csv(index=False))
                return

            if df.empty:
                click.echo("  No facilities found.")
                return

            click.echo(f"{'#':<4} {'Name':<45} {'City':<20} {'County':<15}")
            click.echo("-" * 85)
            for i, (_, row) in enumerate(df.iterrows(), 1):
                click.echo(
                    f"{i:<4} {str(row.get('fac_name', ''))[:44]:<45} "
                    f"{str(row.get('fac_city', ''))[:19]:<20} "
                    f"{str(row.get('fac_county', ''))[:14]:<15}"
                )
            click.echo(f"\n{len(df)} facilities found.")

        except ImportError:
            click.echo("Error: duckdb is required — pip install duckdb")
        except Exception as e:
            click.echo(f"Error: {e}")


# ---------------------------------------------------------------------------
# SITE REGISTRY commands (wired to site_master_registry toolset)
# ---------------------------------------------------------------------------
@cli.group("site-registry")
def site_registry():
    """Unified industrial site master registry — search, export, map."""


@site_registry.command("search")
@click.option("--name", default=None, help="Facility name (partial match).")
@click.option("--state", default=None, help="Two-letter state code.")
@click.option("--sector", default=None, help="Commodity sector (steel, cement, etc.).")
@click.option("--rail", is_flag=True, default=False, help="Only rail-served sites.")
@click.option("--water", is_flag=True, default=False, help="Only water-access sites.")
@click.option("--limit", default=25, type=int, help="Max results.")
def site_registry_search(name, state, sector, rail, water, limit):
    """Search the master site registry."""
    db_path = (get_project_root() / "02_TOOLSETS" / "site_master_registry"
               / "data" / "site_master.duckdb")
    if not db_path.exists():
        click.echo("Error: site_master.duckdb not found. Run the build pipeline first.")
        return

    _site_toolset = str(get_project_root() / "02_TOOLSETS" / "site_master_registry")
    if _site_toolset not in sys.path:
        sys.path.insert(0, _site_toolset)

    from src.query import SiteRegistryQuery
    query = SiteRegistryQuery(str(db_path))

    results = query.search(
        name=name, state=state, sector=sector,
        rail_served=True if rail else None,
        water_access=True if water else None,
        limit=limit,
    )
    query.close()

    if not results:
        click.echo("No sites found.")
        return

    click.echo(f"\n{'#':<4} {'Name':<42} {'City':<18} {'St':<4} {'Sector':<14} {'Src':<4} {'Flags'}")
    click.echo("-" * 95)
    for i, s in enumerate(results, 1):
        flags = []
        if s.get("rail_served"):
            flags.append("R")
        if s.get("water_access"):
            flags.append("W")
        click.echo(
            f"{i:<4} {str(s['canonical_name'])[:41]:<42} "
            f"{str(s.get('city', ''))[:17]:<18} "
            f"{s.get('state', ''):<4} "
            f"{str(s.get('commodity_sectors', ''))[:13]:<14} "
            f"{s.get('source_count', 0):<4} "
            f"{','.join(flags)}"
        )
    click.echo(f"\n{len(results)} sites found.")


@site_registry.command("summary")
def site_registry_summary():
    """Show registry statistics."""
    db_path = (get_project_root() / "02_TOOLSETS" / "site_master_registry"
               / "data" / "site_master.duckdb")
    if not db_path.exists():
        click.echo("Error: site_master.duckdb not found.")
        return

    _site_toolset = str(get_project_root() / "02_TOOLSETS" / "site_master_registry")
    if _site_toolset not in sys.path:
        sys.path.insert(0, _site_toolset)

    from src.query import SiteRegistryQuery
    query = SiteRegistryQuery(str(db_path))
    s = query.summary()
    query.close()

    click.echo("\n" + "=" * 50)
    click.echo("  Site Master Registry — Summary")
    click.echo("=" * 50)
    click.echo(f"  Total sites:       {s['total_sites']:,}")
    click.echo(f"  Source links:      {s['total_links']:,}")
    click.echo(f"  States:            {s['states']}")
    click.echo(f"  Rail served:       {s['rail_served']:,}")
    click.echo(f"  Water access:      {s['water_access']:,}")
    click.echo(f"  Multimodal:        {s['multimodal']:,}")
    click.echo("-" * 50)
    click.echo("  Sites by sector:")
    for sector, count in sorted(s["sectors"].items(), key=lambda x: -x[1]):
        click.echo(f"    {sector:25s}: {count:,}")
    click.echo("=" * 50 + "\n")


@site_registry.command("export")
@click.option("--format", "fmt", default="csv",
              type=click.Choice(["csv", "geojson", "json"]),
              help="Export format.")
@click.option("--sector", default=None, help="Filter to sector.")
@click.option("--output", default=None, help="Output file path.")
def site_registry_export(fmt, sector, output):
    """Export registry data to CSV, GeoJSON, or JSON."""
    db_path = (get_project_root() / "02_TOOLSETS" / "site_master_registry"
               / "data" / "site_master.duckdb")
    if not db_path.exists():
        click.echo("Error: site_master.duckdb not found.")
        return

    _site_toolset = str(get_project_root() / "02_TOOLSETS" / "site_master_registry")
    if _site_toolset not in sys.path:
        sys.path.insert(0, _site_toolset)

    from src.query import SiteRegistryQuery
    from src.exporters import export_csv, export_geojson, export_json_summary

    sectors = [sector] if sector else None
    default_dir = get_project_root() / "02_TOOLSETS" / "site_master_registry" / "data"

    query = SiteRegistryQuery(str(db_path))

    if fmt == "csv":
        out = output or str(default_dir / "site_master_export.csv")
        export_csv(query, out, sectors=sectors)
    elif fmt == "geojson":
        out = output or str(default_dir / "site_master_export.geojson")
        export_geojson(query, out, sectors=sectors)
    elif fmt == "json":
        out = output or str(default_dir / "site_master_summary.json")
        export_json_summary(query, out)

    query.close()
    click.echo(f"Exported to {out}")


@site_registry.command("map")
@click.option("--sector", default=None, help="Filter to sector (comma-separated for multiple).")
@click.option("--min-sources", default=0, type=int, help="Minimum source count.")
@click.option("--output", default=None, help="Output HTML file path.")
@click.option("--open", "open_browser", is_flag=True, help="Open in browser after creating.")
def site_registry_map(sector, min_sources, output, open_browser):
    """Generate interactive Folium map of registry sites."""
    db_path = (get_project_root() / "02_TOOLSETS" / "site_master_registry"
               / "data" / "site_master.duckdb")
    if not db_path.exists():
        click.echo("Error: site_master.duckdb not found.")
        return

    _site_toolset = str(get_project_root() / "02_TOOLSETS" / "site_master_registry")
    if _site_toolset not in sys.path:
        sys.path.insert(0, _site_toolset)

    from src.query import SiteRegistryQuery
    from src.map_builder import build_registry_map

    sectors = [s.strip() for s in sector.split(",")] if sector else None
    default_out = get_project_root() / "02_TOOLSETS" / "site_master_registry" / "data" / "site_master_map.html"
    out = output or str(default_out)

    query = SiteRegistryQuery(str(db_path))
    path = build_registry_map(query, out, sectors=sectors, min_sources=min_sources)
    query.close()

    click.echo(f"Map saved to {path}")
    if open_browser:
        import webbrowser
        webbrowser.open(f"file://{path.resolve()}")


@site_registry.command("enrich-geo")
@click.option("--reference-dir", default=None,
              help="Path to reference data directory (default: data/reference/).")
def site_registry_enrich_geo(reference_dir):
    """Run geographic identity enrichment on all master sites.

    Adds 15 geographic columns: DMS coordinates, FIPS codes, Census/BEA/EPA
    regions, congressional district, market region, nearest port code,
    port name, consolidated group, coast, and region.
    """
    db_path = (get_project_root() / "02_TOOLSETS" / "site_master_registry"
               / "data" / "site_master.duckdb")
    if not db_path.exists():
        click.echo("Error: site_master.duckdb not found. Run the build pipeline first.")
        return

    _site_toolset = str(get_project_root() / "02_TOOLSETS" / "site_master_registry")
    if _site_toolset not in sys.path:
        sys.path.insert(0, _site_toolset)

    ref_dir = reference_dir or str(
        get_project_root() / "02_TOOLSETS" / "site_master_registry"
        / "data" / "reference"
    )

    click.echo("\nRunning geographic identity enrichment...")
    from src.geo_enrichment import enrich_master_sites
    enrich_master_sites(
        db_path=str(db_path),
        reference_dir=ref_dir,
        project_root=str(get_project_root()),
    )


@site_registry.command("build-port-dict")
def site_registry_build_port_dict():
    """Build the unified port geo-dictionary from all port reference sources.

    Merges Census port_reference.csv, USACE dictionaries, and Panjiva
    ports_master.csv into a single JSON at data/reference/port_geo_dictionary.json.
    """
    _site_toolset = str(get_project_root() / "02_TOOLSETS" / "site_master_registry")
    if _site_toolset not in sys.path:
        sys.path.insert(0, _site_toolset)

    click.echo("\nBuilding port geo-dictionary...")
    from src.build_port_geo_dictionary import build_port_geo_dictionary
    try:
        out_path = build_port_geo_dictionary(str(get_project_root()))
        click.echo(f"Done. Output: {out_path}")
    except FileNotFoundError as e:
        click.echo(f"Error: {e}")
    except Exception as e:
        click.echo(f"Error building port dictionary: {e}")


@site_registry.command("dashboard")
@click.option("--sector", default=None, help="Filter to sector (comma-separated for multiple).")
@click.option("--min-sources", default=0, type=int, help="Minimum source count.")
@click.option("--output", default=None, help="Output HTML file path.")
@click.option("--open", "open_browser", is_flag=True, help="Open in browser after creating.")
def site_registry_dashboard(sector, min_sources, output, open_browser):
    """Generate interactive dashboard with search, filter, map, and CSV export."""
    db_path = (get_project_root() / "02_TOOLSETS" / "site_master_registry"
               / "data" / "site_master.duckdb")
    if not db_path.exists():
        click.echo("Error: site_master.duckdb not found.")
        return

    _site_toolset = str(get_project_root() / "02_TOOLSETS" / "site_master_registry")
    if _site_toolset not in sys.path:
        sys.path.insert(0, _site_toolset)

    from src.query import SiteRegistryQuery
    from src.map_builder import build_registry_dashboard

    sectors = [s.strip() for s in sector.split(",")] if sector else None
    default_out = (get_project_root() / "02_TOOLSETS" / "site_master_registry"
                   / "data" / "site_master_dashboard.html")
    out = output or str(default_out)

    query = SiteRegistryQuery(str(db_path))
    path = build_registry_dashboard(
        query, out, sectors=sectors, min_sources=min_sources,
    )
    query.close()

    click.echo(f"Dashboard saved to {path}")
    if open_browser:
        import webbrowser
        webbrowser.open(f"file://{path.resolve()}")


# ---------------------------------------------------------------------------
# POLICY commands (wired to policy_analysis toolset)
# ---------------------------------------------------------------------------
@cli.group()
def policy():
    """Maritime policy analysis — Section 301, Jones Act, tariffs."""


@policy.command("section-301")
@click.option("--vessel-type", required=True,
              type=click.Choice(["container", "bulk", "tanker", "roro", "car_carrier"]),
              help="Vessel type.")
@click.option("--nrt", required=True, type=int, help="Net registered tonnage.")
@click.option("--category", default="chinese_built",
              type=click.Choice(["chinese_built", "chinese_operated", "chinese_owned"]),
              help="Chinese nexus category.")
@click.option("--phase", default=1, type=int, help="Fee phase (1, 2, or 3).")
@click.option("--cargo-tons", default=30000.0, type=float, help="Cargo tons for per-ton impact.")
def section_301(vessel_type: str, nrt: int, category: str, phase: int, cargo_tons: float):
    """Calculate Section 301 maritime shipping fee."""
    from policy_analysis.src.section_301_model import assess_section_301, compare_phases
    result = assess_section_301(
        vessel_name="CLI Query",
        vessel_nrt=nrt,
        vessel_type=vessel_type,
        category=category,
        phase=phase,
        cargo_tons=cargo_tons,
    )
    click.echo(f"\nSection 301 Fee Assessment")
    click.echo(f"  Vessel type:    {result.vessel_type}")
    click.echo(f"  NRT:            {result.vessel_nrt:,}")
    click.echo(f"  Category:       {result.category}")
    click.echo(f"  Phase:          {result.phase}")
    click.echo(f"  Fee type:       {result.fee_type}")
    click.echo(f"  Calculated fee: ${result.calculated_fee:,.2f}")
    if result.fee_cap > 0:
        click.echo(f"  Fee cap:        ${result.fee_cap:,.2f}")
    click.echo(f"  Applied fee:    ${result.applied_fee:,.2f}")
    if cargo_tons > 0:
        click.echo(f"  Impact/ton:     ${result.fee_per_ton_cargo:,.2f}")

    click.echo(f"\n  Phase comparison (same vessel, {cargo_tons:,.0f} tons):")
    for p in compare_phases(nrt, vessel_type, category, cargo_tons):
        click.echo(f"    Phase {p.phase}: ${p.applied_fee:>12,.2f}  (${p.fee_per_ton_cargo:.2f}/ton)")


@policy.command("landed-cost")
@click.option("--hts", required=True, help="HTS code (e.g., 2523.29).")
@click.option("--origin", required=True, help="Origin country.")
@click.option("--fob", required=True, type=float, help="FOB price per ton.")
@click.option("--freight", required=True, type=float, help="Ocean freight per ton.")
@click.option("--tons", default=30000.0, type=float, help="Cargo tonnage.")
@click.option("--port-charge", default=8.0, type=float, help="Port charges per ton.")
@click.option("--inland", default=15.0, type=float, help="Inland freight per ton.")
def landed_cost(hts: str, origin: str, fob: float, freight: float,
                tons: float, port_charge: float, inland: float):
    """Calculate landed cost with tariff breakdown."""
    from policy_analysis.src.tariff_impact import calculate_landed_cost
    lc = calculate_landed_cost(
        commodity="cement",
        hts_code=hts,
        origin_country=origin,
        cargo_tons=tons,
        fob_price_per_ton=fob,
        ocean_freight_per_ton=freight,
        port_charges_per_ton=port_charge,
        inland_freight_per_ton=inland,
    )
    click.echo(f"\nLanded Cost Breakdown: {origin} -> US")
    click.echo(f"  HTS: {lc.hts_code}  |  Cargo: {lc.cargo_tons:,.0f} tons")
    click.echo(f"\n  FOB:             ${lc.fob_price_per_ton:>8.2f}/ton")
    click.echo(f"  Ocean freight:   ${lc.ocean_freight_per_ton:>8.2f}/ton")
    click.echo(f"  Insurance:       ${lc.insurance_per_ton:>8.2f}/ton")
    click.echo(f"  CIF:             ${lc.cif_per_ton:>8.2f}/ton")
    click.echo(f"  General duty:    ${lc.general_duty_per_ton:>8.2f}/ton ({lc.general_duty_pct}%)")
    click.echo(f"  ADD:             ${lc.add_per_ton:>8.2f}/ton")
    click.echo(f"  CVD:             ${lc.cvd_per_ton:>8.2f}/ton")
    click.echo(f"  Port charges:    ${lc.port_charges_per_ton:>8.2f}/ton")
    click.echo(f"  Inland freight:  ${lc.inland_freight_per_ton:>8.2f}/ton")
    click.echo(f"  -----------------------------")
    click.echo(f"  LANDED COST:     ${lc.total_landed_per_ton:>8.2f}/ton")
    click.echo(f"  TOTAL:           ${lc.total_landed_cost:>12,.2f}")


@policy.command("regulatory")
@click.option("--mode", default=None, help="Filter by transport mode (vessel, barge, rail).")
@click.option("--agency", default=None, help="Filter by agency (USTR, USCG, EPA, STB, etc.).")
@click.option("--category", default=None,
              help="Filter by category (trade, environmental, safety, economic, maritime).")
@click.option("--commodity", default=None,
              help="Filter by affected commodity (e.g., cement, all_imports).")
def regulatory(mode: str | None, agency: str | None,
               category: str | None, commodity: str | None):
    """Show active regulatory actions affecting supply chain."""
    from policy_analysis.src.regulatory_tracker import get_active_actions
    actions = get_active_actions(
        category=category, agency=agency, mode=mode, commodity=commodity,
    )

    click.echo(f"\nActive Regulatory Actions:")
    filters = []
    if category:
        filters.append(f"category={category}")
    if agency:
        filters.append(f"agency={agency}")
    if mode:
        filters.append(f"mode={mode}")
    if commodity:
        filters.append(f"commodity={commodity}")
    if filters:
        click.echo(f"  Filters: {', '.join(filters)}")

    click.echo(f"\n{'ID':<20} {'Agency':<8} {'Status':<12} Title")
    click.echo("-" * 90)
    for a in actions:
        click.echo(f"  {a.action_id:<18} {a.agency:<8} {a.status:<12} {a.title[:48]}")
        if a.estimated_cost_impact:
            click.echo(f"    Impact: {a.estimated_cost_impact}")
    click.echo(f"\n{len(actions)} actions found.")


# ---------------------------------------------------------------------------
# REPORT commands
# ---------------------------------------------------------------------------
@cli.group()
def report():
    """Report generation — create, preview, and export reports."""


@report.command("generate")
@click.option("--report", "report_name", required=True,
              type=click.Choice(["us_bulk_supply_chain", "cement_commodity"]),
              help="Report to generate.")
@click.option("--format", "fmt", default="md",
              type=click.Choice(["md", "docx", "html"]),
              help="Output format.")
@click.option("--section", default=None, help="Generate a specific section only (e.g., '09').")
@click.option("--with-data", is_flag=True, help="Run data extractors for live data injection.")
def report_generate(report_name: str, fmt: str, section: str | None, with_data: bool):
    """Generate a master report or commodity report."""
    import logging

    logging.basicConfig(level=logging.INFO, format="  %(message)s")

    from report_platform.reports.engine import ReportEngine

    click.echo(f"Generating: {report_name}")
    click.echo(f"  Format:    {fmt}")
    if section:
        click.echo(f"  Section:   {section}")
    if with_data:
        click.echo(f"  Data:      live extraction enabled")

    try:
        engine = ReportEngine()
        output_path = engine.generate(
            report_name=report_name,
            fmt=fmt,
            section=section,
            with_data=with_data,
        )
        click.echo(f"\n  Output: {output_path}")
        click.echo(f"  Size:   {output_path.stat().st_size:,} bytes")
    except FileNotFoundError as e:
        click.echo(f"Error: {e}")
    except Exception as e:
        click.echo(f"Error generating report: {e}")


@report.command("preview")
@click.option("--report", "report_name", required=True,
              type=click.Choice(["us_bulk_supply_chain", "cement_commodity"]),
              help="Report to preview.")
def report_preview(report_name: str):
    """Preview report structure and chapter listing."""
    from report_platform.reports.engine import ReportEngine

    engine = ReportEngine()
    try:
        chapters = engine.preview_report(report_name)
        click.echo(f"\nReport: {report_name}")
        click.echo(f"Chapters: {len(chapters)}")
        click.echo()
        click.echo(f"  {'#':<4} {'Title':<40} {'Size':<14} {'Template':<9} Extractors")
        click.echo("  " + "-" * 85)
        for ch in chapters:
            click.echo(
                f"  {ch['number']:<4} {ch['title'][:39]:<40} {ch['size']:<14} "
                f"{ch['template']:<9} {ch['extractors']}"
            )
    except FileNotFoundError as e:
        click.echo(f"Error: {e}")


@report.command("list")
def report_list():
    """List available reports and their status."""
    from report_platform.reports.engine import ReportEngine

    engine = ReportEngine()
    reports = engine.list_reports()
    click.echo("Available reports:")
    click.echo()
    for r in reports:
        click.echo(f"  {r['directory']}/ ({r['chapters']} chapters)")
        for f in r['files']:
            click.echo(f"    - {f}")


# ---------------------------------------------------------------------------
# COMMODITY commands
# ---------------------------------------------------------------------------
@cli.group()
def commodity():
    """Commodity module management — list, initialize, and configure."""


@commodity.command("list")
def commodity_list():
    """List active and planned commodity modules."""
    from report_platform.config import get_commodity_modules_config
    modules = get_commodity_modules_config()

    click.echo("Active modules:")
    for mod in modules.get("active", []):
        click.echo(f"  * {mod}")

    click.echo("\nPlanned modules:")
    for mod in modules.get("planned", []):
        click.echo(f"  - {mod}")


@commodity.command("init")
@click.option("--name", required=True, help="Commodity module name (e.g., grain).")
def commodity_init(name: str):
    """Scaffold a new commodity module directory structure."""
    base = get_project_root() / "03_COMMODITY_MODULES" / name

    if base.exists():
        click.echo(f"Module '{name}' already exists at {base}")
        return

    dirs = [
        "market_intelligence/supply_landscape",
        "market_intelligence/demand_analysis",
        "market_intelligence/trade_flows",
        "supply_chain_models/barge_routes",
        "supply_chain_models/rail_routes",
        "supply_chain_models/terminal_operations",
        "reports/templates",
        "reports/drafts",
        "reports/published",
    ]
    for d in dirs:
        (base / d).mkdir(parents=True, exist_ok=True)

    (base / "README.md").write_text(f"# {name.title()} Commodity Module\n")
    (base / "config.yaml").write_text(f"module:\n  name: {name}\n  status: scaffolded\n")
    (base / "naics_codes.json").write_text("{}\n")

    click.echo(f"Scaffolded commodity module: {name}")
    click.echo(f"  Location: {base}")
    click.echo(f"  Directories: {len(dirs)}")
    click.echo(f"  Next: populate naics_codes.json and config.yaml")


# ---------------------------------------------------------------------------
# DB commands
# ---------------------------------------------------------------------------
@cli.group()
def db():
    """Database management — initialize and query DuckDB analytics."""


@db.command("status")
def db_status():
    """Show status of all configured databases."""
    from report_platform.database import show_db_status
    show_db_status()


@db.command("init")
@click.option("--force", is_flag=True, help="Reinitialize (drops existing tables).")
def db_init(force: bool):
    """Initialize the master analytics DuckDB database."""
    from report_platform.database import init_master_db
    init_master_db(force=force)


def main():
    cli()


if __name__ == "__main__":
    main()
