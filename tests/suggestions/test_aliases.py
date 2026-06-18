import yaml
from niyam.suggestions.aliases import get_aliases, resolve_alias

def test_resolve_alias(monkeypatch, tmp_path):
    # Mock find_niyam_root to point to tmp_path
    monkeypatch.setattr("niyam.suggestions.aliases.find_niyam_root", lambda: tmp_path)
    
    # Create mock config
    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir()
    config_path = niyam_dir / "config.yaml"
    
    config_data = {
        "aliases": {
            "lr": "loop run",
            "lv": "loop validate"
        }
    }
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)
        
    assert get_aliases() == {"lr": "loop run", "lv": "loop validate"}
    
    # Test resolving
    assert resolve_alias("lr") == "loop run"
    assert resolve_alias("lr --planner claude") == "loop run --planner claude"
    assert resolve_alias("lv loops/test.yaml") == "loop validate loops/test.yaml"
    assert resolve_alias("unknown") == "unknown"
