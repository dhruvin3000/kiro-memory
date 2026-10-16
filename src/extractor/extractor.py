"""
LLM-powered decision extractor.
Takes a RawChunk and returns 0..N DecisionRecords.
"""
import json
from typing import List

from ..ingestion.models import RawChunk
from .models import DecisionRecord
from .llm_client import call_llm, extract_json_from_response

EXTRACTION_PROMPT = """
Analyze the following text excerpt from a software project's documentation or commit history.

Extract ALL architectural decisions, design choices, or technology selections that are explicitly 
stated or clearly implied. For each decision found, return a JSON object with this exact structure:

{{
  "decisions": [
    {{
      "question": "What problem or choice was being addressed?",
      "decision": "What was decided or chosen?",
      "rationale": "Why was this decision made? What reasoning was given?",
      "alternatives_rejected": ["list", "of", "alternatives", "that", "were", "considered"],
      "tags": ["relevant", "topic", "tags", "like", "database", "auth", "api"],
      "confidence": 0.0
    }}
  ]
}}

Rules:
- confidence should be 0.0-1.0: how confident you are this is a real decision (not just a description)
- If no decisions are found, return {{"decisions": []}}
- Keep rationale concise but complete (1-3 sentences)
- tags should be lowercase single words or hyphenated phrases
- Only extract decisions that have at least some rationale or context

TEXT TO ANALYZE:
---
{content}
---

Respond with ONLY the JSON object, no explanation.
"""


def extract_decisions(chunk: RawChunk) -> List[DecisionRecord]:
    """
    Run LLM extraction on a single RawChunk.
    Returns a list of DecisionRecords (may be empty).
    """
    prompt = EXTRACTION_PROMPT.format(content=chunk.content[:3000])

    raw_response = call_llm(prompt)
    if not raw_response:
        return []

    parsed = extract_json_from_response(raw_response)
    if not parsed or "decisions" not in parsed:
        return []

    records = []
    for item in parsed["decisions"]:
        # Skip low-confidence extractions
        confidence = float(item.get("confidence", 0.0))
        if confidence < 0.4:
            continue

        record = DecisionRecord(
            question=item.get("question", ""),
            decision=item.get("decision", ""),
            rationale=item.get("rationale", ""),
            alternatives_rejected=item.get("alternatives_rejected", []),
            tags=item.get("tags", []),
            confidence=confidence,
            source_type=chunk.source_type,
            source_path=chunk.source_path,
            source_date=chunk.source_date.isoformat() if chunk.source_date else None,
            commit_sha=chunk.commit_sha,
            author=chunk.author,
            raw_excerpt=chunk.content[:500],
        )
        records.append(record)

    return records


def extract_all(chunks: List[RawChunk], verbose: bool = True) -> List[DecisionRecord]:
    """
    Run extraction over all chunks and return all decisions found.
    """
    all_decisions = []
    for i, chunk in enumerate(chunks):
        if verbose:
            print(f"[extract] Processing chunk {i+1}/{len(chunks)}: {chunk.title or chunk.source_path}")
        try:
            decisions = extract_decisions(chunk)
            all_decisions.extend(decisions)
            if verbose and decisions:
                print(f"  → Found {len(decisions)} decision(s)")
        except Exception as e:
            print(f"  → Error: {e}")

    print(f"[extract] Total decisions extracted: {len(all_decisions)}")
    return all_decisions
