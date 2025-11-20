# ABOUTME: Real-time event emission for orchestration progress visibility
# ABOUTME: Provides fire-and-forget JSON event streaming to stdout

import json
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class StreamManager:
    """
    Emits real-time events during orchestration for visibility into progress.

    Outputs JSON-formatted events with type, data, and ISO timestamp.
    Non-blocking: events are printed to stdout and execution continues immediately.
    """

    def emit(self, event_type: str, data: Any) -> None:
        """
        Emit a JSON event with timestamp (fire-and-forget, never raises).

        Non-blocking event streaming: failures are logged but do not crash orchestration.

        Args:
            event_type: Type of event (e.g., "task_started", "task_completed", "reflection")
            data: Event data (typically dict, but any JSON-serializable type)
        """
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            json_str = json.dumps(event)
            print(json_str)
            logger.debug("Emitted event", extra={"event_type": event_type})
        except (TypeError, ValueError) as e:
            extra: dict[str, str] = {
                "event_type": event_type,
                "error": str(e),
            }
            if isinstance(data, dict):
                extra["data_keys"] = str(list(data.keys()))  # pyright: ignore[reportUnknownArgumentType]
            else:
                extra["data_type"] = type(data).__name__
            logger.error("Failed to serialize event for emission", extra=extra)
        except Exception as e:
            logger.error(
                "Failed to write event to stdout",
                extra={
                    "event_type": event_type,
                    "error": str(e),
                },
            )
