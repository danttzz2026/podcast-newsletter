"""Gmail SMTP sender."""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def send_newsletter(html: str, episode_count: int):
    """Send the HTML newsletter via Gmail SMTP."""
    gmail_address = os.getenv("GMAIL_ADDRESS")
    app_password = os.getenv("GMAIL_APP_PASSWORD")
    if not gmail_address or not app_password:
        raise ValueError("GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set")

    recipient = os.getenv("RECIPIENT_EMAIL") or gmail_address
    today = datetime.now().strftime("%b %d")
    s = "" if episode_count == 1 else "s"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎙️ Pod Digest — {episode_count} new episode{s} · {today}"
    msg["From"] = f"Pod Digest <{gmail_address}>"
    msg["To"] = recipient
    msg.attach(MIMEText(f"Your daily podcast digest has {episode_count} new episode{s}.", "plain"))
    msg.attach(MIMEText(html, "html"))

    print(f"Sending to {recipient}...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, app_password)
        server.send_message(msg)
    print(f"✓ Sent.")
