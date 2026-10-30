# repobrief

[![CI](https://github.com/eshitakundu/repobrief/actions/workflows/ci.yml/badge.svg)](https://github.com/eshitakundu/repobrief/actions/workflows/ci.yml)

**Land on any GitHub repo and know what it is in seconds.** repobrief reads a repository's metadata, README and recent commits, then gives you a short plain-English brief: what it does, how alive it is, and what changed lately.

```bash
repobrief astral-sh/uv
```

It works with no API key at all (facts-only brief) and with a **free** OpenRouter key it adds a written summary.

## Example (no key)

```
$ repobrief eshitakundu/DevPulse --offline
eshitakundu/DevPulse
Python · ★ 0 · MIT licence · last push 2026-10-30

What do developers say about a tool? Pros and cons from Hacker News where every
point quotes a real comment. ...
Topics: ai-agents, evals, grounding, hacker-news, llm, openrouter, prompt-injection, python

10 recent commits (2026-10-30 to 2026-10-30).
  2026-10-30  Write README and add a real sample report
  2026-10-30  Run tests and guardrail eval in CI
  ...
```

With `OPENROUTER_API_KEY` set, a model paragraph replaces the description block, and the facts line and commit activity stay underneath it.

## How it works

1. **Parse** a GitHub URL, `owner/repo` shorthand or SSH remote.
2. **Fetch** repo metadata, the README (first 4,000 characters, flagged if truncated) and the last N commits from the GitHub REST API.
3. **Summarise** with an OpenRouter model if a key is set. The README and commit messages are untrusted text, so the prompt tells the model to treat them as data and not to guess beyond them.
4. **Fall back** to a deterministic brief built only from the metadata if there's no key, the call fails or the reply is empty. It never invents anything.

Commit activity groups [Conventional Commit](https://www.conventionalcommits.org) prefixes (`feat`, `fix`, `docs`...) so you can see at a glance whether a project is shipping features or just fixing things.

### Errors you'll actually hit, handled

| Situation | What you see |
|---|---|
| Repo doesn't exist or is private | `acme/widget wasn't found. It may be private or misspelled.` |
| GitHub rate limit (60/hour without a token) | When it resets, and that `GITHUB_TOKEN` raises it to 5,000/hour |
| Empty repo / no README | `No commits yet.` / `No README.` in the brief instead of a crash |
| Network down | A one-line message, exit code 1 |
| Model timeout or bad reply | Silent fallback to the facts-only brief |

## Install and run

```bash
pip install git+https://github.com/eshitakundu/repobrief
repobrief https://github.com/pallets/flask
repobrief pallets/flask --commits 20
repobrief pallets/flask --offline        # never call a model
```

Or from a clone with [uv](https://docs.astral.sh/uv/): `uv run repobrief pallets/flask`.

| Variable | Needed? | Purpose |
|---|---|---|
| `OPENROUTER_API_KEY` | optional | Free key from [openrouter.ai](https://openrouter.ai/keys) for the written summary |
| `REPOBRIEF_MODEL` | optional | OpenRouter model id (default `openrouter/auto`) |
| `GITHUB_TOKEN` | optional | Raises GitHub's rate limit |

## Tests

```bash
pip install -e ".[dev]"
pytest -q
```

19 tests with mocked GitHub and model responses: every URL form, missing repos, rate-limit messages, empty repos, README truncation, commit grouping, the model path (including that the prompt marks repo text as data) and fallback on timeouts and empty replies. CI runs them on Python 3.11, 3.12 and 3.13.

## History

Started in May 2026 as a single script (briefly called GitPulse) that needed a paid Anthropic key. In October 2026 it became a package with free OpenRouter models, an offline mode, real error handling and tests.

## Stack

Python · httpx · GitHub REST API · OpenRouter · pytest · GitHub Actions
