"""AWS SNS Service for sending SMS"""
import logging
import boto3
from botocore.exceptions import ClientError

from app.infrastructure.config import settings

logger = logging.getLogger(__name__)


class SNSService:
    """Service for sending SMS via AWS SNS"""

    def __init__(self):
        self.sns_client = boto3.client(
            "sns",
            region_name=settings.AWS_SNS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self.sender_id = settings.AWS_SNS_SENDER_ID

    async def send_sms(
        self,
        phone_number: str,
        message: str,
        message_type: str = "Transactional",
    ) -> bool:
        """
        Send an SMS via SNS

        Args:
            phone_number: Phone number in E.164 format (e.g., +34600123456)
            message: SMS message content
            message_type: "Promotional" or "Transactional" (default)

        Returns:
            bool: True if sent successfully
        """
        try:
            # Ensure phone number starts with +
            if not phone_number.startswith("+"):
                logger.error(f"Phone number must be in E.164 format: {phone_number}")
                return False

            # Send SMS
            response = self.sns_client.publish(
                PhoneNumber=phone_number,
                Message=message,
                MessageAttributes={
                    "AWS.SNS.SMS.SenderID": {
                        "DataType": "String",
                        "StringValue": self.sender_id,
                    },
                    "AWS.SNS.SMS.SMSType": {
                        "DataType": "String",
                        "StringValue": message_type,
                    },
                },
            )

            logger.info(f"SMS sent successfully to {phone_number}. MessageId: {response['MessageId']}")
            return True

        except ClientError as e:
            logger.error(f"Error sending SMS via SNS: {e}")
            return False

    async def send_otp_sms(self, phone_number: str, otp_code: str) -> bool:
        """Send OTP verification SMS"""
        message = f"Tu código de verificación de Agape es: {otp_code}. Válido por {settings.OTP_EXPIRY_MINUTES} minutos."

        return await self.send_sms(
            phone_number=phone_number,
            message=message,
            message_type="Transactional",
        )

    async def send_password_reset_sms(self, phone_number: str, reset_code: str) -> bool:
        """Send password reset SMS"""
        message = f"Tu código para restablecer contraseña en Agape es: {reset_code}. Válido por {settings.OTP_EXPIRY_MINUTES} minutos."

        return await self.send_sms(
            phone_number=phone_number,
            message=message,
            message_type="Transactional",
        )

    async def send_alert_sms(self, phone_number: str, alert_message: str) -> bool:
        """Send general alert SMS"""
        message = f"Agape: {alert_message}"

        return await self.send_sms(
            phone_number=phone_number,
            message=message,
            message_type="Promotional",
        )


# Singleton instance
sns_service = SNSService()
