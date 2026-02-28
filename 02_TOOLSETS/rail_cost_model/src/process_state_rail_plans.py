"""
State Rail Plan PDF Processing Pipeline
Validates, chunks, and indexes state rail plan PDFs for LLM/RAG consumption.

Usage:
    python process_state_rail_plans.py               # Process all valid PDFs
    python process_state_rail_plans.py --validate     # Only validate PDFs (dry run)
"""

import os
import sys
import json
import re
import argparse
import logging
from pathlib import Path
from datetime import datetime
from collections import Counter

import PyPDF2
import duckdb

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent
PDF_DIR = PROJECT_ROOT / "data" / "state_rail_plans"
CHUNKS_DIR = PROJECT_ROOT / "read_rail" / "processed_docs" / "chunks"
LOGS_DIR = PROJECT_ROOT / "logs"
DB_PATH = PROJECT_ROOT / "rail_analytics" / "data" / "rail_analytics.duckdb"

# ── Chunking parameters (larger for policy narrative) ──────────────────────────
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 400

# ── Validation thresholds ──────────────────────────────────────────────────────
MIN_FILE_SIZE = 5_000          # 5 KB
MIN_EXTRACTABLE_CHARS = 500

# ── State name → abbreviation ─────────────────────────────────────────────────
STATE_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE",
    "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
    "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
#  Text processing (reused from process_documents_rail.py)
# ═══════════════════════════════════════════════════════════════════════════════

