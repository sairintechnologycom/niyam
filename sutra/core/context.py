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
    "src",
    "lib",
    "app",
    "apps",
    "packages",
    "services",
    "server",
    "client",
    "api",
    "components",
    "pages",
    "views",
    "controllers",
    "models",
    "utils",
    "helpers",
    "core",
]

TEST_DIR_CANDIDATES = [
    "tests",
    "test",
    "__tests__",
    "spec",
    "specs",
    "e2e",
    "integration",
    "cypress",
]

CI_FILES = [
    ".github/workflows",
    ".gitlab-ci.yml",
    "Jenkinsfile",
    ".circleci/config.yml",
    "bitbucket-pipelines.yml",
]


def _extract_dependency_versions(repo_root: Path) -> list[str]:
    versions = []
    pkg_json = repo_root / "package.json"
    if pkg_json.exists():
        try:
            with open(pkg_json, encoding="utf-8") as f:
                data = json.load(f)
            deps = data.get("dependencies", {})
            dev_deps = data.get("devDependencies", {})
            for name, ver in sorted({**deps, **dev_deps}.items()):
                clean_ver = str(ver).lstrip("^~>=<")
                versions.append(f"{name} ({clean_ver})")
        except Exception:
            pass

    pyproject = repo_root / "pyproject.toml"
    if pyproject.exists():
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                tomllib = None
        if tomllib:
            try:
                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                project_deps = data.get("project", {}).get("dependencies", [])
                opt_deps = (
                    data.get("project", {}).get("optional-dependencies", {}) or {}
                )
                poetry_deps = (
                    data.get("tool", {}).get("poetry", {}).get("dependencies", {}) or {}
                )
                for name, ver in sorted(poetry_deps.items()):
                    if name != "python":
                        versions.append(f"{name} ({ver})")
                for dep in project_deps:
                    versions.append(str(dep))
                for group_deps in opt_deps.values():
                    if isinstance(group_deps, list):
                        for dep in group_deps:
                            versions.append(str(dep))
            except Exception:
                pass
        else:
            try:
                content = pyproject.read_text(encoding="utf-8")
                in_deps = False
                for line in content.splitlines():
                    if line.strip().startswith("[tool.poetry.dependencies]"):
                        in_deps = True
                        continue
                    if line.strip().startswith("[") and in_deps:
                        in_deps = False
                    if in_deps and "=" in line:
                        parts = line.split("=")
                        name = parts[0].strip()
                        ver = parts[1].strip().strip('"').strip("'")
                        if name != "python":
                            versions.append(f"{name} ({ver})")
            except Exception:
                pass

    cargo = repo_root / "Cargo.toml"
    if cargo.exists():
        try:
            content = cargo.read_text(encoding="utf-8")
            in_deps = False
            for line in content.splitlines():
                if line.strip().startswith("[dependencies]"):
                    in_deps = True
                    continue
                if line.strip().startswith("[") and in_deps:
                    in_deps = False
                if in_deps and "=" in line:
                    parts = line.split("=")
                    name = parts[0].strip()
                    ver = parts[1].strip().strip('"').strip("'")
                    versions.append(f"{name} ({ver})")
        except Exception:
            pass

    return versions[:30]


def _extract_db_schema(repo_root: Path) -> list[str]:
    info = []
    prisma = repo_root / "prisma" / "schema.prisma"
    if prisma.exists():
        try:
            lines = prisma.read_text(encoding="utf-8").splitlines()
            models = []
            for line in lines:
                if line.strip().startswith("model "):
                    models.append(line.split()[1])
            if models:
                info.append(f"Prisma schema with models: {', '.join(models)}")
        except Exception:
            pass

    for m_dir in ["migrations", "alembic", "db/migrate"]:
        mig_path = repo_root / m_dir
        if mig_path.is_dir():
            files = sorted([f.name for f in mig_path.glob("**/*") if f.is_file()])
            if files:
                info.append(
                    f"Database migrations found in {m_dir}/ ({len(files)} files)"
                )

    for sql_name in ["schema.sql", "db.sql", "init.sql"]:
        sql_path = repo_root / sql_name
        if sql_path.exists():
            info.append(f"SQL Schema file found: {sql_name}")

    return info


