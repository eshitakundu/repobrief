#!/usr/bin/env python3
import os
import re
import sys
import requests
import anthropic


def _github_headers():
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def parse_repo(url):
    match = re.search(r"github\.com/([^/]+)/([^/\s]+?)(?:\.git)?(?:/.*)?$", url.strip())
    if not match:
        sys.exit(f"Could not parse GitHub URL: {url}")
    return match.group(1), match.group(2)


def fetch_readme(owner, repo):
    r = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/readme",
        headers={**_github_headers(), "Accept": "application/vnd.github.raw"},
    )
    if r.status_code == 404:
        return "(no README)"
    r.raise_for_status()
    return r.text[:3000]


def fetch_commits(owner, repo):
    r = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/commits",
        params={"per_page": 10},
        headers=_github_headers(),
    )
    r.raise_for_status()
    return "\n".join(
        f"- {c['commit']['message'].splitlines()[0]} ({c['commit']['author']['date'][:10]})"
        for c in r.json()
    )


def summarize(owner, repo, readme, commits):
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Repository: {owner}/{repo}\n\n"
                    f"README (truncated):\n{readme}\n\n"
                    f"Recent commits:\n{commits}\n\n"
                    "Write one paragraph in plain English summarizing what this project does "
                    "and what has changed recently."
                ),
            }
        ],
    )
    return response.content[0].text


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: repobrief <github-repo-url>")
    url = sys.argv[1]
    owner, repo = parse_repo(url)
    print(f"Fetching {owner}/{repo}...", file=sys.stderr)
    readme = fetch_readme(owner, repo)
    commits = fetch_commits(owner, repo)
    print(summarize(owner, repo, readme, commits))


if __name__ == "__main__":
    main()
