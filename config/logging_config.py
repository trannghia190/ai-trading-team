"""
Logging configuration for LangChain Trading Team
--------------------------------------------------
- Console : human-readable format with ANSI colours (no external library required)
- File    : JSON format (python-json-logger), rotated daily (TimedRotatingFileHandler)
            Stored at LOG_DIR/trading_team.log, keeps 1 backup file
- Silences noisy third-party loggers (httpx, httpcore, telegram, openai, ...)

Usage (in main.py):
    from .config.logging_config import setup_logging
    setup_logging()

All modules then use the standard library as normal:
    import logging
    logger = logging.getLogger("trading_team.mymodule")
"""
from __future__ import annotations

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

# ==============================================================================
# ANSI color codes — no colorama needed
# ==============================================================================
_RESET = "\033[0m"
_BOLD  = "\033[1m"
_COLORS = {
    "DEBUG":    "\033[36m",   # cyan
    "INFO":     "\033[32m",   # green
    "WARNING":  "\033[33m",   # yellow
    "ERROR":    "\033[31m",   # red
    "CRITICAL": "\033[35m",   # magenta
}

class _ColorConsoleFormatter(logging.Formatter):
    """Human-readable formatter with ANSI colours for terminal."""

    FMT = "%(asctime)s %(color)s%(levelname)-8s%(reset)s %(name)s — %(message)s"
    DATEFMT = "%Y-%m-%d %H:%M:%S"

    def format(self, record: logging.LogRecord) -> str:
        # Work on a copy to avoid affecting other handlers (JSON file)
        r = logging.makeLogRecord(record.__dict__)
        r.color = _COLORS.get(r.levelname, "")
        r.reset = _RESET
        return logging.Formatter(self.FMT, datefmt=self.DATEFMT).format(r)


# ==============================================================================
# Third-party loggers — silence noisy ones
# ==============================================================================
_NOISY_LOGGERS: list[tuple[str, int]] = [
    ("httpx",               logging.WARNING),
    ("httpcore",            logging.WARNING),
    ("openai",              logging.WARNING),
    ("telegram",            logging.WARNING),
    ("telegram.ext",        logging.WARNING),
    ("telegram.ext.Updater", logging.ERROR),
    ("apscheduler",         logging.WARNING),
    ("asyncio",             logging.WARNING),
    ("hpack",               logging.WARNING),
    ("urllib3",             logging.WARNING),
    ("langchain",           logging.WARNING),
    ("langchain_core",      logging.WARNING),
    ("langgraph",           logging.WARNING),
    ("mcp",                 logging.WARNING),
]


# ==============================================================================
# Public API
# ==============================================================================

def setup_logging(
    log_dir: Optional[str | Path] = None,
    log_level: int | str = logging.INFO,
    log_to_file: bool = True,
) -> None:
    """
    Configure logging for the entire application.

    Args:
        log_dir:     Directory for log files. Defaults to settings.LOG_DIR.
        log_level:   Root log level. Defaults to INFO. Accepts int or string ("DEBUG").
        log_to_file: Whether to write logs to file. Defaults to True.
    """
    if isinstance(log_level, str):
        log_level = logging.getLevelName(log_level.upper())

    # ------------------------------------------------------------------
    # Resolve log_dir from settings if not provided
    # ------------------------------------------------------------------
    if log_dir is None:
        try:
            from .settings import LOG_DIR as _settings_log_dir
            log_dir = _settings_log_dir
        except ImportError:
            log_dir = Path(__file__).resolve().parent.parent / "logs"

    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Root logger
    # ------------------------------------------------------------------
    root = logging.getLogger()
    root.setLevel(log_level)

    # Remove existing handlers to avoid duplicates on reload
    root.handlers.clear()

    # ------------------------------------------------------------------
    # Console handler — ANSI colour
    # ------------------------------------------------------------------
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(
        _ColorConsoleFormatter(
            fmt=_ColorConsoleFormatter.FMT,
            datefmt=_ColorConsoleFormatter.DATEFMT,
        )
    )
    root.addHandler(console_handler)

    # ------------------------------------------------------------------
    # File handler — JSON rotating (daily, keep 1 backup)
    # ------------------------------------------------------------------
    if log_to_file:
        try:
            from pythonjsonlogger.json import JsonFormatter

            log_file = log_dir / "trading_team.log"
            file_handler = logging.handlers.TimedRotatingFileHandler(
                filename=log_file,
                when="midnight",
                interval=1,
                backupCount=1,
                encoding="utf-8",
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(
                JsonFormatter(
                    fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
                    datefmt="%Y-%m-%dT%H:%M:%S",
                    rename_fields={"asctime": "ts", "name": "logger", "levelname": "level"},
                    static_fields={"app": "trading_team"},
                )
            )
            # Set suffix for rotating files
            file_handler.suffix = "%Y-%m-%d"
            root.addHandler(file_handler)
        except ImportError:
            logging.getLogger("trading_team.logging").warning(
                "python-json-logger not installed. Logging to console only."
            )

    # ------------------------------------------------------------------
    # Silence noisy third-party loggers
    # ------------------------------------------------------------------
    for name, level in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(level)

    # Ensure trading_team logger always uses the configured level
    trading_logger = logging.getLogger("trading_team")
    trading_logger.setLevel(log_level)

    # ------------------------------------------------------------------
    # Dedicated tools debug log — always DEBUG regardless of root level
    # Captures every [TOOL_CALL] / [TOOL_RESULT] without polluting main log
    # ------------------------------------------------------------------
    if log_to_file:
        try:
            from pythonjsonlogger.json import JsonFormatter as _JF

            tools_file = log_dir / "tools_debug.log"
            tools_handler = logging.handlers.TimedRotatingFileHandler(
                filename=tools_file,
                when="midnight",
                interval=1,
                backupCount=3,
                encoding="utf-8",
            )
            tools_handler.setLevel(logging.DEBUG)
            tools_handler.setFormatter(
                _JF(
                    fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
                    datefmt="%Y-%m-%dT%H:%M:%S",
                    rename_fields={"asctime": "ts", "name": "logger", "levelname": "level"},
                    static_fields={"app": "trading_team"},
                )
            )
            tools_handler.suffix = "%Y-%m-%d"
            tools_logger = logging.getLogger("trading_team.tools")
            tools_logger.setLevel(logging.DEBUG)
            tools_logger.addHandler(tools_handler)
        except ImportError:
            pass  # json logger not available — debug logs go to console only

    logging.getLogger("trading_team.logging").info(
        "Logging initialised. log_dir=%s level=%s file=%s",
        log_dir,
        logging.getLevelName(log_level),
        log_to_file,
    )
