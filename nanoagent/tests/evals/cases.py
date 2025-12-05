# ABOUTME: Test cases for eval framework
# ABOUTME: Define evaluation test scenarios for quality dimensions

PLAN_QUALITY_CASES = [
    {
        "name": "simple_goal",
        "goal": "Write a hello world program in Python",
        "expected_characteristics": ["focused tasks", "1-3 steps", "clear sequence"],
    },
    {
        "name": "well_defined_goal",
        "goal": "Create a Python script that reads a CSV file and prints the first 5 rows",
        "expected_characteristics": ["concrete steps", "logical ordering", "clear sequence"],
    },
    {
        "name": "multi_step_goal",
        "goal": "Set up a Python virtual environment and install Flask framework",
        "expected_characteristics": ["sequential steps", "clear decomposition", "actionable tasks"],
    },
]

REFLECTION_ACCURACY_CASES = [
    {
        "name": "correct_gap_identification",
        "execution_summary": (
            "Task 1 completed: Analyzed requirements. Task 2 completed: "
            "Designed architecture. Task 3 failed: Database migration timeout."
        ),
        "expected_characteristics": [
            "correct gap identification",
            "realistic assessment",
            "actionable next steps",
        ],
    },
    {
        "name": "progress_assessment",
        "execution_summary": (
            "Started with 5 tasks. Completed 3 tasks successfully "
            "(req analysis, design, API setup). 2 remaining (database, testing)."
        ),
        "expected_characteristics": [
            "accurate progress",
            "realistic completion estimate",
            "no false positives",
        ],
    },
    {
        "name": "false_positive_avoidance",
        "execution_summary": (
            "All 5 tasks completed. Database migration succeeded. API fully functional. All tests passing."
        ),
        "expected_characteristics": [
            "no false gaps",
            "accurate completion",
            "realistic assessment",
        ],
    },
]

EXECUTION_CORRECTNESS_CASES = [
    {
        "name": "correct_execution",
        "task_description": "Implement user login with JWT tokens",
        "execution_result": (
            "Created authentication module with JWT token generation, validation, and refresh logic. All tests passing."
        ),
        "expected_characteristics": [
            "task completed as described",
            "meets requirements",
            "error handling",
        ],
    },
    {
        "name": "partial_execution",
        "task_description": "Set up database with users, posts, and comments tables",
        "execution_result": ("Created users and posts tables. Comments table pending due to schema complexity."),
        "expected_characteristics": [
            "partial completion recognized",
            "quality maintained",
            "gaps identified",
        ],
    },
    {
        "name": "execution_with_issues",
        "task_description": "Integrate external payment API",
        "execution_result": ("Integration complete but with temporary hardcoded credentials. Needs security review."),
        "expected_characteristics": [
            "issues identified",
            "functional output",
            "quality concerns noted",
        ],
    },
]

CONVERGENCE_BEHAVIOR_CASES = [
    {
        "name": "steady_progress",
        "iteration_summary": (
            "Iter 1: Plan 5 tasks. Iter 2: Complete 2 tasks, identify gaps. "
            "Iter 3: Complete 2 more tasks. Iter 4: Final task completed."
        ),
        "expected_characteristics": ["steady progress", "gap reduction", "goal achievement"],
    },
    {
        "name": "divergent_iteration",
        "iteration_summary": (
            "Iter 1: Plan 3 tasks. Iter 2: Realize need for more research. "
            "Iter 3: Replanned with 5 tasks. Iter 4-5: Execute on new plan."
        ),
        "expected_characteristics": [
            "appropriate replanning",
            "recovered convergence",
            "goal-focused",
        ],
    },
    {
        "name": "inefficient_but_converging",
        "iteration_summary": (
            "Iter 1: Plan vague. Iter 2: Clarified. Iter 3: Execute 1 task. "
            "Iter 4: Execute 1 task. Iter 5: Execute 2 tasks. Goal met."
        ),
        "expected_characteristics": [
            "eventually converges",
            "inefficiency recognized",
            "goal reached",
        ],
    },
]
