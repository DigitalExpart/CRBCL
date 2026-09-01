"""Prompt Injection Defense & Prohibited Decision Verification Engine."""

import re

PROHIBITED_DECISION_KEYWORDS = [
    "remove child",
    "child removal",
    "abuse finding",
    "substantiate abuse",
    "custody transfer",
    "close case",
    "intake screening decision",
    "financial approval",
    "placement decision",
]

INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"bypass (the )?system",
    r"dump (the )?database",
    r"show (me )?all clients",
    r"read_table",
    r"execute_sql",
]


def inspect_prompt_safety(prompt: str) -> tuple[bool, str]:
    """Inspect user prompt for prompt injection attempts or requests for prohibited decisions.

    Returns (is_safe, reason).
    """
    p_lower = prompt.lower()

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, p_lower):
            return False, "Prompt injection attempt detected and blocked by security gateway."

    for kw in PROHIBITED_DECISION_KEYWORDS:
        if kw in p_lower:
            return (
                False,
                f"Prohibited decision request detected ('{kw}'). AI is strictly assistive and cannot make authoritative legal or child welfare determinations.",
            )

    return True, "SAFE"
