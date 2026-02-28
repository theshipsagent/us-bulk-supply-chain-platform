"""
PDF Report Generator
Creates executive PDF report for MSC fleet analysis
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates executive PDF report for MSC fleet analysis"""

    def __init__(self, config: dict, output_dir: str):
        """
        Initialize report generator

        Args:
            config: Configuration dictionary
            output_dir: Directory for report output
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.report_config = config['report']
        self.title = self.report_config['title']
        self.subtitle = self.report_config['subtitle']
        self.author = self.report_config['author']

        # Page size
        self.page_size = letter if self.report_config['format'] == 'letter' else A4

        # Setup styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

        # Chart directory
        self.chart_dir = self.output_dir / 'charts'
        self.chart_dir.mkdir(exist_ok=True)

        # Set seaborn style
        sns.set_style('whitegrid')
        sns.set_palette('Set2')

        logger.info("Initialized report generator")

    def generate_report(self, analysis: Dict, vessel_df: pd.DataFrame,
                       operator_df: pd.DataFrame) -> Path:
        """
        Generate complete PDF report

        Args:
            analysis: Analysis results from MSCAnalyzer
            vessel_df: Vessel data DataFrame
            operator_df: Operator directory DataFrame

        Returns:
            Path to generated PDF
        """
        logger.info("Generating PDF report")

        # Create output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = self.output_dir / f'msc_fleet_analysis_{timestamp}.pdf'

        # Build document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=self.page_size,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )

        # Build content
        story = []

        # Title page
        story.extend(self._create_title_page())
        story.append(PageBreak())

        # Executive summary
        story.extend(self._create_executive_summary(analysis))
        story.append(PageBreak())

        # MSC Fleet Composition
        story.extend(self._create_fleet_composition_section(analysis))
        story.append(PageBreak())

        # Norfolk Analysis
        story.extend(self._create_norfolk_section(analysis))
        story.append(PageBreak())

        # Operator Analysis
        story.extend(self._create_operator_section(analysis, operator_df))
        story.append(PageBreak())

        # Status Analysis
        story.extend(self._create_status_section(analysis))
        story.append(PageBreak())

        # Recommendations
        story.extend(self._create_recommendations_section(analysis))
        story.append(PageBreak())

        # Appendices
        story.extend(self._create_appendices(vessel_df, operator_df))

        # Build PDF
        doc.build(story)

        logger.info(f"Report generated: {output_path}")
        return output_path

    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#003366'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#336699'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))

        # Section heading
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#003366'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))

        # Subsection heading
        self.styles.add(ParagraphStyle(
            name='SubsectionHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#336699'),
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))

    def _create_title_page(self) -> List:
        """Create title page elements"""
        elements = []

        # Add logo if configured
        if self.report_config.get('logo_path'):
            try:
                logo = Image(self.report_config['logo_path'], width=2*inch, height=2*inch)
                elements.append(logo)
                elements.append(Spacer(1, 0.5*inch))
            except Exception as e:
                logger.warning(f"Could not load logo: {e}")

        # Title
        elements.append(Spacer(1, 2*inch))
        elements.append(Paragraph(self.title, self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.3*inch))

        # Subtitle
        elements.append(Paragraph(self.subtitle, self.styles['CustomSubtitle']))
        elements.append(Spacer(1, 1*inch))

        # Metadata
        metadata = [
            f"<b>Prepared by:</b> {self.author}",
            f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}",
            "<b>Classification:</b> Unclassified"
        ]

        for item in metadata:
            elements.append(Paragraph(item, self.styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))

        return elements

    def _create_executive_summary(self, analysis: Dict) -> List:
        """Create executive summary section"""
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.2*inch))

        summary = analysis.get('summary', {})

        # Key findings
        findings = [
            f"Total MSC Vessels: <b>{summary.get('total_msc_vessels', 0)}</b>",
            f"US Flag Vessels: <b>{summary.get('us_flag_vessels', 0)}</b>",
            f"Unique Operators: <b>{summary.get('unique_operators', 0)}</b>",
            f"Vessel Types: <b>{summary.get('unique_types', 0)}</b>"
        ]

        if 'average_age' in summary:
            findings.append(f"Average Fleet Age: <b>{summary['average_age']:.1f} years</b>")

        if 'total_gross_tonnage' in summary:
            tonnage = summary['total_gross_tonnage'] / 1_000_000
            findings.append(f"Total Tonnage: <b>{tonnage:.2f} million GT</b>")

        for finding in findings:
            elements.append(Paragraph(f"• {finding}", self.styles['Normal']))

        elements.append(Spacer(1, 0.3*inch))

        # Overview paragraph
        overview_text = f"""
        This report provides a comprehensive analysis of the United States flag vessel
        inventory with specific focus on Military Sealift Command (MSC) civilian-operated
        ships. The analysis examines {summary.get('total_msc_vessels', 0)} MSC vessels
        across multiple categories including combat logistics, strategic sealift, and
        special mission vessels. Particular attention is given to vessels homeported at
        Norfolk, Virginia and the availability of port space for operational requirements.
        """

        elements.append(Paragraph(overview_text, self.styles['BodyText']))

        return elements

    def _create_fleet_composition_section(self, analysis: Dict) -> List:
        """Create fleet composition section"""
        elements = []

        elements.append(Paragraph("MSC Fleet Composition", self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.2*inch))

        composition = analysis.get('fleet_composition', {})

        # By category table
        if 'by_category' in composition and composition['by_category']:
            elements.append(Paragraph("Vessels by Category", self.styles['SubsectionHeading']))

            table_data = [['Category', 'Count', 'Percentage']]
            total = composition['total_vessels']

            for category, count in composition['by_category'].items():
                pct = (count / total * 100) if total > 0 else 0
                table_data.append([
                    category.replace('_', ' ').title(),
                    str(count),
                    f"{pct:.1f}%"
                ])

            table = self._create_table(table_data)
            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))

            # Create pie chart if configured
            if self.report_config['include_charts']:
                chart_path = self._create_pie_chart(
                    composition['by_category'],
                    'MSC Fleet by Category',
                    'fleet_by_category.png'
                )
                if chart_path:
                    elements.append(Image(str(chart_path), width=5*inch, height=3.5*inch))
                    elements.append(Spacer(1, 0.3*inch))

        # By vessel type
        if 'by_type' in composition and composition['by_type']:
            elements.append(Paragraph("Vessels by Type (Top 10)", self.styles['SubsectionHeading']))

            table_data = [['Vessel Type', 'Count']]
            sorted_types = sorted(composition['by_type'].items(),
                                 key=lambda x: x[1], reverse=True)[:10]

            for vtype, count in sorted_types:
                table_data.append([vtype, str(count)])

            table = self._create_table(table_data)
            elements.append(table)

        return elements

    def _create_norfolk_section(self, analysis: Dict) -> List:
        """Create Norfolk analysis section"""
        elements = []

        elements.append(Paragraph("Norfolk Port Analysis", self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.2*inch))

        norfolk = analysis.get('norfolk_analysis', {})

        # Summary stats
        summary_text = f"""
        Norfolk, Virginia serves as a critical homeport for MSC operations.
        This analysis identified <b>{norfolk.get('total_norfolk_vessels', 0)}</b> MSC vessels
        associated with the Norfolk area, including Norfolk, Portsmouth, Newport News,
        and Hampton Roads facilities.
        """

        elements.append(Paragraph(summary_text, self.styles['BodyText']))
        elements.append(Spacer(1, 0.3*inch))

        # Status breakdown
        if 'by_status' in norfolk and norfolk['by_status']:
            elements.append(Paragraph("Norfolk Vessels by Status", self.styles['SubsectionHeading']))

            table_data = [['Status', 'Count']]
            for status, count in norfolk['by_status'].items():
                table_data.append([status.replace('_', ' ').title(), str(count)])

            table = self._create_table(table_data)
            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))

        # Category breakdown
        if 'by_category' in norfolk and norfolk['by_category']:
            elements.append(Paragraph("Norfolk Vessels by Category", self.styles['SubsectionHeading']))

            table_data = [['Category', 'Count']]
            for category, count in norfolk['by_category'].items():
                table_data.append([category.replace('_', ' ').title(), str(count)])

            table = self._create_table(table_data)
            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))

        # Detailed vessel list
        if 'vessels' in norfolk and norfolk['vessels']:
            elements.append(Paragraph("Norfolk Vessel Roster", self.styles['SubsectionHeading']))

            table_data = [['Vessel Name', 'Type', 'Status', 'Operator']]

            for vessel in norfolk['vessels'][:20]:  # Limit to first 20
                table_data.append([
                    str(vessel.get('vessel_name', 'N/A'))[:30],
                    str(vessel.get('vessel_type', 'N/A'))[:25],
                    str(vessel.get('status_standardized', 'N/A')).replace('_', ' ').title(),
                    str(vessel.get('primary_operator', 'N/A'))[:25]
                ])

            table = self._create_table(table_data, col_widths=[2*inch, 1.5*inch, 1.2*inch, 1.8*inch])
            elements.append(table)

            if len(norfolk['vessels']) > 20:
                elements.append(Spacer(1, 0.1*inch))
                elements.append(Paragraph(
                    f"<i>Showing 20 of {len(norfolk['vessels'])} vessels. "
                    "See appendix for complete listing.</i>",
                    self.styles['Normal']
                ))

        return elements

    def _create_operator_section(self, analysis: Dict, operator_df: pd.DataFrame) -> List:
        """Create operator analysis section"""
        elements = []

        elements.append(Paragraph("MSC Civilian Operator Analysis", self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.2*inch))

        operator_analysis = analysis.get('operator_analysis', {})

        # Summary
        summary_text = f"""
        MSC contracts with civilian maritime operators to crew and operate sealift vessels.
        This analysis identified <b>{operator_analysis.get('total_civilian_operated', 0)}</b>
        civilian-operated vessels, representing
        <b>{operator_analysis.get('civilian_percentage', 0):.1f}%</b> of the MSC fleet.
        """

        elements.append(Paragraph(summary_text, self.styles['BodyText']))
        elements.append(Spacer(1, 0.3*inch))

        # Operators table
        if 'by_operator' in operator_analysis and operator_analysis['by_operator']:
            elements.append(Paragraph("Vessels by Operator", self.styles['SubsectionHeading']))

            table_data = [['Operator', 'Vessel Count']]
            sorted_operators = sorted(operator_analysis['by_operator'].items(),
                                     key=lambda x: x[1], reverse=True)

            for operator, count in sorted_operators[:15]:
                table_data.append([str(operator), str(count)])

            table = self._create_table(table_data)
            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))

            # Create bar chart if configured
            if self.report_config['include_charts']:
                chart_data = dict(sorted_operators[:10])
                chart_path = self._create_bar_chart(
                    chart_data,
                    'Top 10 MSC Operators by Vessel Count',
                    'Operator',
                    'Vessel Count',
                    'operators_bar.png'
                )
                if chart_path:
                    elements.append(Image(str(chart_path), width=6*inch, height=4*inch))

        return elements

    def _create_status_section(self, analysis: Dict) -> List:
        """Create status analysis section"""
        elements = []

        elements.append(Paragraph("Vessel Status and Readiness", self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.2*inch))

        status_analysis = analysis.get('status_analysis', {})

        # Readiness summary
        readiness_text = f"""
        Vessel readiness is critical for rapid deployment capabilities. MSC maintains vessels
        in various states of readiness from fully operational to reduced operating status.
        """

        elements.append(Paragraph(readiness_text, self.styles['BodyText']))
        elements.append(Spacer(1, 0.3*inch))

        # Status table
        if 'by_status' in status_analysis and status_analysis['by_status']:
            elements.append(Paragraph("Fleet Status Distribution", self.styles['SubsectionHeading']))

            table_data = [['Status', 'Count', 'Description']]

            status_descriptions = {
                'operational': 'Currently deployed or in active service',
                'ready': 'Available for immediate activation',
                'ready_reserve': 'Available within 4-20 days',
                'ros': 'Reduced Operating Status - limited crew',
                'activation': 'Currently being mobilized',
                'maintenance': 'In maintenance or repair',
                'unknown': 'Status not specified'
            }

            for status, count in status_analysis['by_status'].items():
                desc = status_descriptions.get(status, '')
                table_data.append([
                    status.replace('_', ' ').title(),
                    str(count),
                    desc
                ])

            table = self._create_table(table_data, col_widths=[1.5*inch, 0.8*inch, 4.2*inch])
            elements.append(table)

        return elements

    def _create_recommendations_section(self, analysis: Dict) -> List:
        """Create recommendations section"""
        elements = []

        elements.append(Paragraph("Recommendations", self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.2*inch))

        norfolk = analysis.get('norfolk_analysis', {})
        status = analysis.get('status_analysis', {})

        recommendations = [
            {
                'title': 'Port Space Optimization',
                'text': f"""Based on the analysis of {norfolk.get('total_norfolk_vessels', 0)}
                vessels at Norfolk, recommend conducting a detailed berth utilization study to
                identify opportunities for consolidation and improved space allocation."""
            },
            {
                'title': 'Ready Reserve Activation Planning',
                'text': f"""With {status.get('reserve', 0)} vessels in ready reserve status,
                recommend developing expedited activation procedures to reduce mobilization
                timeline from current 4-20 day standard."""
            },
            {
                'title': 'Civilian Operator Partnership',
                'text': """Continue strengthening partnerships with civilian maritime operators
                to ensure sufficient crewing and operational expertise for sustained operations."""
            },
            {
                'title': 'Fleet Modernization',
                'text': """Review aging vessels identified in this analysis for potential
                replacement or life extension programs to maintain operational capability."""
            }
        ]

        for i, rec in enumerate(recommendations, 1):
            elements.append(Paragraph(
                f"<b>{i}. {rec['title']}</b>",
                self.styles['SubsectionHeading']
            ))
            elements.append(Paragraph(rec['text'], self.styles['BodyText']))
            elements.append(Spacer(1, 0.2*inch))

        return elements

    def _create_appendices(self, vessel_df: pd.DataFrame, operator_df: pd.DataFrame) -> List:
        """Create appendices section"""
        elements = []

        elements.append(Paragraph("Appendices", self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.2*inch))

        # Appendix A: Data Sources
        elements.append(Paragraph("Appendix A: Data Sources and Methodology", self.styles['SubsectionHeading']))

        sources = [
            "• USACE Waterborne Commerce Statistics Center - Vessel Characteristics Database",
            "• Maritime Administration (MARAD) - Fleet Statistics and Data",
            "• Military Sealift Command - Official Fleet Information",
            "• US Navy - Fleet Status Reports",
            "• Department of Transportation - Maritime Data"
        ]

        for source in sources:
            elements.append(Paragraph(source, self.styles['Normal']))

        elements.append(Spacer(1, 0.2*inch))

        methodology_text = """
        <b>Methodology:</b> Data was collected from publicly available government sources,
        processed to standardize vessel characteristics and operator information, and analyzed
        to identify MSC vessels and their operational disposition. Geographic filtering was
        applied to identify Norfolk-area vessels based on homeport and current location data.
        """
        elements.append(Paragraph(methodology_text, self.styles['BodyText']))

        return elements

    def _create_table(self, data: List[List[str]], col_widths: Optional[List] = None) -> Table:
        """
        Create formatted table

        Args:
            data: Table data (list of rows)
            col_widths: Optional column widths

        Returns:
            Table object
        """
        table = Table(data, colWidths=col_widths)

        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),

            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')]),

            # Grid
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))

        return table

    def _create_pie_chart(self, data: Dict, title: str, filename: str) -> Optional[Path]:
        """Create pie chart"""
        try:
            fig, ax = plt.subplots(figsize=(8, 6))

            labels = [k.replace('_', ' ').title() for k in data.keys()]
            values = list(data.values())

            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.set_title(title, fontsize=14, fontweight='bold')

            output_path = self.chart_dir / filename
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()

            return output_path

        except Exception as e:
            logger.error(f"Failed to create pie chart: {e}")
            return None

    def _create_bar_chart(self, data: Dict, title: str, xlabel: str,
                         ylabel: str, filename: str) -> Optional[Path]:
        """Create bar chart"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            labels = [str(k)[:30] for k in data.keys()]
            values = list(data.values())

            ax.barh(labels, values)
            ax.set_xlabel(ylabel, fontsize=11)
            ax.set_ylabel(xlabel, fontsize=11)
            ax.set_title(title, fontsize=14, fontweight='bold')

            # Invert y-axis for descending order
            ax.invert_yaxis()

            output_path = self.chart_dir / filename
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()

            return output_path

        except Exception as e:
            logger.error(f"Failed to create bar chart: {e}")
            return None
