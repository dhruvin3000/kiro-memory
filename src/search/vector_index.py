"""
Semantic vector search over decision records using ChromaDB + sentence-transformers.
Falls back to keyword search if ChromaDB is not available.
"""
import os
from pathlib import Path
from typing import List, Tuple

from ..extractor.models import DecisionRecord


class VectorIndex:
    """
    Wraps ChromaDB collection for semantic similarity search.
    Each decision is embedded as: "{question} {decision} {rationale}"
    """

    COLLECTION_NAME = "kiro_decisions"

    def __init__(self, index_path: str):
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        self._client = None
        self._collection = None
        self._embedding_fn = None
        self._available = False
        self._init()

    def _init(self):
        try:
            import chromadb
            from chromadb.utils import embedding_functions

            model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=model_name
            )
            self._client = chromadb.PersistentClient(path=str(self.index_path))
            self._collection = self._client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                embedding_function=self._embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )
            self._available = True
            print(f"[search] Vector index loaded ({self._collection.count()} docs)")
        except ImportError:
            print("[search] ChromaDB not available — semantic search disabled, using keyword fallback")
        except Exception as e:
            print(f"[search] Vector index init failed: {e} — using keyword fallback")

    @property
    def is_available(self) -> bool:
        return self._available

    def index_decisions(self, decisions: List[DecisionRecord]):
        """Add or update decisions in the vector index."""
        if not self._available:
            return

        # Get already-indexed IDs
        existing = set(self._collection.get()["ids"])

        docs, ids, metas = [], [], []
        for d in decisions:
            if d.id in existing:
                continue
            # Combine fields into one searchable text
            text = f"{d.question} {d.decision} {d.rationale} {' '.join(d.tags)}"
            docs.append(text)
            ids.append(d.id)
            metas.append({
                "source_type": d.source_type,
                "source_path": d.source_path,
                "tags": ",".join(d.tags),
                "confidence": str(d.confidence),
            })

        if docs:
            self._collection.add(documents=docs, ids=ids, metadatas=metas)
            print(f"[search] Indexed {len(docs)} new decisions into vector store")

    def semantic_search(
        self, query: str, top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Search by semantic similarity.
        Returns list of (decision_id, distance) tuples.
        """
        if not self._available or self._collection.count() == 0:
            return []

        results = self._collection.query(
            query_texts=[query],
            n_results=min(top_k, self._collection.count()),
        )

        pairs = []
        for id_, distance in zip(results["ids"][0], results["distances"][0]):
            similarity = 1.0 - distance  # cosine distance → similarity
            pairs.append((id_, similarity))

        return pairs
