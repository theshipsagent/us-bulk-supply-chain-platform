"""
Grain Module — RAG Search System
==================================
TF-IDF retrieval over the grain knowledge base chunks.
Covers all PDFs and Markdown abstracts in the grain module.

Usage:
  # Build / rebuild the search index:
  python grain_rag.py --build

  # One-shot query (prints top results):
  python grain_rag.py "barge rates Gulf corn export"

  # Interactive session:
  python grain_rag.py

  # Filter by category:
  python grain_rag.py "shuttle train economics" --category modal_economics

  # Importable API:
  from grain_rag import GrainRAG
  rag = GrainRAG()
  results = rag.search("PNW wheat export facilities", top_k=5)

Categories available:
  pdf_abstract       - Markdown abstracts of research PDFs (knowledge_bank/pdf_abstracts/)
  modal_economics    - Transport benchmarks (knowledge_bank/modal_economics/)
  facility_taxonomy  - Elevator types and NAICS (knowledge_bank/facility_taxonomy/)
  supply_chain_flows - Supply chain structure docs
  source_pdf         - Raw text extracted directly from the source PDFs
  reference          - Other reference markdown files
"""

import json
import re
import math
import argparse
import sys
from pathlib import Path
from collections import defaultdict
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).resolve().parent
MODULE_ROOT = SCRIPT_DIR.parent
CHUNKS_DIR  = MODULE_ROOT / "knowledge_bank" / "processed" / "chunks"
INDEX_FILE  = MODULE_ROOT / "knowledge_bank" / "processed" / "rag_index.json"

# ── Stopwords (common words that don't help retrieval) ────────────────────────
STOPWORDS = {
    "the", "and", "for", "are", "was", "were", "has", "have", "had",
    "that", "this", "with", "from", "not", "but", "also", "its",
    "more", "than", "such", "which", "when", "they", "their", "been",
    "each", "into", "can", "may", "will", "all", "per", "one", "two",
    "use", "used", "using", "total", "data", "year", "table", "figure",
    "source", "page", "report", "note", "see", "includes", "including",
}


