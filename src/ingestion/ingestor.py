"""
Top-level ingestion orchestrator.
Collects RawChunks from all source types.
"""
from typing import List
from .models import RawChunk
from .spec_parser import parse_specs, parse_readme
from .git_parser import parse_git_log


def ingest_all(workspace_path: str) -> List[RawChunk]:
    """
    Run all ingestion parsers and return a deduplicated list of RawChunks.
    """
    print(f"[ingest] Scanning workspace: {workspace_path}")

    chunks: List[RawChunk] = []

    # 1. Kiro specs and steering files
    spec_chunks = parse_specs(workspace_path)
    print(f"[ingest] Found {len(spec_chunks)} spec/steering chunks")
    chunks.extend(spec_chunks)

    # 2. README files
    readme_chunks = parse_readme(workspace_path)
    print(f"[ingest] Found {len(readme_chunks)} README chunks")
    chunks.extend(readme_chunks)

    # 3. Git commit history
    git_chunks = parse_git_log(workspace_path)
    print(f"[ingest] Found {len(git_chunks)} relevant git commits")
    chunks.extend(git_chunks)

    # Deduplicate by content hash
    seen = set()
    unique_chunks = []
    for chunk in chunks:
        key = hash(chunk.content[:200])
        if key not in seen:
            seen.add(key)
            unique_chunks.append(chunk)

    print(f"[ingest] Total unique chunks: {len(unique_chunks)}")
    return unique_chunks
