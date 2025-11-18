# Task 011: Stream Manager for Event Emission

**Iteration:** Integration
**Status:** Pending
**Dependencies:** 010 (Orchestrator - needs integration points)
**Files:** nanoagent/core/stream_manager.py, nanoagent/core/stream_manager_test.py

## Description
Implement StreamManager for real-time event emission during orchestration. Simple print-based event streaming for M2 (can upgrade to SSE/WebSocket in M3). Follow TDD approach.

## Working Result
- StreamManager class with emit(event_type, data) method
- JSON-formatted event output
- Integration points in Orchestrator for key events
- Comprehensive tests
- All tests passing

## Validation
- [ ] stream_manager.py implements StreamManager (~30 LOC as per DESIGN.md)
- [ ] emit(event_type, data) outputs JSON events with timestamp
- [ ] Support event types: task_started, task_completed, reflection, thought
- [ ] Tests cover event emission and JSON formatting
- [ ] Integration with Orchestrator emits events at key points
- [ ] `uv run pytest nanoagent/core/stream_manager_test.py` passes
- [ ] `uv run ruff check` passes

## LLM Prompt
<prompt>
**Goal:** Implement simple event streaming for real-time visibility into orchestration progress

**Constraints:**
- Must follow TDD: write tests before implementation
- Must match DESIGN.md § StreamManager architecture
- Target ~30 LOC for implementation
- Keep it simple: JSON print to stdout (defer SSE/WebSocket to M3)
- Must not block orchestration (events are fire-and-forget)

**Implementation Guidance:**
- Reference DESIGN.md § StreamManager for architecture
- Simple class structure:
  ```python
  class StreamManager:
      def emit(self, event_type: str, data: Any) -> None:
          event = {
              "type": event_type,
              "data": data,
              "timestamp": datetime.now().isoformat()
          }
          print(json.dumps(event))
  ```
- Event types (from DESIGN.md):
  - `task_started`: {task_id, description}
  - `task_completed`: {task_id, success, output}
  - `reflection`: {done, gaps, new_tasks}
  - `thought`: {text} (optional for M2)
- Write tests first:
  - Test emit() produces correct JSON structure
  - Test timestamp is ISO format
  - Test all event types
  - Use capsys fixture to capture stdout
- Add ABOUTME comments
- Keep implementation minimal

**Integration with Orchestrator:**
- Add StreamManager instance to Orchestrator.__init__()
- Emit events at key points:
  - task_started before executor.run()
  - task_completed after executor.run()
  - reflection after reflector.run()
- Make integration non-blocking (don't wait for events)

**Deferred to M3:**
- SSE/WebSocket streaming
- Buffered event queues
- Client-side event consumption
- Streaming LLM tokens (thought events)

**Validation:**
- Run `uv run pytest nanoagent/core/stream_manager_test.py` - all tests pass
- Run `uv run ruff check` - no errors
- Verify LOC count ~30 LOC
- Verify events appear during orchestration
</prompt>

## Notes

**planning:** Deferred from M1 because manual POC worked without it. Now adding for M2 to provide visibility into the automated loop. Keep it simple - just print JSON events. Can upgrade to real streaming (SSE/WebSocket) in M3 if needed. This matches M1 learning that streaming is nice-to-have, not blocking.
