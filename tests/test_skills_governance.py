import pytest
from pathlib import Path
import json
from niyam.core.skills import register_skill, load_skill_registry, parse_skill_file
from niyam.core.scan import run_scanner_checks

def test_skill_manifest_parsing(tmp_path: Path):
    """Test parsing a skill file with frontmatter."""
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    
    content = """---
name: "test-skill"
version: "2.0.0"
capabilities: ["run_command", "read_file"]
---
# Prompt
Execute some commands.
"""
    skill_file.write_text(content)
    
    manifest, checksum, prompt = parse_skill_file(skill_file)
    
    assert manifest.name == "test-skill"
    assert manifest.version == "2.0.0"
    assert "run_command" in manifest.capabilities
    assert "Execute some commands." in prompt
    assert checksum is not None

def test_skill_registration(tmp_path: Path):
    """Test registering a skill in the registry."""
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("---\nname: 'test-skill'\ncapabilities: ['read_file']\n---\nPrompt content")
    
    # Register the skill
    skill = register_skill(skill_file, root=tmp_path)
    
    assert skill.manifest.name == "test-skill"
    assert skill.risk_level == "medium"
    assert skill.approved is True  # Auto-approved because risk <= medium
    
    # Load registry and verify
    registry = load_skill_registry(root=tmp_path)
    assert "test-skill" in registry.skills
    assert registry.skills["test-skill"].manifest.version == "1.0.0"

def test_high_risk_skill_requires_approval(tmp_path: Path):
    """Test that high risk skills are not auto-approved."""
    skill_dir = tmp_path / "critical-skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    # 'run_command' triggers critical risk
    skill_file.write_text("---\nname: 'critical-skill'\ncapabilities: ['run_command']\n---\nPrompt content")
    
    skill = register_skill(skill_file, root=tmp_path)
    
    assert skill.risk_level == "critical"
    assert skill.approved is False
    assert skill.requires_approval is True

def test_scanner_flags_unapproved_skill(tmp_path: Path):
    """Test that niyam scan flags unapproved skills."""
    # Setup niyam root
    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir()
    (niyam_dir / "niyam.yaml").write_text("project:\n  name: test\n")
    
    # Create and register a critical skill
    skill_dir = niyam_dir / "skills" / "evil-skill"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("---\nname: 'evil-skill'\ncapabilities: ['run_command']\n---\nPrompt content")
    
    register_skill(skill_file, root=tmp_path)
    
    # Run scan
    report = run_scanner_checks(tmp_path)
    
    findings = [f for f in report["findings"] if f["id"] == "SKILL-001"]
    assert len(findings) == 1
    assert findings[0]["severity"] == "critical"
    assert "evil-skill" in findings[0]["description"]
    
    # Verify decision is NO_GO due to critical finding
    assert report["decision"] == "NO_GO"
    assert "Hard blocker triggered" in report["decision_reason"]
