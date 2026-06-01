# niyam mission plan

Generate a mission plan from a requirements file.

## Usage

```bash
niyam mission plan [OPTIONS] REQUIREMENTS
```

## Arguments

* `requirements`: Path to requirements markdown file.

## Options

* `--strict`: Fail if AI-powered planning fails, instead of falling back. (Default: False)
* `--template, -t`: Use a mission template for planning.
* `--runtime, -r`: Runtime override for this mission.

