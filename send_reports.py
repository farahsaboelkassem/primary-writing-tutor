"""Send the weekly progress reports. Run it on a schedule (see .github/workflows/weekly_reports.yml).

    python send_reports.py              send every report that is due (weekly: every 6+ days)
    python send_reports.py --dry-run    show who would get one, send nothing
    python send_reports.py --force      send to everyone confirmed, even if one went recently

Needs these environment variables: SUPABASE_URL, SUPABASE_SERVICE_KEY, SMTP_HOST, SMTP_PORT,
SMTP_USER, SMTP_PASSWORD, SMTP_FROM, APP_URL (and optionally REPORT_LINK_SECRET).
"""
import argparse
import os
import sys

from supabase import create_client

import emailer
import report_delivery


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not emailer.email_ready():
        print("Email is not set up (check SMTP_* and APP_URL). Nothing sent.")
        return 1
    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
    due = report_delivery.due_recipients(db, force=args.force)
    print(f"{len(due)} report(s) due.")
    sent = failed = 0
    for recipient in due:
        label = f"{recipient['email']} (student {recipient['student_id']})"
        if args.dry_run:
            print(f"  would send to {label}")
            continue
        try:
            report_delivery.send_report_to(db, recipient)
            sent += 1
            print(f"  sent to {label}")
        except Exception as exc:          # one bad address must not stop the rest
            failed += 1
            print(f"  FAILED for {label}: {exc}")
    print(f"Done. Sent {sent}, failed {failed}.")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
