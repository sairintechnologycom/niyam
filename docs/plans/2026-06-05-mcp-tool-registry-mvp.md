# Phase 4A — MCP/Tool Registry MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow users to register, classify, approve, and report on AI tools and MCP servers used by agents in local-first registry with secret redaction and proper risk classification.

**Architecture:** We will extend the existing Pydantic models in `niyam/core/mcp.py` to support new fields, upgrade risk classification heuristics to support risk classification v1, add recursive secret redaction before writing the registry JSON, and update the Typer commands in `niyam/cli/mcp.py` to add `niyam mcp approve <name>`, multiple `--capability` options, and duplicate registration update logic.

**Tech Stack:** Python, Typer, Pydantic, Rich, Pytest

---

### Task 1: Update MCPTool Model in Core

**Files:**
- Modify: `niyam/core/mcp.py`
- Test: `tests/test_mcp.py`

**Step 1: Write the failing test**

We will add a test in `tests/test_mcp.py` to assert that the new fields (`network_access`, `requires_approval`, `created_at`, `updated_at`, `schema_version`) are present in `MCPTool` model and serialize correctly.

```python
def test_mcp_tool_model_fields():
    from niyam.core.mcp import MCPTool
    tool = MCPTool(
        name="test-fields",
        type="mcp_server",
        risk_level="low",
        network_access="localhost",
        requires_approval=True,
        created_at="2026-06-05T10:00:00Z",
        updated_at="2026-06-05T10:00:00Z",
    )
    data = tool.model_dump()
    assert data["schema_version"] == "1.0.0"
    assert data["network_access"] == "localhost"
    assert data["requires_approval"] is True
    assert data["created_at"] == "2026-06-05T10:00:00Z"
    assert data["updated_at"] == "2026-06-05T10:00:00Z"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_mcp.py -k test_mcp_tool_model_fields`
Expected: FAIL with ValidationError or KeyError (fields not present in model)

**Step 3: Write minimal implementation**

Modify `niyam/core/mcp.py` to add the fields to `MCPTool` class:
```python
class MCPTool(BaseModel):
    """Pydantic model representing a registered tool or MCP server."""

    schema_version: str = "1.0.0"
    name: str
    type: Literal["mcp_server", "api", "cli", "local_tool", "browser", "other"]
    command_or_url: Optional[str] = None
    owner: Optional[str] = None
    risk_level: Literal["low", "medium", "high", "critical"]
    approved: bool = False
    capabilities: list[str] = Field(default_factory=list)
    data_access: Optional[str] = None
    network_access: Optional[str] = None
    requires_approval: bool = True
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_mcp.py -k test_mcp_tool_model_fields`
Expected: PASS

**Step 5: Commit**

```bash
git add niyam/core/mcp.py tests/test_mcp.py
git commit -m "feat(core): add new fields to MCPTool schema"
```

---

### Task 2: Implement Risk Classification v1

**Files:**
- Modify: `niyam/core/mcp.py`
- Test: `tests/test_mcp.py`

**Step 1: Write the failing test**

Add a test in `tests/test_mcp.py` for Risk Classification v1 mappings:
- `public_search` => low
- `docs_read` => medium
- `repo_read` => medium
- `file_write` => high
- `shell_execute` => critical
- `cloud_api` => critical
- `secrets_access` => critical
- `production_deploy` => critical

```python
def test_risk_classification_v1():
    from niyam.core.mcp import classify_risk
    assert classify_risk("search", "other", capabilities=["public_search"]) == "low"
    assert classify_risk("docs", "api", capabilities=["docs_read"]) == "medium"
    assert classify_risk("repo", "api", capabilities=["repo_read"]) == "medium"
    assert classify_risk("file", "local_tool", capabilities=["file_write"]) == "high"
    assert classify_risk("shell", "cli", capabilities=["shell_execute"]) == "critical"
    assert classify_risk("cloud", "api", capabilities=["cloud_api"]) == "critical"
    assert classify_risk("secrets", "other", capabilities=["secrets_access"]) == "critical"
    assert classify_risk("deploy", "other", capabilities=["production_deploy"]) == "critical"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_mcp.py -k test_risk_classification_v1`
