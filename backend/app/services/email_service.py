"""CRBCL Platform — Email Delivery Service & OTP Engine.

Supports:
1. Resend API (HTTP REST)
2. SMTP / STARTTLS (Gmail, SendGrid, Amazon SES, Custom SMTP)
3. Console fallback logger (prints OTP to server logs when email is unconfigured)
"""

from __future__ import annotations

import asyncio
import email.message
import hashlib
import logging
import secrets
import smtplib
from datetime import UTC, datetime, timedelta
from email.utils import formataddr

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_settings
from app.models.user import EmailVerificationCode, User

logger = logging.getLogger("crbcl.email")


class EmailService:
    """Dispatches verification emails and manages OTP lifecycles."""

    def __init__(self, db: AsyncSession | None = None) -> None:
        self.db = db
        self.settings = get_settings()

    @staticmethod
    def generate_otp_code(length: int = 6) -> str:
        """Generate a cryptographically secure numeric OTP."""
        return "".join(secrets.choice("0123456789") for _ in range(length))

    @staticmethod
    def hash_code(code: str) -> str:
        """Deterministic hash for verification lookup."""
        return hashlib.sha256(code.strip().encode("utf-8")).hexdigest()

    async def create_and_send_verification_code(self, email_address: str) -> str:
        """Generate, store, and dispatch a 6-digit OTP code."""
        code = self.generate_otp_code(6)
        code_hash = self.hash_code(code)
        expires_at = datetime.now(UTC) + timedelta(minutes=15)
        normalized = email_address.strip().lower()

        if self.db:
            # Invalidate prior unused codes for this email
            await self.db.execute(
                update(EmailVerificationCode)
                .where(
                    EmailVerificationCode.email == normalized,
                    EmailVerificationCode.is_used == False,  # noqa: E712
                )
                .values(is_used=True)
            )

            # Store new code
            record = EmailVerificationCode(
                email=normalized,
                code_hash=code_hash,
                expires_at=expires_at,
                is_used=False,
                attempts=0,
            )
            self.db.add(record)
            await self.db.flush()

        # Dispatch email asynchronously
        await self.send_verification_email(normalized, code)
        return code

    async def verify_otp(self, email_address: str, code: str) -> bool:
        """Verify an OTP code against active unexpired records."""
        if not self.db:
            return False

        normalized = email_address.strip().lower()
        now = datetime.now(UTC)

        query = (
            select(EmailVerificationCode)
            .where(
                EmailVerificationCode.email == normalized,
                EmailVerificationCode.is_used == False,  # noqa: E712
                EmailVerificationCode.expires_at > now,
            )
            .order_by(EmailVerificationCode.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(query)
        record = result.scalar_one_or_none()

        if not record:
            logger.warning("No active verification code found for email: %s", normalized)
            return False

        if record.attempts >= 5:
            record.is_used = True
            await self.db.flush()
            logger.warning("Verification code exceeded maximum attempts for: %s", normalized)
            return False

        record.attempts += 1
        expected_hash = self.hash_code(code)

        if record.code_hash == expected_hash:
            record.is_used = True
            # Mark user as verified in database
            user_query = select(User).where(User.email_normalized == normalized)
            user_res = await self.db.execute(user_query)
            user = user_res.scalar_one_or_none()
            if user:
                user.is_verified = True
            await self.db.flush()
            logger.info("Email verification successful for: %s", normalized)
            return True

        await self.db.flush()
        logger.warning("Incorrect OTP code attempted for: %s", normalized)
        return False

    async def send_verification_email(self, to_email: str, code: str) -> bool:
        """Send 6-digit verification code using configured email provider."""
        subject = f"Your CRBCL Verification Code: {code}"
        html_content = self._render_verification_email_html(code)
        text_content = f"Tansi,\n\nYour Chief Red Bear Children's Lodge verification code is: {code}\n\nThis code expires in 15 minutes."

        provider = self._detect_provider()

        if provider == "resend":
            return await self._send_via_resend(to_email, subject, html_content, text_content)
        elif provider == "smtp":
            return await self._send_via_smtp(to_email, subject, html_content, text_content)
        else:
            # Console & Log Fallback (Guarantees dev testing is never blocked)
            logger.info(
                "\n"
                "==============================================================\n"
                "📧 [CRBCL EMAIL OTP NOTIFICATION]\n"
                "--------------------------------------------------------------\n"
                "Recipient : %s\n"
                "OTP Code  : %s\n"
                "Expires In: 15 minutes\n"
                "Notice    : To send real emails, set RESEND_API_KEY or SMTP credentials in .env\n"
                "==============================================================",
                to_email,
                code,
            )
            return True

    def _detect_provider(self) -> str:
        """Determine which email provider to use based on configuration."""
        if self.settings.resend_api_key:
            return "resend"
        if self.settings.smtp_host and self.settings.smtp_user:
            return "smtp"
        if self.settings.email_provider in ("smtp", "resend"):
            return self.settings.email_provider
        return "console"

    async def _send_via_resend(self, to_email: str, subject: str, html: str, text: str) -> bool:
        """Dispatch email via Resend REST API."""
        from_addr = self.settings.smtp_from_email
        if not from_addr or "crbcl.ca" in from_addr:
            from_addr = "onboarding@resend.dev"

        from_header = f"{self.settings.smtp_from_name} <{from_addr}>"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self.settings.resend_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": from_header,
                        "to": [to_email],
                        "subject": subject,
                        "html": html,
                        "text": text,
                    },
                )
                if res.status_code in (200, 201):
                    logger.info("Verification email successfully sent via Resend to %s", to_email)
                    return True
                logger.error("Resend API failed [%s]: %s", res.status_code, res.text)
                return False
        except Exception as e:
            logger.error("Resend network exception: %s", e)
            return False

    async def _send_via_smtp(self, to_email: str, subject: str, html: str, text: str) -> bool:
        """Dispatch email via standard SMTP / STARTTLS."""
        msg = email.message.EmailMessage()
        msg["Subject"] = subject
        msg["From"] = formataddr((self.settings.smtp_from_name, self.settings.smtp_from_email))
        msg["To"] = to_email
        msg.set_content(text)
        msg.add_alternative(html, subtype="html")

        def _sync_send():
            if self.settings.smtp_use_tls and self.settings.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=10)
                if self.settings.smtp_use_tls:
                    server.starttls()

            if self.settings.smtp_user and self.settings.smtp_password:
                server.login(self.settings.smtp_user, self.settings.smtp_password)

            server.send_message(msg)
            server.quit()

        try:
            await asyncio.to_thread(_sync_send)
            logger.info("Verification email sent via SMTP to %s", to_email)
            return True
        except Exception as e:
            logger.error("SMTP delivery failed to %s: %s", to_email, e)
            return False

    @staticmethod
    def _render_verification_email_html(code: str) -> str:
        """Generate high-contrast, accessible HTML email template."""
        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Verify Your Email</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; padding: 40px 16px;">
    <tr>
      <td align="center">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 560px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; overflow: hidden;">
          <!-- Header Banner -->
          <tr>
            <td style="background-color: #881337; padding: 28px 32px; text-align: center;">
              <h1 style="color: #ffffff; font-size: 22px; font-weight: 700; margin: 0; letter-spacing: 0.5px;">Chief Red Bear Children's Lodge</h1>
              <p style="color: #fecdd3; font-size: 13px; margin: 6px 0 0 0;">Family Wellness & Child Protection Platform</p>
            </td>
          </tr>

          <!-- Main Body -->
          <tr>
            <td style="padding: 36px 32px;">
              <h2 style="color: #0f172a; font-size: 20px; font-weight: 600; margin: 0 0 16px 0;">Verify Your Email Address</h2>
              <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                Tansi! Thank you for accessing the CRBCL Platform. Please enter the following 6-digit verification code to complete your registration:
              </p>

              <!-- OTP Code Display -->
              <div style="background-color: #f1f5f9; border-radius: 10px; border: 1px dashed #cbd5e1; padding: 20px; text-align: center; margin: 24px 0;">
                <span style="font-family: monospace, Courier, sans-serif; font-size: 36px; font-weight: 700; letter-spacing: 10px; color: #881337; display: inline-block;">
                  {code}
                </span>
              </div>

              <p style="color: #64748b; font-size: 13px; line-height: 1.5; margin: 20px 0 0 0;">
                ⏱️ <strong>Note:</strong> This verification code will expire in <strong>15 minutes</strong>. If you did not initiate this request, you may safely ignore this email.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px 32px; text-align: center;">
              <p style="color: #94a3b8; font-size: 12px; margin: 0; line-height: 1.4;">
                Cote First Nation • Treaty 4 Territory • CRBCL Family Wellness Information System
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
