"""Quality issue tracking for data validation."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .event import Event


@dataclass
class QualityIssue:
    """Represents a data quality issue found during processing."""

    issue_type: str        # MISSING_CROSS_OUT, ORPHANED_ARRIVAL, etc.
    severity: str          # ERROR, WARNING, INFO
    voyage_id: str
    imo: str
    vessel_name: str
    timestamp: Optional[datetime]
    description: str
    affected_events: List['Event'] = field(default_factory=list)

    def __str__(self) -> str:
        """Human-readable issue representation."""
        time_str = self.timestamp.strftime('%Y-%m-%d %H:%M') if self.timestamp else 'N/A'
        return f"[{self.severity}] {self.issue_type}: {self.description} (Voyage: {self.voyage_id}, Time: {time_str})"


# Issue type constants
class IssueType:
    """Standard quality issue types."""
    MISSING_CROSS_OUT = "MISSING_CROSS_OUT"
    MISSING_CROSS_IN = "MISSING_CROSS_IN"
    ORPHANED_ARRIVAL = "ORPHANED_ARRIVAL"
    ORPHANED_DEPARTURE = "ORPHANED_DEPARTURE"
    OUT_OF_SEQUENCE = "OUT_OF_SEQUENCE"
    DUPLICATE_EVENT = "DUPLICATE_EVENT"
    TIME_GAP = "TIME_GAP"
    NEGATIVE_DURATION = "NEGATIVE_DURATION"
    ZONE_TRANSITION_ANOMALY = "ZONE_TRANSITION_ANOMALY"
    UNPAIRED_STOP = "UNPAIRED_STOP"


# Severity constants
class Severity:
    """Standard severity levels."""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
