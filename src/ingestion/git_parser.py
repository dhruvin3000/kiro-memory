"""
Extracts meaningful commit messages and PR-style descriptions from git history.
Filters out noise (merge commits, version bumps, trivial one-liners).
"""
import re
from datetime import datetime
from typing import List, Optional

from .models import RawChunk

# Patterns that usually signal architectural decisions in commit messages
DECISION_SIGNALS = [
    r"\bchose\b", r"\bdecided\b", r"\bswitch(ed)?\b", r"\breplace(d)?\b",
    r"\bmigrat(e|ed|ing)\b", r"\brefactor\b", r"\badd(ed)?\b.{0,30}\bsupport\b",
    r"\bdrop(ped)?\b", r"\bremov(e|ed)\b", r"\buse\b.{0,20}\binstead\b",
    r"\barchitect\b", r"\bdesign\b", r"\bapproach\b", r"\btrade.?off\b",
]
_SIGNAL_RE = re.compile("|".join(DECISION_SIGNALS), re.IGNORECASE)

# Commits to skip
SKIP_PATTERNS = re.compile(
    r"^(Merge (pull request|branch)|Bump version|chore:|style:|"
    r"auto.?format|fix typo|minor fix|wip:?)",
    re.IGNORECASE,
)


def parse_git_log(workspace_path: str, max_commits: int = 500) -> List[RawChunk]:
    """
    Walk git history and return RawChunks for commits that look like
    they contain architectural or design decisions.
    """
    try:
        import git  # gitpython
    except ImportError:
        print("[warn] gitpython not installed — skipping git ingestion")
        return []

    try:
        repo = git.Repo(workspace_path, search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        print(f"[warn] No git repo found at {workspace_path}")
        return []

    chunks = []
    for commit in repo.iter_commits(max_count=max_commits):
        message = commit.message.strip()

        # Skip noise
        if SKIP_PATTERNS.match(message):
            continue

        # Only keep commits with decision-like language OR long bodies
        body = message.split("\n", 1)[1].strip() if "\n" in message else ""
        subject = message.split("\n")[0]

        has_signal = bool(_SIGNAL_RE.search(message))
        has_body = len(body) > 100

        if not (has_signal or has_body):
            continue

        content = f"Commit: {subject}\n\n{body}" if body else f"Commit: {subject}"

        chunks.append(RawChunk(
            content=content,
            source_type="git_commit",
            source_path=f"git:{commit.hexsha[:8]}",
            source_date=datetime.fromtimestamp(commit.committed_date),
            commit_sha=commit.hexsha,
            author=str(commit.author),
            title=subject,
        ))

    return chunks
