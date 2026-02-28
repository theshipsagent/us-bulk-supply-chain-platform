#!/usr/bin/env python3
"""
Fly Ash ATLAS CLI - Command Line Interface
=============================================
Click-based CLI for Fly Ash/CCP ATLAS project operations.

Commands:
    refresh  - Refresh data from EPA FRS, run entity resolution
    query    - Query facility data with filters
    stats    - Show database statistics
    info     - Show facility information or state summary
    plants   - Show coal power plant and ash processor data
"""

import click
import yaml
import logging
import sys
from pathlib import Path
from tabulate import tabulate

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from etl.epa_frs import EPAFRSLoader
from etl.facility_master import FacilityMasterBuilder
from harmonize.entity_resolver import EntityResolver
from analytics.supply import SupplyAnalytics

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
    """Fly Ash ATLAS - Analytical Tool for Logistics, Assets, Trade & Supply (Fly Ash/CCP)"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = load_config(config)


@cli.command()
@click.option('--source', type=click.Choice(['epa', 'entities', 'master', 'all']),
              default='epa', help='Data source to refresh')
@click.pass_context
def refresh(ctx, source):
    """Refresh data from specified source(s).

    Sources:
        epa      - EPA FRS facilities (coal plants, ash processors, cement end users) [default]
        entities - Run entity resolution on loaded facilities
        master   - Build master facilities table
        all      - Refresh all sources in order
    """
    config = ctx.obj['config']

    click.echo("=" * 70)
    click.echo("FLY ASH ATLAS DATA REFRESH")
    click.echo("=" * 70)

    atlas_db_path = str(Path(__file__).parent / config['data']['atlas']['path'])
    click.echo(f"ATLAS Database: {atlas_db_path}")
    click.echo("")

    Path(atlas_db_path).parent.mkdir(parents=True, exist_ok=True)

    sources_to_load = ['epa', 'entities', 'master'] if source == 'all' else [source]

    try:
        if 'epa' in sources_to_load:
            frs_db_path = str(Path(__file__).parent / config['data']['epa_frs']['path'])
            naics_config_path = str(Path(__file__).parent / config['naics']['flyash_config'])

            click.echo(f"[FRS] Loading EPA FRS data for fly ash/CCP...")
            click.echo(f"      Source: {frs_db_path}")

            if not Path(frs_db_path).exists():
                click.echo(f"[WARN] FRS database not found at {frs_db_path}", err=True)
            else:
                loader = EPAFRSLoader(frs_db_path, atlas_db_path, naics_config_path)
                loader.refresh()
                click.secho("[OK] EPA FRS data loaded successfully", fg='green')
            click.echo("")

        if 'entities' in sources_to_load:
            companies_config_path = str(Path(__file__).parent / config['entity_resolution']['target_companies'])
            threshold = config['entity_resolution']['fuzzy_threshold']

            click.echo(f"[ENTITIES] Running entity resolution...")

            if not Path(atlas_db_path).exists():
                click.echo("[WARN] ATLAS database not found. Run 'refresh --source epa' first.", err=True)
            else:
                import duckdb
                con = duckdb.connect(atlas_db_path, read_only=True)
                try:
                    df = con.execute("SELECT * FROM frs_facilities").fetchdf()
                finally:
                    con.close()

                if df.empty:
                    click.echo("[WARN] No facilities in database.", err=True)
                else:
                    resolver = EntityResolver(companies_config_path, threshold)
                    resolved_df = resolver.resolve_entities(df)
                    resolver.save_resolved(resolved_df, atlas_db_path)

                    matched = resolved_df['resolved_company'].notna().sum()
                    click.secho(
                        f"[OK] Entity resolution complete: {matched:,} of {len(resolved_df):,} matched",
                        fg='green'
                    )
            click.echo("")

        if 'master' in sources_to_load:
            click.echo("[MASTER] Building master facilities table...")

            if not Path(atlas_db_path).exists():
                click.echo("[WARN] ATLAS database not found.", err=True)
            else:
                builder = FacilityMasterBuilder(atlas_db_path)
                tables = builder.check_source_tables()
                if not tables['frs_facilities']:
                    click.echo("[WARN] No source tables available.", err=True)
                else:
                    builder.build_master()
                    click.secho("[OK] Master facilities table built", fg='green')
            click.echo("")

        click.secho("[OK] Data refresh complete", fg='green', bold=True)

    except Exception as e:
        click.secho(f"[ERROR] Error during refresh: {e}", fg='red', err=True)
        logger.exception("Refresh failed")
        sys.exit(1)


@cli.command()
@click.option('--state', help='Filter by state code')
@click.option('--naics', help='Filter by NAICS code prefix')
@click.option('--company', help='Filter by company name')
@click.option('--category', type=click.Choice([
    'Coal Power (Fly Ash Source)', 'Ash Processing/Harvesting',
    'Cement/Concrete End User', 'Distribution'
]), help='Filter by facility category')
@click.option('--limit', default=25, help='Maximum results')
@click.option('--output', type=click.Path(), help='Export to CSV')
@click.pass_context
def query(ctx, state, naics, company, category, limit, output):
    """Query facility data with filters.

    Examples:
        flyash-atlas query --state WV
        flyash-atlas query --category "Coal Power (Fly Ash Source)"
        flyash-atlas query --company "Duke Energy"
        flyash-atlas query --naics 221112
    """
    config = ctx.obj['config']
    atlas_db_path = str(Path(__file__).parent / config['data']['atlas']['path'])

    if not Path(atlas_db_path).exists():
        click.echo("ERROR: ATLAS database not found. Run 'refresh --source epa' first.", err=True)
        sys.exit(1)

    try:
        analytics = SupplyAnalytics(atlas_db_path)

        if naics and not state and not company:
            click.echo(f"Querying facilities with NAICS {naics}...")
            df = analytics.count_by_naics(naics)
        elif state and not naics and not company:
            click.echo(f"Querying facilities in {state}...")
            df = analytics.get_facility_details(state=state, category=category, limit=limit)
        elif company:
            click.echo(f"Querying facilities for company: {company}...")
            df = analytics.get_facility_details(company=company, limit=limit)
        elif category:
            click.echo(f"Querying {category} facilities...")
            df = analytics.get_facility_details(category=category, limit=limit)
        else:
            df = analytics.get_facility_details(limit=limit)

        if df.empty:
            click.echo("No results found.")
            return

        click.echo(f"\nFound {len(df)} results:\n")

        display_df = df.head(limit)
        if 'naics_codes' in display_df.columns:
            display_df = display_df.copy()
            display_df['naics_codes'] = display_df['naics_codes'].apply(
                lambda x: str(x)[:30] + '...' if x and len(str(x)) > 30 else x
            )

        click.echo(tabulate(display_df, headers='keys', tablefmt='psql', showindex=False))

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
@click.option('--by-category', is_flag=True, help='Show breakdown by facility category')
@click.pass_context
def stats(ctx, by_state, by_naics, by_company, by_category):
    """Show database statistics."""
    config = ctx.obj['config']
    atlas_db_path = str(Path(__file__).parent / config['data']['atlas']['path'])

    if not Path(atlas_db_path).exists():
        click.echo("ERROR: ATLAS database not found.", err=True)
        sys.exit(1)

    try:
        analytics = SupplyAnalytics(atlas_db_path)

        click.echo("=" * 70)
        click.echo("FLY ASH ATLAS DATABASE STATISTICS")
        click.echo("=" * 70)

        db_stats = analytics.get_database_stats()

        click.echo(f"\nTotal Facilities:          {db_stats['total_facilities']:,}")
        click.echo(f"States Covered:            {db_stats['total_states']}")
        click.echo(f"Facilities with Coords:    {db_stats['facilities_with_coords']:,}")
        click.echo(f"Facilities with Company:   {db_stats['facilities_with_company']:,}")
        click.echo(f"Unique Companies:          {db_stats['unique_companies']}")

        if db_stats['last_load_timestamp']:
            click.echo(f"Last Updated:              {db_stats['last_load_timestamp']}")

        if db_stats.get('by_category'):
            click.echo("\nFacility Categories:")
            for item in db_stats['by_category']:
                click.echo(f"  {item['naics_category']}: {item['count']:,}")

        if by_state:
            click.echo("\n" + "=" * 70)
            click.echo("FACILITIES BY STATE (Top 25)")
            click.echo("=" * 70)
            df = analytics.count_by_state()
            click.echo(tabulate(df.head(25), headers='keys', tablefmt='psql', showindex=False))

        if by_naics:
            click.echo("\n" + "=" * 70)
            click.echo("FACILITIES BY NAICS CODE")
            click.echo("=" * 70)
            df = analytics.count_by_naics()
            click.echo(tabulate(df.head(20), headers='keys', tablefmt='psql', showindex=False))

        if by_category:
            click.echo("\n" + "=" * 70)
            click.echo("FACILITIES BY CATEGORY")
            click.echo("=" * 70)
            df = analytics.count_by_category()
            click.echo(tabulate(df, headers='keys', tablefmt='psql', showindex=False))

        if by_company:
            click.echo("\n" + "=" * 70)
            click.echo("FACILITIES BY COMPANY (Top 25)")
            click.echo("=" * 70)
            df = analytics.count_by_company()
            if not df.empty:
                click.echo(tabulate(df.head(25), headers='keys', tablefmt='psql', showindex=False))
            else:
                click.echo("No company data. Run 'refresh --source entities' first.")

    except Exception as e:
        click.secho(f"[ERROR] Error: {e}", fg='red', err=True)
        logger.exception("Stats failed")
        sys.exit(1)


@cli.command()
@click.option('--coal', is_flag=True, help='Show coal power plants (fly ash source)')
@click.option('--ash-processors', is_flag=True, help='Show ash processing/harvesting facilities')
@click.option('--all-plants', 'show_all', is_flag=True, help='Show all coal plants and ash processors')
@click.pass_context
def plants(ctx, coal, ash_processors, show_all):
    """Show coal power plant and ash processor data.

    Coal power plants produce fly ash; ash processors harvest and market it.

    Examples:
        flyash-atlas plants --coal            # Fly ash source plants
        flyash-atlas plants --ash-processors  # Ash processing facilities
        flyash-atlas plants --all-plants      # All source + processing
    """
    config = ctx.obj['config']
    atlas_db_path = str(Path(__file__).parent / config['data']['atlas']['path'])

    if not Path(atlas_db_path).exists():
        click.echo("ERROR: ATLAS database not found.", err=True)
        sys.exit(1)

    try:
        analytics = SupplyAnalytics(atlas_db_path)

        if coal:
            click.echo("=" * 70)
            click.echo("COAL POWER PLANTS (FLY ASH SOURCE)")
            click.echo("=" * 70)
            df = analytics.get_coal_plants(plant_type='coal')
        elif ash_processors:
            click.echo("=" * 70)
            click.echo("ASH PROCESSING / HARVESTING FACILITIES")
            click.echo("=" * 70)
            df = analytics.get_coal_plants(plant_type='ash-processors')
        elif show_all:
            click.echo("=" * 70)
            click.echo("ALL COAL PLANTS AND ASH PROCESSORS")
            click.echo("=" * 70)
            df = analytics.get_coal_plants()
        else:
            # Default: summary
            click.echo("=" * 70)
            click.echo("FLY ASH SOURCE SUMMARY")
            click.echo("=" * 70)

            coal_df = analytics.get_coal_plants(plant_type='coal')
            ash_df = analytics.get_coal_plants(plant_type='ash-processors')

            click.echo(f"\nCoal Power (fly ash source):     {len(coal_df):,} facilities")
            click.echo(f"Ash Processing/Harvesting:       {len(ash_df):,} facilities")
            click.echo(f"Total:                           {len(coal_df) + len(ash_df):,} facilities")
            click.echo("\nUse --coal, --ash-processors, or --all-plants for details")
            return

        if df.empty:
            click.echo("\nNo facilities found.")
            return

        click.echo(f"\nFound {len(df)} facilities:\n")

        display_cols = ['facility_name', 'city', 'state', 'naics_category']
        if 'resolved_company' in df.columns:
            display_cols.append('resolved_company')
        display_df = df[[c for c in display_cols if c in df.columns]]

        click.echo(tabulate(display_df, headers='keys', tablefmt='psql', showindex=False))

    except Exception as e:
        click.secho(f"[ERROR] Error: {e}", fg='red', err=True)
        logger.exception("Plants command failed")
        sys.exit(1)


@cli.command()
@click.argument('registry_id', required=False)
@click.option('--state', help='Get state summary')
@click.pass_context
def info(ctx, registry_id, state):
    """Show detailed facility information or state summary."""
    config = ctx.obj['config']
    atlas_db_path = str(Path(__file__).parent / config['data']['atlas']['path'])

    if not Path(atlas_db_path).exists():
        click.echo("ERROR: ATLAS database not found.", err=True)
        sys.exit(1)

    analytics = SupplyAnalytics(atlas_db_path)

    try:
        if state:
            click.echo(f"State Summary: {state}")
            click.echo("=" * 70)

            summary = analytics.get_state_summary(state)
            click.echo(f"\nTotal Facilities: {summary['total_facilities']:,}")

            if summary.get('categories'):
                click.echo("\nBy Category:")
                for item in summary['categories']:
                    click.echo(f"  {item['naics_category']}: {item['count']} facilities")

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
            click.echo(f"Facility Details: {registry_id}")
            click.echo("=" * 70)

            df = analytics.get_facility_details(registry_id=registry_id)
            if df.empty:
                click.echo(f"No facility found with Registry ID: {registry_id}")
                return

            record = df.iloc[0]
            click.echo(f"\nRegistry ID:     {record['registry_id']}")
            click.echo(f"Facility Name:   {record['facility_name']}")
            if 'street_address' in record:
                click.echo(f"Address:         {record['street_address']}")
            click.echo(f"City:            {record['city']}")
            click.echo(f"State:           {record['state']}")
            if record.get('latitude') and record.get('longitude'):
                click.echo(f"Coordinates:     {record['latitude']}, {record['longitude']}")
            if record.get('naics_codes'):
                click.echo(f"NAICS Codes:     {record['naics_codes']}")
            if record.get('naics_category'):
                click.echo(f"Category:        {record['naics_category']}")
            if 'resolved_company' in record and record.get('resolved_company'):
                click.echo(f"Company:         {record['resolved_company']} (score: {record['match_score']:.1f})")
        else:
            click.echo("Please provide either a registry_id or --state option")
            click.echo("Examples:")
            click.echo("  flyash-atlas info 110000123456")
            click.echo("  flyash-atlas info --state WV")

    except Exception as e:
        click.secho(f"[ERROR] Error: {e}", fg='red', err=True)
        logger.exception("Info command failed")
        sys.exit(1)


if __name__ == '__main__':
    cli(obj={})
