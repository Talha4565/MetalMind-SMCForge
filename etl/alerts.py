"""
Email alert service for trading signals.
Sends email when model predicts BUY/SELL with confidence > threshold.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class EmailAlertService:
    """Send email alerts for high-confidence trading signals."""
    
    def __init__(
        self,
        smtp_host: str = None,
        smtp_port: int = 587,
        sender_email: str = None,
        sender_password: str = None,
        recipient_email: str = None,
        confidence_threshold: float = 0.70
    ):
        self.smtp_host = smtp_host or os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = sender_email or os.getenv('SENDER_EMAIL', '')
        self.sender_password = sender_password or os.getenv('SENDER_PASSWORD', '')
        self.recipient_email = recipient_email or os.getenv('RECIPIENT_EMAIL', '')
        self.confidence_threshold = confidence_threshold
        self.enabled = bool(self.sender_email and self.sender_password and self.recipient_email)
    
    def should_alert(self, signal: int, confidence: float) -> bool:
        """Check if signal should trigger an alert."""
        if not self.enabled:
            return False
        # Alert on BUY (1) or SELL (-1) with confidence above threshold
        return signal != 0 and confidence >= self.confidence_threshold
    
    def send_alert(
        self,
        asset: str,
        signal: int,
        confidence: float,
        price: float,
        shap_values: list = None,
        prediction_log: dict = None
    ) -> bool:
        """
        Send email alert for a trading signal.
        
        Args:
            asset: 'gold' or 'silver'
            signal: 1 (BUY), -1 (SELL), 0 (HOLD)
            confidence: Model confidence (0-1)
            price: Current price
            shap_values: Top contributing features
            prediction_log: Full prediction data
        
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.warning("Email alerts not configured - missing credentials")
            return False
        
        if not self.should_alert(signal, confidence):
            return False
        
        signal_text = "BUY" if signal == 1 else "SELL"
        signal_emoji = "🟢" if signal == 1 else "🔴"
        asset_upper = asset.upper()
        confidence_pct = f"{confidence * 100:.1f}%"
        
        # Build email
        subject = f"{signal_emoji} {signal_text} Signal: {asset_upper} @ ${price:,.2f} ({confidence_pct} confidence)"
        
        # HTML body
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: {'#059669' if signal == 1 else '#dc2626'}; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0; font-size: 24px;">{signal_emoji} {signal_text} Signal</h1>
                <p style="margin: 5px 0 0; font-size: 18px;">{asset_upper} / USD</p>
            </div>
            
            <div style="padding: 20px; background: #f9fafb;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Signal</td>
                        <td style="padding: 8px; color: {'#059669' if signal == 1 else '#dc2626'}; font-weight: bold; font-size: 18px;">{signal_text}</td>
                    </tr>
                    <tr style="background: #f3f4f6;">
                        <td style="padding: 8px; font-weight: bold;">Confidence</td>
                        <td style="padding: 8px; font-size: 18px;">{confidence_pct}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Price</td>
                        <td style="padding: 8px; font-size: 18px;">${price:,.2f}</td>
                    </tr>
                    <tr style="background: #f3f4f6;">
                        <td style="padding: 8px; font-weight: bold;">Time</td>
                        <td style="padding: 8px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
                    </tr>
                </table>
            """
        
        # Add SHAP values if available
        if shap_values and len(shap_values) > 0:
            html += """
                <div style="margin-top: 20px; padding: 15px; background: white; border-radius: 8px;">
                    <h3 style="margin: 0 0 10px; font-size: 16px;">Key Drivers (SHAP)</h3>
            """
            for sv in shap_values[:5]:
                feature = sv.get('feature', 'Unknown')
                contrib = sv.get('contribution', 0)
                color = '#059669' if contrib > 0 else '#dc2626'
                html += f"""
                    <div style="display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid #e5e7eb;">
                        <span>{feature}</span>
                        <span style="color: {color}; font-weight: bold;">{contrib:+.4f}</span>
                    </div>
                """
            html += "</div>"
        
        html += """
                <div style="margin-top: 20px; padding: 15px; background: #dbeafe; border-radius: 8px;">
                    <p style="margin: 0; font-size: 14px;">
                        <strong>Disclaimer:</strong> This is an automated signal from the MetalMind SMCForge ML model.
                        It is not financial advice. Always do your own research before trading.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send email
        try:
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.sender_email
            message['To'] = self.recipient_email
            
            message.attach(MIMEText(html, 'html'))
            
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.recipient_email, message.as_string())
            
            logger.info(f"✓ Email alert sent: {signal_text} {asset_upper} @ ${price:,.2f} ({confidence_pct})")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to send email alert: {e}")
            return False
    
    def send_raw_email(self, subject: str, body: str) -> bool:
        """Send a raw email (for health alerts, system notifications, etc.)."""
        if not self.enabled:
            return False
        
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.recipient_email, msg.as_string())
            
            logger.info(f"✓ Raw email sent: {subject}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to send raw email: {e}")
            return False
