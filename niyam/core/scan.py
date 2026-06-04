"""Niyam production-readiness repository scanner and rule engine."""

from __future__ import annotations

import re
import os
import fnmatch
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError

# Deductions by severity
DEDUCTIONS = {"critical": 25, "high": 15, "medium": 8, "low": 3, "info": 0}

# Supported match types
SUPPORTED_MATCH_TYPES = {
    "file_exists",
    "file_missing",
    "filename_pattern",
    "content_contains",
    "content_regex",
    "directory_exists",
    "directory_missing",
}

# Text extensions allowed for full file content search
TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".java",
    ".rb",
    ".php",
    ".cs",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".txt",
    ".md",
    ".env",
    "dockerfile",
}


class MatchDefinition(BaseModel):
    type: str
    patterns: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    if_exists: list[str] | str | None = None


class GovernanceRule(BaseModel):
    id: str
    title: str
    category: str
    severity: str
    description: str
    recommendation: str
    match: MatchDefinition

    def validate_rule(self) -> None:
        """Additional validation for rule types and constraints."""
        if self.match.type not in SUPPORTED_MATCH_TYPES:
            raise ValueError(
                f"Rule '{self.id}' has unsupported match type '{self.match.type}'. "
                f"Supported types: {', '.join(sorted(SUPPORTED_MATCH_TYPES))}"
            )
        if not self.match.patterns and self.match.type not in (
            "directory_exists",
            "directory_missing",
        ):
            raise ValueError(
                f"Rule '{self.id}' of type '{self.match.type}' must specify 'patterns'."
            )
        if self.severity not in DEDUCTIONS:
            raise ValueError(
                f"Rule '{self.id}' has invalid severity '{self.severity}'. "
                f"Allowed severities: {', '.join(sorted(DEDUCTIONS.keys()))}"
            )


def is_text_file(path: Path) -> bool:
    """Check if the file is a text file that should be scanned."""
    name_lower = path.name.lower()
    if name_lower == "dockerfile" or name_lower.startswith(".env"):
        return True
    return path.suffix.lower() in TEXT_EXTENSIONS


def walk_files(root: Path) -> list[Path]:
    """Find all relevant files to scan, ignoring build directories and metadata."""
    exclude_dirs = {
        ".git",
        ".venv",
        ".niyam",
        "node_modules",
        "dist",
        "build",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".sutra",
    }

    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for f in filenames:
            file_path = Path(dirpath) / f
            if is_text_file(file_path):
                files.append(file_path)
    return files


def get_project_profile(root: Path) -> str:
    """Retrieve profile from configuration or fall back to 'startup'."""
    try:
        from niyam.core.config import load_niyam_config

        config = load_niyam_config(root)
        if config and config.governance and config.governance.scan:
            return config.governance.scan.profile
    except Exception:
        pass
    return "startup"


def load_rules_from_yaml(path: Path) -> list[GovernanceRule]:
    """Load, validate, and return list of governance rules from YAML file."""
    if not path.exists():
        raise FileNotFoundError(f"Rules file not found at: {path}")

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        raise ValueError(f"Failed to parse YAML file: {e}")

    if not isinstance(data, dict) or "rules" not in data:
        raise ValueError("Rules file must be a YAML mapping containing a 'rules' list.")

    rules_list = data["rules"]
    if not isinstance(rules_list, list):
        raise ValueError("'rules' key must be a list.")

    loaded_rules = []
    for idx, rule_data in enumerate(rules_list):
        if not isinstance(rule_data, dict):
            raise ValueError(f"Rule at index {idx} is not a valid YAML mapping.")

        try:
            rule = GovernanceRule(**rule_data)
            rule.validate_rule()
            loaded_rules.append(rule)
        except ValidationError as ve:
            raise ValueError(f"Validation error in rule at index {idx}: {ve}")
        except ValueError as ve:
            raise ValueError(str(ve))

    return loaded_rules


def load_profile_rules(profile: str) -> list[GovernanceRule]:
    """Load default rules based on the profile name."""
    rules_dir = Path(__file__).parent.parent / "governance" / "rules"
    profile_path = rules_dir / f"{profile}.yaml"
    if not profile_path.exists():
        # Fall back to startup if profile file does not exist
        profile_path = rules_dir / "startup.yaml"
    return load_rules_from_yaml(profile_path)


