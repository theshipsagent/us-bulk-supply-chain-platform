"""
Chemicals Decline Investigation
Lower Mississippi River Import Analysis

Investigates the 91% decline in chemical imports from 2023 to 2025:
- 2023: 5.5M tons
- 2024: 2.7M tons (-50.4%)
- 2025: 0.5M tons (-81.1%)

Analysis Focus:
- Which chemical products declined?
- Which consignees stopped importing?
- Which origin countries were affected?
- Is this gradual or sudden decline?
- Data quality issues?
- Supply chain rerouting?
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class ChemicalsDeclineInvestigator:
    """Investigate the catastrophic chemicals import decline"""

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.manifest_path = self.base_dir / "PIPELINE" / "phase_07_enrichment" / "phase_07_output.csv"
        self.output_dir = self.base_dir / "user_notes" / "chemicals_investigation"
        self.output_dir.mkdir(exist_ok=True)

        # Lower Mississippi ports
        self.lower_miss_ports = [
            'New Orleans', 'Baton Rouge', 'Gramercy', 'Garyville',
            'Chalmette', 'Venice', 'Morgan City', 'Lake Charles'
        ]

        print("Chemicals Decline Investigator initialized")
        print(f"Output directory: {self.output_dir}")

    def load_chemicals_data(self):
        """Load all chemical imports for Lower Mississippi River"""
        print("\n" + "="*80)
        print("LOADING CHEMICALS DATA")
        print("="*80)

        # Load manifest data
        print(f"Loading: {self.manifest_path}")
        df = pd.read_csv(self.manifest_path, low_memory=False)

        # Parse date
        df['Arrival Date'] = pd.to_datetime(df['Arrival Date'], errors='coerce')

        # Filter to Lower Mississippi + Chemicals
        df_chem = df[
            (df['Port_Consolidated'].isin(self.lower_miss_ports)) &
            (df['Commodity'] == 'Chemicals')
        ].copy()

        # Convert tons
        df_chem['Tons'] = pd.to_numeric(df_chem['Tons'], errors='coerce').fillna(0)

        # Add temporal columns
        df_chem['Year'] = df_chem['Arrival Date'].dt.year
        df_chem['Month'] = df_chem['Arrival Date'].dt.month
        df_chem['YearMonth'] = df_chem['Arrival Date'].dt.to_period('M')
        df_chem['MonthName'] = df_chem['Arrival Date'].dt.strftime('%B')

        print(f"\nTotal chemicals records: {len(df_chem):,}")
        print(f"Total tonnage: {df_chem['Tons'].sum():,.0f} tons")
        print(f"Date range: {df_chem['Arrival Date'].min()} to {df_chem['Arrival Date'].max()}")

        # Annual breakdown
        annual = df_chem.groupby('Year').agg({
            'Tons': 'sum',
            'Bill of Lading Number': 'count'
        })
        print("\nAnnual Chemicals Imports:")
        for year, row in annual.iterrows():
            print(f"  {int(year)}: {row['Tons']:,.0f} tons ({int(row['Bill of Lading Number']):,} shipments)")

        return df_chem

    def analyze_monthly_pattern(self, df_chem):
        """Analyze monthly pattern to identify when decline occurred"""
        print("\n" + "="*80)
        print("MONTHLY DECLINE PATTERN")
        print("="*80)

        monthly = df_chem.groupby('YearMonth').agg({
            'Tons': 'sum',
            'Bill of Lading Number': 'count',
            'Consignee': 'nunique',
            'Country of Origin (F)': 'nunique'
        }).reset_index()

        monthly.columns = ['YearMonth', 'Tons', 'Shipments', 'Consignees', 'Countries']
        monthly = monthly.sort_values('YearMonth')

        print("\nMonthly Chemical Imports (2023-2025):")
        print("-" * 100)
        print(f"{'Month':<12} {'Tons':>15} {'Shipments':>12} {'Consignees':>12} {'Countries':>12}")
        print("-" * 100)

        for _, row in monthly.iterrows():
            print(f"{str(row['YearMonth']):<12} {row['Tons']:>15,.0f} {row['Shipments']:>12,.0f} {row['Consignees']:>12} {row['Countries']:>12}")

        # Identify the drop-off point
        print("\n" + "-" * 100)
        print("Identifying Major Decline Points:")
        print("-" * 100)

        for i in range(1, len(monthly)):
            prev_tons = monthly.iloc[i-1]['Tons']
            curr_tons = monthly.iloc[i]['Tons']

            if prev_tons > 0:
                pct_change = (curr_tons - prev_tons) / prev_tons * 100
                if abs(pct_change) > 30:  # Flag >30% monthly changes
                    print(f"\n{monthly.iloc[i]['YearMonth']}:")
                    print(f"  Previous: {prev_tons:,.0f} tons")
                    print(f"  Current: {curr_tons:,.0f} tons")
                    print(f"  Change: {pct_change:+.1f}%")

        # Save monthly data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"monthly_chemicals_trend_{timestamp}.csv"
        monthly.to_csv(output_file, index=False)
        print(f"\nSaved: {output_file}")

        return monthly

    def analyze_cargo_detail(self, df_chem):
        """Analyze which specific chemical products declined"""
        print("\n" + "="*80)
        print("CHEMICAL PRODUCT BREAKDOWN")
        print("="*80)

        # Group by Cargo and Cargo_Detail
        cargo_annual = df_chem.groupby(['Year', 'Cargo', 'Cargo_Detail']).agg({
            'Tons': 'sum',
            'Bill of Lading Number': 'count'
        }).reset_index()

        cargo_annual.columns = ['Year', 'Cargo', 'Cargo_Detail', 'Tons', 'Shipments']

        # Pivot to see year-over-year
        cargo_pivot = cargo_annual.pivot_table(
            index=['Cargo', 'Cargo_Detail'],
            columns='Year',
            values='Tons',
            fill_value=0
        )

        # Calculate change
        if 2023 in cargo_pivot.columns and 2025 in cargo_pivot.columns:
            cargo_pivot['Change_2023_2025'] = cargo_pivot[2025] - cargo_pivot[2023]
            cargo_pivot['Pct_Change'] = (cargo_pivot['Change_2023_2025'] / cargo_pivot[2023] * 100).replace([np.inf, -np.inf], 0)

        # Sort by 2023 tonnage
        if 2023 in cargo_pivot.columns:
            cargo_pivot = cargo_pivot.sort_values(2023, ascending=False)

        print("\nChemical Products by Cargo Type:")
        print("-" * 120)
        print(f"{'Cargo':<30} {'Cargo_Detail':<30} {'2023':>12} {'2024':>12} {'2025':>12} {'Change':>12}")
        print("-" * 120)

        for (cargo, detail), row in cargo_pivot.iterrows():
            tons_2023 = row.get(2023, 0)
            tons_2024 = row.get(2024, 0)
            tons_2025 = row.get(2025, 0)
            change = row.get('Change_2023_2025', 0)

            cargo_str = str(cargo)[:29]
            detail_str = str(detail)[:29]

            print(f"{cargo_str:<30} {detail_str:<30} {tons_2023:>12,.0f} {tons_2024:>12,.0f} {tons_2025:>12,.0f} {change:>12,.0f}")

        # Save cargo detail analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"chemical_products_annual_{timestamp}.csv"
        cargo_pivot.to_csv(output_file)
        print(f"\nSaved: {output_file}")

        return cargo_pivot

    def analyze_consignees(self, df_chem):
        """Identify which consignees stopped importing"""
        print("\n" + "="*80)
        print("CONSIGNEE ANALYSIS - Who Stopped Importing?")
        print("="*80)

        # Group by consignee and year
        consignee_annual = df_chem.groupby(['Year', 'Consignee']).agg({
            'Tons': 'sum',
            'Bill of Lading Number': 'count'
        }).reset_index()

        consignee_annual.columns = ['Year', 'Consignee', 'Tons', 'Shipments']

        # Pivot by year
        consignee_pivot = consignee_annual.pivot_table(
            index='Consignee',
            columns='Year',
            values='Tons',
            fill_value=0
        )

        # Calculate changes
        if 2023 in consignee_pivot.columns and 2025 in consignee_pivot.columns:
            consignee_pivot['Change_2023_2025'] = consignee_pivot[2025] - consignee_pivot[2023]

            # Flag consignees who stopped
            consignee_pivot['Status'] = 'Active'
            consignee_pivot.loc[(consignee_pivot[2023] > 1000) & (consignee_pivot[2025] == 0), 'Status'] = 'STOPPED'
            consignee_pivot.loc[(consignee_pivot[2023] == 0) & (consignee_pivot[2025] > 1000), 'Status'] = 'NEW'
            consignee_pivot.loc[
                (consignee_pivot[2023] > 1000) &
                (consignee_pivot[2025] > 0) &
                (consignee_pivot['Change_2023_2025'] < -1000),
                'Status'
            ] = 'MAJOR_DECLINE'

        # Sort by 2023 tonnage
        if 2023 in consignee_pivot.columns:
            consignee_pivot = consignee_pivot.sort_values(2023, ascending=False)

        # Display top consignees
        print("\nTop Chemical Consignees (sorted by 2023 volume):")
        print("-" * 120)
        print(f"{'Consignee':<40} {'2023':>12} {'2024':>12} {'2025':>12} {'Change':>12} {'Status':<15}")
        print("-" * 120)

        for consignee, row in consignee_pivot.head(30).iterrows():
            tons_2023 = row.get(2023, 0)
            tons_2024 = row.get(2024, 0)
            tons_2025 = row.get(2025, 0)
            change = row.get('Change_2023_2025', 0)
            status = row.get('Status', '')

            consignee_str = str(consignee)[:39]
            print(f"{consignee_str:<40} {tons_2023:>12,.0f} {tons_2024:>12,.0f} {tons_2025:>12,.0f} {change:>12,.0f} {status:<15}")

        # Summary statistics
        print("\n" + "-" * 120)
        print("Consignee Status Summary:")
        print("-" * 120)

        status_counts = consignee_pivot['Status'].value_counts()
        for status, count in status_counts.items():
            total_tons_2023 = consignee_pivot[consignee_pivot['Status'] == status].get(2023, pd.Series([0])).sum()
            print(f"  {status}: {count} consignees ({total_tons_2023:,.0f} tons in 2023)")

        # Save consignee analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"consignee_analysis_{timestamp}.csv"
        consignee_pivot.to_csv(output_file)
        print(f"\nSaved: {output_file}")

        return consignee_pivot

    def analyze_origin_countries(self, df_chem):
        """Identify which origin countries were affected"""
        print("\n" + "="*80)
        print("ORIGIN COUNTRY ANALYSIS")
        print("="*80)

        # Group by country and year
        country_annual = df_chem.groupby(['Year', 'Country of Origin (F)']).agg({
            'Tons': 'sum',
            'Bill of Lading Number': 'count'
        }).reset_index()

        country_annual.columns = ['Year', 'Country', 'Tons', 'Shipments']

        # Pivot by year
        country_pivot = country_annual.pivot_table(
            index='Country',
            columns='Year',
            values='Tons',
            fill_value=0
        )

        # Calculate changes
        if 2023 in country_pivot.columns and 2025 in country_pivot.columns:
            country_pivot['Change_2023_2025'] = country_pivot[2025] - country_pivot[2023]

        # Sort by 2023 tonnage
        if 2023 in country_pivot.columns:
            country_pivot = country_pivot.sort_values(2023, ascending=False)

        print("\nChemical Imports by Origin Country:")
        print("-" * 100)
        print(f"{'Country':<30} {'2023':>12} {'2024':>12} {'2025':>12} {'Change':>12}")
        print("-" * 100)

        for country, row in country_pivot.head(20).iterrows():
            tons_2023 = row.get(2023, 0)
            tons_2024 = row.get(2024, 0)
            tons_2025 = row.get(2025, 0)
            change = row.get('Change_2023_2025', 0)

            country_str = str(country)[:29]
            print(f"{country_str:<30} {tons_2023:>12,.0f} {tons_2024:>12,.0f} {tons_2025:>12,.0f} {change:>12,.0f}")

        # Save country analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"origin_country_analysis_{timestamp}.csv"
        country_pivot.to_csv(output_file)
        print(f"\nSaved: {output_file}")

        return country_pivot

    def analyze_ports(self, df_chem):
        """Check which Lower Mississippi ports were affected"""
        print("\n" + "="*80)
        print("PORT-LEVEL ANALYSIS")
        print("="*80)

        # Group by port and year
        port_annual = df_chem.groupby(['Year', 'Port_Consolidated']).agg({
            'Tons': 'sum',
            'Bill of Lading Number': 'count'
        }).reset_index()

        port_annual.columns = ['Year', 'Port', 'Tons', 'Shipments']

        # Pivot by year
        port_pivot = port_annual.pivot_table(
            index='Port',
            columns='Year',
            values='Tons',
            fill_value=0
        )

        # Calculate changes
        if 2023 in port_pivot.columns and 2025 in port_pivot.columns:
            port_pivot['Change_2023_2025'] = port_pivot[2025] - port_pivot[2023]

        # Sort by 2023 tonnage
        if 2023 in port_pivot.columns:
            port_pivot = port_pivot.sort_values(2023, ascending=False)

        print("\nChemical Imports by Port:")
        print("-" * 100)
        print(f"{'Port':<25} {'2023':>12} {'2024':>12} {'2025':>12} {'Change':>12}")
        print("-" * 100)

        for port, row in port_pivot.iterrows():
            tons_2023 = row.get(2023, 0)
            tons_2024 = row.get(2024, 0)
            tons_2025 = row.get(2025, 0)
            change = row.get('Change_2023_2025', 0)

            port_str = str(port)[:24]
            print(f"{port_str:<25} {tons_2023:>12,.0f} {tons_2024:>12,.0f} {tons_2025:>12,.0f} {change:>12,.0f}")

        # Save port analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"port_analysis_{timestamp}.csv"
        port_pivot.to_csv(output_file)
        print(f"\nSaved: {output_file}")

        return port_pivot

    def analyze_vessel_carriers(self, df_chem):
        """Check if transportation mode changed"""
        print("\n" + "="*80)
        print("VESSEL & CARRIER ANALYSIS")
        print("="*80)

        # Vessel type analysis (if column exists)
        vessel_pivot = None
        if 'VesselType' in df_chem.columns:
            vessel_annual = df_chem.groupby(['Year', 'VesselType']).agg({
                'Tons': 'sum',
                'Bill of Lading Number': 'count'
            }).reset_index()

            vessel_annual.columns = ['Year', 'VesselType', 'Tons', 'Shipments']

            print("\nChemical Imports by Vessel Type:")
            print("-" * 80)

            vessel_pivot = vessel_annual.pivot_table(
                index='VesselType',
                columns='Year',
                values='Tons',
                fill_value=0
            )

            if 2023 in vessel_pivot.columns:
                vessel_pivot = vessel_pivot.sort_values(2023, ascending=False)

            for vessel_type, row in vessel_pivot.iterrows():
                tons_2023 = row.get(2023, 0)
                tons_2024 = row.get(2024, 0)
                tons_2025 = row.get(2025, 0)

                print(f"  {vessel_type}: 2023={tons_2023:,.0f} | 2024={tons_2024:,.0f} | 2025={tons_2025:,.0f}")
        else:
            print("\nVesselType column not found in data")

        # Carrier analysis
        carrier_annual = df_chem.groupby(['Year', 'Carrier']).agg({
            'Tons': 'sum',
            'Bill of Lading Number': 'count'
        }).reset_index()

        carrier_annual.columns = ['Year', 'Carrier', 'Tons', 'Shipments']

        carrier_pivot = carrier_annual.pivot_table(
            index='Carrier',
            columns='Year',
            values='Tons',
            fill_value=0
        )

        if 2023 in carrier_pivot.columns:
            carrier_pivot = carrier_pivot.sort_values(2023, ascending=False)

        print("\nTop Chemical Carriers:")
        print("-" * 80)

        for carrier, row in carrier_pivot.head(10).iterrows():
            tons_2023 = row.get(2023, 0)
            tons_2024 = row.get(2024, 0)
            tons_2025 = row.get(2025, 0)

            carrier_str = str(carrier)[:30]
            print(f"  {carrier_str}: 2023={tons_2023:,.0f} | 2024={tons_2024:,.0f} | 2025={tons_2025:,.0f}")

        # Save vessel/carrier analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if vessel_pivot is not None:
            vessel_file = self.output_dir / f"vessel_type_analysis_{timestamp}.csv"
            vessel_pivot.to_csv(vessel_file)
            print(f"\nSaved vessel analysis: {vessel_file}")

        carrier_file = self.output_dir / f"carrier_analysis_{timestamp}.csv"
        carrier_pivot.to_csv(carrier_file)
        print(f"Saved carrier analysis: {carrier_file}")

        return vessel_pivot, carrier_pivot

    def generate_investigation_report(self, df_chem, monthly, cargo_pivot, consignee_pivot, country_pivot, port_pivot):
        """Generate comprehensive investigation report"""
        print("\n" + "="*80)
        print("GENERATING INVESTIGATION REPORT")
        print("="*80)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"chemicals_decline_investigation_{timestamp}.txt"

        with open(report_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("CHEMICALS DECLINE INVESTIGATION REPORT\n")
            f.write("Lower Mississippi River Import Analysis\n")
            f.write("="*80 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("EXECUTIVE SUMMARY:\n\n")
            f.write("Chemical imports to Lower Mississippi River declined 91% from 2023 to 2025:\n")
            f.write("  - 2023: 5,546,646 tons\n")
            f.write("  - 2024: 2,749,258 tons (-50.4%)\n")
            f.write("  - 2025: 519,268 tons (-81.1% from 2024)\n\n")

            # Top findings
            f.write("KEY FINDINGS:\n\n")

            # 1. Consignees who stopped
            if 'Status' in consignee_pivot.columns and 2023 in consignee_pivot.columns:
                stopped = consignee_pivot[consignee_pivot['Status'] == 'STOPPED']
                f.write(f"1. CONSIGNEES WHO STOPPED IMPORTING:\n")
                f.write(f"   Total: {len(stopped)} companies stopped\n")
                f.write(f"   Lost tonnage: {stopped[2023].sum():,.0f} tons (2023 baseline)\n\n")

                f.write("   Top 10 Stopped Consignees:\n")
                for consignee, row in stopped.head(10).iterrows():
                    f.write(f"     - {consignee}: {row[2023]:,.0f} tons (2023)\n")
                f.write("\n")

            # 2. Product breakdown
            if 2023 in cargo_pivot.columns:
                f.write("2. CHEMICAL PRODUCTS AFFECTED:\n")
                cargo_sorted = cargo_pivot.sort_values(2023, ascending=False)
                for (cargo, detail), row in cargo_sorted.head(10).iterrows():
                    tons_2023 = row.get(2023, 0)
                    tons_2025 = row.get(2025, 0)
                    change = row.get('Change_2023_2025', 0)
                    f.write(f"   - {cargo} / {detail}:\n")
                    f.write(f"     2023: {tons_2023:,.0f} tons -> 2025: {tons_2025:,.0f} tons (Change: {change:+,.0f})\n")
                f.write("\n")

            # 3. Origin countries
            if 2023 in country_pivot.columns:
                f.write("3. ORIGIN COUNTRIES AFFECTED:\n")
                country_sorted = country_pivot.sort_values(2023, ascending=False)
                for country, row in country_sorted.head(10).iterrows():
                    tons_2023 = row.get(2023, 0)
                    tons_2025 = row.get(2025, 0)
                    change = row.get('Change_2023_2025', 0)
                    f.write(f"   - {country}: {tons_2023:,.0f} -> {tons_2025:,.0f} tons ({change:+,.0f})\n")
                f.write("\n")

            # 4. Port impact
            if 2023 in port_pivot.columns:
                f.write("4. PORT-LEVEL IMPACT:\n")
                for port, row in port_pivot.iterrows():
                    tons_2023 = row.get(2023, 0)
                    tons_2025 = row.get(2025, 0)
                    if tons_2023 > 0:
                        pct_change = (tons_2025 - tons_2023) / tons_2023 * 100
                        f.write(f"   - {port}: {tons_2023:,.0f} -> {tons_2025:,.0f} tons ({pct_change:+.1f}%)\n")
                f.write("\n")

            # Monthly pattern
            f.write("5. MONTHLY DECLINE PATTERN:\n")
            f.write("   See monthly_chemicals_trend.csv for detailed timeline\n\n")

            f.write("="*80 + "\n")
            f.write("RECOMMENDATION:\n\n")
            f.write("The 91% decline in chemical imports requires immediate stakeholder investigation.\n")
            f.write("Potential causes to investigate:\n")
            f.write("  1. Major chemical plant closures or operational changes\n")
            f.write("  2. Supply chain rerouting to Houston or other Gulf Coast ports\n")
            f.write("  3. Domestic chemical production substitution\n")
            f.write("  4. Data quality issues (missing 2025 import records)\n")
            f.write("  5. Changes in import classification methodology\n\n")

            f.write("Recommended next steps:\n")
            f.write("  1. Interview major consignees who stopped importing\n")
            f.write("  2. Check Houston/Gulf Coast for corresponding import increases\n")
            f.write("  3. Verify 2025 data completeness with Panjiva/CBP\n")
            f.write("  4. Analyze Louisiana chemical industry production reports\n")
            f.write("  5. Review chemical import tariff/regulatory changes\n\n")

            f.write("="*80 + "\n")
            f.write("All detailed outputs saved to: user_notes/chemicals_investigation/\n")
            f.write("="*80 + "\n")

        print(f"\nInvestigation report saved: {report_file}")
        return report_file

    def run_investigation(self):
        """Run complete chemicals decline investigation"""
        print("\n" + "="*80)
        print("CHEMICALS DECLINE INVESTIGATION")
        print("91% Import Decline Analysis (2023-2025)")
        print("="*80)

        # Load data
        df_chem = self.load_chemicals_data()

        # Run analyses
        monthly = self.analyze_monthly_pattern(df_chem)
        cargo_pivot = self.analyze_cargo_detail(df_chem)
        consignee_pivot = self.analyze_consignees(df_chem)
        country_pivot = self.analyze_origin_countries(df_chem)
        port_pivot = self.analyze_ports(df_chem)
        vessel_pivot, carrier_pivot = self.analyze_vessel_carriers(df_chem)

        # Generate report
        report_file = self.generate_investigation_report(
            df_chem, monthly, cargo_pivot, consignee_pivot, country_pivot, port_pivot
        )

        print("\n" + "="*80)
        print("INVESTIGATION COMPLETE")
        print("="*80)
        print(f"\nReport: {report_file}")
        print(f"All outputs: {self.output_dir}")

        return report_file


if __name__ == "__main__":
    investigator = ChemicalsDeclineInvestigator()
    investigator.run_investigation()
