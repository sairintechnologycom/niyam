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
    "content_missing",
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
    ".pem",
    ".key",
    ".crt",
    ".cer",
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
    confidence: str | None = None
    remediation_effort: str | None = None
    tags: list[str] = Field(default_factory=list)

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
    if name_lower in (
        "dockerfile",
        "jenkinsfile",
        ".gitignore",
        ".gitattributes",
    ) or name_lower.startswith(".env"):
        return True
    suffix = path.suffix.lower()
    if suffix in (".lock", ".sum"):
        return True
    return suffix in TEXT_EXTENSIONS


def walk_files(root: Path, *, include_test_dirs: bool = False) -> list[Path]:
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
        "scratch",
        "examples",
    }
    if not include_test_dirs:
        exclude_dirs.update({"test-fixtures", "tests"})

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
            rule_id = rule_data.get("id") or f"<missing id at index {idx}>"
            missing_fields = []
            for err in ve.errors():
                if err.get("type") == "missing":
                    loc = err.get("loc")
                    if loc:
                        missing_fields.append(str(loc[0]))
            if missing_fields:
                raise ValueError(
                    f"Validation error: Rule '{rule_id}' is missing required field: {', '.join(missing_fields)}"
                )
            else:
                raise ValueError(f"Validation error in rule at index {idx}: {ve}")
        except ValueError as ve:
            raise ValueError(str(ve))

    return loaded_rules


def load_profile_rules(profile: str) -> list[GovernanceRule]:
    """Load default rules based on the profile name."""
    rules_dir = Path(__file__).parent.parent / "governance" / "rules" / "profiles"
    profile_path = rules_dir / f"{profile}.yaml"
    if not profile_path.exists():
        # Fall back to startup if profile file does not exist
        profile_path = rules_dir / "startup.yaml"
    return load_rules_from_yaml(profile_path)