def evaluate_rule(
    rule: GovernanceRule, root: Path, files: list[Path]
) -> list[dict[str, Any]]:
    """Evaluate a single governance rule against the workspace files."""
    findings = []

    # 1. Resolve relative paths
    relative_paths = [f.relative_to(root) for f in files]

    # 2. Check conditional execution (if_exists)
    if_exists = rule.match.if_exists
    if if_exists:
        if isinstance(if_exists, str):
            if_exists = [if_exists]

        condition_met = False
        for f in relative_paths:
            for pat in if_exists:
                if fnmatch.fnmatch(f.name, pat) or fnmatch.fnmatch(str(f), pat):
                    condition_met = True
                    break
            if condition_met:
                break
        if not condition_met:
            return []  # Skip evaluation as condition is not met

    # 3. Match type evaluation
    mtype = rule.match.type
    patterns = rule.match.patterns

    if mtype in ("file_exists", "filename_pattern"):
        for f in relative_paths:
            for pat in patterns:
                if fnmatch.fnmatch(f.name, pat) or fnmatch.fnmatch(str(f), pat):
                    findings.append(
                        {
                            "id": rule.id,
                            "title": rule.title,
                            "category": rule.category,
                            "severity": rule.severity,
                            "file_path": str(f),
                            "description": rule.description,
                            "recommendation": rule.recommendation,
                        }
                    )
                    break  # One finding per file

    elif mtype == "file_missing":
        # Check if ANY file matches the patterns
        for pat in patterns:
            matched = False
            for f in relative_paths:
                if fnmatch.fnmatch(f.name, pat) or fnmatch.fnmatch(str(f), pat):
                    matched = True
                    break
            if matched:
                return []  # If any matching file exists, the dependency is NOT missing

        # If none of the files matched the lockfile/check patterns
        findings.append(
            {
                "id": rule.id,
                "title": rule.title,
                "category": rule.category,
                "severity": rule.severity,
                "file_path": "",
                "description": rule.description,
                "recommendation": rule.recommendation,
            }
        )

    elif mtype in ("content_contains", "content_regex"):
        # Filter files by pattern match if specified
        target_files = files
        if rule.match.files:
            target_files = []
            for f in files:
                rel = f.relative_to(root)
                if any(
                    fnmatch.fnmatch(f.name, p) or fnmatch.fnmatch(str(rel), p)
                    for p in rule.match.files
                ):
                    target_files.append(f)

        for f in target_files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                rel = f.relative_to(root)

                for pat in patterns:
                    matched = False
                    if mtype == "content_contains":
                        if pat in content:
                            matched = True
                    else:  # content_regex
                        if re.search(pat, content):
                            matched = True

                    if matched:
                        findings.append(
                            {
                                "id": rule.id,
                                "title": rule.title,
                                "category": rule.category,
                                "severity": rule.severity,
                                "file_path": str(rel),
                                "description": rule.description,
                                "recommendation": rule.recommendation,
                            }
                        )
                        break  # Limit to one finding of this type per file
            except Exception:
                pass

    elif mtype == "directory_exists":
        for pat in patterns:
            dir_path = root / pat
            if dir_path.is_dir():
                findings.append(
                    {
                        "id": rule.id,
                        "title": rule.title,
                        "category": rule.category,
                        "severity": rule.severity,
                        "file_path": pat,
                        "description": rule.description,
                        "recommendation": rule.recommendation,
                    }
                )

    elif mtype == "directory_missing":
        for pat in patterns:
            dir_path = root / pat
            if not dir_path.is_dir():
                findings.append(
                    {
                        "id": rule.id,
                        "title": rule.title,
                        "category": rule.category,
                        "severity": rule.severity,
                        "file_path": "",
                        "description": f"{rule.description} (Missing directory: {pat})",
                        "recommendation": rule.recommendation,
                    }
                )

    return findings


def run_scanner_checks(
    root: Path, profile: str | None = None, custom_rules_path: Path | None = None
) -> dict[str, Any]:
    """Run readiness checks using the rule engine and return a report."""
    root = Path(root).resolve()

    # 1. Determine profile and load rules
    if custom_rules_path:
        rules = load_rules_from_yaml(custom_rules_path)
        profile_name = "custom"
    else:
        if profile is None:
            profile = get_project_profile(root)
        rules = load_profile_rules(profile)
        profile_name = profile

    # 2. Gather scanned files
    files = walk_files(root)

    # 3. Evaluate all rules
    findings = []
    for rule in rules:
        findings.extend(evaluate_rule(rule, root, files))

    # 4. Calculate score
    score = 100
    for finding in findings:
        score -= DEDUCTIONS.get(finding["severity"], 0)

    score = max(0, min(100, score))

    # 5. Map Decision
    if score >= 85:
        decision = "GO"
    elif score >= 70:
        decision = "CONDITIONAL_GO"
    elif score >= 50:
        decision = "HIGH_RISK"
    else:
        decision = "NO_GO"

    return {
        "profile": profile_name,
        "score": score,
        "decision": decision,
        "findings": findings,
    }
