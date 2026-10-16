"""
Structured decision record — the output of LLM extraction.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import uuid


@dataclass
class DecisionRecord:
    """A single architectural or design decision extracted from source material."""
    id: str = field(default_factory=lambda: f"dec_{uuid.uuid4().hex[:8]}")
    question: str = ""              # "Which database should we use?"
    decision: str = ""              # "PostgreSQL"
    rationale: str = ""             # "Chosen for ACID compliance..."
    alternatives_rejected: List[str] = field(default_factory=list)
    source_type: str = ""           # "spec" | "git_commit" | "readme"
    source_path: str = ""           # file path or "git:<sha>"
    source_date: Optional[str] = None
    commit_sha: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.0         # LLM confidence 0.0 - 1.0
    raw_excerpt: str = ""           # Original text that produced this decision

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "question": self.question,
            "decision": self.decision,
            "rationale": self.rationale,
            "alternatives_rejected": self.alternatives_rejected,
            "source_type": self.source_type,
            "source_path": self.source_path,
            "source_date": self.source_date,
            "commit_sha": self.commit_sha,
            "author": self.author,
            "tags": self.tags,
            "confidence": self.confidence,
            "raw_excerpt": self.raw_excerpt,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DecisionRecord":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
