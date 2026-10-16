"""
kiro-recall CLI — main entry point.

Commands:
  scan     — ingest workspace and extract decisions
  recall   — search for a decision by natural language query
  list     — list all stored decisions
  show     — show full detail for a specific decision ID
  stats    — show counts and tag breakdown
  serve    — start the web dashboard
"""
import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console

# Load .env from current dir or project root
load_dotenv()

console = Console()


def _get_paths():
    workspace = os.getenv("WORKSPACE_PATH", os.getcwd())
    decisions_rel = os.getenv("DECISIONS_PATH", ".kiro/decisions")
    decisions_abs = str(Path(workspace) / decisions_rel)
    return workspace, decisions_abs


def _get_engine():
    """Lazy-build the store + search engine."""
    from ..store.decision_store import DecisionStore
    from ..search.vector_index import VectorIndex
    from ..search.search_engine import SearchEngine

    _, decisions_path = _get_paths()
    store = DecisionStore(decisions_path)
    index = VectorIndex(str(Path(decisions_path) / "chroma"))
    engine = SearchEngine(store, index)
    return store, index, engine


# ── CLI Group ──────────────────────────────────────────────────────────────────

@click.group()
@click.version_option("1.0.0", prog_name="kiro-recall")
def cli():
    """
    kiro-recall — surfaces architectural decisions from your .kiro/specs, 
    git history, and README files so you never re-litigate settled choices.
    """
    pass


# ── scan ──────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--workspace", "-w", default=None, help="Path to workspace root (default: $WORKSPACE_PATH or cwd)")
@click.option("--no-git", is_flag=True, help="Skip git commit ingestion")
@click.option("--verbose", "-v", is_flag=True, help="Show chunk-by-chunk progress")
def scan(workspace, no_git, verbose):
    """Scan workspace, extract decisions, and save to the decision store."""
    from ..ingestion.ingestor import ingest_all
    from ..ingestion.spec_parser import parse_specs, parse_readme
    from ..ingestion.git_parser import parse_git_log
    from ..extractor.extractor import extract_all
    from ..store.decision_store import DecisionStore
    from ..search.vector_index import VectorIndex

    ws, decisions_path = _get_paths()
    if workspace:
        ws = workspace

    console.print(f"\n[bold cyan]kiro-recall scan[/bold cyan] — scanning [yellow]{ws}[/yellow]\n")

    # Ingest
    chunks = ingest_all(ws)
    if not chunks:
        console.print("[yellow]No content found to scan. Make sure .kiro/specs/ exists.[/yellow]")
        return

    # Extract
    decisions = extract_all(chunks, verbose=verbose)
    if not decisions:
        console.print("[yellow]No decisions could be extracted from the content.[/yellow]")
        return

    # Store
    store = DecisionStore(decisions_path)
    saved = store.save_many(decisions)

    # Index
    index = VectorIndex(str(Path(decisions_path) / "chroma"))
    index.index_decisions(store.get_all())

    console.print(f"\n[bold green]✓ Done![/bold green] "
                  f"{saved} new decisions saved to [dim]{decisions_path}[/dim]")
    console.print(f"Total decisions in store: [bold]{store.count()}[/bold]\n")


# ── recall ─────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("query", nargs=-1, required=True)
@click.option("--top", "-n", default=5, help="Number of results to return (default: 5)")
@click.option("--table", "-t", is_flag=True, help="Show results as a compact table")
def recall(query, top, table):
    """Search for decisions matching a natural language QUERY.

    Examples:\n
      kiro-recall recall "why did we choose postgres"\n
      kiro-recall recall authentication approach\n
      kiro-recall recall database -n 3
    """
    from .display import print_decision, print_decisions_table, print_no_results

    query_str = " ".join(query)
    console.print(f"\n[bold cyan]Searching:[/bold cyan] [italic]{query_str}[/italic]\n")

    try:
        store, index, engine = _get_engine()
    except Exception as e:
        console.print(f"[red]Error loading decision store: {e}[/red]")
        console.print("Run [bold]kiro-recall scan[/bold] first to index your workspace.")
        sys.exit(1)

    results = engine.search(query_str, top_k=top)

    if not results:
        print_no_results(query_str)
        return

    if table:
        print_decisions_table(results)
    else:
        for i, record in enumerate(results, 1):
            print_decision(record, index=i)

    console.print(f"\n[dim]Found {len(results)} result(s) for '{query_str}'[/dim]\n")


# ── list ───────────────────────────────────────────────────────────────────────

@cli.command("list")
@click.option("--tag", "-t", default=None, help="Filter by tag")
@click.option("--limit", "-n", default=20, help="Max results (default: 20)")
def list_decisions(tag, limit):
    """List all stored decisions."""
    from .display import print_decisions_table

    try:
        store, _, _ = _get_engine()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    if tag:
        records = store.search_by_tag(tag)
        console.print(f"\n[bold]Decisions tagged '[cyan]{tag}[/cyan]'[/bold]\n")
    else:
        records = store.get_all()
        console.print(f"\n[bold]All decisions ({store.count()} total)[/bold]\n")

    print_decisions_table(records[:limit])


# ── show ───────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("decision_id")
def show(decision_id):
    """Show full detail for a specific decision by ID."""
    from .display import print_decision

    try:
        store, _, _ = _get_engine()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    record = store.get_by_id(decision_id)
    if not record:
        console.print(f"[red]Decision '{decision_id}' not found.[/red]")
        sys.exit(1)

    print_decision(record)

    if record.raw_excerpt:
        console.print(f"\n[bold]Source excerpt:[/bold]")
        console.print(f"[dim]{record.raw_excerpt}[/dim]\n")


# ── stats ──────────────────────────────────────────────────────────────────────

@cli.command()
def stats():
    """Show decision store statistics and tag breakdown."""
    from rich.table import Table
    import json

    try:
        store, index, _ = _get_engine()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    records = store.get_all()
    total = len(records)

    # Tag frequency
    tag_counts: dict = {}
    source_counts: dict = {}
    for r in records:
        for t in r.tags:
            tag_counts[t] = tag_counts.get(t, 0) + 1
        source_counts[r.source_type] = source_counts.get(r.source_type, 0) + 1

    console.print(f"\n[bold cyan]kiro-recall stats[/bold cyan]\n")
    console.print(f"  Total decisions: [bold]{total}[/bold]")
    console.print(f"  Vector index: [bold]{'available' if index.is_available else 'disabled (keyword only)'}[/bold]")

    if source_counts:
        console.print(f"\n[bold]By source:[/bold]")
        for src, count in sorted(source_counts.items(), key=lambda x: -x[1]):
            console.print(f"  {src:<15} {count}")

    if tag_counts:
        top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:15]
        console.print(f"\n[bold]Top tags:[/bold]")
        for tag, count in top_tags:
            bar = "|" * min(count, 20)
            console.print(f"  [cyan]#{tag:<20}[/cyan] {bar} {count}")

    console.print()


# ── serve ──────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--port", "-p", default=8765, help="Port to serve on (default: 8765)")
def serve(port):
    """Start the web dashboard at http://localhost:<port>"""
    try:
        import uvicorn
        from ..api.app import create_app
        app = create_app()
        console.print(f"\n[bold green]Starting kiro-recall dashboard[/bold green]")
        console.print(f"Open: [link]http://localhost:{port}[/link]\n")
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
    except ImportError:
        console.print("[red]FastAPI/uvicorn not installed. Run: pip install fastapi uvicorn[/red]")


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    cli()


if __name__ == "__main__":
    main()
