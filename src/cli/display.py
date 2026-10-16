"""
Rich-based terminal display helpers for decision records.
"""
from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from ..extractor.models import DecisionRecord

console = Console()


def print_decision(record: DecisionRecord, index: int = None):
    """Print a single decision as a rich Panel."""
    prefix = f"#{index} " if index is not None else ""
    title = f"{prefix}[bold cyan]{record.decision}[/bold cyan]"

    lines = []
    lines.append(f"[bold yellow]Q:[/bold yellow] {record.question}")
    lines.append(f"[bold green]Decision:[/bold green] {record.decision}")
    lines.append(f"[bold white]Rationale:[/bold white] {record.rationale}")

    if record.alternatives_rejected:
        alts = ", ".join(record.alternatives_rejected)
        lines.append(f"[bold red]Rejected:[/bold red] {alts}")

    if record.tags:
        tags_str = " ".join(f"[dim]#{t}[/dim]" for t in record.tags)
        lines.append(f"[bold blue]Tags:[/bold blue] {tags_str}")

    lines.append(
        f"[dim]Source: {record.source_type} | {record.source_path} | "
        f"{record.source_date or 'unknown date'} | confidence: {record.confidence:.0%}[/dim]"
    )

    console.print(Panel("\n".join(lines), title=title, border_style="blue"))


def print_decisions_table(records: List[DecisionRecord]):
    """Print a compact table of decisions."""
    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("Decision", style="cyan", min_width=20)
    table.add_column("Question", style="white", min_width=30)
    table.add_column("Tags", style="blue")
    table.add_column("Source", style="dim", min_width=15)
    table.add_column("Conf.", style="green", width=6)

    for i, r in enumerate(records, 1):
        table.add_row(
            str(i),
            r.decision[:40],
            r.question[:50],
            ", ".join(r.tags[:3]),
            r.source_type,
            f"{r.confidence:.0%}",
        )

    console.print(table)


def print_no_results(query: str):
    console.print(
        f"\n[yellow]No decisions found for:[/yellow] [italic]{query}[/italic]\n"
        "Try: [dim]kiro-recall list[/dim] to see all decisions, "
        "or [dim]kiro-recall scan[/dim] to index your workspace."
    )
