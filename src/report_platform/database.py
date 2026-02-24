"""DuckDB master analytics database management.

Provides initialization, status, and schema management for the
platform's analytical databases.
"""

from pathlib import Path

import click

from report_platform.config import get_databases_config, get_project_root

try:
    import duckdb
except ImportError:
    duckdb = None


def _resolve_db_path(rel_path: str) -> Path:
    """Resolve a config-relative database path to absolute."""
    return get_project_root() / rel_path


def show_db_status() -> None:
    """Print status of all configured databases."""
    if duckdb is None:
        click.echo("duckdb is not installed. Run: pip install duckdb")
        return

    dbs = get_databases_config()
    if not dbs:
        click.echo("No databases configured in config.yaml.")
        return

    click.echo()
    click.echo(f"{'Database':<22} {'Engine':<10} {'Status':<12} {'Tables':<8} {'Size':<12} Path")
    click.echo("-" * 90)

    for name, cfg in sorted(dbs.items()):
        engine = cfg.get("engine", "unknown")
        db_path = _resolve_db_path(cfg["path"])

        if not db_path.exists():
            status = click.style("NOT INIT", fg="yellow")
            click.echo(f"  {name:<20} {engine:<10} {status:<20} {'—':<8} {'—':<12} {db_path}")
            continue

        size_mb = db_path.stat().st_size / (1024 * 1024)
        try:
            con = duckdb.connect(str(db_path), read_only=True)
            tables = con.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main'"
            ).fetchall()
            con.close()
            table_count = len(tables)
            status = click.style("OK", fg="green")
        except Exception as e:
            table_count = "?"
            status = click.style("ERROR", fg="red")
            click.echo(f"  {name}: {e}")

        click.echo(
            f"  {name:<20} {engine:<10} {status:<20} "
            f"{str(table_count):<8} {size_mb:>8.1f} MB   {db_path}"
        )

    click.echo()


# ---------------------------------------------------------------------------
# Master analytics schema
# ---------------------------------------------------------------------------

_MASTER_SCHEMA = """
-- Waterway segments and lock chambers
CREATE TABLE IF NOT EXISTS waterway_segments (
    segment_id    VARCHAR PRIMARY KEY,
    waterway      VARCHAR NOT NULL,
    from_mile     DOUBLE,
    to_mile       DOUBLE,
    state         VARCHAR(2),
    navigable     BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS lock_chambers (
    lock_id       VARCHAR PRIMARY KEY,
    lock_name     VARCHAR NOT NULL,
    waterway      VARCHAR,
    river_mile    DOUBLE,
    state         VARCHAR(2),
    latitude      DOUBLE,
    longitude     DOUBLE,
    chamber_count INTEGER DEFAULT 1
);

-- Port and terminal facilities
CREATE TABLE IF NOT EXISTS ports (
    port_id       VARCHAR PRIMARY KEY,
    port_name     VARCHAR NOT NULL,
    state         VARCHAR(2),
    latitude      DOUBLE,
    longitude     DOUBLE,
    port_type     VARCHAR,
    customs_district VARCHAR
);

CREATE TABLE IF NOT EXISTS terminals (
    terminal_id   VARCHAR PRIMARY KEY,
    terminal_name VARCHAR NOT NULL,
    port_id       VARCHAR REFERENCES ports(port_id),
    commodity     VARCHAR,
    capacity_tons DOUBLE,
    latitude      DOUBLE,
    longitude     DOUBLE
);

-- Rail network reference
CREATE TABLE IF NOT EXISTS rail_nodes (
    node_id       VARCHAR PRIMARY KEY,
    node_name     VARCHAR,
    state         VARCHAR(2),
    latitude      DOUBLE,
    longitude     DOUBLE,
    node_type     VARCHAR
);

CREATE TABLE IF NOT EXISTS rail_segments (
    segment_id    VARCHAR PRIMARY KEY,
    from_node     VARCHAR REFERENCES rail_nodes(node_id),
    to_node       VARCHAR REFERENCES rail_nodes(node_id),
    railroad      VARCHAR,
    miles         DOUBLE,
    track_class   INTEGER
);

-- Facility registry (EPA FRS summary)
CREATE TABLE IF NOT EXISTS facilities (
    registry_id   VARCHAR PRIMARY KEY,
    facility_name VARCHAR NOT NULL,
    state         VARCHAR(2),
    city          VARCHAR,
    latitude      DOUBLE,
    longitude     DOUBLE,
    naics_primary VARCHAR,
    sic_primary   VARCHAR
);

-- Commodity trade flows
CREATE TABLE IF NOT EXISTS trade_flows (
    flow_id       INTEGER PRIMARY KEY,
    year          INTEGER,
    month         INTEGER,
    hts_code      VARCHAR,
    commodity     VARCHAR,
    origin        VARCHAR,
    destination   VARCHAR,
    tons          DOUBLE,
    value_usd     DOUBLE,
    mode          VARCHAR
);

-- Cost model results cache
CREATE TABLE IF NOT EXISTS cost_estimates (
    estimate_id   INTEGER PRIMARY KEY,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mode          VARCHAR NOT NULL,
    origin        VARCHAR,
    destination   VARCHAR,
    commodity     VARCHAR,
    tons          DOUBLE,
    cost_usd      DOUBLE,
    cost_per_ton  DOUBLE,
    parameters    VARCHAR
);
"""


def init_master_db(force: bool = False) -> None:
    """Initialize the master analytics DuckDB database with base schema."""
    if duckdb is None:
        click.echo("duckdb is not installed. Run: pip install duckdb")
        return

    dbs = get_databases_config()
    master_cfg = dbs.get("master_analytics")
    if not master_cfg:
        click.echo("No 'master_analytics' database in config.yaml.")
        return

    db_path = _resolve_db_path(master_cfg["path"])
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if db_path.exists() and force:
        click.echo(f"Dropping existing database: {db_path}")
        db_path.unlink()
    elif db_path.exists() and not force:
        click.echo(f"Database already exists: {db_path}")
        click.echo("Use --force to reinitialize.")

    click.echo(f"Initializing master analytics database at {db_path} ...")
    con = duckdb.connect(str(db_path))

    for statement in _MASTER_SCHEMA.strip().split(";"):
        statement = statement.strip()
        if statement:
            con.execute(statement)

    tables = con.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'main'"
    ).fetchall()
    con.close()

    click.echo(f"Created {len(tables)} tables:")
    for (t,) in sorted(tables):
        click.echo(f"  - {t}")
    click.echo("Done.")
