"""
Report Export Utilities — generate downloadable report artefacts.

* DataFrame → formatted markdown table / CSV bytes
* Plotly figure → PNG bytes (via kaleido or fallback)
* Auto-generated executive summary markdown
"""

import io
import datetime

import pandas as pd

# ---------------------------------------------------------------------------
# DataFrame exports
# ---------------------------------------------------------------------------


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Return CSV-encoded bytes (UTF-8 with BOM for Excel compatibility)."""
    buf = io.BytesIO()
    buf.write(b"\xef\xbb\xbf")  # UTF-8 BOM
    df.to_csv(buf, index=False, encoding="utf-8")
    return buf.getvalue()


def df_to_markdown(df: pd.DataFrame, title: str = "") -> str:
    """Render a DataFrame as a GitHub-flavoured markdown table."""
    lines = []
    if title:
        lines.append(f"### {title}\n")
    lines.append(df.to_markdown(index=False))
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Plotly figure export
# ---------------------------------------------------------------------------


def fig_to_png_bytes(fig, width: int = 1200, height: int = 600) -> bytes | None:
    """Export a Plotly figure to PNG bytes. Returns None if kaleido unavailable."""
    try:
        return fig.to_image(format="png", width=width, height=height, engine="kaleido")
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Executive summary
# ---------------------------------------------------------------------------


def generate_executive_summary(
    total_tonnage: float,
    joined_records: int,
    top_rivers: pd.DataFrame,
    commodity_mix: pd.DataFrame,
    top_corridors: pd.DataFrame,
    lock_overlay: pd.DataFrame,
    cargo_value: pd.DataFrame,
) -> str:
    """Auto-generate an executive summary in markdown.

    Parameters mirror the DataFrames returned by CargoFlowAnalyzer methods.
    """

    date_str = datetime.date.today().strftime("%B %d, %Y")

    sections = []

    # Header
    sections.append(f"# Inland Waterway Cargo Flow Analysis")
    sections.append(f"*Generated {date_str}*\n")

    # Overview
    total_value = cargo_value["estimated_value"].sum() if not cargo_value.empty else 0
    sections.append("## System Overview\n")
    sections.append(f"- **Total system tonnage:** {total_tonnage:,.0f} tons")
    sections.append(f"- **Estimated cargo value:** ${total_value:,.0f}")
    sections.append(f"- **Waterway links analysed:** {joined_records:,}")
    sections.append("")

    # Top rivers
    if not top_rivers.empty:
        sections.append("## Top River Corridors\n")
        sections.append("| Rank | River | Total Tonnage | Links |")
        sections.append("|------|-------|---------------|-------|")
        for i, (_, r) in enumerate(top_rivers.head(10).iterrows(), 1):
            sections.append(
                f"| {i} | {r['RIVERNAME']} | {r['total']:,.0f} | {r['link_count']} |"
            )
        sections.append("")

    # Commodity mix
    if not commodity_mix.empty:
        sections.append("## National Commodity Mix\n")
        sections.append("| Commodity | Tonnage | Share |")
        sections.append("|-----------|---------|-------|")
        for _, c in commodity_mix.iterrows():
            sections.append(
                f"| {c['display_name']} | {c['total_tons']:,.0f} | {c['pct']:.1f}% |"
            )
        sections.append("")

    # Top corridors
    if not top_corridors.empty:
        sections.append("## Highest-Traffic Links\n")
        sections.append("| Link | River | State | Tonnage |")
        sections.append("|------|-------|-------|---------|")
        for _, c in top_corridors.head(10).iterrows():
            sections.append(
                f"| {c['LINKNUM']} | {c['RIVERNAME']} | {c['STATE']} | {c['total']:,.0f} |"
            )
        sections.append("")

    # Bottleneck locks
    if not lock_overlay.empty:
        sections.append("## Most Constrained Locks\n")
        sections.append("| Lock | River | Chamber (ft) | Adj. Tonnage | Score |")
        sections.append("|------|-------|-------------|--------------|-------|")
        for _, lk in lock_overlay.head(10).iterrows():
            dim = f"{int(lk['chamber_length'])}x{int(lk['chamber_width'])}"
            flag = " *" if lk["is_600ft"] else ""
            sections.append(
                f"| {lk['lock_name']} | {lk['river']} | {dim}{flag} | "
                f"{lk['adjacent_tonnage']:,.0f} | {lk['bottleneck_score']:,.1f} |"
            )
        sections.append("\n\\* 600-ft or smaller chamber — requires double lockage for standard 15-barge tow")
        sections.append("")

    # Cargo value
    if not cargo_value.empty:
        sections.append("## Estimated Cargo Value\n")
        sections.append("| Commodity | Tons | $/Ton | Est. Value |")
        sections.append("|-----------|------|-------|------------|")
        for _, v in cargo_value.iterrows():
            sections.append(
                f"| {v['display_name']} | {v['total_tons']:,.0f} | "
                f"${v['value_per_ton']:,.0f} | ${v['estimated_value']:,.0f} |"
            )
        sections.append("")

    sections.append("---")
    sections.append("*Report generated by Cargo Flow Analysis Tool*")

    return "\n".join(sections)
