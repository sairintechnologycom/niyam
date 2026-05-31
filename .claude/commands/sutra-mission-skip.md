# sutra mission skip

Skip a specific task and resume the mission execution.

## Usage

```bash
sutra mission skip [OPTIONS] TASK_ID
```

## Arguments

* `task_id`: ID of the task to skip.

## Options

* `--parallel, -p`: Override the number of parallel workers.
* `--worktree`: Enable or disable git worktree isolation.
* `--non-interactive, --ci`: Run in non-interactive (CI/CD) mode. (Default: False)
* `--mission`: Mission ID containing the task.

