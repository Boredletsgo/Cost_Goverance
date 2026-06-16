"""Email reporting. Uses SMTP if configured, otherwise logs to console."""
from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


def send_email(subject: str, html_body: str, text_body: str, recipients: List[str]) -> bool:
    """Send an email. Returns True if dispatched via SMTP, False if console-only."""
    if not settings.smtp_host:
        logger.info(
            "[EMAIL:console] To=%s | Subject=%s\n%s",
            ", ".join(recipients),
            subject,
            text_body,
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_from, recipients, msg.as_string())
    logger.info("Email sent to %s via SMTP.", recipients)
    return True
