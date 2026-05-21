# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

GitPulse is a single-file Python CLI tool (`gitpulse.py`) that fetches a GitHub repo's README and recent commits via the GitHub API, then uses the Claude API to generate a one-paragraph plain-English summary.

## Commands

```bash
pip install -r requirements.txt
python gitpulse.py <github-repo-url>
# Example:
python gitpulse.py https://github.com/anthropics/anthropic-sdk-python
```

Requires `ANTHROPIC_API_KEY` in the environment.

## 1. Think Before Coding
Before implementing: state assumptions explicitly, ask if uncertain, present multiple interpretations rather than picking silently, stop and name what's confusing if unclear.

## 2. Simplicity First
Minimum code that solves the problem. No features beyond what was asked. No abstractions for single-use code. No speculative flexibility. If you write 200 lines and it could be 50, rewrite it.

## 3. Surgical Changes
Touch only what you must. Don't improve adjacent code. Match existing style. Remove only imports/variables YOUR changes made unused.

## 4. Goal-Driven Execution
Define success criteria before implementing. For multi-step tasks, state a brief plan with verification steps.
