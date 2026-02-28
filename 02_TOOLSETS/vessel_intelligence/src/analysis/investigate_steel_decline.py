"""
Steel Decline Investigation
Lower Mississippi River Import Analysis

Investigates the 68% decline in steel imports from 2023 to 2025:
- 2023: 4.5M tons
- 2024: 2.1M tons (-54%)
- 2025: 1.5M tons (-30%)

Analysis Focus:
- Which steel products declined?
- Which consignees stopped importing?
- Which origin countries were affected?
- Is this gradual or sudden decline?
- Single-company or broad market trend?
- Tariff/trade policy impacts?
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class SteelDeclineInvestigator:
    """Investigate the 68% steel import decline"""

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.manifest_path = self.base_dir / "PIPELINE" / "phase_07_enrichment" / "phase_07_output.csv"
        self.output_dir = self.base_dir / "user_notes" / "steel_investigation"
        self.output_dir.mkdir(exist_ok=True)

        # Lower Mississippi ports
        self.lower_miss_ports = [
            'New Orleans', 'Baton Rouge', 'Gramercy', 'Garyville',
            'Chalmette', 'Venice', 'Morgan City', 'Lake Charles'
        ]

        print("Steel Decline Investigator initialized")
        print(f"Output directory: {self.output_dir}")

    def load_steel_data(self):
        """Load all steel imports for Lower Mississippi River"""
        print("\n" + "="*80)
        print("LOADING STEEL DATA")
        print("="*80)

        # Load manifest data
        print(f"Loading: {self.manifest_path}")
        df = pd.read_csv(self.manifest_path, low_memory=False)

        # Parse date
        df['Arrival Date'] = pd.to_datetime(df['Arrival Date'], errors='coerce')

        # Filter to Lower Mississippi + Steel
        df_steel = df[
            (df['Port_Consolidated'].isin(self.lower_miss_ports)) &
            (df['Commodity'] == 'Steel')
        ].copy()

        # Convert tons
        df_steel['Tons'] = pd.to_numeric(df_steel['Tons'], errors='coerce').fillna(0)

        # Add temporal columns
        df_steel['Year'] = df_steel['Arrival Date'].dt.year
        df_steel['Month'] = df_steel['Arrival Date'].dt.month
        df_steel['YearMonth'] = df_steel['Arrival Date'].dt.to_period('M')
        df_steel['MonthName'] = df_steel['Arrival Date'].dt.strftime('%B')

        print(f"\nTotal steel records: {len(df_steel):,}")
        print(f"Total tonnage: {df_steel['Tons'].sum():,.0f} tons")
        print(f"Date range: {df_steel['Arrival Date'].min()} to {df_steel['Arrival Date'].max()}")

        # Annual breakdown
        annual = df_steel.groupby('Year').agg({
            'Tons': 'sum',
            'Bill of Lading Number': 'count'
        })
        print("\nAnnual Steel Imports:")
        for year, row in annual.iterrows():
            print(f"  {int(year)}: {row['Tons']:,.0f} tons ({int(row['Bill of Lading Number']):,} shipments)")

        return df_steel

    def analyze_monthly_pattern(self, df_steel):
        """Analyze monthly pattern to identify when decline occurred"""
        print("\n" + "="*80)
        print("MONTHLY DECLINE PATTERN")
        print("="*80)

        monthly = df_steel.groupby('YearMonth').agg({
            'Tons': 'sum',
            'Bill of Lading Number': 'count',
            'Consignee': 'nunique',
            'Country of Origin (F)': 'nunique'
        }).reset_index()

        monthly.columns = ['YearMonth', 'Tons', 'Shipments', 'Consignees', 'Countries']
        monthly = monthly.sort_values('YearMonth')

        print("\nMonthly Steel Imports (2023-2025):")
        print("-" * 100)
        print(f"{'Month':<12} {'Tons':>15} {'Shipments':>12} {'Consignees':>12} {'Countries':>12}")
        print("-" * 100)

        for _, row in monthly.iterrows():
            print(f"{str(row['YearMonth']):<12} {row['Tons']:>15,.0f} {row['Shipments']:>12,.0f} {row['Consignees']:>12} {row['Countries']:>12}")

        # Identify major decline points
        print("\n" + "-" * 100)
        print("Identifying Major Decline Points:")
        print("-" * 100)

        for i in range(1, len(monthly)):
            prev_tons = monthly.iloc[i-1]['Tons']
            curr_tons = monthly.iloc[i]['Tons']

            if prev_tons > 10000:  # Only flag if previous month was significant
                pct_change = (curr_tons - prev_tons) / prev_tons * 100
                if abs(pct_change) > 40:  # Flag >40% monthly changes
                    print(f"\n{monthly.iloc[i]['YearMonth']}:")
                    print(f"  Previous: {prev_tons:,.0f} tons")
                    print(f"  Current: {curr_tons:,.0f} tons")
                    print(f"  Change: {pct_change:+.1f}%")

        # Save monthly data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"monthly_steel_trend_{timestamp}.csv"
        monthly.to_csv(output_file, index=False)
        print(f"\nSaved: {output_file}")

        return monthly

    def analyze_steel_products(self, df_steel):
        """Analyze which specific steel products declined"""
        print("\n" + "="*80)
        print("STEEL PRODUCT BREAKDOWN")
        print("="*80)

        # Group by Cargo and Cargo Detail
        cargo_annual = df_steel.groupby(['Year', 'Cargo', 'Cargo_Detail']).agg({
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

        print("\nSteel Products by Type:")
        print("-" * 120)
        print(f"{'Cargo':<30} {'Cargo Detail':<30} {'2023':>12} {'2024':>12} {'2025':>12} {'Change':>12}")
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
        output_file = self.output_dir / f"steel_products_annual_{timestamp}.csv"
        cargo_pivot.to_csv(output_file)
        print(f"\nSaved: {output_file}")

        return cargo_pivot

    def analyze_consignees(self, df_steel):
        """Identify which consignees stopped importing"""
        print("\n" + "="*80)
        print("CONSIGNEE ANALYSIS - Who Stopped Importing?")
        print("="*80)

        # Group by consignee and year
        consignee_annual = df_steel.groupby(['Year', 'Consignee']).agg({
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

            # Flag consignees who stopped or declined significantly
            consignee_pivot['Status'] = 'Active'
            consignee_pivot.loc[(consignee_pivot[2023] > 5000) & (consignee_pivot[2025] == 0), 'Status'] = 'STOPPED'
            consignee_pivot.loc[(consignee_pivot[2023] == 0) & (consignee_pivot[2025] > 5000), 'Status'] = 'NEW'
            consignee_pivot.loc[
                (consignee_pivot[2023] > 5000) &
                (consignee_pivot[2025] > 0) &
                (consignee_pivot['Change_2023_2025'] < -5000),
                'Status'
            ] = 'MAJOR_DECLINE'

        # Sort by 2023 tonnage
        if 2023 in consignee_pivot.columns:
            consignee_pivot = consignee_pivot.sort_values(2023, ascending=False)

        # Display top consignees
        print("\nTop Steel Consignees (sorted by 2023 volume):")
        print("-" * 120)
        print(f"{'Consignee':<40} {'2023':>12} {'2024':>12} {'2025':>12} {'Change':>12} {'Status':<15}")
        print("-" * 120)

        for consignee, row in consignee_pivot.head(40).iterrows():
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

        if 'Status' in consignee_pivot.columns:
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

    def analyze_origin_countries(self, df_steel):
        """Identify which origin countries were affected"""
        print("\n" + "="*80)
        print("ORIGIN COUNTRY ANALYSIS")
        print("="*80)

        # Group by country and year
        country_annual = df_steel.groupby(['Year', 'Country of Origin (F)']).agg({
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
            country_pivot['Pct_Change'] = (country_pivot['Change_2023_2025'] / country_pivot[2023] * 100).replace([np.inf, -np.inf], 0)

        # Sort by 2023 tonnage
        if 2023 in country_pivot.columns:
            country_pivot = country_pivot.sort_values(2023, ascending=False)

        print("\nSteel Imports by Origin Country:")
        print("-" * 110)
        print(f"{'Country':<30} {'2023':>12} {'2024':>12} {'2025':>12} {'Change':>12} {'% Change':>12}")
        print("-" * 110)

        for country, row in country_pivot.head(20).iterrows():
            tons_2023 = row.get(2023, 0)
            tons_2024 = row.get(2024, 0)
            tons_2025 = row.get(2025, 0)
            change = row.get('Change_2023_2025', 0)
            pct_change = row.get('Pct_Change', 0)

            country_str = str(country)[:29]
            print(f"{country_str:<30} {tons_2023:>12,.0f} {tons_2024:>12,.0f} {tons_2025:>12,.0f} {change:>12,.0f} {pct_change:>11,.1f}%")

        # Save country analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"origin_country_analysis_{timestamp}.csv"
        country_pivot.to_csv(output_file)
        print(f"\nSaved: {output_file}")

        return country_pivot

    def analyze_ports(self, df_steel):
        """Check which Lower Mississippi ports were affected"""
        print("\n" + "="*80)
        print("PORT-LEVEL ANALYSIS")
        print("="*80)

        # Group by port and year
        port_annual = df_steel.groupby(['Year', 'Port_Consolidated']).agg({
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
            port_pivot['Pct_Change'] = (port_pivot['Change_2023_2025'] / port_pivot[2023] * 100).replace([np.inf, -np.inf], 0)

        # Sort by 2023 tonnage
        if 2023 in port_pivot.columns:
            port_pivot = port_pivot.sort_values(2023, ascending=False)

        print("\nSteel Imports by Port:")
        print("-" * 110)
        print(f"{'Port':<25} {'2023':>12} {'2024':>12} {'2025':>12} {'Change':>12} {'% Change':>12}")
        print("-" * 110)

        for port, row in port_pivot.iterrows():
            tons_2023 = row.get(2023, 0)
            tons_2024 = row.get(2024, 0)
            tons_2025 = row.get(2025, 0)
            change = row.get('Change_2023_2025', 0)
            pct_change = row.get('Pct_Change', 0)

            port_str = str(port)[:24]
            print(f"{port_str:<25} {tons_2023:>12,.0f} {tons_2024:>12,.0f} {tons_2025:>12,.0f} {change:>12,.0f} {pct_change:>11,.1f}%")

        # Save port analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"port_analysis_{timestamp}.csv"
        port_pivot.to_csv(output_file)
        print(f"\nSaved: {output_file}")

        return port_pivot

    def analyze_tariffs_timeline(self, df_steel):
        """Analyze if decline correlates with steel tariff events"""
        print("\n" + "="*80)
        print("TARIFF/TRADE POLICY TIMELINE ANALYSIS")
        print("="*80)

        print("\nSteel Tariff Events Timeline:")
        print("-" * 80)
        print("  2018: Section 232 steel tariffs (25%) imposed")
        print("  2020-2022: Some exemptions granted for select countries")
        print("  2023: Potential tariff adjustments or enforcement changes")
        print("  2024-2025: Trade policy evolution")
        print()

        # Compare China vs other countries (China typically has highest tariffs)
        china_annual = df_steel[df_steel['Country of Origin (F)'] == 'China'].groupby('Year')['Tons'].sum()
        non_china_annual = df_steel[df_steel['Country of Origin (F)'] != 'China'].groupby('Year')['Tons'].sum()

        print("China vs Non-China Imports:")
        print("-" * 80)
        for year in sorted(df_steel['Year'].dropna().unique()):
            china_tons = china_annual.get(year, 0)
            non_china_tons = non_china_annual.get(year, 0)
            total_tons = china_tons + non_china_tons
            china_pct = (china_tons / total_tons * 100) if total_tons > 0 else 0

            print(f"  {int(year)}: China={china_tons:>10,.0f} tons ({china_pct:>5.1f}%) | Non-China={non_china_tons:>10,.0f} tons")

        return china_annual, non_china_annual

    def generate_investigation_report(self, df_steel, monthly, cargo_pivot, consignee_pivot, country_pivot, port_pivot):
        """Generate comprehensive investigation report"""
        print("\n" + "="*80)
        print("GENERATING INVESTIGATION REPORT")
        print("="*80)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"steel_decline_investigation_{timestamp}.txt"

        with open(report_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("STEEL DECLINE INVESTIGATION REPORT\n")
            f.write("Lower Mississippi River Import Analysis\n")
            f.write("="*80 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("EXECUTIVE SUMMARY:\n\n")
            f.write("Steel imports to Lower Mississippi River declined 68% from 2023 to 2025:\n")
            f.write("  - 2023: 4,496,980 tons\n")
            f.write("  - 2024: 2,071,134 tons (-54%)\n")
            f.write("  - 2025: 1,450,019 tons (-30% from 2024)\n\n")

            # Top findings
            f.write("KEY FINDINGS:\n\n")

            # 1. Consignees analysis
            if 'Status' in consignee_pivot.columns and 2023 in consignee_pivot.columns:
                stopped = consignee_pivot[consignee_pivot['Status'] == 'STOPPED']
                major_decline = consignee_pivot[consignee_pivot['Status'] == 'MAJOR_DECLINE']

                f.write(f"1. CONSIGNEE PATTERNS:\n")
                f.write(f"   Stopped: {len(stopped)} companies ({stopped[2023].sum():,.0f} tons in 2023)\n")
                f.write(f"   Major Decline: {len(major_decline)} companies ({major_decline[2023].sum():,.0f} tons in 2023)\n\n")

                if len(stopped) > 0:
                    f.write("   Top Stopped Consignees:\n")
                    for consignee, row in stopped.head(10).iterrows():
                        f.write(f"     - {consignee}: {row[2023]:,.0f} tons (2023)\n")
                    f.write("\n")

            # 2. Product breakdown
            if 2023 in cargo_pivot.columns:
                f.write("2. STEEL PRODUCTS AFFECTED:\n")
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
                    pct = row.get('Pct_Change', 0)
                    f.write(f"   - {country}: {tons_2023:,.0f} -> {tons_2025:,.0f} tons ({change:+,.0f}, {pct:+.1f}%)\n")
                f.write("\n")

            # 4. Port impact
            if 2023 in port_pivot.columns:
                f.write("4. PORT-LEVEL IMPACT:\n")
                for port, row in port_pivot.iterrows():
                    tons_2023 = row.get(2023, 0)
                    tons_2025 = row.get(2025, 0)
                    pct = row.get('Pct_Change', 0)
                    if tons_2023 > 0:
                        f.write(f"   - {port}: {tons_2023:,.0f} -> {tons_2025:,.0f} tons ({pct:+.1f}%)\n")
                f.write("\n")

            f.write("="*80 + "\n")
            f.write("ANALYSIS:\n\n")
            f.write("The steel decline pattern differs from chemicals (Celanese case):\n")
            f.write("  - Not dominated by single company (more distributed)\n")
            f.write("  - Multiple countries affected (not single origin)\n")
            f.write("  - Gradual decline over 3 years (not sudden stop)\n")
            f.write("  - Likely influenced by:\n")
            f.write("    * Steel tariffs (Section 232)\n")
            f.write("    * Domestic steel production increases\n")
            f.write("    * Trade policy changes\n")
            f.write("    * Economic demand shifts\n\n")

            f.write("="*80 + "\n")
            f.write("RECOMMENDATIONS:\n\n")
            f.write("1. Compare domestic US steel production 2023-2025\n")
            f.write("2. Analyze tariff impact by country (China, Brazil, etc.)\n")
            f.write("3. Interview steel consignees about supply chain changes\n")
            f.write("4. Check if steel imports shifted to other US ports\n")
            f.write("5. Review Louisiana steel demand (construction, manufacturing)\n\n")

            f.write("="*80 + "\n")
            f.write("All detailed outputs saved to: user_notes/steel_investigation/\n")
            f.write("="*80 + "\n")

        print(f"\nInvestigation report saved: {report_file}")
        return report_file

    def run_investigation(self):
        """Run complete steel decline investigation"""
        print("\n" + "="*80)
        print("STEEL DECLINE INVESTIGATION")
        print("68% Import Decline Analysis (2023-2025)")
        print("="*80)

        # Load data
        df_steel = self.load_steel_data()

        # Run analyses
        monthly = self.analyze_monthly_pattern(df_steel)
        cargo_pivot = self.analyze_steel_products(df_steel)
        consignee_pivot = self.analyze_consignees(df_steel)
        country_pivot = self.analyze_origin_countries(df_steel)
        port_pivot = self.analyze_ports(df_steel)
        china_annual, non_china_annual = self.analyze_tariffs_timeline(df_steel)

        # Generate report
        report_file = self.generate_investigation_report(
            df_steel, monthly, cargo_pivot, consignee_pivot, country_pivot, port_pivot
        )

        print("\n" + "="*80)
        print("INVESTIGATION COMPLETE")
        print("="*80)
        print(f"\nReport: {report_file}")
        print(f"All outputs: {self.output_dir}")

        return report_file


if __name__ == "__main__":
    investigator = SteelDeclineInvestigator()
    investigator.run_investigation()