def _extract_api_routes(repo_root: Path) -> list[str]:
    routes = []
    for r_dir in ["api", "routes", "controllers"]:
        dir_path = repo_root / r_dir
        if dir_path.is_dir():
            files = [
                str(f.relative_to(repo_root))
                for f in dir_path.glob("**/*")
                if f.is_file() and f.suffix in (".py", ".js", ".ts", ".go", ".rs")
            ]
            if files:
                routes.append(
                    f"Routes / controllers in {r_dir}/: {', '.join(files[:10])}"
                    + ("..." if len(files) > 10 else "")
                )
    return routes


def _extract_env_vars(repo_root: Path) -> list[str]:
    env_vars = []
    for env_name in [".env.example", ".env.template", ".env.defaults"]:
        env_path = repo_root / env_name
        if env_path.exists():
            try:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        var_name = line.split("=")[0].strip()
                        env_vars.append(var_name)
            except Exception:
                pass
            break
    return sorted(list(set(env_vars)))


def _get_readme_summary(repo_root: Path) -> str:
    for r_name in ["README.md", "readme.md", "README", "README.txt"]:
        r_path = repo_root / r_name
        if r_path.exists():
            try:
                lines = r_path.read_text(encoding="utf-8").splitlines()
                return "\n".join(lines[:50])
            except Exception:
                pass
    return ""


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

    # Scan dependencies for framework indicators
    dependency_frameworks = {
        "typer": "Typer",
        "rich": "Rich",
        "pytest": "pytest",
        "pydantic": "Pydantic",
        "fastapi": "FastAPI",
        "django": "Django",
        "flask": "Flask",
        "sqlalchemy": "SQLAlchemy",
        "react": "React",
        "express": "Express",
        "jest": "Jest",
        "next": "Next.js",
        "vue": "Vue",
        "angular": "Angular",
        "svelte": "Svelte",
    }
    dep_versions = _extract_dependency_versions(repo_root)
    # Also extract requirements.txt if present
    req_txt = repo_root / "requirements.txt"
    if req_txt.exists():
        try:
            for line in req_txt.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    dep_name = (
                        line.split("=")[0]
                        .split(">")[0]
                        .split("<")[0]
                        .split("[")[0]
                        .strip()
                        .lower()
                    )
                    if dep_name in dependency_frameworks:
                        frameworks.add(dependency_frameworks[dep_name])
        except Exception:
            pass

    for dep_str in dep_versions:
        dep_name = (
            dep_str.split()[0]
            .split(">")[0]
            .split("<")[0]
            .split("=")[0]
            .split("[")[0]
            .strip()
            .lower()
        )
        if dep_name in dependency_frameworks:
            frameworks.add(dependency_frameworks[dep_name])

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

    # Detect project package directory as primary source root
    try:
        config = load_sutra_config(repo_root)
        project_name = config.project_name
        if (
            project_name
            and (repo_root / project_name).is_dir()
            and project_name not in source_dirs
        ):
            source_dirs.append(project_name)
    except Exception:
        pass

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
        "dependency_versions": dep_versions,
        "db_schema": _extract_db_schema(repo_root),
        "api_routes": _extract_api_routes(repo_root),
        "env_vars": _extract_env_vars(repo_root),
        "readme_summary": _get_readme_summary(repo_root),
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

    if scan_result.get("dependency_versions"):
        lines.append("## Dependency Versions")
        for dep in scan_result["dependency_versions"]:
            lines.append(f"- {dep}")
        lines.append("")

    if scan_result.get("db_schema"):
        lines.append("## Database Schema & Migrations")
        for db in scan_result["db_schema"]:
            lines.append(f"- {db}")
        lines.append("")

    if scan_result.get("api_routes"):
        lines.append("## API Routes & Controllers")
        for route in scan_result["api_routes"]:
            lines.append(f"- {route}")
        lines.append("")

    if scan_result.get("env_vars"):
        lines.append("## Environment Variables")
        for ev in scan_result["env_vars"]:
            lines.append(f"- `{ev}`")
        lines.append("")

    if scan_result.get("readme_summary"):
        lines.append("## Project Readme Summary")
        lines.append("```markdown")
        lines.append(scan_result["readme_summary"])
        lines.append("```")
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

    lines.extend(
        [
            "---",
            "",
            "<!-- MANUAL SECTION: Add your own architecture notes below this line -->",
            "",
        ]
    )

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
            lines.append("```bash")
            lines.append(f"{cmd}")
            lines.append("```")
            lines.append("")
    else:
        lines.append("No validation commands detected. Add them manually.")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "<!-- MANUAL SECTION: Add your own validation commands below this line -->",
            "",
        ]
    )

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
        newline_idx = (
            after_marker.index("\n") if "\n" in after_marker else len(after_marker)
        )
        manual_section = after_marker[newline_idx:].strip()

    # If there's manual content, append it to the new content
    if manual_section:
        if manual_marker in new_content:
            idx = new_content.index(manual_marker)
            after_marker = new_content[idx:]
            newline_idx = (
                after_marker.index("\n") if "\n" in after_marker else len(after_marker)
            )
            marker_line = after_marker[: newline_idx + 1]
            return new_content[:idx] + marker_line + "\n" + manual_section + "\n"

    return new_content