Expected: FAIL (rules not fully implemented or returning wrong levels)

**Step 3: Write minimal implementation**

Modify `classify_risk` in `niyam/core/mcp.py` to evaluate these capability mappings exactly, using a severity priority so the highest risk capability determines the final risk level.

```python
def classify_risk(
    name: str,
    type: str,
    command_or_url: str | None = None,
    capabilities: list[str] | None = None,
    data_access: str | None = None,
    notes: str | None = None,
) -> Literal["low", "medium", "high", "critical"]:
    import re

    caps = [c.lower().strip() for c in (capabilities or [])]
    text = f"{name} {command_or_url or ''} {data_access or ''} {notes or ''}".lower()

    # Risk level priority mapping
    risk_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    inv_risk_levels = {1: "low", 2: "medium", 3: "high", 4: "critical"}
    max_risk_val = 0

    # Map capabilities directly
    capability_risks = {
        "production_deploy": 4,
        "secrets_access": 4,
        "cloud_api": 4,
        "shell_execute": 4,
        "file_write": 3,
        "repo_read": 2,
        "docs_read": 2,
        "public_search": 1,
    }

    for cap in caps:
        if cap in capability_risks:
            max_risk_val = max(max_risk_val, capability_risks[cap])

    # Fallback to text heuristics if no capability matched or to refine
    def has_word(words: list[str], target: str) -> bool:
        for w in words:
            if re.search(r"\b" + re.escape(w) + r"\b", target):
                return True
        return False

    text_critical = ["shell", "bash", "zsh", "terminal", "powershell", "aws", "gcp", "azure", "kubernetes", "k8s", "secret", "deploy", "publish"]
    text_high = ["file", "filesystem", "write", "create", "delete", "modify"]
    text_medium = ["docs", "doc", "wiki", "read-only", "repo", "repository"]
    text_low = ["search", "google", "query", "web"]

    if max_risk_val < 4 and (has_word(text_critical, text) or any(k in caps for k in ["run_command", "execute", "exec", "secrets_access", "cloud_api", "shell_execute", "production_deploy"])):
        max_risk_val = max(max_risk_val, 4)
    if max_risk_val < 3 and (has_word(text_high, text) or "file_write" in caps):
        max_risk_val = max(max_risk_val, 3)
    if max_risk_val < 2 and (has_word(text_medium, text) or any(k in caps for k in ["docs_read", "repo_read"])):
        max_risk_val = max(max_risk_val, 2)
    if max_risk_val < 1 and (has_word(text_low, text) or "public_search" in caps):
        max_risk_val = max(max_risk_val, 1)

    if max_risk_val == 0:
        return "medium"  # Default fallback
    return inv_risk_levels[max_risk_val]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_mcp.py -k test_risk_classification_v1`
Expected: PASS

**Step 5: Commit**

```bash
git add niyam/core/mcp.py tests/test_mcp.py
git commit -m "feat(core): implement risk classification v1 heuristics"
```

---

### Task 3: Implement Secret Redaction before Save

**Files:**
- Modify: `niyam/core/mcp.py`
- Test: `tests/test_mcp.py`

**Step 1: Write the failing test**

Add a test in `tests/test_mcp.py` to verify secrets (like API keys) are redacted when saving the registry.

```python
def test_save_registry_redacts_secrets(tmp_path: Path):
    from niyam.core.mcp import MCPRegistry, MCPTool, save_mcp_registry
    registry = MCPRegistry()
    registry.tools["secret-tool"] = MCPTool(
        name="secret-tool",
        type="api",
        command_or_url="https://api.example.com?key=sk-ant-123456789012345678901234",
        owner="test",
        risk_level="medium",
        notes="Secret password is 'supersecretpasswd123'",
    )
    save_mcp_registry(registry, root=tmp_path)
    
    registry_file = tmp_path / ".niyam" / "mcp-registry.json"
    content = registry_file.read_text(encoding="utf-8")
    assert "sk-ant-" not in content
    assert "supersecretpasswd123" not in content
    assert "[REDACTED_SECRET]" in content
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_mcp.py -k test_save_registry_redacts_secrets`
Expected: FAIL (secrets written in plain text to the file)

