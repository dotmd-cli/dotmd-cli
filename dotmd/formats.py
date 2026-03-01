"""Mappings from registry format types to local output paths."""

from __future__ import annotations

import re

FORMAT_TO_PATH: dict[str, str] = {
    # Anthropic Claude
    "claude.md": "CLAUDE.md",
    # Cursor IDE
    "cursorrules": ".cursorrules",
    # Windsurf IDE
    "windsurfrules": ".windsurfrules",
    # OpenAI Codex / generic agents
    "agents.md": "AGENTS.md",
    # GitHub Copilot
    "copilot": ".github/copilot-instructions.md",
    # Google Gemini CLI
    "gemini": "GEMINI.md",
    # Cline (VS Code extension)
    "cline": ".clinerules",
    # Aider
    "aider": ".aider.conf.yml",
    # Continue.dev
    "continue": ".continue/config.json",
}

# Friendly tool-name aliases → format_type key in FORMAT_TO_PATH.
# Used by `dotmd get <rule> <tool>` to override the output destination.
TOOL_ALIASES: dict[str, str] = {
    # Cursor
    "cursor": "cursorrules",
    # Windsurf
    "windsurf": "windsurfrules",
    # Claude / Anthropic
    "claude": "claude.md",
    # OpenAI Codex / Agents
    "agents": "agents.md",
    "codex": "agents.md",
    "openai": "agents.md",
    # GitHub Copilot
    "copilot": "copilot",
    "github": "copilot",
    # Google Gemini
    "gemini": "gemini",
    "google": "gemini",
    # Cline
    "cline": "cline",
    # Aider
    "aider": "aider",
    # Continue.dev
    "continue": "continue",
}

#: Format type used by the official dotmd registry rules.
MD_FORMAT = "md"


def _safe_filename(title: str) -> str:
    """Sanitise a rule title into a safe filename component.

    Strips leading/trailing whitespace, lowercases, replaces spaces and
    path-unsafe characters with hyphens, and collapses repeated hyphens.
    """
    name = title.strip().lower()
    name = re.sub(r"[^\w\-]", "-", name)
    name = re.sub(r"-{2,}", "-", name)
    return name.strip("-") or "rule"


def output_path_for_format(format_type: str, title: str = "") -> str:
    """Return the local destination path for a given registry format type.

    For the ``md`` format (used by official dotmd registry rules), each rule
    is written to its own file under a ``dotmd/`` subdirectory so that
    multiple rules can coexist without overwriting each other:

        dotmd/cli-ux.md
        dotmd/testing.md
        dotmd/git.md

    All other known formats map to their canonical tool-specific paths
    (e.g. ``cursorrules`` → ``.cursorrules``).  Unknown formats fall back to
    ``AGENTS.md``.

    Args:
        format_type: The ``format_type`` string returned by the registry API.
        title: The rule title, used to derive the filename for ``md`` rules.

    Returns:
        A relative path string suitable for writing under the current directory.
    """
    fmt = (format_type or "").strip().lower()
    if fmt == MD_FORMAT:
        filename = _safe_filename(title) if title else "rule"
        return f".dotmd/{filename}.md"
    return FORMAT_TO_PATH.get(fmt, "AGENTS.md")


def resolve_tool_alias(tool: str) -> str | None:
    """Resolve a friendly tool name to a format_type key.

    Returns the format_type string if the alias is recognised, or ``None``
    if the tool name is unknown.

    Args:
        tool: A case-insensitive tool name, e.g. ``"cursor"``, ``"claude"``.

    Returns:
        A format_type key (e.g. ``"cursorrules"``) or ``None``.
    """
    return TOOL_ALIASES.get(tool.strip().lower())

