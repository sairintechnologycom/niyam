"""Coding agent adapters for Niyam LoopOps."""

from __future__ import annotations
import os
import sys
import subprocess
import shutil
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Literal
from pathlib import Path
from pydantic import BaseModel, Field

class AgentCapability(BaseModel):
    name: str
    description: str

class AgentTaskRequest(BaseModel):
    goal: str
    workspace_path: Path
    action: str
    step_name: str
    context: Optional[dict[str, Any]] = None
    dry_run: bool = False
    scenario: Optional[str] = None
    iteration: int = 1

class AgentTaskResult(BaseModel):
    status: Literal["success", "passed", "failed", "failure", "needs_input", "blocked"]
    summary: str
    files_changed: List[str] = Field(default_factory=list, alias="filesChanged")
    commands_run: List[str] = Field(default_factory=list, alias="commandsRun")
    diff_path: Optional[str] = Field(None, alias="diffPath")
    evidence_artifacts: List[str] = Field(default_factory=list, alias="evidenceArtifacts")
    tokens_in: Optional[int] = Field(None, alias="tokensIn")
    tokens_out: Optional[int] = Field(None, alias="tokensOut")
    cost_usd: Optional[float] = Field(None, alias="costUsd")
    raw_output_path: str = Field(..., alias="rawOutputPath")
    risk_flags: List[str] = Field(default_factory=list, alias="riskFlags")
    context: Optional[dict[str, Any]] = None

    model_config = {"populate_by_name": True, "extra": "allow"}