def evaluate_rule(
    rule: GovernanceRule,
    root: Path,
    files: list[Path],
    existence_files: list[Path] | None = None,
) -> list[dict[str, Any]]:
    """Evaluate a single governance rule against the workspace files."""
    import hashlib

    findings = []
    existence_files = existence_files or files

    # 1. Resolve relative paths
    relative_paths = [f.relative_to(root) for f in files]
    existence_relative_paths = [f.relative_to(root) for f in existence_files]

    # 2. Check conditional execution (if_exists)
    if_exists = rule.match.if_exists
    if if_exists:
        if isinstance(if_exists, str):
            if_exists = [if_exists]

        condition_met = False
        for f in existence_relative_paths:
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

    # Default values logic
    confidence_val = rule.confidence
    if not confidence_val:
        confidence_val = (
            "high"
            if mtype
            in ("file_exists", "file_missing", "directory_exists", "directory_missing")
            else "medium"
        )

    remediation_val = rule.remediation_effort
    if not remediation_val:
        if rule.category == "secrets":
            remediation_val = "medium"
        elif rule.category in ("dependencies", "docs", "cicd", "health", "ai_risk"):
            remediation_val = "low"
        else:
            remediation_val = "medium"

    tags_val = list(rule.tags)
    if not tags_val:
        if rule.category == "secrets":
            tags_val = ["security", "secrets"]
        elif rule.category == "dependencies":
            tags_val = ["maintenance", "dependencies"]
        elif rule.category == "docs":
            tags_val = ["documentation"]
        elif rule.category == "tests":
            tags_val = ["testing"]
        elif rule.category == "cicd":
            tags_val = ["devops", "cicd"]
        elif rule.category == "health":
            tags_val = ["ops", "monitoring"]
        elif rule.category == "ai_risk":
            tags_val = ["ai", "governance"]
        else:
            tags_val = [rule.category]

    if mtype in ("file_exists", "filename_pattern"):
        for f in relative_paths:
            for pat in patterns:
                if fnmatch.fnmatch(f.name, pat) or fnmatch.fnmatch(str(f), pat):
                    fp_src = f"{rule.id}:{str(f)}:"
                    fingerprint = hashlib.sha256(fp_src.encode("utf-8")).hexdigest()
                    findings.append(
                        {
                            "schema_version": "1.0.0",
                            "id": rule.id,
                            "title": rule.title,
                            "category": rule.category,
                            "severity": rule.severity,
                            "confidence": confidence_val,
                            "file_path": str(f),
                            "line_number": None,
                            "description": rule.description,
                            "recommendation": rule.recommendation,
                            "remediation_effort": remediation_val,
                            "tags": tags_val,
                            "fingerprint": fingerprint,
                        }
                    )
                    break  # One finding per file

    elif mtype == "file_missing":
        # Check if ANY file matches the patterns
        for pat in patterns:
            matched = False
            for f in existence_relative_paths:
                if fnmatch.fnmatch(f.name, pat) or fnmatch.fnmatch(str(f), pat):
                    matched = True
                    break
            if matched:
                return []  # If any matching file exists, the dependency is NOT missing

        # If none of the files matched the lockfile/check patterns
        fp_src = f"{rule.id}::"
        fingerprint = hashlib.sha256(fp_src.encode("utf-8")).hexdigest()
        findings.append(
            {
                "schema_version": "1.0.0",
                "id": rule.id,
                "title": rule.title,
                "category": rule.category,
                "severity": rule.severity,
                "confidence": confidence_val,
                "file_path": "",
                "line_number": None,
                "description": rule.description,
                "recommendation": rule.recommendation,
                "remediation_effort": remediation_val,
                "tags": tags_val,
                "fingerprint": fingerprint,
            }
        )

    elif mtype in ("content_contains", "content_regex", "content_missing"):
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

        if mtype == "content_missing":
            found = False
            for f in target_files:
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    for pat in patterns:
                        if re.search(pat, content):
                            found = True
                            break
                    if found:
                        break
                except Exception:
                    pass

            if not found:
                fp_src = f"{rule.id}::"
                fingerprint = hashlib.sha256(fp_src.encode("utf-8")).hexdigest()
                findings.append(
                    {
                        "schema_version": "1.0.0",
                        "id": rule.id,
                        "title": rule.title,
                        "category": rule.category,
                        "severity": rule.severity,
                        "confidence": confidence_val,
                        "file_path": "",
                        "line_number": None,
                        "description": rule.description,
                        "recommendation": rule.recommendation,
                        "remediation_effort": remediation_val,
                        "tags": tags_val,
                        "fingerprint": fingerprint,
                    }
                )
            return findings

        for f in target_files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                rel = f.relative_to(root)

                for pat in patterns:
                    matched = False
                    line_num = None
                    if mtype == "content_contains":
                        if pat in content:
                            matched = True
                            lines = content.splitlines()
                            for idx, line in enumerate(lines, 1):
                                if pat in line:
                                    line_num = idx
                                    break
                    else:  # content_regex
                        if re.search(pat, content):
                            matched = True
                            lines = content.splitlines()
                            for idx, line in enumerate(lines, 1):
                                if re.search(pat, line):
                                    line_num = idx
                                    break

                    if matched:
                        fp_src = f"{rule.id}:{str(rel)}:{line_num or ''}"
                        fingerprint = hashlib.sha256(fp_src.encode("utf-8")).hexdigest()
                        findings.append(
                            {
                                "schema_version": "1.0.0",
                                "id": rule.id,
                                "title": rule.title,
                                "category": rule.category,
                                "severity": rule.severity,
                                "confidence": confidence_val,
                                "file_path": str(rel),
                                "line_number": line_num,
                                "description": rule.description,
                                "recommendation": rule.recommendation,
                                "remediation_effort": remediation_val,
                                "tags": tags_val,
                                "fingerprint": fingerprint,
                            }
                        )
                        break  # Limit to one finding of this type per file
            except Exception:
                pass

    elif mtype == "directory_exists":
        for pat in patterns:
            dir_path = root / pat
            if dir_path.is_dir():
                fp_src = f"{rule.id}:{pat}:"
                fingerprint = hashlib.sha256(fp_src.encode("utf-8")).hexdigest()
                findings.append(
                    {
                        "schema_version": "1.0.0",
                        "id": rule.id,
                        "title": rule.title,
                        "category": rule.category,
                        "severity": rule.severity,
                        "confidence": confidence_val,
                        "file_path": pat,
                        "line_number": None,
                        "description": rule.description,
                        "recommendation": rule.recommendation,
                        "remediation_effort": remediation_val,
                        "tags": tags_val,
                        "fingerprint": fingerprint,
                    }
                )

    elif mtype == "directory_missing":
        for pat in patterns:
            dir_path = root / pat
            if not dir_path.is_dir():
                fp_src = f"{rule.id}::"
                fingerprint = hashlib.sha256(fp_src.encode("utf-8")).hexdigest()
                findings.append(
                    {
                        "schema_version": "1.0.0",
                        "id": rule.id,
                        "title": rule.title,
                        "category": rule.category,
                        "severity": rule.severity,
                        "confidence": confidence_val,
                        "file_path": "",
                        "line_number": None,
                        "description": f"{rule.description} (Missing directory: {pat})",
                        "recommendation": rule.recommendation,
                        "remediation_effort": remediation_val,
                        "tags": tags_val,
                        "fingerprint": fingerprint,
                    }
                )

    return findings


