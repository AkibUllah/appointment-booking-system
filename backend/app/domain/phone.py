"""Bangladeshi mobile number normalisation.

Accepts 01XXXXXXXXX, +8801XXXXXXXXX, 8801XXXXXXXXX (with spaces/dashes) and returns
the E.164 form +8801XXXXXXXXX. Valid operator prefixes: 013-019.
"""

from __future__ import annotations

import re

from app.core.errors import ValidationError

_OPERATOR_PREFIXES = {"13", "14", "15", "16", "17", "18", "19"}


def normalize_bd_phone(raw: str) -> str:
    digits = re.sub(r"[\s\-()]", "", raw.strip())
    if digits.startswith("+"):
        digits = digits[1:]
    if digits.startswith("880"):
        digits = digits[3:]
    if digits.startswith("0"):
        digits = digits[1:]
    if len(digits) != 10 or not digits.isdigit() or digits[0] != "1":
        raise ValidationError("phone must be a Bangladeshi mobile number like 01712345678")
    if digits[:2] not in _OPERATOR_PREFIXES:
        raise ValidationError(f"unknown operator prefix 0{digits[:2]}")
    return f"+880{digits}"