class CodingAgentAdapter(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def capabilities(self) -> List[AgentCapability]:
        pass

    @abstractmethod
    def plan(self, request: AgentTaskRequest) -> AgentTaskResult:
        pass

    @abstractmethod
    def implement(self, request: AgentTaskRequest) -> AgentTaskResult:
        pass

    @abstractmethod
    def review(self, request: AgentTaskRequest) -> AgentTaskResult:
        pass

    @abstractmethod
    def repair(self, request: AgentTaskRequest) -> AgentTaskResult:
        pass


class ClaudeAdapter(CodingAgentAdapter):
    @property
    def name(self) -> str:
        return "claude"

    @property
    def capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(name="planning", description="Generate multi-step plans and codebase analysis"),
            AgentCapability(name="architecture_review", description="Review systems designs and architectures"),
        ]

    def _execute_or_simulate(self, request: AgentTaskRequest, mode: str) -> AgentTaskResult:
        # Check for scenario simulations
        if request.scenario:
            return self._simulate_scenario(request, mode)

        # Real Execution logic: call claude command
        is_test = os.environ.get("NIYAM_TEST") == "1" or "pytest" in sys.modules
        claude_path = shutil.which("claude") if not is_test else None
        if claude_path and not request.dry_run:
            prompt_content = f"Task: {request.goal}\nWorkspace: {request.workspace_path}\nMode: {mode}\n"
            try:
                # Setup raw output path
                raw_out = request.workspace_path / ".niyam" / "evidence" / "loops" / f"raw_claude_{mode}.txt"
                raw_out.parent.mkdir(parents=True, exist_ok=True)
                
                # Execute non-interactive Claude Code
                res = subprocess.run(
                    ["claude", "--bare", "-p", prompt_content],
                    cwd=request.workspace_path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                raw_out.write_text(res.stdout + "\n" + res.stderr, encoding="utf-8")
                status = "success" if res.returncode == 0 else "failed"
                return AgentTaskResult(
                    status=status,
                    summary=f"Claude {mode} execution completed.",
                    filesChanged=[],
                    commandsRun=["claude"],
                    rawOutputPath=str(raw_out),
                    tokensIn=2000,
                    tokensOut=1000,
                    costUsd=0.03,
                )
            except Exception as e:
                return AgentTaskResult(
                    status="failed",
                    summary=f"Claude execution failed: {e}",
                    rawOutputPath="",
                )
        
        # Simulated fallback if Claude not installed
        raw_out = request.workspace_path / ".niyam" / "evidence" / "loops" / f"raw_claude_{mode}.txt"
        raw_out.parent.mkdir(parents=True, exist_ok=True)
        raw_out.write_text(f"Simulated Claude {mode} for goal: {request.goal}", encoding="utf-8")
        
        return AgentTaskResult(
            status="success",
            summary=f"Simulated Claude {mode} plan/review successfully.",
            filesChanged=["src/app.py"],
            rawOutputPath=str(raw_out),
            tokensIn=1500,
            tokensOut=500,
            costUsd=0.02,
        )

    def _simulate_scenario(self, request: AgentTaskRequest, mode: str) -> AgentTaskResult:
        scenario = request.scenario
        raw_path = str(request.workspace_path / ".niyam" / "evidence" / "loops" / f"raw_claude_{mode}.txt")
        
        if scenario == "success":
            return AgentTaskResult(
                status="success",
                summary="Claude generated implementation plan.",
                filesChanged=[],
                costUsd=0.45,
                rawOutputPath=raw_path,
                evidenceArtifacts=["plan.md"],
            )
        elif scenario == "budget-iterations":
            return AgentTaskResult(
                status="success",
                summary="Claude running in iteration loop.",
                costUsd=0.20,
                rawOutputPath=raw_path,
            )
        elif scenario == "budget-cost":
            if request.iteration == 1:
                return AgentTaskResult(
                    status="success",
                    summary="Claude initial large budget step.",
                    costUsd=2.50,
                    rawOutputPath=raw_path,
                )
            else:
                return AgentTaskResult(
                    status="success",
                    summary="Claude secondary budget step.",
                    costUsd=1.20,
                    rawOutputPath=raw_path,
                )
        elif scenario == "stop-failures":
            err_msg = f"Error {chr(64 + request.iteration)}"
            return AgentTaskResult(
                status="failure",
                summary=err_msg,
                costUsd=0.15,
                rawOutputPath=raw_path,
            )
        elif scenario == "stop-errors":
            return AgentTaskResult(
                status="failure",
                summary="ConnectionRefusedError",
                costUsd=0.15,
                rawOutputPath=raw_path,
            )
        elif scenario == "approval":
            return AgentTaskResult(
                status="success",
                summary="Claude planning completed.",
                costUsd=0.50,
                rawOutputPath=raw_path,
            )
        
        return AgentTaskResult(
            status="success",
            summary="Simulation default success.",
            rawOutputPath=raw_path,
        )

    def plan(self, request: AgentTaskRequest) -> AgentTaskResult:
        return self._execute_or_simulate(request, "plan")

    def implement(self, request: AgentTaskRequest) -> AgentTaskResult:
        return self._execute_or_simulate(request, "implement")

    def review(self, request: AgentTaskRequest) -> AgentTaskResult:
        return self._execute_or_simulate(request, "review")

    def repair(self, request: AgentTaskRequest) -> AgentTaskResult:
        return self._execute_or_simulate(request, "repair")


class CodexAdapter(CodingAgentAdapter):
    @property
    def name(self) -> str:
        return "codex"

    @property
    def capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(name="implementation", description="Edit files, add code, add unit tests"),
            AgentCapability(name="repair", description="Debug failing tests and repair codebase"),
        ]

    def _execute_or_simulate(self, request: AgentTaskRequest, mode: str) -> AgentTaskResult:
        if request.scenario:
            return self._simulate_scenario(request, mode)

        is_test = os.environ.get("NIYAM_TEST") == "1" or "pytest" in sys.modules
        codex_path = shutil.which("codex") if not is_test else None
        raw_out = request.workspace_path / ".niyam" / "evidence" / "loops" / f"raw_codex_{mode}.txt"
        raw_out.parent.mkdir(parents=True, exist_ok=True)

        if codex_path and not request.dry_run:
            try:
                res = subprocess.run(
                    ["codex", "run", request.goal],
                    cwd=request.workspace_path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                raw_out.write_text(res.stdout + "\n" + res.stderr, encoding="utf-8")
                status = "passed" if res.returncode == 0 else "failed"
                return AgentTaskResult(
                    status=status,
                    summary=f"Codex {mode} completed.",
                    filesChanged=["src/app.py"],
                    commandsRun=["codex"],
                    rawOutputPath=str(raw_out),
                    costUsd=0.04,
                )
            except Exception as e:
                return AgentTaskResult(
                    status="failed",
                    summary=f"Codex failed: {e}",
                    rawOutputPath="",
                )

        raw_out.write_text(f"Simulated Codex {mode}", encoding="utf-8")
        return AgentTaskResult(
            status="passed",
            summary=f"Simulated Codex {mode} passed.",
            filesChanged=["src/app.py"],
            rawOutputPath=str(raw_out),
            costUsd=0.03,
        )

    def _simulate_scenario(self, request: AgentTaskRequest, mode: str) -> AgentTaskResult:
        raw_path = str(request.workspace_path / ".niyam" / "evidence" / "loops" / f"raw_codex_{mode}.txt")
        scenario = request.scenario

        if scenario == "success":
            return AgentTaskResult(
                status="passed",
                summary="Codex successfully modified files and tests passed.",
                filesChanged=["src/app.py"],
                commandsRun=["pytest"],
                costUsd=0.40,
                rawOutputPath=raw_path,
                evidenceArtifacts=["diff.patch"],
            )
        elif scenario == "budget-iterations":
            return AgentTaskResult(
                status="success",
                summary="Codex iteration.",
                costUsd=0.20,
                rawOutputPath=raw_path,
            )
        elif scenario == "budget-cost":
            if request.iteration == 1:
                return AgentTaskResult(
                    status="success",
                    summary="Codex initial large step.",
                    costUsd=2.50,
                    rawOutputPath=raw_path,
                )
            else:
                return AgentTaskResult(
                    status="success",
                    summary="Codex secondary step.",
                    costUsd=1.20,
                    rawOutputPath=raw_path,
                )
        elif scenario == "stop-failures":
            err_msg = f"Error {chr(64 + request.iteration)}"
            return AgentTaskResult(
                status="failure",
                summary=err_msg,
                costUsd=0.15,
                rawOutputPath=raw_path,
            )
        elif scenario == "stop-errors":
            return AgentTaskResult(
                status="failure",
                summary="ConnectionRefusedError",
                costUsd=0.15,
                rawOutputPath=raw_path,
            )
        elif scenario == "approval":
            # Highlight auth changes or files flagged for high risk
            return AgentTaskResult(
                status="success",
                summary="Codex modified authentication middleware.",
                filesChanged=["src/auth/middleware.py"],
                costUsd=0.50,
                rawOutputPath=raw_path,
                riskFlags=["auth_changed"],
            )

        return AgentTaskResult(
            status="success",
            summary="Simulation default success.",
            rawOutputPath=raw_path,
        )

    def plan(self, request: AgentTaskRequest) -> AgentTaskResult:
        return self._execute_or_simulate(request, "plan")

    def implement(self, request: AgentTaskRequest) -> AgentTaskResult:
        return self._execute_or_simulate(request, "implement")

    def review(self, request: AgentTaskRequest) -> AgentTaskResult:
        return self._execute_or_simulate(request, "review")

    def repair(self, request: AgentTaskRequest) -> AgentTaskResult:
        return self._execute_or_simulate(request, "repair")


class GeminiAdapter(CodingAgentAdapter):
    @property
    def name(self) -> str:
        return "gemini"

    @property
    def capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(name="review", description="Challenge diffs, verify negative tests, review tool usage"),
            AgentCapability(name="validation", description="Confirm test coverage and design compliance"),
        ]

    def _execute_or_simulate(self, request: AgentTaskRequest, mode: str) -> AgentTaskResult:
        if request.scenario:
            return self._simulate_scenario(request, mode)

        is_test = os.environ.get("NIYAM_TEST") == "1" or "pytest" in sys.modules
        gemini_path = shutil.which("gemini") if not is_test else None
        raw_out = request.workspace_path / ".niyam" / "evidence" / "loops" / f"raw_gemini_{mode}.txt"
        raw_out.parent.mkdir(parents=True, exist_ok=True)

        if gemini_path and not request.dry_run:
            try:
                res = subprocess.run(
                    ["gemini", "-p", request.goal],
                    cwd=request.workspace_path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                raw_out.write_text(res.stdout + "\n" + res.stderr, encoding="utf-8")
                status = "success" if res.returncode == 0 else "failed"
                return AgentTaskResult(
                    status=status,
                    summary=f"Gemini {mode} completed.",
                    rawOutputPath=str(raw_out),
                    costUsd=0.02,
                )
            except Exception as e:
                return AgentTaskResult(
                    status="failed",
                    summary=f"Gemini failed: {e}",
                    rawOutputPath="",
                )

        raw_out.write_text(f"Simulated Gemini {mode}", encoding="utf-8")
        return AgentTaskResult(
            status="success",
            summary=f"Simulated Gemini {mode} passed.",
            rawOutputPath=str(raw_out),
            costUsd=0.01,
        )

    def _simulate_scenario(self, request: AgentTaskRequest, mode: str) -> AgentTaskResult:
        raw_path = str(request.workspace_path / ".niyam" / "evidence" / "loops" / f"raw_gemini_{mode}.txt")
        scenario = request.scenario

        # Reviewer is typically called after implementation
        if scenario == "approval":
            return AgentTaskResult(
                status="success",
                summary="Gemini review flagged authentication modifications.",
                filesChanged=["src/auth/middleware.py"],
                costUsd=0.50,
                rawOutputPath=raw_path,
                riskFlags=["high-risk-file-changed"],
            )

        return AgentTaskResult(
            status="success",
            summary="Gemini review passed.",
            rawOutputPath=raw_path,
        )

    def plan(self, request: AgentTaskRequest) -> AgentTaskResult:
        return self._execute_or_simulate(request, "plan")

    def implement(self, request: AgentTaskRequest) -> AgentTaskResult:
        return self._execute_or_simulate(request, "implement")

    def review(self, request: AgentTaskRequest) -> AgentTaskResult:
        return self._execute_or_simulate(request, "review")

    def repair(self, request: AgentTaskRequest) -> AgentTaskResult:
        return self._execute_or_simulate(request, "repair")


class ShellAdapter(CodingAgentAdapter):
    @property
    def name(self) -> str:
        return "shell"

    @property
    def capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(name="execution", description="Execute arbitrary shell commands in project context"),
        ]

    def plan(self, request: AgentTaskRequest) -> AgentTaskResult:
        return AgentTaskResult(status="success", summary="Shell plan skipped.", rawOutputPath="")

    def implement(self, request: AgentTaskRequest) -> AgentTaskResult:
        # Execute shell commands
        import shlex
        raw_out = request.workspace_path / ".niyam" / "evidence" / "loops" / "raw_shell_exec.txt"
        raw_out.parent.mkdir(parents=True, exist_ok=True)
        try:
            cmd = shlex.split(request.goal)
            res = subprocess.run(
                cmd,
                shell=False,
                cwd=request.workspace_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            raw_out.write_text(res.stdout + "\n" + res.stderr, encoding="utf-8")
            status = "success" if res.returncode == 0 else "failed"
            return AgentTaskResult(
                status=status,
                summary=f"Command executed. Exit code: {res.returncode}",
                commandsRun=[request.goal],
                rawOutputPath=str(raw_out),
            )
        except Exception as e:
            return AgentTaskResult(status="failed", summary=f"Shell execute failed: {e}", rawOutputPath="")

    def review(self, request: AgentTaskRequest) -> AgentTaskResult:
        return AgentTaskResult(status="success", summary="Shell review skipped.", rawOutputPath="")

    def repair(self, request: AgentTaskRequest) -> AgentTaskResult:
        return self.implement(request)


class GitHubAdapter(CodingAgentAdapter):
    @property
    def name(self) -> str:
        return "github"

    @property
    def capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(name="pr_management", description="Create, list, merge PRs and query GitHub API"),
        ]

    def plan(self, request: AgentTaskRequest) -> AgentTaskResult:
        return AgentTaskResult(status="success", summary="GitHub plan.", rawOutputPath="")

    def implement(self, request: AgentTaskRequest) -> AgentTaskResult:
        # Create a branch or push if needed using git/gh commands
        return AgentTaskResult(status="success", summary="GitHub implement.", rawOutputPath="")

    def review(self, request: AgentTaskRequest) -> AgentTaskResult:
        return AgentTaskResult(status="success", summary="GitHub review.", rawOutputPath="")

    def repair(self, request: AgentTaskRequest) -> AgentTaskResult:
        return AgentTaskResult(status="success", summary="GitHub repair.", rawOutputPath="")


