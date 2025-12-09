import logging
import os
from typing import Optional


def _get_logs_dir() -> str:
    """
    Returns the absolute path to the shared logs directory and ensures it exists.
    Logs live at: <project_root>/logs
    """
    # app/core/logging_utils.py -> app/core -> app -> project_root
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir


def get_logger(name: str, filename: str, level: int = logging.INFO) -> logging.Logger:
    """
    Returns a logger that writes to logs/<filename>, creating the logs directory if needed.
    Each logical part of the system (agent, llm, tools) should use its own file.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)

    logs_dir = _get_logs_dir()
    file_path = os.path.join(logs_dir, filename)

    fh = logging.FileHandler(file_path, encoding="utf-8")
    fh.setLevel(level)
    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh.setFormatter(fmt)

    logger.addHandler(fh)
    logger.propagate = False
    return logger


