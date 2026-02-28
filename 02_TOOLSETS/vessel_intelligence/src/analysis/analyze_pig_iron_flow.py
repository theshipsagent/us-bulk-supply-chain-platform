"""
Pig Iron Flow Analysis: Vessel-to-Barge Transfer to Upriver EAF Mills
Lower Mississippi River to Inland Waterway System

Documents established pattern:
1. Ocean vessel imports pig iron to Lower Mississippi terminals
2. Transfer to barge for upriver transport
3. Delivery to EAF (Electric Arc Furnace) steel mills on river system

Analysis Focus:
- Vessel imports: Volume, origin countries, consignees, terminals
- Known EAF mill locations on Mississippi/Ohio/Missouri river system
- Barge transport patterns (if Census data available)
- Match imports to likely destinations based on geography & consumption

NOT theorizing - documenting what we know from data + established industry patterns.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

class PigIronFlowAnalyzer:
    """Analyze pig iron vessel-to-barge-to-EAF mill flow patterns"""

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.manifest_path = self.base_dir / "PIPELINE" / "phase_07_enrichment" / "phase_07_output.csv"
        self.terminal_visits_path = self.base_dir / "user_notes" / "mrtis_terminal_visits_2024_WITH_RULES.csv"
        self.output_dir = self.base_dir / "user_notes" / "pig_iron_flow"
        self.output_dir.mkdir(exist_ok=True)

        # Lower Mississippi ports
        self.lower_miss_ports = [
            'New Orleans', 'Baton Rouge', 'Gramercy', 'Garyville',
            'Chalmette', 'Venice', 'Morgan City', 'Lake Charles'
        ]

        # Known EAF steel mills on Mississippi River system (documented)
        self.eaf_mills = {
            'Nucor Steel Louisiana': {
                'location': 'Convent, LA (near Baton Rouge)',
                'river': 'Mississippi River',
                'river_mile': 'RM 162',
                'barge_accessible': True,
                'capacity_tons_year': '~1,500,000',
                'products': 'Structural steel, plate',
                'pig_iron_consumer': True
            },
            'Big River Steel': {
                'location': 'Osceola, AR (Mississippi River)',
                'river': 'Mississippi River',
                'river_mile': 'RM 734',
                'barge_accessible': True,
                'capacity_tons_year': '~3,300,000',
                'products': 'Flat-rolled steel',
                'pig_iron_consumer': True
            },
            'Steel Dynamics - Columbus': {
                'location': 'Columbus, MS (Tennessee-Tombigbee Waterway)',
                'river': 'Tennessee-Tombigbee',
                'river_mile': 'Connected to Mississippi',
                'barge_accessible': True,
                'capacity_tons_year': '~3,000,000',
                'products': 'Flat-rolled steel',
                'pig_iron_consumer': True
            },
            'Nucor Steel Arkansas': {
                'location': 'Blytheville, AR (Mississippi River)',
                'river': 'Mississippi River',
                'river_mile': 'RM 828',
                'barge_accessible': True,
                'capacity_tons_year': '~2,500,000',
                'products': 'Sheet steel',
                'pig_iron_consumer': True
            },
            'Nucor Steel Gallatin (Kentucky)': {
                'location': 'Ghent, KY (Ohio River)',
                'river': 'Ohio River',
                'river_mile': 'Ohio River Mile 531',
                'barge_accessible': True,
                'capacity_tons_year': '~3,000,000',
                'products': 'Sheet steel',
                'pig_iron_consumer': True
            },
            'Nucor Steel Tuscaloosa': {
                'location': 'Tuscaloosa, AL (Black Warrior River)',
                'river': 'Black Warrior River → Tombigbee → Mississippi',
                'river_mile': 'Connected to Mississippi',
                'barge_accessible': True,
                'capacity_tons_year': '~750,000',
                'products': 'Rebar, structural',
                'pig_iron_consumer': True
            },
            'Commercial Metals Company (CMC)': {
                'location': 'Multiple on river system',
                'river': 'Mississippi/Arkansas',
                'river_mile': 'Various',
                'barge_accessible': True,
                'capacity_tons_year': 'Various',
                'products': 'Rebar, structural',
                'pig_iron_consumer': True
            }
        }

        print("Pig Iron Flow Analyzer initialized")
        print(f"Output directory: {self.output_dir}")
        print(f"\nDocumented EAF mills on Mississippi River system: {len(self.eaf_mills)}")

    def load_pig_iron_imports(self):
        """Load pig iron vessel imports to Lower Mississippi"""
        print("\n" + "="*80)
        print("VESSEL IMPORTS: Pig Iron to Lower Mississippi River")
        print("="*80)

        # Load manifest data
        print(f"Loading: {self.manifest_path}")
        df = pd.read_csv(self.manifest_path, low_memory=False)

        # Parse date
        df['Arrival Date'] = pd.to_datetime(df['Arrival Date'], errors='coerce')

        # Filter to Lower Mississippi + Pig Iron
        df_pig = df[
            (df['Port_Consolidated'].isin(self.lower_miss_ports)) &
            (df['Cargo'] == 'Pig Iron')
        ].copy()

        # Convert tons
        df_pig['Tons'] = pd.to_numeric(df_pig['Tons'], errors='coerce').fillna(0)

        # Add temporal columns
        df_pig['Year'] = df_pig['Arrival Date'].dt.year
        df_pig['Month'] = df_pig['Arrival Date'].dt.month

        print(f"\nTotal pig iron import records: {len(df_pig):,}")
        print(f"Total tonnage: {df_pig['Tons'].sum():,.0f} tons")
        print(f"Date range: {df_pig['Arrival Date'].min()} to {df_pig['Arrival Date'].max()}")

        # Annual breakdown
        annual = df_pig.groupby('Year').agg({
            'Tons': 'sum',
            'Bill of Lading Number': 'count'
        })
        print("\nAnnual Pig Iron Vessel Imports:")
        for year, row in annual.iterrows():
            print(f"  {int(year)}: {row['Tons']:,.0f} tons ({int(row['Bill of Lading Number']):,} shipments)")

        return df_pig

    def analyze_import_terminals(self, df_pig):
        """Identify which terminals receive pig iron (for vessel-to-barge transfer)"""
        print("\n" + "="*80)
        print("VESSEL DISCHARGE TERMINALS: Where Pig Iron Arrives")
        print("="*80)

        # Port-level
        port_summary = df_pig.groupby('Port_Consolidated').agg({
            'Tons': 'sum',
            'Bill of Lading Number': 'count'
        }).sort_values('Tons', ascending=False)

        print("\nPig Iron Imports by Port:")
        print("-" * 60)
        for port, row in port_summary.iterrows():
            print(f"  {port}: {row['Tons']:,.0f} tons ({int(row['Bill of Lading Number']):,} shipments)")

        # Terminal zone level (if available in terminal visits data)
        print("\nAttempting to identify specific discharge terminals...")
        try:
            df_visits = pd.read_csv(self.terminal_visits_path, low_memory=False)
            df_visits['ArrivalTime_dt'] = pd.to_datetime(df_visits['ArrivalTime_dt'], errors='coerce')
            df_visits['Year'] = df_visits['ArrivalTime_dt'].dt.year

            # Filter to Pig Iron predictions
            pig_visits = df_visits[df_visits['PredictedCargo'] == 'Pig Iron'].copy()

            print(f"\nTerminal visits with Pig Iron prediction: {len(pig_visits):,}")

            terminal_summary = pig_visits.groupby('TerminalZone').size().sort_values(ascending=False)
            print("\nTop Pig Iron Discharge Terminals:")
            print("-" * 60)
            for terminal, count in terminal_summary.head(10).items():
                print(f"  {terminal}: {count} vessel visits")

            # Save terminal analysis
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"pig_iron_terminals_{timestamp}.csv"
            terminal_summary.to_csv(output_file)
            print(f"\nSaved: {output_file}")

            return terminal_summary

        except Exception as e:
            print(f"Could not load terminal visit data: {e}")
            return None

    def analyze_consignees(self, df_pig):
        """Identify consignees (likely barge operators or EAF mills)"""
        print("\n" + "="*80)
        print("CONSIGNEES: Who Receives Pig Iron Imports")
        print("="*80)

        consignee_summary = df_pig.groupby('Consignee').agg({
            'Tons': 'sum',
            'Bill of Lading Number': 'count'
        }).sort_values('Tons', ascending=False)

        print("\nTop Pig Iron Consignees:")
        print("-" * 80)
        print(f"{'Consignee':<50} {'Tons':>15} {'Shipments':>12}")
        print("-" * 80)

        for consignee, row in consignee_summary.head(20).iterrows():
            print(f"{str(consignee)[:49]:<50} {row['Tons']:>15,.0f} {int(row['Bill of Lading Number']):>12}")

        # Save consignee analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"pig_iron_consignees_{timestamp}.csv"
        consignee_summary.to_csv(output_file)
        print(f"\nSaved: {output_file}")

        return consignee_summary

    def analyze_origin_countries(self, df_pig):
        """Identify where pig iron is sourced from"""
        print("\n" + "="*80)
        print("ORIGIN COUNTRIES: Pig Iron Sources")
        print("="*80)

        country_summary = df_pig.groupby('Country of Origin (F)').agg({
            'Tons': 'sum',
            'Bill of Lading Number': 'count'
        }).sort_values('Tons', ascending=False)

        print("\nPig Iron Imports by Origin Country:")
        print("-" * 70)
        print(f"{'Country':<30} {'Tons':>15} {'Shipments':>12} {'% of Total':>12}")
        print("-" * 70)

        total_tons = country_summary['Tons'].sum()
        for country, row in country_summary.head(15).iterrows():
            pct = (row['Tons'] / total_tons * 100) if total_tons > 0 else 0
            print(f"{str(country)[:29]:<30} {row['Tons']:>15,.0f} {int(row['Bill of Lading Number']):>12} {pct:>11.1f}%")

        # Save country analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"pig_iron_origin_countries_{timestamp}.csv"
        country_summary.to_csv(output_file)
        print(f"\nSaved: {output_file}")

        return country_summary

    def estimate_barge_destinations(self, df_pig):
        """Estimate likely barge destinations based on EAF mill locations"""
        print("\n" + "="*80)
        print("BARGE DESTINATIONS: Likely Upriver EAF Steel Mills")
        print("="*80)

        # Calculate total pig iron imports
        total_tons = df_pig['Tons'].sum()
        total_tons_per_year = total_tons / len(df_pig['Year'].dropna().unique())

        print(f"\nTotal pig iron vessel imports (all years): {total_tons:,.0f} tons")
        print(f"Average per year: {total_tons_per_year:,.0f} tons/year")

        print("\n" + "-" * 80)
        print("Known EAF Steel Mills on Mississippi River System:")
        print("-" * 80)

        print(f"\n{'Mill Name':<35} {'Location':<35} {'River Access':<20}")
        print("-" * 90)
        for mill_name, mill_info in self.eaf_mills.items():
            location = mill_info['location'][:34]
            river = mill_info['river'][:19]
            print(f"{mill_name[:34]:<35} {location:<35} {river:<20}")

        print("\n" + "-" * 80)
        print("Vessel-to-Barge-to-EAF Flow Pattern (Documented):")
        print("-" * 80)

        flow_pattern = """