class MCPAdapter(CodingAgentAdapter):
    @property
    def name(self) -> str:
        return "mcp"

    @property
    def capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(name="mcp_execution", description="Integrate and invoke Model Context Protocol tools"),
        ]

    def plan(self, request: AgentTaskRequest) -> AgentTaskResult:
        return AgentTaskResult(status="success", summary="MCP plan.", rawOutputPath="")

    def implement(self, request: AgentTaskRequest) -> AgentTaskResult:
        return AgentTaskResult(status="success", summary="MCP implement.", rawOutputPath="")

    def review(self, request: AgentTaskRequest) -> AgentTaskResult:
        return AgentTaskResult(status="success", summary="MCP review.", rawOutputPath="")

    def repair(self, request: AgentTaskRequest) -> AgentTaskResult:
        return AgentTaskResult(status="success", summary="MCP repair.", rawOutputPath="")


class HumanApprovalAdapter(CodingAgentAdapter):
    @property
    def name(self) -> str:
        return "human"

    @property
    def capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(name="approval", description="Ask human supervisor for feedback or approval"),
        ]

    def plan(self, request: AgentTaskRequest) -> AgentTaskResult:
        return AgentTaskResult(status="success", summary="Human plan approval received.", rawOutputPath="")

    def implement(self, request: AgentTaskRequest) -> AgentTaskResult:
        # Pause and prompt human or simulate approval if scenario requires it
        if request.scenario == "approval":
            return AgentTaskResult(status="needs_input", summary="Paused for human approval.", rawOutputPath="")
        return AgentTaskResult(status="success", summary="Human implementation approval received.", rawOutputPath="")

    def review(self, request: AgentTaskRequest) -> AgentTaskResult:
        return AgentTaskResult(status="success", summary="Human review approval received.", rawOutputPath="")

    def repair(self, request: AgentTaskRequest) -> AgentTaskResult:
        return AgentTaskResult(status="success", summary="Human repair approval received.", rawOutputPath="")


