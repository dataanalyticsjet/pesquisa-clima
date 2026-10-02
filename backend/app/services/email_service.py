import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import settings


logger = logging.getLogger(__name__)


class EmailUnavailableError(RuntimeError):
    pass


class EmailService:
    def send_login_code(self, recipient: str, code: str, ttl_minutes: int) -> None:
        message = EmailMessage()
        message["Subject"] = "Pesquisa de Clima — Código de acesso"
        message["From"] = settings.smtp_from
        message["To"] = recipient
        message.set_content(
            "Pesquisa de Clima\n\n"
            f"Seu código de acesso é: {code}\n\n"
            f"O código expira em {ttl_minutes} minutos e pode ser usado uma única vez.\n\n"
            "Se você não solicitou este acesso, ignore esta mensagem."
        )
        self._deliver(message)

    def _deliver(self, message: EmailMessage) -> None:
        if not settings.smtp_configured:
            logger.error("email.config Configuração SMTP incompleta")
            raise EmailUnavailableError("Serviço de e-mail indisponível.")
        try:
            smtp_class = smtplib.SMTP_SSL if settings.smtp_ssl else smtplib.SMTP
            options: dict[str, object] = {
                "host": settings.smtp_host,
                "port": settings.smtp_port,
                "timeout": settings.smtp_timeout_seconds,
            }
            if settings.smtp_ssl:
                options["context"] = ssl.create_default_context()
            with smtp_class(**options) as smtp:
                smtp.ehlo()
                if settings.smtp_starttls:
                    smtp.starttls(context=ssl.create_default_context())
                    smtp.ehlo()
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException):
            logger.error("email.send Falha controlada no envio SMTP")
            raise EmailUnavailableError("Serviço de e-mail indisponível.") from None
        logger.info("email.send E-mail aceito pelo SMTP")


email_service = EmailService()