def clean_text(text: str) -> str:
    """Clean extracted text."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,;:!?()\-\'"]+', '', text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """Split text into overlapping chunks with sentence-boundary snapping."""
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size

        if end < text_length:
            last_period = text.rfind('.', end - 100, end)
            last_question = text.rfind('?', end - 100, end)
            last_exclamation = text.rfind('!', end - 100, end)
            sentence_end = max(last_period, last_question, last_exclamation)
            if sentence_end != -1:
                end = sentence_end + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append({
                'text': chunk,
                'start_pos': start,
                'end_pos': end,
                'length': len(chunk),
            })

        start = end - overlap

    return chunks


def extract_keywords(text: str, top_n: int = 20) -> list[tuple[str, int]]:
    """Extract most common keywords from text."""
    common_words = set([
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
        'that', 'these', 'those', 'it', 'its', 'they', 'their', 'them',
    ])
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    filtered = [w for w in words if w not in common_words]
    return Counter(filtered).most_common(top_n)


# ═══════════════════════════════════════════════════════════════════════════════
#  Metadata resolution
# ═══════════════════════════════════════════════════════════════════════════════

def load_ingestion_map() -> dict[str, dict]:
    """Build filename→{state_name, state_abbr} from ALL ingestion logs + static fallbacks."""

    # Static fallback for filenames not in any ingestion log
    FILENAME_STATE_FALLBACK = {
        # Batch 1
        "Alabama_State_Rail_Plan.pdf":                  ("Alabama", "AL"),
        "2024_California_State_Rail_Plan.pdf":           ("California", "CA"),
        "2024_Colorado_Freight_Passenger_Rail_Plan.pdf": ("Colorado", "CO"),
        "CT_State_Rail_Plan_2022-2026.pdf":              ("Connecticut", "CT"),
        "2023_Florida_Rail_System_Plan_ExecSummary.pdf": ("Florida", "FL"),
        "2021_Georgia_State_Rail_Plan.pdf":              ("Georgia", "GA"),
        "2023_Illinois_State_Rail_Plan.pdf":             ("Illinois", "IL"),
        "2021_Indiana_State_Rail_Plan.pdf":              ("Indiana", "IN"),
        "2022_Iowa_State_Rail_Plan.pdf":                 ("Iowa", "IA"),
        "Maryland_State_Rail_Plan_v2.pdf":               ("Maryland", "MD"),
        "2025_North_Carolina_Rail_Plan_ExecSummary.pdf": ("North Carolina", "NC"),
        "2025_Ohio_Draft_Rail_Plan.pdf":                 ("Ohio", "OH"),
        "2020_Pennsylvania_State_Rail_Plan.pdf":         ("Pennsylvania", "PA"),
        "2019_Washington_State_Rail_Plan.pdf":           ("Washington", "WA"),
        "2023_Wisconsin_Rail_Plan_2050_Draft.pdf":       ("Wisconsin", "WI"),
        # Batch 2
        "MN_State_Rail_Plan_Draft.pdf":                  ("Minnesota", "MN"),
        "2010_Montana_State_Rail_Plan.pdf":              ("Montana", "MT"),
        "AK_State_Rail_Plan.pdf":                        ("Alaska", "AK"),
        "2025_Arkansas_State_Rail_Plan.pdf":              ("Arkansas", "AR"),
        "2022_Arizona_State_Rail_Plan_Update.pdf":       ("Arizona", "AZ"),
        "DE_State_Rail_Plan.pdf":                        ("Delaware", "DE"),
        "ID_Statewide_Rail_Plan.pdf":                    ("Idaho", "ID"),
        "2022_Kansas_State_Rail_Plan.pdf":               ("Kansas", "KS"),
        "2025_Kentucky_Statewide_Rail_Plan.pdf":         ("Kentucky", "KY"),
        "2018_Massachusetts_State_Rail_Plan.pdf":        ("Massachusetts", "MA"),
        "2023_Maine_State_Rail_Plan.pdf":                ("Maine", "ME"),
        "MI_State_Rail_Plan_Supplement.pdf":             ("Michigan", "MI"),
        "2022_Missouri_Freight_Rail_Plan.pdf":           ("Missouri", "MO"),
        "MS_State_Rail_Plan.pdf":                        ("Mississippi", "MS"),
        "2023_North_Dakota_Freight_Rail_Plan.pdf":       ("North Dakota", "ND"),
        "2012_New_Hampshire_State_Rail_Plan.pdf":        ("New Hampshire", "NH"),
        "2012_New_Jersey_State_Rail_Plan.pdf":           ("New Jersey", "NJ"),
        "2018_New_Mexico_State_Rail_Plan_Update.pdf":    ("New Mexico", "NM"),
        "2021_Oklahoma_State_Rail_Plan.pdf":             ("Oklahoma", "OK"),
        "2014_Rhode_Island_State_Rail_Plan.pdf":         ("Rhode Island", "RI"),
        "2024_South_Carolina_Rail_Plan.pdf":             ("South Carolina", "SC"),
        "2022_South_Dakota_State_Rail_Plan.pdf":         ("South Dakota", "SD"),
        "2019_Tennessee_State_Rail_Plan.pdf":            ("Tennessee", "TN"),
        "2015_Utah_State_Rail_Plan.pdf":                 ("Utah", "UT"),
        "2021_Vermont_Rail_Plan.pdf":                    ("Vermont", "VT"),
        "2020_West_Virginia_State_Rail_Plan.pdf":        ("West Virginia", "WV"),
        "2021_Wyoming_State_Rail_Plan.pdf":              ("Wyoming", "WY"),
    }

    mapping = {}

    # Seed from static fallback first
    for filename, (state_name, abbr) in FILENAME_STATE_FALLBACK.items():
        mapping[filename] = {"state_name": state_name, "state_abbr": abbr}

    # Overlay from ALL ingestion logs (newer logs override older)
    for log_file in sorted(LOGS_DIR.glob("ingestion_results_*.json")):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for state_name, info in data.get("details", {}).items():
                fp = info.get("filepath")
                if fp and info.get("success"):
                    filename = Path(fp).name
                    mapping[filename] = {
                        "state_name": state_name,
                        "state_abbr": STATE_ABBR.get(state_name, ""),
                    }
        except Exception:
            continue

    return mapping


def extract_year_from_filename(filename: str) -> int | None:
    """Try to pull a 4-digit year from the filename."""
    match = re.search(r'(20[12]\d)', filename)
    return int(match.group(1)) if match else None


# ═══════════════════════════════════════════════════════════════════════════════
#  PDF validation + extraction
# ═══════════════════════════════════════════════════════════════════════════════

def validate_pdf(pdf_path: Path) -> tuple[bool, str]:
    """Check magic bytes, size, and extractable text.  Returns (is_valid, notes)."""
    # File size check
    size = pdf_path.stat().st_size
    if size < MIN_FILE_SIZE:
        return False, f"Too small ({size:,} bytes)"

    # Magic bytes
    with open(pdf_path, "rb") as f:
        header = f.read(8)
    if not header.startswith(b"%PDF"):
        return False, "Missing %PDF magic bytes (likely HTML error page)"

    # Extractable text
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            sample_text = ""
            for page in reader.pages[:5]:
                sample_text += page.extract_text() or ""
                if len(sample_text) >= MIN_EXTRACTABLE_CHARS:
                    break
        if len(sample_text) < MIN_EXTRACTABLE_CHARS:
            return False, f"Only {len(sample_text)} chars extractable from first 5 pages"
    except Exception as e:
        return False, f"PyPDF2 error: {e}"

    return True, "OK"


def extract_text_with_pages(pdf_path: Path) -> tuple[str, int, list[int]]:
    """Extract text preserving page boundaries.

    Returns (full_text, page_count, page_char_offsets)
    where page_char_offsets[i] is the character offset where page i+1 starts.
    """
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        page_count = len(reader.pages)
        full_text = ""
        page_offsets = []          # char offset of each page start

        for page_num, page in enumerate(reader.pages):
            page_offsets.append(len(full_text))
            try:
                page_text = page.extract_text() or ""
                full_text += f"\n\n--- Page {page_num + 1} ---\n\n{page_text}"
            except Exception as e:
                log.warning("  Page %d extraction error: %s", page_num + 1, e)

    return full_text, page_count, page_offsets


def page_for_offset(offset: int, page_offsets: list[int]) -> int:
    """Return 1-based page number for a given character offset."""
    page = 1
    for i, po in enumerate(page_offsets):
        if offset >= po:
            page = i + 1
        else:
            break
    return page


# ═══════════════════════════════════════════════════════════════════════════════
#  DuckDB helpers
# ═══════════════════════════════════════════════════════════════════════════════

def init_duckdb_tables(con):
    """Create dim + fact tables if they don't exist."""
    con.execute("""
        CREATE TABLE IF NOT EXISTS dim_state_rail_plan (
            plan_id          VARCHAR PRIMARY KEY,
            state_name       VARCHAR NOT NULL,
            state_abbr       VARCHAR(2) NOT NULL,
            plan_year        INTEGER,
            filename         VARCHAR NOT NULL,
            page_count       INTEGER,
            total_chunks     INTEGER,
            total_words      INTEGER,
            file_size_bytes  INTEGER,
            is_valid         BOOLEAN DEFAULT TRUE,
            validation_notes TEXT,
            processed_at     TIMESTAMP,
            top_keywords     VARCHAR
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS fact_rail_plan_chunk (
            chunk_id     INTEGER,
            plan_id      VARCHAR NOT NULL,
            chunk_index  INTEGER NOT NULL,
            text         TEXT NOT NULL,
            text_length  INTEGER,
            page_start   INTEGER,
            page_end     INTEGER,
            state_abbr   VARCHAR(2),
            plan_year    INTEGER
        )
    """)