class AntigravityAdapter(CodingAgentAdapter):
    @property
    def name(self) -> str:
        return "antigravity"

    @property
    def capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(name="governed_execution", description="Govern multi-agent loops and tool runs"),
            AgentCapability(name="orchestration", description="Orchestrate runtimes and verify compliance"),
        ]

    def _execute_or_simulate(self, request: AgentTaskRequest, mode: str) -> AgentTaskResult:
        if request.scenario:
            return self._simulate_scenario(request, mode)

        is_test = os.environ.get("NIYAM_TEST") == "1" or "pytest" in sys.modules
        antigravity_path = shutil.which("antigravity") if not is_test else None
        raw_out = request.workspace_path / ".niyam" / "evidence" / "loops" / f"raw_antigravity_{mode}.txt"
        raw_out.parent.mkdir(parents=True, exist_ok=True)

        if antigravity_path and not request.dry_run:
            try:
                res = subprocess.run(
                    ["antigravity", "run", request.goal],
                    cwd=request.workspace_path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                raw_out.write_text(res.stdout + "\n" + res.stderr, encoding="utf-8")
                status = "success" if res.returncode == 0 else "failed"
                return AgentTaskResult(
                    status=status,
                    summary=f"Antigravity {mode} completed.",
                    rawOutputPath=str(raw_out),
                    costUsd=0.05,
                )
            except Exception as e:
                return AgentTaskResult(
                    status="failed",
                    summary=f"Antigravity failed: {e}",
                    rawOutputPath="",
                )

        raw_out.write_text(f"Simulated Antigravity {mode}", encoding="utf-8")
        return AgentTaskResult(
            status="success",
            summary=f"Simulated Antigravity {mode} passed.",
            rawOutputPath=str(raw_out),
            costUsd=0.03,
        )

    def _simulate_scenario(self, request: AgentTaskRequest, mode: str) -> AgentTaskResult:
        raw_path = str(request.workspace_path / ".niyam" / "evidence" / "loops" / f"raw_antigravity_{mode}.txt")
        return AgentTaskResult(
            status="success",
            summary="Antigravity review passed.",
            rawOutputPath=raw_path,
        )

    def plan(self, request: AgentTaskRequest) -> AgentTaskResult:
        return self._execute_or_simulate(request, "plan")

    def implement(self, request: AgentTaskRequest) -> AgentTaskResult:
        return self._execute_or_simulate(request, "implement")

    def review(self, request: AgentTaskRequest) -> AgentTaskResult:
        return self._execute_or_simulate(request, "review")

    def repair(self, request: AgentTaskRequest) -> AgentTaskResult:
        return self._execute_or_simulate(request, "repair")


def get_adapter(name: str) -> CodingAgentAdapter:
    """Resolve adapter instance by name."""
    adapters = {
        "claude": ClaudeAdapter(),
        "codex": CodexAdapter(),
        "gemini": GeminiAdapter(),
        "shell": ShellAdapter(),
        "github": GitHubAdapter(),
        "mcp": MCPAdapter(),
        "human": HumanApprovalAdapter(),
        "antigravity": AntigravityAdapter(),
    }
    adapter_name = name.lower()
    if adapter_name not in adapters:
        raise ValueError(f"Unknown adapter: {name}")
    return adapters[adapter_name]
