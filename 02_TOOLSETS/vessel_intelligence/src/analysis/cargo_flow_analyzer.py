#!/usr/bin/env python3
"""
Lower Mississippi River Cargo Flow Analyzer

Integrates three data systems for comprehensive cargo flow analysis:
1. Maritime imports (Panjiva manifest + MRTIS terminal visits)
2. Census trade statistics (official waterborne commerce)
3. Rail transport (STB freight data)

Usage:
    python cargo_flow_analyzer.py --analysis terminal_profiles
    python cargo_flow_analyzer.py --analysis import_flows
    python cargo_flow_analyzer.py --analysis export_flows
    python cargo_flow_analyzer.py --analysis rail_hinterland
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys
import json

# Add Census module path
sys.path.insert(0, str(Path("G:/My Drive/LLM/task_census")))

try:
    from census_trade.config import port_codes, country_codes, cargo_codes
    CENSUS_AVAILABLE = True
except ImportError:
    print("Warning: Census trade modules not available")
    CENSUS_AVAILABLE = False

class CargoFlowAnalyzer:
    """Unified analyzer for Lower Mississippi River cargo flows"""

    def __init__(self, output_dir=None):
        # Define paths
        self.base_path = Path("G:/My Drive/LLM/project_manifest")
        self.census_path = Path("G:/My Drive/LLM/task_census")
        self.rail_path = Path("G:/My Drive/LLM/project_rail")

        # Output directory
        self.output_dir = Path(output_dir) if output_dir else self.base_path / "user_notes" / "cargo_flow_analysis"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Data file paths
        self.manifest_path = self.base_path / "PIPELINE" / "phase_07_enrichment" / "phase_07_output.csv"
        self.terminal_visits_path = self.base_path / "user_notes" / "mrtis_terminal_visits_2024_WITH_RULES.csv"

        # Load reference systems if available
        if CENSUS_AVAILABLE:
            self.ports = port_codes.load_port_reference()
            self.countries = country_codes.load_country_reference()
            self.cargo_ref = cargo_codes.load_cargo_reference()
        else:
            self.ports = {}
            self.countries = {}
            self.cargo_ref = {}

        # Lower Mississippi port definitions
        self.lower_miss_ports = {
            '2704': 'New Orleans',
            '2709': 'Baton Rouge',
            '2771': 'Gramercy',
            '2773': 'Garyville',
            '2777': 'Chalmette',
            '2779': 'Venice',
            '2721': 'Morgan City',
            '2729': 'Lake Charles'
        }

        # Panjiva text to port code mapping
        self.panjiva_port_mapping = {
            'New Orleans': '2704',
            'Baton Rouge': '2709',
            'Gramercy': '2771',
            'Garyville': '2773',
            'Chalmette': '2777',
            'Venice': '2779',
            'Morgan City': '2721',
            'Lake Charles': '2729'
        }

        print(f"Cargo Flow Analyzer initialized")
        print(f"Output directory: {self.output_dir}")

    # ============================================================================
    # DATA LOADING
    # ============================================================================

    def load_manifest_data(self, ports=['New Orleans', 'Baton Rouge']):
        """Load Panjiva manifest data for Lower Mississippi ports"""
        print(f"\nLoading Panjiva manifest data...")
        print(f"Source: {self.manifest_path}")

        if not self.manifest_path.exists():
            print(f"ERROR: Manifest file not found: {self.manifest_path}")
            return None

        df = pd.read_csv(self.manifest_path, low_memory=False, dtype=str)
        print(f"Loaded: {len(df):,} total records")

        # Filter to Lower Mississippi ports
        if isinstance(ports, str):
            ports = [ports]

        df_filtered = df[df['Port_Consolidated'].isin(ports)]
        print(f"Filtered to Lower Mississippi: {len(df_filtered):,} records ({len(df_filtered)/len(df)*100:.1f}%)")
        print(f"Ports included: {', '.join(ports)}")

        return df_filtered

    def load_terminal_visits(self):
        """Load MRTIS terminal visits with Phase 3 predictions"""
        print(f"\nLoading MRTIS terminal visits...")
        print(f"Source: {self.terminal_visits_path}")

        if not self.terminal_visits_path.exists():
            print(f"ERROR: Terminal visits file not found: {self.terminal_visits_path}")
            return None

        df = pd.read_csv(self.terminal_visits_path, low_memory=False)
        print(f"Loaded: {len(df):,} terminal visits")

        # Parse dates
        df['ArrivalTime_dt'] = pd.to_datetime(df['ArrivalTime_dt'])
        df['Month'] = df['ArrivalTime_dt'].dt.to_period('M')

        print(f"Date range: {df['ArrivalTime_dt'].min()} to {df['ArrivalTime_dt'].max()}")
        return df

    # ============================================================================
    # TERMINAL CARGO PROFILING
    # ============================================================================

    def analyze_terminal_cargo_profiles(self):
        """Generate terminal cargo mix profiles using Phase 3 predictions"""
        print("\n" + "=" * 80)
        print("TERMINAL CARGO PROFILING - Lower Mississippi River")
        print("=" * 80)

        df = self.load_terminal_visits()
        if df is None:
            return

        # Filter to visits with cargo assignments (manifest or predicted)
        df_with_cargo = df[df['FinalCargoGroup'].notna()].copy()
        print(f"\nVisits with cargo assignments: {len(df_with_cargo):,} ({len(df_with_cargo)/len(df)*100:.1f}%)")

        # Aggregate by facility and cargo type
        facility_cargo = df_with_cargo.groupby(['Facility', 'FinalCargoGroup', 'FinalCargo']).agg({
            'IMO': 'count',
            'OperationType': lambda x: x.value_counts().to_dict()
        }).reset_index()
        facility_cargo.columns = ['Facility', 'CargoGroup', 'Cargo', 'VisitCount', 'OperationTypes']

        # Sort by visit count
        facility_cargo = facility_cargo.sort_values('VisitCount', ascending=False)

        # Calculate facility totals
        facility_totals = df_with_cargo.groupby('Facility').agg({
            'IMO': 'count',
            'FinalCargoGroup': lambda x: x.value_counts().to_dict(),
            'OperationType': lambda x: x.value_counts().to_dict(),
            'ManifestMatchStatus': lambda x: (x == 'MATCHED').sum(),
            'PredictionConfidence': lambda x: x.notna().sum()
        }).reset_index()
        facility_totals.columns = ['Facility', 'TotalVisits', 'CargoMix', 'Operations', 'ManifestMatches', 'Predictions']
        facility_totals = facility_totals.sort_values('TotalVisits', ascending=False)

        # Save detailed cargo breakdown
        output_file = self.output_dir / f'terminal_cargo_profiles_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        facility_cargo.to_csv(output_file, index=False)
        print(f"\nSaved detailed cargo profiles: {output_file}")

        # Save facility totals
        totals_file = self.output_dir / f'facility_totals_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        facility_totals.to_csv(totals_file, index=False)
        print(f"Saved facility totals: {totals_file}")

        # Print top 20 facilities
        print("\n" + "-" * 100)
        print("TOP 20 FACILITIES BY CARGO VOLUME")
        print("-" * 100)
        print(f"{'Facility':<35s} {'Visits':>8s} {'Manifest':>10s} {'Predicted':>10s} {'Top Cargo':<25s}")
        print("-" * 100)

        for _, row in facility_totals.head(20).iterrows():
            top_cargo = max(row['CargoMix'], key=row['CargoMix'].get) if row['CargoMix'] else 'Unknown'
            print(f"{row['Facility']:<35s} {row['TotalVisits']:>8.0f} {row['ManifestMatches']:>10.0f} "
                  f"{row['Predictions']:>10.0f} {top_cargo:<25s}")

        # Generate cargo group summary
        print("\n" + "-" * 80)
        print("CARGO GROUP DISTRIBUTION")
        print("-" * 80)
        cargo_summary = df_with_cargo.groupby('FinalCargoGroup').agg({
            'IMO': 'count',
            'ManifestMatchStatus': lambda x: (x == 'MATCHED').sum(),
            'PredictionConfidence': lambda x: x.notna().sum()
        }).reset_index()
        cargo_summary.columns = ['CargoGroup', 'TotalVisits', 'ManifestMatches', 'Predictions']
        cargo_summary = cargo_summary.sort_values('TotalVisits', ascending=False)

        for _, row in cargo_summary.iterrows():
            pct = row['TotalVisits'] / len(df_with_cargo) * 100
            print(f"{row['CargoGroup']:<20s}: {row['TotalVisits']:>5.0f} visits ({pct:>5.1f}%) "
                  f"[{row['ManifestMatches']:>4.0f} manifest, {row['Predictions']:>4.0f} predicted]")

        return facility_totals, facility_cargo

    # ============================================================================
    # IMPORT CARGO FLOWS
    # ============================================================================

    def analyze_import_flows(self):
        """Analyze import cargo flows to Lower Mississippi"""
        print("\n" + "=" * 80)
        print("IMPORT CARGO FLOW ANALYSIS - Lower Mississippi River")
        print("=" * 80)

        df = self.load_manifest_data(ports=['New Orleans', 'Baton Rouge', 'Gramercy', 'Garyville'])
        if df is None:
            return

        # Convert Tons to numeric
        df['Tons_num'] = pd.to_numeric(df['Tons'], errors='coerce')
        df = df[df['Tons_num'] > 0]

        # Aggregate by origin country
        print("\n" + "-" * 80)
        print("TOP 20 ORIGIN COUNTRIES BY TONNAGE")
        print("-" * 80)

        country_summary = df.groupby('Country of Origin (F)').agg({
            'Tons_num': 'sum',
            'Bill of Lading Number': 'count',
            'Vessel': lambda x: x.nunique()
        }).reset_index()
        country_summary.columns = ['Country', 'TotalTons', 'BOLCount', 'UniqueVessels']
        country_summary = country_summary.sort_values('TotalTons', ascending=False)

        print(f"{'Country':<30s} {'Tons':>15s} {'BOLs':>8s} {'Vessels':>8s} {'% of Total':>10s}")
        print("-" * 80)
        total_tons = country_summary['TotalTons'].sum()
        for _, row in country_summary.head(20).iterrows():
            pct = row['TotalTons'] / total_tons * 100
            print(f"{row['Country']:<30s} {row['TotalTons']:>15,.0f} {row['BOLCount']:>8.0f} "
                  f"{row['UniqueVessels']:>8.0f} {pct:>9.1f}%")

        # Aggregate by commodity
        print("\n" + "-" * 80)
        print("TOP 20 COMMODITIES BY TONNAGE")
        print("-" * 80)

        commodity_summary = df.groupby(['Group', 'Commodity', 'Cargo']).agg({
            'Tons_num': 'sum',
            'Bill of Lading Number': 'count'
        }).reset_index()
        commodity_summary.columns = ['Group', 'Commodity', 'Cargo', 'TotalTons', 'BOLCount']
        commodity_summary = commodity_summary.sort_values('TotalTons', ascending=False)

        print(f"{'Group':<15s} {'Commodity':<25s} {'Cargo':<20s} {'Tons':>15s} {'BOLs':>8s}")
        print("-" * 80)
        for _, row in commodity_summary.head(20).iterrows():
            print(f"{row['Group']:<15s} {row['Commodity']:<25s} {row['Cargo']:<20s} "
                  f"{row['TotalTons']:>15,.0f} {row['BOLCount']:>8.0f}")

        # Save outputs
        country_file = self.output_dir / f'import_by_country_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        country_summary.to_csv(country_file, index=False)
        print(f"\nSaved country analysis: {country_file}")

        commodity_file = self.output_dir / f'import_by_commodity_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        commodity_summary.to_csv(commodity_file, index=False)
        print(f"Saved commodity analysis: {commodity_file}")

        return country_summary, commodity_summary

    # ============================================================================
    # EXPORT CARGO FLOWS (ESTIMATED)
    # ============================================================================

    def analyze_export_flows(self):
        """Estimate export cargo flows from Lower Mississippi using MRTIS predictions"""
        print("\n" + "=" * 80)
        print("EXPORT CARGO FLOW ANALYSIS (ESTIMATED) - Lower Mississippi River")
        print("=" * 80)

        df = self.load_terminal_visits()
        if df is None:
            return

        # Filter to LOADING operations (exports) with predictions
        df_exports = df[(df['OperationType'] == 'LOADING') & (df['FinalCargoGroup'].notna())].copy()
        print(f"\nExport LOADING operations with cargo: {len(df_exports):,}")

        # Aggregate by cargo type
        print("\n" + "-" * 80)
        print("ESTIMATED EXPORT VOLUMES BY CARGO")
        print("-" * 80)

        export_summary = df_exports.groupby(['FinalCargoGroup', 'FinalCargoCommodity', 'FinalCargo']).agg({
            'IMO': 'count',
            'Facility': lambda x: ', '.join(x.value_counts().head(3).index)
        }).reset_index()
        export_summary.columns = ['Group', 'Commodity', 'Cargo', 'Visits', 'TopFacilities']
        export_summary = export_summary.sort_values('Visits', ascending=False)

        print(f"{'Cargo Group':<20s} {'Commodity':<25s} {'Cargo':<20s} {'Visits':>8s} {'Top Facilities':<30s}")
        print("-" * 80)
        for _, row in export_summary.head(20).iterrows():
            print(f"{row['Group']:<20s} {row['Commodity']:<25s} {row['Cargo']:<20s} "
                  f"{row['Visits']:>8.0f} {row['TopFacilities']:<30s}")

        # Grain elevator exports (special analysis)
        grain_exports = df_exports[df_exports['ZoneType'] == 'Elevator']
        print(f"\n" + "-" * 80)
        print(f"GRAIN ELEVATOR EXPORTS: {len(grain_exports):,} loading operations")
        print("-" * 80)

        grain_by_facility = grain_exports.groupby('Facility').size().sort_values(ascending=False)
        for facility, count in grain_by_facility.head(10).items():
            print(f"  {facility:<35s}: {count:>4.0f} export loadings")

        # Save outputs
        export_file = self.output_dir / f'export_estimates_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        export_summary.to_csv(export_file, index=False)
        print(f"\nSaved export estimates: {export_file}")

        return export_summary

    # ============================================================================
    # COMPREHENSIVE REPORT
    # ============================================================================

    def generate_comprehensive_report(self):
        """Generate comprehensive multimodal cargo flow report"""
        print("\n" + "=" * 80)
        print("GENERATING COMPREHENSIVE CARGO FLOW REPORT")
        print("=" * 80)

        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("LOWER MISSISSIPPI RIVER CARGO FLOW ANALYSIS")
        report_lines.append("Comprehensive Multimodal Analysis Report")
        report_lines.append("=" * 80)
        report_lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Output Directory: {self.output_dir}")

        report_lines.append("\n\n" + "=" * 80)
        report_lines.append("DATA SOURCES")
        report_lines.append("=" * 80)
        report_lines.append(f"1. Panjiva Import Manifest: {self.manifest_path}")
        report_lines.append(f"2. MRTIS Terminal Visits: {self.terminal_visits_path}")
        report_lines.append(f"3. Census Trade Data: {self.census_path}")
        report_lines.append(f"4. Rail Transport Data: {self.rail_path}")

        # Run all analyses
        print("\n1. Terminal cargo profiles...")
        facility_totals, facility_cargo = self.analyze_terminal_cargo_profiles()

        print("\n2. Import cargo flows...")
        country_summary, commodity_summary = self.analyze_import_flows()

        print("\n3. Export cargo flows (estimated)...")
        export_summary = self.analyze_export_flows()

        # Add summaries to report
        report_lines.append("\n\n" + "=" * 80)
        report_lines.append("EXECUTIVE SUMMARY")
        report_lines.append("=" * 80)
        report_lines.append(f"\nTerminal Visits Analyzed: {len(self.load_terminal_visits()):,}")
        report_lines.append(f"Import Records Analyzed: {len(self.load_manifest_data(['New Orleans', 'Baton Rouge'])):,}")
        report_lines.append(f"Facilities Profiled: {len(facility_totals):,}")
        report_lines.append(f"Origin Countries: {len(country_summary):,}")
        report_lines.append(f"Export Cargo Types: {len(export_summary):,}")

        # Save report
        report_file = self.output_dir / f'comprehensive_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(report_file, 'w') as f:
            f.write('\n'.join(report_lines))

        print(f"\n\nComprehensive report saved: {report_file}")
        print(f"All analysis outputs saved to: {self.output_dir}")
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)

        return report_file


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Lower Mississippi River Cargo Flow Analyzer')
    parser.add_argument('--analysis', choices=['terminal_profiles', 'import_flows', 'export_flows', 'comprehensive'],
                        default='comprehensive', help='Type of analysis to run')
    parser.add_argument('--output', help='Output directory (default: user_notes/cargo_flow_analysis)')

    args = parser.parse_args()

    analyzer = CargoFlowAnalyzer(output_dir=args.output)

    if args.analysis == 'terminal_profiles':
        analyzer.analyze_terminal_cargo_profiles()
    elif args.analysis == 'import_flows':
        analyzer.analyze_import_flows()
    elif args.analysis == 'export_flows':
        analyzer.analyze_export_flows()
    elif args.analysis == 'comprehensive':
        analyzer.generate_comprehensive_report()
