"""Human-readable report generation."""

from pathlib import Path
from typing import List, Dict
import logging
from datetime import datetime
from ..models.voyage import Voyage
from ..models.quality_issue import Severity

logger = logging.getLogger(__name__)


class ReportWriter:
    """Writes human-readable quality reports."""

    def write_quality_report(
        self,
        voyages: List[Voyage],
        quality_stats: Dict,
        output_path: str
    ) -> None:
        """
        Write quality report as formatted text file.

        Args:
            voyages: List of all Voyage objects
            quality_stats: Quality statistics dictionary from QualityAnalyzer
            output_path: Output file path
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("MARITIME VOYAGE ANALYSIS - QUALITY REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\n")

            # Summary Statistics
            f.write("SUMMARY STATISTICS\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total Voyages:              {quality_stats['total_voyages']:>10}\n")
            f.write(f"Complete Voyages:           {quality_stats['complete_voyages']:>10}\n")
            f.write(f"Incomplete Voyages:         {quality_stats['incomplete_voyages']:>10}\n")
            f.write(f"Completeness Rate:          {quality_stats['completeness_percentage']:>9.1f}%\n")
            f.write(f"Total Events Processed:     {quality_stats['total_events']:>10}\n")
            f.write(f"Total Quality Issues:       {quality_stats['total_issues']:>10}\n")
            f.write(f"Vessels with Issues:        {quality_stats['vessels_with_issues']:>10}\n")
            f.write(f"Issue Rate:                 {quality_stats['vessels_with_issues_percentage']:>9.1f}%\n")
            f.write("\n")

            # Issues by Type
            f.write("ISSUES BY TYPE\n")
            f.write("-" * 80 + "\n")
            issues_by_type = quality_stats.get('issues_by_type', {})
            if issues_by_type:
                for issue_type, count in sorted(
                    issues_by_type.items(),
                    key=lambda x: x[1],
                    reverse=True
                ):
                    f.write(f"{issue_type:<35} {count:>10}\n")
            else:
                f.write("No issues found.\n")
            f.write("\n")

            # Issues by Severity
            f.write("ISSUES BY SEVERITY\n")
            f.write("-" * 80 + "\n")
            issues_by_severity = quality_stats.get('issues_by_severity', {})
            for severity in [Severity.ERROR, Severity.WARNING, Severity.INFO]:
                count = issues_by_severity.get(severity, 0)
                f.write(f"{severity:<35} {count:>10}\n")
            f.write("\n")

            # Top Problematic Vessels
            f.write("TOP 10 VESSELS WITH MOST ISSUES\n")
            f.write("-" * 80 + "\n")
            top_vessels = quality_stats.get('top_problematic_vessels', [])
            if top_vessels:
                for i, (vessel, count) in enumerate(top_vessels, 1):
                    f.write(f"{i:>2}. {vessel:<60} {count:>5} issues\n")
            else:
                f.write("No problematic vessels found.\n")
            f.write("\n")

            # Detailed Issue List
            f.write("DETAILED ISSUE LIST\n")
            f.write("=" * 80 + "\n")
            all_issues = quality_stats.get('all_issues', [])

            if all_issues:
                # Sort by severity (ERROR first, then WARNING, then INFO)
                severity_order = {Severity.ERROR: 0, Severity.WARNING: 1, Severity.INFO: 2}
                sorted_issues = sorted(
                    all_issues,
                    key=lambda x: (severity_order.get(x.severity, 3), x.timestamp or datetime.min)
                )

                for issue in sorted_issues:
                    f.write(f"\n[{issue.severity}] {issue.issue_type}\n")
                    f.write(f"Voyage:     {issue.voyage_id}\n")
                    f.write(f"Vessel:     {issue.vessel_name} (IMO: {issue.imo})\n")
                    if issue.timestamp:
                        f.write(f"Time:       {issue.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Details:    {issue.description}\n")
                    if issue.affected_events:
                        f.write(f"Affected:   {len(issue.affected_events)} event(s)\n")
                    f.write("-" * 80 + "\n")
            else:
                f.write("\nNo issues found. Data quality is excellent!\n")

            # Recommendations
            f.write("\n")
            f.write("RECOMMENDATIONS\n")
            f.write("=" * 80 + "\n")

            # Get recommendations from quality analyzer
            from ..processing.quality_analyzer import QualityAnalyzer
            analyzer = QualityAnalyzer()
            recommendations = analyzer.get_recommendations(quality_stats)

            for i, recommendation in enumerate(recommendations, 1):
                f.write(f"{i}. {recommendation}\n")

            f.write("\n")
            f.write("=" * 80 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 80 + "\n")

        logger.info(f"Wrote quality report to {output_path}")
