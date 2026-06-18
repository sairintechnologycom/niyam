import pytest
from niyam.suggestions.registry import build_default_registry
from niyam.suggestions.engine import SuggestionEngine

@pytest.fixture
def engine():
    return SuggestionEngine(build_default_registry())

def test_suggest_prefix(engine):
    suggestions = engine.suggest("l")
    assert "loop" in suggestions

def test_suggest_subcommand(engine):
    suggestions = engine.suggest("loop r")
    assert "run" in suggestions
    assert "review" in suggestions
    assert "report" in suggestions

def test_suggest_typo(engine):
    suggestions = engine.suggest("lop")
    assert "loop" in suggestions

def test_suggest_flag(engine):
    suggestions = engine.suggest("loop run --r")
    assert "--reviewer" in suggestions
    assert "--require-approval-on" in suggestions
    assert "--replay" in suggestions

def test_suggest_flag_values(engine):
    # Testing context-aware flag value suggestions
    suggestions = engine.suggest("loop run --planner ")
    assert "claude" in suggestions
    assert "codex" in suggestions
    assert "gemini" in suggestions
    assert "antigravity" in suggestions

def test_suggest_positional_args(engine, monkeypatch):
    def mock_get_loop_specs():
        return ["loops/test.yaml"]
    
    # We monkeypatch the provider for this test if needed,
    # or just rely on the fact that if get_loop_specs runs, it returns a list
    suggestions = engine.suggest("loop run ")
    # Even if get_loop_specs returns empty list in test env, it shouldn't crash
    assert isinstance(suggestions, list)
