"""
Email Service using Resend SDK
Handles OTP, verification, and notification emails
"""

import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Resend API configuration
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', 'demo-mode')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@metalmind-smc.com')

# Check if Resend is available
try:
    import resend
    RESEND_AVAILABLE = True
    if RESEND_API_KEY != 'demo-mode':
        resend.api_key = RESEND_API_KEY
except ImportError:
    RESEND_AVAILABLE = False
    logger.warning("Resend SDK not installed. Emails will be logged to console only.")


class EmailService:
    """Email service for sending OTPs and notifications."""
    
    def __init__(self):
        self.from_email = FROM_EMAIL
        self.demo_mode = RESEND_API_KEY == 'demo-mode' or not RESEND_AVAILABLE
        
        if self.demo_mode:
            logger.info("Email service running in DEMO MODE - emails will be logged to console")
    
    def send_otp(self, to_email: str, otp_code: str) -> bool:
        """
        Send OTP verification email.
        
        Args:
            to_email: Recipient email address
            otp_code: 6-digit OTP code
            
        Returns:
            bool: True if sent successfully
        """
        subject = "MetalMind SMCForge - Email Verification Code"
        html_content = self._generate_otp_email_html(otp_code)
        text_content = f"Your MetalMind SMCForge verification code is: {otp_code}\n\nThis code expires in 10 minutes."
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    def send_welcome_email(self, to_email: str, username: str) -> bool:
        """Send welcome email after successful verification."""
        subject = "Welcome to MetalMind SMCForge!"
        html_content = self._generate_welcome_email_html(username)
        text_content = f"Welcome to MetalMind SMCForge, {username}!\n\nYour account has been successfully verified."
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    def send_password_reset(self, to_email: str, reset_token: str) -> bool:
        """Send password reset email."""
        subject = "MetalMind SMCForge - Password Reset"
        reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
        html_content = self._generate_reset_email_html(reset_link)
        text_content = f"Reset your password: {reset_link}\n\nThis link expires in 1 hour."
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    def send_2fa_enabled(self, to_email: str) -> bool:
        """Send notification that 2FA was enabled."""
        subject = "MetalMind SMCForge - 2FA Enabled"
        html_content = self._generate_2fa_enabled_html()
        text_content = "Two-factor authentication has been enabled on your account."
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """
        Internal method to send email via Resend or console.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML body
            text_content: Plain text body
            
        Returns:
            bool: True if sent successfully
        """
        if self.demo_mode:
            # Demo mode - log to console
            logger.info("=" * 60)
            logger.info("EMAIL (DEMO MODE)")
            logger.info("=" * 60)
            logger.info(f"To: {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body: {text_content}")
            logger.info("=" * 60)
            print("\n" + "=" * 60)
            print("📧 EMAIL (DEMO MODE)")
            print("=" * 60)
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Body: {text_content}")
            print("=" * 60 + "\n")
            return True
        
        try:
            # Production mode - use Resend
            params = {
                "from": self.from_email,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
                "text": text_content
            }
            
            response = resend.Emails.send(params)
            logger.info(f"Email sent successfully to {to_email}: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def _generate_otp_email_html(self, otp_code: str) -> str:
        """Generate HTML for OTP email."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #0f172a; color: #e2e8f0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #22c55e, #14b8a6); padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background-color: #1e293b; padding: 40px; border-radius: 0 0 10px 10px; }}
                .otp-code {{ font-size: 32px; font-weight: bold; color: #22c55e; letter-spacing: 8px; text-align: center; padding: 20px; background-color: #0f172a; border-radius: 10px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #64748b; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0; color: white;">🧠 MetalMind SMCForge</h1>
                    <p style="margin: 10px 0 0 0; color: white;">ML Trading Intelligence</p>
                </div>
                <div class="content">
                    <h2 style="color: #22c55e;">Email Verification</h2>
                    <p>Thank you for registering with MetalMind SMCForge!</p>
                    <p>Your verification code is:</p>
                    <div class="otp-code">{otp_code}</div>
                    <p>This code will expire in <strong>10 minutes</strong>.</p>
                    <p>If you didn't request this code, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2026 MetalMind SMCForge. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _generate_welcome_email_html(self, username: str) -> str:
        """Generate HTML for welcome email."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #0f172a; color: #e2e8f0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #22c55e, #14b8a6); padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background-color: #1e293b; padding: 40px; border-radius: 0 0 10px 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0; color: white;">🧠 MetalMind SMCForge</h1>
                </div>
                <div class="content">
                    <h2 style="color: #22c55e;">Welcome, {username}! 🎉</h2>
                    <p>Your account has been successfully verified.</p>
                    <p>You can now access all features including:</p>
                    <ul>
                        <li>Live ML predictions with 90.59% accuracy</li>
                        <li>SHAP explainability analysis</li>
                        <li>Backtesting with 1,997 simulated trades</li>
                        <li>Real-time signal generation</li>
                    </ul>
                    <p>Start trading smarter with AI-powered insights!</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _generate_reset_email_html(self, reset_link: str) -> str:
        """Generate HTML for password reset email."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #0f172a; color: #e2e8f0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .content {{ background-color: #1e293b; padding: 40px; border-radius: 10px; }}
                .button {{ display: inline-block; padding: 15px 30px; background-color: #22c55e; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="content">
                    <h2 style="color: #22c55e;">Password Reset Request</h2>
                    <p>Click the button below to reset your password:</p>
                    <a href="{reset_link}" class="button">Reset Password</a>
                    <p>This link expires in 1 hour.</p>
                    <p>If you didn't request this, please ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _generate_2fa_enabled_html(self) -> str:
        """Generate HTML for 2FA enabled notification."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; background-color: #0f172a; color: #e2e8f0; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .content { background-color: #1e293b; padding: 40px; border-radius: 10px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="content">
                    <h2 style="color: #22c55e;">🔒 2FA Enabled</h2>
                    <p>Two-factor authentication has been successfully enabled on your account.</p>
                    <p>Your account is now more secure!</p>
                </div>
            </div>
        </body>
        </html>
        """


# Global email service instance
email_service = EmailService()
