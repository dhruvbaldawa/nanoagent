# ABOUTME: Pydantic data models for agent coordination
# ABOUTME: Type-safe structured outputs for reliable agent communication

import logging
import secrets
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


def generate_task_id() -> str:
    """Generate a cryptographically secure 8-character task ID"""
    # Use secrets module for cryptographic security instead of predictable fallback
    return secrets.token_urlsafe(6)[:8]


class TaskStatus(str, Enum):
    """Task status enumeration"""

    PENDING = "pending"
    DONE = "done"
    CANCELLED = "cancelled"


class Task(BaseModel):
    """Represents a single task in the todo list"""

    id: str = Field(
        default_factory=generate_task_id,
        description="8-character task identifier",
        min_length=8,
        max_length=8,
    )
    description: str = Field(..., description="Task description", min_length=1)
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task status")
    priority: int = Field(default=5, ge=1, le=10, description="Task priority (1-10)")


class TaskPlanOutput(BaseModel):
    """Output from task planning agent"""

    tasks: list[str] = Field(..., description="List of tasks to execute", max_length=50)
    questions: list[str] = Field(default_factory=list, description="Questions for human clarification", max_length=20)


class ExecutionResult(BaseModel):
    """Result from task execution"""

    success: bool = Field(..., description="Whether execution succeeded")
    output: str = Field(..., description="Execution output or error message")


class ReflectionOutput(BaseModel):
    """Output from reflection agent"""

    done: bool = Field(..., description="Whether goal is complete")
    gaps: list[str] = Field(..., description="Identified gaps or issues", max_length=20)
    new_tasks: list[str] = Field(..., description="New tasks to address gaps", max_length=20)
    complete_ids: list[str] = Field(default_factory=list, description="IDs of completed tasks", max_length=50)


class AgentStatus(str, Enum):
    """Agent run status enumeration"""

    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class AgentRunResult(BaseModel):
    """Generic result from any agent run"""

    output: str = Field(..., description="Agent output")
    status: AgentStatus = Field(..., description="Agent run status")
