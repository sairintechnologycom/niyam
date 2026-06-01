# niyam review pr

Run a structured code review on a GitHub pull request.

## Usage

```bash
niyam review pr [OPTIONS] PR
```

## Arguments

* `pr`: Pull Request ID.

## Options

* `--lens, -l`: Review lens/perspective. (Default: ReviewLens.engineering)
* `--runtime, -r`: Runtime to execute the review with. (Default: Runtime.claude)
* `--mode, -m`: Review mode. (Default: ReviewMode.collaborative)
* `--token`: GitHub token (overrides GITHUB_TOKEN environment variable).

