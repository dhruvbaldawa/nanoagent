# Lightweight Generic Agent Framework Architecture

**Version:** 1.0
**Philosophy:** Frugal, pragmatic, production-ready

---

## Overview

A minimal multi-agent framework for autonomous task execution inspired by Enterprise Deep Research (EDR), built with Pydantic AI. Designed for solo engineers who need sophisticated agent capabilities without framework bloat.

**Key Features:**

- 🎯 Generic task decomposition and execution
- 🔧 Pluggable tool system
- 🔄 Reflection-based iterative refinement
- 📡 Real-time streaming
- 🪶 <500 LOC core framework

---

## Core Principles

1. **Minimal Data Models** - Only what's needed for control flow
2. **No Over-tracking** - Don't log what you won't use
3. **Simple State** - Dicts and sets over complex objects
4. **Pydantic AI Native** - Leverage built-in features (tools, streaming, structured outputs)
5. **Type-safe** - But not at the cost of complexity

---

## Data Models

### Task

```python
class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str
    status: Literal["pending", "done", "cancelled"] = "pending"
    priority: int = 5
```

### TaskPlanOutput

```python
class TaskPlanOutput(BaseModel):
    """What TaskPlanner returns"""
    tasks: List[str]  # Just descriptions
    questions: List[str] = []  # Only if needs clarification
```

### ExecutionResult

```python
class ExecutionResult(BaseModel):
    """What Executor returns"""
    success: bool
    output: str  # The actual result
```

### ReflectionOutput

```python
class ReflectionOutput(BaseModel):
    """What Reflector returns"""
    done: bool  # Are we finished?
    gaps: List[str] = []  # What's missing
    new_tasks: List[str] = []  # New task descriptions
    complete_ids: List[str] = []  # Task IDs to mark done
```

### AgentRunResult

```python
class AgentRunResult(BaseModel):
    """Final output to user"""
    output: str  # The synthesized answer
    status: str  # "completed" or "incomplete"
```

---

## Core Components

### 1. TaskPlanner (Pydantic AI Agent)

**Role:** Decomposes high-level goals into actionable subtasks

**Responsibilities:**

- Initial goal decomposition (3-7 tasks)
- Ask clarifying questions when ambiguous
- Generate new tasks based on reflection feedback

**Configuration:**

```python
task_planner = Agent(
    model='anthropic:claude-sonnet-4-0',
    output_type=TaskPlanOutput,
    instructions="""
    Decompose this goal into 3-7 specific, actionable tasks.
    If the goal is unclear, ask clarifying questions.
    """
)
```

**Tools:** `ask_clarifying_question(question: str)` - pauses for user input

---

### 2. TodoManager (Plain Python Class)

**Role:** Centralized task queue and state management

**State:**

```python
class TodoManager:
    tasks: Dict[str, Task]  # id -> Task
    completed: Set[str]     # Just IDs
```

**Key Methods:**

```python
add_tasks(descriptions: List[str], priority: int = 5)
get_next() -> Optional[Task]  # Highest priority pending
mark_done(task_id: str, result: str)
get_pending() -> List[Task]
get_done() -> List[Task]
```

**Why Plain Class:** Deterministic, fast, no LLM uncertainty in state management

---

### 3. Executor (Pydantic AI Agent)

**Role:** Execute individual tasks using available tools

**Responsibilities:**

- Receive one task at a time
- Decide which tool(s) to use
- Handle errors and retries
- Return structured result

**Configuration:**

```python
executor = Agent(
    model='anthropic:claude-sonnet-4-0',
    output_type=ExecutionResult,
    deps_type=ExecutorDeps,
    instructions="Execute the task using available tools. Be thorough."
)

@dataclass
class ExecutorDeps:
    registry: ToolRegistry
    task: Task
    context: Dict[str, str]
```

**Tool Integration:**

```python
@executor.tool
async def web_search(ctx: RunContext[ExecutorDeps], query: str) -> str:
    return ctx.deps.registry.get("web_search")(query)
```

---

### 4. Reflector (Pydantic AI Agent)

**Role:** Evaluate progress and identify knowledge gaps

**Inputs:**

- Original goal
- Completed tasks + results
- Pending tasks

**Outputs:** `ReflectionOutput` (structured)

