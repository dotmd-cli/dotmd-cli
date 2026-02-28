"""dotmd command line interface."""

from __future__ import annotations

from pathlib import Path

import typer

from .api import DotmdAPI, DotmdAPIError
from .formats import output_path_for_format

app = typer.Typer(help="Fetch and manage AI instruction files from mydotmd.io")


def _parse_rule_slug(value: str) -> tuple[str, str]:
    if "/" not in value:
        raise typer.BadParameter("Expected format '<username>/<title>'")

    username, title = value.split("/", 1)
    username = username.strip()
    title = title.strip()
    if not username or not title:
        raise typer.BadParameter("Both username and title are required")

    # Allow users to pass files like react-best-practices.md.
    for suffix in (".md", ".txt"):
        if title.lower().endswith(suffix):
            title = title[: -len(suffix)]
            break

    return username, title


def _write_output(destination: Path, content: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")


def _exit_with_api_error(exc: DotmdAPIError) -> None:
    typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
    raise typer.Exit(code=1)


@app.command()
def get(rule: str = typer.Argument(..., help="Rule path in the form '<username>/<title>'")) -> None:
    """Fetch a rule and write it to the correct instruction file."""
    username, title = _parse_rule_slug(rule)
    api = DotmdAPI()

    try:
        with typer.progressbar(length=2, label=f"Fetching {rule}") as progress:
            user_id = api.resolve_username(username)
            progress.update(1)
            record = api.get_rule(user_id, title)
            progress.update(1)
    except DotmdAPIError as exc:
        _exit_with_api_error(exc)

    relative_path = output_path_for_format(record.format_type)
    destination = Path.cwd() / relative_path
    _write_output(destination, record.content)

    typer.secho(f"✓ Saved {rule} to {destination}", fg=typer.colors.GREEN)


@app.command(name="search")
def search_rules(
    keywords: list[str] = typer.Argument(..., help="One or more search keywords")
) -> None:
    """Search rules by keyword."""
    api = DotmdAPI()
    try:
        rows = api.search_rules(keywords)
    except DotmdAPIError as exc:
        _exit_with_api_error(exc)

    if not rows:
        typer.echo("No matching rules found.")
        raise typer.Exit(code=0)

    typer.echo(f"Found {len(rows)} rules:\n")
    for row in rows:
        username = row.get("username")
        title = row.get("title", "<untitled>")
        fmt = row.get("format_type", "unknown")
        if isinstance(username, str) and username.strip():
            typer.echo(f"- {username}/{title} ({fmt})")
        else:
            typer.echo(f"- {title} ({fmt})")


@app.command(name="list")
def list_rules(username: str = typer.Argument(..., help="Registry username")) -> None:
    """List rules for a given username."""
    api = DotmdAPI()
    try:
        rows = api.list_rules(username)
    except DotmdAPIError as exc:
        _exit_with_api_error(exc)

    if not rows:
        typer.echo(f"No rules found for {username}.")
        raise typer.Exit(code=0)

    typer.echo(f"Rules for {username}:\n")
    for row in rows:
        title = row.get("title", "<untitled>")
        fmt = row.get("format_type", "unknown")
        typer.echo(f"- {title} ({fmt})")


@app.callback()
def main() -> None:
    """dotmd CLI."""


def run() -> None:
    """Console script entrypoint with graceful API error handling."""
    try:
        app()
    except DotmdAPIError as exc:
        _exit_with_api_error(exc)


if __name__ == "__main__":
    run()
