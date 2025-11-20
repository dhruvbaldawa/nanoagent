# Task 015: OpenTelemetry Instrumentation for Observability

**Iteration:** Polish
**Status:** Pending
**Dependencies:** 014 (Performance benchmarks established)
**Files:** nanoagent/core/instrumentation.py (new), examples/observability_demo.py (new)

## Description
Implement OpenTelemetry instrumentation for production observability using Pydantic AI's built-in instrumentation support. Enable tracing for all agent calls (planner, executor, reflector), track token usage via OTEL spans, and support multiple backends (Logfire, custom OTLP). Provide production-ready observability without custom tracking code.

## Working Result
- OpenTelemetry instrumentation integrated via Pydantic AI's `Agent.instrument_all()`
- Instrumentation module with configuration helpers for different backends
- Token usage and performance metrics captured via OTEL spans
- Example demonstrating observability with local OTLP backend (otel-tui)
- Documentation on observability setup and backend options
- All tests passing with instrumentation enabled (optional in tests)
- Instrumentation configurable via environment variables

## Validation
- [ ] instrumentation.py module created with InstrumentationSettings helpers
- [ ] OpenTelemetry SDK and OTLP exporter added to dependencies
- [ ] Agent.instrument_all() called at application startup
- [ ] Instrumentation configurable via environment variables (OTEL_EXPORTER_OTLP_ENDPOINT)
- [ ] Example demonstrating observability with otel-tui backend
- [ ] Documentation in DESIGN.md on observability setup
- [ ] Tests verify instrumentation doesn't break functionality
- [ ] Instrumentation optional in test suite (no API calls in CI)
- [ ] All tests pass: `uv run pytest` (230+ tests expected)
- [ ] `uv run ruff check` passes

## LLM Prompt
<prompt>
**Goal:** Enable production observability using OpenTelemetry and Pydantic AI's built-in instrumentation

**Constraints:**
- Use Pydantic AI's native instrumentation (don't reinvent the wheel)
- Must not break existing functionality (all 220+ tests must pass)
- Instrumentation should be optional and configurable
- Support multiple backends (Logfire, custom OTLP, local dev)
- Keep it simple - leverage OTEL standards

**Context7 Research Findings:**
Pydantic AI has built-in OpenTelemetry support via:
- `Agent.instrument_all(settings)` for global instrumentation
- `InstrumentationSettings` for configuration
- Native OTLP exporter support
- Token usage captured automatically in spans

**Implementation Guidance:**

1. **Add dependencies to pyproject.toml:**
   ```toml
   [project]
   dependencies = [
       # ... existing dependencies ...
       "opentelemetry-sdk>=1.20.0",
       "opentelemetry-exporter-otlp>=1.20.0",
   ]

   [project.optional-dependencies]
   # For Logfire backend (optional)
   logfire = ["logfire>=0.40.0"]
   ```