**Configuration:**

```python
reflector = Agent(
    model='anthropic:claude-sonnet-4-0',
    output_type=ReflectionOutput,
    instructions="""
    Evaluate if goal is achieved. If not:
    1. What critical information is missing?
    2. Which pending tasks are now irrelevant?
    3. What new tasks would fill the gaps?
    """
)
```

**No Tools:** Pure reasoning agent

---

### 5. ToolRegistry (Plain Python Class)

**Role:** Pluggable tool management

**Implementation:**

```python
class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        self.tools[name] = func

    def get(self, name: str) -> Callable:
        return self.tools[name]

    def list_names() -> List[str]:
        return list(self.tools.keys())
```

**Built-in Tools:**

- `web_search(query: str) -> str`
- `read_file(path: str) -> str`
- `write_file(path: str, content: str) -> bool`
- `execute_code(code: str, language: str) -> str`
- `api_call(url: str, method: str, payload: dict) -> dict`

---

### 6. StreamManager (Plain Python Class)

**Role:** Real-time event broadcasting

**Implementation:**

```python
class StreamManager:
    def emit(self, event_type: str, data: Any):
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(event))  # Or send via SSE/websocket
```

**Event Types:**

- `task_started`
- `tool_called`
- `task_completed`
- `reflection`
- `thought` (streaming LLM tokens)

---

### 7. Orchestrator (Main Controller)

**Role:** Coordinates all components in iterative loops

**Core State:**

```python
class Orchestrator:
    goal: str
    max_iterations: int
    todo: TodoManager
    context: Dict[str, str]  # task_id -> result
    iteration: int
```

