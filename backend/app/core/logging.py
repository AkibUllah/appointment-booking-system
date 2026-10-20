"""Logging configuration shared by the API process and the scheduler."""

from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level.upper())
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s | %(message)s", "%Y-%m-%dT%H:%M:%S")
    )
    root.addHandler(handler)
    root.setLevel(level.upper())
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
