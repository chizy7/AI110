"""
Guardrails: input validation, logging setup, and safety checks.

Provides centralized logging configuration and validation functions
that the agent uses before and after processing requests.
"""

import logging
import sys

# Minimum confidence below which the system warns the user
LOW_CONFIDENCE_THRESHOLD = 0.4

# Queries shorter than this are rejected
MIN_QUERY_LENGTH = 3


def setup_logging(level: int = logging.INFO) -> None:
    """Configure structured logging to both console and file."""
    root = logging.getLogger()
    root.setLevel(level)

    # Clear existing handlers
    root.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(formatter)
    root.addHandler(console)

    # File handler
    file_handler = logging.FileHandler("docubot.log", mode="a")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


def validate_query(query: str) -> tuple[bool, str]:
    """
    Validate user input before processing.
    Returns (is_valid, error_message).
    """
    if not query or not query.strip():
        return False, "Empty query. Please describe what kind of music you want."

    cleaned = query.strip()
    if len(cleaned) < MIN_QUERY_LENGTH:
        return False, f"Query too short (minimum {MIN_QUERY_LENGTH} characters)."

    return True, ""


def check_confidence(confidence: float) -> str | None:
    """
    Returns a warning message if confidence is below threshold, else None.
    """
    if confidence < LOW_CONFIDENCE_THRESHOLD:
        return (
            f"Low confidence ({confidence:.0%}). The recommendations may not "
            f"match your request well. Try being more specific about genre, "
            f"mood, or energy level."
        )
    return None
