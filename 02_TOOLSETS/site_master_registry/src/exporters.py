"""Export master registry data to CSV, JSON, and GeoJSON formats."""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any, Optional

from .query import SiteRegistryQuery

logger = logging.getLogger(__name__)


def export_csv(
    query: SiteRegistryQuery,
    output_path: str,
    sectors: Optional[list[str]] = None,
) -> Path:
    """Export master_sites to CSV."""
    sites = query.all_sites_for_map(sectors=sectors)
    if not sites:
        logger.warning("No sites to export")
        return Path(output_path)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(sites[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sites)

    logger.info(f"Exported {len(sites)} sites to {path}")
    return path


def export_geojson(
    query: SiteRegistryQuery,
    output_path: str,
    sectors: Optional[list[str]] = None,
) -> Path:
    """Export master_sites as GeoJSON FeatureCollection."""
    sites = query.all_sites_for_map(sectors=sectors)

    features = []
    for site in sites:
        if site.get("latitude") is None or site.get("longitude") is None:
            continue
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [site["longitude"], site["latitude"]],
            },
            "properties": {
                k: v for k, v in site.items()
                if k not in ("latitude", "longitude")
            },
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(geojson, f, indent=2, default=str)

    logger.info(f"Exported {len(features)} features to {path}")
    return path


def export_json_summary(
    query: SiteRegistryQuery,
    output_path: str,
) -> Path:
    """Export registry summary as JSON."""
    summary = query.summary()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(summary, f, indent=2, default=str)

    logger.info(f"Exported summary to {path}")
    return path
