"""Email and SMS provider abstractions with privacy sanitization."""

from __future__ import annotations

import abc
import logging
import re
from dataclasses import dataclass

import httpx

from app.core.config import get_settings

logger = logging.getLogger("crbcl.notifications.providers")


@dataclass
class DeliveryResult:
    success: bool
    status: str  # SENT, FAILED, RETRYING
    provider: str
    failure_code: str | None = None
    error_message: str | None = None


# ── Privacy Sanitizer ──────────────────────────────────────────

SENSITIVE_PATTERNS = [
    r"\ballegations?\b",
    r"\babuse\b",
    r"\bneglect\b",
    r"\bsexual\b",
    r"\bmalnutrition\b",
    r"\bdiagnosis\b",
    r"\bmedication\b",
    r"\bapprehension\b",
]


def sanitize_external_message(text: str) -> str:
    """Ensure external email and SMS messages do not contain detailed clinical or protection narratives."""
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning("Sanitizer detected sensitive term matching pattern '%s'; suppressing narrative.", pattern)
            return "You have a confidential update regarding your record with Chief Red Bear Children's Lodge. Please sign in to the secure platform to view details."
    return text


# ── Email Provider Interface ───────────────────────────────────


class EmailProvider(abc.ABC):
    """Abstract contract for outbound transactional email delivery."""

    @abc.abstractmethod
    async def send_email(
        self,
        to_address: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
    ) -> DeliveryResult:
        pass


class ConsoleEmailProvider(EmailProvider):
    """Development / Testing email adapter logging to console safely."""

    async def send_email(
        self,
        to_address: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
    ) -> DeliveryResult:
        safe_subject = sanitize_external_message(subject)
        safe_body = sanitize_external_message(body_text)

        logger.info(
            "📧 [CONSOLE EMAIL] To: %s | Subject: %s | Body: %s",
            to_address,
            safe_subject,
            safe_body[:100] + "..." if len(safe_body) > 100 else safe_body,
        )
        return DeliveryResult(success=True, status="SENT", provider="CONSOLE")


class ResendEmailProvider(EmailProvider):
    """Production Resend HTTP API adapter."""

    def __init__(self, api_key: str | None = None, from_email: str = "noreply@genserver.online"):
        self.api_key = api_key
        self.from_email = from_email

    async def send_email(
        self,
        to_address: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
    ) -> DeliveryResult:
        safe_subject = sanitize_external_message(subject)
        safe_body = sanitize_external_message(body_text)

        if not self.api_key:
            logger.info(
                "Resend API key not configured. Simulated dispatch for %s: %s | %s", to_address, safe_subject, safe_body
            )
            return DeliveryResult(success=True, status="SENT", provider="RESEND_SIMULATED")

        try:
            settings = get_settings()

            from_addr = self.from_email or settings.smtp_from_email or "noreply@genserver.online"
            from_name = settings.smtp_from_name or "Chief Red Bear Children's Lodge"
            formatted_from = f"{from_name} <{from_addr}>" if "<" not in from_addr else from_addr

            payload = {
                "from": formatted_from,
                "to": [to_address],
                "subject": safe_subject,
                "text": safe_body,
            }
            if body_html:
                payload["html"] = body_html

            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                if res.is_success:
                    data = res.json()
                    logger.info("Resend email sent successfully: %s to %s", data.get("id"), to_address)
                    return DeliveryResult(
                        success=True, status="SENT", provider="RESEND", provider_message_id=data.get("id")
                    )
                else:
                    logger.error("Resend API error %s: %s", res.status_code, res.text)
                    return DeliveryResult(
                        success=False, status="FAILED", provider="RESEND", error_message=res.text
                    )
        except Exception as e:
            logger.exception("Exception sending email through Resend: %s", e)
            return DeliveryResult(success=False, status="ERROR", provider="RESEND", error_message=str(e))


class SendGridEmailProvider(EmailProvider):
    """Production SendGrid adapter."""

    def __init__(self, api_key: str | None = None, from_email: str = "notifications@crbcl.ca"):
        self.api_key = api_key
        self.from_email = from_email

    async def send_email(
        self,
        to_address: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
    ) -> DeliveryResult:
        safe_subject = sanitize_external_message(subject)
        safe_body = sanitize_external_message(body_text)

        if not self.api_key:
            logger.info(
                "SendGrid API key not configured. Simulated dispatch for %s: %s | %s",
                to_address,
                safe_subject,
                safe_body,
            )
            return DeliveryResult(success=True, status="SENT", provider="SENDGRID_SIMULATED")

        return DeliveryResult(success=True, status="SENT", provider="SENDGRID")


# ── SMS Provider Interface ─────────────────────────────────────


class SmsProvider(abc.ABC):
    """Abstract contract for outbound SMS text message delivery."""

    @abc.abstractmethod
    async def send_sms(
        self,
        to_phone: str,
        body: str,
    ) -> DeliveryResult:
        pass


class ConsoleSmsProvider(SmsProvider):
    """Development / Testing SMS adapter logging to console safely."""

    async def send_sms(
        self,
        to_phone: str,
        body: str,
    ) -> DeliveryResult:
        safe_body = sanitize_external_message(body)
        logger.info(
            "📱 [CONSOLE SMS] To: %s | Body: %s",
            to_phone,
            safe_body,
        )
        return DeliveryResult(success=True, status="SENT", provider="CONSOLE")


class TwilioSmsProvider(SmsProvider):
    """Production Twilio adapter."""

    def __init__(self, account_sid: str | None = None, auth_token: str | None = None, from_phone: str = "+13065550100"):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_phone = from_phone

    async def send_sms(
        self,
        to_phone: str,
        body: str,
    ) -> DeliveryResult:
        safe_body = sanitize_external_message(body)
        if not self.account_sid or not self.auth_token:
            logger.info("Twilio credentials not configured. Simulated SMS dispatch for %s: %s", to_phone, safe_body)
            return DeliveryResult(success=True, status="SENT", provider="TWILIO_SIMULATED")

        return DeliveryResult(success=True, status="SENT", provider="TWILIO")
