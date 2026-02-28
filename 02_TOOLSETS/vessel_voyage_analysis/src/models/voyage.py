"""Voyage data model with metrics calculation."""

from dataclasses import dataclass, field
from typing import Optional, List
from .event import Event
from .quality_issue import QualityIssue


@dataclass
class Voyage:
    """Represents a complete voyage from Cross In to Cross Out."""

    voyage_id: str              # {IMO}_{CrossIn_Timestamp}
    imo: str
    vessel_name: str
    cross_in_event: Event
    cross_out_event: Optional[Event]
    events: List[Event] = field(default_factory=list)  # All events chronologically

    # Metrics (calculated)
    total_port_time_hours: Optional[float] = None
    total_transit_time_hours: float = 0.0
    total_anchor_time_hours: float = 0.0
    total_terminal_time_hours: float = 0.0
    num_anchor_stops: int = 0
    num_terminal_stops: int = 0

    # Quality
    is_complete: bool = False
    quality_issues: List[QualityIssue] = field(default_factory=list)

    def add_quality_issue(self, issue: QualityIssue) -> None:
        """Add a quality issue to this voyage."""
        self.quality_issues.append(issue)

    def has_errors(self) -> bool:
        """Check if this voyage has any ERROR-level quality issues."""
        return any(issue.severity == 'ERROR' for issue in self.quality_issues)

    def has_warnings(self) -> bool:
        """Check if this voyage has any WARNING-level quality issues."""
        return any(issue.severity == 'WARNING' for issue in self.quality_issues)

    def get_quality_flags(self) -> str:
        """Get comma-separated list of quality issue types."""
        if not self.quality_issues:
            return ""
        return ",".join(sorted(set(issue.issue_type for issue in self.quality_issues)))

    def get_duration_days(self) -> Optional[float]:
        """Get total voyage duration in days."""
        if self.total_port_time_hours is not None:
            return self.total_port_time_hours / 24.0
        return None

    def __str__(self) -> str:
        """Human-readable voyage representation."""
        status = "Complete" if self.is_complete else "Incomplete"
        return f"Voyage {self.voyage_id}: {self.vessel_name} ({status})"
