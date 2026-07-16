"""Small deterministic runtime for fixture-based harness tests."""

from __future__ import annotations

import difflib
import hashlib
import json
import shlex
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from niyam.governance.common.redaction import contains_secret, redact_secrets, redact_text
from niyam.harness.sandbox import LocalSandbox
from niyam.harness.evidence import verify_evidence, write_manifest


class ScriptedModel:
    """Returns predefined model actions without calling a provider."""

    def __init__(self, actions: list[dict[str, Any]]) -> None:
        self._actions = iter(actions)

    def next_action(self) -> dict[str, Any] | None:
        return next(self._actions, None)


@dataclass
class HarnessResult:
    state: str
    changed_files: set[str]
    evaluation: dict[str, str]
    events: list[dict[str, Any]]
    evidence_path: Path

    @property
    def event_types(self) -> list[str]:
        return [event["type"] for event in self.events]

    def events_by_type(self, event_type: str) -> list[dict[str, Any]]:
        return [event for event in self.events if event["type"] == event_type]


class Harness:
    """Executes scripted actions in a copied fixture with scoped writes."""

    REGISTERED_TOOLS = {"workspace.patch", "test.run", "security.scan", "dependency.install", "memory.propose", "shell.exec"}
    DESTRUCTIVE_COMMANDS = (
        "rm -rf", "git reset --hard", "git push --force", "drop table",
        "drop database", "terraform apply", "terraform destroy", "npm publish",
    )

    def __init__(self, fixture: Path, workspace: Path, model: ScriptedModel, sandbox: Any | None = None) -> None:
        self.fixture = fixture
        self.workspace = workspace
        self.model = model
        self.run_id = f"run_{uuid.uuid4().hex}"
        self.sandbox = sandbox or LocalSandbox()
        task = yaml.safe_load((fixture / ".niyam/task.yaml").read_text(encoding="utf-8"))
        self.allowed_files = set(task["allowed_files"])
        self.required_commands = set(task["required_commands"])
        self.contract_hash = hashlib.sha256(
            (fixture / ".niyam/task.yaml").read_bytes()
        ).hexdigest()
        self.events: list[dict[str, Any]] = []
        self.changed_files: set[str] = set()
        self.original_files: dict[str, str] = {}
        self.test_outputs: list[str] = []
        self.executed_commands: list[str] = []
        self.dependency_commands: list[str] = []
        self.evidence_path = workspace / ".niyam/evidence"
        self.completion_claim_accepted = False
        self.out_of_scope_attempts = 0
        self.terminal_state: str | None = None
        self.denied_call_counts: dict[str, int] = {}
        self.security_scan_passed: bool | None = None
        self.pending_approval_id: str | None = None
        self.pending_dependency_command: str | None = None
        self.approval_granted = False
        self.started = False
        self.completed_actions = 0

    @classmethod
    def for_test(
        cls, *, fixture: Path, workspace: Path, model: ScriptedModel, sandbox: Any | None = None
    ) -> "Harness":
        return cls(fixture, workspace, model, sandbox)

    def run(self, max_actions: int | None = None) -> HarnessResult:
        if not self.started:
            shutil.copytree(self.fixture, self.workspace)
            self.started = True
            self._event("TASK_RECEIVED")
            self._event("PLAN_CREATED")
        state = "EXECUTING"
        actions_run = 0

        if self.pending_dependency_command:
            if not self.approval_granted:
                state = "WAITING_APPROVAL"
            else:
                self._run_dependency_install(self.pending_dependency_command)
                self.pending_dependency_command = None
                self.pending_approval_id = None
                self.approval_granted = False

        while state == "EXECUTING" and (action := self.model.next_action()) is not None:
            if action["type"] == "tool_call":
                self._tool_call(action["tool"], action["arguments"])
                self.completed_actions += 1
                actions_run += 1
                self._save_checkpoint()
                if self.pending_dependency_command:
                    state = "WAITING_APPROVAL"
                    break
                if self.terminal_state:
                    state = self.terminal_state
                    break
            elif action["type"] == "final":
                self._event("COMPLETION_EVALUATED")
                evaluation = self._evaluate()
                if all(result == "PASS" for name, result in evaluation.items() if name != "evidence"):
                    self.completion_claim_accepted = True
                    break
                self._event("COMPLETION_REJECTED", reason=self._rejection_reason(evaluation))
            if max_actions is not None and actions_run >= max_actions:
                state = "INTERRUPTED"
                self._event("RUN_INTERRUPTED")
                break

        if state == "EXECUTING" and self.security_scan_passed is False:
            state = "FAILED"
            self._event("RUN_FAILED", reason="security_scan_failed")

        evaluation = self._evaluate()
        self._write_evidence(evaluation)
        self._rewrite_events()
        write_manifest(self.evidence_path, self.run_id)
        evaluation["evidence"] = "PASS" if not verify_evidence(self.evidence_path) else "FAIL"
        (self.evidence_path / "evaluator-results.json").write_text(
            json.dumps(evaluation, indent=2) + "\n", encoding="utf-8"
        )
        write_manifest(self.evidence_path, self.run_id)
        if self.completion_claim_accepted and evaluation["evidence"] == "PASS":
            state = "COMPLETED"
            self._event("RUN_COMPLETED")
            self._rewrite_events()
            write_manifest(self.evidence_path, self.run_id)
        return HarnessResult(state, self.changed_files, evaluation, self.events, self.evidence_path)

    def resume(self) -> HarnessResult:
        # ponytail: in-process resume; reconstruct a fresh runtime from the checkpoint before claiming crash recovery.
        checkpoint = json.loads((self.workspace / ".niyam/checkpoint.json").read_text(encoding="utf-8"))
        if checkpoint["run_id"] != self.run_id or checkpoint["contract_hash"] != self.contract_hash:
            raise ValueError("checkpoint does not match this harness run")
        self._event("RUN_RESUMED", run_id=self.run_id)
        return self.run()

    def approve(self, approval_id: str, command: str) -> None:
        if approval_id != self.pending_approval_id or command != self.pending_dependency_command:
            raise ValueError("approval does not match the pending command")
        self.approval_granted = True
        self._event("APPROVAL_GRANTED", approval_id=approval_id)

    def _tool_call(self, tool: str, arguments: dict[str, Any]) -> None:
        event_count = len(self.events)
        if tool not in self.REGISTERED_TOOLS:
            self._event("TOOL_DENIED", tool=tool, reason="unknown_tool")
        elif tool == "workspace.patch":
            self._patch(arguments)
        elif tool == "test.run":
            self._run_test(arguments["command"])
        elif tool == "security.scan":
            self._run_security_scan(arguments["command"])
        elif tool == "dependency.install":
            self.pending_dependency_command = arguments["command"]
            self.pending_approval_id = f"approval_{self.run_id}_{self.completed_actions + 1}"
            self._event("APPROVAL_REQUESTED", approval_id=self.pending_approval_id, command=arguments["command"])
        elif tool == "memory.propose":
            self._event("MEMORY_PROPOSAL_REJECTED", reason="missing_source_ref")
        elif tool == "shell.exec":
            self._shell_exec(arguments["command"])
        if any(event["type"] in {"DENIED_BY_POLICY", "TOOL_DENIED"} for event in self.events[event_count:]):
            self._record_denied_call(tool, arguments)

    def _record_denied_call(self, tool: str, arguments: dict[str, Any]) -> None:
        key = f"{tool}:{json.dumps(arguments, sort_keys=True)}"
        self.denied_call_counts[key] = self.denied_call_counts.get(key, 0) + 1
        if self.denied_call_counts[key] == 2:
            self._event("LOOP_DETECTED", tool=tool)
            self._event("REPLAN_REQUESTED")
        elif self.denied_call_counts[key] >= 3:
            self.terminal_state = "ESCALATED"
            self._event("RUN_ESCALATED", reason="repeated_tool_loop")

    def _patch(self, arguments: dict[str, Any]) -> None:
        path = arguments["path"]
        if path not in self.allowed_files:
            self._event("PATCH_DENIED", path=path, rule="allowed_files")
            self.out_of_scope_attempts += 1
            if self.out_of_scope_attempts >= 2:
                self.terminal_state = "ESCALATED"
                self._event("RUN_ESCALATED", reason="repeated_out_of_scope_write")
            return
        target = self.workspace / path
        self.original_files.setdefault(path, target.read_text(encoding="utf-8"))
        target.write_text(arguments["content"], encoding="utf-8")
        self.changed_files.add(path)
        self._event("PATCH_APPLIED", path=path)

    def _run_test(self, command: str) -> None:
        self.executed_commands.append(command)
        try:
            completed = self.sandbox.run(shlex.split(command), self.workspace)
        except (OSError, subprocess.TimeoutExpired, TimeoutError) as exc:
            self.terminal_state = "ESCALATED"
            self._event("SANDBOX_CRASHED", reason=type(exc).__name__)
            self._event("RUN_ESCALATED", reason="sandbox_crash")
            return
        output = redact_text(completed.stdout + completed.stderr)
        self.test_outputs.append(output)
        self._event("TEST_PASSED" if completed.returncode == 0 else "TEST_FAILED", command=command)

    def _run_security_scan(self, command: str) -> None:
        completed = self.sandbox.run(shlex.split(command), self.workspace)
        self.security_scan_passed = completed.returncode == 0
        self._event("SECURITY_SCAN_PASSED" if self.security_scan_passed else "SECURITY_SCAN_FAILED", command=command)

    def _run_dependency_install(self, command: str) -> None:
        completed = self.sandbox.run(shlex.split(command), self.workspace)
        self.dependency_commands.append(command)
        self._event("DEPENDENCY_INSTALLED" if completed.returncode == 0 else "DEPENDENCY_INSTALL_FAILED", command=command)

    def _shell_exec(self, command: str) -> None:
        normalized = command.strip().lower()
        if "|" in normalized and any(client in normalized for client in ("curl", "wget")) and any(shell in normalized for shell in (" sh", " bash")):
            self._event("DENIED_BY_POLICY", command=command, rule="pipe_to_shell")
        elif any(normalized.startswith(pattern) for pattern in self.DESTRUCTIVE_COMMANDS):
            self._event("DENIED_BY_POLICY", command=command, rule="destructive_command")
        elif normalized.startswith(("curl ", "wget ")):
            self._event("DENIED_BY_POLICY", command=command, rule="network_default_deny")
        else:
            self._event("TOOL_DENIED", tool="shell.exec", reason="not_authorized_by_contract")

    def _tests_passed(self) -> bool:
        last_test = next(
            (event["type"] for event in reversed(self.events) if event["type"].startswith("TEST_")),
            None,
        )
        return last_test == "TEST_PASSED"

    def _evaluate(self) -> dict[str, str]:
        executed = {self._normalized_command(command) for command in self.executed_commands}
        required = {self._normalized_command(command) for command in self.required_commands}
        return {
            "tests": "PASS" if self._tests_passed() and required <= executed else "FAIL",
            "scope": "PASS" if self.changed_files <= self.allowed_files else "FAIL",
            "security": "FAIL" if self.security_scan_passed is False else "PASS",
            "evidence": "PENDING",
        }

    @staticmethod
    def _normalized_command(command: str) -> str:
        tokens = shlex.split(command)
        if tokens and Path(tokens[0]).name.startswith("python"):
            tokens[0] = "python"
        return shlex.join(tokens)

    @staticmethod
    def _rejection_reason(evaluation: dict[str, str]) -> str:
        if evaluation["tests"] == "FAIL":
            return "missing_required_test_evidence"
        if evaluation["scope"] == "FAIL":
            return "out_of_scope_changes"
        if evaluation["security"] == "FAIL":
            return "security_scan_failed"
        return "missing_required_evidence"

    def _event(self, event_type: str, **details: Any) -> None:
        has_secret = contains_secret(json.dumps(details))
        self.events.append({"sequence": len(self.events) + 1, "type": event_type, **redact_secrets(details)})
        if has_secret:
            self.events.append({
                "sequence": len(self.events) + 1,
                "type": "SECRET_REDACTED",
                "source_event": event_type,
            })

    def _save_checkpoint(self) -> None:
        checkpoint_path = self.workspace / ".niyam/checkpoint.json"
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.write_text(json.dumps({
            "run_id": self.run_id,
            "contract_hash": self.contract_hash,
            "completed_actions": self.completed_actions,
        }, indent=2) + "\n", encoding="utf-8")
        self._event("CHECKPOINT_SAVED", completed_actions=self.completed_actions)

    def _write_evidence(self, evaluation: dict[str, str]) -> None:
        self.evidence_path.mkdir(parents=True, exist_ok=True)
        (self.evidence_path / "task-contract.yaml").write_text(
            (self.fixture / ".niyam/task.yaml").read_text(encoding="utf-8"), encoding="utf-8"
        )
        (self.evidence_path / "execution-plan.yaml").write_text("steps: [discover, reproduce, implement, validate, finalize]\n", encoding="utf-8")
        (self.evidence_path / "tool-calls.jsonl").write_text("\n".join(json.dumps(event) for event in self.events if event["type"] in {"PATCH_APPLIED", "PATCH_DENIED", "TEST_FAILED", "TEST_PASSED"}) + "\n", encoding="utf-8")
        (self.evidence_path / "tests-before.txt").write_text(self.test_outputs[0] if self.test_outputs else "", encoding="utf-8")
        (self.evidence_path / "tests-after.txt").write_text(self.test_outputs[-1] if self.test_outputs else "", encoding="utf-8")
        (self.evidence_path / "diff.patch").write_text(self._diff(), encoding="utf-8")
        (self.evidence_path / "evaluator-results.json").write_text(json.dumps(evaluation, indent=2) + "\n", encoding="utf-8")
        (self.evidence_path / "provenance.json").write_text(json.dumps({"model": "scripted", "fixture": self.fixture.name}, indent=2) + "\n", encoding="utf-8")
        (self.evidence_path / "final-report.md").write_text(f"# Harness run\n\nState: {evaluation['tests']}\n", encoding="utf-8")
        self._event("EVIDENCE_FINALIZED")

    def _rewrite_events(self) -> None:
        (self.evidence_path / "events.jsonl").write_text(
            "\n".join(json.dumps(event) for event in self.events) + "\n", encoding="utf-8"
        )

    def _diff(self) -> str:
        return "".join(
            "".join(
                difflib.unified_diff(
                    original.splitlines(keepends=True),
                    (self.workspace / path).read_text(encoding="utf-8").splitlines(keepends=True),
                    fromfile=f"a/{path}", tofile=f"b/{path}",
                )
            )
            for path, original in self.original_files.items()
        )
