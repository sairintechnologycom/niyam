# Technology Stack

**Analysis Date:** 2025-03-05

## Languages

**Primary:**
- Python 3.11+ - Core CLI logic, runtime adapters, and policy enforcement.

**Secondary:**
- Markdown - Used for instruction files (CLAUDE.md, AGENTS.md, GEMINI.md) and memory.
- YAML - Configuration and policy definition in `.niyam/`.

## Runtime

**Environment:**
- Python Runtime (3.11, 3.12, 3.13)

**Package Manager:**
- Pip / Hatch (implied by `pyproject.toml` and `hatchling` build backend)
- Lockfile: missing (not committed in root)

## Frameworks

**Core:**
- Typer >= 0.15.0 - CLI framework for command routing and argument parsing.
- Pydantic >= 2.0.0 - Data validation and settings management.
- Rich >= 13.0.0 - Terminal UI formatting, panels, and tables.

**Testing:**
- Pytest >= 8.0.0 - Unit and integration testing suite.
- Pytest-cov >= 5.0.0 - Test coverage reporting.

**Build/Dev:**
- Hatchling - Build backend for the `niyam` package.

## Key Dependencies

**Critical:**
- `gitpython` - Git repository interaction and management.
- `jinja2` - Templating engine for generating configuration and instruction files.
- `pyyaml` - Parsing and writing YAML configuration and policy files.

**Infrastructure:**
- `urllib` (Standard Library) - Used for direct GitHub REST API interactions in `niyam/core/pr.py`.

## Configuration

**Environment:**
- Configured via `.niyam/` directory in project roots.
- Environment variables for sensitive tokens (e.g., `GITHUB_TOKEN`).

**Build:**
- `pyproject.toml` - Main project configuration and dependency list.

## Platform Requirements

**Development:**
- Python 3.11 or higher.
- Git installed and configured.

**Production:**
- Cross-platform support (Linux, macOS, Windows) where Python is available.
- Supported AI CLIs: `claude` (Claude Code), `gemini` (Gemini CLI).

---

*Stack analysis: 2025-03-05*
