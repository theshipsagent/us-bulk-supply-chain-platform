"""
Grain Flow Analysis: Vessel Exports and Barge Transport to Lower Mississippi
Midwest Grain Belt to Gulf Export Terminals

Documents established pattern:
1. Grain production in Midwest (Illinois, Iowa, Indiana, Ohio, Minnesota)
2. Barge transport downriver to Lower Mississippi export terminals
3. Transfer to ocean vessels for export (primarily to Asia, Latin America)

Analysis Focus:
- Grain exports: Volume, destination countries, products (corn, soybeans, wheat)
- Origin regions: Barge loading points upriver
- Export terminals: New Orleans area elevator capacity
- Seasonal patterns: Harvest-driven flows (fall peak)

References:
- National mapping: 178 grain elevators (sources_data_maps)
- USDA grain transport data (to be integrated)
- USDA crop geospatial data: planted acres, yields
- Fertilizer demand calculation: acres × application rate

REVERSE FLOW from fertilizer - grain goes DOWN river, fertilizer goes UP river.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

class GrainFlowAnalyzer:
    """Analyze grain barge-to-vessel export flow patterns"""

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.manifest_path = self.base_dir / "PIPELINE" / "phase_07_enrichment" / "phase_07_output.csv"
        self.mapping_facilities_path = Path("G:/My Drive/LLM/sources_data_maps/national_supply_chain/national_industrial_facilities.csv")
        self.output_dir = self.base_dir / "user_notes" / "grain_flow"
        self.output_dir.mkdir(exist_ok=True)

        # Lower Mississippi ports (export terminals)
        self.lower_miss_ports = [
            'New Orleans', 'Baton Rouge', 'Gramercy', 'Garyville',
            'Chalmette', 'Venice', 'Morgan City', 'Lake Charles'
        ]

        # Major grain production regions (from mapping + USDA)
        self.grain_production_regions = {
            'Illinois/Iowa Corn Belt': {
                'states': 'Illinois, Iowa',
                'primary_crops': 'Corn, soybeans',
                'market_cluster': 'Chicago/Illinois River (190 facilities)',
                'grain_elevators': '68 elevators',
                'distance_to_lower_miss': '773 miles',
                'river_route': 'Illinois Waterway to Mississippi',
                'harvest_season': 'September-November'
            },
            'Memphis/Arkansas Delta': {
                'states': 'Missouri, Arkansas, Tennessee',
                'primary_crops': 'Soybeans, rice, wheat',
                'market_cluster': 'Memphis/Cincinnati (292 facilities)',
                'grain_elevators': '76 elevators',
                'distance_to_lower_miss': '496 miles',
                'river_route': 'Mississippi River',
                'harvest_season': 'September-October'
            },
            'Ohio River Valley': {
                'states': 'Ohio, Indiana, Kentucky',
                'primary_crops': 'Corn, soybeans',
                'market_cluster': 'Ohio River corridor',
                'grain_elevators': 'Multiple elevators',
                'distance_to_lower_miss': '600-1000 miles',
                'river_route': 'Ohio River to Mississippi',
                'harvest_season': 'September-October'
            },
            'Upper Mississippi': {
                'states': 'Minnesota, Wisconsin',
                'primary_crops': 'Corn, soybeans, wheat',
                'market_cluster': 'St. Paul/Minnesota',
                'grain_elevators': 'Multiple elevators',
                'distance_to_lower_miss': '1050 miles',
                'river_route': 'Mississippi River south',
                'harvest_season': 'September-November'
            }
        }

        # Lower Mississippi grain export terminals (documented)
        self.export_terminals = {
            'Cargill Reserve Terminal': {
                'location': 'Reserve, LA',
                'capacity': 'Major grain elevator',
                'products': 'Corn, soybeans, wheat',
                'export_markets': 'Asia, Latin America'
            },
            'ADM Ama Terminal': {
                'location': 'Ama, LA',
                'capacity': 'Major grain elevator',
                'products': 'Corn, soybeans',
                'export_markets': 'Asia, Latin America'
            },
            'Bunge Destrehan': {
                'location': 'Destrehan, LA',
                'capacity': 'Major grain elevator',
                'products': 'Soybeans, corn',
                'export_markets': 'Asia, Latin America'
            },
            'Louis Dreyfus Company': {
                'location': 'New Orleans area',
                'capacity': 'Major grain elevator',
                'products': 'Soybeans, corn, wheat',
                'export_markets': 'Global'
            },
            'CHS Myrtle Grove': {
                'location': 'Myrtle Grove, LA',
                'capacity': 'Grain elevator',
                'products': 'Soybeans, corn',
                'export_markets': 'Asia'
            }
        }

        # USDA data integration notes
        self.usda_data_sources = {
            'Grain Transport': 'USDA Agricultural Marketing Service - Grain Transportation Report',
            'Crop Planted Acres': 'USDA NASS - Crop Production geospatial data',
            'Yield Data': 'USDA NASS - County-level yield estimates',
            'Fertilizer Rates': 'USDA ERS - Fertilizer application rates by crop',
            'Fertilizer Dashboard': 'USDA ERS - Fertilizer use and price dashboard'
        }

    def load_manifest_data(self):
        """Load classified manifest data"""
        print("Loading manifest data...")
        df = pd.read_csv(self.manifest_path, low_memory=False)

        # Convert dates
        df['Arrival Date'] = pd.to_datetime(df['Arrival Date'], errors='coerce')

        # Filter to Lower Mississippi ports
        df_lower_miss = df[
            df['Port_Consolidated'].isin(self.lower_miss_ports)
        ].copy()

        print(f"Total Lower Miss records: {len(df_lower_miss):,}")
        return df_lower_miss

    def filter_grain_cargo(self, df):
        """Filter for grain cargo (exports from Lower Miss)"""
        print("\nFiltering for grain cargo...")

        # Note: Panjiva data is IMPORTS, but grain flow is EXPORTS from Lower Miss
        # We're looking at IMPORT records that might be grain (e.g., specialty grains)
        # For export data, we'd need different source (USDA grain inspection, port data)

        df_grain = df[
            (df['Commodity'] == 'Grain') |
            (df['Cargo'] == 'Corn') |
            (df['Cargo'] == 'Soybeans') |
            (df['Cargo'] == 'Wheat') |
            (df['Cargo'].str.contains('Grain', case=False, na=False))
        ].copy()

        # Add temporal columns
        df_grain['Year'] = df_grain['Arrival Date'].dt.year
        df_grain['Month'] = df_grain['Arrival Date'].dt.month
        df_grain['Quarter'] = df_grain['Arrival Date'].dt.quarter

        print(f"Grain records found: {len(df_grain):,}")
        if len(df_grain) > 0:
            print(f"Total grain tonnage: {df_grain['Tons'].sum():,.0f} tons")
        else:
            print("NOTE: Panjiva data is IMPORTS. Grain flow analysis needs EXPORT data.")
            print("      Recommend using USDA Grain Inspection data or FGIS export records.")

        return df_grain

    def analyze_grain_imports(self, df_grain):
        """Analyze grain imports (if any - noting this is opposite of main flow)"""
        print("\n" + "="*80)
        print("GRAIN IMPORTS TO LOWER MISSISSIPPI (Import Data)")
        print("="*80)

        if len(df_grain) == 0:
            print("\nNo grain imports found in dataset.")
            print("This is EXPECTED - grain flows OUT of Lower Miss (exports), not in.")
            print("\nTo analyze grain EXPORTS, need:")
            print("  - USDA Grain Inspection (FGIS) export data")
            print("  - Port of New Orleans grain export statistics")
            print("  - USDA Agricultural Marketing Service barge data")
            return None

        # If we do have grain imports (unexpected but analyze it)
        total_tons = df_grain['Tons'].sum()
        years = df_grain['Year'].nunique()
        avg_per_year = total_tons / years if years > 0 else 0

        print(f"\nTotal grain imports: {total_tons:,.0f} tons (UNUSUAL - grain typically EXPORTS)")
        print(f"Average per year: {avg_per_year:,.0f} tons/year")

        # Origin countries
        print("\nORIGIN COUNTRIES:")
        origin_summary = df_grain.groupby('Country of Origin (F)')['Tons'].sum().sort_values(ascending=False)
        for country, tons in origin_summary.head(10).items():
            pct = (tons / total_tons) * 100
            print(f"  {country}: {tons:,.0f} tons ({pct:.1f}%)")

        # Product types
        print("\nPRODUCT TYPES:")
        cargo_summary = df_grain.groupby('Cargo')['Tons'].sum().sort_values(ascending=False)
        for cargo, tons in cargo_summary.head(10).items():
            print(f"  {cargo}: {tons:,.0f} tons")

        return {
            'total_tons': total_tons,
            'origin_summary': origin_summary,
            'cargo_summary': cargo_summary
        }

    def load_national_grain_facilities(self):
        """Load grain elevators from national mapping data"""
        print("\n" + "="*80)
        print("NATIONAL GRAIN ELEVATOR FACILITIES (from mapping session)")
        print("="*80)

        if not self.mapping_facilities_path.exists():
            print("Mapping facilities file not found - using documented terminals only")
            return None

        facilities = pd.read_csv(self.mapping_facilities_path)
        grain_facilities = facilities[facilities['facility_type'] == 'GRAIN_ELEVATOR'].copy()

        print(f"\nTotal grain elevators: {len(grain_facilities)}")

        # By state (top 10)
        print("\nBY STATE (Top 10):")
        state_counts = grain_facilities.groupby('state').size().sort_values(ascending=False)
        for state, count in state_counts.head(10).items():
            print(f"  {state}: {count} elevators")

        # By region (approximation)
        print("\nBY REGION:")
        print(f"  Illinois (corn belt hub): {state_counts.get('IL', 0)} elevators")
        print(f"  Iowa (corn/soybean): {state_counts.get('IA', 0)} elevators")
        print(f"  Missouri (Mississippi River): {state_counts.get('MO', 0)} elevators")
        print(f"  Minnesota (northern grain): {state_counts.get('MN', 0)} elevators")
        print(f"  Louisiana (export terminals): {state_counts.get('LA', 0)} elevators")

        # Save facility list
        output_file = self.output_dir / f"national_grain_elevators_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        grain_facilities.to_csv(output_file, index=False)
        print(f"\nGrain elevators saved to: {output_file}")

        return grain_facilities

    def document_export_flow_pattern(self):
        """Document the established grain export flow (opposite of fertilizer)"""
        print("\n" + "="*80)
        print("ESTABLISHED GRAIN EXPORT FLOW PATTERN")
        print("="*80)
        print("\nREVERSE FLOW from Fertilizer (Grain goes DOWN, Fertilizer goes UP):")
        print("\n1. Grain production in Midwest:")
        print("   - Illinois/Iowa corn belt (68 elevators)")
        print("   - Ohio River Valley")
        print("   - Upper Mississippi (Minnesota/Wisconsin)")
        print("\n2. Harvest season (September-November):")
        print("   - Corn harvest: September-October")
        print("   - Soybean harvest: September-November")
        print("   - Wheat harvest: June-July (winter wheat)")
        print("\n3. Barge loading at upriver elevators:")
        print("   - Illinois Waterway (Chicago region)")
        print("   - Upper Mississippi")
        print("   - Ohio River")
        print("\n4. Barge transport DOWNRIVER to Lower Mississippi:")
        print("   - Illinois Waterway to Mississippi (773 miles)")
        print("   - Ohio River to Mississippi (600-1000 miles)")
        print("   - Upper Mississippi south (1050 miles)")
        print("\n5. Transfer to ocean vessels at export terminals:")
        print("   - Cargill Reserve")
        print("   - ADM Ama")
        print("   - Bunge Destrehan")
        print("   - CHS Myrtle Grove")
        print("   - Louis Dreyfus Company")
        print("\n6. Export destinations:")
        print("   - China (soybeans, corn)")
        print("   - Mexico (corn, soybeans)")
        print("   - Japan (corn, wheat)")
        print("   - Latin America (soybeans)")

    def document_usda_data_integration(self):
        """Document USDA data sources for validation"""
        print("\n" + "="*80)
        print("USDA DATA SOURCES FOR VALIDATION")
        print("="*80)

        print("\n1. GRAIN TRANSPORT DATA:")
        print("   Source: USDA Agricultural Marketing Service")
        print("   Data: Weekly barge tonnages by river segment")
        print("   Use: Validate downriver grain flows vs upriver fertilizer flows")

        print("\n2. CROP GEOSPATIAL DATA:")
        print("   Source: USDA NASS Cropland Data Layer")
        print("   Data: Planted acres by county, crop type")
        print("   Use: Map production regions to barge loading points")

        print("\n3. YIELD DATA:")
        print("   Source: USDA NASS County Estimates")
        print("   Data: Bushels per acre by county, crop, year")
        print("   Use: Calculate total production volume by region")

        print("\n4. FERTILIZER APPLICATION RATES:")
        print("   Source: USDA ERS Fertilizer Use Survey")
        print("   Data: Pounds per acre by crop type (N, P, K)")
        print("   Example rates:")
        print("     - Corn: 140 lbs N, 60 lbs P2O5, 60 lbs K2O per acre")
        print("     - Soybeans: 10 lbs N, 40 lbs P2O5, 60 lbs K2O per acre")
        print("     - Wheat: 90 lbs N, 50 lbs P2O5, 40 lbs K2O per acre")

        print("\n5. FERTILIZER DEMAND CALCULATION:")
        print("   Bottom-up validation of 8.86M tons/year fertilizer imports:")
        print("   Example (Illinois corn):")
        print("     - Planted acres: 11 million (2023)")
        print("     - Fertilizer rate: 260 lbs total NPK per acre")
        print("     - Total demand: 11M acres × 260 lbs = 2.86B lbs = 1.43M tons")
        print("   Repeat for all crops/states to estimate total demand")
        print("   Compare to 8.86M tons imports to understand:")
        print("     - Import vs domestic fertilizer production split")
        print("     - Regional application patterns")

        print("\n6. GRAIN INSPECTION (FGIS) DATA:")
        print("   Source: USDA Grain Inspection, Packers & Stockyards")
        print("   Data: Export inspections by port, commodity, destination")
        print("   Use: Actual Lower Mississippi grain export volumes")

    def generate_report(self, grain_import_stats):
        """Generate grain flow analysis report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.output_dir / f"grain_flow_report_{timestamp}.txt"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("GRAIN FLOW ANALYSIS\n")
            f.write("Midwest Production to Lower Mississippi Export Terminals\n")
            f.write("Barge Transport DOWNRIVER (Reverse of Fertilizer Flow)\n")
            f.write("="*80 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Note about data limitations
            f.write("DATA NOTE:\n")
            f.write("="*80 + "\n")
            f.write("Panjiva manifest data contains IMPORTS, but grain is primarily EXPORTED\n")
            f.write("from Lower Mississippi. This analysis documents the export flow pattern\n")
            f.write("and identifies USDA data sources needed for complete validation.\n\n")

            # Grain import summary (if any)
            if grain_import_stats:
                f.write("GRAIN IMPORTS (Unusual - grain typically exports):\n\n")
                f.write(f"Total imports: {grain_import_stats['total_tons']:,.0f} tons\n\n")

                f.write("Origin countries:\n")
                for country, tons in grain_import_stats['origin_summary'].head(5).items():
                    f.write(f"  {country}: {tons:,.0f} tons\n")
                f.write("\n")

            # Production regions
            f.write("="*80 + "\n")
            f.write("GRAIN PRODUCTION REGIONS (Upriver Sources):\n")
            f.write("="*80 + "\n\n")
            for region, info in self.grain_production_regions.items():
                f.write(f"{region}:\n")
                f.write(f"  States: {info['states']}\n")
                f.write(f"  Primary crops: {info['primary_crops']}\n")
                f.write(f"  Market cluster: {info['market_cluster']}\n")
                f.write(f"  Grain elevators: {info['grain_elevators']}\n")
                f.write(f"  Distance to Lower Miss: {info['distance_to_lower_miss']}\n")
                f.write(f"  River route: {info['river_route']}\n")
                f.write(f"  Harvest season: {info['harvest_season']}\n\n")

            # Export terminals
            f.write("="*80 + "\n")
            f.write("LOWER MISSISSIPPI EXPORT TERMINALS:\n")
            f.write("="*80 + "\n\n")
            for terminal, info in self.export_terminals.items():
                f.write(f"{terminal}:\n")
                f.write(f"  Location: {info['location']}\n")
                f.write(f"  Capacity: {info['capacity']}\n")
                f.write(f"  Products: {info['products']}\n")
                f.write(f"  Export markets: {info['export_markets']}\n\n")

            # Flow pattern
            f.write("="*80 + "\n")
            f.write("ESTABLISHED FLOW PATTERN:\n")
            f.write("="*80 + "\n\n")
            f.write("REVERSE FLOW from Fertilizer (Grain DOWN, Fertilizer UP):\n\n")
            f.write("1. Grain production in Midwest (Sept-Nov harvest)\n")
            f.write("2. Barge loading at upriver elevators (178 elevators)\n")
            f.write("3. Barge transport DOWNRIVER to Lower Mississippi\n")
            f.write("4. Transfer to ocean vessels at export terminals\n")
            f.write("5. Export to Asia, Latin America, global markets\n\n")

            # USDA data sources
            f.write("="*80 + "\n")
            f.write("USDA DATA SOURCES FOR VALIDATION:\n")
            f.write("="*80 + "\n\n")
            for source, description in self.usda_data_sources.items():
                f.write(f"{source}:\n  {description}\n\n")

            f.write("FERTILIZER DEMAND VALIDATION:\n")
            f.write("-" * 40 + "\n")
            f.write("Calculate bottom-up from crop planted acres:\n")
            f.write("  Corn: 140 lbs N + 60 lbs P + 60 lbs K = 260 lbs/acre\n")
            f.write("  Soybeans: 10 lbs N + 40 lbs P + 60 lbs K = 110 lbs/acre\n")
            f.write("  Wheat: 90 lbs N + 50 lbs P + 40 lbs K = 180 lbs/acre\n\n")
            f.write("Example (Illinois corn 11M acres):\n")
            f.write("  11M acres × 260 lbs/acre = 2.86B lbs = 1.43M tons\n\n")
            f.write("Compare regional demand to 8.86M tons/year fertilizer imports\n")
            f.write("to validate upriver distribution pattern.\n\n")

            f.write("="*80 + "\n")

        print(f"\nReport saved to: {report_file}")
        return report_file

    def run_analysis(self):
        """Run complete grain flow analysis"""
        print("\n" + "="*80)
        print("GRAIN FLOW ANALYSIS")
        print("Midwest Production to Lower Mississippi Export Terminals")
        print("="*80)

        # Load data
        df = self.load_manifest_data()
        df_grain = self.filter_grain_cargo(df)

        # Analyze imports (if any - expected to be minimal)
        grain_import_stats = self.analyze_grain_imports(df_grain)

        # Load national grain facilities
        grain_facilities = self.load_national_grain_facilities()

        # Document export flow pattern
        self.document_export_flow_pattern()

        # Document USDA data sources
        self.document_usda_data_integration()

        # Generate report
        report_file = self.generate_report(grain_import_stats)

        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print(f"\nReport saved to: {self.output_dir}")
        print("\nNEXT STEPS:")
        print("  1. Obtain USDA FGIS grain export data for Lower Mississippi")
        print("  2. Download USDA NASS crop planted acres (geospatial)")
        print("  3. Get fertilizer application rates by crop/region")
        print("  4. Calculate bottom-up fertilizer demand validation")
        print("  5. Integrate USDA AMS barge transport data")

if __name__ == "__main__":
    analyzer = GrainFlowAnalyzer()
    analyzer.run_analysis()
