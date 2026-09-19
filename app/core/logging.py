"""Structured logging configuration for LLM Brand Visibility Audit Tool.

Configures consistent standard library logging with contextual metadata,
supporting traceable request IDs, audit IDs, provider tags, and execution latency.
Ensures sensitive data such as API credentials and full raw payloads are never leaked.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JSONLogFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects for structured log aggregation.

    Extracts standard fields as well as arbitrary extra contextual attributes
    (e.g., audit_id, provider, prompt_id, latency_ms).
    """

    def format(self, record: logging.LogRecord) -> str:
        log_payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include traceback details if an exception is attached
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        # Include standard context fields if injected via extra={...}
        context_keys = (
            "audit_id",
            "run_id",
            "prompt_id",
            "response_id",
            "provider",
            "model",
            "stage",
            "status",
            "latency_ms",
        )
        for key in context_keys:
            val = getattr(record, key, None)
            if val is not None:
                log_payload[key] = val

        return json.dumps(log_payload, default=str)


def setup_logging(
    log_level: str = "INFO",
    json_format: bool = False,
) -> None:
    """Initialize root logger configuration.

    Args:
        log_level: Desired log level string (e.g. DEBUG, INFO, WARNING, ERROR).
        json_format: Whether to output structured JSON strings or human-readable format.
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)

    if json_format:
        handler.setFormatter(JSONLogFormatter())
    else:
        text_formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(text_formatter)

    root_logger.addHandler(handler)

    # Silence overly verbose external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
