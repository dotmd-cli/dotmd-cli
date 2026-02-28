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
# A friendly rounded blob holding a markdown clipboard.
# All lines are exactly 42 characters wide.
# ---------------------------------------------------------------------------
_MASCOT: List[str] = [
    "       .~~~~~~~~~~~~~~~~~~~~~~~~~~~.      ",
    "     .'                             '.    ",
    "    /   ( o )               ( o )    \\    ",
    "   |                                  |   ",
    "   |          .-------------.         |   ",
    "   |          |  ~ ~ ~ ~ ~  |         |   ",
    "   |          '-------------'         |   ",
    "    \\                                /    ",
    "     '----._______________________.---'   ",
    "   .------------------------------------. ",
    "   | (o)    .-----------------------.   | ",
    "   |  |     |  ##  claude.md        |   | ",
    "   |  '---  |  ##  .cursorrules     |   | ",
    "   |        |  ##  windsurf.md      |   | ",
    "   |        '-----------------------'   | ",
    "   '------------------------------------' ",
    "         |  |               |  |          ",
    "        _|__|_             _|__|_         ",
    "       /______\\           /______\\        ",
]


def _mascot_text() -> Text:
    """Build a rich Text object from the mascot lines with a colour gradient."""
    t = Text(no_wrap=True)
    total = len(_MASCOT)
    colours = [
        "bold bright_cyan",   # top ~30%
        "bold cyan",          # mid ~40%
        "bold bright_blue",   # lower ~20%
        "bold blue",          # feet ~10%
    ]
    for i, line in enumerate(_MASCOT):
        ratio = i / max(total - 1, 1)
        if ratio < 0.30:
            style = colours[0]
        elif ratio < 0.65:
            style = colours[1]
        elif ratio < 0.85:
            style = colours[2]
        else:
            style = colours[3]
        suffix = "\n" if i < total - 1 else ""
        t.append(line + suffix, style=style)
    return t


def build_banner() -> str:
    """Return a rich-rendered dotmd welcome banner for CLI splash screens."""
    buf = io.StringIO()
    c = Console(file=buf, highlight=False, force_terminal=True, width=110)

    # ── Giant wordmark via pyfiglet ───────────────────────────────────────────
    raw = pyfiglet.figlet_format("dotmd", font="speed")
    wm_lines = raw.splitlines()
    while wm_lines and not wm_lines[-1].strip():
        wm_lines.pop()

    wordmark = Text(justify="left")
    wm_colours = ["bold bright_cyan", "bold cyan", "bold bright_blue", "bold blue", "bold bright_cyan"]
    for i, line in enumerate(wm_lines):
        wordmark.append(line + "\n", style=wm_colours[i % len(wm_colours)])

    # ── Description text ──────────────────────────────────────────────────────
    desc = Text()
    desc.append("Like Docker Hub, but for ", style="white")
    desc.append(".md", style="bold bright_cyan")
    desc.append(" files.\n\n", style="white")

    desc.append("Fetch and install the instruction files\n", style="dim white")
    desc.append("that power your AI coding assistants.\n\n", style="dim white")

    tools = ["Cursor", "Windsurf", "Claude", "Copilot", "Cline", "Aider"]
    desc.append("Works with ", style="dim white")
    for j, tool in enumerate(tools):
        desc.append(tool, style="bold bright_blue")
        if j < len(tools) - 1:
            desc.append("  ", style="dim white")
    desc.append("\nand more.\n\n", style="dim white")

    desc.append("Quick start\n", style="bold white")
    desc.append("─" * 28 + "\n", style="dim blue")
    for cmd, note in [
        ("dotmd list", "browse the registry"),
        ("dotmd search <query>", "find rules"),
        ("dotmd get <user>/<rule>", "install a rule"),
        ("dotmd info <user>/<rule>", "inspect a rule"),
    ]:
        desc.append("  $ ", style="dim white")
        desc.append(f"{cmd:<24}", style="bold bright_cyan")
        desc.append(f"  {note}\n", style="dim white")

    desc.append("\n")
    desc.append("  ● ", style="bold bright_blue")
    desc.append("mydotmd.io", style="bold white")
    desc.append("  ·  ", style="dim white")
    desc.append("github.com/dotmd-cli/dotmd-cli", style="dim white")

    # ── Tagline under wordmark ────────────────────────────────────────────────
    tagline = Text()
    tagline.append("  The open registry for AI coding assistant rules  ", style="dim white")

    # ── Right column: wordmark + tagline + description ────────────────────────
    right = Text()
    right.append_text(wordmark)
    right.append_text(tagline)
    right.append("\n\n")
    right.append_text(desc)

    # ── Two-column grid: mascot left, content right ───────────────────────────
    grid = Table.grid(expand=True, padding=(0, 1))
    grid.add_column(width=42)   # mascot — fixed width
    grid.add_column()            # content — fills remaining space
    grid.add_row(_mascot_text(), right)

    c.print(
        Panel(
            grid,
            border_style="bright_blue",
            padding=(1, 2),
        )
    )

    return buf.getvalue()

# Made with Bob
