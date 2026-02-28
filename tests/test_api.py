import requests

from dotmd.api import DotmdAPI, DotmdAPIError


class DummyResponse:
    def __init__(self, status_code=200, data=None, text=""):
        self.status_code = status_code
        self._data = data if data is not None else []
        self.text = text

    def json(self):
        return self._data


def test_resolve_username(monkeypatch):
    api = DotmdAPI()

    def fake_get(url, headers=None, params=None, timeout=None):
        assert params["username"] == "eq.dotmd"
        return DummyResponse(data=[{"user_id": "user-123"}])

    monkeypatch.setattr("dotmd.api.requests.get", fake_get)

    assert api.resolve_username("dotmd") == "user-123"


def test_get_rule(monkeypatch):
    api = DotmdAPI()

    def fake_get(url, headers=None, params=None, timeout=None):
        assert params["title"] == "ilike.react-best-practices"
        return DummyResponse(data=[{"content": "# hello", "format_type": "claude.md"}])

    monkeypatch.setattr("dotmd.api.requests.get", fake_get)

    rule = api.get_rule("user-123", "react-best-practices")
    assert rule.content == "# hello"
    assert rule.format_type == "claude.md"


def test_get_rule_tries_md_variant(monkeypatch):
    api = DotmdAPI()
    calls = []

    def fake_get(url, headers=None, params=None, timeout=None):
        calls.append(params["title"])
        if params["title"] == "ilike.react-best-practices":
            return DummyResponse(data=[])
        if params["title"] == "ilike.react-best-practices.md":
            return DummyResponse(data=[{"content": "# hello", "format_type": "claude.md"}])
        return DummyResponse(data=[])

    monkeypatch.setattr("dotmd.api.requests.get", fake_get)
    rule = api.get_rule("user-123", "react-best-practices")
    assert rule.content == "# hello"
    assert "ilike.react-best-practices" in calls
    assert "ilike.react-best-practices.md" in calls


def test_api_error_response(monkeypatch):
    api = DotmdAPI()

    def fake_get(url, headers=None, params=None, timeout=None):
        return DummyResponse(status_code=500, text="boom")

    monkeypatch.setattr("dotmd.api.requests.get", fake_get)

    try:
        api.resolve_username("dotmd")
        assert False, "expected DotmdAPIError"
    except DotmdAPIError as exc:
        assert "API request failed" in str(exc)


def test_search_rules_uses_all_keywords_and_hydrates_username(monkeypatch):
    api = DotmdAPI()

    def fake_get(url, headers=None, params=None, timeout=None):
        if url.endswith("/rules"):
            assert params["title"] == "ilike.%react%typescript%performance%"
            return DummyResponse(
                data=[
                    {
                        "title": "react-typescript-performance",
                        "format_type": "claude.md",
                        "user_id": "user-123",
                    }
                ]
            )

        if url.endswith("/profiles"):
            assert params["user_id"] == "in.(user-123)"
            return DummyResponse(data=[{"user_id": "user-123", "username": "dotmd"}])

        return DummyResponse(status_code=404, text="not found")

    monkeypatch.setattr("dotmd.api.requests.get", fake_get)

    rows = api.search_rules(["react", "typescript", "performance"])

    assert len(rows) == 1
    assert rows[0]["title"] == "react-typescript-performance"
    assert rows[0]["username"] == "dotmd"


def test_api_uses_env_key_and_base_url(monkeypatch):
    monkeypatch.setenv("DOTMD_SUPABASE_ANON_KEY", "env-key")
    monkeypatch.setenv("DOTMD_SUPABASE_BASE_URL", "https://example.supabase.co/rest/v1")

    api = DotmdAPI()

    assert api.base_url == "https://example.supabase.co/rest/v1"
    assert api.headers["apikey"] == "env-key"
    assert api.headers["Authorization"] == "Bearer env-key"


def test_api_defaults_to_no_auth_headers(monkeypatch):
    monkeypatch.delenv("DOTMD_SUPABASE_ANON_KEY", raising=False)
    monkeypatch.delenv("DOTMD_API_KEY", raising=False)

    api = DotmdAPI()

    assert api.headers == {}


def test_fallback_discovers_supabase_base_url_on_network_error(monkeypatch):
    monkeypatch.delenv("DOTMD_SUPABASE_BASE_URL", raising=False)
    monkeypatch.delenv("DOTMD_BASE_URL", raising=False)

    api = DotmdAPI()

    def fake_get(url, headers=None, params=None, timeout=None):
        if url == "https://xxdzzzloqgdexwlkljbi.supabase.co/rest/v1/profiles":
            raise requests.RequestException("dns failure")

        if url == "https://mydotmd.io":
            return DummyResponse(text='<script src="/assets/app.js"></script>')

        if url == "https://mydotmd.io/assets/app.js":
            return DummyResponse(
                text='window.__CFG__="https:\\/\\/newprojectref.supabase.co\\/rest\\/v1";'
            )

        if url == "https://newprojectref.supabase.co/rest/v1/profiles":
            assert params["username"] == "eq.dotmd"
            return DummyResponse(data=[{"user_id": "user-999"}])

        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr("dotmd.api.requests.get", fake_get)

    assert api.resolve_username("dotmd") == "user-999"
    assert api.base_url == "https://newprojectref.supabase.co/rest/v1"


def test_fallback_discovers_anon_key_on_missing_key_error(monkeypatch):
    monkeypatch.delenv("DOTMD_SUPABASE_ANON_KEY", raising=False)
    monkeypatch.delenv("DOTMD_API_KEY", raising=False)

    api = DotmdAPI()
    anon_jwt = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJpc3MiOiJzdXBhYmFzZSIsInJvbGUiOiJhbm9uIn0."
        "AAAAAAAAAAAA"
    )

    def fake_get(url, headers=None, params=None, timeout=None):
        if url == "https://xxdzzzloqgdexwlkljbi.supabase.co/rest/v1/profiles":
            if headers and headers.get("apikey") == anon_jwt:
                return DummyResponse(data=[{"user_id": "user-777"}])
            return DummyResponse(
                status_code=401,
                text='{"message":"No API key found in request"}',
            )

        if url == "https://mydotmd.io":
            return DummyResponse(text='<script src="/assets/app.js"></script>')

        if url == "https://mydotmd.io/assets/app.js":
            return DummyResponse(text=f'window.__ANON__ = "{anon_jwt}";')

        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr("dotmd.api.requests.get", fake_get)

    assert api.resolve_username("dotmd") == "user-777"
    assert api.headers.get("apikey") == anon_jwt


def test_list_rules_without_username_hydrates_usernames(monkeypatch):
    api = DotmdAPI()

    def fake_get(url, headers=None, params=None, timeout=None):
        if url.endswith("/rules"):
            return DummyResponse(
                data=[
                    {
                        "title": "react-best-practices",
                        "format_type": "claude.md",
                        "user_id": "user-123",
                    }
                ]
            )

        if url.endswith("/profiles"):
            assert params["user_id"] == "in.(user-123)"
            return DummyResponse(data=[{"user_id": "user-123", "username": "dotmd"}])

        return DummyResponse(status_code=404, text="not found")

    monkeypatch.setattr("dotmd.api.requests.get", fake_get)

    rows = api.list_rules()
    assert len(rows) == 1
    assert rows[0]["title"] == "react-best-practices"
    assert rows[0]["username"] == "dotmd"
