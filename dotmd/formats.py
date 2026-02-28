"""Mappings from registry format types to local output paths."""

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


def output_path_for_format(format_type: str) -> str:
    """Return the local destination path for a given registry format type.

    Falls back to ``AGENTS.md`` for unknown or missing format types so that
    fetched content is always written somewhere useful.

    Args:
        format_type: The ``format_type`` string returned by the registry API.

    Returns:
        A relative path string suitable for writing under the current directory.
    """
    return FORMAT_TO_PATH.get((format_type or "").strip().lower(), "AGENTS.md")


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

# Made with Bob
