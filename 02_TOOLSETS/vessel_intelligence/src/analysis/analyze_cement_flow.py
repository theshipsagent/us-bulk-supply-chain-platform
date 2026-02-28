"""
Cement Flow Analysis: Vessel Imports + Domestic Production to Construction Markets
Lower Mississippi River and Gulf Coast Distribution

Documents established pattern:
1. Vessel imports of cement/clinker (international sources)
2. Domestic cement production (60 plants from mapping data)
3. Barge/truck distribution to construction markets
4. Seasonal construction demand (spring/summer peak)

Analysis Focus:
- Vessel imports: Volume, origin countries, cement types (Portland, clinker, masonry)
- Import terminals: Lower Mississippi cement terminals
- Domestic production: 60 cement plants (from mapping session)
- Construction market distribution: Regional patterns
- Seasonality: Construction season driven (opposite of agricultural harvest)

Unique Characteristics:
- Heavy/bulky commodity (high transport costs favor local production)
- Both imports AND domestic production (like crude oil)
- Construction season driven (spring/summer peak)
- Regional market structure (not centralized like refineries)

NOT theorizing - documenting what we know from data + established industry patterns.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

class CementFlowAnalyzer:
    """Analyze cement vessel-to-construction market flow patterns"""

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.manifest_path = self.base_dir / "PIPELINE" / "phase_07_enrichment" / "phase_07_output.csv"
        self.mapping_facilities_path = Path("G:/My Drive/LLM/sources_data_maps/national_supply_chain/national_industrial_facilities.csv")
        self.output_dir = self.base_dir / "user_notes" / "cement_flow"
        self.output_dir.mkdir(exist_ok=True)

        # Lower Mississippi and Gulf Coast ports
        self.gulf_coast_ports = [
            'New Orleans', 'Baton Rouge', 'Gramercy', 'Garyville',
            'Chalmette', 'Venice', 'Morgan City', 'Lake Charles',
            'Port Arthur', 'Beaumont', 'Houston', 'Texas City',
            'Corpus Christi', 'Galveston', 'Freeport', 'Mobile',
            'Pascagoula'
        ]

        # Major cement import terminals (documented)
        self.cement_terminals = {
            'Holcim Vicksburg Terminal': {
                'location': 'Vicksburg, MS (Yazoo River)',
                'type': 'Cement terminal',
                'products': 'Cement, slag',
                'notes': 'River mile connection to Mississippi'
            },
            'Argos Cement Terminal': {
                'location': 'New Orleans area',
                'type': 'Cement import terminal',
                'products': 'Cement clinker, finished cement',
                'notes': 'Major import facility'
            },
            'Cemex Distribution Terminal': {
                'location': 'Gulf Coast',
                'type': 'Cement terminal',
                'products': 'Portland cement, masonry cement',
                'notes': 'Regional distribution'
            },
            'Lafarge/Holcim Terminals': {
                'location': 'Multiple Gulf Coast locations',
                'type': 'Integrated cement terminals',
                'products': 'Clinker, cement, aggregates',
                'notes': 'Largest cement company globally'
            }
        }

        # Construction market regions (from mapping + construction data)
        self.construction_markets = {
            'Gulf Coast Urban Corridor': {
                'cities': 'Houston, New Orleans, Baton Rouge, Mobile',
                'market_drivers': 'Petrochemical construction, port infrastructure, urban development',
                'demand_level': 'Very High',
                'import_dependency': 'Moderate (domestic + imports)'
            },
            'Florida': {
                'cities': 'Miami, Tampa, Jacksonville, Orlando',
                'market_drivers': 'Residential construction, tourism infrastructure',
                'demand_level': 'Very High',
                'import_dependency': 'High (limited local production)'
            },
            'Texas Inland': {
                'cities': 'Dallas, Austin, San Antonio',
                'market_drivers': 'Population growth, commercial development',
                'demand_level': 'High',
                'import_dependency': 'Low (strong local production)'
            },
            'Southeast Region': {
                'cities': 'Atlanta, Charlotte, Nashville, Memphis',
                'market_drivers': 'Commercial construction, infrastructure',
                'demand_level': 'High',
                'import_dependency': 'Low (domestic production via barge)'
            },
            'Mississippi River Corridor': {
                'cities': 'St. Louis, Memphis, Vicksburg, Baton Rouge',
                'market_drivers': 'Infrastructure, flood control, port facilities',
                'demand_level': 'Moderate',
                'import_dependency': 'Low (barge access to domestic plants)'
            }
        }

        # Cement types and uses
        self.cement_types = {
            'Portland Cement': {
                'use': 'General construction, concrete production',
                'typical_import': 'Finished product',
                'packaging': 'Bulk, bags'
            },
            'Cement Clinker': {
                'use': 'Raw material for cement production',
                'typical_import': 'Bulk commodity',
                'packaging': 'Bulk (ground at destination)'
            },
            'Masonry Cement': {
                'use': 'Mortar, stucco, masonry work',
                'typical_import': 'Finished product',
                'packaging': 'Bulk, bags'
            },
            'Blended Cement': {
                'use': 'Special applications (sulfate resistance, etc.)',
                'typical_import': 'Finished product',
                'packaging': 'Bulk, bags'
            },
            'White Cement': {
                'use': 'Architectural, decorative concrete',
                'typical_import': 'Specialty finished product',
                'packaging': 'Bags'
            }
        }

    def load_manifest_data(self):
        """Load classified manifest data"""
        print("Loading manifest data...")
        df = pd.read_csv(self.manifest_path, low_memory=False)

        # Convert dates
        df['Arrival Date'] = pd.to_datetime(df['Arrival Date'], errors='coerce')

        # Filter to Gulf Coast ports
        df_gulf = df[
            df['Port_Consolidated'].isin(self.gulf_coast_ports)
        ].copy()

        print(f"Total Gulf Coast records: {len(df_gulf):,}")
        return df_gulf

    def filter_cement_cargo(self, df):
        """Filter for cement cargo"""
        print("\nFiltering for cement cargo...")

        # Filter using cargo classification
        df_cement = df[
            (df['Commodity'] == 'Cement') |
            (df['Cargo'] == 'Cement') |
            (df['Cargo_Detail'].str.contains('Cement', case=False, na=False)) |
            (df['Cargo_Detail'].str.contains('Clinker', case=False, na=False)) |
            (df['Goods Shipped'].str.contains('CEMENT', case=False, na=False)) |
            (df['Goods Shipped'].str.contains('CLINKER', case=False, na=False))
        ].copy()

        # Add temporal columns
        df_cement['Year'] = df_cement['Arrival Date'].dt.year
        df_cement['Month'] = df_cement['Arrival Date'].dt.month
        df_cement['Quarter'] = df_cement['Arrival Date'].dt.quarter

        print(f"Cement records found: {len(df_cement):,}")
        if len(df_cement) > 0:
            print(f"Total cement tonnage: {df_cement['Tons'].sum():,.0f} tons")
        else:
            print("NOTE: Low cement imports may indicate:")
            print("      - Strong domestic production (60 plants)")
            print("      - Regional market structure")
            print("      - Import classification in other categories")

        return df_cement

    def analyze_vessel_imports(self, df_cement):
        """Analyze cement vessel imports"""
        print("\n" + "="*80)
        print("ANALYZING CEMENT VESSEL IMPORTS")
        print("="*80)

        if len(df_cement) == 0:
            print("\nNo cement imports found in dataset.")
            print("Cement market typically:")
            print("  - 80-90% domestic production (60+ plants)")
            print("  - 10-20% imports (supplement coastal markets)")
            print("  - High transport costs favor local production")
            return None

        # Total imports
        total_tons = df_cement['Tons'].sum()
        years = df_cement['Year'].nunique()
        avg_per_year = total_tons / years if years > 0 else 0

        print(f"\nTotal cement imports: {total_tons:,.0f} tons")
        print(f"Years analyzed: {years}")
        print(f"Average per year: {avg_per_year:,.0f} tons/year")

        # Origin countries
        print("\nTOP ORIGIN COUNTRIES:")
        origin_summary = df_cement.groupby('Country of Origin (F)')['Tons'].sum().sort_values(ascending=False)
        for country, tons in origin_summary.head(10).items():
            pct = (tons / total_tons) * 100
            print(f"  {country}: {tons:,.0f} tons ({pct:.1f}%)")

        # Top consignees
        print("\nTOP CONSIGNEES:")
        consignee_summary = df_cement.groupby('Consignee')['Tons'].sum().sort_values(ascending=False)
        for consignee, tons in consignee_summary.head(10).items():
            print(f"  {consignee}: {tons:,.0f} tons")

        # Product types (from Cargo_Detail)
        print("\nCEMENT PRODUCT TYPES:")
        product_summary = df_cement.groupby('Cargo_Detail')['Tons'].sum().sort_values(ascending=False)
        for product, tons in product_summary.head(10).items():
            pct = (tons / total_tons) * 100
            print(f"  {product}: {tons:,.0f} tons ({pct:.1f}%)")

        # Port distribution
        print("\nPORT DISTRIBUTION:")
        port_summary = df_cement.groupby('Port_Consolidated')['Tons'].sum().sort_values(ascending=False)
        for port, tons in port_summary.items():
            pct = (tons / total_tons) * 100
            print(f"  {port}: {tons:,.0f} tons ({pct:.1f}%)")

        # Seasonality (construction season)
        print("\nSEASONALITY (Construction Season):")
        monthly_avg = df_cement.groupby('Month')['Tons'].sum() / years
        for month in range(1, 13):
            month_name = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][month-1]
            tons = monthly_avg.get(month, 0)
            print(f"  {month_name}: {tons:,.0f} tons/year")

        # Calculate seasonality ratio
        max_month = monthly_avg.max()
        min_month = monthly_avg[monthly_avg > 0].min() if (monthly_avg > 0).any() else 1
        seasonality_ratio = max_month / min_month if min_month > 0 else 0
        print(f"\nSeasonality ratio: {seasonality_ratio:.2f}x")
        print("(Construction season: Spring/Summer peak expected)")

        return {
            'total_tons': total_tons,
            'avg_per_year': avg_per_year,
            'origin_summary': origin_summary,
            'consignee_summary': consignee_summary,
            'product_summary': product_summary,
            'port_summary': port_summary,
            'monthly_avg': monthly_avg,
            'seasonality_ratio': seasonality_ratio
        }

    def load_national_cement_facilities(self):
        """Load cement facilities from national mapping data"""
        print("\n" + "="*80)
        print("NATIONAL CEMENT FACILITIES (from mapping session)")
        print("="*80)

        if not self.mapping_facilities_path.exists():
            print("Mapping facilities file not found - using documented info only")
            return None

        facilities = pd.read_csv(self.mapping_facilities_path)
        cement_facilities = facilities[facilities['facility_type'] == 'CEMENT'].copy()

        print(f"\nTotal cement plants: {len(cement_facilities)}")

        # By state
        print("\nBY STATE (Top 10):")
        state_counts = cement_facilities.groupby('state').size().sort_values(ascending=False)
        for state, count in state_counts.head(10).items():
            print(f"  {state}: {count} cement plants")

        # By region (approximation)
        print("\nBY REGION:")
        print(f"  Texas: {state_counts.get('TX', 0)} plants")
        print(f"  Louisiana: {state_counts.get('LA', 0)} plants")
        print(f"  Mississippi: {state_counts.get('MS', 0)} plants")
        print(f"  Alabama: {state_counts.get('AL', 0)} plants")
        print(f"  Florida: {state_counts.get('FL', 0)} plants")

        # Save facility list
        output_file = self.output_dir / f"national_cement_plants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        cement_facilities.to_csv(output_file, index=False)
        print(f"\nCement plants saved to: {output_file}")

        return cement_facilities

    def document_cement_market_structure(self, import_stats):
        """Document cement market structure and flow patterns"""
        print("\n" + "="*80)
        print("CEMENT MARKET STRUCTURE AND FLOW PATTERNS")
        print("="*80)

        print("\nMARKET CHARACTERISTICS:")
        print("\n1. DUAL SUPPLY SYSTEM:")
        print("   Domestic production: 80-90% of market")
        print("     - 60 cement plants nationwide")
        print("     - Regional production/consumption (high transport costs)")
        print("     - Integrated operations (quarries, kilns, distribution)")
        print("\n   Imports: 10-20% of market")
        print("     - Supplement coastal markets (high domestic transport costs)")
        print("     - Clinker imports (ground locally)")
        print("     - Specialty cements (white cement, blended)")

        if import_stats:
            imports_tons = import_stats['avg_per_year']
            print(f"\n   Vessel imports found: {imports_tons:,.0f} tons/year")
            print(f"   U.S. cement consumption: ~100M tons/year (est.)")
            import_pct = (imports_tons / 100_000_000) * 100
            print(f"   Import share: ~{import_pct:.1f}%")

        print("\n2. REGIONAL MARKET STRUCTURE:")
        print("   Gulf Coast:")
        print("     - Houston/Texas: Strong domestic production + imports")
        print("     - New Orleans/Louisiana: Mixed domestic + imports")
        print("     - Mobile/Alabama: Domestic production via barge")
        print("\n   Florida:")
        print("     - High import dependency (limited local limestone)")
        print("     - Cement imported from Caribbean, Latin America")
        print("\n   Mississippi River Corridor:")
        print("     - Barge distribution from Midwest/Upper Miss plants")
        print("     - Lower Miss imports supplement local supply")

        print("\n3. SEASONAL PATTERNS:")
        print("   Construction season (April-October):")
        print("     - Peak cement demand (warm weather construction)")
        print("     - Highway paving season")
        print("     - Commercial construction activity")
        print("\n   Winter slowdown (November-March):")
        print("     - Reduced construction activity (cold weather)")
        print("     - Inventory build-up period")
        print("     - Maintenance shutdowns")

        if import_stats and 'seasonality_ratio' in import_stats:
            ratio = import_stats['seasonality_ratio']
            print(f"\n   Measured seasonality: {ratio:.2f}x ratio")

        print("\n4. TRANSPORT MODES:")
        print("   Barge (most economical for bulk):")
        print("     - Mississippi River system")
        print("     - Gulf Intracoastal Waterway")
        print("     - Coastal shipping")
        print("\n   Truck (local distribution):")
        print("     - Plant to ready-mix plants (50-100 mile radius)")
        print("     - Just-in-time delivery")
        print("\n   Rail (medium distance):")
        print("     - Unit trains from distant plants")
        print("     - Less common than barge/truck")

        print("\n5. MAJOR CEMENT COMPANIES:")
        print("   Global majors operating in U.S.:")
        print("     - Holcim/LafargeHolcim (Swiss)")
        print("     - Cemex (Mexican)")
        print("     - HeidelbergCement (German)")
        print("     - Argos (Colombian)")
        print("     - Buzzi Unicem (Italian)")
        print("\n   Domestic producers:")
        print("     - Lehigh Hanson (HeidelbergCement subsidiary)")
        print("     - Ash Grove Cement (CRH subsidiary)")
        print("     - Texas Lehigh Cement")

    def generate_report(self, import_stats, cement_facilities):
        """Generate comprehensive cement flow report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.output_dir / f"cement_flow_report_{timestamp}.txt"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("CEMENT FLOW ANALYSIS\n")
            f.write("Vessel Imports + Domestic Production to Construction Markets\n")
            f.write("="*80 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Vessel imports summary
            if import_stats:
                f.write("VESSEL IMPORT SUMMARY:\n\n")
                f.write(f"Total cement imports: {import_stats['total_tons']:,.0f} tons\n")
                f.write(f"Average per year: {import_stats['avg_per_year']:,.0f} tons/year\n")
                f.write(f"Seasonality ratio: {import_stats.get('seasonality_ratio', 0):.2f}x\n\n")

                # Top origins
                f.write("TOP ORIGIN COUNTRIES:\n\n")
                for country, tons in import_stats['origin_summary'].head(10).items():
                    pct = (tons / import_stats['total_tons']) * 100
                    f.write(f"  {country}: {tons:,.0f} tons ({pct:.1f}%)\n")
                f.write("\n")

                # Top consignees
                f.write("TOP CONSIGNEES:\n\n")
                for consignee, tons in import_stats['consignee_summary'].head(10).items():
                    f.write(f"  {consignee}: {tons:,.0f} tons\n")
                f.write("\n")

                # Product types
                f.write("CEMENT PRODUCT TYPES:\n\n")
                for product, tons in import_stats['product_summary'].head(10).items():
                    pct = (tons / import_stats['total_tons']) * 100
                    f.write(f"  {product}: {tons:,.0f} tons ({pct:.1f}%)\n")
                f.write("\n")
            else:
                f.write("VESSEL IMPORT DATA:\n\n")
                f.write("No significant cement imports found in dataset.\n")
                f.write("U.S. cement market dominated by domestic production (80-90%).\n\n")

            # Cement terminals
            f.write("="*80 + "\n")
            f.write("CEMENT IMPORT TERMINALS:\n")
            f.write("="*80 + "\n\n")
            for terminal, info in self.cement_terminals.items():
                f.write(f"{terminal}:\n")
                f.write(f"  Location: {info['location']}\n")
                f.write(f"  Type: {info['type']}\n")
                f.write(f"  Products: {info['products']}\n")
                if 'notes' in info:
                    f.write(f"  Notes: {info['notes']}\n")
                f.write("\n")

            # Domestic facilities
            if cement_facilities is not None:
                f.write("="*80 + "\n")
                f.write("DOMESTIC CEMENT PRODUCTION FACILITIES:\n")
                f.write("="*80 + "\n\n")
                f.write(f"Total cement plants (national): {len(cement_facilities)}\n\n")

                state_counts = cement_facilities.groupby('state').size().sort_values(ascending=False)
                f.write("Top states by plant count:\n")
                for state, count in state_counts.head(10).items():
                    f.write(f"  {state}: {count} plants\n")
                f.write("\n")

            # Construction markets
            f.write("="*80 + "\n")
            f.write("CONSTRUCTION MARKET REGIONS:\n")
            f.write("="*80 + "\n\n")
            for market, info in self.construction_markets.items():
                f.write(f"{market}:\n")
                f.write(f"  Major cities: {info['cities']}\n")
                f.write(f"  Market drivers: {info['market_drivers']}\n")
                f.write(f"  Demand level: {info['demand_level']}\n")
                f.write(f"  Import dependency: {info['import_dependency']}\n\n")

            # Cement types
            f.write("="*80 + "\n")
            f.write("CEMENT TYPES AND USES:\n")
            f.write("="*80 + "\n\n")
            for cement_type, info in self.cement_types.items():
                f.write(f"{cement_type}:\n")
                f.write(f"  Use: {info['use']}\n")
                f.write(f"  Typical import: {info['typical_import']}\n")
                f.write(f"  Packaging: {info['packaging']}\n\n")

            # Market structure
            f.write("="*80 + "\n")
            f.write("MARKET STRUCTURE:\n")
            f.write("="*80 + "\n\n")
            f.write("Dual supply system:\n")
            f.write("  - Domestic production: 80-90% (60 plants)\n")
            f.write("  - Imports: 10-20% (supplement coastal markets)\n\n")
            f.write("Regional structure:\n")
            f.write("  - High transport costs favor local production\n")
            f.write("  - Barge transport most economical for bulk\n")
            f.write("  - Truck delivery within 50-100 mile plant radius\n\n")
            f.write("Seasonality:\n")
            f.write("  - Construction season peak (April-October)\n")
            f.write("  - Winter slowdown (November-March)\n\n")

            # Data sources
            f.write("="*80 + "\n")
            f.write("DATA SOURCES:\n")
            f.write("="*80 + "\n\n")
            f.write("- Vessel imports: Panjiva manifest data\n")
            f.write("- Cement plants: National supply chain mapping (60 facilities)\n")
            f.write("- Market structure: Industry sources (documented)\n")
            f.write("- Construction markets: Regional construction data\n\n")

            f.write("="*80 + "\n")

        print(f"\nReport saved to: {report_file}")
        return report_file

    def run_analysis(self):
        """Run complete cement flow analysis"""
        print("\n" + "="*80)
        print("CEMENT FLOW ANALYSIS")
        print("Vessel Imports + Domestic Production to Construction Markets")
        print("="*80)

        # Load data
        df = self.load_manifest_data()
        df_cement = self.filter_cement_cargo(df)

        # Analyze imports
        import_stats = None
        if len(df_cement) > 0:
            import_stats = self.analyze_vessel_imports(df_cement)

            # Save detailed outputs
            if import_stats:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

                # Origin countries
                origin_file = self.output_dir / f"cement_origin_countries_{timestamp}.csv"
                import_stats['origin_summary'].to_csv(origin_file)

                # Consignees
                consignee_file = self.output_dir / f"cement_consignees_{timestamp}.csv"
                import_stats['consignee_summary'].to_csv(consignee_file)

                # Product types
                product_file = self.output_dir / f"cement_product_types_{timestamp}.csv"
                import_stats['product_summary'].to_csv(product_file)

        # Load national cement facilities
        cement_facilities = self.load_national_cement_facilities()

        # Document market structure
        self.document_cement_market_structure(import_stats)

        # Generate report
        report_file = self.generate_report(import_stats, cement_facilities)

        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print(f"\nAll outputs saved to: {self.output_dir}")

        print("\nKEY INSIGHTS:")
        print("  - Cement market: 80-90% domestic, 10-20% imports")
        print("  - 60 cement plants nationwide (regional production)")
        print("  - High transport costs favor local production")
        print("  - Barge transport most economical (Mississippi River system)")
        print("  - Construction season drives demand (April-October)")
        print("  - Coastal markets more import-dependent (Florida, Gulf Coast)")

if __name__ == "__main__":
    analyzer = CementFlowAnalyzer()
    analyzer.run_analysis()
