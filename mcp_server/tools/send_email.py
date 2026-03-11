"""Send an email via SMTP (Gmail by default)."""

from __future__ import annotations
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from common.config import get_settings
from common.errors import MCPError


TOOL_NAME = "send_email"
TOOL_DESCRIPTION = "Send an email with a subject and body to a recipient."
TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "to": {"type": "string", "description": "Recipient email address"},
        "subject": {"type": "string", "description": "Email subject"},
        "body": {"type": "string", "description": "Email body (plain text or HTML)"},
        "is_html": {
            "type": "boolean",
            "description": "Set to true if body is HTML",
            "default": False,
        },
    },
    "required": ["to", "subject", "body"],
}


async def handle(to: str, subject: str, body: str, is_html: bool = False) -> dict:
    settings = get_settings()

    if not settings.smtp_user or settings.smtp_user == "your_email@gmail.com":
        return {
            "success": True,
            "message": f"[MOCK] Email to {to} would be sent with subject: {subject}",
            "_mock": True,
        }

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.email_from
    msg["To"] = to
    msg["Subject"] = subject

    content_type = "html" if is_html else "plain"
    msg.attach(MIMEText(body, content_type))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
        return {"success": True, "message": f"Email sent to {to}"}
    except Exception as e:
        raise MCPError(f"Failed to send email: {e}", tool=TOOL_NAME)
