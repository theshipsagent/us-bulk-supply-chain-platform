"""
Generic fixed-width text file parser for Census trade data products.

All Census bulk data products use fixed-width ASCII text format.
This parser uses record layout definitions from config/record_layouts.py
to convert raw text files into pandas DataFrames.
"""

from pathlib import Path

import pandas as pd

from ..config.record_layouts import get_layout, get_record_length, FILE_LAYOUTS


def parse_fixed_width(text: str, layout: list) -> pd.DataFrame:
    """Parse fixed-width text into a DataFrame using a layout definition.

    Args:
        text: Raw text content (full file or subset of lines).
        layout: List of (field_name, start_pos, length, data_type) tuples.

    Returns:
        DataFrame with one column per field.
    """
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        row = {}
        for field_name, start, length, dtype in layout:
            raw = line[start:start + length]
            if dtype == "int":
                raw = raw.strip()
                row[field_name] = int(raw) if raw and raw.lstrip("-").isdigit() else 0
            else:
                row[field_name] = raw.strip()
        rows.append(row)

    df = pd.DataFrame(rows)
    return df


def parse_file(filepath: str | Path, layout: list = None) -> pd.DataFrame:
    """Parse a fixed-width Census data file into a DataFrame.

    Args:
        filepath: Path to the .TXT file.
        layout: Record layout. If None, auto-detected from filename.

    Returns:
        DataFrame with parsed data.
    """
    filepath = Path(filepath)

    if layout is None:
        layout = get_layout(filepath.stem)

    # Census files can be large; read with encoding fallback
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            text = filepath.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise UnicodeDecodeError(f"Could not decode {filepath} with any known encoding")

    return parse_fixed_width(text, layout)


def parse_directory(directory: str | Path, file_filter: list[str] = None) -> dict[str, pd.DataFrame]:
    """Parse all recognized .TXT files in a directory.

    Args:
        directory: Path to extracted ZIP directory.
        file_filter: Optional list of file stems to parse (e.g. ['EXP_DETL', 'CONCORD']).
                     If None, parses all recognized files.

    Returns:
        Dict mapping file stem to DataFrame.
    """
    directory = Path(directory)
    results = {}

    for txt_file in sorted(directory.glob("*.TXT")) + sorted(directory.glob("*.txt")):
        stem = txt_file.stem.upper()

        # Check if we have a layout for this file
        layout_key = None
        for key in FILE_LAYOUTS:
            if stem.startswith(key):
                layout_key = key
                break

        if layout_key is None:
            continue

        if file_filter and layout_key not in [f.upper() for f in file_filter]:
            continue

        try:
            results[layout_key] = parse_file(txt_file)
        except Exception as e:
            print(f"  [warn] Failed to parse {txt_file.name}: {e}")

    return results
