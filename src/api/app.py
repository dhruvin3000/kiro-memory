"""
FastAPI backend for the kiro-recall web dashboard.
Serves the React SPA and provides REST endpoints for the decision store.
"""
import os
import sys
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure project root is on sys.path so absolute imports always work
_PROJECT_ROOT = str(Path(__file__).parent.parent.parent.resolve())
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


# ── Response models ────────────────────────────────────────────────────────────

class DecisionResponse(BaseModel):
    id: str
    question: str
    decision: str
    rationale: str
    alternatives_rejected: List[str]
    source_type: str
    source_path: str
    source_date: Optional[str] = None
    commit_sha: Optional[str] = None
    author: Optional[str] = None
    tags: List[str]
    confidence: float


class StatsResponse(BaseModel):
    total: int
    by_source: dict
    top_tags: dict
    vector_index_available: bool


# ── App factory ────────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="kiro-recall",
        description="Architectural decision log for your Kiro workspace",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def get_engine():
        """Build store + search engine using absolute imports."""
        from src.store.decision_store import DecisionStore
        from src.search.vector_index import VectorIndex
        from src.search.search_engine import SearchEngine

        workspace = os.getenv("WORKSPACE_PATH", _PROJECT_ROOT)
        decisions_rel = os.getenv("DECISIONS_PATH", ".kiro/decisions")
        decisions_path = str(Path(workspace) / decisions_rel)

        store = DecisionStore(decisions_path)
        index = VectorIndex(str(Path(decisions_path) / "chroma"))
        engine = SearchEngine(store, index)
        return store, index, engine

    # ── Routes ─────────────────────────────────────────────────────────────

    @app.get("/api/decisions", response_model=List[DecisionResponse])
    def list_decisions(
        tag: Optional[str] = Query(None),
        limit: int = Query(50),
    ):
        store, _, _ = get_engine()
        records = store.search_by_tag(tag) if tag else store.get_all()
        return [_to_response(r) for r in records[:limit]]

    @app.get("/api/decisions/search", response_model=List[DecisionResponse])
    def search_decisions(
        q: str = Query(..., description="Natural language query"),
        top: int = Query(5),
    ):
        _, _, engine = get_engine()
        results = engine.search(q, top_k=top)
        return [_to_response(r) for r in results]

    @app.get("/api/decisions/{decision_id}", response_model=DecisionResponse)
    def get_decision(decision_id: str):
        store, _, _ = get_engine()
        record = store.get_by_id(decision_id)
        if not record:
            raise HTTPException(status_code=404, detail="Decision not found")
        return _to_response(record)

    @app.get("/api/stats", response_model=StatsResponse)
    def get_stats():
        store, index, _ = get_engine()
        records = store.get_all()

        tag_counts: dict = {}
        source_counts: dict = {}
        for r in records:
            for t in r.tags:
                tag_counts[t] = tag_counts.get(t, 0) + 1
            source_counts[r.source_type] = source_counts.get(r.source_type, 0) + 1

        top_tags = dict(sorted(tag_counts.items(), key=lambda x: -x[1])[:20])
        return StatsResponse(
            total=len(records),
            by_source=source_counts,
            top_tags=top_tags,
            vector_index_available=index.is_available,
        )

    # ── Static SPA (built React app) ───────────────────────────────────────
    static_dir = Path(_PROJECT_ROOT) / "web" / "dist"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="spa")

    return app


def _to_response(record) -> DecisionResponse:
    return DecisionResponse(
        id=record.id,
        question=record.question,
        decision=record.decision,
        rationale=record.rationale,
        alternatives_rejected=record.alternatives_rejected,
        source_type=record.source_type,
        source_path=record.source_path,
        source_date=record.source_date,
        commit_sha=record.commit_sha,
        author=record.author,
        tags=record.tags,
        confidence=record.confidence,
    )
