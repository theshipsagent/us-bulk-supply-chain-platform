"""EPA FRS Analytics Tool - CLI Interface."""

import logging
import sys
from pathlib import Path

import click

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.etl import download, ingest
from src.analyze import query_engine, stats
from src.harmonize import entity_resolver

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """EPA FRS Analytics Tool - Manage and analyze EPA Facility Registry Service data."""
    pass


@cli.group()
def download_cmd():
    """Download EPA FRS data from various sources."""
    pass


@cli.group()
def ingest_cmd():
    """Ingest and load data into DuckDB."""
    pass


@cli.group()
def query():
    """Query facilities and program data."""
    pass


@cli.group()
def stats_cmd():
    """Get statistical summaries and analyses."""
    pass


@cli.group()
def harmonize():
    """Entity harmonization and parent company rollup."""
    pass


# Download commands
@download_cmd.command(name='echo')
@click.option('--force', is_flag=True, help='Force re-download even if files exist')
def download_echo(force):
    """Download ECHO FRS simplified CSV files."""
    click.echo("Downloading ECHO FRS files...")
    success = download.download_echo_files(force=force)

    if success:
        click.secho("[OK] Download complete!", fg='green')
    else:
        click.secho("[ERROR] Download failed", fg='red')
        sys.exit(1)


@download_cmd.command(name='national')
@click.option('--force', is_flag=True, help='Force re-download even if file exists')
def download_national(force):
    """Download EPA FRS National Combined ZIP file."""
    click.echo("Downloading National Combined ZIP (this may take a while)...")
    success = download.download_national_combined(force=force)

    if success:
        click.secho("[OK] Download and extraction complete!", fg='green')
    else:
        click.secho("[ERROR] Download failed", fg='red')
        sys.exit(1)


@download_cmd.command(name='state')
@click.argument('state_abbr')
@click.option('--force', is_flag=True, help='Force re-download even if file exists')
def download_state(state_abbr, force):
    """Download individual state CSV files."""
    click.echo(f"Downloading state data for {state_abbr}...")
    success = download.download_state_csv(state_abbr, force=force)

    if success:
        click.secho("[OK] Download and extraction complete!", fg='green')
    else:
        click.secho("[ERROR] Download failed", fg='red')
        sys.exit(1)


# Ingest commands
@ingest_cmd.command(name='echo')
@click.option('--force', is_flag=True, help='Drop and recreate tables if they exist')
def ingest_echo(force):
    """Ingest ECHO FRS CSV files into DuckDB."""
    click.echo("Ingesting ECHO FRS files into DuckDB...")

    try:
        conn = ingest.get_db_connection()
        row_counts = ingest.ingest_echo_files(conn, force=force)

        click.secho("[OK] Ingest complete!", fg='green')

        # Print summary
        ingest.print_ingest_summary(conn)

        conn.close()

    except Exception as e:
        logger.error(f"Ingest failed: {e}", exc_info=True)
        click.secho(f"[ERROR] Ingest failed: {e}", fg='red')
        sys.exit(1)


# Query commands
@query.command(name='facilities')
@click.option('--state', help='Filter by state code (e.g., VA)')
@click.option('--naics', 'naics_prefix', help='Filter by NAICS code prefix (e.g., 325)')
@click.option('--name', 'name_pattern', help='Filter by facility name pattern')
@click.option('--city', help='Filter by city name')
@click.option('--limit', default=100, help='Maximum number of results')
@click.option('--format', 'output_format', type=click.Choice(['table', 'csv']), default='table',
              help='Output format')
def query_facilities_cmd(state, naics_prefix, name_pattern, city, limit, output_format):
    """Query facilities with flexible filters."""
    try:
        df = query_engine.query_facilities(
            state=state,
            naics_prefix=naics_prefix,
            name_pattern=name_pattern,
            city=city,
            limit=limit,
            output_format=output_format
        )

        click.echo(f"\nReturned {len(df)} rows")

    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        click.secho(f"[ERROR] Query failed: {e}", fg='red')
        sys.exit(1)


@query.command(name='programs')
@click.argument('registry_id')
@click.option('--format', 'output_format', type=click.Choice(['table', 'csv']), default='table',
              help='Output format')
def query_programs_cmd(registry_id, output_format):
    """Get all program linkages for a specific facility."""
    try:
        df = query_engine.query_facility_programs(registry_id, output_format=output_format)

        if len(df) == 0:
            click.secho(f"No program links found for Registry ID: {registry_id}", fg='yellow')
        else:
            click.echo(f"\nFound {len(df)} program links")

    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        click.secho(f"[ERROR] Query failed: {e}", fg='red')
        sys.exit(1)


