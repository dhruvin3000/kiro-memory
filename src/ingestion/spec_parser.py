"""
Parses .kiro/specs/*.md files into raw chunks.
Splits on markdown headings so each section becomes one chunk.
"""
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List

from .models import RawChunk


def parse_specs(workspace_path: str) -> List[RawChunk]:
    """
    Walk .kiro/specs/ and extract all markdown sections as RawChunks.
    Also scans .kiro/steering/ for additional context.
    """
    chunks: List[RawChunk] = []

    search_dirs = [
        (Path(workspace_path) / ".kiro" / "specs", "spec"),
        (Path(workspace_path) / ".kiro" / "steering", "steering"),
        (Path(workspace_path) / "docs", "spec"),
    ]

    for search_dir, source_type in search_dirs:
        if not search_dir.exists():
            continue

        for md_file in search_dir.rglob("*.md"):
            try:
                file_chunks = _parse_markdown_file(md_file, source_type)
                chunks.extend(file_chunks)
            except Exception as e:
                print(f"[warn] Could not parse {md_file}: {e}")

    return chunks


def _parse_markdown_file(path: Path, source_type: str) -> List[RawChunk]:
    """Split a markdown file into per-section chunks."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    mtime = datetime.fromtimestamp(path.stat().st_mtime)

    # Split on H1/H2/H3 headings
    sections = re.split(r"(?=^#{1,3} )", text, flags=re.MULTILINE)

    chunks = []
    for section in sections:
        section = section.strip()
        if len(section) < 50:   # skip trivially short sections
            continue

        # Extract heading as title
        heading_match = re.match(r"^(#{1,3})\s+(.+)", section)
        title = heading_match.group(2) if heading_match else path.stem

        chunks.append(RawChunk(
            content=section,
            source_type=source_type,
            source_path=str(path),
            source_date=mtime,
            title=title,
        ))

    return chunks


def parse_readme(workspace_path: str) -> List[RawChunk]:
    """Parse README files at the workspace root."""
    chunks = []
    for readme in Path(workspace_path).glob("README*"):
        if readme.suffix.lower() in (".md", ".txt", ""):
            try:
                file_chunks = _parse_markdown_file(readme, "readme")
                chunks.extend(file_chunks)
            except Exception as e:
                print(f"[warn] Could not parse {readme}: {e}")
    return chunks