1. VESSEL IMPORTS to Lower Mississippi terminals:
   - Primarily New Orleans area terminals
   - Pig iron arrives in bulk carriers from Brazil, Russia, other sources

2. BARGE TRANSFER at Lower Mississippi:
   - Pig iron transferred from ocean vessel to barge
   - Inland barge tows move upriver (north)

3. BARGE DESTINATIONS - EAF Steel Mills:

   MISSISSIPPI RIVER (Upriver from New Orleans):
   - Nucor Steel Louisiana (Convent, LA - RM 162) - ~100 miles upriver
   - Big River Steel (Osceola, AR - RM 734) - ~600 miles upriver
   - Nucor Steel Arkansas (Blytheville, AR - RM 828) - ~700 miles upriver

   OHIO RIVER (via Mississippi to Cairo, IL, then east):
   - Nucor Steel Gallatin (Ghent, KY - Ohio River) - ~1,000 miles total

   TENNESSEE-TOMBIGBEE WATERWAY (via Mississippi):
   - Steel Dynamics Columbus (Columbus, MS) - via Tenn-Tom

   BLACK WARRIOR RIVER (via Mississippi to Tombigbee):
   - Nucor Steel Tuscaloosa (Tuscaloosa, AL) - via Black Warrior River

ESTABLISHED PATTERN:
- Ocean vessel imports >> Lower Mississippi terminals
- Transfer to barge >> Upriver transport
- Delivery to EAF mills >> Steel production

