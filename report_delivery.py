"""Who gets progress reports, and how they are confirmed and sent.

A child (or the grown-up using their account) adds a parent or teacher's email. Nothing is sent
except ONE confirmation email. Reports only start once that person clicks the confirm link, and
every report has a "stop these emails" link. Links are signed, so they cannot be guessed or edited.
"""
import hashlib
import hmac
import html
import re
from datetime import datetime, timedelta, timezone

import emailer
import progress_report

EMAIL_RE = re.compile(r"^[^@\s,;]+@[^@\s,;]+\.[^@\s,;]+$")
MAX_RECIPIENTS = 3            # per student
CONFIRM_COOLDOWN_MINUTES = 10


def _now():
    return datetime.now(timezone.utc)


# ---- signed links
def sign(action, recipient_id):
    key = emailer.link_secret()
    if not key:
        raise RuntimeError("No link secret is set.")
    sig = hmac.new(key.encode(), f"{action}:{recipient_id}".encode(), hashlib.sha256).hexdigest()[:32]
    return f"{recipient_id}.{sig}"


def verify(action, token):
    """Returns the recipient id if the link is genuine, else None."""
    rid, _, sig = str(token or "").rpartition(".")
    if not rid or not sig:
        return None
    try:
        expected = sign(action, rid).rpartition(".")[2]
    except RuntimeError:
        return None
    return rid if hmac.compare_digest(sig, expected) else None


def link(action, recipient_id):
    return f"{emailer.get_setting('APP_URL').rstrip('/')}/?{action}={sign(action, recipient_id)}"


# ---- adding a recipient
def list_recipients(db, student_id):
    try:
        rows = db.table("report_recipients").select("*").eq("student_id", student_id).execute().data or []
    except Exception as exc:
        print(f"[inky] reports: could not read recipients: {exc}")
        return []
    return sorted(rows, key=lambda r: str(r.get("created_at", "")))


def _send_confirmation(rid, email, recipient_name, student_name):
    url = link("confirm", rid)
    who = html.escape(recipient_name or "there")
    child = html.escape(student_name)
    body = (
        f"<div style='font-family:Arial,sans-serif;max-width:560px;line-height:1.5;color:#2b2a4a;'>"
        f"<p>Hello {who},</p><p><b>{child}</b> would like to share progress reports from <b>The Writing Adventure</b> with you. "
        f"Each report shows what {child} has practised, strengths, and areas to work on. It never includes their writing.</p>"
        f"<p><a href='{html.escape(url)}' style='background:#4a43b0;color:#fff;padding:10px 18px;border-radius:999px;"
        f"text-decoration:none;font-weight:bold;'>Yes, send me reports</a></p>"
        f"<p style='color:#5b5a73;font-size:13px;'>If you were not expecting this, just ignore this email. "
        f"Nothing will be sent to you unless you press the button.</p></div>"
    )
    text = (f"Hello {recipient_name or 'there'},\n\n{student_name} would like to share progress reports from The Writing Adventure "
            f"with you (strengths and areas to practise; never their writing).\n\nTo agree, open: {url}\n\n"
            f"If you were not expecting this, ignore this email. Nothing will be sent unless you open the link.")
    emailer.send_email(email, f"{student_name} would like to share progress reports with you", body, text)


def request_recipient(db, student_id, student_name, email, recipient_name="", role="parent"):
    """Returns (ok, message for the screen)."""
    if not emailer.email_ready():
        return False, "Emailing is not switched on yet. Ask the app owner to set it up. You can still download the report."
    email = str(email or "").strip().lower()
    if not EMAIL_RE.match(email) or len(email) > 120:
        return False, "That email address does not look right. Please check it."
    recipient_name = " ".join(str(recipient_name or "").split())[:60]
    role = role if role in ("parent", "teacher") else "parent"
    rows = list_recipients(db, student_id)
    existing = next((r for r in rows if r.get("email") == email), None)
    if existing:
        if existing.get("status") == "confirmed":
            return False, "That address is already receiving reports."
        if existing.get("status") == "unsubscribed":
            return False, "That address asked not to receive reports, so we can't add it again."
        sent = _parse(existing.get("confirm_sent_at"))
        if sent and _now() - sent < timedelta(minutes=CONFIRM_COOLDOWN_MINUTES):
            return False, "A confirmation email was just sent. Please wait a few minutes before sending another."
    elif sum(1 for r in rows if r.get("status") != "unsubscribed") >= MAX_RECIPIENTS:
        return False, f"You can add up to {MAX_RECIPIENTS} people. Remove one first."
    try:
        if existing:
            rid = existing["id"]
            db.table("report_recipients").update(
                {"recipient_name": recipient_name, "role": role, "confirm_sent_at": _now().isoformat()}
            ).eq("id", rid).execute()
        else:
            res = db.table("report_recipients").insert({
                "student_id": student_id, "email": email, "recipient_name": recipient_name, "role": role,
                "status": "pending", "confirm_sent_at": _now().isoformat(),
            }).execute()
            rid = res.data[0]["id"]
        _send_confirmation(rid, email, recipient_name, student_name)
    except Exception as exc:
        print(f"[inky] reports: could not add recipient: {exc}")
        return False, "Something went wrong, so no email was sent. Please try again later."
    return True, f"We sent a confirmation email to {email}. Reports start once they press the button in it."


def remove_recipient(db, student_id, recipient_id):
    try:
        db.table("report_recipients").delete().eq("id", recipient_id).eq("student_id", student_id).execute()
        return True
    except Exception as exc:
        print(f"[inky] reports: could not remove recipient: {exc}")
        return False


def confirm_or_unsub(db, action, token):
    """Handles the links in emails. Returns (ok, message)."""
    rid = verify(action, token)
    if not rid:
        return False, "This link is not valid, or it has been changed."
    try:
        if action == "confirm":
            db.table("report_recipients").update({"status": "confirmed", "confirmed_at": _now().isoformat()}).eq("id", rid).execute()
            return True, "Thank you! You will now receive progress reports. Each one has a link to stop them at any time."
        db.table("report_recipients").update({"status": "unsubscribed"}).eq("id", rid).execute()
        return True, "Done. You will not receive any more progress reports."
    except Exception as exc:
        print(f"[inky] reports: could not update recipient: {exc}")
        return False, "Something went wrong. Please try the link again later."


# ---- sending reports
def _parse(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def send_report_to(db, recipient, days=None):
    """Build and email one report to one confirmed recipient. Returns the student's report dict."""
    days = days or (30 if recipient.get("frequency") == "monthly" else 7)
    raw = progress_report.collect(db, recipient["student_id"])
    report = progress_report.build_report(raw, days=days)
    unsub = link("unsub", recipient["id"])
    filename = re.sub(r"[^A-Za-z0-9]+", "-", report["name"]).strip("-") or "student"
    emailer.send_email(
        recipient["email"], f"{report['name']}'s progress report",
        progress_report.report_html(report, unsub), progress_report.report_text(report, unsub),
        attachments=[(f"{filename}-progress-report.pdf", progress_report.report_pdf(report), "application/pdf")],
    )
    db.table("report_recipients").update({"last_sent_at": _now().isoformat()}).eq("id", recipient["id"]).execute()
    return report


def due_recipients(db, force=False, now=None):
    now = now or _now()
    rows = db.table("report_recipients").select("*").eq("status", "confirmed").execute().data or []
    if force:
        return rows
    due = []
    for r in rows:
        last = _parse(r.get("last_sent_at"))
        gap = timedelta(days=27 if r.get("frequency") == "monthly" else 6)
        if last is None or now - last >= gap:
            due.append(r)
    return due
