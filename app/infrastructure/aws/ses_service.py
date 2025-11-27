"""AWS SES Service for sending emails"""
import logging
from typing import List, Optional
import boto3
from botocore.exceptions import ClientError

from app.infrastructure.config import settings

logger = logging.getLogger(__name__)


class SESService:
    """Service for sending emails via AWS SES"""

    def __init__(self):
        self.ses_client = boto3.client(
            "ses",
            region_name=settings.AWS_SES_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self.from_email = settings.AWS_SES_FROM_EMAIL
        self.reply_to_email = settings.AWS_SES_REPLY_TO_EMAIL

    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> bool:
        """
        Send an email via SES

        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            html_body: HTML body content
            text_body: Plain text body (optional)
            reply_to: Reply-to address (optional)

        Returns:
            bool: True if sent successfully
        """
        try:
            # Prepare message
            message = {
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": html_body, "Charset": "UTF-8"},
                },
            }

            if text_body:
                message["Body"]["Text"] = {"Data": text_body, "Charset": "UTF-8"}

            # Prepare destination
            destination = {"ToAddresses": to_emails}

            # Reply-to address
            reply_to_addresses = [reply_to or self.reply_to_email or self.from_email]

            # Send email
            response = self.ses_client.send_email(
                Source=self.from_email,
                Destination=destination,
                Message=message,
                ReplyToAddresses=reply_to_addresses,
            )

            logger.info(f"Email sent successfully to {to_emails}. MessageId: {response['MessageId']}")
            return True

        except ClientError as e:
            logger.error(f"Error sending email via SES: {e}")
            return False

    async def send_otp_email(self, email: str, otp_code: str, purpose: str = "login") -> bool:
        """Send OTP verification email"""
        subject = "Tu código de verificación - Agape"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
                <h2 style="color: #4a4a4a; text-align: center;">Código de Verificación</h2>
                <p>Hola,</p>
                <p>Tu código de verificación para <strong>{purpose}</strong> es:</p>
                <div style="background-color: #f4f4f4; padding: 15px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 8px; border-radius: 5px; margin: 20px 0;">
                    {otp_code}
                </div>
                <p>Este código expirará en {settings.OTP_EXPIRY_MINUTES} minutos.</p>
                <p>Si no solicitaste este código, puedes ignorar este correo.</p>
                <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
                <p style="font-size: 12px; color: #888; text-align: center;">
                    Este es un correo automático, por favor no respondas a este mensaje.
                </p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Tu código de verificación para {purpose} es: {otp_code}

        Este código expirará en {settings.OTP_EXPIRY_MINUTES} minutos.

        Si no solicitaste este código, puedes ignorar este correo.
        """

        return await self.send_email(
            to_emails=[email],
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )

    async def send_welcome_email(self, email: str, username: str) -> bool:
        """Send welcome email to new users"""
        subject = "¡Bienvenido a Agape!"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4a4a4a; text-align: center;">¡Bienvenido a Agape, {username}!</h2>
                <p>Nos alegra tenerte con nosotros.</p>
                <p>Tu cuenta ha sido creada exitosamente y ya puedes comenzar a explorar la plataforma.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{settings.FRONTEND_URL}" style="background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Ir a la Plataforma
                    </a>
                </div>
                <p>Si tienes alguna pregunta, no dudes en contactarnos.</p>
                <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
                <p style="font-size: 12px; color: #888; text-align: center;">
                    Este es un correo automático, por favor no respondas a este mensaje.
                </p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        ¡Bienvenido a Agape, {username}!

        Nos alegra tenerte con nosotros.
        Tu cuenta ha sido creada exitosamente y ya puedes comenzar a explorar la plataforma.

        Visita: {settings.FRONTEND_URL}
        """

        return await self.send_email(
            to_emails=[email],
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )

    async def send_password_reset_email(self, email: str, reset_code: str) -> bool:
        """Send password reset email"""
        subject = "Restablece tu contraseña - Agape"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
                <h2 style="color: #4a4a4a; text-align: center;">Restablecer Contraseña</h2>
                <p>Hola,</p>
                <p>Recibimos una solicitud para restablecer tu contraseña. Tu código de verificación es:</p>
                <div style="background-color: #f4f4f4; padding: 15px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 8px; border-radius: 5px; margin: 20px 0;">
                    {reset_code}
                </div>
                <p>Este código expirará en {settings.OTP_EXPIRY_MINUTES} minutos.</p>
                <p>Si no solicitaste restablecer tu contraseña, ignora este correo y tu contraseña permanecerá sin cambios.</p>
                <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
                <p style="font-size: 12px; color: #888; text-align: center;">
                    Este es un correo automático, por favor no respondas a este mensaje.
                </p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Restablecer Contraseña

        Recibimos una solicitud para restablecer tu contraseña.
        Tu código de verificación es: {reset_code}

        Este código expirará en {settings.OTP_EXPIRY_MINUTES} minutos.

        Si no solicitaste restablecer tu contraseña, ignora este correo.
        """

        return await self.send_email(
            to_emails=[email],
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )


# Singleton instance
ses_service = SESService()
