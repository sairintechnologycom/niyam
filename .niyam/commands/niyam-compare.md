# niyam compare

Compare performance, cost, and validation status of multiple runtimes on a task.

## Usage

```bash
niyam compare [OPTIONS] TASK_ID
```

## Arguments

* `task_id`: Task ID to run comparison for (e.g., T1, TASK-001).

## Options

* `--executors, -e`: Comma-separated list of executors to compare (e.g., claude,gemini,codex). (Default: claude,gemini,codex)

