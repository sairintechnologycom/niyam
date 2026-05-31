# sutra pr create

Push the active branch and create a GitHub pull request with evidence report attached.

## Usage

```bash
sutra pr create [OPTIONS]
```

## Options

* `--title, -t`: Pull Request title.
* `--body, -b`: Pull Request body/description.
* `--base`: Target branch for the pull request. (Default: main)
* `--token`: GitHub token (overrides GITHUB_TOKEN environment variable).

