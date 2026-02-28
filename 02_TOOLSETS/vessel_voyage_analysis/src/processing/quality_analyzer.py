"""Data quality validation and analysis."""

from typing import List, Dict
from collections import defaultdict, Counter
import logging
from ..models.voyage import Voyage
from ..models.quality_issue import QualityIssue, IssueType, Severity

logger = logging.getLogger(__name__)


class QualityAnalyzer:
    """Analyzes data quality across all voyages."""

    def __init__(self):
        self.total_voyages = 0
        self.total_issues = 0
        self.issues_by_type = Counter()
        self.issues_by_severity = Counter()
        self.vessels_with_issues = set()

    def analyze_quality(self, voyages: List[Voyage]) -> Dict:
        """
        Analyze quality across all voyages and generate statistics.

        Args:
            voyages: List of all Voyage objects

        Returns:
            Dictionary with quality statistics
        """
        self.total_voyages = len(voyages)

        # Collect all issues
        all_issues = []
        complete_voyages = 0
        total_events = 0

        for voyage in voyages:
            if voyage.is_complete:
                complete_voyages += 1

            total_events += len(voyage.events)

            for issue in voyage.quality_issues:
                all_issues.append(issue)
                self.total_issues += 1
                self.issues_by_type[issue.issue_type] += 1
                self.issues_by_severity[issue.severity] += 1
                self.vessels_with_issues.add(voyage.imo)

        # Calculate statistics
        completeness_pct = (complete_voyages / self.total_voyages * 100) if self.total_voyages > 0 else 0
        vessels_with_issues_pct = (
            len(self.vessels_with_issues) / len(set(v.imo for v in voyages)) * 100
            if voyages else 0
        )

        # Find vessels with most issues
        vessels_issue_count = defaultdict(int)
        for issue in all_issues:
            vessels_issue_count[f"{issue.imo} ({issue.vessel_name})"] += 1

        top_problematic_vessels = sorted(
            vessels_issue_count.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        stats = {
            'total_voyages': self.total_voyages,
            'complete_voyages': complete_voyages,
            'incomplete_voyages': self.total_voyages - complete_voyages,
            'completeness_percentage': completeness_pct,
            'total_events': total_events,
            'total_issues': self.total_issues,
            'issues_by_type': dict(self.issues_by_type),
            'issues_by_severity': dict(self.issues_by_severity),
            'vessels_with_issues': len(self.vessels_with_issues),
            'vessels_with_issues_percentage': vessels_with_issues_pct,
            'top_problematic_vessels': top_problematic_vessels,
            'all_issues': all_issues
        }

        logger.info(
            f"Quality Analysis: {self.total_voyages} voyages, "
            f"{complete_voyages} complete ({completeness_pct:.1f}%), "
            f"{self.total_issues} issues found"
        )

        return stats

    def get_recommendations(self, stats: Dict) -> List[str]:
        """
        Generate recommendations based on quality analysis.

        Args:
            stats: Quality statistics dictionary

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Completeness recommendations
        completeness = stats['completeness_percentage']
        if completeness < 80:
            recommendations.append(
                f"Low voyage completeness ({completeness:.1f}%). "
                "Investigate missing Cross Out events in recent data."
            )

        # Issue type recommendations
        issues_by_type = stats['issues_by_type']

        if issues_by_type.get(IssueType.MISSING_CROSS_OUT, 0) > 10:
            recommendations.append(
                f"High number of missing Cross Out events ({issues_by_type[IssueType.MISSING_CROSS_OUT]}). "
                "Check if vessels are still in port or if data collection is incomplete."
            )

        if issues_by_type.get(IssueType.ORPHANED_ARRIVAL, 0) > 5:
            recommendations.append(
                f"Multiple orphaned arrivals ({issues_by_type[IssueType.ORPHANED_ARRIVAL]}). "
                "Review data collection process for missed departure events."
            )

        if issues_by_type.get(IssueType.NEGATIVE_DURATION, 0) > 0:
            recommendations.append(
                f"Found {issues_by_type[IssueType.NEGATIVE_DURATION]} negative duration(s). "
                "Critical data quality issue - check timestamp accuracy."
            )

        # Vessel-specific recommendations
        top_vessels = stats.get('top_problematic_vessels', [])
        if top_vessels and top_vessels[0][1] > 10:
            recommendations.append(
                f"Vessel {top_vessels[0][0]} has {top_vessels[0][1]} issues. "
                "Review this vessel's data for systematic problems."
            )

        if not recommendations:
            recommendations.append(
                "Data quality is good. No major issues detected."
            )

        return recommendations

    def get_stats(self) -> dict:
        """Get analyzer statistics."""
        return {
            'total_voyages': self.total_voyages,
            'total_issues': self.total_issues,
            'issues_by_type': dict(self.issues_by_type),
            'issues_by_severity': dict(self.issues_by_severity),
            'vessels_with_issues': len(self.vessels_with_issues)
        }
