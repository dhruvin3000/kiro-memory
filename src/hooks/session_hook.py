"""
Kiro SessionStart hook script.

When Kiro starts a session, this script:
1. Reads context from stdin (JSON with session info, open files, etc.)
2. Queries the decision store for relevant past decisions
3. Prints a context block to stdout that Kiro injects into the session

Usage in .kiro/hooks/decisions.json:
  {
    "version": "v1",
    "hooks": [{
      "name": "Surface Past Decisions",
      "trigger": "SessionStart",
      "action": {
        "type": "command",
        "command": "python -m src.hooks.session_hook"
      }
    }]
  }
"""
import sys
import json
import os
from pathlib import Path


def get_context_query(session_data: dict) -> str:
    """
    Build a search query from the session context.
    Uses open file paths, workspace name, and recent activity.
    """
    parts = []

    # Extract open files / current working files
    open_files = session_data.get("openFiles", [])
    for f in open_files[:5]:
        # Use filename stem as search hint
        stem = Path(f).stem.replace("-", " ").replace("_", " ")
        parts.append(stem)

    # Workspace name
    workspace = session_data.get("workspaceName", "")
    if workspace:
        parts.append(workspace)

    # Recent prompt if available
    recent_prompt = session_data.get("lastPrompt", "")
    if recent_prompt:
        parts.append(recent_prompt[:100])

    return " ".join(parts) if parts else "architecture design decisions"


def format_decisions_for_context(decisions: list) -> str:
    """Format decisions as a compact context block for Kiro injection."""
    if not decisions:
        return ""

    lines = [
        "## Past Architectural Decisions (from kiro-recall)",
        "",
        "The following decisions were previously made in this project. "
        "Do not re-litigate these unless the user explicitly asks to revisit them:",
        "",
    ]

    for i, d in enumerate(decisions, 1):
        lines.append(f"**{i}. {d['decision']}**")
        lines.append(f"   - Question: {d['question']}")
        lines.append(f"   - Rationale: {d['rationale']}")
        if d.get("alternatives_rejected"):
            lines.append(f"   - Rejected alternatives: {', '.join(d['alternatives_rejected'])}")
        lines.append(f"   - Source: {d['source_type']} ({d.get('source_date', 'unknown date')})")
        lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def main():
    # Read session data from stdin
    try:
        raw = sys.stdin.read()
        session_data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        session_data = {}

    # Locate the decision store
    workspace = session_data.get("workspacePath", os.getcwd())
    decisions_rel = os.getenv("DECISIONS_PATH", ".kiro/decisions")
    decisions_path = str(Path(workspace) / decisions_rel)

    # Check if store exists
    db_path = Path(decisions_path) / "decisions.db"
    if not db_path.exists():
        # No decisions indexed yet — exit silently
        sys.exit(0)

    try:
        # Import store + search
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.store.decision_store import DecisionStore
        from src.search.vector_index import VectorIndex
        from src.search.search_engine import SearchEngine

        store = DecisionStore(decisions_path)
        index = VectorIndex(str(Path(decisions_path) / "chroma"))
        engine = SearchEngine(store, index)

        query = get_context_query(session_data)
        results = engine.search(query, top_k=5)

        if not results:
            sys.exit(0)

        context_block = format_decisions_for_context([r.to_dict() for r in results])
        print(context_block)

    except Exception as e:
        # Hook should never crash the session — fail silently
        sys.exit(0)


if __name__ == "__main__":
    main()
