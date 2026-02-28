"""Supabase API helpers for dotmd CLI."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import json
import os
import re
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urljoin

import requests

DEFAULT_BASE_URL = "https://xxdzzzloqgdexwlkljbi.supabase.co/rest/v1"
DEFAULT_REGISTRY_SITE_URL = "https://mydotmd.io"
SUPABASE_REST_RE = re.compile(r"https://[a-z0-9-]+\.supabase\.co/rest/v1", re.IGNORECASE)
SCRIPT_SRC_RE = re.compile(r"""<script[^>]+src=["']([^"']+)["']""", re.IGNORECASE)
JWT_RE = re.compile(
    r"eyJ[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{6,}",
    re.IGNORECASE,
)


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
        self.registry_site_url = (
            os.getenv("DOTMD_REGISTRY_SITE_URL") or DEFAULT_REGISTRY_SITE_URL
        ).rstrip("/")
        self._base_url_is_explicit = bool(
            base_url or os.getenv("DOTMD_SUPABASE_BASE_URL") or os.getenv("DOTMD_BASE_URL")
        )
        self._anon_key_is_explicit = bool(
            anon_key or os.getenv("DOTMD_SUPABASE_ANON_KEY") or os.getenv("DOTMD_API_KEY")
        )
        self._discovery_attempted = False
        self._key_discovery_attempted = False
        self.headers: Dict[str, str] = {}
        if configured_anon_key:
            self._set_auth_headers(configured_anon_key)

    def _set_auth_headers(self, anon_key: str) -> None:
        self.headers = {
            "apikey": anon_key,
            "Authorization": f"Bearer {anon_key}",
        }

    @staticmethod
    def _decode_jwt_payload(token: str) -> Optional[Dict[str, Any]]:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        payload_part = parts[1]
        padding = "=" * (-len(payload_part) % 4)
        try:
            decoded = base64.urlsafe_b64decode(payload_part + padding)
            payload = json.loads(decoded.decode("utf-8"))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            return None

        if isinstance(payload, dict):
            return payload
        return None

    @staticmethod
    def _extract_supabase_rest_url(text: str) -> Optional[str]:
        if not text:
            return None

        direct = SUPABASE_REST_RE.search(text)
        if direct:
            return direct.group(0)

        unescaped = text.replace("\\/", "/")
        escaped = SUPABASE_REST_RE.search(unescaped)
        if escaped:
            return escaped.group(0)

        return None

    @staticmethod
    def _extract_supabase_anon_key(text: str) -> Optional[str]:
        if not text:
            return None

        candidates = JWT_RE.findall(text)
        for candidate in candidates:
            payload = DotmdAPI._decode_jwt_payload(candidate)
            if not payload:
                continue
            if str(payload.get("iss", "")).lower() == "supabase" and str(
                payload.get("role", "")
            ).lower() == "anon":
                return candidate

        return None

    def _registry_payloads(self) -> List[str]:
        try:
            homepage = requests.get(self.registry_site_url, timeout=min(self.timeout, 10))
        except requests.RequestException:
            return []

        candidates: List[str] = [homepage.text or ""]
        for script_path in SCRIPT_SRC_RE.findall(homepage.text or "")[:8]:
            script_url = urljoin(f"{self.registry_site_url}/", script_path)
            try:
                script_response = requests.get(script_url, timeout=min(self.timeout, 10))
            except requests.RequestException:
                continue
            candidates.append(script_response.text or "")

        return candidates

    def _discover_base_url_from_registry(self) -> Optional[str]:
        for payload in self._registry_payloads():
            discovered = self._extract_supabase_rest_url(payload)
            if discovered:
                return discovered.rstrip("/")

        return None

    def _discover_anon_key_from_registry(self) -> Optional[str]:
        for payload in self._registry_payloads():
            discovered = self._extract_supabase_anon_key(payload)
            if discovered:
                return discovered

        return None

    def _try_discover_and_swap_base_url(self) -> bool:
        if self._base_url_is_explicit or self._discovery_attempted:
            return False

        self._discovery_attempted = True
        discovered = self._discover_base_url_from_registry()
        if not discovered or discovered == self.base_url:
            return False

        self.base_url = discovered
        return True

    def _try_discover_and_set_anon_key(self) -> bool:
        if self._anon_key_is_explicit or self._key_discovery_attempted:
            return False

        self._key_discovery_attempted = True
        discovered = self._discover_anon_key_from_registry()
        if not discovered:
            return False

        self._set_auth_headers(discovered)
        return True

    @staticmethod
    def _looks_like_api_key_error(status_code: int, body: str) -> bool:
        if status_code != 401:
            return False

        normalized = (body or "").lower()
        return "api key" in normalized or "apikey" in normalized

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        path = path.lstrip("/")
        url = f"{self.base_url}/{path}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            if self._try_discover_and_swap_base_url():
                retry_url = f"{self.base_url}/{path}"
                try:
                    response = requests.get(
                        retry_url, headers=self.headers, params=params, timeout=self.timeout
                    )
                except requests.RequestException as retry_exc:
                    raise DotmdAPIError(
                        f"Network error while calling {retry_url}: {retry_exc}"
                    ) from retry_exc
                url = retry_url
            else:
                raise DotmdAPIError(f"Network error while calling {url}: {exc}") from exc

        if response.status_code >= 400:
            if self._looks_like_api_key_error(response.status_code, response.text):
                if self._try_discover_and_set_anon_key():
                    retry_url = f"{self.base_url}/{path}"
                    try:
                        response = requests.get(
                            retry_url, headers=self.headers, params=params, timeout=self.timeout
                        )
                    except requests.RequestException as retry_exc:
                        raise DotmdAPIError(
                            f"Network error while calling {retry_url}: {retry_exc}"
                        ) from retry_exc
                    url = retry_url

            if self._try_discover_and_swap_base_url():
                retry_url = f"{self.base_url}/{path}"
                try:
                    retry_response = requests.get(
                        retry_url, headers=self.headers, params=params, timeout=self.timeout
                    )
                except requests.RequestException as retry_exc:
                    raise DotmdAPIError(
                        f"Network error while calling {retry_url}: {retry_exc}"
                    ) from retry_exc

                response = retry_response
                url = retry_url

            if response.status_code >= 400 and self._looks_like_api_key_error(
                response.status_code, response.text
            ):
                if self._try_discover_and_set_anon_key():
                    retry_url = f"{self.base_url}/{path}"
                    try:
                        response = requests.get(
                            retry_url, headers=self.headers, params=params, timeout=self.timeout
                        )
                    except requests.RequestException as retry_exc:
                        raise DotmdAPIError(
                            f"Network error while calling {retry_url}: {retry_exc}"
                        ) from retry_exc
                    url = retry_url

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

    @staticmethod
    def _title_candidates(title: str) -> List[str]:
        raw = title.strip()
        if not raw:
            return []

        candidates: List[str] = [raw]
        lower = raw.lower()
        if lower.endswith(".md") or lower.endswith(".txt"):
            stem = raw.rsplit(".", 1)[0]
            if stem:
                candidates.append(stem)
        else:
            candidates.append(f"{raw}.md")
            candidates.append(f"{raw}.txt")

        deduped: List[str] = []
        seen: set[str] = set()
        for item in candidates:
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

    def get_rule(self, user_id: str, title: str) -> RuleRecord:
        title_candidates = self._title_candidates(title)
        rows: List[Dict[str, Any]] = []
        for candidate in title_candidates:
            rows = self._get(
                "rules",
                params={
                    "select": "content,format_type,title",
                    "user_id": f"eq.{user_id}",
                    "title": f"ilike.{candidate}",
                    "limit": 1,
                },
            )
            if rows:
                break

        if not rows:
            search_rows = self._get(
                "rules",
                params={
                    "select": "title",
                    "user_id": f"eq.{user_id}",
                    "title": f"ilike.%{title}%",
                    "limit": 5,
                    "order": "title.asc",
                },
            )
            if search_rows:
                examples = ", ".join(str(row.get("title", "")).strip() for row in search_rows[:5])
                raise DotmdAPIError(
                    f"Rule not found for title: {title}. Close matches: {examples}"
                )
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

    def list_rules(self, username: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        if username:
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

        rows = self._get(
            "rules",
            params={
                "select": "title,format_type,user_id",
                "limit": max(1, min(limit, 200)),
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
            username_value = user_map.get(str(row.get("user_id")))
            if username_value:
                hydrated["username"] = username_value
            hydrated_rows.append(hydrated)

        return hydrated_rows
