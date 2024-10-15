"""This module is used to manage messages"""
from typing import Optional, Dict
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.config import settings
from app.models.message import SentDetails

class TwilioRepository:
    """Repository for handling Twilio WhatsApp, SMS, and email sending operations."""

    def __init__(self):
        """Initialize the repository with Twilio and email clients."""
        self.twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)

    async def send_whatsapp(self, to: str, body: str) -> Optional[SentDetails]:
        """Send a WhatsApp message using Twilio."""
        return await self._send_message(
            to=f"whatsapp:+57{to}",
            body=body,
            from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
            message_type="WhatsApp"
        )

    async def send_sms(self, to: str, body: str) -> Optional[SentDetails]:
        """Send an SMS message using Twilio."""
        return await self._send_message(
            to=f"+57{to}",
            body=body,
            from_=settings.TWILIO_SMS_NUMBER,
            message_type="SMS"
        )

    async def send_email(self, to_email: str, subject: str, content: str) -> Optional[Dict[str, str]]:
        """Send an email using SendGrid."""
        try:
            message = Mail(
                from_email=settings.SENDGRID_FROM_EMAIL,
                to_emails=to_email,
                subject=subject,
                html_content=content
            )
            response = self.sendgrid_client.send(message)
            return {
                "status_code": str(response.status_code),
                "body": response.body.decode(),
                "headers": str(response.headers)
            }
        except Exception as e:
            print(f"Error sending email: {e}")
            return None

    async def _send_message(self, to: str, body: str, from_: str, message_type: str) -> Optional[SentDetails]:
        """Helper method to send messages via Twilio (SMS or WhatsApp)."""
        try:
            # Log message details
            print(f"Sending {message_type} message to: {to}")
            print(f"From number: {from_}")
            print(f"Message body: {body}")

            # Use the correct `create` method to send the message
            message = self.twilio_client.messages.create(
                body=body,
                from_=from_,
                to=to
            )

            # Return details of the sent message
            return SentDetails(
                sid=message.sid,
                dateCreated=str(message.date_created),
                dateQueued=str(message.date_sent),
                to=to,
                from_=from_,
                body=body,
                status=message.status
            )
        except Exception as e:
            print(f"Error sending {message_type} message: {e}")
            return None
