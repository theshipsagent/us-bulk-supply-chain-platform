"""Report manifest loader — reads YAML manifests or auto-discovers chapters."""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from report_platform.config import get_project_root

logger = logging.getLogger(__name__)

# Map report names to their directories under 04_REPORTS
REPORT_DIR_MAP: dict[str, str] = {
    "us_bulk_supply_chain": "us_bulk_supply_chain",
    "cement_commodity": "cement_commodity_report",
}


@dataclass
class ChapterConfig:
    """Configuration for a single report chapter."""
    number: str          # e.g. "00", "01"
    title: str           # Human-readable title
    file_path: Path      # Absolute path to .md file
    extractors: list[str] = field(default_factory=list)  # Which extractors to run
    template: bool = False  # Whether this chapter uses Jinja2 templates


@dataclass
class ReportManifest:
    """Full report configuration."""
    name: str
    title: str
    chapters: list[ChapterConfig]
    report_dir: Path
    output_dir: Path
    metadata: dict[str, Any] = field(default_factory=dict)


def load_manifest(report_name: str) -> ReportManifest:
    """Load report manifest from YAML, falling back to auto-discovery."""
    root = get_project_root()
    reports_dir = root / "04_REPORTS"

    # Try YAML manifest first
    manifest_path = reports_dir / "templates" / f"{report_name}.yaml"
    if manifest_path.exists():
        return _load_yaml_manifest(manifest_path, report_name, root)

    # Auto-discover chapters
    return _auto_discover(report_name, root)


def _load_yaml_manifest(
    manifest_path: Path, report_name: str, root: Path
) -> ReportManifest:
    """Load manifest from YAML file."""
    with open(manifest_path) as f:
        data = yaml.safe_load(f)

    dir_name = data.get("directory", REPORT_DIR_MAP.get(report_name, report_name))
    report_dir = root / "04_REPORTS" / dir_name
    output_dir = report_dir / "output"

    chapters = []
    for ch in data.get("chapters", []):
        file_path = report_dir / ch["file"]
        if not file_path.exists():
            logger.warning("Chapter file not found: %s", file_path)
            continue
        chapters.append(ChapterConfig(
            number=ch.get("number", re.match(r"(\d+)", ch["file"]).group(1)
                          if re.match(r"\d+", ch["file"]) else "00"),
            title=ch.get("title", ch["file"]),
            file_path=file_path,
            extractors=ch.get("extractors", []),
            template=ch.get("template", False),
        ))

    return ReportManifest(
        name=report_name,
        title=data.get("title", report_name.replace("_", " ").title()),
        chapters=chapters,
        report_dir=report_dir,
        output_dir=output_dir,
        metadata=data.get("metadata", {}),
    )


def _auto_discover(report_name: str, root: Path) -> ReportManifest:
    """Auto-discover chapters by scanning for NN_*.md files."""
    dir_name = REPORT_DIR_MAP.get(report_name, report_name)
    report_dir = root / "04_REPORTS" / dir_name
    output_dir = report_dir / "output"

    if not report_dir.exists():
        raise FileNotFoundError(
            f"Report directory not found: {report_dir}\n"
            f"Available: {[d.name for d in (root / '04_REPORTS').iterdir() if d.is_dir()]}"
        )

    # Find NN_*.md files, sorted by number prefix
    md_files = sorted(report_dir.glob("[0-9][0-9]_*.md"))
    if not md_files:
        raise FileNotFoundError(f"No chapter files (NN_*.md) found in {report_dir}")

    chapters = []
    for md_file in md_files:
        match = re.match(r"(\d+)_(.*?)\.md", md_file.name)
        if match:
            number = match.group(1)
            title = match.group(2).replace("_", " ").title()
        else:
            number = "00"
            title = md_file.stem

        chapters.append(ChapterConfig(
            number=number,
            title=title,
            file_path=md_file,
        ))

    logger.info(
        "Auto-discovered %d chapters for '%s' in %s",
        len(chapters), report_name, report_dir,
    )

    return ReportManifest(
        name=report_name,
        title=report_name.replace("_", " ").title(),
        chapters=chapters,
        report_dir=report_dir,
        output_dir=output_dir,
    )
