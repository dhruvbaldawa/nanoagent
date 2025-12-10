# ABOUTME: SQLite implementation of persistence protocols
# ABOUTME: Uses WAL mode for concurrent access, implements RunStore, TaskStore, ContextStore

import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from nanoagent.models.schemas import Task, TaskStatus
from nanoagent.persistence.protocols import ContextStore, Phase, RunState, RunStore, TaskStore

logger = logging.getLogger(__name__)


class SQLiteStore(RunStore, TaskStore, ContextStore):
    """
    SQLite-backed persistence store implementing all three protocols.

    Uses WAL mode for concurrent read access. Each run_id provides isolated state.
    """

    def __init__(self, db_path: str | Path, allowed_dir: Path | None = None) -> None:
        """
        Initialize SQLite store.

        Args:
            db_path: Path to SQLite database file. Use ":memory:" for in-memory database.
            allowed_dir: Directory where database files are allowed. If None, path validation
                        is skipped (caller is responsible for ensuring safe paths).

        Raises:
            ValueError: If db_path attempts to escape allowed_dir via path traversal.
            sqlite3.Error: If database connection or initialization fails.
        """
        # Validate and normalize path
        if db_path == ":memory:":
            self.db_path = ":memory:"
        else:
            path = Path(db_path)
            if allowed_dir is not None:
                allowed_dir = allowed_dir.resolve()
                resolved_path = (allowed_dir / path).resolve()
                if not str(resolved_path).startswith(str(allowed_dir)):
                    raise ValueError(f"Database path '{db_path}' escapes allowed directory '{allowed_dir}'")
                self.db_path = str(resolved_path)
            else:
                self.db_path = str(path)

        self._conn: sqlite3.Connection | None = None
        try:
            self._init_db()
        except sqlite3.Error:
            # Clean up connection if initialization fails
            if self._conn is not None:
                try:
                    self._conn.close()
                except sqlite3.Error:
                    pass
                self._conn = None
            raise

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            try:
                self._conn = sqlite3.connect(self.db_path)
                self._conn.execute("PRAGMA journal_mode=WAL")
                self._conn.execute("PRAGMA foreign_keys=ON")
            except sqlite3.Error as e:
                self._conn = None  # Reset on partial failure
                logger.error(f"Failed to connect to database at {self.db_path}: {e}")
                raise
        return self._conn

    def _init_db(self) -> None:
        """Initialize database schema."""
        try:
            conn = self._get_conn()

            conn.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    goal TEXT NOT NULL,
                    max_iterations INTEGER NOT NULL,
                    phase TEXT NOT NULL,
                    iteration INTEGER NOT NULL,
                    current_task_id TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    result TEXT,
                    PRIMARY KEY (run_id, id),
                    FOREIGN KEY (run_id) REFERENCES runs(run_id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS context (
                    run_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    result TEXT NOT NULL,
                    PRIMARY KEY (run_id, task_id),
                    FOREIGN KEY (run_id) REFERENCES runs(run_id)
                )
            """)

            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database schema: {e}")
            raise

    def close(self) -> None:
        """Close database connection. Safe to call multiple times."""
        if self._conn is not None:
            try:
                self._conn.close()
            except sqlite3.Error as e:
                logger.warning(f"Error closing database connection: {e}")
            finally:
                self._conn = None

    # --- RunStore implementation ---

    def create(self, run_id: str, goal: str, max_iterations: int) -> None:
        """Create a new run"""
        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO runs (run_id, goal, max_iterations, phase, iteration, current_task_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, goal, max_iterations, Phase.PLANNING.value, 0, None, datetime.now().isoformat()),
        )
        conn.commit()

    def get(self, run_id: str) -> RunState | None:
        """Get run state by ID"""
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT run_id, goal, max_iterations, phase, iteration, current_task_id, created_at
            FROM runs WHERE run_id = ?
            """,
            (run_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return RunState(
            run_id=row[0],
            goal=row[1],
            max_iterations=row[2],
            phase=Phase(row[3]),
            iteration=row[4],
            current_task_id=row[5],
            created_at=datetime.fromisoformat(row[6]),
        )

    def list_runs(self) -> list[str]:
        """List all run IDs"""
        conn = self._get_conn()
        cursor = conn.execute("SELECT run_id FROM runs ORDER BY created_at DESC")
        return [row[0] for row in cursor.fetchall()]

    def update_loop_state(
        self,
        run_id: str,
        phase: Phase,
        iteration: int,
        current_task_id: str | None,
    ) -> None:
        """Update loop state for checkpointing"""
        conn = self._get_conn()
        conn.execute(
            """
            UPDATE runs SET phase = ?, iteration = ?, current_task_id = ?
            WHERE run_id = ?
            """,
            (phase.value, iteration, current_task_id, run_id),
        )
        conn.commit()

    # --- TaskStore implementation ---

    def save_task(self, run_id: str, task: Task) -> None:
        """Save or update a task"""
        conn = self._get_conn()
        conn.execute(
            """
            INSERT OR REPLACE INTO tasks (id, run_id, description, status, priority, result)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (task.id, run_id, task.description, task.status.value, task.priority, task.result),
        )
        conn.commit()

    def get_all_tasks(self, run_id: str) -> list[Task]:
        """Get all tasks for a run"""
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT id, description, status, priority, result
            FROM tasks WHERE run_id = ?
            ORDER BY priority DESC
            """,
            (run_id,),
        )
        return [
            Task(
                id=row[0],
                description=row[1],
                status=TaskStatus(row[2]),
                priority=row[3],
                result=row[4],
            )
            for row in cursor.fetchall()
        ]

    def get_pending_tasks(self, run_id: str) -> list[Task]:
        """Get pending tasks for a run, ordered by priority descending"""
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT id, description, status, priority, result
            FROM tasks WHERE run_id = ? AND status = ?
            ORDER BY priority DESC
            """,
            (run_id, TaskStatus.PENDING.value),
        )
        return [
            Task(
                id=row[0],
                description=row[1],
                status=TaskStatus(row[2]),
                priority=row[3],
                result=row[4],
            )
            for row in cursor.fetchall()
        ]

    # --- ContextStore implementation ---

    def save_result(self, run_id: str, task_id: str, result: str) -> None:
        """Save task execution result"""
        conn = self._get_conn()
        conn.execute(
            """
            INSERT OR REPLACE INTO context (run_id, task_id, result)
            VALUES (?, ?, ?)
            """,
            (run_id, task_id, result),
        )
        conn.commit()

    def get_all_results(self, run_id: str) -> dict[str, str]:
        """Get all results for a run"""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT task_id, result FROM context WHERE run_id = ?",
            (run_id,),
        )
        return dict(cursor.fetchall())
