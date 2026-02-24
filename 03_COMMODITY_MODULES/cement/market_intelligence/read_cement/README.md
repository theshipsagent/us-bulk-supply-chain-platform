# Cement Documents RAG System

## Overview
This system processes Zotero library documents about cement and creates a searchable RAG (Retrieval-Augmented Generation) database.

## What's Been Created

### 1. Document Extraction (`zotero_extractor.py`)
- Extracts documents from Zotero "My Library / Cargo / Cement" collection
- Copies 19 PDFs with 39 files total to `cement_docs/`
- Creates manifest of all extracted documents

### 2. Document Processing (`process_documents.py`)
- Processes all 19 PDF documents
- **Total Output**: 5,394 text chunks
- Extracts text from 2,449 pages total
- Performs keyword analysis for each document
- Saves processed chunks to `processed_docs/chunks/`

### 3. RAG System (`rag_system.py`)
- Builds searchable index with 27,321 unique terms
- Implements TF-IDF based search
- Provides interactive query interface
- Supports context retrieval around relevant chunks

## Statistics

| Metric | Value |
|--------|-------|
| Total Documents | 19 PDFs |
| Total Pages | 2,449 pages |
| Total Chunks | 5,394 chunks |
| Unique Terms | 27,321 words |
| Chunk Size | ~1,000 characters |
| Overlap | 200 characters |

## Key Documents Processed

1. **The Cement Plant Operations Handbook** (287 pages, 1,041 chunks)
2. **Cement Production Technology** (440 pages, 1,228 chunks)
3. **Environmental Manager Handbook** (321 pages, 807 chunks)
4. **Formula Handbook for Cement Industry** (184 pages, 449 chunks)
5. **Egypt Cement Sector Reports** (multiple documents)
6. **Pakistan Cement Industry Studies**
7. **CEMEX Market Analysis**
8. And 12 more specialized documents...

## Usage

### Interactive Search
```bash
python rag_system.py
```

Then enter queries like:
- "cement production process"
- "environmental impact"
- "cement market in Egypt"
- "clinker manufacturing"

### Programmatic Access
```python
from rag_system import CementRAG

rag = CementRAG()
rag.build_index()

# Search
results = rag.search("cement plant operations", top_k=5)

# Get context around a chunk
context = rag.get_chunk_context(chunk_id=100, context_size=2)
```

### Batch Queries
```bash
python rag_system.py test
```

## File Structure

```
read_cement/
├── cement_docs/              # Original PDFs from Zotero
│   ├── *.pdf                 # 19 PDF documents
│   └── manifest.txt          # Document listing
├── processed_docs/
│   ├── chunks/               # JSON files with text chunks
│   │   └── *_chunks.json     # One file per document
│   ├── analytics/
│   │   ├── document_analytics.json
│   │   └── summary_report.txt
│   ├── rag_index.json        # Searchable index
│   └── test_queries.txt      # Sample query results
├── zotero_extractor.py       # Extraction script
├── process_documents.py      # Processing script
└── rag_system.py            # RAG query system
```

## Integration with LLM Applications

### For RAG Pipeline
1. Use `rag_system.search(query)` to retrieve relevant chunks
2. Pass top-k results as context to LLM
3. Use `get_chunk_context()` for expanded context

### For Embeddings
Chunk data is in `processed_docs/chunks/*.json` format:
```json
{
  "chunk_id": 0,
  "text": "...",
  "source": "filename.pdf",
  "metadata": {...}
}
```

You can generate embeddings using OpenAI, Cohere, or other providers.

## Next Steps

1. **Add Embeddings**: Generate vector embeddings for semantic search
2. **Add Vector Database**: Integrate with ChromaDB, Pinecone, or FAISS
3. **Enhance Chunking**: Implement semantic chunking strategies
4. **Add Metadata**: Extract more metadata (dates, authors, citations)
5. **Build API**: Create REST API for querying the RAG system

## Requirements

```
PyPDF2
```

Install with:
```bash
pip install PyPDF2
```
