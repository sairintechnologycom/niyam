# Requirement: Add Sutra Info Command

## Goal
Add a new top-level command `sutra info` that displays basic information about the system and the current Sutra workspace.

## Expected Outcome
- A new command `sutra info` is available in the CLI.
- The command prints:
    - OS type
    - Python version
    - Sutra version
    - Whether the current directory is a Sutra workspace.
- Unit tests for the new command are added.

## Constraints
- Use `typer` for the new command implementation in `sutra/cli/main_cmds.py`.
- Use `rich` for formatting the output.
- Follow existing coding style and conventions.

## Validation
- `sutra info` runs without errors.
- New tests pass using `pytest`.
