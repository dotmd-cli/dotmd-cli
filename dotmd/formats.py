"""Mappings from registry format types to output paths."""

FORMAT_TO_PATH = {
    "claude.md": "CLAUDE.md",
    "cursorrules": ".cursorrules",
    "windsurfrules": ".windsurfrules",
    "agents.md": "AGENTS.md",
    "copilot": ".github/copilot-instructions.md",
}


def output_path_for_format(format_type: str) -> str:
    """Return destination path for a format type.

    Falls back to AGENTS.md if the API returns an unknown format.
    """
    return FORMAT_TO_PATH.get((format_type or "").strip().lower(), "AGENTS.md")
