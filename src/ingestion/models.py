"""
Data models for raw ingested chunks before LLM extraction.
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class RawChunk:
    """A raw text chunk extracted from a source file or commit."""
    content: str                          # The actual text content
    source_type: str                      # "spec" | "git_commit" | "readme" | "steering"
    source_path: str                      # File path or "git:<sha>"
    source_date: Optional[datetime]       # When was this created/modified
    commit_sha: Optional[str] = None      # Git commit SHA if applicable
    author: Optional[str] = None         # Author name if available
    title: Optional[str] = None          # Section heading or commit subject
    tags: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "source_type": self.source_type,
            "source_path": self.source_path,
            "source_date": self.source_date.isoformat() if self.source_date else None,
            "commit_sha": self.commit_sha,
            "author": self.author,
            "title": self.title,
            "tags": self.tags,
        }
