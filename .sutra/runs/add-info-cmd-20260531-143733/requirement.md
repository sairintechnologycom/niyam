# Requirement: Add Niyam Info Command

## Goal
Add a new top-level command `niyam info` that displays basic information about the system and the current Niyam workspace.

## Expected Outcome
- A new command `niyam info` is available in the CLI.
- The command prints:
    - OS type
    - Python version
    - Niyam version
    - Whether the current directory is a Niyam workspace.
- Unit tests for the new command are added.

## Constraints
- Use `typer` for the new command implementation in `niyam/cli/main_cmds.py`.
- Use `rich` for formatting the output.
- Follow existing coding style and conventions.

## Validation
- `niyam info` runs without errors.
- New tests pass using `pytest`.
