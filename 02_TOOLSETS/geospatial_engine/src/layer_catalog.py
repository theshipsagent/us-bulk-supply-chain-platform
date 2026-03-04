"""Layer catalog — registry of all Knowledge Bank GeoJSON layers.

Provides a single discovery point for the 20 GeoJSON layers stored
in ``07_KNOWLEDGE_BANK/master_facility_register/``.  Each entry
records the layer key, a human description, its relative path from
the project root, and a category tag for filtering.

Usage::

    from geospatial_engine.src.layer_catalog import LAYER_CATALOG, get_layer_path

    for name, meta in LAYER_CATALOG.items():
        print(f"{name}: {meta['description']}")

    path = get_layer_path("facilities_cement")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Resolve project root (four levels up from this file)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

_KB_BASE = "07_KNOWLEDGE_BANK/master_facility_register"
_NSC = f"{_KB_BASE}/data/national_supply_chain"
_GEO = f"{_KB_BASE}/geojson"


LAYER_CATALOG: dict[str, dict[str, str]] = {
    # ---- Facility layers ----
    "facilities_cement": {
        "path": f"{_NSC}/facilities_cement.geojson",
        "description": "Cement plants — kilns, grinding, terminals",
        "category": "facilities",
    },
    "facilities_steel_mill": {
        "path": f"{_NSC}/facilities_steel_mill.geojson",
        "description": "Steel mills — integrated, EAF, rolling",
        "category": "facilities",
    },
    "facilities_refinery": {
        "path": f"{_NSC}/facilities_refinery.geojson",
        "description": "Petroleum refineries",
        "category": "facilities",
    },
    "facilities_chemical": {
        "path": f"{_NSC}/facilities_chemical.geojson",
        "description": "Chemical manufacturing facilities",
        "category": "facilities",
    },
    "facilities_fertilizer": {
        "path": f"{_NSC}/facilities_fertilizer.geojson",
        "description": "Fertilizer production and distribution",
        "category": "facilities",
    },
    "facilities_grain_elevator": {
        "path": f"{_NSC}/facilities_grain_elevator.geojson",
        "description": "Grain elevators — river, rail, country (inland waterway)",
        "category": "facilities",
    },
    "facilities_grain_export_elevator": {
        "path": f"{_NSC}/facilities_grain_export_elevator.geojson",
        "description": "Grain export elevators — BWS portmaps (29 terminals: Miss River IENC-calibrated, PNW/TX/Norfolk/Mobile)",
        "category": "facilities",
    },
    "facilities_bws_all_terminals": {
        "path": f"{_NSC}/facilities_bws_all_terminals.geojson",
        "description": "All Blue Water Shipping port map terminals — grain + coal + chemicals + petroleum (57 features)",
        "category": "facilities",
    },
    "lower_miss_bws_terminals": {
        "path": f"{_NSC}/lower_miss_bws_terminals.geojson",
        "description": "Lower Mississippi River BWS terminals — 21 features (MM 0–229), filtered from facilities_bws_all_terminals",
        "category": "facilities",
    },
    "lower_miss_river_centerline": {
        "path": f"{_NSC}/lower_miss_river_centerline.geojson",
        "description": "Lower Mississippi River USACE waterway centerline — 25 segments filtered from waterways_major",
        "category": "infrastructure",
    },
    "facilities_aggregate": {
        "path": f"{_NSC}/facilities_aggregate.geojson",
        "description": "Aggregate quarries and distribution",
        "category": "facilities",
    },
    "facilities_coal_terminal": {
        "path": f"{_NSC}/facilities_coal_terminal.geojson",
        "description": "Coal loading/unloading terminals",
        "category": "facilities",
    },
    "facilities_general_cargo": {
        "path": f"{_NSC}/facilities_general_cargo.geojson",
        "description": "General cargo handling facilities",
        "category": "facilities",
    },
    "facilities_pipeline_terminal": {
        "path": f"{_NSC}/facilities_pipeline_terminal.geojson",
        "description": "Pipeline terminals — tank farms, pump stations",
        "category": "facilities",
    },
    "seaports_us": {
        "path": f"{_GEO}/seaports_us.geojson",
        "description": "US seaports — Census Schedule D (99 coastal + Great Lakes ports)",
        "category": "facilities",
    },
    "national_industrial_facilities": {
        "path": f"{_NSC}/national_industrial_facilities.geojson",
        "description": "Combined national industrial facility layer",
        "category": "facilities",
    },
    # ---- Infrastructure layers ----
    "rail_network": {
        "path": f"{_NSC}/rail_network_simplified.geojson",
        "description": "Simplified US rail network (Class I + short line)",
        "category": "infrastructure",
    },
    "waterways_major": {
        "path": f"{_NSC}/waterways_major.geojson",
        "description": "Major navigable waterways (USACE)",
        "category": "infrastructure",
    },
    "pipelines_national": {
        "path": f"{_NSC}/pipelines_national.geojson",
        "description": "National pipeline network (all products)",
        "category": "infrastructure",
    },
    "pipelines_crude": {
        "path": f"{_NSC}/pipelines_crude.geojson",
        "description": "Crude oil pipelines",
        "category": "infrastructure",
    },
    "pipelines_hgl": {
        "path": f"{_NSC}/pipelines_hgl.geojson",
        "description": "HGL / NGL / LPG pipelines",
        "category": "infrastructure",
    },
    # ---- Commodity cluster layers ----
    "clusters_grain": {
        "path": f"{_GEO}/commodity_clusters_grain.geojson",
        "description": "Grain commodity market clusters",
        "category": "clusters",
    },
    "clusters_petroleum": {
        "path": f"{_GEO}/commodity_clusters_petroleum.geojson",
        "description": "Petroleum commodity market clusters",
        "category": "clusters",
    },
    "clusters_chemical": {
        "path": f"{_GEO}/commodity_clusters_chemical.geojson",
        "description": "Chemical commodity market clusters",
        "category": "clusters",
    },
    "clusters_multimodal": {
        "path": f"{_GEO}/commodity_clusters_multimodal.geojson",
        "description": "Multimodal transport hub clusters",
        "category": "clusters",
    },
}


def get_layer_path(layer_name: str) -> Path:
    """Return absolute path to a registered GeoJSON layer.

    Raises ``KeyError`` if the layer name is not in the catalog.
    """
    entry = LAYER_CATALOG[layer_name]
    return _PROJECT_ROOT / entry["path"]


def list_layers(category: str | None = None) -> list[dict[str, Any]]:
    """List layers, optionally filtered by category.

    Returns list of dicts with keys: name, description, category, path, exists.
    """
    results = []
    for name, meta in sorted(LAYER_CATALOG.items()):
        if category and meta["category"] != category:
            continue
        abs_path = _PROJECT_ROOT / meta["path"]
        results.append({
            "name": name,
            "description": meta["description"],
            "category": meta["category"],
            "path": meta["path"],
            "exists": abs_path.exists(),
        })
    return results


def get_layer_info(layer_name: str) -> dict[str, Any]:
    """Return metadata for a single layer including file size.

    Raises ``KeyError`` if the layer name is not in the catalog.
    """
    meta = LAYER_CATALOG[layer_name]
    abs_path = _PROJECT_ROOT / meta["path"]
    info: dict[str, Any] = {
        "name": layer_name,
        "description": meta["description"],
        "category": meta["category"],
        "path": meta["path"],
        "absolute_path": str(abs_path),
        "exists": abs_path.exists(),
    }
    if abs_path.exists():
        size = abs_path.stat().st_size
        if size > 1_048_576:
            info["size"] = f"{size / 1_048_576:.1f} MB"
        else:
            info["size"] = f"{size / 1024:.1f} KB"
    return info
