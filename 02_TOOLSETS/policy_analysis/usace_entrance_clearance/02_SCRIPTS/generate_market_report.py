"""
USACE Market Study - PDF Report Generator
Assembles analysis and visualizations into a comprehensive PDF report
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


def add_title_page(pdf: PdfPages, results: Dict[str, Any]):
    """Add title page to PDF."""
    fig = plt.figure(figsize=(8.5, 11))
    fig.patch.set_facecolor('white')

    # Title
    fig.text(0.5, 0.75, 'US PORT CLEARANCE', ha='center', va='center',
            fontsize=32, fontweight='bold', color='navy')
    fig.text(0.5, 0.68, 'MARKET STUDY 2023', ha='center', va='center',
            fontsize=32, fontweight='bold', color='navy')

    # Subtitle
    fig.text(0.5, 0.58, 'Operator Market Analysis & Regional Revenue Distribution',
            ha='center', va='center', fontsize=14, style='italic', color='darkslategray')

    # Key metrics box
    market = results['market']
    metrics_text = f"""
    Total Market Revenue: ${market['total_revenue']/1e6:.1f}M
    Total Clearances: {market['total_clearances']:,}
    Unique Vessels: {market['unique_vessels']:,}
    Analysis Period: 2023
    """

    fig.text(0.5, 0.40, metrics_text, ha='center', va='center',
            fontsize=12, family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))

    # Footer
    report_date = datetime.now().strftime('%B %d, %Y')
    fig.text(0.5, 0.15, f'Report Generated: {report_date}', ha='center', va='center',
            fontsize=10, color='gray')
    fig.text(0.5, 0.10, 'USACE Port Clearance Analysis', ha='center', va='center',
            fontsize=10, color='gray')

    plt.axis('off')
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def add_section_header(pdf: PdfPages, section_number: int, section_title: str, description: str = None):
    """Add a section header page."""
    fig = plt.figure(figsize=(8.5, 11))
    fig.patch.set_facecolor('white')

    # Section number
    fig.text(0.1, 0.85, f'{section_number}.', ha='left', va='top',
            fontsize=48, fontweight='bold', color='steelblue')

    # Section title
    fig.text(0.2, 0.85, section_title, ha='left', va='top',
            fontsize=24, fontweight='bold', color='navy')

    # Description
    if description:
        fig.text(0.1, 0.70, description, ha='left', va='top',
                fontsize=12, color='darkslategray', wrap=True)

    plt.axis('off')
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def add_text_page(pdf: PdfPages, title: str, content: Dict[str, Any], bullet_points: list = None):
    """Add a text-based page with formatted content."""
    fig = plt.figure(figsize=(8.5, 11))
    fig.patch.set_facecolor('white')

    y_pos = 0.95

    # Title
    fig.text(0.1, y_pos, title, ha='left', va='top',
            fontsize=16, fontweight='bold', color='navy')
    y_pos -= 0.08

    # Content
    if isinstance(content, dict):
        for key, value in content.items():
            text = f"{key}: {value}"
            fig.text(0.1, y_pos, text, ha='left', va='top', fontsize=11)
            y_pos -= 0.04

    # Bullet points
    if bullet_points:
        y_pos -= 0.02
        for point in bullet_points:
            fig.text(0.12, y_pos, f"• {point}", ha='left', va='top', fontsize=10)
            y_pos -= 0.04

    plt.axis('off')
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def add_executive_summary(pdf: PdfPages, results: Dict[str, Any], summary_fig):
    """Add executive summary section."""
    add_section_header(pdf, 1, 'Executive Summary',
                      'Overview of the US port clearance market for 2023')

    # Summary statistics page
    pdf.savefig(summary_fig, bbox_inches='tight')
    plt.close(summary_fig)

    # Key findings page
    market = results['market']
    vessel_types = results['vessel_types']
    regions = results['regions']
    grain = results['grain']

    findings = [
        f"Market generated ${market['total_revenue']/1e6:.1f}M in revenue from {market['total_clearances']:,} clearances",
        f"Top 10 vessels account for {market['top_10_pct']:.1f}% of total market revenue",
        f"Top 50 vessels account for {market['top_50_pct']:.1f}% of total market revenue",
        f"Market concentration (HHI): {market['hhi']:.0f} - indicates {'high' if market['hhi'] > 2500 else 'moderate'} concentration",
        f"{vessel_types['total_types']} distinct vessel types operating across {regions['total_regions']} regions",
        f"Average clearance fee: ${market['avg_fee']:,.0f}",
        f"Grain shipments: {grain['grain_clearances']:,} ({grain['grain_pct']:.1f}% of total)",
        f"Multi-visit vessels: {market['multi_visit_vessels']:,} | Single-visit: {market['single_visit_vessels']:,}"
    ]

    add_text_page(pdf, 'Key Findings', {}, findings)


def add_market_overview(pdf: PdfPages, results: Dict[str, Any]):
    """Add market overview section."""
    add_section_header(pdf, 2, 'Market Overview',
                      'Total market size, clearance volume, and concentration metrics')

    market = results['market']

    # Market metrics page
    metrics = {
        'Total Revenue': f"${market['total_revenue']:,.0f}",
        'Total Clearances': f"{market['total_clearances']:,}",
        'Average Fee per Clearance': f"${market['avg_fee']:,.0f}",
        'Unique Vessels': f"{market['unique_vessels']:,}",
        'HHI (Market Concentration)': f"{market['hhi']:.0f}",
        'Multi-Visit Vessels': f"{market['multi_visit_vessels']:,}",
        'Single-Visit Vessels': f"{market['single_visit_vessels']:,}"
    }

    notes = [
        "HHI above 2,500 indicates high market concentration",
        "HHI between 1,500-2,500 indicates moderate concentration",
        f"Current HHI of {market['hhi']:.0f} suggests {'high' if market['hhi'] > 2500 else 'moderate'} concentration"
    ]

    add_text_page(pdf, 'Market Metrics', metrics, notes)


def add_operator_analysis(pdf: PdfPages, results: Dict[str, Any], figures: Dict[str, Any]):
    """Add operator market share analysis section."""
    add_section_header(pdf, 3, 'Operator Market Share Analysis',
                      'Analysis of top vessels (proxy for operators) by revenue')

    # Add charts
    if 'top_20_vessels' in figures['revenue']:
        pdf.savefig(figures['revenue']['top_20_vessels'], bbox_inches='tight')
        plt.close(figures['revenue']['top_20_vessels'])

    if 'market_concentration' in figures['revenue']:
        pdf.savefig(figures['revenue']['market_concentration'], bbox_inches='tight')
        plt.close(figures['revenue']['market_concentration'])

    if 'lorenz_curve' in figures['revenue']:
        pdf.savefig(figures['revenue']['lorenz_curve'], bbox_inches='tight')
        plt.close(figures['revenue']['lorenz_curve'])

    # Add top 50 table
    market = results['market']
    add_table_page(pdf, 'Top 50 Vessels by Revenue', market['top_50_vessels'],
                  ['Vessel_ID', 'Fee_Adj', 'Clearances'])


def add_vessel_type_analysis(pdf: PdfPages, results: Dict[str, Any], figures: Dict[str, Any]):
    """Add vessel type revenue analysis section."""
    add_section_header(pdf, 4, 'Vessel Type Revenue Analysis',
                      'Revenue distribution across vessel types and cargo classes')

    # Add charts
    if 'type_revenue' in figures['vessel_types']:
        pdf.savefig(figures['vessel_types']['type_revenue'], bbox_inches='tight')
        plt.close(figures['vessel_types']['type_revenue'])

    if 'cargo_revenue' in figures['vessel_types']:
        pdf.savefig(figures['vessel_types']['cargo_revenue'], bbox_inches='tight')
        plt.close(figures['vessel_types']['cargo_revenue'])

    if 'fee_distribution' in figures['vessel_types']:
        pdf.savefig(figures['vessel_types']['fee_distribution'], bbox_inches='tight')
        plt.close(figures['vessel_types']['fee_distribution'])

    if 'type_region_heatmap' in figures['vessel_types']:
        pdf.savefig(figures['vessel_types']['type_region_heatmap'], bbox_inches='tight')
        plt.close(figures['vessel_types']['type_region_heatmap'])

    # Add disparity analysis
    vessel_types = results['vessel_types']
    disparity = vessel_types['disparity']

    disparity_metrics = {
        'Highest Revenue Type': f"{disparity['highest_type']} (${disparity['highest_revenue']/1e6:.1f}M)",
        'Lowest Revenue Type': f"{disparity['lowest_type']} (${disparity['lowest_revenue']/1e6:.1f}M)",
        'Revenue Disparity Ratio': f"{disparity['revenue_ratio']:.1f}x",
        'Highest Avg Fee': f"${disparity['avg_fee_highest']:,.0f}",
        'Lowest Avg Fee': f"${disparity['avg_fee_lowest']:,.0f}"
    }

    add_text_page(pdf, 'Revenue Disparity Analysis', disparity_metrics)


def add_regional_analysis(pdf: PdfPages, results: Dict[str, Any], figures: Dict[str, Any]):
    """Add regional market analysis section."""
    add_section_header(pdf, 5, 'Regional Market Analysis',
                      'Revenue and clearance distribution across US port regions')

    # Add charts
    if 'region_revenue' in figures['regions']:
        pdf.savefig(figures['regions']['region_revenue'], bbox_inches='tight')
        plt.close(figures['regions']['region_revenue'])

    if 'region_clearances' in figures['regions']:
        pdf.savefig(figures['regions']['region_clearances'], bbox_inches='tight')
        plt.close(figures['regions']['region_clearances'])

    if 'region_avg_fee' in figures['regions']:
        pdf.savefig(figures['regions']['region_avg_fee'], bbox_inches='tight')
        plt.close(figures['regions']['region_avg_fee'])

    # Add regional statistics table
    regions = results['regions']
    add_table_page(pdf, 'Regional Statistics', regions['region_revenue_df'],
                  ['Port_Region', 'Total_Revenue', 'Clearances', 'Avg_Fee', 'Revenue_Pct'])


def add_ship_revenue_analysis(pdf: PdfPages, results: Dict[str, Any], figures: Dict[str, Any]):
    """Add average revenue per ship analysis section."""
    add_section_header(pdf, 6, 'Average Revenue Per Ship Analysis',
                      'Analysis of revenue distribution across individual vessels')

    # Add summary metrics
    per_ship = results['per_ship']

    metrics = {
        'Total Unique Vessels': f"{per_ship['total_vessels']:,}",
        'Average Revenue per Ship': f"${per_ship['avg_revenue_per_ship']:,.0f}",
        'Median Revenue per Ship': f"${per_ship['percentiles'][0.5]:,.0f}",
        '10th Percentile': f"${per_ship['percentiles'][0.1]:,.0f}",
        '90th Percentile': f"${per_ship['percentiles'][0.9]:,.0f}"
    }

    add_text_page(pdf, 'Per-Ship Revenue Metrics', metrics)

    # Add charts
    if 'revenue_distribution' in figures['per_ship']:
        pdf.savefig(figures['per_ship']['revenue_distribution'], bbox_inches='tight')
        plt.close(figures['per_ship']['revenue_distribution'])

    if 'revenue_by_type' in figures['per_ship']:
        pdf.savefig(figures['per_ship']['revenue_by_type'], bbox_inches='tight')
        plt.close(figures['per_ship']['revenue_by_type'])

    if 'visits_revenue' in figures['per_ship']:
        pdf.savefig(figures['per_ship']['visits_revenue'], bbox_inches='tight')
        plt.close(figures['per_ship']['visits_revenue'])


def add_grain_analysis(pdf: PdfPages, results: Dict[str, Any], figures: Dict[str, Any]):
    """Add grain shipment analysis section."""
    add_section_header(pdf, 7, 'Grain Shipment Analysis',
                      'Detailed analysis of grain export clearances')

    grain = results['grain']

    if grain['grain_clearances'] == 0:
        add_text_page(pdf, 'No Grain Data', {'Note': 'No grain shipments found in dataset'})
        return

    # Add metrics
    metrics = {
        'Grain Clearances': f"{grain['grain_clearances']:,}",
        'Percentage of Total': f"{grain['grain_pct']:.1f}%",
        'Grain Revenue': f"${grain['grain_revenue']:,.0f}",
        'Total Tonnage': f"{grain['grain_tonnage']:,.0f} MT"
    }

    add_text_page(pdf, 'Grain Shipment Metrics', metrics)

    # Add charts
    if 'grain_destinations' in figures['grain']:
        pdf.savefig(figures['grain']['grain_destinations'], bbox_inches='tight')
        plt.close(figures['grain']['grain_destinations'])

    if 'grain_tonnage_pie' in figures['grain']:
        pdf.savefig(figures['grain']['grain_tonnage_pie'], bbox_inches='tight')
        plt.close(figures['grain']['grain_tonnage_pie'])

    if 'grain_vessel_types' in figures['grain']:
        pdf.savefig(figures['grain']['grain_vessel_types'], bbox_inches='tight')
        plt.close(figures['grain']['grain_vessel_types'])


def add_conclusions(pdf: PdfPages, results: Dict[str, Any]):
    """Add conclusions and market insights section."""
    add_section_header(pdf, 8, 'Conclusions & Market Insights',
                      'Key takeaways and strategic observations')

    market = results['market']
    vessel_types = results['vessel_types']
    regions = results['regions']
    grain = results['grain']

    insights = [
        f"The US port clearance market generated ${market['total_revenue']/1e6:.1f}M in 2023",
        f"Market shows {'high' if market['hhi'] > 2500 else 'moderate'} concentration with top 10 vessels controlling {market['top_10_pct']:.1f}%",
        f"Significant revenue disparity across vessel types: {vessel_types['disparity']['revenue_ratio']:.1f}x ratio",
        f"Regional distribution varies significantly, with top region generating {regions['region_revenue_df'].iloc[0]['Revenue_Pct']:.1f}% of revenue",
        f"Average revenue per vessel is ${results['per_ship']['avg_revenue_per_ship']:,.0f}, with significant variance",
        f"Grain exports represent {grain['grain_pct']:.1f}% of clearances but contribute ${grain['grain_revenue']/1e6:.1f}M in revenue",
        "Multi-visit vessels indicate established trade routes and partnerships",
        "Vessel type diversity (60 types) reflects varied cargo and operational requirements"
    ]

    add_text_page(pdf, 'Market Insights', {}, insights)


def add_table_page(pdf: PdfPages, title: str, df: pd.DataFrame, columns: list = None, max_rows: int = 50):
    """Add a page with a formatted table."""
    if columns:
        df_display = df[columns].copy()
    else:
        df_display = df.copy()

    # Limit rows
    df_display = df_display.head(max_rows)

    # Format numeric columns
    for col in df_display.columns:
        if df_display[col].dtype in ['float64', 'int64']:
            if 'Revenue' in col or 'Fee' in col or 'Tonnage' in col:
                df_display[col] = df_display[col].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else '')
            elif 'Pct' in col:
                df_display[col] = df_display[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else '')
            else:
                df_display[col] = df_display[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else '')

    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.axis('tight')
    ax.axis('off')

    # Title
    fig.text(0.5, 0.98, title, ha='center', va='top', fontsize=14, fontweight='bold')

    # Create table
    table = ax.table(cellText=df_display.values,
                     colLabels=df_display.columns,
                     cellLoc='left',
                     loc='center',
                     bbox=[0.05, 0.05, 0.9, 0.9])

    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.5)

    # Style header
    for i in range(len(df_display.columns)):
        table[(0, i)].set_facecolor('#4472C4')
        table[(0, i)].set_text_props(weight='bold', color='white')

    # Alternate row colors
    for i in range(1, len(df_display) + 1):
        for j in range(len(df_display.columns)):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#E7E6E6')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def create_pdf_report(results: Dict[str, Any], figures: Dict[str, Any], output_path: str) -> str:
    """Create comprehensive PDF report."""
    print("\n" + "="*60)
    print("USACE Market Study - Generating PDF Report")
    print("="*60 + "\n")

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Output file: {output_path}")

    with PdfPages(output_path) as pdf:
        print("Adding title page...")
        add_title_page(pdf, results)

        print("Adding executive summary...")
        add_executive_summary(pdf, results, figures['summary'])

        print("Adding market overview...")
        add_market_overview(pdf, results)

        print("Adding operator analysis...")
        add_operator_analysis(pdf, results, figures)

        print("Adding vessel type analysis...")
        add_vessel_type_analysis(pdf, results, figures)

        print("Adding regional analysis...")
        add_regional_analysis(pdf, results, figures)

        print("Adding ship revenue analysis...")
        add_ship_revenue_analysis(pdf, results, figures)

        print("Adding grain analysis...")
        add_grain_analysis(pdf, results, figures)

        print("Adding conclusions...")
        add_conclusions(pdf, results)

        # Set PDF metadata
        d = pdf.infodict()
        d['Title'] = 'US Port Clearance Market Study 2023'
        d['Author'] = 'USACE Analysis'
        d['Subject'] = 'Port clearance market analysis and regional revenue distribution'
        d['Keywords'] = 'USACE, port clearance, market study, vessel revenue'
        d['CreationDate'] = datetime.now()

    file_size = Path(output_path).stat().st_size / (1024 * 1024)  # MB
    print(f"\nReport generated successfully!")
    print(f"File size: {file_size:.2f} MB")
    print("="*60 + "\n")

    return output_path


if __name__ == '__main__':
    print("PDF Report Generator module loaded successfully")
    print("Run from main orchestrator to generate report")
