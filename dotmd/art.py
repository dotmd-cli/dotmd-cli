"""ASCII art assets for dotmd CLI output."""

from __future__ import annotations

import io
from typing import List

import pyfiglet
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# ---------------------------------------------------------------------------
# Hand-crafted mascot — the dotmd blob doctor
# Round blob body, big eyes, wave smile, stethoscope on left arm,
# markdown clipboard held in right arm.
# ---------------------------------------------------------------------------
_MASCOT: List[str] = [
    "          .--------.",
    "        .'          '.",
    "       /  (O)    (O)  \\",
    "      |                |",
    "      |    .-------.   |",
    "      |   ( ~~~~~~~ )  |",
    "       \\   '-------'  /",
    "        '.          .'",
    "   .-----'----------'-----.",
    "  /  @                     \\",
    " | @--)      .----------.   |",
    " |           | # .md    |   |",
    " |           |----------|   |",
    " |           |  rules   |   |",
    "  \\          '----------'  /",
    "   '------.        .------'",
    "          |        |",
    "         _|_      _|_",
    "        /___\\    /___\\",
]


def _mascot_text() -> Text:
    """Build a rich Text object from the mascot lines with a colour gradient."""
    t = Text(no_wrap=True)
    total = len(_MASCOT)
    for i, line in enumerate(_MASCOT):
        ratio = i / max(total - 1, 1)
        if ratio < 0.45:
            style = "bold bright_blue"
        elif ratio < 0.75:
            style = "bold cyan"
        else:
            style = "bold blue"
        # No trailing newline on the last line — prevents an empty row in the panel
        suffix = "\n" if i < total - 1 else ""
        t.append(line + suffix, style=style)
    return t


def build_banner() -> str:
    """Return a rich-rendered dotmd welcome banner for CLI splash screens."""
    buf = io.StringIO()
    c = Console(file=buf, highlight=False, force_terminal=True, width=100)

    # ── Giant wordmark via pyfiglet (speed font) ─────────────────────────────
    raw = pyfiglet.figlet_format("dotmd", font="speed")
    wm_lines = raw.splitlines()
    # Strip trailing blank lines produced by pyfiglet
    while wm_lines and not wm_lines[-1].strip():
        wm_lines.pop()

    wordmark = Text(justify="left")
    for i, line in enumerate(wm_lines):
        style = "bold bright_blue" if i % 2 == 0 else "bold blue"
        wordmark.append(line + "\n", style=style)

    # ── Tagline ───────────────────────────────────────────────────────────────
    tagline = Text()
    tagline.append("  Share your ", style="white")
    tagline.append(".md", style="bold bright_cyan")
    tagline.append(" instruction files.  ", style="white")
    tagline.append(
        "Open source registry for AI coding assistants.", style="dim white"
    )

    top_content = Text()
    top_content.append_text(wordmark)
    top_content.append_text(tagline)

    c.print(
        Panel(
            top_content,
            border_style="bright_blue",
            padding=(0, 2),
        )
    )

    # ── Description text ──────────────────────────────────────────────────────
    desc = Text()
    desc.append("\n")
    desc.append("Like Docker Hub, but for ", style="white")
    desc.append(".md", style="bold bright_cyan")
    desc.append(" files.\n\n", style="white")
    desc.append("Fetch and share the instruction files\n", style="white")
    desc.append("that power AI coding assistants.\n\n", style="white")
    desc.append("Works with ", style="dim white")
    tools = ["Cursor", "Windsurf", "Claude", "Copilot"]
    for j, tool in enumerate(tools):
        desc.append(tool, style="bold bright_blue")
        if j < len(tools) - 1:
            desc.append(", ", style="dim white")
    desc.append(", and more.\n\n", style="dim white")
    desc.append("Quick start:\n", style="bold white")
    for cmd in [
        "dotmd list",
        "dotmd search <keywords>",
        "dotmd get <user>/<rule>",
    ]:
        desc.append("  $ ", style="dim white")
        desc.append(cmd + "\n", style="bold bright_cyan")
    desc.append("\n  mydotmd.io", style="bold bright_blue")

    # ── Two-column grid: mascot left, description right ───────────────────────
    grid = Table.grid(expand=True)
    grid.add_column(width=32)  # mascot — fixed width
    grid.add_column()           # description — fills remaining space
    grid.add_row(_mascot_text(), desc)

    c.print(
        Panel(
            grid,
            title=(
                "[bold bright_blue]dotmd[/bold bright_blue]"
                " [dim white]— the open .md registry[/dim white]"
            ),
            border_style="bright_blue",
            padding=(0, 1),
        )
    )

    return buf.getvalue()

# Made with Bob