**Step 3: Write minimal implementation**

Modify `save_mcp_registry` in `niyam/core/mcp.py` to import and call `redact_secrets` on the dictionary representation before JSON dump.

```python
def save_mcp_registry(registry: MCPRegistry, root: Path | None = None) -> None:
    """Save the MCP/tool registry locally to the JSON file with secret redaction."""
    path = get_mcp_registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    from niyam.governance.common.redaction import redact_secrets
    redacted_data = redact_secrets(registry.model_dump())
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(redacted_data, f, indent=2)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_mcp.py -k test_save_registry_redacts_secrets`
Expected: PASS

**Step 5: Commit**

```bash
git add niyam/core/mcp.py tests/test_mcp.py
git commit -m "feat(core): redact secrets before writing registry file"
```

---

### Task 4: Add Multiple Capability Flags and Update/Duplicate Logic to CLI Register

**Files:**
- Modify: `niyam/cli/mcp.py`
- Test: `tests/test_mcp.py`

**Step 1: Write the failing test**

Add tests for:
- Registering a tool using multiple `--capability` flags.
- Registering a duplicate tool without `--update` (fails clearly).
- Registering a duplicate tool with `--update` (updates fields and updates `updated_at` while preserving `created_at`).

```python
def test_mcp_register_multiple_capability(tmp_path: Path):
    from typer.testing import CliRunner
    from niyam.cli import app
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "mcp", "register", "multi-cap",
            "--type", "cli",
            "--capability", "file_read",
            "--capability", "file_write",
        ]
    )
    assert result.exit_code == 0
    
    # Check stored capabilities
    from niyam.core.mcp import load_mcp_registry
    reg = load_mcp_registry(tmp_path)
    assert reg.tools["multi-cap"].capabilities == ["file_read", "file_write"]

def test_mcp_register_duplicate_with_update(tmp_path: Path):
    from typer.testing import CliRunner
    from niyam.cli import app
    runner = CliRunner()
    
    # First register
    runner.invoke(app, ["mcp", "register", "dup-tool", "--type", "api", "--notes", "old notes"])
    
    # Second register without --update (fails)
    res_fail = runner.invoke(app, ["mcp", "register", "dup-tool", "--type", "api", "--notes", "new notes"])
    assert res_fail.exit_code == 1
    assert "already registered" in res_fail.stdout
    
    # Third register with --update (succeeds)
    res_ok = runner.invoke(app, ["mcp", "register", "dup-tool", "--type", "api", "--notes", "new notes", "--update"])
    assert res_ok.exit_code == 0
    assert "successfully registered" in res_ok.stdout or "updated" in res_ok.stdout
    
    # Check fields
    from niyam.core.mcp import load_mcp_registry
    reg = load_mcp_registry(tmp_path)
    tool = reg.tools["dup-tool"]
    assert tool.notes == "new notes"
    assert tool.created_at is not None
    assert tool.updated_at is not None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_mcp.py -k "test_mcp_register_multiple_capability or test_mcp_register_duplicate_with_update"`
Expected: FAIL

**Step 3: Write minimal implementation**

