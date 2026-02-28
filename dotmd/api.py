"""Supabase API helpers for dotmd CLI."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Dict, List, Optional, Sequence

import requests

DEFAULT_BASE_URL = "https://xxdzzzloqgdexwlkljbi.supabase.co/rest/v1"


class DotmdAPIError(RuntimeError):
    """Raised when the dotmd backend request fails."""


@dataclass
class RuleRecord:
    content: str
    format_type: str


class DotmdAPI:
    """Thin API client for the mydotmd Supabase backend."""

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        anon_key: Optional[str] = None,
        timeout: int = 20,
    ):
        configured_base_url = (
            base_url
            or os.getenv("DOTMD_SUPABASE_BASE_URL")
            or os.getenv("DOTMD_BASE_URL")
            or DEFAULT_BASE_URL
        )
        configured_anon_key = (
            anon_key
            or os.getenv("DOTMD_SUPABASE_ANON_KEY")
            or os.getenv("DOTMD_API_KEY")
        )

        self.base_url = configured_base_url.rstrip("/")
        self.timeout = timeout
        self.headers: Dict[str, str] = {}
        if configured_anon_key:
            self.headers = {
                "apikey": configured_anon_key,
                "Authorization": f"Bearer {configured_anon_key}",
            }

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            raise DotmdAPIError(f"Network error while calling {url}: {exc}") from exc

        if response.status_code >= 400:
            raise DotmdAPIError(
                f"API request failed ({response.status_code}) for {path}: {response.text.strip()}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise DotmdAPIError(f"Invalid JSON response for {path}") from exc

        if not isinstance(payload, list):
            raise DotmdAPIError(f"Unexpected API response for {path}: {payload!r}")

        return payload

    @staticmethod
    def _normalize_keywords(keywords: Sequence[str] | str) -> List[str]:
        if isinstance(keywords, str):
            parts = keywords.split()
        else:
            parts = list(keywords)

        return [part.strip() for part in parts if part and part.strip()]

    def resolve_username(self, username: str) -> str:
        rows = self._get(
            "profiles",
            params={"select": "user_id", "username": f"eq.{username}"},
        )
        if not rows:
            raise DotmdAPIError(f"Username not found: {username}")

        user_id = rows[0].get("user_id")
        if not user_id:
            raise DotmdAPIError(f"No user_id returned for username: {username}")

        return str(user_id)

    def get_rule(self, user_id: str, title: str) -> RuleRecord:
        rows = self._get(
            "rules",
            params={
                "select": "content,format_type,title",
                "user_id": f"eq.{user_id}",
                "title": f"ilike.{title}",
                "limit": 1,
            },
        )
        if not rows:
            raise DotmdAPIError(f"Rule not found for title: {title}")

        row = rows[0]
        content = row.get("content")
        if not isinstance(content, str) or not content.strip():
            raise DotmdAPIError("Rule content was empty")

        format_type = row.get("format_type") or "agents.md"
        return RuleRecord(content=content, format_type=str(format_type))

    def search_rules(self, keywords: Sequence[str] | str, limit: int = 20) -> List[Dict[str, Any]]:
        keyword_parts = self._normalize_keywords(keywords)
        if not keyword_parts:
            raise DotmdAPIError("At least one keyword is required for search")

        pattern = f"%{'%'.join(keyword_parts)}%"
        rows = self._get(
            "rules",
            params={
                "select": "title,format_type,user_id",
                "title": f"ilike.{pattern}",
                "limit": max(1, min(limit, 100)),
                "order": "title.asc",
            },
        )

        user_ids = sorted(
            {
                str(row.get("user_id"))
                for row in rows
                if isinstance(row.get("user_id"), str) and row.get("user_id")
            }
        )
        if not user_ids:
            return rows

        profiles = self._get(
            "profiles",
            params={
                "select": "user_id,username",
                "user_id": f"in.({','.join(user_ids)})",
            },
        )
        user_map = {
            str(row.get("user_id")): str(row.get("username"))
            for row in profiles
            if isinstance(row.get("user_id"), str) and isinstance(row.get("username"), str)
        }

        hydrated_rows: List[Dict[str, Any]] = []
        for row in rows:
            hydrated = dict(row)
            username = user_map.get(str(row.get("user_id")))
            if username:
                hydrated["username"] = username
            hydrated_rows.append(hydrated)

        return hydrated_rows

    def list_rules(self, username: str, limit: int = 100) -> List[Dict[str, Any]]:
        user_id = self.resolve_username(username)
        return self._get(
            "rules",
            params={
                "select": "title,format_type",
                "user_id": f"eq.{user_id}",
                "limit": max(1, min(limit, 200)),
                "order": "title.asc",
            },
        )
