"""dotmd command line interface."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, NoReturn, Optional

import typer

from .__init__ import __version__
from .api import DotmdAPI, DotmdAPIError
from .art import build_banner
from .formats import FORMAT_TO_PATH, output_path_for_format, resolve_tool_alias

app = typer.Typer(
    help="Fetch and manage AI instruction files from mydotmd.io",
    no_args_is_help=True,
    add_completion=False,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


class _NoProgress:
    def __enter__(self) -> "_NoProgress":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        return False

    def update(self, _amount: int) -> None:
        return None


def _is_tty() -> bool:
    """Return True when stdout is an interactive terminal."""
    return sys.stdout.isatty()


def _no_color() -> bool:
    """Return True when color output should be suppressed.

    Respects the NO_COLOR env var (https://no-color.org/) and --no-color flag
    as well as non-TTY environments (pipes, LLM tool calls, CI).
    """
    return bool(os.environ.get("NO_COLOR")) or not _is_tty()


def _parse_rule_input(value: str) -> tuple[Optional[str], str]:
    raw = value.strip()
    if not raw:
        raise typer.BadParameter("Rule cannot be empty")

    if "/" not in raw:
        return None, raw

    username, title = raw.split("/", 1)
    username = username.strip()
    title = title.strip()
    if not username or not title:
        raise typer.BadParameter(
            "Both username and title are required when using '<username>/<title>' format"
        )

    return username, title


def _normalize_title(value: str) -> str:
    title = value.strip().lower()
    for suffix in (".md", ".txt"):
        if title.endswith(suffix):
            return title[: -len(suffix)]
    return title


#: Default registry username used when no username is specified in the rule input.
DEFAULT_USERNAME = "dotmd"


def _resolve_get_target(
    api: DotmdAPI,
    *,
    rule_input: str,
    username_option: Optional[str],
) -> tuple[str, str]:
    input_username, input_title = _parse_rule_input(rule_input)

    if input_username and username_option:
        _exit_with_error(
            "Provide username either in RULE (<username>/<title>) or with --username, not both.\n"
            "  Example: dotmd get dotmd/react-best-practices\n"
            "  Example: dotmd get react-best-practices --username dotmd",
            code=2,
        )

    username = input_username or (username_option.strip() if username_option else None)
    title = input_title.strip()
    if not title:
        raise typer.BadParameter("Title cannot be empty")

    if username:
        return username, title

    # No username provided — default to the official dotmd registry namespace.
    return DEFAULT_USERNAME, title


def _write_output(destination: Path, content: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")


def _exit_with_error(message: str, *, code: int = 1) -> NoReturn:
    typer.secho(f"Error: {message}", fg=typer.colors.RED, err=True)
    raise typer.Exit(code=code)


def _exit_with_api_error(exc: DotmdAPIError) -> NoReturn:
    typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
    raise typer.Exit(code=1)


def _show_banner(plain: bool = False) -> None:
    """Print the welcome banner — skipped when plain=True or output is not a TTY."""
    if plain or _no_color():
        return
    typer.echo(build_banner())


def _print_json(payload: Dict[str, Any]) -> None:
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


def _progress(enabled: bool, *, length: int, label: str) -> Any:
    if enabled and _is_tty():
        return typer.progressbar(length=length, label=label)
    return _NoProgress()


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"dotmd {__version__}")
        raise typer.Exit(code=0)


def _command_hint() -> str:
    return "Run 'dotmd --help' to view commands and options."


def _format_table_row(index: int, username: Optional[str], title: str, fmt: str) -> str:
    """Format a single rule row for human-readable list/search output."""
    slug = f"{username}/{title}" if username else title
    return f"  {index:>3}.  {slug:<50}  {fmt}"


# ── Commands ──────────────────────────────────────────────────────────────────


@app.command()
def get(
    rule: str = typer.Argument(
        ...,
        help=(
            "Rule to fetch. Formats accepted:\n\n"
            "  <title>              fetches dotmd/<title> by default\n\n"
            "  <username>/<title>   e.g. alice/react-best-practices\n\n"
            "Use --username to fetch from a specific user other than dotmd."
        ),
    ),
    tool: Optional[str] = typer.Argument(
        None,
        help=(
            "Target tool to write the rule for. Overrides the format from the registry.\n\n"
            "  cursor  windsurf  claude  copilot  cline  aider  gemini  continue\n\n"
            "Example: dotmd get hippa cursor  →  writes to .cursorrules"
        ),
        metavar="TOOL",
    ),
    username: Optional[str] = typer.Option(
        None,
        "--username",
        "-u",
        help="Registry username. Overrides the default 'dotmd' namespace.",
        metavar="USER",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Write to this exact path instead of the default format-mapped destination.",
        metavar="PATH",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help=(
            "Overwrite destination file if it already exists. "
            "Automatically enabled when stdout is not a TTY (scripts, LLM agents, CI)."
        ),
    ),
    print_only: bool = typer.Option(
        False,
        "--print",
        help=(
            "Print the rule content to stdout instead of writing a file. "
            "Ideal for LLM agents and scripts that need to read the content directly."
        ),
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview the destination path without writing any files.",
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress non-error output."),
    json_output: bool = typer.Option(
        False,
        "--json",
        help=(
            "Emit machine-readable JSON to stdout. "
            "Includes 'content' field with the full rule text."
        ),
    ),
) -> None:
    """Fetch a rule from the registry and write it to a local instruction file.

    \b
    LLM / agent usage:
      dotmd get cli-ux --print          Print content to stdout (no file written)
      dotmd get cli-ux --json           JSON with full content field
      dotmd get cli-ux                  Auto-overwrites in non-TTY environments

    \b
    Examples:
      dotmd get hippa
      dotmd get hippa cursor
      dotmd get soc2 windsurf
      dotmd get react-best-practices claude
      dotmd get alice/react-best-practices
      dotmd get react-best-practices --username alice
      dotmd get hippa --output .cursorrules
      dotmd get hippa --dry-run
      dotmd get cli-ux --print
      dotmd get cli-ux --json
    """
    # Validate tool alias early so we fail fast before hitting the network.
    tool_format_type: Optional[str] = None
    if tool:
        tool_format_type = resolve_tool_alias(tool)
        if tool_format_type is None:
            valid = ", ".join(sorted({"cursor", "windsurf", "claude", "copilot", "cline", "aider", "gemini", "continue"}))
            _exit_with_error(
                f"Unknown tool '{tool}'. Valid options: {valid}\n"
                "  Example: dotmd get hippa cursor",
                code=2,
            )

    # In non-TTY environments (LLM agents, scripts, CI), auto-enable --force so
    # the command never blocks on "file already exists".
    effective_force = force or not _is_tty()

    api = DotmdAPI()
    resolved_username, resolved_title = _resolve_get_target(
        api,
        rule_input=rule,
        username_option=username,
    )

    record: Any = None
    try:
        with _progress(
            enabled=not quiet and not json_output and not print_only,
            length=2,
            label=f"Fetching {resolved_username}/{resolved_title}",
        ) as progress:
            user_id = api.resolve_username(resolved_username)
            progress.update(1)
            record = api.get_rule(user_id, resolved_title)
            progress.update(1)
    except DotmdAPIError as exc:
        _exit_with_api_error(exc)

    # --print: dump content to stdout and exit — no file written
    if print_only:
        typer.echo(record.content, nl=False)
        return

    # Determine destination: --output > tool alias > registry format_type
    effective_format = tool_format_type or record.format_type
    if output:
        destination = output.expanduser()
    else:
        relative_path = output_path_for_format(effective_format)
        destination = Path.cwd() / relative_path

    if dry_run:
        if json_output:
            _print_json(
                {
                    "dry_run": True,
                    "rule": rule,
                    "tool": tool,
                    "username": resolved_username,
                    "title": resolved_title,
                    "format_type": effective_format,
                    "destination": str(destination),
                    "bytes": len(record.content.encode("utf-8")),
                    "would_overwrite": destination.exists(),
                    "content": record.content,
                }
            )
        else:
            typer.echo(f"  rule:        {resolved_username}/{resolved_title}")
            typer.echo(f"  tool:        {tool or '(from registry)'}")
            typer.echo(f"  format:      {effective_format}")
            typer.echo(f"  destination: {destination}")
            typer.echo(f"  size:        {len(record.content.encode('utf-8'))} bytes")
            if destination.exists():
                typer.secho(
                    f"  warning:     destination exists — use --force to overwrite",
                    fg=typer.colors.YELLOW,
                )
        return

    if destination.exists() and not effective_force:
        _exit_with_error(
            f"Destination already exists: {destination}\n"
            f"  Use --force to overwrite, or --output to choose a different path.",
            code=2,
        )

    _write_output(destination, record.content)

    if json_output:
        _print_json(
            {
                "status": "saved",
                "rule": rule,
                "tool": tool,
                "username": resolved_username,
                "title": resolved_title,
                "format_type": effective_format,
                "destination": str(destination),
                "bytes": len(record.content.encode("utf-8")),
                "content": record.content,
            }
        )
        return

    if not quiet:
        typer.secho(
            f"  ✓ Saved {resolved_username}/{resolved_title} → {destination}  [{effective_format}]",
            fg=typer.colors.GREEN,
        )


@app.command(name="search")
def search_rules(
    keywords: List[str] = typer.Argument(
        ...,
        help="One or more search keywords. Matched against rule titles.",
    ),
    limit: int = typer.Option(
        20, "--limit", "-n", min=1, max=100, help="Maximum number of results to return."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit machine-readable JSON to stdout."
    ),
) -> None:
    """Search the registry for rules by keyword.

    \b
    Examples:
      dotmd search react typescript
      dotmd search python best-practices --limit 5
      dotmd search react --json
    """
    api = DotmdAPI()
    rows: List[Dict[str, Any]] = []
    try:
        rows = api.search_rules(keywords, limit=limit)
    except DotmdAPIError as exc:
        _exit_with_api_error(exc)

    if json_output:
        _print_json({"count": len(rows), "keywords": keywords, "results": rows})
        return

    if not rows:
        typer.echo("No matching rules found.")
        typer.echo(f"  Tip: try broader keywords, e.g. 'dotmd search {keywords[0]}'")
        raise typer.Exit(code=0)

    typer.echo(f"Found {len(rows)} rule{'s' if len(rows) != 1 else ''}:")
    typer.echo()
    for index, row in enumerate(rows, start=1):
        row_username: Optional[str] = row.get("username")
        title: str = str(row.get("title", "<untitled>"))
        fmt: str = str(row.get("format_type", "unknown"))
        if isinstance(row_username, str) and row_username.strip():
            typer.echo(_format_table_row(index, row_username.strip(), title, fmt))
        else:
            typer.echo(_format_table_row(index, None, title, fmt))
    typer.echo()
    typer.echo(f"  To fetch a rule: dotmd get <username>/<title>")


@app.command(name="list")
def list_rules(
    username: Optional[str] = typer.Argument(
        None,
        help="Registry username. Omit to list all discoverable rules.",
        metavar="USER",
    ),
    limit: int = typer.Option(
        100, "--limit", "-n", min=1, max=200, help="Maximum number of results to return."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit machine-readable JSON to stdout."
    ),
) -> None:
    """List rules for a given username, or all public rules when omitted.

    \b
    Examples:
      dotmd list
      dotmd list dotmd
      dotmd list dotmd --json
    """
    api = DotmdAPI()
    rows: List[Dict[str, Any]] = []
    try:
        rows = api.list_rules(username, limit=limit)
    except DotmdAPIError as exc:
        _exit_with_api_error(exc)

    if json_output:
        _print_json({"count": len(rows), "username": username, "results": rows})
        return

    if not rows:
        if username:
            typer.echo(f"No rules found for '{username}'.")
            typer.echo(f"  Check the username at mydotmd.io or try: dotmd search <keywords>")
        else:
            typer.echo("No rules found.")
        raise typer.Exit(code=0)

    if username:
        typer.echo(f"Rules for {username} ({len(rows)} total):")
    else:
        typer.echo(f"All rules ({len(rows)} total):")
    typer.echo()

    for index, row in enumerate(rows, start=1):
        username_value: Optional[str] = row.get("username")
        title = str(row.get("title", "<untitled>"))
        fmt = str(row.get("format_type", "unknown"))
        if not username and isinstance(username_value, str) and username_value.strip():
            typer.echo(_format_table_row(index, username_value.strip(), title, fmt))
        else:
            typer.echo(_format_table_row(index, None, title, fmt))

    typer.echo()
    typer.echo("  To fetch a rule: dotmd get <username>/<title>")


@app.command()
def info(
    plain: bool = typer.Option(False, "--plain", help="Skip the ASCII art banner."),
    json_output: bool = typer.Option(
        False, "--json", help="Emit machine-readable JSON to stdout."
    ),
) -> None:
    """Show dotmd version, registry info, and supported formats.

    \b
    Examples:
      dotmd info
      dotmd info --json
      dotmd info --plain
    """
    api = DotmdAPI()
    payload: Dict[str, Any] = {
        "version": __version__,
        "registry": "https://mydotmd.io",
        "commands": ["get", "search", "list", "info"],
        "formats": FORMAT_TO_PATH,
        "config": {
            "base_url": api.base_url,
            "registry_site_url": api.registry_site_url,
            "auth_headers_enabled": bool(api.headers),
            "env_vars": {
                "DOTMD_SUPABASE_BASE_URL": "Override the Supabase REST base URL",
                "DOTMD_BASE_URL": "Alias for DOTMD_SUPABASE_BASE_URL",
                "DOTMD_SUPABASE_ANON_KEY": "Supabase anonymous API key",
                "DOTMD_API_KEY": "Alias for DOTMD_SUPABASE_ANON_KEY",
                "NO_COLOR": "Set to any value to disable color output",
            },
        },
    }

    if json_output:
        _print_json(payload)
        return

    _show_banner(plain=plain)
    typer.echo(f"  Version:   {payload['version']}")
    typer.echo(f"  Registry:  {payload['registry']}")
    typer.echo(f"  Commands:  {', '.join(payload['commands'])}")
    typer.echo()
    typer.echo("  Supported formats:")
    for fmt, path in FORMAT_TO_PATH.items():
        typer.echo(f"    {fmt:<20}  →  {path}")
    typer.echo()
    typer.echo("  Config:")
    typer.echo(f"    base_url:             {payload['config']['base_url']}")
    typer.echo(f"    auth_headers_enabled: {payload['config']['auth_headers_enabled']}")
    typer.echo()
    typer.echo("  Environment variables:")
    for var, desc in payload["config"]["env_vars"].items():  # type: ignore[union-attr]
        typer.echo(f"    {var:<30}  {desc}")


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show dotmd version and exit.",
        is_eager=True,
        callback=_version_callback,
    ),
) -> None:
    """dotmd — the open .md registry CLI.

    Fetch and manage AI instruction files from mydotmd.io.
    Use 'dotmd COMMAND --help' for command-specific help and examples.

    \b
    Quick start:
      dotmd list
      dotmd search react typescript
      dotmd get dotmd/react-best-practices
    """
    _ = version


def run() -> None:
    """Console script entrypoint with graceful error handling."""
    try:
        app()
    except DotmdAPIError as exc:
        _exit_with_api_error(exc)
    except KeyboardInterrupt:
        typer.secho(f"\nCancelled. {_command_hint()}", fg=typer.colors.YELLOW, err=True)
        raise typer.Exit(code=130)


if __name__ == "__main__":
    run()

# Made with Bob
