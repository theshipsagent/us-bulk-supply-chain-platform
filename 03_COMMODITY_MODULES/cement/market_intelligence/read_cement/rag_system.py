import json
import os
from pathlib import Path
import re
from collections import defaultdict
import math

# Paths
CHUNKS_DIR = r"G:\My Drive\LLM\project_cement_markets\read_cement\processed_docs\chunks"
INDEX_FILE = r"G:\My Drive\LLM\project_cement_markets\read_cement\processed_docs\rag_index.json"

class CementRAG:
    def __init__(self):
        self.chunks = []
        self.index = defaultdict(list)  # word -> list of chunk indices
        self.doc_freq = defaultdict(int)  # word -> number of documents containing it
        self.total_docs = 0

    def build_index(self):
        """Load all chunks and build inverted index"""
        print("Building RAG index...")

        chunk_files = list(Path(CHUNKS_DIR).glob("*_chunks.json"))
        self.total_docs = len(chunk_files)

        chunk_id = 0
        for chunk_file in chunk_files:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for chunk in data['chunks']:
                # Add global chunk ID
                chunk['global_id'] = chunk_id
                chunk['source_file'] = data['source_file']
                self.chunks.append(chunk)

                # Extract words for indexing
                words = set(self._tokenize(chunk['text']))

                for word in words:
                    self.index[word].append(chunk_id)

                chunk_id += 1

        # Calculate document frequency
        for word, chunk_ids in self.index.items():
            self.doc_freq[word] = len(set(chunk_ids))

        print(f"Indexed {len(self.chunks)} chunks with {len(self.index)} unique terms")

    def _tokenize(self, text):
        """Simple tokenization"""
        # Convert to lowercase and extract words
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        return words

    def _calculate_tfidf(self, query_words, chunk_id):
        """Calculate TF-IDF score for a chunk given query words"""
        chunk_text = self.chunks[chunk_id]['text'].lower()
        chunk_words = self._tokenize(chunk_text)

        score = 0
        for word in query_words:
            if word not in self.index:
                continue

            # Term frequency in document
            tf = chunk_words.count(word) / len(chunk_words) if chunk_words else 0

            # Inverse document frequency
            df = self.doc_freq[word]
            idf = math.log(self.total_docs / df) if df > 0 else 0

            score += tf * idf

        return score

    def search(self, query, top_k=5):
        """Search for relevant chunks given a query"""
        query_words = self._tokenize(query)

        if not query_words:
            return []

        # Find candidate chunks (chunks containing at least one query word)
        candidate_chunks = set()
        for word in query_words:
            if word in self.index:
                candidate_chunks.update(self.index[word])

        # Calculate TF-IDF scores
        scores = []
        for chunk_id in candidate_chunks:
            score = self._calculate_tfidf(query_words, chunk_id)
            scores.append((chunk_id, score))

        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)

        # Return top-k results
        results = []
        for chunk_id, score in scores[:top_k]:
            chunk = self.chunks[chunk_id]
            results.append({
                'chunk_id': chunk_id,
                'score': score,
                'text': chunk['text'],
                'source': chunk['source_file'],
                'metadata': chunk.get('metadata', {})
            })

        return results

    def get_chunk_context(self, chunk_id, context_size=1):
        """Get surrounding chunks for context"""
        results = []

        # Find chunk
        target_chunk = self.chunks[chunk_id]
        source_file = target_chunk['source_file']

        # Get all chunks from the same document
        doc_chunks = [c for c in self.chunks if c['source_file'] == source_file]

        # Find position in document
        doc_chunk_ids = [c['global_id'] for c in doc_chunks]
        position = doc_chunk_ids.index(chunk_id)

        # Get context
        start = max(0, position - context_size)
        end = min(len(doc_chunks), position + context_size + 1)

        for i in range(start, end):
            results.append({
                'chunk_id': doc_chunks[i]['global_id'],
                'text': doc_chunks[i]['text'],
                'is_target': (i == position)
            })

        return results

    def save_index(self):
        """Save index to file"""
        index_data = {
            'total_chunks': len(self.chunks),
            'total_terms': len(self.index),
            'doc_freq': dict(self.doc_freq),
            'index': {k: v for k, v in self.index.items()}
        }

        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2)

        print(f"Index saved to {INDEX_FILE}")

def interactive_search():
    """Interactive search interface"""
    rag = CementRAG()
    rag.build_index()
    rag.save_index()

    print("\n" + "="*80)
    print("CEMENT DOCUMENTS RAG SYSTEM")
    print("="*80)
    print("\nCommands:")
    print("  - Enter a query to search")
    print("  - 'context <chunk_id>' to see context around a chunk")
    print("  - 'quit' to exit")
    print()

    while True:
        query = input("\nQuery: ").strip()

        if query.lower() == 'quit':
            break

        if query.lower().startswith('context '):
            try:
                chunk_id = int(query.split()[1])
                context = rag.get_chunk_context(chunk_id, context_size=2)

                print(f"\n{'='*80}")
                print(f"Context for chunk {chunk_id}")
                print(f"{'='*80}\n")

                for item in context:
                    marker = " >>> TARGET <<<" if item['is_target'] else ""
                    print(f"Chunk {item['chunk_id']}{marker}")
                    print(f"{item['text'][:300]}...")
                    print()

            except (ValueError, IndexError):
                print("Invalid chunk ID")
            continue

        # Search
        results = rag.search(query, top_k=5)

        if not results:
            print("No results found.")
            continue

        print(f"\n{'='*80}")
        print(f"Found {len(results)} results:")
        print(f"{'='*80}\n")

        for i, result in enumerate(results, 1):
            print(f"{i}. [Score: {result['score']:.4f}] from {result['source']}")
            print(f"   Chunk ID: {result['chunk_id']}")
            print(f"   {result['text'][:300]}...")
            print()

def batch_query():
    """Test queries"""
    rag = CementRAG()
    rag.build_index()

    test_queries = [
        "cement production process",
        "environmental impact of cement",
        "cement market in Egypt",
        "cement plant operations",
        "clinker manufacturing",
        "cement terminal handling"
    ]

    output_file = os.path.join(os.path.dirname(INDEX_FILE), "test_queries.txt")

    with open(output_file, 'w', encoding='utf-8') as f:
        for query in test_queries:
            results = rag.search(query, top_k=3)

            f.write(f"\n{'='*80}\n")
            f.write(f"Query: {query}\n")
            f.write(f"{'='*80}\n\n")

            for i, result in enumerate(results, 1):
                f.write(f"{i}. [Score: {result['score']:.4f}] from {result['source']}\n")
                f.write(f"   {result['text'][:200]}...\n\n")

    print(f"Test queries saved to {output_file}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        batch_query()
    else:
        interactive_search()
