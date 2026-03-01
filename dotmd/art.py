"""ASCII art assets for dotmd CLI output."""

from __future__ import annotations

import io

import pyfiglet
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


def build_banner() -> str:
    """Return a rich-rendered dotmd welcome banner for CLI splash screens."""
    buf = io.StringIO()
    c = Console(file=buf, highlight=False, force_terminal=True, width=80)

    # ── Giant wordmark via pyfiglet ───────────────────────────────────────────
    raw = pyfiglet.figlet_format("dotmd", font="slant")
    wm_lines = raw.splitlines()
    while wm_lines and not wm_lines[-1].strip():
        wm_lines.pop()

    wordmark = Text(justify="left")
    wm_colours = [
        "bold bright_cyan",
        "bold cyan",
        "bold bright_blue",
        "bold blue",
        "bold bright_cyan",
    ]
    for i, line in enumerate(wm_lines):
        wordmark.append(line + "\n", style=wm_colours[i % len(wm_colours)])

    # ── Tagline ───────────────────────────────────────────────────────────────
    tagline = Text()
    tagline.append("  Like Docker Hub, but for ", style="white")
    tagline.append(".md", style="bold bright_cyan")
    tagline.append(" files.\n", style="white")

    # ── Description ───────────────────────────────────────────────────────────
    body = Text()
    body.append("\n")
    body.append("  Fetch and install the instruction files that power\n", style="dim white")
    body.append("  your AI coding assistants.\n", style="dim white")

    body.append("\n")
    tools = ["Cursor", "Windsurf", "Claude", "Copilot", "Cline", "Aider"]
    body.append("  Works with  ", style="dim white")
    for j, tool in enumerate(tools):
        body.append(tool, style="bold bright_blue")
        if j < len(tools) - 1:
            body.append("  ", style="dim white")
    body.append("\n\n", style="dim white")

    body.append("  Quick start\n", style="bold white")
    body.append("  " + "─" * 34 + "\n", style="dim blue")
    for cmd, note in [
        ("dotmd list", "browse the registry"),
        ("dotmd search <query>", "find rules"),
        ("dotmd get <user>/<rule>", "install a rule"),
        ("dotmd info <user>/<rule>", "inspect a rule"),
    ]:
        body.append("  $ ", style="dim white")
        body.append(f"{cmd:<26}", style="bold bright_cyan")
        body.append(f"  {note}\n", style="dim white")

    body.append("\n")
    body.append("  ● ", style="bold bright_blue")
    body.append("mydotmd.io", style="bold white")
    body.append("  ·  ", style="dim white")
    body.append("github.com/dotmd-cli/dotmd-cli", style="dim white")
    body.append("\n")

    # ── Assemble ──────────────────────────────────────────────────────────────
    content = Text()
    content.append_text(wordmark)
    content.append_text(tagline)
    content.append_text(body)

    c.print(
        Panel(
            content,
            border_style="bright_blue",
            padding=(0, 1),
        )
    )

    return buf.getvalue()

