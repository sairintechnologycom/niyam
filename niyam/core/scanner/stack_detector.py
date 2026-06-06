"""Niyam stack detector — identify languages, frameworks, and tools in a repo."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from niyam.core.config import load_niyam_config

logger = logging.getLogger(__name__)

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
        except Exception as e:
            logger.debug("Failed to extract dependency versions from package.json: %s", e)

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
            except Exception as e:
                logger.debug("Failed to parse pyproject.toml: %s", e)
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
            except Exception as e:
                logger.debug("Failed to read pyproject.toml: %s", e)

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
        except Exception as e:
            logger.debug("Failed to read Cargo.toml: %s", e)

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
        except Exception as e:
            logger.debug("Failed to extract schema from Prisma file: %s", e)

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
            except Exception as e:
                logger.debug("Failed to extract environment variables from %s: %s", env_name, e)
            break
    return sorted(list(set(env_vars)))


def _get_readme_summary(repo_root: Path) -> str:
    for r_name in ["README.md", "readme.md", "README", "README.txt"]:
        r_path = repo_root / r_name
        if r_path.exists():
            try:
                lines = r_path.read_text(encoding="utf-8").splitlines()
                return "\n".join(lines[:50])
            except Exception as e:
                logger.debug("Failed to read readme file %s: %s", r_name, e)
    return ""


def detect_stack(repo_root: Path) -> dict[str, Any]:
    """Scan repository and return detected stack context."""
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
        if (repo_root / filename).exists() or (repo_root / f"**/ {filename}").exists():
            # Basic check for existence
            pass
        # Better: recursively check or check common locations
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
        languages.add("Python")
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
        except Exception as e:
            logger.debug("Failed to read requirements.txt: %s", e)

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
        config = load_niyam_config(repo_root)
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
        "languages": sorted(list(languages)),
        "frameworks": sorted(list(frameworks)),
        "package_managers": sorted(list(package_managers)),
        "validation": validation,
        "source_dirs": sorted(source_dirs),
        "test_dirs": sorted(test_dirs),
        "ci_detected": ci_detected,
        "dependency_versions": dep_versions,
        "db_schema": _extract_db_schema(repo_root),
        "api_routes": _extract_api_routes(repo_root),
        "env_vars": _extract_env_vars(repo_root),
        "readme_summary": _get_readme_summary(repo_root),
    }