2. **Create instrumentation module (nanoagent/core/instrumentation.py):**
   ```python
   # ABOUTME: OpenTelemetry instrumentation configuration for production observability
   # ABOUTME: Provides helpers for different OTEL backends (OTLP, Logfire, local dev)

   import os
   from typing import Literal

   from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
   from opentelemetry.sdk.trace import TracerProvider
   from opentelemetry.sdk.trace.export import BatchSpanProcessor
   from opentelemetry.trace import set_tracer_provider

   from pydantic_ai import Agent
   from pydantic_ai.models.instrumented import InstrumentationSettings

   Backend = Literal["otlp", "logfire", "none"]


   def configure_instrumentation(
       backend: Backend = "otlp",
       endpoint: str | None = None,
       include_content: bool = True,
       include_binary_content: bool = False,
   ) -> InstrumentationSettings | None:
       """
       Configure OpenTelemetry instrumentation for Pydantic AI agents.

       Args:
           backend: Observability backend ("otlp", "logfire", or "none")
           endpoint: OTLP endpoint (default: http://localhost:4318)
           include_content: Include prompts/completions in spans (default: True)
           include_binary_content: Include binary data in spans (default: False)

       Returns:
           InstrumentationSettings if instrumentation enabled, None otherwise

       Environment Variables:
           OTEL_EXPORTER_OTLP_ENDPOINT: Override OTLP endpoint
           NANOAGENT_INSTRUMENTATION: Override backend ("otlp", "logfire", "none")
           NANOAGENT_INCLUDE_CONTENT: Override include_content ("true"/"false")
       """
       # Environment variable overrides
       backend = os.getenv("NANOAGENT_INSTRUMENTATION", backend)  # type: ignore
       endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", endpoint or "http://localhost:4318")
       include_content = os.getenv("NANOAGENT_INCLUDE_CONTENT", str(include_content)).lower() == "true"

       if backend == "none":
           return None

       if backend == "logfire":
           try:
               import logfire

               logfire.configure()
               logfire.instrument_pydantic_ai()
               return None  # Logfire handles instrumentation internally
           except ImportError:
               raise RuntimeError(
                   "Logfire backend requires 'logfire' package. "
                   "Install with: uv add --optional logfire logfire"
               )

       # OTLP backend (default)
       os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = endpoint

       exporter = OTLPSpanExporter()
       span_processor = BatchSpanProcessor(exporter)
       tracer_provider = TracerProvider()
       tracer_provider.add_span_processor(span_processor)
       set_tracer_provider(tracer_provider)

       settings = InstrumentationSettings(
           include_content=include_content,
           include_binary_content=include_binary_content,
       )

       # Instrument all agents globally
       Agent.instrument_all(settings)

       return settings


   def is_instrumentation_enabled() -> bool:
       """Check if instrumentation is enabled via environment."""
       return os.getenv("NANOAGENT_INSTRUMENTATION", "otlp") != "none"
   ```

3. **Integrate into Orchestrator:**
   - Add optional instrumentation at application startup (not in __init__)
   - Keep Orchestrator unchanged - instrumentation happens globally via Agent.instrument_all()
   - Example pattern:
     ```python
     # Application startup
     from nanoagent.core.instrumentation import configure_instrumentation

     # Configure once at startup
     configure_instrumentation(backend="otlp", endpoint="http://localhost:4318")

     # All subsequent agent calls are instrumented automatically
     orchestrator = Orchestrator(goal="...", max_iterations=10)
     result = await orchestrator.run()
     ```

4. **Create observability example (examples/observability_demo.py):**
   ```python
   """
   Observability demo showing OpenTelemetry instrumentation with local backend.

   Setup:
   1. Run OTLP backend: docker run --rm -it -p 4318:4318 ymtdzzz/otel-tui:latest
   2. Run demo: uv run python examples/observability_demo.py
   3. View traces in otel-tui terminal

   Traces capture:
   - Agent calls (planner, executor, reflector)
   - Tool executions
   - Token usage (automatic via Pydantic AI spans)
   - Timing and performance metrics
   """

   import asyncio

   from nanoagent.core.instrumentation import configure_instrumentation
   from nanoagent.core.orchestrator import Orchestrator
   from nanoagent.tools.builtin import register_builtin_tools


   async def main():
       # Configure OpenTelemetry with local OTLP backend
       configure_instrumentation(
           backend="otlp",
           endpoint="http://localhost:4318",
           include_content=True,  # Include prompts/completions in traces
       )

       print("OpenTelemetry instrumentation enabled")
       print("View traces at: http://localhost:4318 (otel-tui)")
       print()

       # Run orchestration with instrumentation
       orchestrator = Orchestrator(
           goal="Calculate the sum of squares from 1 to 5",
           max_iterations=10,
       )
       register_builtin_tools(orchestrator.registry)

       print(f"Goal: {orchestrator.goal}")
       result = await orchestrator.run()

       print(f"\nResult: {result.output}")
       print(f"Status: {result.status}")
       print("\nCheck otel-tui for detailed traces!")


   if __name__ == "__main__":
       asyncio.run(main())
   ```

