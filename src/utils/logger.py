"""Standardized structured logging."""
import logging
import sys
from pathlib import Path
from typing import Optional


def get_logger(name: str = "app", log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """Configure and return a structured console and file logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        # Formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler if specified
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger
