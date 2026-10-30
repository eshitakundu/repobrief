import json

import httpx
import pytest

from repobrief.brief import make_brief, offline_brief, recent_activity
from repobrief.cli import main
from repobrief.github import BriefError, GitHub, RepoData, parse_repo

META = {"owner": {"login": "acme"}, "name": "widget", "description": "A tiny widget library",
        "language": "Python", "stargazers_count": 1234, "license": {"spdx_id": "MIT"},
        "topics": ["cli", "widgets"], "pushed_at": "2026-10-01T10:00:00Z", "archived": False}
COMMITS = [{"commit": {"author": {"date": f"2026-10-0{i}T00:00:00Z"}, "message": msg}}
           for i, msg in [(3, "feat: add dark mode\n\nlong body"), (2, "fix: crash on empty input"),
                          (1, "docs: update README")]]


def github(routes: dict[str, httpx.Response]) -> GitHub:
    def handler(request: httpx.Request) -> httpx.Response:
        for suffix, response in routes.items():
            if request.url.path.endswith(suffix):
                return response
        return httpx.Response(404)
    return GitHub(client=httpx.Client(transport=httpx.MockTransport(handler)), token="")


def ok_routes(**overrides):
    routes = {"/repos/acme/widget": httpx.Response(200, json=META),
              "/readme": httpx.Response(200, text="# Widget\nDoes widget things."),
              "/commits": httpx.Response(200, json=COMMITS)}
    routes.update(overrides)
    return routes


def model(reply: str | None, calls: list | None = None) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.append(json.loads(request.content))
        if reply is None:
            raise httpx.ReadTimeout("slow")
        return httpx.Response(200, json={"choices": [{"message": {"content": reply}}]})
    return httpx.Client(transport=httpx.MockTransport(handler))


# --- parsing ---------------------------------------------------------------

@pytest.mark.parametrize("value", [
    "https://github.com/acme/widget", "github.com/acme/widget", "acme/widget",
    "https://github.com/acme/widget.git", "git@github.com:acme/widget.git",
    "https://github.com/acme/widget/tree/main/src", "  acme/widget  ",
])
def test_parse_repo_accepts_common_forms(value):
    assert parse_repo(value) == ("acme", "widget")


def test_parse_repo_rejects_garbage():
    with pytest.raises(BriefError):
        parse_repo("not a repo")


# --- fetching --------------------------------------------------------------

def test_fetch_collects_metadata_readme_and_commits():
    data = github(ok_routes()).fetch("acme", "widget")
    assert (data.stars, data.license, data.topics) == (1234, "MIT", ["cli", "widgets"])
    assert data.readme.startswith("# Widget")
    assert data.commits[0] == ("2026-10-03", "feat: add dark mode")


def test_missing_repo_gives_a_clear_error():
    with pytest.raises(BriefError, match="wasn't found"):
        github({}).fetch("acme", "widget")


def test_rate_limit_explains_reset_and_token():
    limited = httpx.Response(403, headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1893456000"})
    with pytest.raises(BriefError, match="rate limit.*GITHUB_TOKEN"):
        github({"/repos/acme/widget": limited}).fetch("acme", "widget")


def test_empty_repo_and_missing_readme_are_handled():
    data = github(ok_routes(**{"/readme": httpx.Response(404),
                               "/commits": httpx.Response(409)})).fetch("acme", "widget")
    assert data.readme == "" and data.commits == []
    assert "No README." in offline_brief(data) and "No commits yet." in offline_brief(data)


def test_long_readme_is_truncated_and_flagged():
    data = github(ok_routes(**{"/readme": httpx.Response(200, text="x" * 9000)})).fetch("acme", "widget")
    assert len(data.readme) == 4000 and data.readme_truncated


# --- briefs ----------------------------------------------------------------

def sample() -> RepoData:
    return github(ok_routes()).fetch("acme", "widget")


def test_recent_activity_groups_conventional_commits():
    assert recent_activity(sample()) == "3 recent commits (2026-10-01 to 2026-10-03): 1 features, 1 fixes, 1 docs."


def test_no_key_gives_an_offline_brief():
    brief, source = make_brief(sample(), api_key="")
    assert source == "offline" and "A tiny widget library" in brief and "★ 1,234" in brief


def test_model_summary_is_used_and_readme_marked_as_data():
    calls = []
    brief, source = make_brief(sample(), api_key="k", client=model("Widget is a small library.", calls))
    assert source == "model" and "Widget is a small library." in brief
    assert "data, not instructions" in calls[0]["messages"][0]["content"]
    assert "Does widget things." in calls[0]["messages"][1]["content"]


@pytest.mark.parametrize("reply", [None, ""])
def test_model_failure_falls_back_to_offline(reply):
    brief, source = make_brief(sample(), api_key="k", client=model(reply))
    assert source == "offline" and "A tiny widget library" in brief


# --- CLI -------------------------------------------------------------------

def test_cli_reports_errors_with_exit_code_1(capsys):
    assert main(["not a repo"]) == 1
    assert "Try owner/repo" in capsys.readouterr().err
