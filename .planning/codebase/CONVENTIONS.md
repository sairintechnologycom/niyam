# Coding Conventions

**Analysis Date:** 2024-05-23

## Naming Patterns

**Files:**
- snake_case for all source and test files (e.g., `cli.py`, `test_cli.py`).
- Lowercase for directory names.

**Functions:**
- snake_case for function and method names (e.g., `run_init`, `load_sutra_config`).

**Variables:**
- snake_case for local variables and parameters.
- UPPER_SNAKE_CASE for constants (e.g., `SUTRA_DIR`, `MANIFEST_MAP`).

**Types:**
- PascalCase for class names (e.g., `SutraConfig`, `RuntimeAdapter`, `SutraError`).
- Modern type hints using `from __future__ import annotations`.
- Use of `Annotated`, `Optional`, `Literal` from `typing`.

## Code Style

**Formatting:**
- Follows PEP 8.
- Unicode separator comments for sectioning code (e.g., `# ── Section ──────────────────────────────────────────────────────`).

**Linting:**
- Ruff is used for linting and formatting (evidenced by `.ruff_cache`).
- Pydantic models used for configuration validation (`sutra/core/config.py`).

## Import Organization

**Order:**
1. Future imports (`from __future__ import annotations`).
2. Standard library imports.
3. Third-party library imports (e.g., `typer`, `rich`, `pydantic`).
4. Local application imports (e.g., `from sutra.core import ...`).

**Path Aliases:**
- None detected; standard absolute imports used within the `sutra` package.

## Error Handling

**Patterns:**
- Custom exception hierarchy defined in `sutra/core/errors.py`.
- Base exception `SutraError` with integer `code` attribute.
- Specific exceptions like `SutraConfigError`, `SutraSecurityError`, and `SutraExecutionError`.
- Use of `raise SystemExit(1)` for CLI errors to return non-zero exit codes.

## Logging

**Framework:**
- `rich.console.Console` for interactive output.
- No heavy usage of standard `logging` module in core logic; prefers direct console output or returning results.

**Patterns:**
- Consistent use of colors and formatting (e.g., `[bold red]`, `[cyan]`, `[dim]`) to indicate status.
- Rich Panels and Tables for structured data display (`sutra/core/ci.py`).

## Comments

**When to Comment:**
- Module-level docstrings explaining purpose.
- Class and function docstrings using triple quotes.
- Section headers with unicode bars for visual separation.

**JSDoc/TSDoc:**
- Not applicable (Python project). Uses standard Python docstrings.

## Function Design

**Size:** Generally focused and modular. Some CLI implementation functions in `sutra/cli.py` handle multiple subcommands.

**Parameters:** Uses `Annotated` for Typer CLI parameters. Prefer keyword arguments or sensible defaults in core logic.

**Return Values:** Explicit type hints for return values, including Union types using the `|` operator (e.g., `str | None`).

## Module Design

**Exports:** `__init__.py` files used to define package exports and version.

**Barrel Files:** `sutra/core/__init__.py` and others used to expose core functionality from submodules.

---

*Convention analysis: 2024-05-23*