@query.command(name='naics')
@click.argument('registry_id')
@click.option('--format', 'output_format', type=click.Choice(['table', 'csv']), default='table',
              help='Output format')
def query_naics_cmd(registry_id, output_format):
    """Get all NAICS codes for a specific facility."""
    try:
        df = query_engine.query_facility_naics(registry_id, output_format=output_format)

        if len(df) == 0:
            click.secho(f"No NAICS codes found for Registry ID: {registry_id}", fg='yellow')
        else:
            click.echo(f"\nFound {len(df)} NAICS codes")

    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        click.secho(f"[ERROR] Query failed: {e}", fg='red')
        sys.exit(1)


# Stats commands
@stats_cmd.command(name='summary')
@click.option('--state', help='Filter by state code')
@click.option('--naics-prefix', help='Filter by NAICS prefix')
def stats_summary(state, naics_prefix):
    """Display summary statistics."""
    try:
        stats.print_summary_stats(state=state, naics_prefix=naics_prefix)
    except Exception as e:
        logger.error(f"Stats failed: {e}", exc_info=True)
        click.secho(f"[ERROR] Stats failed: {e}", fg='red')
        sys.exit(1)


@stats_cmd.command(name='naics-distribution')
@click.option('--state', help='Filter by state code')
@click.option('--top', default=20, help='Number of top codes to show')
@click.option('--digits', default=2, type=click.IntRange(2, 6),
              help='NAICS digit level (2, 3, 4, or 6)')
@click.option('--format', 'output_format', type=click.Choice(['table', 'csv']), default='table',
              help='Output format')
def stats_naics_distribution(state, top, digits, output_format):
    """Show NAICS code distribution."""
    try:
        query_engine.get_naics_distribution(
            state=state,
            digit_level=digits,
            top_n=top,
            output_format=output_format
        )
    except Exception as e:
        logger.error(f"Stats failed: {e}", exc_info=True)
        click.secho(f"[ERROR] Stats failed: {e}", fg='red')
        sys.exit(1)


@stats_cmd.command(name='by-state')
@click.option('--format', 'output_format', type=click.Choice(['table', 'csv']), default='table',
              help='Output format')
def stats_by_state(output_format):
    """Show facility count by state."""
    try:
        query_engine.get_facility_count_by_state(output_format=output_format)
    except Exception as e:
        logger.error(f"Stats failed: {e}", exc_info=True)
        click.secho(f"[ERROR] Stats failed: {e}", fg='red')
        sys.exit(1)


@stats_cmd.command(name='by-epa-region')
@click.option('--format', 'output_format', type=click.Choice(['table', 'csv']), default='table',
              help='Output format')
def stats_by_epa_region(output_format):
    """Show facility count by EPA region."""
    try:
        query_engine.get_facility_count_by_epa_region(output_format=output_format)
    except Exception as e:
        logger.error(f"Stats failed: {e}", exc_info=True)
        click.secho(f"[ERROR] Stats failed: {e}", fg='red')
        sys.exit(1)


@stats_cmd.command(name='programs')
@click.option('--format', 'output_format', type=click.Choice(['table', 'csv']), default='table',
              help='Output format')
def stats_programs(output_format):
    """Show program system summary."""
    try:
        query_engine.get_program_summary(output_format=output_format)
    except Exception as e:
        logger.error(f"Stats failed: {e}", exc_info=True)
        click.secho(f"[ERROR] Stats failed: {e}", fg='red')
        sys.exit(1)


@stats_cmd.command(name='null-rates')
def stats_null_rates():
    """Analyze null rates in facilities table."""
    try:
        stats.get_null_rate_analysis()
    except Exception as e:
        logger.error(f"Stats failed: {e}", exc_info=True)
        click.secho(f"[ERROR] Stats failed: {e}", fg='red')
        sys.exit(1)


