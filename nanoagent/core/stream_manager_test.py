# ABOUTME: Tests for StreamManager event emission and JSON formatting
# ABOUTME: Validates emit() method, timestamp format, and all event types

import json
from datetime import datetime

from _pytest.capture import CaptureFixture
from _pytest.logging import LogCaptureFixture

from nanoagent.core.stream_manager import StreamManager


def test_emit_basic_json_structure(capsys: CaptureFixture[str]) -> None:
    """Test emit() produces correct JSON structure with type, data, and timestamp."""
    manager = StreamManager()
    test_data = {"task_id": "abc123", "description": "Test task"}

    manager.emit("task_started", test_data)

    captured = capsys.readouterr()
    output = json.loads(captured.out.strip())

    assert output["type"] == "task_started"
    assert output["data"] == test_data
    assert "timestamp" in output


def test_emit_timestamp_is_iso_format(capsys: CaptureFixture[str]) -> None:
    """Test emit() outputs ISO 8601 formatted timestamps."""
    manager = StreamManager()

    manager.emit("test_event", {"test": "data"})

    captured = capsys.readouterr()
    output = json.loads(captured.out.strip())

    # Verify ISO format by trying to parse it
    timestamp_str = output["timestamp"]
    parsed = datetime.fromisoformat(timestamp_str)
    assert isinstance(parsed, datetime)


def test_emit_task_started_event(capsys: CaptureFixture[str]) -> None:
    """Test task_started event type."""
    manager = StreamManager()
    data = {"task_id": "task1", "description": "Calculate sum"}

    manager.emit("task_started", data)

    captured = capsys.readouterr()
    output = json.loads(captured.out.strip())

    assert output["type"] == "task_started"
    assert output["data"]["task_id"] == "task1"
    assert output["data"]["description"] == "Calculate sum"


def test_emit_task_completed_event(capsys: CaptureFixture[str]) -> None:
    """Test task_completed event type."""
    manager = StreamManager()
    data = {"task_id": "task1", "success": True, "output": "Result is 55"}

    manager.emit("task_completed", data)

    captured = capsys.readouterr()
    output = json.loads(captured.out.strip())

    assert output["type"] == "task_completed"
    assert output["data"]["success"] is True
    assert output["data"]["output"] == "Result is 55"


def test_emit_reflection_event(capsys: CaptureFixture[str]) -> None:
    """Test reflection event type."""
    manager = StreamManager()
    data = {
        "done": False,
        "gaps": ["Missing step 1"],
        "new_tasks": ["Refine calculation"],
    }

    manager.emit("reflection", data)

    captured = capsys.readouterr()
    output = json.loads(captured.out.strip())

    assert output["type"] == "reflection"
    assert output["data"]["done"] is False
    assert len(output["data"]["gaps"]) == 1
    assert len(output["data"]["new_tasks"]) == 1


def test_emit_thought_event(capsys: CaptureFixture[str]) -> None:
    """Test thought event type (optional for M2)."""
    manager = StreamManager()
    data = {"text": "Thinking about the next step"}

    manager.emit("thought", data)

    captured = capsys.readouterr()
    output = json.loads(captured.out.strip())

    assert output["type"] == "thought"
    assert output["data"]["text"] == "Thinking about the next step"


def test_emit_multiple_events(capsys: CaptureFixture[str]) -> None:
    """Test multiple emit() calls produce separate JSON lines."""
    manager = StreamManager()

    manager.emit("event1", {"data": "first"})
    manager.emit("event2", {"data": "second"})

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")

    assert len(lines) == 2
    event1 = json.loads(lines[0])
    event2 = json.loads(lines[1])

    assert event1["type"] == "event1"
    assert event2["type"] == "event2"


def test_emit_with_empty_data(capsys: CaptureFixture[str]) -> None:
    """Test emit() works with empty data dict."""
    manager = StreamManager()

    manager.emit("empty_event", {})

    captured = capsys.readouterr()
    output = json.loads(captured.out.strip())

    assert output["type"] == "empty_event"
    assert output["data"] == {}
    assert "timestamp" in output


def test_emit_with_complex_nested_data(capsys: CaptureFixture[str]) -> None:
    """Test emit() preserves complex nested data structures."""
    manager = StreamManager()
    data = {
        "tasks": [
            {"id": "t1", "description": "task 1"},
            {"id": "t2", "description": "task 2"},
        ],
        "metadata": {"count": 2, "completed": True},
    }

    manager.emit("complex_event", data)

    captured = capsys.readouterr()
    output = json.loads(captured.out.strip())

    assert output["data"]["tasks"][0]["id"] == "t1"
    assert output["data"]["metadata"]["count"] == 2


def test_emit_with_non_serializable_object_never_raises(capsys: CaptureFixture[str], caplog: LogCaptureFixture) -> None:
    """Test emit() handles non-serializable objects gracefully without raising."""
    import logging

    caplog.set_level(logging.ERROR)
    manager = StreamManager()

    class CustomObject:
        pass

    # Should not raise - emit() handles errors internally
    manager.emit("bad_event", {"object": CustomObject()})

    # Verify error was logged
    assert "Failed to serialize event for emission" in caplog.text

    # No output should be printed (serialization failed)
    captured = capsys.readouterr()
    assert captured.out.strip() == ""
