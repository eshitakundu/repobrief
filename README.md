# GitPulse

> Land on any GitHub repo and understand it in 10 seconds.

GitPulse is a CLI tool that takes a GitHub repo URL, fetches its README and last 10 commits via the GitHub API, and uses Claude to generate a plain-English summary of what the project does and what's changed recently.

## Usage

```bash
# Run directly with uv (no install needed)
uv run gitpulse.py https://github.com/anthropics/anthropic-sdk-python

# Or via main.py
uv run main.py https://github.com/anthropics/anthropic-sdk-python
```

## Setup

**Required:** `ANTHROPIC_API_KEY` environment variable.

**Optional:** `GITHUB_TOKEN` environment variable — set this to avoid GitHub's 60 requests/hour unauthenticated rate limit.

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export GITHUB_TOKEN=ghp_...        # optional but recommended
```

## Example output

```
$ uv run gitpulse.py https://github.com/anthropics/anthropic-sdk-python
Fetching anthropics/anthropic-sdk-python...
The Anthropic Python SDK provides a convenient interface for interacting with
Anthropic's Claude models via their REST API. It supports both sync and async
usage, streaming responses, tool use, and vision capabilities. Recent changes
include updates to the latest Claude model aliases and minor documentation fixes.
```
