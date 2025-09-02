import smtplib
from email.mime.text import MIMEText
from ..config import settings


def send_email(to_email: str, subject: str, body: str):
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = settings.smtp_from
    msg['To'] = to_email

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        try:
            server.starttls()
        except Exception:
            pass
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_from, [to_email], msg.as_string())


