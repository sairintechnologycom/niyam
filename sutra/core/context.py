"""Sutra context — scan repo and maintain AI project context."""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from sutra.core.config import find_sutra_root, load_sutra_config


# ── Stack detection rules ──────────────────────────────────────────────

MANIFEST_MAP: dict[str, dict] = {
    "package.json": {"language": "JavaScript/TypeScript", "package_manager": "npm"},
    "yarn.lock": {"package_manager": "yarn"},
    "pnpm-lock.yaml": {"package_manager": "pnpm"},
    "bun.lockb": {"package_manager": "bun"},
    "pyproject.toml": {"language": "Python"},
    "requirements.txt": {"language": "Python", "package_manager": "pip"},
    "Pipfile": {"language": "Python", "package_manager": "pipenv"},
    "poetry.lock": {"package_manager": "poetry"},
    "go.mod": {"language": "Go", "package_manager": "go modules"},
    "Cargo.toml": {"language": "Rust", "package_manager": "cargo"},
    "Gemfile": {"language": "Ruby", "package_manager": "bundler"},
    "build.gradle": {"language": "Java/Kotlin", "package_manager": "gradle"},
    "pom.xml": {"language": "Java", "package_manager": "maven"},
    "composer.json": {"language": "PHP", "package_manager": "composer"},
}

FRAMEWORK_INDICATORS: dict[str, str] = {
    "next.config.js": "Next.js",
    "next.config.ts": "Next.js",
    "next.config.mjs": "Next.js",
    "nuxt.config.ts": "Nuxt",
    "angular.json": "Angular",
    "svelte.config.js": "SvelteKit",
    "astro.config.mjs": "Astro",
    "vite.config.ts": "Vite",
    "vite.config.js": "Vite",
    "remix.config.js": "Remix",
    "tailwind.config.js": "Tailwind CSS",
    "tailwind.config.ts": "Tailwind CSS",
    "tsconfig.json": "TypeScript",
    "django": "Django",
    "manage.py": "Django",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    "terraform": "Terraform",
    "pulumi": "Pulumi",
}

VALIDATION_RULES: dict[str, dict] = {
    "package.json": {
        "build": "npm run build",
        "test": "npm test",
        "lint": "npm run lint",
    },
    "pyproject.toml": {
        "test": "pytest",
        "lint": "ruff check .",
        "format": "ruff format --check .",
    },
    "Cargo.toml": {
        "build": "cargo build",
        "test": "cargo test",
        "lint": "cargo clippy",
    },
    "go.mod": {
        "build": "go build ./...",
        "test": "go test ./...",
        "lint": "golangci-lint run",
    },
    "Makefile": {},
}

SOURCE_DIR_CANDIDATES = [
    "src", "lib", "app", "apps", "packages",
    "services", "server", "client", "api",
    "components", "pages", "views", "controllers",
    "models", "utils", "helpers", "core",
]

TEST_DIR_CANDIDATES = [
    "tests", "test", "__tests__", "spec", "specs",
    "e2e", "integration", "cypress",
]

CI_FILES = [
    ".github/workflows",
    ".gitlab-ci.yml",
    "Jenkinsfile",
    ".circleci/config.yml",
    "bitbucket-pipelines.yml",
]


def _scan_repo(repo_root: Path) -> dict:
    """Scan repository and return detected context."""
    languages: set[str] = set()
    frameworks: set[str] = set()
    package_managers: set[str] = set()
    validation: dict[str, str] = {}
    source_dirs: list[str] = []
    test_dirs: list[str] = []
    ci_detected: list[str] = []

    # Scan manifests
    for filename, info in MANIFEST_MAP.items():
        if (repo_root / filename).exists():
            if "language" in info:
                languages.add(info["language"])
            if "package_manager" in info:
                package_managers.add(info["package_manager"])

    # Scan framework indicators
    for filename, framework in FRAMEWORK_INDICATORS.items():
        if (repo_root / filename).exists():
            frameworks.add(framework)

    # Detect validation commands
    for manifest, commands in VALIDATION_RULES.items():
        if (repo_root / manifest).exists():
            for cmd_type, cmd in commands.items():
                if cmd_type not in validation:
                    validation[cmd_type] = cmd

    # Detect source directories
    for dirname in SOURCE_DIR_CANDIDATES:
        if (repo_root / dirname).is_dir():
            source_dirs.append(dirname)

    # Detect test directories
    for dirname in TEST_DIR_CANDIDATES:
        if (repo_root / dirname).is_dir():
            test_dirs.append(dirname)

    # Detect CI
    for ci_path in CI_FILES:
        if (repo_root / ci_path).exists():
            ci_detected.append(ci_path)

    return {
        "languages": sorted(languages),
        "frameworks": sorted(frameworks),
        "package_managers": sorted(package_managers),
        "validation": validation,
        "source_dirs": source_dirs,
        "test_dirs": test_dirs,
        "ci": ci_detected,
    }


