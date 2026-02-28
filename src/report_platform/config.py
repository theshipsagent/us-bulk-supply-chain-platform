"""Configuration loader for the reporting platform."""

from pathlib import Path
from typing import Any

import yaml


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


def load_config() -> dict[str, Any]:
    """Load the global config.yaml."""
    config_path = get_project_root() / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    with open(config_path) as f:
        return yaml.safe_load(f)


def get_data_sources_config() -> dict[str, Any]:
    """Return just the data_sources section of config."""
    return load_config().get("data_sources", {})


def get_databases_config() -> dict[str, Any]:
    """Return the databases section of config."""
    return load_config().get("databases", {})


def get_commodity_modules_config() -> dict[str, Any]:
    """Return the commodity_modules section of config."""
    return load_config().get("commodity_modules", {})


def get_reports_config() -> dict[str, Any]:
    """Return the reports section of config."""
    return load_config().get("reports", {})
