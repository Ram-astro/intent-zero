from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

ActionType = Literal["think", "analyze", "transform", "prepare", "review", "notify", "external_action"]

class PlanRequest(BaseModel):
    goal: str = Field(min_length=3, max_length=2000)

class WorkflowStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=600)
    action_type: ActionType = "think"
    depends_on: list[str] = Field(default_factory=list)
    requires_approval: bool = False

class WorkflowPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    goal: str
    domain: str
    summary: str
    steps: list[WorkflowStep] = Field(min_length=1, max_length=12)
    assumptions: list[str] = Field(default_factory=list)
    planner_mode: Literal["ollama", "fallback"] = "fallback"

class ValidationIssue(BaseModel):
    severity: Literal["error", "warning", "info"]
    code: str
    message: str

class ValidationResponse(BaseModel):
    valid: bool
    issues: list[ValidationIssue]
    checked_steps: int
