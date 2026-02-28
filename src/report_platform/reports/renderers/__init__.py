"""Renderer registry — maps format names to renderer functions."""

from pathlib import Path
from typing import Protocol


class Renderer(Protocol):
    """Protocol for report renderers."""

    def render(self, markdown_content: str, output_path: Path, title: str = "") -> Path:
        """Render Markdown content to the target format.

        Args:
            markdown_content: Assembled Markdown text.
            output_path: File path for the output.
            title: Report title for headers/metadata.

        Returns:
            Path to the generated file.
        """
        ...


def get_renderer(fmt: str) -> "Renderer":
    """Get a renderer instance by format name."""
    if fmt == "md":
        from report_platform.reports.renderers.markdown_renderer import MarkdownRenderer
        return MarkdownRenderer()
    elif fmt == "docx":
        from report_platform.reports.renderers.docx_renderer import DocxRenderer
        return DocxRenderer()
    elif fmt == "html":
        from report_platform.reports.renderers.html_renderer import HtmlRenderer
        return HtmlRenderer()
    else:
        raise ValueError(f"Unknown format: {fmt!r}. Supported: md, docx, html")