class GrainRAG:
    """
    TF-IDF retrieval system over the grain knowledge base.

    Build the index once with .build_index(), then call .search() as needed.
    The index is persisted to disk and auto-loaded if it exists.
    """

    def __init__(self, auto_build: bool = True):
        self.chunks:     list[dict] = []
        self.index:      defaultdict = defaultdict(list)  # term → [chunk_global_ids]
        self.doc_freq:   defaultdict = defaultdict(int)   # term → # docs containing it
        self.total_docs: int = 0
        self._built = False

        if auto_build:
            if INDEX_FILE.exists():
                self._load_index()
            elif CHUNKS_DIR.exists():
                self.build_index()
            else:
                print("[GrainRAG] Chunks not found. Run chunk_grain_knowledge.py first.")

    # ── Index building ────────────────────────────────────────────────────────

    def build_index(self, save: bool = True) -> None:
        """Load all chunk files and build an in-memory TF-IDF inverted index."""
        chunk_files = sorted(CHUNKS_DIR.glob("*_chunks.json"))
        if not chunk_files:
            print(f"[ERROR] No chunk files found in {CHUNKS_DIR}")
            print("  Run:  python chunk_grain_knowledge.py")
            return

        print(f"Building index from {len(chunk_files)} chunk files...")

        self.chunks    = []
        self.index     = defaultdict(list)
        self.doc_freq  = defaultdict(int)
        self.total_docs = 0  # set after all chunks loaded (= total chunks, not files)

        global_id = 0

        for chunk_file in chunk_files:
            try:
                with open(chunk_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"  [WARNING] Could not load {chunk_file.name}: {e}")
                continue

            for chunk in data.get("chunks", []):
                chunk["global_id"]   = global_id
                chunk["source_file"] = data["source_file"]
                chunk["source_type"] = data.get("source_type", "unknown")
                chunk["category"]    = data.get("category", "unknown")
                chunk["doc_title"]   = data.get("doc_title", data["source_file"])
                self.chunks.append(chunk)

                # Build index
                words = set(self._tokenize(chunk["text"]))
                for word in words:
                    self.index[word].append(global_id)

                global_id += 1

        # Document frequency (count of chunks containing each term)
        for word, ids in self.index.items():
            self.doc_freq[word] = len(set(ids))

        # Use total chunks as N for IDF — keeps scores positive for reasonably rare terms
        self.total_docs = len(self.chunks)

        self._built = True
        n_files = len(chunk_files)
        print(f"  Indexed {len(self.chunks):,} chunks  |  {len(self.index):,} unique terms")
        print(f"  Source files: {n_files}")

        if save:
            self._save_index()

    def _save_index(self) -> None:
        INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
        index_data = {
            "total_chunks":  len(self.chunks),
            "total_terms":   len(self.index),
            "total_docs":    self.total_docs,
            "chunks":        self.chunks,
            "doc_freq":      dict(self.doc_freq),
            "index":         {k: v for k, v in self.index.items()},
        }
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False)
        size_mb = INDEX_FILE.stat().st_size / 1_048_576
        print(f"  Index saved → {INDEX_FILE.name}  ({size_mb:.1f} MB)")

    def _load_index(self) -> None:
        print(f"Loading index from {INDEX_FILE.name}...")
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.chunks     = data["chunks"]
            self.doc_freq   = defaultdict(int, data["doc_freq"])
            self.index      = defaultdict(list, data["index"])
            self.total_docs = data.get("total_docs", len(self.chunks))
            self._built = True
            print(f"  Loaded {len(self.chunks):,} chunks  |  {len(self.index):,} terms")
        except Exception as e:
            print(f"  [ERROR] Could not load index: {e}. Rebuilding...")
            self.build_index()

    # ── Tokenization & scoring ────────────────────────────────────────────────

    def _tokenize(self, text: str) -> list[str]:
        """Lowercase, extract words ≥3 chars, remove stopwords."""
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        return [w for w in words if w not in STOPWORDS]

    def _tfidf_score(self, query_words: list[str], chunk_id: int) -> float:
        """TF-IDF relevance score for a chunk given query terms."""
        chunk_text  = self.chunks[chunk_id]["text"].lower()
        chunk_words = self._tokenize(chunk_text)
        if not chunk_words:
            return 0.0

        score = 0.0
        for word in query_words:
            tf = chunk_words.count(word) / len(chunk_words)
            df = self.doc_freq.get(word, 0)
            if df > 0:
                idf = math.log((self.total_docs + 1) / df)
                score += tf * idf

        return score

    # ── Search ────────────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        source_type: Optional[str] = None,
    ) -> list[dict]:
        """
        Search for relevant chunks.

        Args:
            query:       Natural language query
            top_k:       Number of results to return
            category:    Filter by category (pdf_abstract, modal_economics, etc.)
            source_type: Filter by 'pdf' or 'markdown'

        Returns:
            List of result dicts with keys: rank, score, text, source, category,
            source_type, doc_title, chunk_id
        """
        if not self._built:
            print("[GrainRAG] Index not built. Run .build_index() first.")
            return []

        query_words = self._tokenize(query)
        if not query_words:
            return []

        # Candidate chunks (contain at least one query word)
        candidates: set[int] = set()
        for word in query_words:
            if word in self.index:
                candidates.update(self.index[word])

        if not candidates:
            return []

        # Apply filters
        if category:
            candidates = {
                cid for cid in candidates
                if self.chunks[cid].get("category") == category
            }
        if source_type:
            candidates = {
                cid for cid in candidates
                if self.chunks[cid].get("source_type") == source_type
            }

        # Score and rank
        scores = [
            (cid, self._tfidf_score(query_words, cid))
            for cid in candidates
        ]
        scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for rank, (cid, score) in enumerate(scores[:top_k], 1):
            c = self.chunks[cid]
            results.append({
                "rank":        rank,
                "score":       round(score, 5),
                "text":        c["text"],
                "source":      c["source_file"],
                "source_type": c.get("source_type", "unknown"),
                "category":    c.get("category", "unknown"),
                "doc_title":   c.get("doc_title", c["source_file"]),
                "chunk_id":    cid,
            })

        return results

    # ── Context retrieval ─────────────────────────────────────────────────────

    def get_context(self, chunk_id: int, window: int = 2) -> list[dict]:
        """Return surrounding chunks from the same document for context."""
        if chunk_id >= len(self.chunks):
            return []

        target = self.chunks[chunk_id]
        source_file = target["source_file"]
        doc_chunks = [
            (i, c) for i, c in enumerate(self.chunks)
            if c["source_file"] == source_file
        ]

        pos = next((i for i, (gid, _) in enumerate(doc_chunks) if gid == chunk_id), None)
        if pos is None:
            return []

        results = []
        for i in range(max(0, pos - window), min(len(doc_chunks), pos + window + 1)):
            gid, c = doc_chunks[i]
            results.append({
                "chunk_id":  gid,
                "text":      c["text"],
                "is_target": (gid == chunk_id),
            })

        return results

    # ── Document catalog ──────────────────────────────────────────────────────

    def list_documents(self) -> list[dict]:
        """Return a deduplicated list of all indexed documents."""
        seen = {}
        for c in self.chunks:
            sf = c["source_file"]
            if sf not in seen:
                seen[sf] = {
                    "source_file": sf,
                    "source_type": c.get("source_type", "unknown"),
                    "category":    c.get("category", "unknown"),
                    "doc_title":   c.get("doc_title", sf),
                    "chunk_count": 0,
                }
            seen[sf]["chunk_count"] += 1
        return list(seen.values())

    def list_categories(self) -> dict[str, int]:
        """Return chunk counts by category."""
        counts: dict[str, int] = defaultdict(int)
        for c in self.chunks:
            counts[c.get("category", "unknown")] += 1
        return dict(sorted(counts.items()))


