"""ReportEngine — orchestrates chapter assembly, data extraction, and rendering."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from report_platform.config import get_project_root
from report_platform.reports.assembler import assemble_report
from report_platform.reports.renderers import get_renderer
from report_platform.reports.report_config import load_manifest

logger = logging.getLogger(__name__)


class ReportEngine:
    """Orchestrates the full report generation pipeline.

    Usage:
        engine = ReportEngine()
        path = engine.generate("us_bulk_supply_chain", fmt="docx")
        path = engine.generate("cement_commodity", fmt="html", with_data=True)
        path = engine.generate("us_bulk_supply_chain", fmt="md", section="09")
    """

    def generate(
        self,
        report_name: str,
        fmt: str = "md",
        section: str | None = None,
        with_data: bool = False,
        output_dir: Path | None = None,
    ) -> Path:
        """Generate a report.

        Args:
            report_name: Report identifier (e.g., 'us_bulk_supply_chain').
            fmt: Output format — 'md', 'docx', or 'html'.
            section: If set, only include chapters matching this number prefix.
            with_data: If True, run data extractors and inject live data.
            output_dir: Override the default output directory.

        Returns:
            Path to the generated output file.
        """
        logger.info(
            "Generating report: %s (format=%s, section=%s, with_data=%s)",
            report_name, fmt, section, with_data,
        )

        # 1. Load manifest (YAML or auto-discover)
        manifest = load_manifest(report_name)
        logger.info(
            "Loaded manifest: %s — %d chapters", manifest.title, len(manifest.chapters)
        )

        # 2. Collect data context from extractors (if requested)
        data_context: dict[str, Any] | None = None
        if with_data:
            data_context = self._run_extractors(manifest)

        # 3. Assemble Markdown (read chapters, render Jinja2)
        markdown = assemble_report(manifest, data_context, section_filter=section)

        # 4. Determine output path
        if output_dir is None:
            output_dir = manifest.output_dir / fmt
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        section_suffix = f"_section_{section}" if section else ""
        filename = f"{report_name}{section_suffix}_{timestamp}"

        ext_map = {"md": ".md", "docx": ".docx", "html": ".html"}
        output_path = output_dir / f"{filename}{ext_map[fmt]}"

        # 5. Render to target format
        renderer = get_renderer(fmt)
        result_path = renderer.render(markdown, output_path, title=manifest.title)

        logger.info("Report generated: %s", result_path)
        return result_path

    def _run_extractors(self, manifest) -> dict[str, Any]:
        """Collect data from all extractors referenced by the manifest's chapters."""
        from report_platform.reports.extractors import run_extractors

        # Gather unique extractor names from all chapters
        extractor_names: set[str] = set()
        for chapter in manifest.chapters:
            extractor_names.update(chapter.extractors)

        if not extractor_names:
            # Default: run all available extractors
            extractor_names = {"barge", "rail", "facility", "policy", "port", "vessel", "commodity"}
            logger.info("No per-chapter extractors specified — running all: %s", extractor_names)

        return run_extractors(sorted(extractor_names))

    def list_reports(self) -> list[dict[str, Any]]:
        """List available reports with chapter counts."""
        root = get_project_root()
        reports_dir = root / "04_REPORTS"
        results = []

        for report_dir in sorted(reports_dir.iterdir()):
            if not report_dir.is_dir() or report_dir.name.startswith("."):
                continue
            chapters = sorted(report_dir.glob("[0-9][0-9]_*.md"))
            if chapters:
                results.append({
                    "directory": report_dir.name,
                    "chapters": len(chapters),
                    "files": [ch.name for ch in chapters],
                })

        return results

    def preview_report(self, report_name: str) -> list[dict[str, str]]:
        """Preview report structure without generating output."""
        manifest = load_manifest(report_name)
        return [
            {
                "number": ch.number,
                "title": ch.title,
                "file": ch.file_path.name,
                "size": f"{ch.file_path.stat().st_size:,} bytes" if ch.file_path.exists() else "MISSING",
                "template": "yes" if ch.template else "no",
                "extractors": ", ".join(ch.extractors) if ch.extractors else "none",
            }
            for ch in manifest.chapters
        ]
