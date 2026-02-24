"""Data source freshness tracker.

Scans 01_DATA_SOURCES/ and compares file modification dates against
the configured refresh cadence to report staleness.
"""

import datetime as dt
from pathlib import Path

import click

from report_platform.config import get_data_sources_config, get_project_root


# Map refresh cadence strings to approximate day thresholds
_CADENCE_DAYS = {
    "daily": 2,
    "weekly": 10,
    "monthly": 45,
    "quarterly": 120,
    "annual": 400,
}


def _newest_file(directory: Path) -> tuple[Path | None, dt.datetime | None]:
    """Return the newest file in *directory* (recursive) and its mtime."""
    newest: Path | None = None
    newest_mtime: float = 0.0
    if not directory.exists():
        return None, None
    for p in directory.rglob("*"):
        if p.is_file() and not p.name.startswith("."):
            mt = p.stat().st_mtime
            if mt > newest_mtime:
                newest = p
                newest_mtime = mt
    if newest is None:
        return None, None
    return newest, dt.datetime.fromtimestamp(newest_mtime)


def _freshness_label(mtime: dt.datetime | None, cadence: str) -> str:
    """Return a coloured freshness label."""
    if mtime is None:
        return click.style("NO DATA", fg="red")
    age_days = (dt.datetime.now() - mtime).days
    threshold = _CADENCE_DAYS.get(cadence, 365)
    if age_days <= threshold:
        return click.style("FRESH", fg="green")
    elif age_days <= threshold * 2:
        return click.style("STALE", fg="yellow")
    else:
        return click.style("EXPIRED", fg="red")


def _source_directory(source_key: str) -> Path:
    """Best-effort mapping from config key to a data-sources subdirectory."""
    root = get_project_root() / "01_DATA_SOURCES"
    # Direct match
    if (root / source_key).exists():
        return root / source_key
    # Try common prefix groups
    prefix_map = {
        "usace_": "federal_waterway/usace",
        "stb_": "federal_rail/stb",
        "ntad_": "federal_rail/ntad",
        "epa_": "environmental/epa",
        "usda_": "market_data",
        "usgs_": "market_data",
        "panjiva": "trade_data/panjiva",
        "noaa_": "geospatial/noaa_enc",
    }
    for prefix, subdir in prefix_map.items():
        if source_key.startswith(prefix):
            candidate = root / subdir
            if candidate.exists():
                return candidate
            # Try with source key appended
            candidate = root / subdir / source_key
            if candidate.exists():
                return candidate
    return root / source_key


def show_data_status(source: str | None = None, verbose: bool = False) -> None:
    """Print freshness status of configured data sources."""
    sources = get_data_sources_config()
    if not sources:
        click.echo("No data sources configured in config.yaml.")
        return

    if source:
        if source not in sources:
            click.echo(f"Unknown source: {source}")
            click.echo(f"Available: {', '.join(sorted(sources))}")
            return
        sources = {source: sources[source]}

    click.echo()
    click.echo(f"{'Source':<25} {'Refresh':<12} {'Status':<12} {'Last Updated':<22} {'Type'}")
    click.echo("-" * 85)

    for key in sorted(sources):
        cfg = sources[key]
        cadence = cfg.get("refresh", "unknown")
        src_type = cfg.get("type", "unknown")
        data_dir = _source_directory(key)
        newest_path, mtime = _newest_file(data_dir)
        label = _freshness_label(mtime, cadence)
        mtime_str = mtime.strftime("%Y-%m-%d %H:%M") if mtime else "—"

        click.echo(f"  {key:<23} {cadence:<12} {label:<20} {mtime_str:<22} {src_type}")

        if verbose and newest_path:
            click.echo(f"    newest: {newest_path.relative_to(get_project_root())}")

    click.echo()
