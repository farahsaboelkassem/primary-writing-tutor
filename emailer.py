"""Sending email over SMTP (works with Gmail app passwords, Brevo, Mailgun, Resend SMTP and others).

Settings come from environment variables (used by send_reports.py) or from Streamlit secrets:
    SMTP_HOST, SMTP_PORT (587 default; 465 uses SSL), SMTP_USER, SMTP_PASSWORD,
    SMTP_FROM   e.g.  The Writing Adventure <reports@yourdomain.com>
    APP_URL     the public address of the app, used in the confirm and stop-emails links
    REPORT_LINK_SECRET   any long random text; signs the links (falls back to the Supabase service key)
"""
import os
import smtplib
import ssl
from email.message import EmailMessage


def get_setting(name, default=""):
    value = os.environ.get(name)
    if value:
        return value
    try:
        import streamlit as st

        value = st.secrets.get(name)
        return str(value) if value else default
    except Exception:
        return default


def link_secret():
    return get_setting("REPORT_LINK_SECRET") or get_setting("SUPABASE_SERVICE_KEY") or get_setting("SUPABASE_SERVICE_ROLE_KEY")


def email_ready():
    """True when everything needed to send reports is set up."""
    needed = ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM", "APP_URL")
    return all(get_setting(k) for k in needed) and bool(link_secret())


def send_email(to, subject, html_body, text_body, attachments=None):
    """attachments: list of (filename, bytes, mime_type) such as ("report.pdf", data, "application/pdf")."""
    msg = EmailMessage()
    msg["From"] = get_setting("SMTP_FROM")
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")
    for filename, data, mime in attachments or []:
        maintype, _, subtype = mime.partition("/")
        msg.add_attachment(data, maintype=maintype, subtype=subtype or "octet-stream", filename=filename)
    host = get_setting("SMTP_HOST")
    port = int(get_setting("SMTP_PORT", "587") or 587)
    context = ssl.create_default_context()
    if port == 465:
        with smtplib.SMTP_SSL(host, port, context=context, timeout=30) as server:
            server.login(get_setting("SMTP_USER"), get_setting("SMTP_PASSWORD"))
            server.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.starttls(context=context)
            server.login(get_setting("SMTP_USER"), get_setting("SMTP_PASSWORD"))
            server.send_message(msg)
