"""repobrief: understand any GitHub repo in seconds."""
from __future__ import annotations

import argparse
import sys

from . import __version__
from .brief import DEFAULT_MODEL, make_brief
from .github import BriefError, GitHub, parse_repo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="repobrief",
        description="Understand any GitHub repo in seconds.",
        epilog=(
            "Environment variables:\n"
            "  OPENROUTER_API_KEY  (optional) free key from openrouter.ai for a written summary;\n"
            "                      without it you get a facts-only brief\n"
            "  REPOBRIEF_MODEL     (optional) OpenRouter model id, default " + DEFAULT_MODEL + "\n"
            "  GITHUB_TOKEN        (optional) raises GitHub's limit from 60 to 5,000 requests/hour"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("repo", help="GitHub URL or owner/repo")
    parser.add_argument("--commits", type=int, default=10, metavar="N",
                        help="recent commits to read (1-100, default 10)")
    parser.add_argument("--offline", action="store_true", help="skip the model, facts only")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    try:
        owner, repo = parse_repo(args.repo)
        print(f"Fetching {owner}/{repo}...", file=sys.stderr)
        data = GitHub().fetch(owner, repo, commits=max(1, min(args.commits, 100)))
    except BriefError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    brief, source = make_brief(data, api_key="" if args.offline else None)
    sys.stdout.reconfigure(encoding="utf-8")
    print(brief)
    if source == "offline" and not args.offline:
        print("\n(Facts-only brief. Set OPENROUTER_API_KEY for a written summary.)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
