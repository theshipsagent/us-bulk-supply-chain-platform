"""
Phase 2: RAG-based topic extraction from chunks per state.
Queries the TF-IDF RAG system with targeted keywords for each of 10 topic areas.
"""

import logging
import sys
from pathlib import Path

# Add project root to path so we can import RailRAG
sys.path.insert(0, str(Path(__file__).parent.parent))

from .config import STATES_46, TOPICS, RAG_TOP_K, CHUNKS_PER_TOPIC

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
log = logging.getLogger(__name__)


def _state_chunk_source_pattern(state_abbr):
    """Return the expected source filename pattern for a state's chunk file."""
    return f"{state_abbr}_state_rail_plan"


def extract_topics(rag, state_abbr, state_name):
    """
    Extract structured topic information for a single state from the RAG.

    Returns dict: {topic_key: [list of relevant text excerpts]}
    """
    results = {}
    seen_chunk_ids = set()  # dedup across topics

    source_pattern = _state_chunk_source_pattern(state_abbr).lower()
    state_lower = state_name.lower()

    for topic_key, topic_info in TOPICS.items():
        topic_chunks = []

        for query_template in topic_info["queries"]:
            query = query_template.format(state=state_name)
            hits = rag.search(query, top_k=RAG_TOP_K)

            for hit in hits:
                cid = hit["chunk_id"]
                if cid in seen_chunk_ids:
                    continue

                source = (hit.get("source") or "").lower()
                text_lower = hit["text"].lower()

                # Keep if: from this state's plan file, OR mentions this state
                is_state_source = source_pattern in source
                mentions_state = state_lower in text_lower or state_abbr.lower() in text_lower

                if is_state_source or mentions_state:
                    topic_chunks.append({
                        "chunk_id": cid,
                        "score": hit["score"],
                        "text": hit["text"],
                        "source": hit.get("source", ""),
                        "is_state_source": is_state_source,
                    })
                    seen_chunk_ids.add(cid)

        # Sort by score (prefer state-source chunks via bonus), keep top N
        for tc in topic_chunks:
            if tc["is_state_source"]:
                tc["_sort_score"] = tc["score"] * 1.5
            else:
                tc["_sort_score"] = tc["score"]

        topic_chunks.sort(key=lambda x: x["_sort_score"], reverse=True)
        results[topic_key] = topic_chunks[:CHUNKS_PER_TOPIC]

    return results


def extract_all_states(rag):
    """
    Extract topics for all 46 states.
    Returns dict: {state_abbr: {topic_key: [chunks]}}
    """
    extractions = {}
    total = len(STATES_46)

    for i, (abbr, name) in enumerate(sorted(STATES_46.items()), 1):
        log.info("[%d/%d] Extracting topics for %s (%s)...", i, total, name, abbr)
        extractions[abbr] = extract_topics(rag, abbr, name)

        # Count non-empty topics
        topic_count = sum(1 for v in extractions[abbr].values() if v)
        chunk_count = sum(len(v) for v in extractions[abbr].values())
        log.info("  -> %d topics with data, %d total chunks", topic_count, chunk_count)

    return extractions
