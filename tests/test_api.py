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

    def fake_get(url, headers, params, timeout):
        assert params["username"] == "eq.dotmd"
        return DummyResponse(data=[{"user_id": "user-123"}])

    monkeypatch.setattr("dotmd.api.requests.get", fake_get)

    assert api.resolve_username("dotmd") == "user-123"


def test_get_rule(monkeypatch):
    api = DotmdAPI()

    def fake_get(url, headers, params, timeout):
        assert params["title"] == "ilike.react-best-practices"
        return DummyResponse(data=[{"content": "# hello", "format_type": "claude.md"}])

    monkeypatch.setattr("dotmd.api.requests.get", fake_get)

    rule = api.get_rule("user-123", "react-best-practices")
    assert rule.content == "# hello"
    assert rule.format_type == "claude.md"


def test_api_error_response(monkeypatch):
    api = DotmdAPI()

    def fake_get(url, headers, params, timeout):
        return DummyResponse(status_code=500, text="boom")

    monkeypatch.setattr("dotmd.api.requests.get", fake_get)

    try:
        api.resolve_username("dotmd")
        assert False, "expected DotmdAPIError"
    except DotmdAPIError as exc:
        assert "API request failed" in str(exc)


def test_search_rules_uses_all_keywords_and_hydrates_username(monkeypatch):
    api = DotmdAPI()

    def fake_get(url, headers, params, timeout):
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
