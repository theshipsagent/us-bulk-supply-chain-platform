"""
Fertilizer Flow Analysis: Vessel-to-Barge Transfer to Upriver Agricultural Markets
Lower Mississippi River to Midwest Grain Belt

Documents established pattern:
1. Ocean vessel imports fertilizer to Lower Mississippi terminals
2. Transfer to barge for upriver transport
3. Delivery to agricultural regions (Illinois, Iowa, Ohio River Valley) during planting season

Analysis Focus:
- Vessel imports: Volume, origin countries, consignees, terminals, seasonality
- Known fertilizer terminals/plants on Mississippi/Illinois/Ohio river system
- Agricultural demand regions (grain belt states)
- Match imports to likely destinations based on geography & planting seasons

References:
- Previous fertilizer work: project_fertilizer directory (YARA analysis, European origins)
- National mapping: 33 fertilizer plants (sources_data_maps)
- Temporal analysis: 3.05x seasonality ratio (planting season driven)

NOT theorizing - documenting what we know from data + established industry patterns.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

class FertilizerFlowAnalyzer:
    """Analyze fertilizer vessel-to-barge-to-agricultural market flow patterns"""

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.manifest_path = self.base_dir / "PIPELINE" / "phase_07_enrichment" / "phase_07_output.csv"
        self.mapping_facilities_path = Path("G:/My Drive/LLM/sources_data_maps/national_supply_chain/national_industrial_facilities.csv")
        self.output_dir = self.base_dir / "user_notes" / "fertilizer_flow"
        self.output_dir.mkdir(exist_ok=True)

        # Lower Mississippi ports
        self.lower_miss_ports = [
            'New Orleans', 'Baton Rouge', 'Gramercy', 'Garyville',
            'Chalmette', 'Venice', 'Morgan City', 'Lake Charles'
        ]

        # Known fertilizer terminals/plants on Mississippi River system (from mapping + industry sources)
        self.fertilizer_terminals = {
            'Helm Fertilizer Terminal Memphis': {
                'location': 'Memphis, TN',
                'facility_type': 'Liquid bulk fertilizer terminal',
                'river': 'Memphis Harbor',
                'barge_accessible': True,
                'serves': 'Mid-South agricultural region'
            },
            'Pemiscot County Port Authority': {
                'location': 'Caruthersville, MO',
                'facility_type': 'Fertilizer dock',
                'river': 'Mississippi River',
                'barge_accessible': True,
                'serves': 'Missouri/Arkansas farmland'
            },
            'Mississippi Lime Terminal': {
                'location': 'Ste. Genevieve, MO',
                'facility_type': 'Lime terminal (agricultural lime)',
                'river': 'Mississippi River',
                'barge_accessible': True,
                'serves': 'Upper Mississippi agricultural region'
            },
            'Illinois River Fertilizer Distribution': {
                'location': 'Illinois River corridor',
                'facility_type': 'Multiple fertilizer terminals',
                'river': 'Illinois River',
                'barge_accessible': True,
                'serves': 'Illinois/Iowa corn belt'
            },
            'Ohio River Valley Distribution': {
                'location': 'Ohio River corridor',
                'facility_type': 'Multiple fertilizer terminals',
                'river': 'Ohio River',
                'barge_accessible': True,
                'serves': 'Ohio/Indiana farmland'
            }
        }

        # Agricultural market regions (from mapping analysis)
        self.agricultural_markets = {
            'Illinois/Iowa Grain Belt': {
                'primary_crop': 'Corn, soybeans',
                'market_cluster': 'Chicago/Illinois River (190 facilities)',
                'distance_from_lower_miss': '773 miles',
                'river_route': 'Mississippi to Illinois Waterway',
                'peak_fertilizer_demand': 'March-May (spring planting)'
            },
            'Memphis/Arkansas Delta': {
                'primary_crop': 'Rice, cotton, soybeans',
                'market_cluster': 'Memphis/Cincinnati (292 facilities)',
                'distance_from_lower_miss': '496 miles',
                'river_route': 'Mississippi River',
                'peak_fertilizer_demand': 'March-June'
            },
            'Ohio River Valley': {
                'primary_crop': 'Corn, soybeans',
                'market_cluster': 'Ohio River corridor (73-72 facilities)',
                'distance_from_lower_miss': '600-1000 miles',
                'river_route': 'Mississippi to Ohio River',
                'peak_fertilizer_demand': 'April-May'
            },
            'Upper Mississippi': {
                'primary_crop': 'Corn, soybeans',
                'market_cluster': 'St. Paul/Minnesota (19 facilities)',
                'distance_from_lower_miss': '1050 miles',
                'river_route': 'Mississippi River north',
                'peak_fertilizer_demand': 'April-May'
            }
        }

    def load_manifest_data(self):
        """Load classified manifest data"""
        print("Loading manifest data...")
        df = pd.read_csv(self.manifest_path, low_memory=False)

        # Convert dates
        df['Arrival Date'] = pd.to_datetime(df['Arrival Date'], errors='coerce')

        # Filter to Lower Mississippi ports (data is already imports-only)
        df_lower_miss = df[
            df['Port_Consolidated'].isin(self.lower_miss_ports)
        ].copy()

        print(f"Total Lower Miss imports: {len(df_lower_miss):,} records")
        return df_lower_miss

    def filter_fertilizer_cargo(self, df):
        """Filter for fertilizer cargo"""
        print("\nFiltering for fertilizer cargo...")

        # Filter using cargo classification
        df_fert = df[
            (df['Commodity'] == 'Fertilizer') |
            (df['Cargo'] == 'Nitrogen Fertilizers') |
            (df['Cargo'] == 'Phosphate Fertilizers') |
            (df['Cargo'] == 'Potash Fertilizers') |
            (df['Cargo'].str.contains('Fertilizer', case=False, na=False))
        ].copy()

        # Add temporal columns
        df_fert['Year'] = df_fert['Arrival Date'].dt.year
        df_fert['Month'] = df_fert['Arrival Date'].dt.month
        df_fert['Quarter'] = df_fert['Arrival Date'].dt.quarter

        print(f"Fertilizer records found: {len(df_fert):,}")
        print(f"Total fertilizer tonnage: {df_fert['Tons'].sum():,.0f} tons")

        return df_fert

    def analyze_vessel_imports(self, df_fert):
        """Analyze fertilizer vessel imports"""
        print("\n" + "="*80)
        print("ANALYZING FERTILIZER VESSEL IMPORTS")
        print("="*80)

        # Total imports
        total_tons = df_fert['Tons'].sum()
        years = df_fert['Year'].nunique()
        avg_per_year = total_tons / years if years > 0 else 0

        print(f"\nTotal fertilizer imports: {total_tons:,.0f} tons")
        print(f"Years analyzed: {years}")
        print(f"Average per year: {avg_per_year:,.0f} tons/year")

        # Origin countries
        print("\nTOP ORIGIN COUNTRIES:")
        origin_summary = df_fert.groupby('Country of Origin (F)')['Tons'].sum().sort_values(ascending=False)
        for country, tons in origin_summary.head(10).items():
            pct = (tons / total_tons) * 100
            print(f"  {country}: {tons:,.0f} tons ({pct:.1f}%)")

        # Top consignees
        print("\nTOP CONSIGNEES:")
        consignee_summary = df_fert.groupby('Consignee')['Tons'].sum().sort_values(ascending=False)
        for consignee, tons in consignee_summary.head(10).items():
            print(f"  {consignee}: {tons:,.0f} tons")

        # Seasonality analysis
        print("\nSEASONALITY ANALYSIS:")
        monthly_avg = df_fert.groupby('Month')['Tons'].sum() / years
        for month in range(1, 13):
            month_name = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][month-1]
            tons = monthly_avg.get(month, 0)
            print(f"  {month_name}: {tons:,.0f} tons/year")

        # Port distribution
        print("\nPORT DISTRIBUTION:")
        port_summary = df_fert.groupby('Port_Consolidated')['Tons'].sum().sort_values(ascending=False)
        for port, tons in port_summary.items():
            pct = (tons / total_tons) * 100
            print(f"  {port}: {tons:,.0f} tons ({pct:.1f}%)")

        return {
            'total_tons': total_tons,
            'avg_per_year': avg_per_year,
            'origin_summary': origin_summary,
            'consignee_summary': consignee_summary,
            'monthly_avg': monthly_avg,
            'port_summary': port_summary
        }

    def analyze_fertilizer_types(self, df_fert):
        """Analyze fertilizer product types"""
        print("\n" + "="*80)
        print("FERTILIZER PRODUCT TYPES")
        print("="*80)

        # By Cargo_Detail
        print("\nBY PRODUCT TYPE:")
        cargo_detail_summary = df_fert.groupby('Cargo_Detail')['Tons'].sum().sort_values(ascending=False)
        for cargo_detail, tons in cargo_detail_summary.head(15).items():
            print(f"  {cargo_detail}: {tons:,.0f} tons")

        return cargo_detail_summary

    def load_national_fertilizer_facilities(self):
        """Load fertilizer facilities from national mapping data"""
        print("\n" + "="*80)
        print("NATIONAL FERTILIZER FACILITIES (from mapping session)")
        print("="*80)

        if not self.mapping_facilities_path.exists():
            print("Mapping facilities file not found - using documented terminals only")
            return None

        facilities = pd.read_csv(self.mapping_facilities_path)
        fert_facilities = facilities[facilities['facility_type'] == 'FERTILIZER'].copy()

        print(f"\nTotal fertilizer facilities: {len(fert_facilities)}")

        # By state
        print("\nBY STATE:")
        state_counts = fert_facilities.groupby('state').size().sort_values(ascending=False)
        for state, count in state_counts.items():
            print(f"  {state}: {count} facilities")

        # Save facility list
        output_file = self.output_dir / f"national_fertilizer_facilities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        fert_facilities.to_csv(output_file, index=False)
        print(f"\nFertilizer facilities saved to: {output_file}")

        return fert_facilities

    def estimate_barge_destinations(self, df_fert, import_stats):
        """Estimate barge destinations based on agricultural markets"""
        print("\n" + "="*80)
        print("ESTIMATED BARGE DESTINATIONS (based on agricultural demand)")
        print("="*80)

        total_tons = import_stats['total_tons']
        avg_per_year = import_stats['avg_per_year']

        print(f"\nTotal vessel imports: {avg_per_year:,.0f} tons/year")
        print("\nLIKELY UPRIVER DESTINATIONS:")

        # Rough distribution estimates based on agricultural market size
        # (from mapping analysis + USDA crop data patterns)
        destinations = {
            'Illinois/Iowa Grain Belt': {
                'estimated_pct': 40,
                'route': 'Mississippi to Illinois Waterway',
                'distance': '773 miles',
                'primary_season': 'March-May'
            },
            'Memphis/Arkansas Delta': {
                'estimated_pct': 20,
                'route': 'Mississippi River',
                'distance': '496 miles',
                'primary_season': 'March-June'
            },
            'Ohio River Valley': {
                'estimated_pct': 20,
                'route': 'Mississippi to Ohio River',
                'distance': '600-1000 miles',
                'primary_season': 'April-May'
            },
            'Upper Mississippi': {
                'estimated_pct': 10,
                'route': 'Mississippi River north',
                'distance': '1050 miles',
                'primary_season': 'April-May'
            },
            'Local Louisiana/Gulf': {
                'estimated_pct': 10,
                'route': 'Local distribution',
                'distance': '0-200 miles',
                'primary_season': 'Year-round'
            }
        }

        for destination, info in destinations.items():
            est_tons = avg_per_year * (info['estimated_pct'] / 100)
            print(f"\n{destination}:")
            print(f"  Estimated tonnage: {est_tons:,.0f} tons/year ({info['estimated_pct']}%)")
            print(f"  Route: {info['route']}")
            print(f"  Distance: {info['distance']}")
            print(f"  Peak season: {info['primary_season']}")

    def generate_report(self, df_fert, import_stats, cargo_detail_summary):
        """Generate comprehensive fertilizer flow report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.output_dir / f"fertilizer_flow_report_{timestamp}.txt"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("FERTILIZER FLOW ANALYSIS\n")
            f.write("Vessel-to-Barge-to-Agricultural Market Supply Chain\n")
            f.write("Lower Mississippi River to Midwest Grain Belt\n")
            f.write("="*80 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Vessel import summary
            f.write("VESSEL IMPORT SUMMARY:\n\n")
            f.write(f"Total fertilizer imports: {import_stats['total_tons']:,.0f} tons\n")
            f.write(f"Average per year: {import_stats['avg_per_year']:,.0f} tons/year\n\n")

            # Top origins
            f.write("TOP ORIGIN COUNTRIES:\n\n")
            for country, tons in import_stats['origin_summary'].head(10).items():
                pct = (tons / import_stats['total_tons']) * 100
                f.write(f"  {country}: {tons:,.0f} tons ({pct:.1f}%)\n")

            # Top consignees
            f.write("\nTOP CONSIGNEES:\n\n")
            for consignee, tons in import_stats['consignee_summary'].head(10).items():
                f.write(f"  {consignee}: {tons:,.0f} tons\n")

            # Seasonality
            f.write("\nSEASONALITY (Monthly Average):\n\n")
            for month in range(1, 13):
                month_name = ['January', 'February', 'March', 'April', 'May', 'June',
                             'July', 'August', 'September', 'October', 'November', 'December'][month-1]
                tons = import_stats['monthly_avg'].get(month, 0)
                f.write(f"  {month_name}: {tons:,.0f} tons\n")

            # Product types
            f.write("\nTOP FERTILIZER PRODUCTS:\n\n")
            for product, tons in cargo_detail_summary.head(10).items():
                f.write(f"  {product}: {tons:,.0f} tons\n")

            # Fertilizer terminals
            f.write("\n" + "="*80 + "\n")
            f.write("DOCUMENTED FERTILIZER TERMINALS ON RIVER SYSTEM:\n")
            f.write("="*80 + "\n\n")
            for name, info in self.fertilizer_terminals.items():
                f.write(f"{name}:\n")
                f.write(f"  Location: {info['location']}\n")
                f.write(f"  Facility type: {info['facility_type']}\n")
                f.write(f"  River access: {info['river']}\n")
                f.write(f"  Serves: {info['serves']}\n\n")

            # Agricultural markets
            f.write("="*80 + "\n")
            f.write("AGRICULTURAL MARKET DESTINATIONS:\n")
            f.write("="*80 + "\n\n")
            for market, info in self.agricultural_markets.items():
                f.write(f"{market}:\n")
                f.write(f"  Primary crops: {info['primary_crop']}\n")
                f.write(f"  Market cluster: {info['market_cluster']}\n")
                f.write(f"  Distance from Lower Miss: {info['distance_from_lower_miss']}\n")
                f.write(f"  River route: {info['river_route']}\n")
                f.write(f"  Peak fertilizer demand: {info['peak_fertilizer_demand']}\n\n")

            # Established flow pattern
            f.write("="*80 + "\n")
            f.write("ESTABLISHED FLOW PATTERN:\n")
            f.write("="*80 + "\n\n")
            f.write("1. Ocean vessel imports fertilizer to Lower Mississippi terminals\n")
            f.write("   (Primarily New Orleans area)\n\n")
            f.write("2. Transfer from vessel to barge at import terminals\n\n")
            f.write("3. Barge transport upriver to agricultural regions:\n")
            f.write("   - Illinois Waterway to Iowa/Illinois grain belt\n")
            f.write("   - Mississippi River to Memphis/Arkansas Delta\n")
            f.write("   - Ohio River to Ohio/Indiana farmland\n")
            f.write("   - Upper Mississippi to Minnesota/Wisconsin\n\n")
            f.write("4. Distribution to farms during planting season (March-May peak)\n\n")
            f.write("5. Strong seasonality (3.05x ratio) driven by spring planting demand\n\n")

            # Data sources
            f.write("="*80 + "\n")
            f.write("DATA SOURCES:\n")
            f.write("="*80 + "\n\n")
            f.write("- Vessel imports: Panjiva manifest data (documented)\n")
            f.write("- Terminal locations: National supply chain mapping (documented)\n")
            f.write("- Agricultural markets: Market cluster analysis (documented)\n")
            f.write("- Seasonality: Temporal analysis (3.05x seasonal ratio)\n")
            f.write("- Previous work: G:\\My Drive\\LLM\\project_fertilizer (YARA analysis)\n")
            f.write("- Barge flows: Census waterborne commerce (to be obtained)\n\n")

            f.write("="*80 + "\n")

        print(f"\nReport saved to: {report_file}")
        return report_file

    def run_analysis(self):
        """Run complete fertilizer flow analysis"""
        print("\n" + "="*80)
        print("FERTILIZER FLOW ANALYSIS")
        print("Vessel-to-Barge-to-Agricultural Market Supply Chain")
        print("="*80)

        # Load data
        df = self.load_manifest_data()
        df_fert = self.filter_fertilizer_cargo(df)

        if len(df_fert) == 0:
            print("No fertilizer records found!")
            return

        # Analyze imports
        import_stats = self.analyze_vessel_imports(df_fert)

        # Analyze product types
        cargo_detail_summary = self.analyze_fertilizer_types(df_fert)

        # Load national facilities
        fert_facilities = self.load_national_fertilizer_facilities()

        # Estimate destinations
        self.estimate_barge_destinations(df_fert, import_stats)

        # Generate report
        report_file = self.generate_report(df_fert, import_stats, cargo_detail_summary)

        # Save detailed outputs
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Origin countries
        origin_file = self.output_dir / f"fertilizer_origin_countries_{timestamp}.csv"
        import_stats['origin_summary'].to_csv(origin_file)

        # Consignees
        consignee_file = self.output_dir / f"fertilizer_consignees_{timestamp}.csv"
        import_stats['consignee_summary'].to_csv(consignee_file)

        # Monthly seasonality
        monthly_file = self.output_dir / f"fertilizer_monthly_seasonality_{timestamp}.csv"
        import_stats['monthly_avg'].to_csv(monthly_file)

        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print(f"\nAll outputs saved to: {self.output_dir}")

if __name__ == "__main__":
    analyzer = FertilizerFlowAnalyzer()
    analyzer.run_analysis()
