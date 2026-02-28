"""Base extractor protocol and ABC."""

from abc import ABC, abstractmethod
from typing import Any


class BaseExtractor(ABC):
    """Abstract base class for data extractors.

    Each extractor pulls data from a specific toolset and returns a dict
    of key-value pairs that become available as Jinja2 template variables.
    """

    @abstractmethod
    def extract(self) -> dict[str, Any]:
        """Extract data and return as a dict for Jinja2 context.

        Keys should be namespaced (e.g., 'barge_corridor_rates') to avoid
        collisions when multiple extractors run together.

        Returns:
            Dict of template variables. Values can be strings, numbers,
            lists, or dicts — anything Jinja2 can render.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier for this extractor (e.g., 'barge', 'rail')."""
        ...
