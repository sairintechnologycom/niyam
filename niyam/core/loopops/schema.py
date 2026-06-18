"""LoopSpec Pydantic models for Niyam LoopOps."""

from __future__ import annotations

from typing import Optional, Any, Literal
from pydantic import BaseModel, Field


class LoopMetadata(BaseModel):
    """Metadata for the loop specification."""

    model_config = {"populate_by_name": True, "extra": "allow"}

    name: str = Field(..., alias="name")
    owner: str = Field(..., alias="owner")
    risk_tier: Optional[str] = Field(None, alias="riskTier")


class LoopGoal(BaseModel):
    """Goal configuration for the loop."""

    model_config = {"populate_by_name": True, "extra": "allow"}

    type: str = Field(..., alias="type")
    description: str = Field(..., alias="description")


class LoopStep(BaseModel):
    """A single step within the execution loop."""

    model_config = {"populate_by_name": True, "extra": "allow"}

    name: str = Field(..., alias="name")
    action: str = Field(..., alias="action")
    required_evidence: Optional[list[str]] = Field(None, alias="requiredEvidence")
    max_attempts: Optional[int] = Field(None, alias="maxAttempts")
    policy: Optional[dict[str, Any]] = Field(None, alias="policy")
    actor: Optional[str] = Field(None, alias="actor")
    evaluator: Optional[str] = Field(None, alias="evaluator")


class LoopBudgets(BaseModel):
    """Execution budgets for safety limits."""

    model_config = {"populate_by_name": True, "extra": "allow"}

    max_iterations: int = Field(..., alias="maxIterations")
    max_tokens: Optional[int] = Field(None, alias="maxTokens")
    max_cost_usd: Optional[float] = Field(None, alias="maxCostUsd")
    max_runtime_minutes: Optional[int] = Field(None, alias="maxRuntimeMinutes")


class LoopEvaluator(BaseModel):
    """An evaluator/critic that runs after step execution to assess quality."""

    model_config = {"populate_by_name": True, "extra": "allow"}

    name: str = Field(..., alias="name")
    type: Literal["ai_critic", "command"] = Field(..., alias="type")
    actor: Optional[str] = Field(None, alias="actor")
    command: Optional[str] = Field(None, alias="command")
    required: bool = Field(True, alias="required")
    criteria: Optional[str] = Field(None, alias="criteria")


class LoopWorkspace(BaseModel):
    """Workspace configuration for isolation."""

    model_config = {"populate_by_name": True, "extra": "allow"}

    isolation: Optional[str] = Field("git_worktree", alias="isolation")
    base_branch: Optional[str] = Field("main", alias="baseBranch")
    working_branch_prefix: Optional[str] = Field("niyam-loop/", alias="workingBranchPrefix")


class LoopSpec(BaseModel):
    """Top-level LoopSpec configuration model."""

    model_config = {"populate_by_name": True, "extra": "allow"}

    api_version: str = Field(..., alias="apiVersion")
    kind: str = Field("LoopSpec", alias="kind")
    metadata: LoopMetadata = Field(..., alias="metadata")
    goal: LoopGoal = Field(..., alias="goal")
    actors: dict[str, str] = Field(default_factory=dict, alias="actors")
    steps: list[LoopStep] = Field(default_factory=list, alias="steps")
    workspace: Optional[LoopWorkspace] = Field(default_factory=LoopWorkspace, alias="workspace")
    budgets: LoopBudgets = Field(..., alias="budgets")
    stop_conditions: list[str] = Field(default_factory=list, alias="stopConditions")
    evaluators: list[LoopEvaluator] = Field(default_factory=list, alias="evaluators")