Modify `niyam/cli/mcp.py` to:
1. Make `type` optional in `mcp_register`.
2. Add `capability: Annotated[Optional[list[str]], typer.Option("--capability", help="Capability...")] = None`
3. Add `network_access: Annotated[Optional[str], typer.Option("--network-access", help="...")] = None`
4. Add `requires_approval: Annotated[Optional[str], typer.Option("--requires-approval", help="...")] = None`
5. Add `update: Annotated[bool, typer.Option("--update", help="...")] = False`
6. Merge `--capability` and `--capabilities`.
7. Handle duplicate update check & merge logic. Set `created_at` and `updated_at`.
8. Redact CLI arguments using `redact_text` before creating the tool object.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_mcp.py -k "test_mcp_register_multiple_capability or test_mcp_register_duplicate_with_update"`
Expected: PASS

**Step 5: Commit**

```bash
git add niyam/cli/mcp.py tests/test_mcp.py
git commit -m "feat(cli): support multiple capability options and update flag on register"
```

---

### Task 5: Implement MCP Approve Command

**Files:**
- Modify: `niyam/cli/mcp.py`
- Test: `tests/test_mcp.py`

**Step 1: Write the failing test**

Add a test in `tests/test_mcp.py` to verify `niyam mcp approve <name>`:

```python
def test_mcp_approve_tool(tmp_path: Path):
    from typer.testing import CliRunner
    from niyam.cli import app
    runner = CliRunner()
    
    # Register tool as not approved
    runner.invoke(app, ["mcp", "register", "app-tool", "--type", "api", "--approved", "false"])
    
    # Approve tool
    result = runner.invoke(app, ["mcp", "approve", "app-tool"])
    assert result.exit_code == 0
    assert "successfully approved" in result.stdout
    
    # Check registry
    from niyam.core.mcp import load_mcp_registry
    reg = load_mcp_registry(tmp_path)
    assert reg.tools["app-tool"].approved is True
    assert reg.tools["app-tool"].updated_at is not None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_mcp.py -k test_mcp_approve_tool`
Expected: FAIL with command not found or exit code 2.

**Step 3: Write minimal implementation**

Add `@mcp_app.command("approve")` command to `niyam/cli/mcp.py`.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_mcp.py -k test_mcp_approve_tool`
Expected: PASS

**Step 5: Commit**

```bash
git add niyam/cli/mcp.py tests/test_mcp.py
git commit -m "feat(cli): add niyam mcp approve command"
```

---

### Task 6: Update CLI Show Command to Display All Fields

**Files:**
- Modify: `niyam/cli/mcp.py`
- Test: `tests/test_mcp.py`

**Step 1: Write the failing test**

Add a test in `tests/test_mcp.py` to verify `niyam mcp show` output includes the new fields.

```python
def test_mcp_show_all_fields(tmp_path: Path):
    from typer.testing import CliRunner
    from niyam.cli import app
    runner = CliRunner()
    
    runner.invoke(
        app,
        [
            "mcp", "register", "show-tool",
            "--type", "api",
            "--network-access", "internet",
            "--requires-approval", "true",
        ]
    )
    
    result = runner.invoke(app, ["mcp", "show", "show-tool"])
    assert result.exit_code == 0
    assert "Network Access:" in result.stdout
    assert "Requires Approval:" in result.stdout
    assert "Created At:" in result.stdout
    assert "Updated At:" in result.stdout
    assert "Schema Version:" in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_mcp.py -k test_mcp_show_all_fields`
Expected: FAIL (fields missing from stdout)

**Step 3: Write minimal implementation**

Update `mcp_show` in `niyam/cli/mcp.py` to print:
- `Schema Version:`
- `Network Access:`
- `Requires Approval:`
- `Created At:`
- `Updated At:`

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_mcp.py -k test_mcp_show_all_fields`
Expected: PASS

**Step 5: Commit**

```bash
git add niyam/cli/mcp.py tests/test_mcp.py
git commit -m "feat(cli): update show command to display new registry fields"
```

---

### Task 7: Update Documentation

**Files:**
- Modify: `docs/mcp-registry.md` or similar, and updates in `README.md` if necessary. Let's create `docs/mcp-registry.md` if it doesn't exist, detailing the command usage, risk classification, sample registry, and enterprise approval pattern.

**Step 1: Verify documentation requirements**
Create `docs/mcp-registry.md` with:
- MCP registry usage commands (`niyam mcp register/list/show/approve/risk-report`).
- Risk classification v1 table.
- Sample registry JSON showing schema_version and redaction.
- Enterprise approval pattern explanation.

**Step 2: Write documentation file**
Create `docs/mcp-registry.md`.

**Step 3: Commit**

```bash
git add docs/mcp-registry.md
git commit -m "docs: add MCP registry guide and risk classification documentation"
```

---

### Task 8: Final Verification & Clean up

**Step 1: Run full regression tests**

Run: `uv run pytest` to ensure no regression across all niyam features.

**Step 2: Verify offline execution**

Ensure all changes execute offline without calling any external APIs.
