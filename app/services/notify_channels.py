import os
import logging

logger = logging.getLogger(__name__)


async def send_email(to: str | None, subject: str, body: str) -> None:
    """Integrasi email (SMTP/SendGrid). Set SMTP_* di .env untuk mengaktifkan."""
    if not to:
        return
    smtp_host = os.getenv("SMTP_HOST")
    if not smtp_host:
        logger.debug("Email skipped (SMTP_HOST not set): %s", to)
        return
    # TODO: implementasi SMTP sesuai environment kampus
    logger.info("Email [%s] %s", subject, to)


async def send_whatsapp_fonnte(no_hp: str | None, message: str) -> None:
    """Fonnte WhatsApp API — https://fonnte.com"""
    token = os.getenv("FONNTE_TOKEN")
    if not token or not no_hp:
        return
    try:
        import httpx

        async with httpx.AsyncClient() as client:
            await client.post(
                "https://api.fonnte.com/send",
                headers={"Authorization": token},
                data={"target": no_hp, "message": message},
                timeout=15.0,
            )
    except Exception as exc:
        logger.warning("WhatsApp notify failed: %s", exc)
