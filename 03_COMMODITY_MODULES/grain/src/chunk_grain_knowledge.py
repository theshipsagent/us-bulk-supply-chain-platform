"""
Grain Module — Knowledge Base Chunker
======================================
Chunks all source documents (PDFs + Markdown) in the grain knowledge bank
into overlapping text segments for LLM consumption and TF-IDF search.

Sources ingested:
  - PDFs:     ../  (all .pdf files in grain module root)
  - Markdown: ../knowledge_bank/**/*.md (all abstract and reference files)

Output:
  - ../knowledge_bank/processed/chunks/<filename>.json  (one per source)
  - ../knowledge_bank/processed/document_index.json     (master catalog)

Usage:
  python chunk_grain_knowledge.py           # process all sources
  python chunk_grain_knowledge.py --pdfs    # PDFs only
  python chunk_grain_knowledge.py --md      # Markdown only
  python chunk_grain_knowledge.py --force   # reprocess already-chunked files
"""

import json
import re
import sys
import argparse
from pathlib import Path
from typing import Optional

# ── Paths (all relative to this script's location) ──────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
MODULE_ROOT  = SCRIPT_DIR.parent
KB_ROOT      = MODULE_ROOT / "knowledge_bank"
OUTPUT_DIR   = KB_ROOT / "processed" / "chunks"

# ── Chunking configuration ───────────────────────────────────────────────────
CHUNK_SIZE    = 1000   # characters per chunk
CHUNK_OVERLAP = 200    # overlap between consecutive chunks
MIN_CHUNK_LEN = 100    # discard chunks shorter than this


def _try_import_pdf_lib():
    """Pick best available PDF extraction library."""
    for lib, name in [
        ("fitz",       "fitz"),       # pymupdf   — best overall
        ("pdfplumber", "pdfplumber"), # pdfplumber — great for tables (already installed)
        ("pypdfium2",  "pypdfium2"),  # pypdfium2  — also available
        ("PyPDF2",     "pypdf2"),     # PyPDF2     — legacy fallback
    ]:
        try:
            __import__(lib)
            return name
        except ImportError:
            continue
    return None


PDF_LIB = _try_import_pdf_lib()


# ── Text extraction ───────────────────────────────────────────────────────────

def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from a PDF using best available library."""
    if PDF_LIB == "fitz":
        import fitz
        text_parts = []
        try:
            doc = fitz.open(str(pdf_path))
            for page_num, page in enumerate(doc, 1):
                page_text = page.get_text("text")
                if page_text.strip():
                    text_parts.append(f"\n--- Page {page_num} ---\n{page_text}")
            doc.close()
        except Exception as e:
            print(f"  [ERROR] fitz failed on {pdf_path.name}: {e}")
        return "\n".join(text_parts)

    elif PDF_LIB == "pdfplumber":
        import pdfplumber
        text_parts = []
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        text_parts.append(f"\n--- Page {page_num} ---\n{page_text}")
        except Exception as e:
            print(f"  [ERROR] pdfplumber failed on {pdf_path.name}: {e}")
        return "\n".join(text_parts)

    elif PDF_LIB == "pypdfium2":
        import pypdfium2
        text_parts = []
        try:
            doc = pypdfium2.PdfDocument(str(pdf_path))
            for page_num, page in enumerate(doc, 1):
                textpage = page.get_textpage()
                page_text = textpage.get_text_range() or ""
                if page_text.strip():
                    text_parts.append(f"\n--- Page {page_num} ---\n{page_text}")
        except Exception as e:
            print(f"  [ERROR] pypdfium2 failed on {pdf_path.name}: {e}")
        return "\n".join(text_parts)

    elif PDF_LIB == "pypdf2":
        import PyPDF2
        text_parts = []
        try:
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page_num, page in enumerate(reader.pages, 1):
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        text_parts.append(f"\n--- Page {page_num} ---\n{page_text}")
        except Exception as e:
            print(f"  [ERROR] PyPDF2 failed on {pdf_path.name}: {e}")
        return "\n".join(text_parts)

    else:
        print(f"  [SKIP] No PDF library available.")
        print(f"  Install: pip install pymupdf  OR  pip install pdfplumber")
        return ""


def extract_markdown_text(md_path: Path) -> str:
    """Read markdown file as plain text (preserve structure)."""
    try:
        return md_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  [ERROR] Could not read {md_path.name}: {e}")
        return ""


# ── Text cleaning ─────────────────────────────────────────────────────────────

def clean_pdf_text(text: str) -> str:
    """Normalize PDF-extracted text."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'--- Page \d+ ---', ' ', text)
    text = re.sub(r'[^\w\s\.\,\!\?\-\:\;\(\)\[\]\{\}\'\"\/\%\$\#\@\&\*\+\=]', ' ', text)
    return text.strip()


