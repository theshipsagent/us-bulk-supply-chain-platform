"""
Matplotlib chart generation for Mississippi River dry barge fleet report.
All charts saved as PNG at 150 DPI, 6" wide for DOCX embedding.
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import numpy as np

# Professional color palette
NAVY = '#003366'
COVERED_COLOR = '#1a5276'
OPEN_COLOR = '#c0392b'
ACCENT = '#2e86c1'
GRID_COLOR = '#d5d8dc'
COLORS_TOP5 = ['#1a5276', '#c0392b', '#2e86c1', '#e67e22', '#27ae60']
COLORS_PALETTE = [
    '#1a5276', '#c0392b', '#2e86c1', '#e67e22', '#27ae60',
    '#8e44ad', '#16a085', '#d35400', '#2c3e50', '#7f8c8d',
    '#f39c12', '#1abc9c', '#e74c3c', '#3498db', '#9b59b6',
]

DPI = 150
FIG_WIDTH = 6


def _style_ax(ax, title: str, xlabel: str = '', ylabel: str = ''):
    """Apply consistent styling to axes."""
    ax.set_title(title, fontsize=11, fontweight='bold', color=NAVY, pad=10)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9, color='#333333')
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9, color='#333333')
    ax.tick_params(labelsize=8, colors='#333333')
    ax.grid(axis='y', color=GRID_COLOR, linewidth=0.5)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color(GRID_COLOR)


class BargeCharts:
    """Generates all charts for the barge fleet report."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def fleet_size_trend(self, df: pd.DataFrame) -> Path:
        """Line chart: covered vs open barge counts over 10 years."""
        fig, ax = plt.subplots(figsize=(FIG_WIDTH, 3.5))

        ax.plot(df['year'], df['covered'], color=COVERED_COLOR, marker='o',
                markersize=4, linewidth=2, label='Covered Hopper')
        ax.plot(df['year'], df['open'], color=OPEN_COLOR, marker='s',
                markersize=4, linewidth=2, label='Open Hopper')
        ax.plot(df['year'], df['total'], color=NAVY, marker='D',
                markersize=3, linewidth=1.5, linestyle='--', label='Total', alpha=0.7)

        _style_ax(ax, 'Mississippi River Dry Barge Fleet (2013-2023)',
                  ylabel='Number of Barges')
        ax.legend(fontsize=8, loc='upper left')
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))

        # Annotate missing 2019
        mid_total = (df.loc[df['year'] == 2018, 'total'].values[0] +
                     df.loc[df['year'] == 2020, 'total'].values[0]) / 2
        ax.annotate('No 2019\ndata', xy=(2019, mid_total),
                    xytext=(2019.3, df['total'].min() * 0.92),
                    fontsize=7, color='gray', ha='center',
                    arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))

        plt.tight_layout()
        path = self.output_dir / 'fleet_size_trend.png'
        fig.savefig(path, dpi=DPI, bbox_inches='tight')
        plt.close(fig)
        return path

    def covered_vs_open_area(self, df: pd.DataFrame) -> Path:
        """Stacked area chart: covered vs open composition over time."""
        fig, ax = plt.subplots(figsize=(FIG_WIDTH, 3.5))

        ax.fill_between(df['year'], 0, df['covered'],
                        color=COVERED_COLOR, alpha=0.7, label='Covered Hopper')
        ax.fill_between(df['year'], df['covered'], df['total'],
                        color=OPEN_COLOR, alpha=0.7, label='Open Hopper')

        _style_ax(ax, 'Covered vs Open Hopper Composition (2013-2023)',
                  ylabel='Number of Barges')
        ax.legend(fontsize=8, loc='upper left')
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))

        plt.tight_layout()
        path = self.output_dir / 'covered_vs_open_area.png'
        fig.savefig(path, dpi=DPI, bbox_inches='tight')
        plt.close(fig)
        return path

    def age_distribution(self, df: pd.DataFrame) -> Path:
        """Horizontal bar chart: fleet by 5-year age buckets."""
        fig, ax = plt.subplots(figsize=(FIG_WIDTH, 3.5))

        y_pos = np.arange(len(df))
        bars_covered = ax.barh(y_pos, df['covered'], height=0.4,
                               color=COVERED_COLOR, label='Covered')
        bars_open = ax.barh(y_pos, df['open'], height=0.4,
                            left=df['covered'], color=OPEN_COLOR, label='Open')

        ax.set_yticks(y_pos)
        ax.set_yticklabels(df['age_bucket'].astype(str) + ' yrs')
        ax.invert_yaxis()

        # Value labels on bars
        for i, (c, o) in enumerate(zip(df['covered'], df['open'])):
            total = c + o
            ax.text(total + 50, i, f'{total:,.0f}', va='center', fontsize=7, color='#333333')

        _style_ax(ax, 'Fleet Age Distribution (2023)', xlabel='Number of Barges')
        ax.legend(fontsize=8)
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))

        plt.tight_layout()
        path = self.output_dir / 'age_distribution.png'
        fig.savefig(path, dpi=DPI, bbox_inches='tight')
        plt.close(fig)
        return path

    def build_decade_cohorts(self, df: pd.DataFrame) -> Path:
        """Bar chart: fleet by build decade (1970s onward, older grouped as 'Pre-1970')."""
        fig, ax = plt.subplots(figsize=(FIG_WIDTH, 3.5))

        # Group pre-1970 into single bucket
        old = df[df['decade'] < 1970]
        recent = df[df['decade'] >= 1970].copy()

        labels = []
        covered_vals = []
        open_vals = []

        if not old.empty:
            labels.append('Pre-1970')
            covered_vals.append(old['covered'].sum())
            open_vals.append(old['open'].sum())

        for _, r in recent.iterrows():
            labels.append(f"{int(r['decade'])}s")
            covered_vals.append(r['covered'])
            open_vals.append(r['open'])

        x_pos = np.arange(len(labels))
        width = 0.35

        ax.bar(x_pos - width/2, covered_vals, width, color=COVERED_COLOR, label='Covered')
        ax.bar(x_pos + width/2, open_vals, width, color=OPEN_COLOR, label='Open')

        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, rotation=45, ha='right')

        # Value labels
        for i, (c, o) in enumerate(zip(covered_vals, open_vals)):
            if c > 0:
                ax.text(i - width/2, c + 30, f'{c:,.0f}', ha='center', fontsize=7, color='#333333')
            if o > 0:
                ax.text(i + width/2, o + 30, f'{o:,.0f}', ha='center', fontsize=7, color='#333333')

        _style_ax(ax, 'Fleet by Build Decade (2023 Snapshot)', ylabel='Number of Barges')
        ax.legend(fontsize=8)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))

        plt.tight_layout()
        path = self.output_dir / 'build_decade_cohorts.png'
        fig.savefig(path, dpi=DPI, bbox_inches='tight')
        plt.close(fig)
        return path

    def build_year_timeline(self, df: pd.DataFrame) -> Path:
        """Stacked bar: new builds per year since 2000, annotate Jeffboat closure."""
        fig, ax = plt.subplots(figsize=(FIG_WIDTH, 3.5))

        ax.bar(df['year_built'], df['covered'], color=COVERED_COLOR, label='Covered')
        ax.bar(df['year_built'], df['open'], bottom=df['covered'],
               color=OPEN_COLOR, label='Open')

        # Annotate Jeffboat closure
        if 2018 in df['year_built'].values:
            total_2018 = df.loc[df['year_built'] == 2018, 'builds'].values[0]
            ax.annotate('Jeffboat\nclosed 2018',
                        xy=(2018, total_2018), xytext=(2015, total_2018 * 1.3),
                        fontsize=7, color='red', fontweight='bold',
                        arrowprops=dict(arrowstyle='->', color='red', lw=1))

        _style_ax(ax, 'New Barge Construction by Year', ylabel='Barges Built')
        ax.legend(fontsize=8)
        ax.set_xlim(1999.5, 2023.5)

        plt.tight_layout()
        path = self.output_dir / 'build_year_timeline.png'
        fig.savefig(path, dpi=DPI, bbox_inches='tight')
        plt.close(fig)
        return path

    def top_operators_bar(self, df: pd.DataFrame) -> Path:
        """Horizontal stacked bar: top 15 operators by fleet size."""
        fig, ax = plt.subplots(figsize=(FIG_WIDTH, 5))

        # Reverse for bottom-to-top display (largest at top)
        df_plot = df.iloc[::-1].reset_index(drop=True)

        y_pos = np.arange(len(df_plot))
        # Truncate long operator names
        labels = [n[:30] if isinstance(n, str) and len(n) > 30 else (n or 'Unknown')
                  for n in df_plot['operator']]

        ax.barh(y_pos, df_plot['covered'], height=0.6,
                color=COVERED_COLOR, label='Covered')
        ax.barh(y_pos, df_plot['open'], height=0.6,
                left=df_plot['covered'], color=OPEN_COLOR, label='Open')

        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=7)

        # Value labels
        for i, total in enumerate(df_plot['total']):
            ax.text(total + 30, i, f'{total:,.0f}', va='center', fontsize=7, color='#333333')

        _style_ax(ax, 'Top 15 Operators — Mississippi Dry Barges (2023)',
                  xlabel='Number of Barges')
        ax.legend(fontsize=8, loc='lower right')
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))

        plt.tight_layout()
        path = self.output_dir / 'top_operators.png'
        fig.savefig(path, dpi=DPI, bbox_inches='tight')
        plt.close(fig)
        return path

    def market_share_donut(self, df: pd.DataFrame) -> Path:
        """Donut chart: top 5 operators + Others."""
        fig, ax = plt.subplots(figsize=(FIG_WIDTH, 4))

        top5 = df.head(5).copy()
        others_total = df.iloc[5:]['total'].sum() if len(df) > 5 else 0

        labels = [(n or 'Unknown') for n in top5['operator'].tolist()]
        sizes = top5['total'].tolist()

        if others_total > 0:
            labels.append('Others')
            sizes.append(others_total)

        colors = COLORS_TOP5[:len(labels)]
        if others_total > 0:
            colors = COLORS_TOP5[:5] + ['#bdc3c7']

        wedges, texts, autotexts = ax.pie(
            sizes, labels=None, colors=colors, autopct='%1.1f%%',
            startangle=90, pctdistance=0.78,
            wedgeprops=dict(width=0.4, edgecolor='white', linewidth=1.5)
        )

        for t in autotexts:
            t.set_fontsize(7)
            t.set_color('white')
            t.set_fontweight('bold')

        ax.legend(labels, loc='center left', bbox_to_anchor=(0.85, 0.5),
                  fontsize=7, frameon=False)
        ax.set_title('Market Share — Top 5 Operators (2023)',
                     fontsize=11, fontweight='bold', color=NAVY, pad=10)

        plt.tight_layout()
        path = self.output_dir / 'market_share.png'
        fig.savefig(path, dpi=DPI, bbox_inches='tight')
        plt.close(fig)
        return path

    def capacity_trend(self, df: pd.DataFrame) -> Path:
        """Line chart: total NRT and total cap_tons over time."""
        fig, ax1 = plt.subplots(figsize=(FIG_WIDTH, 3.5))

        color_nrt = COVERED_COLOR
        color_cap = OPEN_COLOR

        ax1.plot(df['year'], df['total_nrt'] / 1e6, color=color_nrt, marker='o',
                 markersize=4, linewidth=2, label='Total NRT (millions)')
        ax1.set_ylabel('Total NRT (millions)', fontsize=9, color=color_nrt)
        ax1.tick_params(axis='y', labelcolor=color_nrt, labelsize=8)

        ax2 = ax1.twinx()
        ax2.plot(df['year'], df['total_cap_tons'] / 1e6, color=color_cap, marker='s',
                 markersize=4, linewidth=2, label='Cargo Capacity (M tons)')
        ax2.set_ylabel('Cargo Capacity (million tons)', fontsize=9, color=color_cap)
        ax2.tick_params(axis='y', labelcolor=color_cap, labelsize=8)

        ax1.set_title('Fleet Capacity Trends (2013-2023)',
                      fontsize=11, fontweight='bold', color=NAVY, pad=10)
        ax1.tick_params(axis='x', labelsize=8)
        ax1.grid(axis='y', color=GRID_COLOR, linewidth=0.5)
        for spine in ax1.spines.values():
            spine.set_color(GRID_COLOR)
        for spine in ax2.spines.values():
            spine.set_color(GRID_COLOR)

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc='upper left')

        plt.tight_layout()
        path = self.output_dir / 'capacity_trend.png'
        fig.savefig(path, dpi=DPI, bbox_inches='tight')
        plt.close(fig)
        return path

    def generate_all(self, query_results: dict) -> dict:
        """Generate all 8 charts. Returns dict of chart_name -> path."""
        paths = {}
        paths['fleet_size_trend'] = self.fleet_size_trend(query_results['fleet_by_year'])
        paths['covered_vs_open_area'] = self.covered_vs_open_area(query_results['fleet_by_year'])
        paths['age_distribution'] = self.age_distribution(query_results['age_distribution'])
        paths['build_decade_cohorts'] = self.build_decade_cohorts(query_results['build_decade_cohorts'])
        paths['build_year_timeline'] = self.build_year_timeline(query_results['new_builds_by_year'])
        paths['top_operators'] = self.top_operators_bar(query_results['top_operators'])
        paths['market_share'] = self.market_share_donut(query_results['top_operators'])
        paths['capacity_trend'] = self.capacity_trend(query_results['capacity_trend'])
        return paths
