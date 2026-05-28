---
name: repo-context
description: Understand and navigate the repository structure before making changes.
---

# Repository Context

Before making changes, understand the repository's structure, conventions, and patterns.

## When to Use

- At the start of any task
- When working in an unfamiliar part of the codebase
- When unsure about project conventions

## Process

1. **Read project context** — check `.sutra/context/` for architecture and validation info
2. **Scan relevant directories** — understand the file layout
3. **Find existing patterns** — look for similar implementations
4. **Check tests** — understand how existing code is tested
5. **Review recent changes** — `git log` for recent relevant commits

## Rules

- Follow existing patterns — do not introduce new conventions without discussion
- Check for existing utilities before writing new ones
- Respect the project's import/module structure
- Keep file organization consistent with the rest of the codebase
