import os
import re
import sys
import argparse
import requests
import anthropic

__version__ = "0.1.0"

DEFAULT_MODEL = "claude-sonnet-4-5"


def _github_headers():
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def parse_repo(url):
    match = re.search(r"github\.com/([^/]+)/([^/\s]+?)(?:\.git)?(?:/.*)?$", url.strip())
    if not match:
        sys.exit(f"Error: could not parse GitHub URL: {url}")
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


def fetch_commits(owner, repo, count):
    r = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/commits",
        params={"per_page": count},
        headers=_github_headers(),
    )
    r.raise_for_status()
    return "\n".join(
        f"- {c['commit']['message'].splitlines()[0]} ({c['commit']['author']['date'][:10]})"
        for c in r.json()
    )


def summarize(owner, repo, readme, commits, model):
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
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
    parser = argparse.ArgumentParser(
        prog="repobrief",
        description="Understand any GitHub repo in 10 seconds.",
        epilog=(
            "Environment variables:\n"
            "  ANTHROPIC_API_KEY  (required) your Anthropic API key\n"
            "  GITHUB_TOKEN       (optional) raises GitHub rate limit from 60 to 5000 req/hr"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("url", help="GitHub repository URL")
    parser.add_argument(
        "--commits",
        type=int,
        default=10,
        metavar="N",
        help="number of recent commits to include (default: 10)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        metavar="MODEL",
        help=f"Claude model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("Error: ANTHROPIC_API_KEY environment variable is not set.")

    owner, repo = parse_repo(args.url)
    print(f"Fetching {owner}/{repo}...", file=sys.stderr)
    readme = fetch_readme(owner, repo)
    commits = fetch_commits(owner, repo, args.commits)
    print(summarize(owner, repo, readme, commits, args.model))


if __name__ == "__main__":
    main()