def clean_markdown_text(text: str) -> str:
    """Light cleaning for markdown — preserve headings and structure."""
    # Remove HTML tags if any
    text = re.sub(r'<[^>]+>', ' ', text)
    # Collapse excessive blank lines (keep single blank lines as paragraph breaks)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove markdown link syntax but keep link text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    return text.strip()


# ── Chunking ──────────────────────────────────────────────────────────────────

def chunk_by_paragraphs(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Paragraph-aware chunking for markdown:
    Build chunks by accumulating paragraphs until chunk_size is reached,
    then start a new chunk with overlap from the previous paragraph.
    """
    paragraphs = [p.strip() for p in re.split(r'\n\n+', text) if p.strip()]
    chunks = []
    current_chunk = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)
        if current_len + para_len > chunk_size and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            # Keep last paragraph as overlap seed
            current_chunk = current_chunk[-1:] if current_len > overlap else []
            current_len = len(current_chunk[0]) if current_chunk else 0
        current_chunk.append(para)
        current_len += para_len + 2  # +2 for \n\n

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return [c for c in chunks if len(c) >= MIN_CHUNK_LEN]


def chunk_by_characters(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Character-based chunking with sentence-boundary detection (for PDFs)."""
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size

        if end < text_length:
            # Prefer to end at a sentence boundary
            for punct in ['. ', '.\n', '! ', '?\n', '; ']:
                last_punct = text.rfind(punct, start, end)
                if last_punct != -1:
                    end = last_punct + 1
                    break

        chunk = text[start:end].strip()
        if len(chunk) >= MIN_CHUNK_LEN:
            chunks.append(chunk)

        next_start = end - overlap if (end - overlap) > start else end
        start = next_start

    return chunks


# ── Metadata helpers ──────────────────────────────────────────────────────────

def _infer_category(file_path: Path) -> str:
    """Infer document category from path components."""
    parts = [p.lower() for p in file_path.parts]
    if "pdf_abstracts" in parts:
        return "pdf_abstract"
    if "modal_economics" in parts:
        return "modal_economics"
    if "facility_taxonomy" in parts:
        return "facility_taxonomy"
    if "supply_chain_flows" in parts:
        return "supply_chain_flows"
    if file_path.suffix.lower() == ".pdf":
        return "source_pdf"
    return "reference"


def _infer_doc_title(file_path: Path) -> str:
    """Best-effort human title from filename."""
    stem = file_path.stem
    # Replace underscores/hyphens with spaces
    title = stem.replace("_", " ").replace("-", " ")
    # Title-case it
    return title.title()


# ── Document processing ───────────────────────────────────────────────────────

def process_document(source_path: Path) -> Optional[dict]:
    """Extract, clean, and chunk a single document. Returns doc_data dict."""
    ext = source_path.suffix.lower()
    source_type = "pdf" if ext == ".pdf" else "markdown"

    print(f"  Processing [{source_type}]: {source_path.name}")

    # Extract
    if source_type == "pdf":
        raw_text = extract_pdf_text(source_path)
        cleaned_text = clean_pdf_text(raw_text)
        chunks = chunk_by_characters(cleaned_text, CHUNK_SIZE, CHUNK_OVERLAP)
    else:
        raw_text = extract_markdown_text(source_path)
        cleaned_text = clean_markdown_text(raw_text)
        chunks = chunk_by_paragraphs(cleaned_text, CHUNK_SIZE, CHUNK_OVERLAP)

    if not cleaned_text or not chunks:
        print(f"    [WARNING] No content extracted from {source_path.name}")
        return None

    category = _infer_category(source_path)
    doc_title = _infer_doc_title(source_path)

    doc_data = {
        "source_file": source_path.name,
        "source_path": str(source_path),
        "source_type": source_type,
        "category": category,
        "doc_title": doc_title,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "total_chunks": len(chunks),
        "total_chars": len(cleaned_text),
        "chunks": []
    }

    for i, chunk_text in enumerate(chunks):
        doc_data["chunks"].append({
            "chunk_id": i,
            "text": chunk_text,
            "char_count": len(chunk_text),
            "word_count": len(chunk_text.split()),
            "metadata": {
                "source": source_path.name,
                "source_type": source_type,
                "category": category,
                "doc_title": doc_title,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
        })

    print(f"    → {len(chunks)} chunks ({len(cleaned_text):,} chars)")
    return doc_data


# ── Main pipeline ─────────────────────────────────────────────────────────────

def collect_sources(include_pdfs: bool, include_md: bool) -> list[Path]:
    """Collect all source files to process."""
    sources = []

    if include_pdfs:
        pdf_files = sorted(MODULE_ROOT.glob("*.pdf"))
        print(f"\nPDF sources found: {len(pdf_files)}")
        sources.extend(pdf_files)

    if include_md:
        md_files = sorted(KB_ROOT.rglob("*.md"))
        # Exclude the processed/ directory itself
        md_files = [f for f in md_files if "processed" not in f.parts]
        print(f"Markdown sources found: {len(md_files)}")
        sources.extend(md_files)

    return sources


def main():
    parser = argparse.ArgumentParser(
        description="Chunk grain knowledge base documents for LLM/RAG consumption"
    )
    parser.add_argument("--pdfs", action="store_true", help="Process PDF files only")
    parser.add_argument("--md", action="store_true", help="Process Markdown files only")
    parser.add_argument("--force", action="store_true", help="Reprocess already-chunked files")
    args = parser.parse_args()

    # Default: process both
    include_pdfs = args.pdfs or (not args.pdfs and not args.md)
    include_md   = args.md   or (not args.pdfs and not args.md)

    print("=" * 70)
    print("Grain Knowledge Base — Document Chunker")
    print("=" * 70)
    print(f"Module root:  {MODULE_ROOT}")
    print(f"Output dir:   {OUTPUT_DIR}")
    print(f"Chunk size:   {CHUNK_SIZE} chars  |  Overlap: {CHUNK_OVERLAP} chars")
    print(f"PDF library:  {PDF_LIB or 'NONE — install pymupdf or PyPDF2'}")

    if include_pdfs and PDF_LIB is None:
        print("\n[WARNING] No PDF library found. PDFs will be skipped.")
        print("  Install with:  pip install pymupdf")
        include_pdfs = False

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write gitignore for processed output
    gitignore = OUTPUT_DIR.parent / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("# Chunked documents — large, regenerated by chunk_grain_knowledge.py\n*\n!.gitignore\n")

    sources = collect_sources(include_pdfs, include_md)
    if not sources:
        print("\nNo sources found to process.")
        return

    processed_count = 0
    skipped_count   = 0
    failed_count    = 0
    total_chunks    = 0
    all_docs        = []

    print(f"\nProcessing {len(sources)} source files...\n")

    for source_path in sources:
        # Derive output filename (replace spaces with underscores)
        safe_name = source_path.stem.replace(" ", "_")
        output_file = OUTPUT_DIR / f"{safe_name}_chunks.json"

        if output_file.exists() and not args.force:
            print(f"  [SKIP] {source_path.name} (already chunked; use --force to reprocess)")
            # Still load it for the index
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                all_docs.append({
                    "filename": existing["source_file"],
                    "source_type": existing.get("source_type", "unknown"),
                    "category": existing.get("category", "unknown"),
                    "doc_title": existing.get("doc_title", source_path.stem),
                    "total_chunks": existing["total_chunks"],
                    "total_chars": existing.get("total_chars", 0),
                    "chunk_file": output_file.name,
                })
                total_chunks += existing["total_chunks"]
                skipped_count += 1
            except Exception:
                pass
            continue

        doc_data = process_document(source_path)
        if doc_data:
            # Save chunk file
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(doc_data, f, indent=2, ensure_ascii=False)

            all_docs.append({
                "filename": doc_data["source_file"],
                "source_type": doc_data["source_type"],
                "category": doc_data["category"],
                "doc_title": doc_data["doc_title"],
                "total_chunks": doc_data["total_chunks"],
                "total_chars": doc_data["total_chars"],
                "chunk_file": output_file.name,
            })
            total_chunks  += doc_data["total_chunks"]
            processed_count += 1
        else:
            failed_count += 1

    # Save master document index
    index_data = {
        "module": "grain",
        "total_documents": len(all_docs),
        "total_chunks": total_chunks,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "documents": all_docs,
    }
    index_file = OUTPUT_DIR.parent / "document_index.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("Chunking Complete")
    print(f"  Processed:    {processed_count}")
    print(f"  Skipped:      {skipped_count}  (already done; use --force to redo)")
    print(f"  Failed:       {failed_count}")
    print(f"  Total chunks: {total_chunks:,}")
    if (processed_count + skipped_count) > 0:
        avg = total_chunks / (processed_count + skipped_count)
        print(f"  Avg per doc:  {avg:.0f} chunks")
    print(f"\nIndex file: {index_file}")
    print(f"Chunks dir: {OUTPUT_DIR}")
    print("=" * 70)
    print("\nNext step: python grain_rag.py --build")


if __name__ == "__main__":
    main()
