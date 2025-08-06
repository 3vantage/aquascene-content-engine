"""
Email service for the Subscriber Manager Service
"""

import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
import logging
from typing import Dict, Any, List
from datetime import datetime

from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailService:
    """Email service class using SendGrid"""
    
    def __init__(self):
        if settings.SENDGRID_API_KEY and settings.SENDGRID_API_KEY != "your-sendgrid-api-key-here":
            self.sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        else:
            self.sg = None
            logger.warning("SendGrid API key not configured, emails will be logged only")
    
    async def send_confirmation_email(
        self,
        email: str,
        first_name: str,
        confirmation_token: str
    ) -> bool:
        """Send email confirmation"""
        try:
            # Create confirmation URL - in production, use your actual domain
            confirm_url = f"http://localhost:3001/confirm/{confirmation_token}"
            
            subject = "Welcome to AquaScene - Please Confirm Your Email"
            
            html_content = f"""
            <html>
            <body>
                <h2>Welcome to AquaScene, {first_name}!</h2>
                <p>Thank you for subscribing to our aquascaping newsletter.</p>
                <p>To complete your subscription, please click the link below:</p>
                <a href="{confirm_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    Confirm Subscription
                </a>
                <p>Or copy and paste this URL in your browser: {confirm_url}</p>
                <p>This link will expire in {settings.CONFIRM_EMAIL_EXPIRE_HOURS} hours.</p>
                <p>Best regards,<br>The AquaScene Team</p>
            </body>
            </html>
            """
            
            return await self._send_email(email, subject, html_content)
            
        except Exception as e:
            logger.error(f"Send confirmation email error: {e}")
            return False
    
    async def send_welcome_email(self, email: str, first_name: str) -> bool:
        """Send welcome email after confirmation"""
        try:
            subject = "Welcome to AquaScene!"
            
            html_content = f"""
            <html>
            <body>
                <h2>Welcome to AquaScene, {first_name}!</h2>
                <p>Your subscription has been confirmed successfully.</p>
                <p>You'll now receive our weekly aquascaping newsletter with:</p>
                <ul>
                    <li>Latest aquascaping tips and techniques</li>
                    <li>Plant care guides</li>
                    <li>Community showcases</li>
                    <li>Product recommendations</li>
                </ul>
                <p>Stay tuned for amazing aquascaping content!</p>
                <p>Best regards,<br>The AquaScene Team</p>
            </body>
            </html>
            """
            
            return await self._send_email(email, subject, html_content)
            
        except Exception as e:
            logger.error(f"Send welcome email error: {e}")
            return False
    
    async def send_newsletter(
        self,
        subscribers: List[Dict[str, Any]],
        subject: str,
        content: str
    ) -> int:
        """Send newsletter to multiple subscribers"""
        try:
            sent_count = 0
            
            for subscriber in subscribers:
                success = await self._send_email(
                    subscriber['email'],
                    subject,
                    content
                )
                if success:
                    sent_count += 1
            
            logger.info(f"Newsletter sent to {sent_count}/{len(subscribers)} subscribers")
            return sent_count
            
        except Exception as e:
            logger.error(f"Send newsletter error: {e}")
            return 0
    
    async def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send individual email"""
        try:
            if not self.sg:
                logger.info(f"Would send email to {to_email}: {subject}")
                return True
            
            from_email = Email(settings.SENDER_EMAIL, settings.SENDER_NAME)
            to = To(to_email)
            content = Content("text/html", html_content)
            
            mail = Mail(from_email, to, subject, content)
            
            response = self.sg.send(mail)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email to {to_email}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Send email error: {e}")
            return False