# ── CLI ───────────────────────────────────────────────────────────────────────

def _print_result(r: dict, preview_len: int = 400) -> None:
    print(f"\n  [{r['rank']}] Score: {r['score']:.5f}  |  Chunk #{r['chunk_id']}")
    print(f"      Source:   {r['source']}  [{r['source_type']}]")
    print(f"      Category: {r['category']}  |  {r['doc_title']}")
    snippet = r['text'][:preview_len].replace('\n', ' ')
    if len(r['text']) > preview_len:
        snippet += "..."
    print(f"      Text:     {snippet}")


def interactive_mode(rag: GrainRAG) -> None:
    """Full interactive search session."""
    print("\n" + "=" * 70)
    print("GRAIN KNOWLEDGE BASE — RAG SEARCH")
    print("=" * 70)
    print(f"\n  {len(rag.chunks):,} chunks indexed across {len(rag.list_documents())} documents")
    print("\nCommands:")
    print("  <query>                      — keyword/phrase search (top 5)")
    print("  <query> /k:<N>               — return N results  (e.g. /k:10)")
    print("  <query> /cat:<category>      — filter by category")
    print("  <query> /pdf                 — search source PDFs only")
    print("  <query> /md                  — search markdown abstracts only")
    print("  context <chunk_id>           — show surrounding chunks")
    print("  docs                         — list all indexed documents")
    print("  cats                         — show category breakdown")
    print("  quit                         — exit")
    print()

    while True:
        try:
            raw = input("Query: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not raw:
            continue
        if raw.lower() in ("quit", "exit", "q"):
            break

        # --- docs / cats ---
        if raw.lower() == "docs":
            docs = rag.list_documents()
            print(f"\n  {len(docs)} documents indexed:\n")
            for d in sorted(docs, key=lambda x: (x["category"], x["source_file"])):
                print(f"  [{d['category']:20s}]  {d['chunk_count']:3d} chunks  |  {d['source_file']}")
            continue

        if raw.lower() == "cats":
            cats = rag.list_categories()
            print("\n  Category breakdown:")
            for cat, count in cats.items():
                print(f"    {cat:25s}  {count:4d} chunks")
            continue

        # --- context <id> ---
        if raw.lower().startswith("context "):
            try:
                cid = int(raw.split()[1])
                ctx = rag.get_context(cid, window=2)
                if not ctx:
                    print("  Chunk not found.")
                    continue
                print(f"\n  Context around chunk #{cid}:\n")
                for item in ctx:
                    marker = " ← TARGET" if item["is_target"] else ""
                    print(f"  Chunk #{item['chunk_id']}{marker}")
                    print(f"  {item['text'][:300]}\n")
            except (ValueError, IndexError):
                print("  Usage: context <chunk_id>")
            continue

        # --- parse flags ---
        top_k       = 5
        category    = None
        source_type = None
        query_text  = raw

        # /k:N
        k_match = re.search(r'\s*/k:(\d+)', raw)
        if k_match:
            top_k = int(k_match.group(1))
            query_text = query_text.replace(k_match.group(0), "").strip()

        # /cat:name
        cat_match = re.search(r'\s*/cat:(\S+)', raw)
        if cat_match:
            category = cat_match.group(1)
            query_text = query_text.replace(cat_match.group(0), "").strip()

        # /pdf or /md
        if "/pdf" in raw:
            source_type = "pdf"
            query_text  = query_text.replace("/pdf", "").strip()
        elif "/md" in raw:
            source_type = "markdown"
            query_text  = query_text.replace("/md", "").strip()

        results = rag.search(query_text, top_k=top_k, category=category, source_type=source_type)

        if not results:
            print("  No results found.")
        else:
            filter_desc = ""
            if category:
                filter_desc += f"  category={category}"
            if source_type:
                filter_desc += f"  type={source_type}"
            print(f"\n  {len(results)} results for: \"{query_text}\"{filter_desc}")
            for r in results:
                _print_result(r)
            print()


def one_shot_query(rag: GrainRAG, query: str, top_k: int = 5, category: Optional[str] = None) -> None:
    """Single query, print results, exit."""
    results = rag.search(query, top_k=top_k, category=category)
    if not results:
        print(f"No results for: \"{query}\"")
        return
    print(f"\n{len(results)} results for: \"{query}\"\n")
    for r in results:
        _print_result(r)
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Grain Knowledge Base — RAG Search System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("query",     nargs="?", default=None, help="One-shot query text")
    parser.add_argument("--build",   action="store_true",     help="(Re)build the search index from chunks")
    parser.add_argument("--k",       type=int, default=5,     help="Number of results to return")
    parser.add_argument("--category", default=None,           help="Filter by category (e.g. modal_economics)")
    parser.add_argument("--list",    action="store_true",     help="List all indexed documents and exit")
    args = parser.parse_args()

    # Build mode
    if args.build:
        print("Building grain RAG index...")
        rag = GrainRAG(auto_build=False)
        if not CHUNKS_DIR.exists() or not any(CHUNKS_DIR.glob("*_chunks.json")):
            print("[ERROR] No chunk files found.")
            print("  Run first:  python chunk_grain_knowledge.py")
            sys.exit(1)
        rag.build_index(save=True)
        print("\nIndex built. Ready for search: python grain_rag.py")
        return

    # Load index
    if not INDEX_FILE.exists() and not CHUNKS_DIR.exists():
        print("[ERROR] Knowledge base not yet built.")
        print("  Step 1: python chunk_grain_knowledge.py")
        print("  Step 2: python grain_rag.py --build")
        sys.exit(1)

    rag = GrainRAG(auto_build=True)

    if not rag._built:
        print("[ERROR] Could not load or build index. Check chunk files.")
        sys.exit(1)

    # --list
    if args.list:
        docs = rag.list_documents()
        print(f"\n{len(docs)} documents indexed:\n")
        for d in sorted(docs, key=lambda x: (x["category"], x["source_file"])):
            print(f"  [{d['category']:22s}]  {d['chunk_count']:3d} chunks  {d['source_file']}")
        print()
        return

    # One-shot query
    if args.query:
        one_shot_query(rag, args.query, top_k=args.k, category=args.category)
        return

    # Interactive
    interactive_mode(rag)


if __name__ == "__main__":
    main()
