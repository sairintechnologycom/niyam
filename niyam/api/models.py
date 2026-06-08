"""Niyam API models and schemas."""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel


class MissionSummary(BaseModel):
    id: str
    status: str
    orchestrator: str
    created: str
    task_count: int
    completed_tasks: int
    readiness_score: Optional[int] = None
    decision: Optional[str] = None


class TaskInfo(BaseModel):
    id: str
    title: str
    agent: str
    status: str
    duration: float
    depends_on: list[str]


class TokenMetrics(BaseModel):
    actual_tokens: int
    actual_cost_usd: float
    wasted_cost_usd: float = 0.0
    savings_tokens: int
    savings_cost_usd: float
    savings_percent: float


class MissionDetails(BaseModel):
    id: str
    status: str
    orchestrator: str
    created: str
    parallel: int
    worktree: bool
    tasks: list[TaskInfo]
    metrics: Optional[TokenMetrics] = None
    readiness_score: Optional[int] = None
    decision: Optional[str] = None


class ActionResponse(BaseModel):
    success: bool
    message: str
    new_status: Optional[str] = None