def run_scanner_checks(
    root: Path,
    profile: str | None = None,
    custom_rules_path: Path | None = None,
    baseline_path: Path | None = None,
    create_baseline_path: Path | None = None,
) -> dict[str, Any]:
    """Run readiness checks using the rule engine and return a report."""
    from datetime import datetime, timezone
    import hashlib

    root = Path(root).resolve()
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1. Determine profile and load rules
    config = None
    min_coverage = None
    try:
        from niyam.core.config import load_niyam_config

        config = load_niyam_config(root)
        if config and config.governance and config.governance.scan:
            min_coverage = config.governance.scan.min_test_coverage
    except FileNotFoundError:
        pass
    except Exception as e:
        if (root / ".niyam" / "niyam.yaml").exists() or (
            root / ".sutra" / "sutra.yaml"
        ).exists():
            raise ValueError(f"Invalid Niyam configuration: {e}") from e

    if custom_rules_path:
        rules = load_rules_from_yaml(custom_rules_path)
        profile_name = "custom"
    else:
        if profile is None:
            if config and config.governance and config.governance.scan:
                profile = config.governance.scan.profile
            else:
                profile = "startup"
        rules = load_profile_rules(profile)
        profile_name = profile

    # 2. Gather scanned files. Content scanning intentionally skips tests and
    # fixtures; existence checks need the full inventory so real test suites,
    # lockfiles, and CI files are not missed.
    files = walk_files(root)
    existence_files = walk_files(root, include_test_dirs=True)

    # 3. Evaluate all rules
    findings = []
    for rule in rules:
        findings.extend(
            evaluate_rule(rule, root, files, existence_files=existence_files)
        )

    # Test coverage check
    if min_coverage is not None:
        try:
            from niyam.core.coverage import find_and_parse_coverage
            cov_result = find_and_parse_coverage(root)
            if cov_result:
                actual_coverage = cov_result["percentage"]
                if actual_coverage < min_coverage:
                    fp_src = f"TEST-COV-01::{actual_coverage}"
                    fingerprint = hashlib.sha256(fp_src.encode("utf-8")).hexdigest()
                    findings.append({
                        "schema_version": "1.0.0",
                        "id": "TEST-COV-01",
                        "title": "Insufficient Test Coverage",
                        "category": "tests",
                        "severity": "high",
                        "confidence": "high",
                        "file_path": cov_result["file"],
                        "line_number": None,
                        "description": f"Test coverage ({actual_coverage}%) is below the configured minimum threshold ({min_coverage}%).",
                        "recommendation": "Write more tests to increase coverage above the required threshold.",
                        "remediation_effort": "high",
                        "tags": ["testing", "coverage"],
                        "fingerprint": fingerprint,
                    })
            else:
                fp_src = "TEST-COV-02::"
                fingerprint = hashlib.sha256(fp_src.encode("utf-8")).hexdigest()
                findings.append({
                    "schema_version": "1.0.0",
                    "id": "TEST-COV-02",
                    "title": "Missing Test Coverage Report",
                    "category": "tests",
                    "severity": "medium",
                    "confidence": "high",
                    "file_path": "",
                    "line_number": None,
                    "description": f"Minimum test coverage is set to {min_coverage}%, but no recognizable coverage report (e.g. coverage.xml) was found.",
                    "recommendation": "Configure your test runner to generate a coverage report (e.g. coverage.xml or lcov.info).",
                    "remediation_effort": "low",
                    "tags": ["testing", "coverage"],
                    "fingerprint": fingerprint,
                })
        except Exception:
            pass

    # Run external security scanners (gitleaks, semgrep, trivy, checkov)
    try:
        from niyam.core.external_scanners import run_all_external_scanners

        findings.extend(
            run_all_external_scanners(
                root, config=config.model_dump() if config else None
            )
        )
    except Exception:
        pass

    # Skill Governance Check
    try:
        from niyam.core.skills import load_skill_registry
        skill_registry = load_skill_registry(root)
        for skill_name, skill in skill_registry.skills.items():
            if not skill.approved:
                fp_src = f"SKILL-001::{skill_name}"
                fingerprint = hashlib.sha256(fp_src.encode("utf-8")).hexdigest()
                findings.append({
                    "schema_version": "1.0.0",
                    "id": "SKILL-001",
                    "title": "Unapproved Agent Skill",
                    "category": "ai_risk",
                    "severity": "high" if skill.risk_level != "critical" else "critical",
                    "confidence": "high",
                    "file_path": f".niyam/skills/{skill_name}/SKILL.md",
                    "line_number": None,
                    "description": f"The agent skill '{skill_name}' is registered but has not been approved by an operator.",
                    "recommendation": f"Review the skill and run 'niyam skills approve {skill_name}' if it is safe.",
                    "remediation_effort": "low",
                    "tags": ["ai", "governance", "skills"],
                    "fingerprint": fingerprint,
                })
            elif skill.risk_level == "critical":
                fp_src = f"SKILL-002::{skill_name}"
                fingerprint = hashlib.sha256(fp_src.encode("utf-8")).hexdigest()
                findings.append({
                    "schema_version": "1.0.0",
                    "id": "SKILL-002",
                    "title": "Critical Risk Agent Skill",
                    "category": "ai_risk",
                    "severity": "medium", # Informational unless unapproved
                    "confidence": "high",
                    "file_path": f".niyam/skills/{skill_name}/SKILL.md",
                    "line_number": None,
                    "description": f"The agent skill '{skill_name}' has critical-level capabilities (e.g. shell execution).",
                    "recommendation": "Ensure this skill is only used by trusted agents in a sandboxed environment.",
                    "remediation_effort": "medium",
                    "tags": ["ai", "governance", "skills"],
                    "fingerprint": fingerprint,
                })
    except Exception:
        pass

    # Check for missing/skipped external scanners
    from niyam.core.external_scanners import SCANNER_REGISTRY
    import hashlib

    skipped_scanners = []
    # external_scanners may live outside the typed NiyamConfig model
    scanner_config: dict[str, Any] = {}
    if config is not None:
        dumped = config.model_dump()
        scanner_config = dumped.get("external_scanners") or {}
        if not scanner_config:
            # Support extra keys / raw yaml attachment if present
            raw = getattr(config, "model_extra", None) or {}
            if isinstance(raw, dict):
                scanner_config = raw.get("external_scanners") or {}
    for scanner in SCANNER_REGISTRY:
        # Only report as skipped if it's enabled in config but binary is missing
        sc_config = scanner_config.get(scanner.name, {})
        if not isinstance(sc_config, dict):
            sc_config = {}
        if sc_config.get("enabled", True):
            if not scanner.is_available(sc_config):
                skipped_scanners.append(scanner.name)

                # Optional scanners are informational by default so clean projects
                # are not NO_GO solely because gitleaks/trivy/checkov are absent.
                # Mark required: true in niyam.yaml to treat as high severity.
                is_required = bool(sc_config.get("required", False))
                severity = "high" if is_required else "info"
                binary_name = scanner.get_binary(sc_config)
                fp_src = f"EXT-SCAN-MISSING::{scanner.name}"
                fingerprint = hashlib.sha256(fp_src.encode("utf-8")).hexdigest()
                findings.append({
                    "schema_version": "1.0.0",
                    "id": f"EXT-SCAN-MISSING-{scanner.name.upper()}",
                    "title": f"Missing Enabled External Scanner: {scanner.name}",
                    "category": "tooling" if not is_required else "security",
                    "severity": severity,
                    "confidence": "high",
                    "file_path": "niyam.yaml",
                    "line_number": None,
                    "description": (
                        f"The external security scanner '{scanner.name}' is enabled "
                        f"in configuration, but its binary '{binary_name}' is not "
                        f"available on system PATH."
                        + (
                            " This scanner is marked required."
                            if is_required
                            else " Optional scanners do not block readiness by default."
                        )
                    ),
                    "recommendation": (
                        f"Install '{binary_name}' or set the correct path, or disable "
                        f"the scanner in niyam.yaml under "
                        f"'external_scanners.{scanner.name}.enabled: false'."
                        + (
                            ""
                            if is_required
                            else " To enforce this scanner, set "
                            f"'external_scanners.{scanner.name}.required: true'."
                        )
                    ),
                    "remediation_effort": "low",
                    "tags": ["security", "scanners"] if is_required else ["tooling", "scanners"],
                    "fingerprint": fingerprint,
                })

    # 3b. Apply/Create Baseline
    from niyam.core.baseline import load_baseline, apply_baseline, save_baseline

    baseline = {}
    if baseline_path:
        baseline = load_baseline(baseline_path)

    apply_baseline(findings, baseline)

    if create_baseline_path:
        project_name = root.name
        save_baseline(create_baseline_path, findings, project_name)
        new_baseline = load_baseline(create_baseline_path)
        apply_baseline(findings, new_baseline)

    # 4. Calculate score using only open findings
    open_findings = [f for f in findings if f.get("status") != "accepted_existing"]

    from niyam.governance.scoring import calculate_readiness_score

    score, scoring_breakdown, _ = calculate_readiness_score(
        open_findings, profile=profile_name
    )

    # 5. Check hard blockers and override decision/score using only open findings
    from niyam.governance.decision import evaluate_decision

    decision, decision_reason, score = evaluate_decision(
        open_findings, score, profile=profile_name, project_root=root
    )

    # 6. Calculate summary metrics
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        sev = f.get("severity", "info").lower()
        if sev in summary:
            summary[sev] += 1

    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "project_path": str(root),
        "profile": profile_name,
        "score": score,
        "readiness_score": score,
        "decision": decision,
        "decision_reason": decision_reason,
        "findings": findings,
        "summary": summary,
        "scoring_breakdown": scoring_breakdown,
        "redaction_status": {"redacted": True, "engine": "niyam-redaction"},
        "skipped_scanners": skipped_scanners,
    }
