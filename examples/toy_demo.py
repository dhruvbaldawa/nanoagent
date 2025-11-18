#!/usr/bin/env python3
# ABOUTME: Interactive demo script that tests all Milestone 1 foundation components with real LLMs
# ABOUTME: Demonstrates complete orchestration flow: planning → execution → reflection

import asyncio
import sys
from pathlib import Path

# Add parent dir to path so we can import nanoagent
sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import ValidationError

from nanoagent.config import get_settings
from nanoagent.core.executor import execute_task
from nanoagent.core.reflector import reflect_on_progress
from nanoagent.core.task_planner import plan_tasks
from nanoagent.core.todo_manager import TodoManager


async def main() -> None:
    # Load and validate configuration
    try:
        get_settings()  # Validate configuration is present and valid
    except ValidationError as e:
        print("❌ Configuration Error")
        print("\nRequired environment variables:")
        print("  - TASK_PLANNER_MODEL (e.g., 'anthropic:claude-sonnet-4-5-20250514')")
        print("  - EXECUTOR_MODEL (e.g., 'openrouter:anthropic/claude-3.5-sonnet')")
        print("  - REFLECTOR_MODEL (e.g., 'openai:gpt-4o')")
        print("\nAlso set corresponding API keys:")
        print("  - ANTHROPIC_API_KEY (for Anthropic models)")
        print("  - OPENAI_API_KEY (for OpenAI models)")
        print("  - OPENROUTER_API_KEY (for OpenRouter models)")
        print("\nExample setup:")
        print("  export TASK_PLANNER_MODEL='anthropic:claude-sonnet-4-5-20250514'")
        print("  export EXECUTOR_MODEL='anthropic:claude-sonnet-4-5-20250514'")
        print("  export REFLECTOR_MODEL='anthropic:claude-sonnet-4-5-20250514'")
        print("  export ANTHROPIC_API_KEY='sk-ant-...'")
        print("\nDetailed error:")
        print(str(e))
        sys.exit(1)

    print("\n" + "=" * 70)
    print("🤖 Nanoagent Toy Demo - Plan & Execute")
    print("=" * 70)

    # Get goal from user
    goal = input("\nEnter your goal: ").strip()
    if not goal:
        print("❌ Goal cannot be empty")
        sys.exit(1)

    print(f"\n📝 Planning goal: {goal}")
    print("-" * 70)

    # Plan tasks
    try:
        plan_output = await plan_tasks(goal)
        if not plan_output:
            print("❌ Planning failed (API error)")
            sys.exit(1)
    except ValueError as e:
        print(f"❌ Planning validation failed: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"❌ Planning API error: {e}")
        print("\nVerify your configuration:")
        print("  - TASK_PLANNER_MODEL is set and valid")
        print("  - Corresponding API key is set (e.g., ANTHROPIC_API_KEY)")
        print("  - Model format is 'provider:model-name'")
        sys.exit(1)

    # Show planned tasks
    print(f"\n✅ Planned {len(plan_output.tasks)} tasks:")
    for i, task_desc in enumerate(plan_output.tasks, 1):
        print(f"  {i}. {task_desc}")

    if plan_output.questions:
        print("\n❓ Clarifying questions:")
        for q in plan_output.questions:
            print(f"  - {q}")

    # Create task manager and add planned tasks
    todo_mgr = TodoManager()
    task_ids = todo_mgr.add_tasks(plan_output.tasks)

    print("\n" + "=" * 70)
    print(f"⚙️  Executing {len(task_ids)} tasks")
    print("=" * 70)

    # Execute each task
    executed = 0
    failed = 0
    # Limit execution to avoid excessive API calls in demo
    max_tasks = min(3, len(task_ids))

    for i in range(max_tasks):
        next_task = todo_mgr.get_next()
        if not next_task:
            break

        print(f"\n▶️  Executing task {i + 1}/{max_tasks}: {next_task.description}")
        print("-" * 70)

        try:
            result = await execute_task(next_task.description)
            if result.success:
                print(f"✅ Success: {result.output}")
                todo_mgr.mark_done(next_task.id, result.output)
                executed += 1
            else:
                print(f"⚠️  Failed: {result.output}")
                todo_mgr.mark_done(next_task.id, result.output)
                failed += 1
        except ValueError as e:
            print(f"❌ Task validation error: {e}")
            todo_mgr.mark_done(next_task.id, str(e))
            failed += 1
        except RuntimeError as e:
            print(f"❌ Task API error: {e}")
            print("   (Check EXECUTOR_MODEL and corresponding API key)")
            todo_mgr.mark_done(next_task.id, str(e))
            failed += 1
        except Exception as e:
            print(f"❌ Unexpected error: {type(e).__name__}: {e}")
            todo_mgr.mark_done(next_task.id, str(e))
            failed += 1

    # Reflection phase
    print("\n" + "=" * 70)
    print("🔍 Reflecting on progress...")
    print("=" * 70)

    try:
        completed_tasks = todo_mgr.get_done()
        pending_tasks = todo_mgr.get_pending()

        reflection = await reflect_on_progress(goal, completed_tasks, pending_tasks)

        if reflection.done:
            print("✅ Goal is complete!")
        else:
            print("⏳ Goal requires more work")

        if reflection.gaps:
            print("\n❓ Identified gaps:")
            for gap in reflection.gaps:
                print(f"  - {gap}")

        if reflection.new_tasks:
            print("\n📝 Suggested next steps:")
            for task in reflection.new_tasks:
                print(f"  - {task}")

    except ValueError as e:
        print(f"⚠️  Reflection validation error: {e}")
    except RuntimeError as e:
        print(f"⚠️  Reflection API error: {e}")
        print("     (Check REFLECTOR_MODEL and corresponding API key)")
    except Exception as e:
        print(f"⚠️  Reflection skipped: {type(e).__name__}: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("📊 Summary")
    print("=" * 70)
    print(f"✅ Executed successfully: {executed}")
    print(f"❌ Failed: {failed}")
    print(f"📋 Total planned: {len(task_ids)}")
    print(f"⏳ Remaining: {len(todo_mgr.get_pending())}")

    done_tasks = todo_mgr.get_done()
    if done_tasks:
        print("\n✅ Completed tasks:")
        for task in done_tasks:
            print(f"  - {task.description}")
            if task.result and task.result.strip():
                result_preview = task.result[:100] + ("..." if len(task.result) > 100 else "")
                print(f"    → {result_preview}")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