# Harmonize commands
@harmonize.command(name='create-parent-table')
@click.option('--min-facilities', default=3, help='Minimum facilities to suggest parent company')
def harmonize_create_parent_table(min_facilities):
    """Create parent company lookup table from facility names."""
    try:
        click.echo("Analyzing facility names and creating parent company mappings...")
        conn = entity_resolver.get_db_connection()

        # Suggest parent companies first
        suggestions = entity_resolver.suggest_parent_companies(
            conn,
            min_facilities=min_facilities
        )

        click.echo(f"\nFound {len(suggestions)} potential parent companies")
        click.echo("\nTop 10 Parent Companies:")
        for idx, row in suggestions.head(10).iterrows():
            click.echo(f"  {row['base_company']:30s} - {row['facility_count']:5d} facilities across {len(row['fac_name'])} name variations")

        # Create the parent company table
        entity_resolver.create_parent_company_table(conn)

        # Analyze coverage
        coverage = entity_resolver.analyze_parent_company_coverage(conn)

        click.secho("\n[OK] Parent company lookup table created!", fg='green')
        click.echo(f"\nCovered {len(coverage)} parent companies")

        conn.close()

    except Exception as e:
        logger.error(f"Harmonization failed: {e}", exc_info=True)
        click.secho(f"[ERROR] Harmonization failed: {e}", fg='red')
        sys.exit(1)


@harmonize.command(name='analyze')
@click.option('--min-facilities', default=5, help='Minimum facilities to include in analysis')
def harmonize_analyze(min_facilities):
    """Analyze facility names and show suggested parent company rollups."""
    try:
        click.echo("Analyzing facility name patterns...")
        conn = entity_resolver.get_db_connection()

        suggestions = entity_resolver.suggest_parent_companies(
            conn,
            min_facilities=min_facilities
        )

        click.echo(f"\nFound {len(suggestions)} parent companies with multiple facility names")
        click.echo("\nTop 20 Parent Company Groupings:")
        click.echo("="*100)

        for idx, row in suggestions.head(20).iterrows():
            click.echo(f"\n{row['base_company']} ({row['facility_count']} facilities):")
            for name in row['fac_name'][:5]:  # Show first 5 variations
                click.echo(f"  - {name}")
            if len(row['fac_name']) > 5:
                click.echo(f"  ... and {len(row['fac_name'])-5} more variations")

        conn.close()

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        click.secho(f"[ERROR] Analysis failed: {e}", fg='red')
        sys.exit(1)


@harmonize.command(name='export')
@click.option('--naics', help='Filter by NAICS code prefix (e.g., 3273 for cement)')
@click.option('--output', default='facilities_with_parent.csv', help='Output filename')
def harmonize_export(naics, output):
    """Export facilities with parent company rollup."""
    try:
        conn = entity_resolver.get_db_connection()

        # Check if parent_company_lookup table exists
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").df()
        if 'parent_company_lookup' not in tables['name'].values:
            click.secho("[ERROR] Parent company lookup table not found!", fg='red')
            click.echo("Run 'python cli.py harmonize create-parent-table' first")
            sys.exit(1)

        click.echo(f"Exporting facilities with parent company rollup...")

        naics_filter = f"{naics}%" if naics else None
        df = entity_resolver.export_facilities_with_parent(
            conn,
            naics_filter=naics_filter,
            output_file=output
        )

        click.secho(f"\n[OK] Exported {len(df)} facilities to {output}", fg='green')

        # Show summary by parent company
        summary = df.groupby('parent_company').size().sort_values(ascending=False).head(20)
        click.echo("\nTop 20 Parent Companies:")
        for parent, count in summary.items():
            click.echo(f"  {parent:40s}: {count:5d} facilities")

        conn.close()

    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        click.secho(f"[ERROR] Export failed: {e}", fg='red')
        sys.exit(1)


@harmonize.command(name='coverage')
def harmonize_coverage():
    """Show parent company coverage statistics."""
    try:
        conn = entity_resolver.get_db_connection()

        # Check if table exists
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").df()
        if 'parent_company_lookup' not in tables['name'].values:
            click.secho("[ERROR] Parent company lookup table not found!", fg='red')
            click.echo("Run 'python cli.py harmonize create-parent-table' first")
            sys.exit(1)

        coverage = entity_resolver.analyze_parent_company_coverage(conn)

        click.echo("\n" + "="*120)
        click.echo("PARENT COMPANY COVERAGE (5+ facilities)")
        click.echo("="*120)

        from tabulate import tabulate
        print(tabulate(coverage.head(30), headers='keys', tablefmt='psql', showindex=False))

        conn.close()

    except Exception as e:
        logger.error(f"Coverage analysis failed: {e}", exc_info=True)
        click.secho(f"[ERROR] Coverage analysis failed: {e}", fg='red')
        sys.exit(1)


# Register command groups
cli.add_command(download_cmd, name='download')
cli.add_command(ingest_cmd, name='ingest')
cli.add_command(query)
cli.add_command(stats_cmd, name='stats')
cli.add_command(harmonize)


if __name__ == '__main__':
    cli()
