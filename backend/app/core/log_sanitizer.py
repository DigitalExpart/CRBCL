"""Log Sanitizer filter redacting sensitive fields from log outputs."""

import logging
import re

SENSITIVE_PATTERNS = [
    (
        r'(?i)(password|secret|token|ssn|health_card|health_number)\s*[:=]\s*["\']?([^"\'\s,]+)["\']?',
        r"\1=***REDACTED***",
    ),
    (r'(?i)(medical_notes|reporter_name|narrative)\s*[:=]\s*["\']?([^"\'\n]+)["\']?', r"\1=***PII_REDACTED***"),
]


class LogSanitizerFilter(logging.Filter):
    """Logging filter stripping PII/PHI narratives, tokens, and secrets from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            sanitized = record.msg
            for pattern, replacement in SENSITIVE_PATTERNS:
                sanitized = re.sub(pattern, replacement, sanitized)
            record.msg = sanitized
        return True
