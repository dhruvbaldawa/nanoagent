# ABOUTME: Test Pydantic data models with comprehensive validation
# ABOUTME: Ensures structured outputs from agents are reliable and type-safe

# type: ignore  # Ignore type checking violations in test files
# pyright: reportMissingImports = warning
# pyright: reportUnusedCallResult = none

import string

import pytest
from pydantic import ValidationError

# These imports will fail initially - models don't exist yet
from nanoagent.models.schemas import (
    AgentRunResult,
    AgentStatus,
    ExecutionResult,
    ReflectionOutput,
    Task,
    TaskPlanOutput,
    TaskStatus,
    generate_task_id,
)


class TestTask:
    """Test Task model validation and behavior"""

    def test_task_creation_valid(self):
        """Test valid task creation with defaults"""
        task = Task(description="Implement data models")
        assert task.description == "Implement data models"
        assert task.status == TaskStatus.PENDING
        assert task.priority == 5
        assert len(task.id) == 8  # 8-character UUID

    def test_task_creation_custom_values(self):
        """Test task creation with custom values"""
        task = Task(description="Test task", status=TaskStatus.DONE, priority=3)
        assert task.description == "Test task"
        assert task.status == TaskStatus.DONE
        assert task.priority == 3

    def test_task_missing_description(self):
        """Test task creation fails without description"""
        with pytest.raises(ValidationError) as exc_info:
            Task()
        assert "description" in str(exc_info.value)

    def test_task_invalid_status(self):
        """Test task creation fails with invalid status"""
        with pytest.raises(ValidationError) as exc_info:
            Task(description="Test", status="invalid")
        assert "status" in str(exc_info.value)

    def test_task_status_enum_values(self):
        """Test that TaskStatus enum has correct values"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.DONE.value == "done"
        assert TaskStatus.CANCELLED.value == "cancelled"

    def test_task_invalid_priority(self):
        """Test task creation fails with invalid priority type"""
        with pytest.raises(ValidationError) as exc_info:
            Task(description="Test", priority="high")
        assert "priority" in str(exc_info.value)


class TestTaskPlanOutput:
    """Test TaskPlanOutput model validation and behavior"""

    def test_task_plan_output_minimal(self):
        """Test valid creation with minimal data"""
        plan = TaskPlanOutput(tasks=["Task 1", "Task 2"])
        assert plan.tasks == ["Task 1", "Task 2"]
        assert plan.questions == []  # Default empty list

    def test_task_plan_output_with_questions(self):
        """Test valid creation with questions"""
        plan = TaskPlanOutput(tasks=["Task 1"], questions=["Need clarification?", "What format?"])
        assert plan.tasks == ["Task 1"]
        assert plan.questions == ["Need clarification?", "What format?"]

    def test_task_plan_output_empty_tasks(self):
        """Test valid creation with empty tasks"""
        plan = TaskPlanOutput(tasks=[])
        assert plan.tasks == []
        assert plan.questions == []

    def test_task_plan_output_invalid_tasks_type(self):
        """Test creation fails with non-list tasks"""
        with pytest.raises(ValidationError) as exc_info:
            TaskPlanOutput(tasks="Task 1")
        assert "tasks" in str(exc_info.value)

    def test_task_plan_output_invalid_questions_type(self):
        """Test creation fails with non-list questions"""
        with pytest.raises(ValidationError) as exc_info:
            TaskPlanOutput(tasks=[], questions="question")
        assert "questions" in str(exc_info.value)


class TestExecutionResult:
    """Test ExecutionResult model validation and behavior"""

    def test_execution_result_success(self):
        """Test successful execution result"""
        result = ExecutionResult(success=True, output="Task completed")
        assert result.success is True
        assert result.output == "Task completed"

    def test_execution_result_failure(self):
        """Test failed execution result"""
        result = ExecutionResult(success=False, output="Error occurred")
        assert result.success is False
        assert result.output == "Error occurred"

    def test_execution_result_missing_success(self):
        """Test creation fails without success field"""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionResult(output="Some output")
        assert "success" in str(exc_info.value)

    def test_execution_result_missing_output(self):
        """Test creation fails without output field"""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionResult(success=True)
        assert "output" in str(exc_info.value)

    def test_execution_result_invalid_success_type(self):
        """Test creation fails with non-boolean success"""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionResult(success="invalid", output="output")
        assert "success" in str(exc_info.value)


class TestReflectionOutput:
    """Test ReflectionOutput model validation and behavior"""

    def test_reflection_output_complete(self):
        """Test complete reflection output"""
        result = ReflectionOutput(
            done=True,
            gaps=["Missing validation", "No error handling"],
            new_tasks=["Add tests", "Handle errors"],
            complete_ids=["task1", "task2"],
        )
        assert result.done is True
        assert result.gaps == ["Missing validation", "No error handling"]
        assert result.new_tasks == ["Add tests", "Handle errors"]
        assert result.complete_ids == ["task1", "task2"]

    def test_reflection_output_minimal(self):
        """Test minimal reflection output"""
        result = ReflectionOutput(done=False, gaps=[], new_tasks=["Continue implementation"])
        assert result.done is False
        assert result.gaps == []
        assert result.new_tasks == ["Continue implementation"]
        assert result.complete_ids == []  # Default empty list

    def test_reflection_output_empty_lists(self):
        """Test reflection output with all empty lists"""
        result = ReflectionOutput(done=True, gaps=[], new_tasks=[])
        assert result.done is True
        assert result.gaps == []
        assert result.new_tasks == []
        assert result.complete_ids == []

    def test_reflection_output_invalid_done_type(self):
        """Test creation fails with non-boolean done"""
        with pytest.raises(ValidationError) as exc_info:
            ReflectionOutput(done="invalid", gaps=[], new_tasks=[])
        assert "done" in str(exc_info.value)

    def test_reflection_output_invalid_list_types(self):
        """Test creation fails with non-list fields"""
        with pytest.raises(ValidationError):
            ReflectionOutput(
                done=True,
                gaps="gap",  # Should be list
                new_tasks=[],
            )

        with pytest.raises(ValidationError):
            ReflectionOutput(
                done=True,
                gaps=[],
                new_tasks="task",  # Should be list
            )


class TestAgentRunResult:
    """Test AgentRunResult model validation and behavior"""

    def test_agent_run_result_success(self):
        """Test successful agent run result"""
        result = AgentRunResult(output="Agent completed successfully", status=AgentStatus.COMPLETED)
        assert result.output == "Agent completed successfully"
        assert result.status == "completed"

    def test_agent_run_result_failure(self):
        """Test failed agent run result"""
        result = AgentRunResult(output="Agent failed with error", status=AgentStatus.FAILED)
        assert result.output == "Agent failed with error"
        assert result.status == "failed"

    def test_agent_run_result_missing_output(self):
        """Test creation fails without output"""
        with pytest.raises(ValidationError) as exc_info:
            AgentRunResult(status="completed")
        assert "output" in str(exc_info.value)

    def test_agent_run_result_missing_status(self):
        """Test creation fails without status"""
        with pytest.raises(ValidationError) as exc_info:
            AgentRunResult(output="Some output")
        assert "status" in str(exc_info.value)


class TestTaskIdGeneration:
    """Test task ID generation for security and reliability"""

    def test_generate_task_id_length(self):
        """Test that generate_task_id() always returns exactly 8 characters"""
        for _ in range(100):  # Test multiple generations
            task_id = generate_task_id()
            assert len(task_id) == 8
            assert isinstance(task_id, str)

    def test_generate_task_id_uniqueness(self):
        """Test that generated task IDs are unique"""
        # Generate 100 IDs and verify they're all unique
        ids = [generate_task_id() for _ in range(100)]
        assert len(set(ids)) == len(ids)  # All IDs should be unique

    def test_generate_task_id_characters(self):
        """Test that task IDs only contain URL-safe characters"""
        valid_chars = set(string.ascii_letters + string.digits + "-_")

        for _ in range(50):
            task_id = generate_task_id()
            assert all(c in valid_chars for c in task_id)

    def test_task_id_in_model_context(self):
        """Test task ID generation works correctly in model creation"""
        tasks = [Task(description=f"Test task {i}") for i in range(10)]

        # All tasks should have 8-character IDs
        for task in tasks:
            assert len(task.id) == 8
            assert isinstance(task.id, str)

        # All IDs should be unique
        ids = [task.id for task in tasks]
        assert len(set(ids)) == len(ids)


class TestBoundaryValues:
    """Test boundary values for all constrained fields"""

    def test_task_priority_boundaries(self):
        """Test task priority field boundaries"""
        # Valid boundaries
        task_min = Task(description="Test", priority=1)
        assert task_min.priority == 1

        task_max = Task(description="Test", priority=10)
        assert task_max.priority == 10

        # Invalid boundaries
        with pytest.raises(ValidationError) as exc_info:
            Task(description="Test", priority=0)
        assert "priority" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            Task(description="Test", priority=11)
        assert "priority" in str(exc_info.value)

    def test_task_id_length_boundaries(self):
        """Test task ID length validation"""
        # Valid 8-character ID
        task_valid = Task(description="Test", id="abcd1234")
        assert task_valid.id == "abcd1234"

        # Invalid lengths
        with pytest.raises(ValidationError) as exc_info:
            Task(description="Test", id="abcd123")  # 7 chars
        assert "id" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            Task(description="Test", id="abcd12345")  # 9 chars
        assert "id" in str(exc_info.value)

    def test_list_size_boundaries(self):
        """Test list field size boundaries"""
        # Test TaskPlanOutput tasks boundary
        tasks_max = [f"Task {i}" for i in range(50)]
        plan = TaskPlanOutput(tasks=tasks_max)
        assert len(plan.tasks) == 50

        # Test exceeding max_length
        tasks_too_many = [f"Task {i}" for i in range(51)]
        with pytest.raises(ValidationError) as exc_info:
            TaskPlanOutput(tasks=tasks_too_many)
        assert "tasks" in str(exc_info.value)

        # Test TaskPlanOutput questions boundary
        questions_max = [f"Question {i}" for i in range(20)]
        plan_questions = TaskPlanOutput(tasks=["Task1"], questions=questions_max)
        assert len(plan_questions.questions) == 20

        questions_too_many = [f"Question {i}" for i in range(21)]
        with pytest.raises(ValidationError) as exc_info:
            TaskPlanOutput(tasks=["Task1"], questions=questions_too_many)
        assert "questions" in str(exc_info.value)

    def test_reflection_output_list_boundaries(self):
        """Test ReflectionOutput list field boundaries"""
        # Test maximum sizes
        gaps_max = [f"Gap {i}" for i in range(20)]
        new_tasks_max = [f"New task {i}" for i in range(20)]
        complete_ids_max = [f"id{i}" for i in range(50)]

        reflection = ReflectionOutput(done=True, gaps=gaps_max, new_tasks=new_tasks_max, complete_ids=complete_ids_max)
        assert len(reflection.gaps) == 20
        assert len(reflection.new_tasks) == 20
        assert len(reflection.complete_ids) == 50

        # Test exceeding boundaries
        with pytest.raises(ValidationError) as exc_info:
            ReflectionOutput(
                done=True,
                gaps=[f"Gap {i}" for i in range(21)],  # Too many gaps
                new_tasks=[],
            )
        assert "gaps" in str(exc_info.value)

    def test_enum_validation(self):
        """Test enum validation for status fields"""
        # Test TaskStatus enum values
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.DONE.value == "done"
        assert TaskStatus.CANCELLED.value == "cancelled"

        # Test AgentStatus enum values
        assert AgentStatus.COMPLETED.value == "completed"
        assert AgentStatus.FAILED.value == "failed"
        assert AgentStatus.TIMEOUT.value == "timeout"
        assert AgentStatus.CANCELLED.value == "cancelled"

        # Test invalid status rejection
        with pytest.raises(ValidationError) as exc_info:
            Task(description="Test", status="invalid_status")
        assert "status" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            AgentRunResult(output="Output", status="invalid_status")
        assert "status" in str(exc_info.value)

    def test_string_field_validation(self):
        """Test string field validation for edge cases"""
        # Test minimal valid description
        task_min = Task(description="a")
        assert task_min.description == "a"

        # Test empty description rejection
        with pytest.raises(ValidationError) as exc_info:
            Task(description="")
        assert "description" in str(exc_info.value)

        # Test whitespace-only description
        task_whitespace = Task(description="   ")
        assert task_whitespace.description == "   "

        # Test string fields with special characters
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        task_special = Task(description=special_chars)
        assert task_special.description == special_chars

        # Test unicode characters
        unicode_text = "Task with émojis 🚀 and ümlauts"
        task_unicode = Task(description=unicode_text)
        assert task_unicode.description == unicode_text