def upsert_plan_dim(con, row: dict):
    """DELETE + INSERT for idempotent upsert.  Never overwrite a valid entry with an invalid one."""
    existing = con.execute(
        "SELECT is_valid FROM dim_state_rail_plan WHERE plan_id = ?",
        [row["plan_id"]],
    ).fetchone()
    if existing and existing[0] and not row["is_valid"]:
        return  # don't overwrite valid entry with invalid
    con.execute("DELETE FROM dim_state_rail_plan WHERE plan_id = ?", [row["plan_id"]])
    con.execute("""
        INSERT INTO dim_state_rail_plan
        (plan_id, state_name, state_abbr, plan_year, filename,
         page_count, total_chunks, total_words, file_size_bytes,
         is_valid, validation_notes, processed_at, top_keywords)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        row["plan_id"], row["state_name"], row["state_abbr"], row["plan_year"],
        row["filename"], row["page_count"], row["total_chunks"], row["total_words"],
        row["file_size_bytes"], row["is_valid"], row["validation_notes"],
        row["processed_at"], row["top_keywords"],
    ])


def upsert_plan_chunks(con, plan_id: str, chunks: list[dict]):
    """DELETE + INSERT for idempotent chunk upsert."""
    con.execute("DELETE FROM fact_rail_plan_chunk WHERE plan_id = ?", [plan_id])
    for c in chunks:
        con.execute("""
            INSERT INTO fact_rail_plan_chunk
            (chunk_id, plan_id, chunk_index, text, text_length,
             page_start, page_end, state_abbr, plan_year)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            c["chunk_id"], c["plan_id"], c["chunk_index"], c["text"],
            c["text_length"], c["page_start"], c["page_end"],
            c["state_abbr"], c["plan_year"],
        ])


# ═══════════════════════════════════════════════════════════════════════════════
#  Main pipeline
# ═══════════════════════════════════════════════════════════════════════════════

