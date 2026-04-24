"""Gmail SMTP sender — sends the formatted newsletter email."""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def send_newsletter(html: str, episode_count: int):
    """
    Send the newsletter via Gmail SMTP with app password.

    Args:
        html: The formatted HTML newsletter
        episode_count: Number of episodes (for subject line)
    """
    gmail_address = os.getenv("GMAIL_ADDRESS")
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_address or not app_password:
        raise ValueError("GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set in .env")

    today = datetime.now().strftime("%b %d")
    subject = f"🎙️ Pod Digest — {episode_count} new episode{'s' if episode_count != 1 else ''} · {today}"

    msg = MIMEMultipart("alternative")
    recipient = os.getenv("RECIPIENT_EMAIL") or gmail_address

    msg["Subject"] = subject
    msg["From"] = f"Pod Digest <{gmail_address}>"
    msg["To"] = recipient

    # Plain text fallback
    plain_text = f"Your daily podcast digest has {episode_count} new episodes. View this email in HTML for the full newsletter."
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html, "html"))

    print(f"Sending newsletter to {recipient}...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, app_password)
        server.send_message(msg)

    print(f"✓ Newsletter sent successfully!")
