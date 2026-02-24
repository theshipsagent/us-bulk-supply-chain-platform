import os
import json
from pathlib import Path
import re
from collections import Counter
import PyPDF2

# Paths
DOCS_DIR = r"G:\My Drive\LLM\project_cement_markets\read_cement\cement_docs"
OUTPUT_DIR = r"G:\My Drive\LLM\project_cement_markets\read_cement\processed_docs"
CHUNKS_DIR = os.path.join(OUTPUT_DIR, "chunks")
ANALYTICS_DIR = os.path.join(OUTPUT_DIR, "analytics")

# Chunking parameters
CHUNK_SIZE = 1000  # characters
CHUNK_OVERLAP = 200  # characters

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    text += f"\n\n--- Page {page_num + 1} ---\n\n{page_text}"
                except Exception as e:
                    print(f"Error extracting page {page_num + 1} from {pdf_path}: {e}")
            return text, len(pdf_reader.pages)
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return "", 0

def clean_text(text):
    """Clean extracted text"""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,;:!?()\-\'"]+', '', text)
    return text.strip()

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size

        # Try to end at a sentence boundary
        if end < text_length:
            # Look for sentence endings within the last 100 characters
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
                'length': len(chunk)
            })

        start = end - overlap

    return chunks

def extract_keywords(text, top_n=20):
    """Extract most common keywords from text"""
    # Simple keyword extraction - remove common words
    common_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                        'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
                        'that', 'these', 'those', 'it', 'its', 'they', 'their', 'them'])

    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    filtered_words = [w for w in words if w not in common_words]

    word_counts = Counter(filtered_words)
    return word_counts.most_common(top_n)

def process_documents():
    """Process all PDFs in the documents directory"""
    os.makedirs(CHUNKS_DIR, exist_ok=True)
    os.makedirs(ANALYTICS_DIR, exist_ok=True)

    pdf_files = [f for f in os.listdir(DOCS_DIR) if f.endswith('.pdf')]
    print(f"Found {len(pdf_files)} PDF files to process")

    all_analytics = []
    total_chunks = 0

    for pdf_file in pdf_files:
        print(f"\nProcessing: {pdf_file}")
        pdf_path = os.path.join(DOCS_DIR, pdf_file)

        # Extract text
        text, page_count = extract_text_from_pdf(pdf_path)

        if not text:
            print(f"  No text extracted from {pdf_file}")
            continue

        # Clean text
        cleaned_text = clean_text(text)

        # Create chunks
        chunks = chunk_text(cleaned_text)
        print(f"  Created {len(chunks)} chunks from {page_count} pages")

        # Extract keywords
        keywords = extract_keywords(cleaned_text)

        # Save chunks
        base_name = os.path.splitext(pdf_file)[0]
        chunk_file = os.path.join(CHUNKS_DIR, f"{base_name}_chunks.json")

        chunk_data = {
            'source_file': pdf_file,
            'page_count': page_count,
            'total_chunks': len(chunks),
            'chunks': []
        }

        for i, chunk in enumerate(chunks):
            chunk_data['chunks'].append({
                'chunk_id': i,
                'text': chunk['text'],
                'start_pos': chunk['start_pos'],
                'end_pos': chunk['end_pos'],
                'length': chunk['length'],
                'metadata': {
                    'source': pdf_file,
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                }
            })

        with open(chunk_file, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, indent=2, ensure_ascii=False)

        total_chunks += len(chunks)

        # Analytics
        analytics = {
            'file': pdf_file,
            'page_count': page_count,
            'character_count': len(cleaned_text),
            'word_count': len(cleaned_text.split()),
            'chunk_count': len(chunks),
            'avg_chunk_size': sum(c['length'] for c in chunks) // len(chunks) if chunks else 0,
            'top_keywords': keywords[:10]
        }
        all_analytics.append(analytics)

    # Save overall analytics
    analytics_file = os.path.join(ANALYTICS_DIR, "document_analytics.json")
    with open(analytics_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_documents': len(pdf_files),
            'total_chunks': total_chunks,
            'documents': all_analytics
        }, f, indent=2, ensure_ascii=False)

    # Create summary report
    summary_file = os.path.join(ANALYTICS_DIR, "summary_report.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("CEMENT DOCUMENTS PROCESSING SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total Documents Processed: {len(pdf_files)}\n")
        f.write(f"Total Chunks Created: {total_chunks}\n\n")

        f.write("DOCUMENT DETAILS:\n")
        f.write("-" * 80 + "\n")

        for doc in all_analytics:
            f.write(f"\n{doc['file']}\n")
            f.write(f"  Pages: {doc['page_count']}\n")
            f.write(f"  Words: {doc['word_count']:,}\n")
            f.write(f"  Chunks: {doc['chunk_count']}\n")
            f.write(f"  Top Keywords: {', '.join([kw[0] for kw in doc['top_keywords'][:5]])}\n")

    print(f"\n{'=' * 80}")
    print(f"Processing complete!")
    print(f"Total documents: {len(pdf_files)}")
    print(f"Total chunks: {total_chunks}")
    print(f"Chunks saved to: {CHUNKS_DIR}")
    print(f"Analytics saved to: {ANALYTICS_DIR}")

if __name__ == "__main__":
    process_documents()
