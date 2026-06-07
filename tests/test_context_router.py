import pytest
from pathlib import Path
from niyam.core.context import ContextRouter

def test_prune_repo_map_tree():
    router = ContextRouter(Path("."))
    repo_map = """Directory listing for /app
├── src/api/main.py
├── src/api/models.py
├── src/api/utils.py
├── src/web/app.tsx
├── docs/index.md
└── package.json
"""
    allowed = ["src/api/models.py"]
    pruned = router.prune_repo_map(repo_map, allowed)
    
    assert "src/api/models.py" in pruned
    assert "src/api/main.py" in pruned # Sibling
    assert "src/api/utils.py" in pruned # Sibling
    assert "src/web/app.tsx" not in pruned
    assert "docs/index.md" not in pruned

def test_prune_repo_map_flat():
    router = ContextRouter(Path("."))
    repo_map = """src/api/main.py
src/api/models.py
src/api/utils.py
src/web/app.tsx
docs/index.md
package.json
"""
    allowed = ["src/api/models.py"]
    pruned = router.prune_repo_map(repo_map, allowed)
    
    assert "src/api/models.py" in pruned
    assert "src/api/main.py" in pruned # Sibling
    assert "src/api/utils.py" in pruned # Sibling
    assert "src/web/app.tsx" not in pruned
    assert "docs/index.md" not in pruned

def test_prune_repo_map_no_match_conservative():
    router = ContextRouter(Path("."))
    repo_map = "\n".join([f"file{i}.txt" for i in range(50)])
    allowed = ["something/else.py"]
    pruned = router.prune_repo_map(repo_map, allowed)
    
    # Should return first 30 lines + ellipsis if no match found (conservative)
    lines = pruned.splitlines()
    assert len(lines) == 31
    assert "..." in lines[-1]