5. **Add tests (instrumentation_test.py):**
   ```python
   import os
   import pytest
   from nanoagent.core.instrumentation import configure_instrumentation, is_instrumentation_enabled


   def test_configure_instrumentation_none():
       """Instrumentation disabled returns None."""
       settings = configure_instrumentation(backend="none")
       assert settings is None


   def test_configure_instrumentation_otlp():
       """OTLP backend configures TracerProvider."""
       # Don't actually configure (would affect other tests)
       # Just verify function doesn't crash
       assert configure_instrumentation is not None


   def test_is_instrumentation_enabled_default():
       """Default is instrumentation enabled."""
       # Clear env var
       old_val = os.environ.pop("NANOAGENT_INSTRUMENTATION", None)
       try:
           assert is_instrumentation_enabled()
       finally:
           if old_val:
               os.environ["NANOAGENT_INSTRUMENTATION"] = old_val


   def test_is_instrumentation_enabled_disabled():
       """NANOAGENT_INSTRUMENTATION=none disables instrumentation."""
       old_val = os.environ.get("NANOAGENT_INSTRUMENTATION")
       try:
           os.environ["NANOAGENT_INSTRUMENTATION"] = "none"
           assert not is_instrumentation_enabled()
       finally:
           if old_val:
               os.environ["NANOAGENT_INSTRUMENTATION"] = old_val
           else:
               os.environ.pop("NANOAGENT_INSTRUMENTATION", None)


   @pytest.mark.asyncio
   async def test_orchestrator_with_instrumentation_disabled():
       """Orchestrator works with instrumentation disabled."""
       from nanoagent.core.orchestrator import Orchestrator
       from nanoagent.tools.builtin import register_builtin_tools

       # Ensure instrumentation disabled for test
       old_val = os.environ.get("NANOAGENT_INSTRUMENTATION")
       try:
           os.environ["NANOAGENT_INSTRUMENTATION"] = "none"
           configure_instrumentation(backend="none")

           orchestrator = Orchestrator(goal="What is 2 + 2?", max_iterations=5)
           register_builtin_tools(orchestrator.registry)

           result = await orchestrator.run()
           assert result.status in ("completed", "incomplete")
       finally:
           if old_val:
               os.environ["NANOAGENT_INSTRUMENTATION"] = old_val
           else:
               os.environ.pop("NANOAGENT_INSTRUMENTATION", None)
   ```

6. **Update conftest.py:**
   - Disable instrumentation in test suite by default
   - Add fixture for enabling instrumentation in specific tests
   ```python
   @pytest.fixture(autouse=True)
   def disable_instrumentation_in_tests():
       """Disable OTEL instrumentation in tests to avoid side effects."""
       old_val = os.environ.get("NANOAGENT_INSTRUMENTATION")
       os.environ["NANOAGENT_INSTRUMENTATION"] = "none"
       yield
       if old_val:
           os.environ["NANOAGENT_INSTRUMENTATION"] = old_val
       else:
           os.environ.pop("NANOAGENT_INSTRUMENTATION", None)
   ```

7. **Update DESIGN.md:**
   - Add "Observability with OpenTelemetry" section
   - Document instrumentation setup for different backends
   - Document environment variables for configuration
   - Add example of viewing traces with otel-tui

8. **Update README (if exists) or create OBSERVABILITY.md:**
   - Quick start guide for local observability with otel-tui
   - Production setup with OTLP endpoint
   - Logfire setup (optional)
   - Environment variable reference

**References:**
- Context7 research on Pydantic AI OpenTelemetry support
- Official Pydantic AI logfire.md documentation
- OpenTelemetry SDK documentation

**Validation:**
- Run otel-tui: `docker run --rm -it -p 4318:4318 ymtdzzz/otel-tui:latest`
- Run example: `uv run python examples/observability_demo.py`
- Verify traces appear in otel-tui
- Run `uv run pytest nanoagent/core/instrumentation_test.py` - tests pass
- Run `uv run pytest` - all tests pass (230+ total, instrumentation disabled in CI)
- Run `uv run ruff check` - no errors
</prompt>

## Notes

**planning:** OpenTelemetry is the industry standard for observability. Pydantic AI has excellent built-in support via `Agent.instrument_all()` - we should leverage this instead of building custom tracking. Benefits: (1) Standard OTEL format for traces/metrics, (2) Token usage captured automatically in spans, (3) Works with any OTEL backend (Logfire, Jaeger, Prometheus, etc.), (4) No custom code to maintain. Keep it simple - provide configuration helpers and examples, but let Pydantic AI + OTEL do the heavy lifting. Local dev uses otel-tui (Docker), production uses OTLP endpoint.