**Main Loop:** See [Data Flow](#data-flow) section

---

## System Architecture

```
┌─────────────────────────────────────┐
│         USER INPUT (Goal)           │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│          ORCHESTRATOR               │
│  • Main iteration loop              │
│  • Component coordination           │
│  • User interaction                 │
└─────────────────────────────────────┘
         ↓           ↓           ↓
   ┌─────────┐ ┌──────────┐ ┌─────────┐
   │ Stream  │ │   Todo   │ │ Context │
   │ Manager │ │ Manager  │ │  Dict   │
   └─────────┘ └──────────┘ └─────────┘

┌───────── ITERATION LOOP ─────────────┐
│                                       │
│  ┌────────────────────────────────┐  │
│  │  1. PLANNING PHASE             │  │
│  │     TaskPlanner Agent          │  │
│  │     ↓                           │  │
│  │     TodoManager.add_tasks()    │  │
│  └────────────────────────────────┘  │
│              ↓                        │
│  ┌────────────────────────────────┐  │
│  │  2. EXECUTION PHASE            │  │
│  │     TodoManager.get_next()     │  │
│  │     ↓                           │  │
│  │     Executor Agent              │  │
│  │     ├─ ToolRegistry             │  │
│  │     │  ├─ web_search            │  │
│  │     │  ├─ file_ops              │  │
│  │     │  └─ custom_tools          │  │
│  │     ↓                           │  │
│  │     TodoManager.mark_done()    │  │
│  └────────────────────────────────┘  │
│              ↓                        │
│  ┌────────────────────────────────┐  │
│  │  3. REFLECTION PHASE           │  │
│  │     (Every 3 iterations)       │  │
│  │     Reflector Agent            │  │
│  │     ↓                           │  │
│  │     TodoManager.update()       │  │
│  │     • Add new tasks            │  │
│  │     • Mark completed           │  │
│  └────────────────────────────────┘  │
│              ↓                        │
│         Continue? → YES/NO            │
│              ↓                        │
└──────────────┼───────────────────────┘
               ↓
┌─────────────────────────────────────┐
│      FINAL OUTPUT SYNTHESIS         │
│  • Aggregate results                │
│  • Return AgentRunResult            │
└─────────────────────────────────────┘
```

---

## Data Flow

### Initialization

```
User provides: goal, tools, max_iterations

Orchestrator.__init__():
    • Create TodoManager (empty)
    • Create StreamManager
    • Create ToolRegistry + register tools
    • context = {}
```

### Loop 0: Initial Planning

```
1. plan = TaskPlanner.run(goal)
   → Returns: TaskPlanOutput(tasks=[...], questions=[...])

2. IF questions:
      answers = ask_user(questions)
      plan = TaskPlanner.run(goal, answers)

3. TodoManager.add_tasks(plan.tasks, priority=9)
```

### Loop N: Execute + Reflect

```
4. task = TodoManager.get_next()
   stream.emit("task_started", task)

5. result = Executor.run(
       prompt=task.description,
       deps=ExecutorDeps(registry, task, context)
   )
   # Executor calls tools as needed
   # Each tool call → stream.emit("tool_called", ...)

6. context[task.id] = result.output
   TodoManager.mark_done(task.id, result.output)
   stream.emit("task_completed", result)

7. IF (iteration % 3 == 0) OR (no pending tasks):
      # Build context string
      context_str = "\n\n".join([
          f"Task: {todo.tasks[id].description}\n"
          f"Result: {result}"
          for id, result in context.items()
      ])

      reflection = Reflector.run(
          goal=goal,
          done_tasks=context_str,
          pending_tasks=[t.description for t in todo.get_pending()]
      )

      stream.emit("reflection", reflection)

      # Update TodoManager
      for tid in reflection.complete_ids:
          todo.tasks[tid].status = "done"

      todo.add_tasks(reflection.new_tasks, priority=7)

      IF reflection.done:
          BREAK LOOP

8. iteration += 1
   IF iteration >= max_iterations:
       BREAK LOOP

   GOTO Step 4
```

### Finalization

```
9. final_output = synthesize_all_results(context)

10. Return AgentRunResult(
       output=final_output,
       status="completed" if reflection.done else "incomplete"
    )
```

---

## Implementation Patterns

### Tool Registration

```python
# Setup
orchestrator = Orchestrator(goal="...", max_iterations=10)

# Built-in tools auto-register
orchestrator.registry.auto_register_builtins()

# User adds custom tools
@orchestrator.register_tool("fetch_company_data")
def fetch_company_data(ticker: str) -> dict:
    return api.get(f"/company/{ticker}")

# Tools automatically available to Executor
```

### Streaming with Pydantic AI

```python
# Executor uses native streaming
async with executor.run_stream(prompt, deps=deps) as response:
    async for chunk in response.stream_text():
        stream_manager.emit("thought", chunk)
    result = await response.get_data()
```

### Context as Simple Dict

```python
# Store results simply
context = {
    "abc123": "Search results show...",
    "def456": "File contains...",
}

# Pass to agents as formatted string
context_str = "\n\n".join([
    f"Task: {todo.tasks[tid].description}\nResult: {res}"
    for tid, res in context.items()
])
```

---

## Simplified Prompts

### TaskPlanner

```python
PLANNER_PROMPT = """
Goal: {goal}

{context}  # If re-planning

Decompose into 3-7 specific, actionable tasks.
If unclear, ask questions.

Return JSON:
{{
  "tasks": ["task 1", "task 2", ...],
  "questions": ["question 1", ...]
}}
"""
```

### Reflector

```python
REFLECTOR_PROMPT = """
Goal: {goal}

Completed:
{done_tasks_with_results}

Pending:
{pending_task_descriptions}

Are we done? What's missing?

Return JSON:
{{
  "done": true/false,
  "gaps": ["gap 1", ...],
  "new_tasks": ["task 1", ...],
  "complete_ids": ["id1", "id2", ...]
}}
"""
```

---

## File Structure

```
agent_framework/
├── core/
│   ├── __init__.py
│   ├── orchestrator.py      # Main loop (~150 LOC)
│   ├── task_planner.py      # Pydantic AI agent (~50 LOC)
│   ├── executor.py          # Pydantic AI agent (~80 LOC)
│   ├── reflector.py         # Pydantic AI agent (~60 LOC)
│   ├── todo_manager.py      # State management (~60 LOC)
│   └── stream_manager.py    # Event streaming (~30 LOC)
├── models/
│   ├── __init__.py
│   └── schemas.py           # All 5 data models (~40 LOC)
├── tools/
│   ├── __init__.py
│   ├── registry.py          # ToolRegistry (~30 LOC)
│   └── builtin.py           # Built-in tools (~100 LOC)
├── prompts/
│   ├── __init__.py
│   └── templates.py         # Prompt templates (~50 LOC)
└── examples/
    └── basic_usage.py       # Usage examples

Total Core: ~500 LOC
```

---

## Key Design Decisions

### Why Pydantic AI over LiteLLM?

- ✅ Native tool calling with type safety
- ✅ Structured outputs (essential for task/reflection parsing)
- ✅ Dependency injection (cleaner state passing)
- ✅ Built-in streaming support
- ✅ Model-agnostic like LiteLLM, better DX

### Why Separate Planner/Executor/Reflector?

- Clear separation of concerns
- Specialized prompts per role
- Easy independent testing
- Can use different models (fast for execution, smart for reflection)

### Why TodoManager as Plain Class?

- Deterministic state management
- No LLM uncertainty in task lifecycle
- Easy to debug/inspect
- Fast (no API calls)

### Why Minimal Data Models?

- LLMs struggle with complex schemas
- Less data = more reliable parsing
- Faster serialization
- Easier debugging

### Why In-Memory First?

- Simplicity for MVP
- Fast iteration during development
- Easy to add persistence later (just serialize TodoManager)

---

## Extension Points

### Easy to Add Later

**Persistence:**

```python
# Add to TodoManager
def save(self, path: str):
    json.dump(self.tasks, open(path, 'w'))

def load(self, path: str):
    self.tasks = json.load(open(path))
```

**Human-in-the-Loop:**

```python
# Use Pydantic AI's deferred_toolsN
@executor.tool(approval_required=True)
def dangerous_operation(ctx, action: str):
    # Requires approval before executing
    pass
```

**Multi-Agent Specialization:**

```python
# Create specialized executors
research_executor = Agent(..., instructions="Research specialist")
code_executor = Agent(..., instructions="Code specialist")

# Route based on task type
if "research" in task.description:
    result = research_executor.run(...)
```

**MCP Integration:**

```python
# Pydantic AI supports MCP natively
from pydantic_ai.mcp import MCPClient

mcp_client = MCPClient(server_url="...")
registry.register_from_mcp(mcp_client)
```

---

## Usage Example

```python
from agent_framework import Orchestrator, ToolRegistry

# Setup
orchestrator = Orchestrator(
    goal="Research competitor landscape for SaaS analytics tools",
    max_iterations=10
)

# Register custom tools
@orchestrator.register_tool("fetch_crunchbase")
def fetch_crunchbase(company: str) -> dict:
    return crunchbase_api.get(company)

# Run
result = await orchestrator.run()

print(result.output)
# Comprehensive analysis with competitor data...
print(result.status)
# "completed"
```

---

## Production Considerations

**Error Handling:**

- Wrap tool calls in try/except
- Use Pydantic AI's `ModelRetry` for recoverable errors
- Set max retries per tool

**Rate Limiting:**

- Add delays between API calls
- Use async for parallelization where safe
- Implement token budgets

**Cost Control:**

- Use cheaper models for Executor (fast, frequent calls)
- Use smarter models for Reflector (infrequent, critical)
- Track token usage in orchestrator

**Testing:**

- Mock ToolRegistry for unit tests
- Test each agent independently
- Integration tests with real tools

---

## Comparison: Full EDR vs This Framework

| Feature | EDR | This Framework |
|---------|-----|----------------|
| Lines of Code | ~5000+ | ~500 |
| Specialized Agents | 4 (Academic, GitHub, etc) | 1 (generic Executor) |
| Database Support | NL2SQL, MCP | Pluggable via tools |
| Visualization | Dedicated agent | Pluggable via tools |
| Human Steering | Real-time UI | Easy to add |
| Persistence | Full state save | Add when needed |
| Streaming | SSE with frontend | Simple event emit |
| Use Case | Enterprise research | Generic task execution |

---

## Summary

This architecture gives you **80% of EDR's power with 10% of the complexity**. Perfect for:

- Solo engineers building agent systems
- Prototyping agentic workflows
- Learning multi-agent patterns
- Production systems that can start simple and scale

**Core Philosophy:** Start minimal, add complexity only when needed.

---

**Next Steps:**

1. Implement core components (~2-3 days)
2. Add 3-5 essential tools
3. Test with real use cases
4. Extend based on actual pain points
