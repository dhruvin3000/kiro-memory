"""
Unified search engine: merges semantic + keyword results and returns ranked decisions.
"""
from typing import List

from ..extractor.models import DecisionRecord
from ..store.decision_store import DecisionStore
from .vector_index import VectorIndex


class SearchEngine:
    def __init__(self, store: DecisionStore, index: VectorIndex):
        self.store = store
        self.index = index

    def search(self, query: str, top_k: int = 5) -> List[DecisionRecord]:
        """
        Hybrid search: semantic (vector) + keyword (SQL).
        Deduplicates and re-ranks by combined score.
        """
        scores: dict[str, float] = {}

        # 1. Semantic search
        if self.index.is_available:
            for dec_id, similarity in self.index.semantic_search(query, top_k=top_k * 2):
                scores[dec_id] = scores.get(dec_id, 0.0) + similarity * 0.7

        # 2. Keyword search
        keyword_results = self.store.keyword_search(query)
        max_kw = len(keyword_results) or 1
        for rank, record in enumerate(keyword_results[:top_k * 2]):
            kw_score = (max_kw - rank) / max_kw * 0.3
            scores[record.id] = scores.get(record.id, 0.0) + kw_score

        # 3. Fetch, sort, return
        ranked_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        results = []
        for dec_id in ranked_ids[:top_k]:
            record = self.store.get_by_id(dec_id)
            if record:
                results.append(record)

        # If no vector results, fall back to keyword-only
        if not results:
            results = keyword_results[:top_k]

        return results
