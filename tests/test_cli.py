"""Tests for the dotmd CLI."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import patch

from typer.testing import CliRunner

from dotmd.cli import app

runner = CliRunner(env={"NO_COLOR": "1", "FORCE_COLOR": "0"})


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


# ── Stub API ──────────────────────────────────────────────────────────────────


class StubAPI:
    def resolve_username(self, username: str) -> str:
        assert username == "dotmd"
        return "user-123"

    def get_rule(self, user_id: str, title: str) -> Any:
        assert user_id == "user-123"
        assert title in {"react-best-practices", "react-best-practices.md"}

        class Rule:
            content = "# React Best Practices"
            format_type = "claude.md"

        return Rule()

    def search_rules(self, keywords: Any, limit: int = 20) -> List[Dict[str, Any]]:
        assert keywords == ["react", "typescript", "performance"]
        assert limit == 20
        return [
            {
                "title": "react-best-practices",
                "format_type": "claude.md",
                "username": "dotmd",
            }
        ]

    def list_rules(self, username: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        assert limit == 100
        if username is None:
            return [
                {
                    "title": "react-best-practices",
                    "format_type": "claude.md",
                    "username": "dotmd",
                }
            ]
        assert username == "dotmd"
        return [{"title": "react-best-practices", "format_type": "claude.md"}]


# ── get command ───────────────────────────────────────────────────────────────


def test_get_command_writes_file(monkeypatch: Any) -> None:
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["get", "dotmd/react-best-practices.md"])
        assert result.exit_code == 0, result.output
        assert "Saved" in result.stdout or "react-best-practices" in result.stdout

        output = Path("CLAUDE.md")
        assert output.exists()
        assert "# React Best Practices" in output.read_text(encoding="utf-8")


def test_get_command_supports_bare_title_with_username_option(monkeypatch: Any) -> None:
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["get", "react-best-practices.md", "--username", "dotmd"],
        )
        assert result.exit_code == 0, result.output
        assert Path("CLAUDE.md").exists()


def test_get_command_bare_title_defaults_to_dotmd_namespace(monkeypatch: Any) -> None:
    """dotmd get <title> should default to dotmd/<title> without any search call."""
    class NoSearchStubAPI(StubAPI):
        def search_rules(self, keywords: Any, limit: int = 20) -> List[Dict[str, Any]]:
            raise AssertionError("search_rules should not be called for bare title")

    monkeypatch.setattr("dotmd.cli.DotmdAPI", NoSearchStubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["get", "react-best-practices.md"])
        assert result.exit_code == 0, result.output
        assert Path("CLAUDE.md").exists()


def test_get_command_bare_title_shows_resolved_namespace(monkeypatch: Any) -> None:
    """dotmd get <title> output should show dotmd/<title> in the success message."""
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["get", "react-best-practices.md"])
        assert result.exit_code == 0, result.output
        assert "dotmd/react-best-practices" in result.stdout
        assert Path("CLAUDE.md").exists()


def test_get_command_tool_arg_cursor(monkeypatch: Any) -> None:
    """dotmd get <rule> cursor  →  writes to .cursorrules regardless of registry format."""
    class CursorStubAPI(StubAPI):
        def get_rule(self, user_id: str, title: str) -> Any:
            class Rule:
                content = "# React Best Practices"
                format_type = "claude.md"  # registry says claude.md
            return Rule()

    monkeypatch.setattr("dotmd.cli.DotmdAPI", CursorStubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["get", "dotmd/react-best-practices", "cursor"])
        assert result.exit_code == 0, result.output
        # Should write to .cursorrules, NOT CLAUDE.md
        assert Path(".cursorrules").exists()
        assert not Path("CLAUDE.md").exists()
        assert "# React Best Practices" in Path(".cursorrules").read_text(encoding="utf-8")


def test_get_command_tool_arg_windsurf(monkeypatch: Any) -> None:
    """dotmd get <rule> windsurf  →  writes to .windsurfrules."""
    class WindsurfStubAPI(StubAPI):
        def get_rule(self, user_id: str, title: str) -> Any:
            class Rule:
                content = "# React Best Practices"
                format_type = "claude.md"
            return Rule()

    monkeypatch.setattr("dotmd.cli.DotmdAPI", WindsurfStubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["get", "dotmd/react-best-practices", "windsurf"])
        assert result.exit_code == 0, result.output
        assert Path(".windsurfrules").exists()


def test_get_command_md_format_writes_to_dotmd_subdir(monkeypatch: Any) -> None:
    """md format rules write to .dotmd/<title>.md, not AGENTS.md."""
    class MdStubAPI(StubAPI):
        def get_rule(self, user_id: str, title: str) -> Any:
            class Rule:
                content = "# CLI UX Guidelines"
                format_type = "md"
            return Rule()

    monkeypatch.setattr("dotmd.cli.DotmdAPI", MdStubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["get", "dotmd/cli-ux"])
        assert result.exit_code == 0, result.output
        expected = Path(".dotmd/cli-ux.md")
        assert expected.exists(), f"Expected {expected} to exist"
        assert "# CLI UX Guidelines" in expected.read_text(encoding="utf-8")
        assert not Path("AGENTS.md").exists(), "AGENTS.md should not be created for md format"


def test_get_command_md_format_multiple_rules_no_overwrite(monkeypatch: Any) -> None:
    """Multiple md format rules each get their own file under .dotmd/."""
    titles_written: list = []

    class MultiMdStubAPI:
        def resolve_username(self, username: str) -> str:
            return "user-123"

        def get_rule(self, user_id: str, title: str) -> Any:
            titles_written.append(title)

            class Rule:
                content = f"# {title}"
                format_type = "md"
            return Rule()

    monkeypatch.setattr("dotmd.cli.DotmdAPI", MultiMdStubAPI)

    with runner.isolated_filesystem():
        for rule in ["cli-ux", "testing", "git"]:
            result = runner.invoke(app, ["get", f"dotmd/{rule}"])
            assert result.exit_code == 0, result.output

        assert Path(".dotmd/cli-ux.md").exists()
        assert Path(".dotmd/testing.md").exists()
        assert Path(".dotmd/git.md").exists()
        assert "# cli-ux" in Path(".dotmd/cli-ux.md").read_text(encoding="utf-8")
        assert "# testing" in Path(".dotmd/testing.md").read_text(encoding="utf-8")
        assert "# git" in Path(".dotmd/git.md").read_text(encoding="utf-8")


def test_get_command_tool_arg_invalid(monkeypatch: Any) -> None:
    """dotmd get <rule> badtool  →  exits with error."""
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)
    result = runner.invoke(app, ["get", "dotmd/react-best-practices", "badtool"])
    assert result.exit_code == 2
    assert "unknown tool" in result.stderr.lower()


def test_get_command_tool_arg_dry_run(monkeypatch: Any) -> None:
    """dotmd get <rule> cursor --dry-run  →  shows .cursorrules destination."""
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["get", "dotmd/react-best-practices", "cursor", "--dry-run"])
        assert result.exit_code == 0, result.output
        assert ".cursorrules" in result.stdout
        assert not Path(".cursorrules").exists()


def test_get_command_refuses_overwrite_without_force(monkeypatch: Any) -> None:
    """In TTY mode (interactive), overwrite is blocked without --force."""
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)
    # Simulate a TTY so auto-force does NOT kick in
    monkeypatch.setattr("dotmd.cli._is_tty", lambda: True)

    with runner.isolated_filesystem():
        Path("CLAUDE.md").write_text("existing", encoding="utf-8")
        result = runner.invoke(app, ["get", "dotmd/react-best-practices.md"])
        assert result.exit_code == 2
        assert "Use --force to overwrite" in result.stderr


def test_get_command_auto_force_in_non_tty(monkeypatch: Any) -> None:
    """In non-TTY mode (LLM agents, scripts), overwrite happens automatically."""
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)
    # CliRunner is non-TTY by default — auto-force should kick in

    with runner.isolated_filesystem():
        Path("CLAUDE.md").write_text("existing", encoding="utf-8")
        result = runner.invoke(app, ["get", "dotmd/react-best-practices.md"])
        assert result.exit_code == 0, result.output
        assert "# React Best Practices" in Path("CLAUDE.md").read_text(encoding="utf-8")


def test_get_command_print_flag(monkeypatch: Any) -> None:
    """--print outputs content to stdout without writing a file."""
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["get", "dotmd/react-best-practices.md", "--print"])
        assert result.exit_code == 0, result.output
        assert "# React Best Practices" in result.stdout
        # No file should be written
        assert not Path("CLAUDE.md").exists()


def test_get_command_json_includes_content(monkeypatch: Any) -> None:
    """--json output includes 'content' field with the full rule text."""
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["get", "dotmd/react-best-practices.md", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.stdout)
        assert data["status"] == "saved"
        assert "content" in data
        assert "# React Best Practices" in data["content"]


def test_get_command_dry_run_json_includes_content(monkeypatch: Any) -> None:
    """--dry-run --json output includes 'content' field."""
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(
            app, ["get", "dotmd/react-best-practices.md", "--dry-run", "--json"]
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.stdout)
        assert data["dry_run"] is True
        assert "content" in data
        assert "# React Best Practices" in data["content"]
        assert not Path("CLAUDE.md").exists()


def test_get_command_force_overwrites(monkeypatch: Any) -> None:
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    with runner.isolated_filesystem():
        Path("CLAUDE.md").write_text("existing", encoding="utf-8")
        result = runner.invoke(app, ["get", "dotmd/react-best-practices.md", "--force"])
        assert result.exit_code == 0, result.output
        assert "# React Best Practices" in Path("CLAUDE.md").read_text(encoding="utf-8")


def test_get_command_supports_custom_output(monkeypatch: Any) -> None:
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["get", "dotmd/react-best-practices.md", "--output", "custom/AGENTS.md"],
        )
        assert result.exit_code == 0, result.output
        assert Path("custom/AGENTS.md").exists()


def test_get_command_dry_run(monkeypatch: Any) -> None:
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["get", "dotmd/react-best-practices.md", "--dry-run"])
        assert result.exit_code == 0, result.output
        assert "destination" in result.stdout.lower()
        assert "CLAUDE.md" in result.stdout
        # File should NOT be written
        assert not Path("CLAUDE.md").exists()


def test_get_command_dry_run_json(monkeypatch: Any) -> None:
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(
            app, ["get", "dotmd/react-best-practices.md", "--dry-run", "--json"]
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.stdout)
        assert data["dry_run"] is True
        assert data["format_type"] == "claude.md"
        assert "CLAUDE.md" in data["destination"]
        assert not Path("CLAUDE.md").exists()


def test_get_command_json_output(monkeypatch: Any) -> None:
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["get", "dotmd/react-best-practices.md", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.stdout)
        assert data["status"] == "saved"
        assert data["format_type"] == "claude.md"
        assert data["username"] == "dotmd"


def test_get_command_quiet(monkeypatch: Any) -> None:
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["get", "dotmd/react-best-practices.md", "--quiet"])
        assert result.exit_code == 0, result.output
        assert result.stdout.strip() == ""


def test_get_command_rejects_both_slash_and_username(monkeypatch: Any) -> None:
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    result = runner.invoke(
        app, ["get", "dotmd/react-best-practices", "--username", "dotmd"]
    )
    assert result.exit_code == 2
    assert "not both" in result.stderr.lower()


# ── search command ────────────────────────────────────────────────────────────


def test_search_command(monkeypatch: Any) -> None:
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    result = runner.invoke(app, ["search", "react", "typescript", "performance"])
    assert result.exit_code == 0, result.output
    assert "dotmd/react-best-practices" in result.stdout


def test_search_command_json(monkeypatch: Any) -> None:
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    result = runner.invoke(app, ["search", "react", "typescript", "performance", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    assert data["count"] == 1
    assert data["results"][0]["username"] == "dotmd"


def test_search_command_honors_limit(monkeypatch: Any) -> None:
    class LimitStubAPI(StubAPI):
        def search_rules(self, keywords: Any, limit: int = 20) -> List[Dict[str, Any]]:
            assert limit == 7
            return super().search_rules(keywords, limit=20)

    monkeypatch.setattr("dotmd.cli.DotmdAPI", LimitStubAPI)
    result = runner.invoke(app, ["search", "react", "typescript", "performance", "--limit", "7"])
    assert result.exit_code == 0, result.output


def test_search_command_no_results(monkeypatch: Any) -> None:
    class EmptyStubAPI(StubAPI):
        def search_rules(self, keywords: Any, limit: int = 20) -> List[Dict[str, Any]]:
            return []

    monkeypatch.setattr("dotmd.cli.DotmdAPI", EmptyStubAPI)
    result = runner.invoke(app, ["search", "xyzzy"])
    assert result.exit_code == 0
    assert "No matching rules found" in result.stdout


# ── list command ──────────────────────────────────────────────────────────────


def test_list_command_with_username(monkeypatch: Any) -> None:
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    result = runner.invoke(app, ["list", "dotmd"])
    assert result.exit_code == 0, result.output
    assert "Rules for dotmd" in result.stdout


def test_list_command_without_username(monkeypatch: Any) -> None:
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0, result.output
    assert "All rules" in result.stdout
    assert "dotmd/react-best-practices" in result.stdout


def test_list_command_json(monkeypatch: Any) -> None:
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    result = runner.invoke(app, ["list", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    assert data["count"] == 1
    assert data["username"] is None


def test_list_command_honors_limit(monkeypatch: Any) -> None:
    class LimitStubAPI(StubAPI):
        def list_rules(self, username: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
            assert limit == 3
            return super().list_rules(username=username, limit=100)

    monkeypatch.setattr("dotmd.cli.DotmdAPI", LimitStubAPI)
    result = runner.invoke(app, ["list", "--limit", "3"])
    assert result.exit_code == 0, result.output


def test_list_command_no_results(monkeypatch: Any) -> None:
    class EmptyStubAPI(StubAPI):
        def list_rules(self, username: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
            return []

    monkeypatch.setattr("dotmd.cli.DotmdAPI", EmptyStubAPI)
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No rules found" in result.stdout


# ── info command ──────────────────────────────────────────────────────────────


def test_info_command_plain_shows_version() -> None:
    result = runner.invoke(app, ["info", "--plain"])
    assert result.exit_code == 0, result.output
    assert "Version:" in result.stdout
    assert "0.1.1" in result.stdout
    assert "Registry:" in result.stdout
    assert "mydotmd.io" in result.stdout


def test_info_command_shows_formats() -> None:
    result = runner.invoke(app, ["info", "--plain"])
    assert result.exit_code == 0, result.output
    assert "claude.md" in result.stdout
    assert "cursorrules" in result.stdout
    assert "copilot" in result.stdout


def test_info_command_json() -> None:
    result = runner.invoke(app, ["info", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    assert data["version"] == "0.1.1"
    assert "base_url" in data["config"]
    assert "formats" in data
    assert "claude.md" in data["formats"]


def test_info_command_banner_skipped_in_non_tty() -> None:
    """Banner should not render when stdout is not a TTY (e.g. piped to LLM)."""
    # CliRunner uses a non-TTY by default
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0, result.output
    # The doom-font wordmark should NOT appear in non-TTY output
    assert "dotmd" in result.stdout  # version/registry info still present
    assert "Version:" in result.stdout


# ── version flag ──────────────────────────────────────────────────────────────


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0, result.output
    assert "dotmd 0.1.1" in result.stdout


def test_version_flag_short() -> None:
    result = runner.invoke(app, ["-V"])
    assert result.exit_code == 0, result.output
    assert "dotmd 0.1.1" in result.stdout


# ── help ──────────────────────────────────────────────────────────────────────


def test_help_shows_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0, result.output
    for cmd in ["get", "search", "list", "info"]:
        assert cmd in result.stdout


def test_get_help_shows_examples() -> None:
    result = runner.invoke(app, ["get", "--help"])
    assert result.exit_code == 0, result.output
    stdout = _strip_ansi(result.stdout)
    assert "--dry-run" in stdout
    assert "--force" in stdout
    assert "--output" in stdout


def test_search_help() -> None:
    result = runner.invoke(app, ["search", "--help"])
    assert result.exit_code == 0, result.output
    assert "--limit" in _strip_ansi(result.stdout)


def test_list_help() -> None:
    result = runner.invoke(app, ["list", "--help"])
    assert result.exit_code == 0, result.output
    assert "--limit" in _strip_ansi(result.stdout)

# ── find command ─────────────────────────────────────────────────────────────


class FindStubAPI:
    """Stub API for dotmd find tests."""

    def resolve_username(self, username: str) -> str:
        assert username == "dotmd"
        return "user-123"

    def get_rule(self, user_id: str, title: str) -> Any:
        assert user_id == "user-123"

        class Rule:
            content = "# CLI UX Guidelines"
            format_type = "md"

        return Rule()

    def search_rules(self, keywords: Any, limit: int = 5) -> List[Dict[str, Any]]:
        return [
            {
                "title": "cli-ux",
                "format_type": "md",
                "username": "dotmd",
            }
        ]

    def list_rules(self, username: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return []


def test_find_command_writes_to_dotmd_subdir(monkeypatch: Any) -> None:
    """dotmd find <description> writes the best match to .dotmd/<title>.md."""
    monkeypatch.setattr("dotmd.cli.DotmdAPI", FindStubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["find", "cli", "ux", "best", "practices"])
        assert result.exit_code == 0, result.output
        expected = Path(".dotmd/cli-ux.md")
        assert expected.exists(), f"Expected {expected} to exist"
        assert "# CLI UX Guidelines" in expected.read_text(encoding="utf-8")


def test_find_command_print_flag(monkeypatch: Any) -> None:
    """dotmd find --print outputs content to stdout without writing a file."""
    monkeypatch.setattr("dotmd.cli.DotmdAPI", FindStubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["find", "cli", "ux", "--print"])
        assert result.exit_code == 0, result.output
        assert "# CLI UX Guidelines" in result.stdout
        assert not Path(".dotmd/cli-ux.md").exists()


def test_find_command_json_includes_content_and_candidates(monkeypatch: Any) -> None:
    """dotmd find --json includes content and candidates fields."""
    monkeypatch.setattr("dotmd.cli.DotmdAPI", FindStubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["find", "cli", "ux", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.stdout)
        assert data["status"] == "saved"
        assert "content" in data
        assert "# CLI UX Guidelines" in data["content"]
        assert "candidates" in data
        assert isinstance(data["candidates"], list)
        assert data["title"] == "cli-ux"
        assert data["username"] == "dotmd"
        assert ".dotmd/cli-ux.md" in data["destination"]


def test_find_command_dry_run(monkeypatch: Any) -> None:
    """dotmd find --dry-run shows destination without writing."""
    monkeypatch.setattr("dotmd.cli.DotmdAPI", FindStubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["find", "cli", "ux", "--dry-run"])
        assert result.exit_code == 0, result.output
        assert ".dotmd" in result.stdout
        assert not Path(".dotmd/cli-ux.md").exists()


def test_find_command_dry_run_json(monkeypatch: Any) -> None:
    """dotmd find --dry-run --json includes content and would_overwrite."""
    monkeypatch.setattr("dotmd.cli.DotmdAPI", FindStubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["find", "cli", "ux", "--dry-run", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.stdout)
        assert data["dry_run"] is True
        assert "content" in data
        assert "candidates" in data
        assert data["would_overwrite"] is False
        assert not Path(".dotmd/cli-ux.md").exists()


def test_find_command_no_results(monkeypatch: Any) -> None:
    """dotmd find exits with error when no rules match."""

    class EmptyFindStubAPI(FindStubAPI):
        def search_rules(self, keywords: Any, limit: int = 5) -> List[Dict[str, Any]]:
            return []

    monkeypatch.setattr("dotmd.cli.DotmdAPI", EmptyFindStubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["find", "xyzzy", "nonexistent"])
        assert result.exit_code == 1
        assert "No rules found" in result.stderr


def test_find_command_no_results_json(monkeypatch: Any) -> None:
    """dotmd find --json emits not_found status when no rules match."""

    class EmptyFindStubAPI(FindStubAPI):
        def search_rules(self, keywords: Any, limit: int = 5) -> List[Dict[str, Any]]:
            return []

    monkeypatch.setattr("dotmd.cli.DotmdAPI", EmptyFindStubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["find", "xyzzy", "--json"])
        assert result.exit_code == 1
        data = json.loads(result.stdout)
        assert data["status"] == "not_found"


def test_find_command_auto_force_in_non_tty(monkeypatch: Any) -> None:
    """In non-TTY mode, dotmd find auto-overwrites existing .dotmd/<title>.md."""
    monkeypatch.setattr("dotmd.cli.DotmdAPI", FindStubAPI)

    with runner.isolated_filesystem():
        Path(".dotmd").mkdir()
        Path(".dotmd/cli-ux.md").write_text("existing", encoding="utf-8")
        result = runner.invoke(app, ["find", "cli", "ux"])
        assert result.exit_code == 0, result.output
        assert "# CLI UX Guidelines" in Path(".dotmd/cli-ux.md").read_text(encoding="utf-8")


def test_find_command_refuses_overwrite_in_tty(monkeypatch: Any) -> None:
    """In TTY mode, dotmd find blocks overwrite without --force."""
    monkeypatch.setattr("dotmd.cli.DotmdAPI", FindStubAPI)
    monkeypatch.setattr("dotmd.cli._is_tty", lambda: True)

    with runner.isolated_filesystem():
        Path(".dotmd").mkdir()
        Path(".dotmd/cli-ux.md").write_text("existing", encoding="utf-8")
        result = runner.invoke(app, ["find", "cli", "ux"])
        assert result.exit_code == 2
        assert "Use --force to overwrite" in result.stderr


def test_find_command_custom_output(monkeypatch: Any) -> None:
    """dotmd find --output writes to the specified path."""
    monkeypatch.setattr("dotmd.cli.DotmdAPI", FindStubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["find", "cli", "ux", "--output", "custom/cli-ux.md"])
        assert result.exit_code == 0, result.output
        assert Path("custom/cli-ux.md").exists()
        assert "# CLI UX Guidelines" in Path("custom/cli-ux.md").read_text(encoding="utf-8")


def test_find_command_quiet(monkeypatch: Any) -> None:
    """dotmd find --quiet suppresses non-error output."""
    monkeypatch.setattr("dotmd.cli.DotmdAPI", FindStubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["find", "cli", "ux", "--quiet"])
        assert result.exit_code == 0, result.output
        assert result.stdout.strip() == ""


def test_find_help_shows_options() -> None:
    result = runner.invoke(app, ["find", "--help"])
    assert result.exit_code == 0, result.output
    stdout = _strip_ansi(result.stdout)
    assert "--dry-run" in stdout
    assert "--print" in stdout
    assert "--json" in stdout
    assert "--output" in stdout


# Made with Bob
