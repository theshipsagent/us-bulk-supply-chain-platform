"""
Crude Oil Flow Analysis: Vessel Imports + Domestic Pipelines to Gulf Coast Refineries
Lower Mississippi River and Gulf Coast Refining Hub

Documents established pattern:
1. Vessel imports of crude oil (international sources)
2. Domestic crude oil via pipelines (Texas, Louisiana production)
3. Processing at Gulf Coast refineries (146 facilities from EIA)
4. Refined products distributed domestically and exported

Analysis Focus:
- Vessel imports: Volume, origin countries, crude grades, terminals
- Major import terminal: LOOP (Louisiana Offshore Oil Port)
- Refineries: Capacity, locations, operators (from EIA data)
- Pipeline infrastructure: Domestic crude supply routes
- Refined product exports (reverse flow)

Unique Characteristics:
- BOTH import AND domestic supply (unlike fertilizer/grain)
- Refineries are processors, not end consumers
- Refined products flow OUT (gasoline, diesel, jet fuel exports)
- LOOP offshore terminal handles VLCCs (Very Large Crude Carriers)

NOT theorizing - documenting what we know from data + established industry patterns.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

class CrudeOilFlowAnalyzer:
    """Analyze crude oil vessel-to-refinery + pipeline-to-refinery flow patterns"""

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.manifest_path = self.base_dir / "PIPELINE" / "phase_07_enrichment" / "phase_07_output.csv"
        self.eia_refineries_path = self.base_dir / "user_notes" / "usda_validation" / "eia_refineries_official_20260222_231951.csv"
        self.output_dir = self.base_dir / "user_notes" / "crude_oil_flow"
        self.output_dir.mkdir(exist_ok=True)

        # Lower Mississippi and Gulf Coast ports
        self.gulf_coast_ports = [
            'New Orleans', 'Baton Rouge', 'Gramercy', 'Garyville',
            'Chalmette', 'Venice', 'Morgan City', 'Lake Charles',
            'Port Arthur', 'Beaumont', 'Houston', 'Texas City',
            'Corpus Christi', 'Galveston', 'Freeport'
        ]

        # Major crude oil import terminals
        self.import_terminals = {
            'LOOP (Louisiana Offshore Oil Port)': {
                'location': '18 miles offshore, Louisiana',
                'type': 'Deepwater offshore terminal',
                'capacity': 'Up to 1.2M bpd',
                'vessel_size': 'VLCC (Very Large Crude Carriers)',
                'connected_refineries': 'Pipeline to multiple Gulf Coast refineries',
                'depth': '110 feet (handles supertankers)',
                'storage': '50+ million barrels',
                'operators': 'LOOP LLC'
            },
            'Marathon St. James Terminal': {
                'location': 'St. James, LA (Mississippi River)',
                'type': 'River terminal',
                'capacity': 'Moderate',
                'vessel_size': 'Aframax, Suezmax',
                'connected_refineries': 'Marathon Garyville refinery',
                'notes': 'River mile 160'
            },
            'Shell Norco Terminal': {
                'location': 'Norco, LA (Mississippi River)',
                'type': 'River terminal',
                'capacity': 'Moderate',
                'vessel_size': 'Aframax',
                'connected_refineries': 'Shell Norco refinery',
                'notes': 'River mile 138'
            },
            'Exxon Baton Rouge Terminal': {
                'location': 'Baton Rouge, LA (Mississippi River)',
                'type': 'River terminal',
                'capacity': 'Large',
                'vessel_size': 'Aframax',
                'connected_refineries': 'ExxonMobil Baton Rouge refinery',
                'notes': 'River mile 233'
            },
            'Phillips 66 Alliance Terminal': {
                'location': 'Belle Chasse, LA (Mississippi River)',
                'type': 'River terminal',
                'capacity': 'Large',
                'vessel_size': 'Aframax, Suezmax',
                'connected_refineries': 'Phillips 66 Alliance refinery',
                'notes': 'River mile 73'
            }
        }

        # Major Gulf Coast refineries (subset from EIA data)
        # These are the largest refineries in Louisiana/Texas
        self.major_refineries = {
            'ExxonMobil Baton Rouge': {
                'location': 'Baton Rouge, LA',
                'capacity_bpd': 502_500,
                'crude_sources': 'LOOP pipeline, vessel imports, domestic',
                'products': 'Gasoline, diesel, jet fuel, chemicals'
            },
            'Marathon Garyville': {
                'location': 'Garyville, LA',
                'capacity_bpd': 578_000,
                'crude_sources': 'Vessel imports, LOOP, domestic',
                'products': 'Gasoline, diesel, jet fuel'
            },
            'Motiva Port Arthur': {
                'location': 'Port Arthur, TX',
                'capacity_bpd': 607_000,
                'crude_sources': 'LOOP pipeline, vessel imports, domestic',
                'products': 'Gasoline, diesel, jet fuel, chemicals'
            },
            'Valero Port Arthur': {
                'location': 'Port Arthur, TX',
                'capacity_bpd': 335_000,
                'crude_sources': 'Vessel imports, domestic pipelines',
                'products': 'Gasoline, diesel, jet fuel'
            },
            'Total Port Arthur': {
                'location': 'Port Arthur, TX',
                'capacity_bpd': 225_500,
                'crude_sources': 'LOOP, vessel imports',
                'products': 'Gasoline, diesel'
            },
            'Phillips 66 Alliance': {
                'location': 'Belle Chasse, LA',
                'capacity_bpd': 247_000,
                'crude_sources': 'Vessel imports, domestic',
                'products': 'Gasoline, diesel, jet fuel'
            },
            'Valero St. Charles': {
                'location': 'Norco, LA',
                'capacity_bpd': 340_000,
                'crude_sources': 'LOOP, vessel imports, domestic',
                'products': 'Gasoline, diesel, jet fuel'
            }
        }

        # Domestic crude oil pipeline systems to Gulf Coast
        self.pipeline_systems = {
            'Permian Basin to Gulf Coast': {
                'pipelines': 'EPIC, Gray Oak, Cactus II',
                'origin': 'West Texas (Permian Basin)',
                'destination': 'Houston/Corpus Christi area',
                'capacity': '~3M bpd combined',
                'crude_type': 'Light sweet crude'
            },
            'Eagle Ford to Gulf Coast': {
                'pipelines': 'Eagle Ford Pipeline',
                'origin': 'South Texas (Eagle Ford Shale)',
                'destination': 'Corpus Christi area',
                'capacity': '~400K bpd',
                'crude_type': 'Light sweet crude'
            },
            'Louisiana Production': {
                'pipelines': 'Local gathering systems',
                'origin': 'Louisiana onshore/offshore',
                'destination': 'Louisiana refineries',
                'capacity': 'Variable',
                'crude_type': 'Medium/heavy sour crude'
            },
            'Canadian Heavy to Gulf Coast': {
                'pipelines': 'Keystone XL (proposed), existing lines',
                'origin': 'Alberta oil sands',
                'destination': 'Gulf Coast refineries',
                'capacity': 'Variable',
                'crude_type': 'Heavy sour crude'
            }
        }

    def load_manifest_data(self):
        """Load classified manifest data"""
        print("Loading manifest data...")
        df = pd.read_csv(self.manifest_path, low_memory=False)

        # Convert dates
        df['Arrival Date'] = pd.to_datetime(df['Arrival Date'], errors='coerce')

        # Filter to Gulf Coast ports (expanded beyond just Lower Miss)
        df_gulf = df[
            df['Port_Consolidated'].isin(self.gulf_coast_ports)
        ].copy()

        print(f"Total Gulf Coast records: {len(df_gulf):,}")
        return df_gulf

    def filter_crude_oil_cargo(self, df):
        """Filter for crude oil cargo"""
        print("\nFiltering for crude oil cargo...")

        # Filter using cargo classification
        df_crude = df[
            (df['Commodity'] == 'Crude Oil') |
            (df['Cargo'] == 'Crude Oil') |
            (df['Cargo_Detail'].str.contains('Crude', case=False, na=False)) |
            (df['Goods Shipped'].str.contains('CRUDE OIL', case=False, na=False))
        ].copy()

        # Add temporal columns
        df_crude['Year'] = df_crude['Arrival Date'].dt.year
        df_crude['Month'] = df_crude['Arrival Date'].dt.month
        df_crude['Quarter'] = df_crude['Arrival Date'].dt.quarter

        print(f"Crude oil records found: {len(df_crude):,}")
        if len(df_crude) > 0:
            print(f"Total crude oil tonnage: {df_crude['Tons'].sum():,.0f} tons")
        else:
            print("NOTE: Low crude oil imports may indicate:")
            print("      - Domestic production dominates Gulf Coast supply")
            print("      - LOOP offshore terminal not captured in Panjiva port data")
            print("      - Crude oil classified differently in manifest data")

        return df_crude

    def analyze_vessel_imports(self, df_crude):
        """Analyze crude oil vessel imports"""
        print("\n" + "="*80)
        print("ANALYZING CRUDE OIL VESSEL IMPORTS")
        print("="*80)

        if len(df_crude) == 0:
            print("\nNo crude oil imports found in Panjiva data.")
            print("This is expected - most Gulf Coast crude arrives via:")
            print("  1. LOOP offshore terminal (not captured in port data)")
            print("  2. Domestic pipelines (not vessel imports)")
            print("  3. Refined products dominate vessel traffic (not crude)")
            return None

        # Total imports
        total_tons = df_crude['Tons'].sum()
        years = df_crude['Year'].nunique()
        avg_per_year = total_tons / years if years > 0 else 0

        # Convert tons to barrels (crude oil ~ 7.3 barrels per ton)
        total_barrels = total_tons * 7.3
        avg_bpd = total_barrels / (365 * years) if years > 0 else 0

        print(f"\nTotal crude oil imports: {total_tons:,.0f} tons")
        print(f"Total crude oil imports: {total_barrels:,.0f} barrels")
        print(f"Years analyzed: {years}")
        print(f"Average: {avg_per_year:,.0f} tons/year ({avg_bpd:,.0f} bpd)")

        # Origin countries
        print("\nTOP ORIGIN COUNTRIES:")
        origin_summary = df_crude.groupby('Country of Origin (F)')['Tons'].sum().sort_values(ascending=False)
        for country, tons in origin_summary.head(10).items():
            pct = (tons / total_tons) * 100
            barrels = tons * 7.3
            print(f"  {country}: {tons:,.0f} tons ({barrels:,.0f} barrels, {pct:.1f}%)")

        # Top consignees
        print("\nTOP CONSIGNEES:")
        consignee_summary = df_crude.groupby('Consignee')['Tons'].sum().sort_values(ascending=False)
        for consignee, tons in consignee_summary.head(10).items():
            barrels = tons * 7.3
            print(f"  {consignee}: {tons:,.0f} tons ({barrels:,.0f} barrels)")

        # Port distribution
        print("\nPORT DISTRIBUTION:")
        port_summary = df_crude.groupby('Port_Consolidated')['Tons'].sum().sort_values(ascending=False)
        for port, tons in port_summary.items():
            pct = (tons / total_tons) * 100
            barrels = tons * 7.3
            print(f"  {port}: {tons:,.0f} tons ({barrels:,.0f} barrels, {pct:.1f}%)")

        # Seasonality
        print("\nSEASONALITY (Monthly Average):")
        monthly_avg = df_crude.groupby('Month')['Tons'].sum() / years
        for month in range(1, 13):
            month_name = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][month-1]
            tons = monthly_avg.get(month, 0)
            barrels = tons * 7.3
            print(f"  {month_name}: {tons:,.0f} tons ({barrels:,.0f} barrels)")

        return {
            'total_tons': total_tons,
            'total_barrels': total_barrels,
            'avg_per_year': avg_per_year,
            'avg_bpd': avg_bpd,
            'origin_summary': origin_summary,
            'consignee_summary': consignee_summary,
            'port_summary': port_summary,
            'monthly_avg': monthly_avg
        }

    def load_eia_refineries(self):
        """Load EIA refinery data"""
        print("\n" + "="*80)
        print("EIA REFINERY DATA (Gulf Coast Focus)")
        print("="*80)

        try:
            df_refineries = pd.read_csv(self.eia_refineries_path)
            print(f"\nTotal refineries (national): {len(df_refineries)}")

            # Filter to Gulf Coast states (approximate by lat/lng)
            # Gulf Coast: Louisiana, Texas, Alabama, Mississippi (roughly 25-32N, 88-97W)
            df_gulf_refineries = df_refineries[
                (df_refineries['lat'] >= 25) & (df_refineries['lat'] <= 32) &
                (df_refineries['lng'] >= -97) & (df_refineries['lng'] <= -88)
            ].copy()

            print(f"Gulf Coast refineries (LA/TX/MS/AL): {len(df_gulf_refineries)}")

            # Save Gulf Coast subset
            output_file = self.output_dir / f"gulf_coast_refineries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df_gulf_refineries.to_csv(output_file, index=False)
            print(f"Gulf Coast refineries saved to: {output_file}")

            return df_gulf_refineries

        except Exception as e:
            print(f"Error loading EIA refinery data: {e}")
            return None

    def document_crude_supply_pattern(self):
        """Document the crude oil supply pattern to Gulf Coast refineries"""
        print("\n" + "="*80)
        print("CRUDE OIL SUPPLY PATTERN TO GULF COAST REFINERIES")
        print("="*80)

        print("\nTWO-SOURCE SUPPLY SYSTEM:")
        print("\n1. VESSEL IMPORTS (International Crude):")
        print("   Primary terminal: LOOP (Louisiana Offshore Oil Port)")
        print("     - 18 miles offshore, 110 feet depth")
        print("     - Handles VLCCs (Very Large Crude Carriers)")
        print("     - Up to 1.2M bpd capacity")
        print("     - Pipeline connections to multiple refineries")
        print("     - Storage: 50+ million barrels")
        print("\n   River terminals (Lower Mississippi):")
        print("     - Marathon St. James (RM 160)")
        print("     - Shell Norco (RM 138)")
        print("     - ExxonMobil Baton Rouge (RM 233)")
        print("     - Phillips 66 Alliance (RM 73)")
        print("\n   Origin countries (typical):")
        print("     - Saudi Arabia, Iraq, Kuwait (Middle East heavy/medium)")
        print("     - Venezuela (heavy sour)")
        print("     - Mexico (Maya heavy)")
        print("     - Nigeria, Angola (West African light/medium)")

        print("\n2. DOMESTIC PIPELINES (U.S. Production):")
        print("   Permian Basin (West Texas):")
        print("     - Pipelines: EPIC, Gray Oak, Cactus II")
        print("     - Capacity: ~3M bpd combined")
        print("     - Crude type: Light sweet")
        print("\n   Eagle Ford (South Texas):")
        print("     - Eagle Ford Pipeline")
        print("     - Capacity: ~400K bpd")
        print("     - Crude type: Light sweet")
        print("\n   Louisiana Production:")
        print("     - Local gathering systems")
        print("     - Onshore/offshore Gulf of Mexico")
        print("     - Crude type: Medium/heavy sour")

        print("\n3. REFINERY PROCESSING:")
        print("   Gulf Coast refining capacity: ~9M bpd (55% of U.S. total)")
        print("   Major refineries:")
        for refinery, info in self.major_refineries.items():
            print(f"\n   {refinery}:")
            print(f"     Location: {info['location']}")
            print(f"     Capacity: {info['capacity_bpd']:,} bpd")
            print(f"     Crude sources: {info['crude_sources']}")
            print(f"     Products: {info['products']}")

        print("\n4. REFINED PRODUCT DISTRIBUTION:")
        print("   Domestic (pipelines, barges, trucks):")
        print("     - Colonial Pipeline (Southeast, East Coast)")
        print("     - Plantation Pipeline (Southeast)")
        print("     - Explorer Pipeline (Midwest)")
        print("\n   Export (vessels):")
        print("     - Latin America (gasoline, diesel)")
        print("     - Europe (diesel, jet fuel)")
        print("     - Asia (gasoline, petrochemicals)")

    def generate_report(self, import_stats, df_refineries):
        """Generate comprehensive crude oil flow report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.output_dir / f"crude_oil_flow_report_{timestamp}.txt"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("CRUDE OIL FLOW ANALYSIS\n")
            f.write("Vessel Imports + Domestic Pipelines to Gulf Coast Refineries\n")
            f.write("="*80 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Vessel imports summary
            if import_stats:
                f.write("VESSEL IMPORT SUMMARY:\n\n")
                f.write(f"Total crude oil imports: {import_stats['total_tons']:,.0f} tons\n")
                f.write(f"Total crude oil imports: {import_stats['total_barrels']:,.0f} barrels\n")
                f.write(f"Average per year: {import_stats['avg_per_year']:,.0f} tons/year\n")
                f.write(f"Average per day: {import_stats['avg_bpd']:,.0f} bpd\n\n")

                # Top origins
                f.write("TOP ORIGIN COUNTRIES:\n\n")
                for country, tons in import_stats['origin_summary'].head(10).items():
                    pct = (tons / import_stats['total_tons']) * 100
                    barrels = tons * 7.3
                    f.write(f"  {country}: {tons:,.0f} tons ({barrels:,.0f} barrels, {pct:.1f}%)\n")
                f.write("\n")
            else:
                f.write("VESSEL IMPORT DATA:\n\n")
                f.write("No crude oil imports found in Panjiva manifest data.\n")
                f.write("Most Gulf Coast crude arrives via:\n")
                f.write("  - LOOP offshore terminal (not captured in port data)\n")
                f.write("  - Domestic pipelines (not vessel imports)\n\n")

            # Import terminals
            f.write("="*80 + "\n")
            f.write("CRUDE OIL IMPORT TERMINALS:\n")
            f.write("="*80 + "\n\n")
            for terminal, info in self.import_terminals.items():
                f.write(f"{terminal}:\n")
                f.write(f"  Location: {info['location']}\n")
                f.write(f"  Type: {info['type']}\n")
                f.write(f"  Capacity: {info['capacity']}\n")
                f.write(f"  Vessel size: {info['vessel_size']}\n")
                if 'connected_refineries' in info:
                    f.write(f"  Connected to: {info['connected_refineries']}\n")
                if 'storage' in info:
                    f.write(f"  Storage: {info['storage']}\n")
                f.write("\n")

            # Refineries
            f.write("="*80 + "\n")
            f.write("MAJOR GULF COAST REFINERIES:\n")
            f.write("="*80 + "\n\n")
            total_capacity = sum(r['capacity_bpd'] for r in self.major_refineries.values())
            f.write(f"Total capacity (major refineries listed): {total_capacity:,} bpd\n")
            f.write(f"Gulf Coast total capacity: ~9,000,000 bpd (est.)\n\n")

            for refinery, info in self.major_refineries.items():
                f.write(f"{refinery}:\n")
                f.write(f"  Location: {info['location']}\n")
                f.write(f"  Capacity: {info['capacity_bpd']:,} bpd\n")
                f.write(f"  Crude sources: {info['crude_sources']}\n")
                f.write(f"  Products: {info['products']}\n\n")

            # Pipeline systems
            f.write("="*80 + "\n")
            f.write("DOMESTIC CRUDE OIL PIPELINE SYSTEMS:\n")
            f.write("="*80 + "\n\n")
            for system, info in self.pipeline_systems.items():
                f.write(f"{system}:\n")
                if 'pipelines' in info:
                    f.write(f"  Pipelines: {info['pipelines']}\n")
                f.write(f"  Origin: {info['origin']}\n")
                f.write(f"  Destination: {info['destination']}\n")
                f.write(f"  Capacity: {info['capacity']}\n")
                f.write(f"  Crude type: {info['crude_type']}\n\n")

            # Flow pattern
            f.write("="*80 + "\n")
            f.write("ESTABLISHED FLOW PATTERN:\n")
            f.write("="*80 + "\n\n")
            f.write("TWO-SOURCE SUPPLY SYSTEM:\n\n")
            f.write("1. VESSEL IMPORTS (International):\n")
            f.write("   - LOOP offshore terminal (primary for VLCCs)\n")
            f.write("   - River terminals on Lower Mississippi\n")
            f.write("   - Origins: Middle East, Venezuela, Mexico, West Africa\n\n")
            f.write("2. DOMESTIC PIPELINES:\n")
            f.write("   - Permian Basin (West Texas) - 3M bpd light sweet\n")
            f.write("   - Eagle Ford (South Texas) - 400K bpd light sweet\n")
            f.write("   - Louisiana production - local medium/heavy sour\n\n")
            f.write("3. REFINERY PROCESSING:\n")
            f.write("   - Gulf Coast: ~9M bpd capacity (55% of U.S. total)\n")
            f.write("   - Blend heavy/sour imports with light/sweet domestic\n")
            f.write("   - Produce gasoline, diesel, jet fuel, petrochemicals\n\n")
            f.write("4. PRODUCT DISTRIBUTION:\n")
            f.write("   - Domestic: Colonial, Plantation, Explorer pipelines\n")
            f.write("   - Export: Vessels to Latin America, Europe, Asia\n\n")

            # Data sources
            f.write("="*80 + "\n")
            f.write("DATA SOURCES:\n")
            f.write("="*80 + "\n\n")
            f.write("- Vessel imports: Panjiva manifest data (if available)\n")
            f.write("- Refineries: EIA official refinery data (146 facilities national)\n")
            f.write("- LOOP terminal: Industry sources (documented)\n")
            f.write("- Pipeline systems: EIA pipeline data (documented)\n")
            f.write("- Refinery capacities: EIA Refinery Capacity Report\n\n")

            if df_refineries is not None:
                f.write(f"Gulf Coast refineries identified: {len(df_refineries)}\n")
                f.write("(LA/TX/MS/AL region, 25-32N, 88-97W)\n\n")

            f.write("="*80 + "\n")

        print(f"\nReport saved to: {report_file}")
        return report_file

    def run_analysis(self):
        """Run complete crude oil flow analysis"""
        print("\n" + "="*80)
        print("CRUDE OIL FLOW ANALYSIS")
        print("Vessel Imports + Domestic Pipelines to Gulf Coast Refineries")
        print("="*80)

        # Load data
        df = self.load_manifest_data()
        df_crude = self.filter_crude_oil_cargo(df)

        # Analyze imports (if any)
        import_stats = None
        if len(df_crude) > 0:
            import_stats = self.analyze_vessel_imports(df_crude)

            # Save detailed outputs
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            if import_stats:
                # Origin countries
                origin_file = self.output_dir / f"crude_origin_countries_{timestamp}.csv"
                import_stats['origin_summary'].to_csv(origin_file)

                # Consignees
                consignee_file = self.output_dir / f"crude_consignees_{timestamp}.csv"
                import_stats['consignee_summary'].to_csv(consignee_file)

                # Ports
                port_file = self.output_dir / f"crude_ports_{timestamp}.csv"
                import_stats['port_summary'].to_csv(port_file)

        # Load EIA refinery data
        df_refineries = self.load_eia_refineries()

        # Document supply pattern
        self.document_crude_supply_pattern()

        # Generate report
        report_file = self.generate_report(import_stats, df_refineries)

        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print(f"\nAll outputs saved to: {self.output_dir}")

        print("\nKEY INSIGHTS:")
        print("  - Gulf Coast = 55% of U.S. refining capacity (~9M bpd)")
        print("  - Two-source supply: Vessel imports + Domestic pipelines")
        print("  - LOOP offshore terminal handles VLCCs (largest tankers)")
        print("  - Domestic shale (Permian, Eagle Ford) now dominates supply")
        print("  - Refineries export products (gasoline, diesel, jet fuel)")
        print("\nNOTE: If vessel import data is low, this reflects:")
        print("  - Domestic production boom (shale revolution)")
        print("  - LOOP offshore terminal not captured in port data")
        print("  - Refined products dominate vessel traffic, not crude")

if __name__ == "__main__":
    analyzer = CrudeOilFlowAnalyzer()
    analyzer.run_analysis()
