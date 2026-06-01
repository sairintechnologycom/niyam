# niyam mission retry

Retry failed or skipped tasks of the latest mission.

## Usage

```bash
niyam mission retry [OPTIONS]
```

## Options

* `--parallel, -p`: Override the number of parallel workers.
* `--worktree`: Enable or disable git worktree isolation.
* `--non-interactive, --ci`: Run in non-interactive (CI/CD) mode. (Default: False)
* `--mission`: Mission ID to retry.