def _generate_architecture_md(scan_result: dict, project_name: str) -> str:
    """Generate architecture.md content from scan results."""
    lines = [
        f"# {project_name} — Architecture",
        "",
        "<!-- AUTO-GENERATED by sutra context refresh — edits below the manual section will be overwritten -->",
        "",
    ]

    if scan_result["languages"]:
        lines.append("## Languages")
        for lang in scan_result["languages"]:
            lines.append(f"- {lang}")
        lines.append("")

    if scan_result["frameworks"]:
        lines.append("## Frameworks")
        for fw in scan_result["frameworks"]:
            lines.append(f"- {fw}")
        lines.append("")

    if scan_result["package_managers"]:
        lines.append("## Package Managers")
        for pm in scan_result["package_managers"]:
            lines.append(f"- {pm}")
        lines.append("")

    if scan_result["source_dirs"]:
        lines.append("## Source Directories")
        for sd in scan_result["source_dirs"]:
            lines.append(f"- `{sd}/`")
        lines.append("")

    if scan_result["test_dirs"]:
        lines.append("## Test Directories")
        for td in scan_result["test_dirs"]:
            lines.append(f"- `{td}/`")
        lines.append("")

    if scan_result["ci"]:
        lines.append("## CI/CD")
        for ci in scan_result["ci"]:
            lines.append(f"- `{ci}`")
        lines.append("")

    lines.extend([
        "---",
        "",
        "<!-- MANUAL SECTION: Add your own architecture notes below this line -->",
        "",
    ])

    return "\n".join(lines)


def _generate_validation_md(scan_result: dict) -> str:
    """Generate validation.md content from scan results."""
    lines = [
        "# Validation Commands",
        "",
        "<!-- AUTO-GENERATED by sutra context refresh -->",
        "",
    ]

    if scan_result["validation"]:
        for cmd_type, cmd in scan_result["validation"].items():
            lines.append(f"## {cmd_type.title()}")
            lines.append(f"```bash")
            lines.append(f"{cmd}")
            lines.append(f"```")
            lines.append("")
    else:
        lines.append("No validation commands detected. Add them manually.")
        lines.append("")

    lines.extend([
        "---",
        "",
        "<!-- MANUAL SECTION: Add your own validation commands below this line -->",
        "",
    ])

    return "\n".join(lines)


def _preserve_manual_section(existing_content: str, new_content: str) -> str:
    """Preserve manual notes from existing content when regenerating."""
    manual_marker = "<!-- MANUAL SECTION:"

    # Extract manual section from existing content
    manual_section = ""
    if manual_marker in existing_content:
        idx = existing_content.index(manual_marker)
        # Get everything after the marker line
        after_marker = existing_content[idx:]
        # Find the end of the marker line
        newline_idx = after_marker.index("\n") if "\n" in after_marker else len(after_marker)
        manual_section = after_marker[newline_idx:].strip()

    # If there's manual content, append it to the new content
    if manual_section:
        if manual_marker in new_content:
            idx = new_content.index(manual_marker)
            after_marker = new_content[idx:]
            newline_idx = after_marker.index("\n") if "\n" in after_marker else len(after_marker)
            marker_line = after_marker[: newline_idx + 1]
            return new_content[:idx] + marker_line + "\n" + manual_section + "\n"

    return new_content


