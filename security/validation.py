"""
security/validation.py
----------------------
Server-side input validation. Before this, bad input such as seats="abc" or a
made-up role crashed the request with HTTP 500 (a reliability and security issue).
"""

import re

ALLOWED_ROLES = ("admin", "staff")
ALLOWED_SEAT_CLASSES = ("Economy", "Business", "First Class")


def parse_int(value, minimum=0, maximum=100000):
    """Returns an int in range, or None if the input is invalid."""
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return number if minimum <= number <= maximum else None


def parse_price(value, minimum=0.0, maximum=100000.0):
    """Returns a float in range, or None if the input is invalid."""
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN check
        return None
    return number if minimum <= number <= maximum else None


def validate_role(role) -> bool:
    return role in ALLOWED_ROLES


def validate_password_strength(password: str):
    """Returns (ok, message). Rule: 8+ characters with at least one letter and one digit."""
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return False, "Password must contain at least one letter and one digit."
    return True, ""