def _boilerplate_cli_commands(root: Path, console: Console) -> None:
    from sutra.cli import app
    import typer.main
    import typer.core

    commands_dir = root / ".sutra" / "commands"
    commands_dir.mkdir(exist_ok=True)

    click_app = typer.main.get_command(app)

    def traverse(cmd, parts: list[str]):
        name_parts = parts + [cmd.name]

        # If it is a group (TyperGroup), traverse subcommands
        if isinstance(cmd, typer.core.TyperGroup):
            for sub_name in cmd.list_commands(None):
                sub_cmd = cmd.get_command(None, sub_name)
                if sub_cmd:
                    traverse(sub_cmd, name_parts)
        else:
            # It's an executable command
            cmd_full_name = "-".join(name_parts)
            filename = f"{cmd_full_name}.md"
            target_file = commands_dir / filename

            if not target_file.exists():
                # Let's generate markdown content
                help_text = cmd.help or "No description provided."
                usage_parts = []
                for p in cmd.params:
                    if isinstance(p, typer.core.TyperOption):
                        usage_parts.append("[OPTIONS]")
                        break

                for p in cmd.params:
                    if isinstance(p, typer.core.TyperArgument):
                        usage_parts.append(p.name.upper())

                usage_str = " ".join(name_parts) + (
                    " " + " ".join(usage_parts) if usage_parts else ""
                )

                md_lines = [
                    f"# {cmd_full_name.replace('-', ' ')}",
                    "",
                    help_text.strip(),
                    "",
                    "## Usage",
                    "",
                    "```bash",
                    f"{usage_str}",
                    "```",
                    "",
                ]

                options_lines = []
                arguments_lines = []
                for p in cmd.params:
                    p_help = getattr(p, "help", None) or "No description."
                    default_str = (
                        f" (Default: {p.default})" if p.default is not None else ""
                    )
                    if isinstance(p, typer.core.TyperOption):
                        opt_names = ", ".join(p.opts)
                        options_lines.append(f"* `{opt_names}`: {p_help}{default_str}")
                    elif isinstance(p, typer.core.TyperArgument):
                        arguments_lines.append(f"* `{p.name}`: {p_help}{default_str}")

                if arguments_lines:
                    md_lines.extend(
                        ["## Arguments", "", "\n".join(arguments_lines), ""]
                    )
                if options_lines:
                    md_lines.extend(["## Options", "", "\n".join(options_lines), ""])

                target_file.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
                console.print(
                    f"  [dim]•[/] Boilerplated missing command template: [cyan].sutra/commands/{filename}[/]"
                )

    # Start traversal
    traverse(click_app, [])


def run_context_refresh(console: Console) -> None:
    """Scan the repo and update context files."""
    root = find_sutra_root()
    if root is None:
        console.print(
            "[bold red]Error:[/] Not a Sutra workspace. Run [bold]sutra init[/] first."
        )
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
    project_data["dependency_versions"] = scan.get("dependency_versions", [])
    project_data["db_schema"] = scan.get("db_schema", [])
    project_data["api_routes"] = scan.get("api_routes", [])
    project_data["env_vars"] = scan.get("env_vars", [])

    with open(project_yaml_path, "w") as f:
        yaml.dump(project_data, f, default_flow_style=False, sort_keys=False)

    # Auto-boilerplate CLI commands under .sutra/commands/
    try:
        _boilerplate_cli_commands(root, console)
    except Exception as e:
        console.print(
            f"[yellow]Warning: failed to auto-boilerplate command templates: {e}[/]"
        )

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
        console.print(
            "[yellow]No context files found. Run [bold]sutra context refresh[/] first.[/]"
        )
        return

    for md_file in sorted(context_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        console.print(
            Panel(
                Syntax(content, "markdown", theme="monokai"),
                title=f"[bold cyan]{md_file.name}[/]",
                border_style="cyan",
            )
        )


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
        console.print(
            "[yellow]No existing context. Run [bold]sutra context refresh[/] to create it.[/]"
        )
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
