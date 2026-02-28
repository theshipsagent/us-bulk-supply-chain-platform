#!/usr/bin/env python3
"""
ATLAS CLI - Command Line Interface
===================================
Click-based CLI for ATLAS project operations.

Commands:
    refresh - Refresh data from EPA FRS, GEM, or ports
    query   - Query facility data
    stats   - Show database statistics
    info    - Show facility information
"""

import click
import yaml
import logging
import sys
from pathlib import Path
from tabulate import tabulate

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from etl.epa_frs import EPAFRSLoader
from etl.gem_cement import GEMCementLoader, get_gem_stats, query_gem_by_country
from etl.ports import ScheduleKLoader, get_port_stats, find_nearest_port
from etl.facility_master import FacilityMasterBuilder, get_master_stats
from etl.usgs_cement import USGSCementLoader, get_usgs_stats
from harmonize.entity_resolver import EntityResolver
from analytics.supply import SupplyAnalytics


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = None) -> dict:
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = Path(__file__).parent / 'config' / 'settings.yaml'

    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


@click.group()
@click.option('--config', type=click.Path(exists=True), help='Path to configuration file')
@click.pass_context
def cli(ctx, config):
    """ATLAS - Advanced Tracking and Logistics Analytics System for Cement Markets"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = load_config(config)


@cli.command()
@click.option('--source', type=click.Choice(['frs', 'gem', 'ports', 'master', 'usgs', 'all']),
              default='frs', help='Data source to refresh')
@click.option('--resolve-entities', is_flag=True, help='Apply entity resolution after loading')
@click.pass_context
def refresh(ctx, source, resolve_entities):
    """Refresh data from specified source(s).

    Sources:
        frs    - EPA FRS facilities (default)
        gem    - GEM Global Cement Tracker
        ports  - Schedule K port dictionary
        master - Build master facilities table (requires frs/gem/ports)
        usgs   - USGS cement industry statistics
        all    - Refresh all sources
    """
    config = ctx.obj['config']

    click.echo("=" * 70)
    click.echo("ATLAS DATA REFRESH")
    click.echo("=" * 70)

    # Get paths
    atlas_db_path = str(Path(__file__).parent / config['data']['atlas']['path'])
    click.echo(f"ATLAS Database: {atlas_db_path}")
    click.echo("")

    # Ensure data directory exists
    Path(atlas_db_path).parent.mkdir(parents=True, exist_ok=True)

    sources_to_load = []
    if source == 'all':
        sources_to_load = ['frs', 'gem', 'ports', 'usgs', 'master']
    else:
        sources_to_load = [source]

    try:
        # EPA FRS
        if 'frs' in sources_to_load:
            frs_db_path = str(Path(__file__).parent / config['data']['epa_frs']['path'])
            naics_config_path = str(Path(__file__).parent / config['naics']['cement_config'])

            click.echo(f"[FRS] Loading EPA FRS data...")
            click.echo(f"      Source: {frs_db_path}")

            if not Path(frs_db_path).exists():
                click.echo(f"[WARN] FRS database not found at {frs_db_path}", err=True)
                click.echo("       Skipping FRS load.", err=True)
            else:
                loader = EPAFRSLoader(frs_db_path, atlas_db_path, naics_config_path)
                loader.refresh()
                click.secho("[OK] EPA FRS data loaded successfully", fg='green')
            click.echo("")

        # GEM Cement Tracker
        if 'gem' in sources_to_load:
            # Default path for GEM data
            gem_path = str(Path(__file__).parent.parent /
                          'industry_tracker' / 'Global-Cement-and-Concrete-Tracker_July-2025.xlsx')

            click.echo(f"[GEM] Loading GEM Cement Tracker...")
            click.echo(f"      Source: {gem_path}")

            if not Path(gem_path).exists():
                click.echo(f"[WARN] GEM file not found at {gem_path}", err=True)
                click.echo("       Skipping GEM load.", err=True)
            else:
                loader = GEMCementLoader(gem_path, atlas_db_path)
                loader.refresh()
                click.secho("[OK] GEM Cement Tracker loaded successfully", fg='green')
            click.echo("")

        # Schedule K Ports
        if 'ports' in sources_to_load:
            # Default path for Schedule K data
            ports_path = str(Path(__file__).parent.parent /
                            'industry_tracker' / 'Schedule K 4th Quarter 2025.xlsx')

            click.echo(f"[PORTS] Loading Schedule K port dictionary...")
            click.echo(f"        Source: {ports_path}")

            if not Path(ports_path).exists():
                click.echo(f"[WARN] Schedule K file not found at {ports_path}", err=True)
                click.echo("       Skipping ports load.", err=True)
            else:
                loader = ScheduleKLoader(ports_path, atlas_db_path)
                loader.refresh()
                click.secho("[OK] Schedule K ports loaded successfully", fg='green')
            click.echo("")

        # USGS Cement Statistics
        if 'usgs' in sources_to_load:
            # Default path for USGS data
            usgs_path = str(Path(__file__).parent / 'data' / 'source' / 'usgs')

            click.echo(f"[USGS] Loading USGS cement statistics...")
            click.echo(f"       Source: {usgs_path}")

            if not Path(usgs_path).exists():
                click.echo(f"[WARN] USGS data directory not found at {usgs_path}", err=True)
                click.echo("       Skipping USGS load.", err=True)
            else:
                loader = USGSCementLoader(usgs_path, atlas_db_path)
                results = loader.refresh()
                mis_counts = results.get('mis', {})
                myb_counts = results.get('myb', {})
                click.echo(f"       MIS: {mis_counts.get('shipments', 0)} shipments, "
                          f"{mis_counts.get('production', 0)} production, "
                          f"{mis_counts.get('imports', 0)} imports")
                click.echo(f"       MYB: {myb_counts.get('annual_stats', 0)} annual records")
                click.secho("[OK] USGS cement statistics loaded successfully", fg='green')
            click.echo("")

        # Master facilities table
        if 'master' in sources_to_load:
            click.echo("[MASTER] Building master facilities table...")

            builder = FacilityMasterBuilder(atlas_db_path)
            tables = builder.check_source_tables()

            if not any(tables.values()):
                click.echo("[WARN] No source tables available for master build.", err=True)
                click.echo("       Run refresh with --source frs/gem/ports first.", err=True)
            else:
                click.echo(f"        Available sources: {[k for k, v in tables.items() if v]}")
                builder.create_master_table()
                click.secho("[OK] Master facilities table built successfully", fg='green')
            click.echo("")

        # Apply entity resolution if requested
        if resolve_entities:
            click.echo("")
            click.echo("Applying entity resolution...")

            companies_config_path = str(Path(__file__).parent / config['entity_resolution']['target_companies'])
            threshold = config['entity_resolution']['fuzzy_threshold']

            # TODO: Implement entity resolution integration with database
            click.echo("Entity resolution feature coming soon...")

        click.echo("")
        click.secho("[OK] Data refresh complete", fg='green', bold=True)

    except Exception as e:
        click.secho(f"[ERROR] Error during refresh: {e}", fg='red', err=True)
        logger.exception("Refresh failed")
        sys.exit(1)


@cli.command()
@click.option('--state', help='Filter by state code (e.g., CA, TX)')
@click.option('--naics', help='Filter by NAICS code prefix (e.g., 3273, 327310)')
@click.option('--company', help='Filter by company name (fuzzy match)')
@click.option('--country', help='Filter by country (for GEM/global data)')
@click.option('--source', type=click.Choice(['frs', 'gem', 'master']),
              help='Query specific data source')
@click.option('--limit', default=20, help='Maximum number of results to display')
@click.option('--output', type=click.Path(), help='Export results to CSV file')
@click.pass_context
def query(ctx, state, naics, company, country, source, limit, output):
    """Query facility data with filters."""
    config = ctx.obj['config']
    atlas_db_path = str(Path(__file__).parent / config['data']['atlas']['path'])

    if not Path(atlas_db_path).exists():
        click.echo(f"ERROR: ATLAS database not found at {atlas_db_path}", err=True)
        click.echo("Run 'atlas refresh' first to load data.", err=True)
        sys.exit(1)

    try:
        # Country query - use GEM data
        if country:
            click.echo(f"Querying GEM plants in {country}...")
            df = query_gem_by_country(atlas_db_path, country)

            if df.empty:
                click.echo(f"No GEM plants found for country: {country}")
                return

            click.echo(f"\nFound {len(df)} plants in {country}:\n")

            # Select columns for display
            display_cols = ['gem_id', 'plant_name', 'region', 'capacity_mtpa',
                           'status', 'owner_name']
            display_df = df[[c for c in display_cols if c in df.columns]].head(limit)

            click.echo(tabulate(display_df, headers='keys', tablefmt='psql', showindex=False))

            if output:
                df.to_csv(output, index=False)
                click.secho(f"\n[OK] Exported {len(df)} records to {output}", fg='green')
            return

        # Standard FRS query
        analytics = SupplyAnalytics(atlas_db_path)

        if state and not naics and not company:
            # State summary
            click.echo(f"Querying facilities in {state}...")
            df = analytics.get_facility_details(state=state, limit=limit)

        elif naics:
            # NAICS-based query
            click.echo(f"Querying facilities with NAICS {naics}...")
            df = analytics.count_by_naics(naics)

        elif company:
            # Company-based query
            click.echo(f"Querying facilities for company: {company}...")
            df = analytics.get_facility_details(company=company, limit=limit)

        else:
            # General facility details
            click.echo("Querying facilities...")
            df = analytics.get_facility_details(limit=limit)

        if df.empty:
            click.echo("No results found.")
            return

        # Display results
        click.echo(f"\nFound {len(df)} results:\n")

        # Format for display
        display_df = df.head(limit)

        # Truncate long columns for better display
        if 'naics_codes' in display_df.columns:
            display_df = display_df.copy()
            display_df['naics_codes'] = display_df['naics_codes'].apply(
                lambda x: str(x)[:30] + '...' if x and len(str(x)) > 30 else x
            )

        click.echo(tabulate(display_df, headers='keys', tablefmt='psql', showindex=False))

        # Export if requested
        if output:
            df.to_csv(output, index=False)
            click.secho(f"\n[OK] Exported {len(df)} records to {output}", fg='green')

    except Exception as e:
        click.secho(f"[ERROR] Query error: {e}", fg='red', err=True)
        logger.exception("Query failed")
        sys.exit(1)


@cli.command()
@click.option('--by-state', is_flag=True, help='Show breakdown by state')
@click.option('--by-naics', is_flag=True, help='Show breakdown by NAICS code')
@click.option('--by-company', is_flag=True, help='Show breakdown by company')
@click.option('--global', 'show_global', is_flag=True, help='Show global GEM production stats')
@click.option('--ports', is_flag=True, help='Show port statistics')
@click.option('--master', is_flag=True, help='Show master facilities table stats')
@click.option('--usgs', is_flag=True, help='Show USGS cement statistics')
@click.pass_context
def stats(ctx, by_state, by_naics, by_company, show_global, ports, master, usgs):
    """Show database statistics."""
    config = ctx.obj['config']
    atlas_db_path = str(Path(__file__).parent / config['data']['atlas']['path'])

    if not Path(atlas_db_path).exists():
        click.echo(f"ERROR: ATLAS database not found at {atlas_db_path}", err=True)
        click.echo("Run 'atlas refresh' first to load data.", err=True)
        sys.exit(1)

    try:
        # Global GEM stats
        if show_global:
            click.echo("=" * 70)
            click.echo("GLOBAL CEMENT PRODUCTION (GEM Tracker)")
            click.echo("=" * 70)

            gem_stats = get_gem_stats(atlas_db_path)

            if not gem_stats:
                click.echo("\nNo GEM data loaded. Run 'atlas refresh --source gem' first.")
            else:
                click.echo(f"\nTotal Plants:              {gem_stats.get('total_plants', 0):,}")
                click.echo(f"Countries:                 {gem_stats.get('total_countries', 0)}")
                click.echo(f"Total Capacity (MTPA):     {gem_stats.get('total_capacity_mtpa', 0):,.1f}")
                click.echo(f"Geocoded Plants:           {gem_stats.get('geocoded_plants', 0):,}")
                click.echo(f"Unique Parent Companies:   {gem_stats.get('unique_parents', 0)}")

                if gem_stats.get('top_countries'):
                    click.echo("\nTop Countries by Capacity:")
                    for item in gem_stats['top_countries'][:10]:
                        cap = item.get('total_capacity_mtpa') or 0
                        click.echo(f"  {item['country']}: {item['plant_count']} plants, {cap:,.1f} MTPA")

                if gem_stats.get('top_parents'):
                    click.echo("\nTop Parent Companies by Capacity:")
                    for item in gem_stats['top_parents'][:10]:
                        cap = item.get('total_capacity_mtpa') or 0
                        click.echo(f"  {item['parent_company']}: {item['plant_count']} plants, {cap:,.1f} MTPA ({item['country_count']} countries)")

            click.echo("")
            return

        # Port stats
        if ports:
            click.echo("=" * 70)
            click.echo("PORT STATISTICS (Schedule K)")
            click.echo("=" * 70)

            port_stats = get_port_stats(atlas_db_path)

            if not port_stats:
                click.echo("\nNo port data loaded. Run 'atlas refresh --source ports' first.")
            else:
                click.echo(f"\nTotal Ports:               {port_stats.get('total_ports', 0):,}")
                click.echo(f"Countries:                 {port_stats.get('total_countries', 0)}")
                click.echo(f"Geocoded Ports:            {port_stats.get('geocoded_ports', 0):,}")
                click.echo(f"US Ports:                  {port_stats.get('us_ports', 0):,}")

                if port_stats.get('top_countries'):
                    click.echo("\nTop Countries by Port Count:")
                    for item in port_stats['top_countries'][:10]:
                        click.echo(f"  {item['country_name']}: {item['port_count']} ports")

            click.echo("")
            return

        # Master table stats
        if master:
            click.echo("=" * 70)
            click.echo("MASTER FACILITIES TABLE")
            click.echo("=" * 70)

            master_stats = get_master_stats(atlas_db_path)

            if not master_stats:
                click.echo("\nNo master table. Run 'atlas refresh --source master' first.")
            else:
                click.echo(f"\nTotal Facilities:          {master_stats.get('total_facilities', 0):,}")
                click.echo(f"Countries:                 {master_stats.get('total_countries', 0)}")
                click.echo(f"GEM-FRS Matches:           {master_stats.get('gem_frs_matches', 0):,}")
                click.echo(f"Port-Linked Facilities:    {master_stats.get('port_linked', 0):,}")

                if master_stats.get('by_source'):
                    click.echo("\nBy Source:")
                    for item in master_stats['by_source']:
                        click.echo(f"  {item['source']}: {item['count']:,}")

            click.echo("")
            return

        # USGS stats
        if usgs:
            click.echo("=" * 70)
            click.echo("USGS CEMENT STATISTICS")
            click.echo("=" * 70)

            usgs_stats = get_usgs_stats(atlas_db_path)

            if not usgs_stats or not usgs_stats.get('shipments'):
                click.echo("\nNo USGS data loaded. Run 'atlas refresh --source usgs' first.")
            else:
                # Shipments summary
                ship = usgs_stats.get('shipments', {})
                if ship:
                    click.echo(f"\nMonthly Shipments:")
                    click.echo(f"  Records:                 {ship.get('total_records', 0):,}")
                    click.echo(f"  States:                  {ship.get('states', 0)}")
                    click.echo(f"  Year Range:              {ship.get('year_range', 'N/A')}")
                    total_ship = ship.get('total_short_tons')
                    if total_ship:
                        click.echo(f"  Total (short tons):      {total_ship:,.0f}")

                # Production summary
                prod = usgs_stats.get('production', {})
                if prod:
                    click.echo(f"\nMonthly Production:")
                    click.echo(f"  Records:                 {prod.get('total_records', 0):,}")
                    click.echo(f"  Districts:               {prod.get('districts', 0)}")
                    click.echo(f"  Year Range:              {prod.get('year_range', 'N/A')}")

                # Imports summary
                imp = usgs_stats.get('imports', {})
                if imp:
                    click.echo(f"\nMonthly Imports:")
                    click.echo(f"  Records:                 {imp.get('total_records', 0):,}")
                    click.echo(f"  Ports:                   {imp.get('ports', 0)}")
                    click.echo(f"  Countries:               {imp.get('countries', 0)}")
                    click.echo(f"  Year Range:              {imp.get('year_range', 'N/A')}")
                    total_imp = imp.get('total_metric_tons')
                    if total_imp:
                        click.echo(f"  Total (metric tons):     {total_imp:,.0f}")

                # Annual stats summary
                annual = usgs_stats.get('annual', {})
                if annual:
                    click.echo(f"\nAnnual Statistics:")
                    click.echo(f"  Years:                   {annual.get('total_years', 0)}")
                    click.echo(f"  Year Range:              {annual.get('year_range', 'N/A')}")

                # Top states
                if usgs_stats.get('top_states'):
                    click.echo("\nTop States by Shipments (short tons):")
                    for item in usgs_stats['top_states'][:10]:
                        total = item.get('total') or 0
                        click.echo(f"  {item['state']}: {total:,.0f}")

                # Top import countries
                if usgs_stats.get('top_import_countries'):
                    click.echo("\nTop Import Countries (metric tons):")
                    for item in usgs_stats['top_import_countries'][:10]:
                        total = item.get('total') or 0
                        click.echo(f"  {item['country']}: {total:,.0f}")

            click.echo("")
            return

        # Default: FRS stats
        analytics = SupplyAnalytics(atlas_db_path)

        click.echo("=" * 70)
        click.echo("ATLAS DATABASE STATISTICS (EPA FRS)")
        click.echo("=" * 70)

        frs_stats = analytics.get_database_stats()

        click.echo(f"\nTotal Facilities:          {frs_stats['total_facilities']:,}")
        click.echo(f"States Covered:            {frs_stats['total_states']}")
        click.echo(f"Facilities with Coords:    {frs_stats['facilities_with_coords']:,}")
        click.echo(f"Facilities with Company:   {frs_stats['facilities_with_company']:,}")
        click.echo(f"Unique Companies:          {frs_stats['unique_companies']}")

        if frs_stats['last_load_timestamp']:
            click.echo(f"Last Updated:              {frs_stats['last_load_timestamp']}")

        # State breakdown
        if by_state:
            click.echo("\n" + "=" * 70)
            click.echo("FACILITIES BY STATE (Top 20)")
            click.echo("=" * 70)
            df = analytics.count_by_state()
            click.echo(tabulate(df.head(20), headers='keys', tablefmt='psql', showindex=False))

        # NAICS breakdown
        if by_naics:
            click.echo("\n" + "=" * 70)
            click.echo("FACILITIES BY NAICS CODE (Top 20)")
            click.echo("=" * 70)
            df = analytics.count_by_naics()
            click.echo(tabulate(df.head(20), headers='keys', tablefmt='psql', showindex=False))

        # Company breakdown
        if by_company:
            click.echo("\n" + "=" * 70)
            click.echo("FACILITIES BY COMPANY (Top 20)")
            click.echo("=" * 70)
            df = analytics.count_by_company()
            if not df.empty:
                click.echo(tabulate(df.head(20), headers='keys', tablefmt='psql', showindex=False))
            else:
                click.echo("No company resolution data available.")
                click.echo("Run 'atlas refresh --resolve-entities' to add company matching.")

    except Exception as e:
        click.secho(f"[ERROR] Error: {e}", fg='red', err=True)
        logger.exception("Stats failed")
        sys.exit(1)


@cli.command()
@click.argument('registry_id', required=False)
@click.option('--state', help='Get state summary')
@click.option('--nearest-port', nargs=2, type=float, metavar='LAT LON',
              help='Find nearest ports to coordinates')
@click.pass_context
def info(ctx, registry_id, state, nearest_port):
    """Show detailed facility information or state summary."""
    config = ctx.obj['config']
    atlas_db_path = str(Path(__file__).parent / config['data']['atlas']['path'])

    if not Path(atlas_db_path).exists():
        click.echo(f"ERROR: ATLAS database not found at {atlas_db_path}", err=True)
        click.echo("Run 'atlas refresh' first to load data.", err=True)
        sys.exit(1)

    analytics = SupplyAnalytics(atlas_db_path)

    try:
        # Nearest port lookup
        if nearest_port:
            lat, lon = nearest_port
            click.echo(f"Finding nearest ports to ({lat}, {lon})...")
            click.echo("=" * 70)

            df = find_nearest_port(atlas_db_path, lat, lon, limit=10)

            if df.empty:
                click.echo("No ports found. Run 'atlas refresh --source ports' first.")
            else:
                click.echo(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
            return

        if state:
            # State summary
            click.echo(f"State Summary: {state}")
            click.echo("=" * 70)

            summary = analytics.get_state_summary(state)

            click.echo(f"\nTotal Facilities: {summary['total_facilities']:,}")

            if summary['top_naics_codes']:
                click.echo("\nTop NAICS Codes:")
                for item in summary['top_naics_codes'][:10]:
                    click.echo(f"  {item['naics_code']}: {item['count']} facilities")

            if summary['top_companies']:
                click.echo("\nTop Companies:")
                for item in summary['top_companies'][:10]:
                    click.echo(f"  {item['resolved_company']}: {item['count']} facilities")

            if summary['top_cities']:
                click.echo("\nTop Cities:")
                for item in summary['top_cities'][:10]:
                    click.echo(f"  {item['city']}: {item['count']} facilities")

        elif registry_id:
            # Facility details
            click.echo(f"Facility Details: {registry_id}")
            click.echo("=" * 70)

            df = analytics.get_facility_details(registry_id=registry_id)

            if df.empty:
                click.echo(f"No facility found with Registry ID: {registry_id}")
                return

            record = df.iloc[0]

            click.echo(f"\nRegistry ID:     {record['registry_id']}")
            click.echo(f"Facility Name:   {record['facility_name']}")
            click.echo(f"Address:         {record['street_address']}")
            click.echo(f"City:            {record['city']}")
            click.echo(f"State:           {record['state']}")
            click.echo(f"ZIP:             {record['zip']}")
            click.echo(f"County:          {record['county']}")

            if record['latitude'] and record['longitude']:
                click.echo(f"Coordinates:     {record['latitude']}, {record['longitude']}")

            if record['naics_codes']:
                click.echo(f"NAICS Codes:     {record['naics_codes']}")

            if 'resolved_company' in record and record['resolved_company']:
                click.echo(f"Company:         {record['resolved_company']} (score: {record['match_score']:.1f})")

        else:
            click.echo("Please provide either a registry_id or --state option")
            click.echo("Examples:")
            click.echo("  atlas info 110000123456")
            click.echo("  atlas info --state CA")
            click.echo("  atlas info --nearest-port 29.76 -95.36")

    except Exception as e:
        click.secho(f"[ERROR] Error: {e}", fg='red', err=True)
        logger.exception("Info command failed")
        sys.exit(1)


@cli.command()
@click.option('--plants', is_flag=True, help='Show cement plants with rail service')
@click.option('--no-rail', is_flag=True, help='Show cement plants WITHOUT rail service')
@click.option('--by-type', is_flag=True, help='Show facilities by type')
@click.option('--by-company', is_flag=True, help='Show rail network by company')
@click.option('--company', help='Filter by company name')
@click.option('--state', help='Filter by state code')
@click.option('--type', 'facility_type', help='Filter by facility type (CEMENT_PLANT, TERMINAL, etc.)')
@click.option('--limit', default=25, help='Maximum number of results')
@click.pass_context
def rail(ctx, plants, no_rail, by_type, by_company, company, state, facility_type, limit):
    """Query rail-served cement facilities.

    Examples:
        atlas rail --plants              # Cement plants with rail
        atlas rail --no-rail             # Cement plants without rail
        atlas rail --by-type             # Facilities by category
        atlas rail --by-company          # Rail network by company
        atlas rail --company CEMEX       # Sites for specific company
        atlas rail --state TX            # Sites in Texas
    """
    import duckdb

    config = ctx.obj['config']
    atlas_db_path = str(Path(__file__).parent / config['data']['atlas']['path'])

    if not Path(atlas_db_path).exists():
        click.echo(f"ERROR: ATLAS database not found at {atlas_db_path}", err=True)
        sys.exit(1)

    try:
        con = duckdb.connect(atlas_db_path, read_only=True)

        # Check if table exists
        tables = con.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'us_cement_facilities'").fetchall()
        if not tables:
            click.echo("ERROR: Rail facility data not loaded.", err=True)
            click.echo("Run the rail integration script first.", err=True)
            con.close()
            sys.exit(1)

        click.echo("=" * 70)
        click.echo("US CEMENT FACILITIES - RAIL SERVICE")
        click.echo("=" * 70)

        # Plants with rail
        if plants:
            click.echo("\nCEMENT PLANTS WITH RAIL SERVICE:\n")
            df = con.execute(f'''
                SELECT facility_name as plant, company, state,
                       ROUND(capacity_mtpa, 2) as capacity_mtpa,
                       rail_carrier as carriers
                FROM us_cement_facilities
                WHERE facility_type = 'CEMENT_PLANT' AND is_rail_served
                ORDER BY capacity_mtpa DESC
                LIMIT {limit}
            ''').fetchdf()
            click.echo(tabulate(df, headers='keys', tablefmt='psql', showindex=False))

            total = con.execute("SELECT COUNT(*) FROM us_cement_facilities WHERE facility_type = 'CEMENT_PLANT' AND is_rail_served").fetchone()[0]
            click.echo(f"\nTotal: {total} cement plants with rail service")
            con.close()
            return

        # Plants without rail
        if no_rail:
            click.echo("\nCEMENT PLANTS WITHOUT RAIL SERVICE:\n")
            df = con.execute(f'''
                SELECT facility_name as plant, company, state,
                       ROUND(capacity_mtpa, 2) as capacity_mtpa
                FROM us_cement_facilities
                WHERE facility_type = 'CEMENT_PLANT' AND NOT is_rail_served
                ORDER BY capacity_mtpa DESC
                LIMIT {limit}
            ''').fetchdf()
            click.echo(tabulate(df, headers='keys', tablefmt='psql', showindex=False))

            total = con.execute("SELECT COUNT(*) FROM us_cement_facilities WHERE facility_type = 'CEMENT_PLANT' AND NOT is_rail_served").fetchone()[0]
            click.echo(f"\nTotal: {total} cement plants without rail service")
            con.close()
            return

        # By type
        if by_type:
            click.echo("\nFACILITIES BY TYPE:\n")
            df = con.execute('''
                SELECT facility_type,
                       COUNT(*) as count,
                       SUM(CASE WHEN is_rail_served THEN 1 ELSE 0 END) as rail_served,
                       COUNT(DISTINCT company) as companies
                FROM us_cement_facilities
                GROUP BY facility_type
                ORDER BY count DESC
            ''').fetchdf()
            click.echo(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
            con.close()
            return

        # By company
        if by_company:
            click.echo("\nRAIL NETWORK BY COMPANY:\n")
            df = con.execute(f'''
                SELECT company,
                       COUNT(*) as total_sites,
                       SUM(CASE WHEN facility_type = 'CEMENT_PLANT' THEN 1 ELSE 0 END) as plants,
                       SUM(CASE WHEN facility_type = 'CEMENT_DISTRIBUTION' THEN 1 ELSE 0 END) as distribution,
                       SUM(CASE WHEN is_rail_served THEN 1 ELSE 0 END) as rail_served
                FROM us_cement_facilities
                GROUP BY company
                HAVING SUM(CASE WHEN facility_type = 'CEMENT_PLANT' THEN 1 ELSE 0 END) > 0
                ORDER BY total_sites DESC
                LIMIT {limit}
            ''').fetchdf()
            click.echo(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
            con.close()
            return

        # Filter by company
        if company:
            click.echo(f"\nSITES FOR: {company.upper()}\n")
            df = con.execute(f'''
                SELECT facility_name, facility_type, city, state,
                       CASE WHEN is_rail_served THEN 'YES' ELSE 'NO' END as rail,
                       rail_carrier
                FROM us_cement_facilities
                WHERE UPPER(company) LIKE '%{company.upper()}%'
                   OR UPPER(company_normalized) LIKE '%{company.upper()}%'
                ORDER BY facility_type, state
                LIMIT {limit}
            ''').fetchdf()
            click.echo(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
            con.close()
            return

        # Filter by state
        if state:
            click.echo(f"\nRAIL-SERVED SITES IN {state.upper()}:\n")
            df = con.execute(f'''
                SELECT facility_name, company, facility_type, city,
                       rail_carrier
                FROM us_cement_facilities
                WHERE UPPER(state) = '{state.upper()}' AND is_rail_served
                ORDER BY facility_type, company
                LIMIT {limit}
            ''').fetchdf()
            click.echo(tabulate(df, headers='keys', tablefmt='psql', showindex=False))

            total = con.execute(f"SELECT COUNT(*) FROM us_cement_facilities WHERE UPPER(state) = '{state.upper()}' AND is_rail_served").fetchone()[0]
            click.echo(f"\nTotal: {total} rail-served sites in {state.upper()}")
            con.close()
            return

        # Filter by facility type
        if facility_type:
            click.echo(f"\n{facility_type.upper()} FACILITIES:\n")
            df = con.execute(f'''
                SELECT facility_name, company, city, state,
                       CASE WHEN is_rail_served THEN 'YES' ELSE 'NO' END as rail,
                       rail_carrier
                FROM us_cement_facilities
                WHERE UPPER(facility_type) = '{facility_type.upper()}'
                ORDER BY company, state
                LIMIT {limit}
            ''').fetchdf()
            click.echo(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
            con.close()
            return

        # Default: summary
        click.echo("\nSUMMARY:\n")

        total = con.execute("SELECT COUNT(*) FROM us_cement_facilities").fetchone()[0]
        rail_total = con.execute("SELECT COUNT(*) FROM us_cement_facilities WHERE is_rail_served").fetchone()[0]
        plants_total = con.execute("SELECT COUNT(*) FROM us_cement_facilities WHERE facility_type = 'CEMENT_PLANT'").fetchone()[0]
        plants_rail = con.execute("SELECT COUNT(*) FROM us_cement_facilities WHERE facility_type = 'CEMENT_PLANT' AND is_rail_served").fetchone()[0]

        click.echo(f"Total Facilities:        {total:,}")
        click.echo(f"Rail-Served:             {rail_total:,} ({rail_total/total*100:.1f}%)")
        click.echo(f"Cement Plants:           {plants_total}")
        click.echo(f"  With Rail:             {plants_rail} ({plants_rail/plants_total*100:.1f}%)")
        click.echo(f"  Without Rail:          {plants_total - plants_rail}")

        click.echo("\nUse --plants, --by-type, --by-company, --state, or --company for details")

        con.close()

    except Exception as e:
        click.secho(f"[ERROR] Error: {e}", fg='red', err=True)
        logger.exception("Rail command failed")
        sys.exit(1)


@cli.command()
@click.option('--imports', is_flag=True, help='Show import market analysis')
@click.option('--capacity', is_flag=True, help='Show domestic production capacity')
@click.option('--flows', is_flag=True, help='Show top trade flows')
@click.option('--trends', is_flag=True, help='Show monthly import trends')
@click.option('--country', help='Filter imports by origin country')
@click.option('--port', help='Filter imports by US port')
@click.pass_context
def market(ctx, imports, capacity, flows, trends, country, port):
    """US cement market analytics.

    Examples:
        atlas market --imports          # Import market overview
        atlas market --capacity         # Domestic production capacity
        atlas market --flows            # Top trade flows
        atlas market --trends           # Monthly import trends
        atlas market --country Turkey   # Imports from Turkey
    """
    import duckdb

    config = ctx.obj['config']
    atlas_db_path = str(Path(__file__).parent / config['data']['atlas']['path'])

    try:
        con = duckdb.connect(atlas_db_path, read_only=True)

        click.echo("=" * 70)
        click.echo("US CEMENT MARKET ANALYTICS")
        click.echo("=" * 70)

        if capacity:
            click.echo("\nDOMESTIC PRODUCTION CAPACITY:\n")
            df = con.execute("""
                SELECT owner_name as company, COUNT(*) as plants,
                       ROUND(SUM(capacity_mtpa), 2) as capacity_mtpa
                FROM gem_cement_plants WHERE country = 'United States'
                GROUP BY owner_name ORDER BY capacity_mtpa DESC LIMIT 15
            """).fetchdf()
            click.echo(tabulate(df, headers='keys', tablefmt='psql', showindex=False))

            total = con.execute("SELECT ROUND(SUM(capacity_mtpa), 1) FROM gem_cement_plants WHERE country = 'United States'").fetchone()[0]
            click.echo(f"\nTotal US Capacity: {total} MTPA")
            con.close()
            return

        if flows:
            click.echo("\nTOP TRADE FLOWS:\n")
            df = con.execute("""
                SELECT origin_country, us_port, importer, shipments,
                       ROUND(total_tons/1000000, 2) as million_tons
                FROM trade_flows LIMIT 20
            """).fetchdf()
            click.echo(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
            con.close()
            return

        if trends:
            click.echo("\nMONTHLY IMPORT TRENDS:\n")
            df = con.execute("""
                SELECT year, month, shipments,
                       ROUND(SUM(total_tons)/1000000, 2) as million_tons
                FROM imports_monthly_trend
                GROUP BY year, month, shipments
                ORDER BY year DESC, month DESC LIMIT 24
            """).fetchdf()
            click.echo(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
            con.close()
            return

        if country:
            click.echo(f"\nIMPORTS FROM {country.upper()}:\n")
            df = con.execute(f"""
                SELECT port_of_unlading as us_port, consignee as importer,
                       COUNT(*) as shipments,
                       ROUND(SUM(weight_tons)/1000000, 2) as million_tons
                FROM trade_imports
                WHERE UPPER(origin_country) LIKE '%{country.upper()}%'
                GROUP BY port_of_unlading, consignee
                ORDER BY million_tons DESC LIMIT 20
            """).fetchdf()
            click.echo(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
            con.close()
            return

        if port:
            click.echo(f"\nIMPORTS TO {port.upper()}:\n")
            df = con.execute(f"""
                SELECT origin_country, consignee as importer,
                       COUNT(*) as shipments,
                       ROUND(SUM(weight_tons)/1000000, 2) as million_tons
                FROM trade_imports
                WHERE UPPER(port_of_unlading) LIKE '%{port.upper()}%'
                GROUP BY origin_country, consignee
                ORDER BY million_tons DESC LIMIT 20
            """).fetchdf()
            click.echo(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
            con.close()
            return

        # Default: imports overview
        if imports or True:
            stats = con.execute("""
                SELECT ROUND(SUM(weight_tons)/1000000, 1),
                       COUNT(*), COUNT(DISTINCT origin_country),
                       COUNT(DISTINCT port_of_unlading), COUNT(DISTINCT consignee)
                FROM trade_imports
            """).fetchone()

            click.echo(f"\nIMPORT MARKET OVERVIEW:")
            click.echo(f"  Total Volume:      {stats[0]} million metric tons")
            click.echo(f"  Shipments:         {stats[1]:,}")
            click.echo(f"  Source Countries:  {stats[2]}")
            click.echo(f"  Entry Ports:       {stats[3]}")
            click.echo(f"  Importers:         {stats[4]}")

            click.echo("\nTOP SOURCE COUNTRIES:")
            df = con.execute("SELECT * FROM imports_by_country LIMIT 10").fetchdf()
            click.echo(tabulate(df, headers='keys', tablefmt='psql', showindex=False))

            click.echo("\nTOP US PORTS:")
            df = con.execute("SELECT * FROM imports_by_port LIMIT 10").fetchdf()
            click.echo(tabulate(df, headers='keys', tablefmt='psql', showindex=False))

        con.close()

    except Exception as e:
        click.secho(f"[ERROR] Error: {e}", fg='red', err=True)
        logger.exception("Market command failed")
        sys.exit(1)


if __name__ == '__main__':
    cli(obj={})
