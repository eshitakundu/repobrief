"""Fetch what a brief needs from the GitHub REST API: metadata, README and recent commits."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx

API = "https://api.github.com"
README_LIMIT = 4000

REPO_PATTERN = re.compile(
    r"^(?:(?:https?://)?(?:www\.)?github\.com/|git@github\.com:)?"
    r"(?P<owner>[A-Za-z0-9-]+)/(?P<repo>[A-Za-z0-9._-]+?)(?:\.git)?(?:/.*)?$"
)


class BriefError(Exception):
    """A problem worth showing the user as a one-line message."""


@dataclass
class RepoData:
    owner: str
    repo: str
    description: str = ""
    language: str | None = None
    stars: int = 0
    license: str | None = None
    topics: list[str] = field(default_factory=list)
    pushed_at: str = ""
    archived: bool = False
    readme: str = ""
    readme_truncated: bool = False
    commits: list[tuple[str, str]] = field(default_factory=list)  # (date, first line)


def parse_repo(value: str) -> tuple[str, str]:
    """Accept a GitHub URL, an SSH remote or owner/repo shorthand."""
    match = REPO_PATTERN.match(value.strip())
    if not match:
        raise BriefError(f"Couldn't read a GitHub repository from {value!r}. Try owner/repo.")
    return match.group("owner"), match.group("repo")


class GitHub:
    def __init__(self, client: httpx.Client | None = None, token: str | None = None):
        token = token if token is not None else os.getenv("GITHUB_TOKEN", "")
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "repobrief"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.client = client or httpx.Client(timeout=20)
        self.headers = headers

    def _get(self, path: str, accept: str | None = None, **kwargs) -> httpx.Response:
        headers = {**self.headers, "Accept": accept} if accept else self.headers
        try:
            response = self.client.get(f"{API}{path}", headers=headers, **kwargs)
        except httpx.HTTPError:
            raise BriefError("Couldn't reach GitHub. Check your connection and try again.") from None
        if response.status_code in (403, 429) and response.headers.get("x-ratelimit-remaining") == "0":
            reset = response.headers.get("x-ratelimit-reset")
            when = (datetime.fromtimestamp(int(reset), tz=timezone.utc).strftime("%H:%M UTC")
                    if reset and reset.isdigit() else "later")
            raise BriefError(f"GitHub rate limit reached; it resets at {when}. "
                             "Set GITHUB_TOKEN to raise the limit from 60 to 5,000 requests an hour.")
        return response

    def fetch(self, owner: str, repo: str, commits: int = 10) -> RepoData:
        meta = self._get(f"/repos/{owner}/{repo}")
        if meta.status_code == 404:
            raise BriefError(f"{owner}/{repo} wasn't found. It may be private or misspelled.")
        meta.raise_for_status()
        info = meta.json()
        data = RepoData(
            owner=info["owner"]["login"], repo=info["name"],
            description=info.get("description") or "", language=info.get("language"),
            stars=info.get("stargazers_count", 0),
            license=(info.get("license") or {}).get("spdx_id"),
            topics=info.get("topics", []), pushed_at=(info.get("pushed_at") or "")[:10],
            archived=info.get("archived", False),
        )

        readme = self._get(f"/repos/{owner}/{repo}/readme", accept="application/vnd.github.raw")
        if readme.status_code == 200:
            data.readme = readme.text[:README_LIMIT]
            data.readme_truncated = len(readme.text) > README_LIMIT

        history = self._get(f"/repos/{owner}/{repo}/commits", params={"per_page": commits})
        if history.status_code == 200:  # 409 means an empty repository: no commits yet
            data.commits = [(c["commit"]["author"]["date"][:10],
                             c["commit"]["message"].splitlines()[0][:120]) for c in history.json()]
        return data
