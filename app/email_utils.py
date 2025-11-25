# app/email_utils.py
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.config import settings

def send_email(email: str, subject: str, body: str, send_at: int = None):
    
    message = Mail(
        from_email=settings.FROM_EMAIL,
        to_emails=email,
        subject=subject,
        html_content=body
    )

    
    if send_at:
        message.send_at = send_at

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"[SendGrid] Email sent → {email}, Status: {response.status_code}")
    except Exception as e:
        print("[SendGrid] Error:", e)
