"""Markdown renderer — writes assembled Markdown as-is."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MarkdownRenderer:
    """Passthrough renderer that writes concatenated Markdown to a file."""

    def render(self, markdown_content: str, output_path: Path, title: str = "") -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown_content, encoding="utf-8")
        logger.info("Wrote Markdown: %s (%d chars)", output_path, len(markdown_content))
        return output_path
