# niyam run

Plan, approve, and execute a mission in one step.

## Usage

```bash
niyam run [OPTIONS] REQUIREMENT
```

## Arguments

* `requirement`: Requirement text or path to requirements markdown file.

## Options

* `--runtime, -r`: Runtime override for this mission.
* `--parallel, -p`: Number of parallel workers.
* `--auto-approve`: Skip approval gate and execute immediately. (Default: False)
* `--strict`: Fail if AI-powered planning fails, instead of falling back. (Default: False)
* `--worktree`: Enable or disable git worktree isolation.
* `--template, -t`: Use a mission template for planning.

