import smtplib
from email.mime.text import MIMEText
from typing import Optional
import logging
from ..config import settings

logger = logging.getLogger(__name__)

# Global flag to track email availability
_email_available = None

def is_email_available() -> bool:
    """Check if email service is available and configured"""
    global _email_available
    
    if _email_available is not None:
        return _email_available
    
    try:
        # Check if SMTP is configured
        if not settings.smtp_host or not settings.smtp_port:
            logger.warning("Email not configured: Missing SMTP host or port")
            _email_available = False
            return False
        
        if not settings.smtp_from:
            logger.warning("Email not configured: Missing SMTP from address")
            _email_available = False
            return False
        
        # Test SMTP connection
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            try:
                server.starttls()
            except Exception:
                pass  # Some servers don't support STARTTLS
            
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
        
        _email_available = True
        logger.info("Email service is available and configured")
        return True
        
    except Exception as e:
        logger.warning(f"Email service not available: {str(e)}")
        _email_available = False
        return False

def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Send email with error handling
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    if not is_email_available():
        logger.warning("Email service is not available. Cannot send email.")
        return False
    
    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = settings.smtp_from
        msg['To'] = to_email

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            try:
                server.starttls()
            except Exception:
                pass  # Some servers don't support STARTTLS
            
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
            
            server.sendmail(settings.smtp_from, [to_email], msg.as_string())
        
        logger.info(f"Email sent successfully to: {to_email}")
        return True
        
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending email: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email: {str(e)}")
        return False

def send_verification_email(to_email: str, verification_token: str) -> bool:
    """Send email verification email"""
    verify_link = f'https://frontend.example.com/verify-email?token={verification_token}'
    subject = "Verify your email address"
    body = f"""
Hello,

Please verify your email address by clicking the link below:

{verify_link}

If you did not create an account, please ignore this email.

Best regards,
Alta Data Team
"""
    return send_email(to_email, subject, body)

def send_project_invitation_email(to_email: str, project_name: str, invitation_token: str, inviter_name: str = "A team member") -> bool:
    """Send project invitation email"""
    invite_link = f'https://frontend.example.com/accept-invitation?token={invitation_token}'
    subject = f"Invitation to join project: {project_name}"
    body = f"""
Hello,

{inviter_name} has invited you to join the project "{project_name}".

Click the link below to accept the invitation:

{invite_link}

If you do not want to join this project, please ignore this email.

Best regards,
Alta Data Team
"""
    return send_email(to_email, subject, body)