def process_state_rail_plans(validate_only: bool = False):
    if not PDF_DIR.exists():
        log.error("PDF directory not found: %s", PDF_DIR)
        sys.exit(1)

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        log.error("No PDF files found in %s", PDF_DIR)
        sys.exit(1)

    log.info("Found %d PDF files in %s", len(pdf_files), PDF_DIR)

    ingestion_map = load_ingestion_map()
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

    # DuckDB connection (even for validate-only, to record invalid entries)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    init_duckdb_tables(con)

    valid_count = 0
    processed_count = 0
    total_chunks_created = 0

    print()
    print("=" * 80)
    print("  STATE RAIL PLAN PDF PROCESSING")
    print("=" * 80)
    print()

    for pdf_path in pdf_files:
        filename = pdf_path.name
        file_size = pdf_path.stat().st_size

        # ── Resolve metadata ──────────────────────────────────────────────
        meta = ingestion_map.get(filename, {})
        state_name = meta.get("state_name", "")
        state_abbr = meta.get("state_abbr", "")
        plan_year = extract_year_from_filename(filename)
        plan_id = f"{state_abbr}_{plan_year}" if state_abbr and plan_year else \
                  f"{state_abbr}_unknown" if state_abbr else filename.replace(".pdf", "")

        # ── Validate ──────────────────────────────────────────────────────
        is_valid, notes = validate_pdf(pdf_path)
        status = "VALID" if is_valid else "SKIP"
        log.info("%-6s  %-50s  %8s  %s", status, filename[:50],
                 f"{file_size:,}B", f"({state_abbr or '??'}) {notes}")

        if not is_valid:
            # Record invalid entry in DuckDB
            upsert_plan_dim(con, {
                "plan_id": plan_id, "state_name": state_name,
                "state_abbr": state_abbr, "plan_year": plan_year,
                "filename": filename, "page_count": 0, "total_chunks": 0,
                "total_words": 0, "file_size_bytes": file_size,
                "is_valid": False, "validation_notes": notes,
                "processed_at": datetime.now().isoformat(),
                "top_keywords": "",
            })
            continue

        valid_count += 1

        if validate_only:
            continue

        # ── Extract text with page tracking ───────────────────────────────
        full_text, page_count, page_offsets = extract_text_with_pages(pdf_path)
        cleaned = clean_text(full_text)
        word_count = len(cleaned.split())

        if len(cleaned) < MIN_EXTRACTABLE_CHARS:
            log.warning("  Cleaned text too short (%d chars), skipping", len(cleaned))
            continue

        # ── Chunk ─────────────────────────────────────────────────────────
        chunks = chunk_text(cleaned)
        log.info("  → %d chunks from %d pages  (%d words)", len(chunks), page_count, word_count)

        # ── Assign page numbers to each chunk ─────────────────────────────
        chunk_records = []
        for i, c in enumerate(chunks):
            pg_start = page_for_offset(c["start_pos"], page_offsets)
            pg_end = page_for_offset(c["end_pos"], page_offsets)
            chunk_records.append({
                "chunk_id": i,
                "plan_id": plan_id,
                "chunk_index": i,
                "text": c["text"],
                "text_length": c["length"],
                "page_start": pg_start,
                "page_end": pg_end,
                "state_abbr": state_abbr,
                "plan_year": plan_year,
            })

        # ── Save JSON (RAG-compatible) ────────────────────────────────────
        json_filename = f"{state_abbr}_state_rail_plan_chunks.json" if state_abbr \
                        else f"{pdf_path.stem}_chunks.json"
        json_path = CHUNKS_DIR / json_filename

        chunk_data = {
            "source_file": filename,
            "state_name": state_name,
            "state_abbr": state_abbr,
            "plan_year": plan_year,
            "page_count": page_count,
            "total_chunks": len(chunks),
            "chunks": [
                {
                    "chunk_id": i,
                    "text": c["text"],
                    "start_pos": c["start_pos"],
                    "end_pos": c["end_pos"],
                    "length": c["length"],
                    "page_start": chunk_records[i]["page_start"],
                    "page_end": chunk_records[i]["page_end"],
                    "metadata": {
                        "source": filename,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "state_abbr": state_abbr,
                        "plan_year": plan_year,
                    },
                }
                for i, c in enumerate(chunks)
            ],
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(chunk_data, f, indent=2, ensure_ascii=False)

        # ── Keywords ──────────────────────────────────────────────────────
        keywords = extract_keywords(cleaned, top_n=10)
        top_kw_str = ", ".join(f"{w}({n})" for w, n in keywords)

        # ── Save to DuckDB ────────────────────────────────────────────────
        upsert_plan_dim(con, {
            "plan_id": plan_id, "state_name": state_name,
            "state_abbr": state_abbr, "plan_year": plan_year,
            "filename": filename, "page_count": page_count,
            "total_chunks": len(chunks), "total_words": word_count,
            "file_size_bytes": file_size, "is_valid": True,
            "validation_notes": "OK",
            "processed_at": datetime.now().isoformat(),
            "top_keywords": top_kw_str,
        })
        upsert_plan_chunks(con, plan_id, chunk_records)

        processed_count += 1
        total_chunks_created += len(chunks)

    con.close()

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print("=" * 80)
    print(f"  SUMMARY")
    print(f"  Total PDFs scanned:   {len(pdf_files)}")
    print(f"  Valid PDFs:           {valid_count}")
    if not validate_only:
        print(f"  Processed:            {processed_count}")
        print(f"  Total chunks created: {total_chunks_created}")
        print(f"  JSON output:          {CHUNKS_DIR}")
        print(f"  DuckDB tables:        dim_state_rail_plan, fact_rail_plan_chunk")
        print(f"  Database:             {DB_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process state rail plan PDFs for RAG")
    parser.add_argument("--validate", action="store_true",
                        help="Only validate PDFs (no processing)")
    args = parser.parse_args()
    process_state_rail_plans(validate_only=args.validate)