def run_context_refresh(console: Console) -> None:
    """Scan the repo and update context files."""
    root = find_sutra_root()
    if root is None:
        console.print("[bold red]Error:[/] Not a Sutra workspace. Run [bold]sutra init[/] first.")
        raise SystemExit(1)

    config = load_sutra_config(root)
    scan = _scan_repo(root)

    context_dir = root / ".sutra" / "context"
    context_dir.mkdir(exist_ok=True)

    # Generate architecture.md
    arch_path = context_dir / "architecture.md"
    new_arch = _generate_architecture_md(scan, config.project_name)
    if arch_path.exists():
        existing = arch_path.read_text(encoding="utf-8")
        new_arch = _preserve_manual_section(existing, new_arch)
    arch_path.write_text(new_arch, encoding="utf-8")

    # Generate validation.md
    val_path = context_dir / "validation.md"
    new_val = _generate_validation_md(scan)
    if val_path.exists():
        existing = val_path.read_text(encoding="utf-8")
        new_val = _preserve_manual_section(existing, new_val)
    val_path.write_text(new_val, encoding="utf-8")

    # Update project.yaml
    import yaml

    project_yaml_path = root / ".sutra" / "project.yaml"
    project_data: dict = {}
    if project_yaml_path.exists():
        with open(project_yaml_path) as f:
            project_data = yaml.safe_load(f) or {}

    project_data["name"] = config.project_name
    project_data["stack"] = {
        "languages": scan["languages"],
        "frameworks": scan["frameworks"],
        "package_managers": scan["package_managers"],
    }
    project_data["validation"] = scan["validation"]
    project_data["source_dirs"] = scan["source_dirs"]
    project_data["test_dirs"] = scan["test_dirs"]

    with open(project_yaml_path, "w") as f:
        yaml.dump(project_data, f, default_flow_style=False, sort_keys=False)

    # Summary
    console.print(
        Panel(
            f"[bold green]✓[/] Context refreshed\n"
            f"  [dim]•[/] Languages: {', '.join(scan['languages']) or 'none detected'}\n"
            f"  [dim]•[/] Frameworks: {', '.join(scan['frameworks']) or 'none detected'}\n"
            f"  [dim]•[/] Source dirs: {', '.join(scan['source_dirs']) or 'none detected'}\n"
            f"  [dim]•[/] Test dirs: {', '.join(scan['test_dirs']) or 'none detected'}\n"
            f"  [dim]•[/] Validation: {', '.join(scan['validation'].keys()) or 'none detected'}\n"
            "\n"
            "[dim]Run [bold]sutra sync[/] to propagate changes to runtimes.[/]",
            title="[bold green]Context Refresh[/]",
            border_style="green",
        )
    )


def run_context_show(console: Console) -> None:
    """Display the current project context."""
    root = find_sutra_root()
    if root is None:
        console.print("[bold red]Error:[/] Not a Sutra workspace.")
        raise SystemExit(1)

    context_dir = root / ".sutra" / "context"
    if not context_dir.is_dir():
        console.print("[yellow]No context files found. Run [bold]sutra context refresh[/] first.[/]")
        return

    for md_file in sorted(context_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        console.print(Panel(
            Syntax(content, "markdown", theme="monokai"),
            title=f"[bold cyan]{md_file.name}[/]",
            border_style="cyan",
        ))


def run_context_diff(console: Console) -> None:
    """Show what would change on the next context refresh."""
    root = find_sutra_root()
    if root is None:
        console.print("[bold red]Error:[/] Not a Sutra workspace.")
        raise SystemExit(1)

    config = load_sutra_config(root)
    scan = _scan_repo(root)
    context_dir = root / ".sutra" / "context"

    if not context_dir.is_dir():
        console.print("[yellow]No existing context. Run [bold]sutra context refresh[/] to create it.[/]")
        return

    # Compare architecture
    arch_path = context_dir / "architecture.md"
    if arch_path.exists():
        existing = arch_path.read_text(encoding="utf-8")
        new_content = _generate_architecture_md(scan, config.project_name)
        new_content = _preserve_manual_section(existing, new_content)
        if existing.strip() == new_content.strip():
            console.print("[dim]architecture.md — no changes[/]")
        else:
            console.print("[yellow]architecture.md — changes detected[/]")
    else:
        console.print("[green]architecture.md — will be created[/]")

    # Compare validation
    val_path = context_dir / "validation.md"
    if val_path.exists():
        existing = val_path.read_text(encoding="utf-8")
        new_content = _generate_validation_md(scan)
        new_content = _preserve_manual_section(existing, new_content)
        if existing.strip() == new_content.strip():
            console.print("[dim]validation.md — no changes[/]")
        else:
            console.print("[yellow]validation.md — changes detected[/]")
    else:
        console.print("[green]validation.md — will be created[/]")