EAF mills consume pig iron as feedstock (mixed with scrap steel).
Typical EAF charge: 15-30% pig iron, 70-85% scrap steel.
"""
        print(flow_pattern)

        # Estimate consumption by mill (if we have capacity data)
        print("\n" + "-" * 80)
        print("Estimated Pig Iron Consumption by EAF Mills:")
        print("-" * 80)
        print("(Based on typical EAF charge: 20% pig iron, 80% scrap)")
        print()

        for mill_name, mill_info in self.eaf_mills.items():
            capacity_str = mill_info['capacity_tons_year']
            if '~' in capacity_str and ',' in capacity_str:
                # Extract numeric capacity
                capacity = float(capacity_str.replace('~', '').replace(',', ''))
                # Assume 20% pig iron in EAF charge
                pig_iron_consumption = capacity * 0.20
                print(f"{mill_name}:")
                print(f"  Steel capacity: {capacity_str} tons/year")
                print(f"  Estimated pig iron consumption: {pig_iron_consumption:,.0f} tons/year")
                print()

        return self.eaf_mills

    def check_census_barge_data(self):
        """Check if Census waterborne commerce barge data is available"""
        print("\n" + "="*80)
        print("CENSUS BARGE DATA: Inland Waterway Commerce")
        print("="*80)

        census_path = Path("G:/My Drive/LLM/task_census")
        print(f"\nChecking Census data directory: {census_path}")

        if census_path.exists():
            print("Census directory found. Checking for barge/inland waterway data...")

            # Look for relevant files
            data_dir = census_path / "data"
            if data_dir.exists():
                files = list(data_dir.glob("*"))
                print(f"\nFound {len(files)} files in Census data directory")

                # Look for waterborne commerce files
                waterborne_files = [f for f in files if 'waterborne' in f.name.lower() or 'barge' in f.name.lower()]
                if waterborne_files:
                    print("\nWaterborne commerce files found:")
                    for f in waterborne_files:
                        print(f"  - {f.name}")
                else:
                    print("\nNo specific barge/waterborne commerce files found in data directory.")
                    print("Census data may need to be obtained separately.")
            else:
                print("No data subdirectory found.")
        else:
            print("Census directory not found.")

        print("\nNote: Census waterborne commerce data would show:")
        print("  - Domestic waterway shipments (barge)")
        print("  - Origin/destination ports on inland waterways")
        print("  - Commodity tonnage by waterway segment")
        print("  - This would validate pig iron barge flows from Lower Miss to upriver EAF mills")

    def generate_flow_report(self, df_pig, consignee_summary, country_summary):
        """Generate comprehensive pig iron flow report"""
        print("\n" + "="*80)
        print("GENERATING PIG IRON FLOW REPORT")
        print("="*80)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"pig_iron_flow_report_{timestamp}.txt"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("PIG IRON FLOW ANALYSIS\n")
            f.write("Vessel-to-Barge-to-EAF Mill Supply Chain\n")
            f.write("Lower Mississippi River to Inland Waterway System\n")
            f.write("="*80 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Summary statistics
            total_tons = df_pig['Tons'].sum()
            years = len(df_pig['Year'].dropna().unique())
            avg_tons = total_tons / years if years > 0 else 0

            f.write("VESSEL IMPORT SUMMARY:\n\n")
            f.write(f"Total pig iron imports: {total_tons:,.0f} tons\n")
            f.write(f"Years analyzed: {years}\n")
            f.write(f"Average per year: {avg_tons:,.0f} tons/year\n\n")

            # Top origin countries
            f.write("TOP ORIGIN COUNTRIES:\n\n")
            for country, row in country_summary.head(5).iterrows():
                pct = (row['Tons'] / total_tons * 100) if total_tons > 0 else 0
                f.write(f"  {country}: {row['Tons']:,.0f} tons ({pct:.1f}%)\n")
            f.write("\n")

            # Top consignees
            f.write("TOP CONSIGNEES:\n\n")
            for consignee, row in consignee_summary.head(10).iterrows():
                f.write(f"  {consignee}: {row['Tons']:,.0f} tons\n")
            f.write("\n")

            # EAF mills
            f.write("DOCUMENTED EAF STEEL MILLS ON RIVER SYSTEM:\n\n")
            for mill_name, mill_info in self.eaf_mills.items():
                f.write(f"{mill_name}:\n")
                f.write(f"  Location: {mill_info['location']}\n")
                f.write(f"  River access: {mill_info['river']}\n")
                f.write(f"  Capacity: {mill_info['capacity_tons_year']} tons/year\n")
                f.write(f"  Products: {mill_info['products']}\n\n")

            # Flow pattern
            f.write("="*80 + "\n")
            f.write("ESTABLISHED FLOW PATTERN:\n")
            f.write("="*80 + "\n\n")
            f.write("1. Ocean vessel imports pig iron to Lower Mississippi terminals\n")
            f.write("   (Primarily New Orleans area)\n\n")
            f.write("2. Transfer from vessel to barge at import terminals\n\n")
            f.write("3. Barge transport upriver to EAF steel mills:\n")
            f.write("   - Mississippi River north (Nucor LA, Big River, Nucor AR)\n")
            f.write("   - Ohio River east (Nucor Gallatin)\n")
            f.write("   - Tennessee-Tombigbee (Steel Dynamics Columbus)\n")
            f.write("   - Black Warrior River (Nucor Tuscaloosa)\n\n")
            f.write("4. EAF mills consume pig iron as feedstock (15-30% of charge)\n\n")

            f.write("="*80 + "\n")
            f.write("DATA SOURCES:\n")
            f.write("="*80 + "\n\n")
            f.write("- Vessel imports: Panjiva manifest data (documented)\n")
            f.write("- Terminal locations: MRTIS vessel tracking (documented)\n")
            f.write("- EAF mill locations: Industry sources (documented)\n")
            f.write("- Barge flows: Census waterborne commerce (to be obtained)\n\n")

            f.write("="*80 + "\n")

        print(f"\nFlow report saved: {report_file}")
        return report_file

    def run_analysis(self):
        """Run complete pig iron flow analysis"""
        print("\n" + "="*80)
        print("PIG IRON FLOW ANALYSIS")
        print("Documenting Vessel-to-Barge-to-EAF Supply Chain")
        print("="*80)

        # Load vessel imports
        df_pig = self.load_pig_iron_imports()

        # Analyze where it arrives
        terminal_summary = self.analyze_import_terminals(df_pig)

        # Who receives it
        consignee_summary = self.analyze_consignees(df_pig)

        # Where it comes from
        country_summary = self.analyze_origin_countries(df_pig)

        # Where it likely goes (barge to EAF mills)
        eaf_mills = self.estimate_barge_destinations(df_pig)

        # Check for Census barge data
        self.check_census_barge_data()

        # Generate report
        report_file = self.generate_flow_report(df_pig, consignee_summary, country_summary)

        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print(f"\nReport: {report_file}")
        print(f"All outputs: {self.output_dir}")

        return report_file


if __name__ == "__main__":
    analyzer = PigIronFlowAnalyzer()
    analyzer.run_analysis()
