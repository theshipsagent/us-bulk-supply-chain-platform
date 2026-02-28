"""Chapter assembler — reads Markdown files, optionally renders Jinja2 templates."""

import logging
import re
from pathlib import Path
from typing import Any

from report_platform.reports.report_config import ChapterConfig, ReportManifest

logger = logging.getLogger(__name__)

# Lazy-loaded Jinja2
_jinja_env = None


def _get_jinja_env():
    """Lazy-init Jinja2 environment with custom filters."""
    global _jinja_env
    if _jinja_env is not None:
        return _jinja_env

    from jinja2 import Environment, BaseLoader, StrictUndefined

    env = Environment(
        loader=BaseLoader(),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        # Use safe delimiters that won't conflict with Markdown
        variable_start_string="{{",
        variable_end_string="}}",
        block_start_string="{%",
        block_end_string="%}",
        comment_start_string="{#",
        comment_end_string="#}",
    )

    # Custom filters
    env.filters["format_dollars"] = _filter_format_dollars
    env.filters["format_tons"] = _filter_format_tons
    env.filters["format_percent"] = _filter_format_percent
    env.filters["md_table"] = _filter_md_table
    env.filters["commas"] = _filter_commas

    _jinja_env = env
    return env


def _filter_format_dollars(value, decimals=2) -> str:
    """Format a number as US dollars."""
    try:
        val = float(value)
        if abs(val) >= 1_000_000_000:
            return f"${val / 1_000_000_000:,.{decimals}f}B"
        if abs(val) >= 1_000_000:
            return f"${val / 1_000_000:,.{decimals}f}M"
        return f"${val:,.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


def _filter_format_tons(value, decimals=0) -> str:
    """Format a number as tons."""
    try:
        return f"{float(value):,.{decimals}f} tons"
    except (TypeError, ValueError):
        return str(value)


def _filter_format_percent(value, decimals=1) -> str:
    """Format a number as a percentage."""
    try:
        return f"{float(value):.{decimals}f}%"
    except (TypeError, ValueError):
        return str(value)


def _filter_commas(value) -> str:
    """Format a number with commas."""
    try:
        val = float(value)
        if val == int(val):
            return f"{int(val):,}"
        return f"{val:,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _filter_md_table(rows: list[dict], columns: list[str] | None = None) -> str:
    """Convert a list of dicts to a Markdown pipe table."""
    if not rows:
        return ""
    if columns is None:
        columns = list(rows[0].keys())

    # Header
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"

    # Rows
    lines = [header, separator]
    for row in rows:
        cells = [str(row.get(col, "")) for col in columns]
        lines.append("| " + " | ".join(cells) + " |")

    return "\n".join(lines)


def _has_jinja_markers(content: str) -> bool:
    """Check if content contains Jinja2 template markers."""
    return "{{" in content or "{%" in content


def assemble_chapter(
    chapter: ChapterConfig,
    data_context: dict[str, Any] | None = None,
) -> str:
    """Read a chapter file and optionally render Jinja2 templates.

    Args:
        chapter: Chapter configuration with file path.
        data_context: Dict of variables available for Jinja2 rendering.
            If None or empty, chapter is returned as-is.

    Returns:
        Rendered Markdown string.
    """
    content = chapter.file_path.read_text(encoding="utf-8")

    # Only render Jinja2 if: (a) chapter is marked as template, or (b) content
    # has Jinja2 markers AND we have data to inject
    should_render = (
        (chapter.template or _has_jinja_markers(content))
        and data_context
    )

    if should_render:
        try:
            env = _get_jinja_env()
            template = env.from_string(content)
            content = template.render(**data_context)
            logger.info("Rendered Jinja2 template for chapter %s", chapter.number)
        except Exception as e:
            logger.warning(
                "Jinja2 rendering failed for chapter %s (%s): %s — using static content",
                chapter.number, chapter.file_path.name, e,
            )
            # Fall back to static content
            content = chapter.file_path.read_text(encoding="utf-8")

    return content


def assemble_report(
    manifest: ReportManifest,
    data_context: dict[str, Any] | None = None,
    section_filter: str | None = None,
) -> str:
    """Assemble all chapters into a single Markdown document.

    Args:
        manifest: Report manifest with chapter list.
        data_context: Variables for Jinja2 rendering.
        section_filter: If set, only include chapters matching this number prefix.

    Returns:
        Combined Markdown string with page breaks between chapters.
    """
    parts: list[str] = []

    for chapter in manifest.chapters:
        # Filter by section if requested
        if section_filter and not chapter.number.startswith(section_filter):
            continue

        logger.info("Assembling chapter %s: %s", chapter.number, chapter.title)
        content = assemble_chapter(chapter, data_context)
        parts.append(content)

    if not parts:
        if section_filter:
            raise ValueError(
                f"No chapters match section filter '{section_filter}'. "
                f"Available: {[ch.number for ch in manifest.chapters]}"
            )
        raise ValueError(f"No chapters found for report '{manifest.name}'")

    # Join chapters with horizontal rule (used as page break marker by renderers)
    return "\n\n---\n\n".join(parts)
