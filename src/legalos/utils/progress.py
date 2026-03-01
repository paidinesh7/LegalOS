"""Rich progress bars and status displays."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.panel import Panel
from rich.text import Text

console = Console()


def make_progress() -> Progress:
    """Create a styled progress bar."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    )


@contextmanager
def status_spinner(message: str) -> Generator[None, None, None]:
    """Show a spinner with a message."""
    with console.status(f"[bold cyan]{message}…", spinner="dots"):
        yield


def print_header(title: str) -> None:
    """Print a styled header."""
    console.print(Panel(Text(title, style="bold white"), style="blue", expand=False))


def print_success(message: str) -> None:
    console.print(f"[bold green]✓[/] {message}")


def print_warning(message: str) -> None:
    console.print(f"[bold yellow]![/] {message}")


def print_error(message: str) -> None:
    console.print(f"[bold red]✗[/] {message}")


def print_cost(summary: str) -> None:
    console.print(f"[dim]{summary}[/]")
