from pathlib import Path

from typer.testing import CliRunner

from dotmd.cli import app

runner = CliRunner()


class StubAPI:
    def resolve_username(self, username):
        assert username == "dotmd"
        return "user-123"

    def get_rule(self, user_id, title):
        assert user_id == "user-123"
        assert title == "react-best-practices"

        class Rule:
            content = "# React Best Practices"
            format_type = "claude.md"

        return Rule()

    def search_rules(self, keywords, limit=20):
        assert keywords == ["react", "typescript", "performance"]
        return [
            {
                "title": "react-best-practices",
                "format_type": "claude.md",
                "username": "dotmd",
            }
        ]

    def list_rules(self, username, limit=100):
        assert username == "dotmd"
        return [{"title": "react-best-practices", "format_type": "claude.md"}]


def test_get_command_writes_file(monkeypatch):
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["get", "dotmd/react-best-practices.md"])
        assert result.exit_code == 0
        assert "Saved dotmd/react-best-practices.md" in result.stdout

        output = Path("CLAUDE.md")
        assert output.exists()
        assert "# React Best Practices" in output.read_text(encoding="utf-8")


def test_search_command(monkeypatch):
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    result = runner.invoke(app, ["search", "react", "typescript", "performance"])
    assert result.exit_code == 0
    assert "dotmd/react-best-practices" in result.stdout


def test_list_command(monkeypatch):
    monkeypatch.setattr("dotmd.cli.DotmdAPI", StubAPI)

    result = runner.invoke(app, ["list", "dotmd"])
    assert result.exit_code == 0
    assert "Rules for dotmd" in result.stdout
