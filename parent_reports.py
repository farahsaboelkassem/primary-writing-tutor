"""The "Parent & teacher reports" screen (inside Progress & Badges) and the confirm / stop links."""
import html

import streamlit as st

import emailer
import progress_report
import report_delivery

STATUS_TEXT = {
    "pending": "⏳ Waiting for them to confirm",
    "confirmed": "✅ Receiving reports",
    "unsubscribed": "⛔ Stopped",
}


def handle_report_links(db):
    """If the page was opened from a confirm or stop link in an email, handle it. Returns True if so."""
    params = st.query_params
    for action in ("confirm", "unsub"):
        token = params.get(action)
        if token:
            ok, message = report_delivery.confirm_or_unsub(db, action, str(token))
            st.markdown("## 📬 The Writing Adventure")
            (st.success if ok else st.error)(message)
            st.caption("You can close this page now.")
            return True
    return False


def _prepare_pdf(db, student_id):
    raw = progress_report.collect(db, student_id)
    st.session_state["_report_pdf"] = progress_report.report_pdf(progress_report.build_report(raw, days=7))
    st.session_state["_report_name"] = str(raw["profile"].get("display_name") or "student")


def _send_now(db, recipient):
    try:
        report_delivery.send_report_to(db, recipient)
        st.session_state["_reports_msg"] = ("ok", f"A report was sent to {recipient['email']}.")
    except Exception as exc:
        print(f"[inky] reports: could not send now: {exc}")
        st.session_state["_reports_msg"] = ("err", "The report could not be sent just now. Please try again later.")


def _remove(db, student_id, recipient_id):
    report_delivery.remove_recipient(db, student_id, recipient_id)
    st.session_state["_reports_msg"] = ("ok", "Removed.")


def render_parent_reports(db, profile):
    student_id = profile["student_id"]
    name = html.escape(str(profile.get("display_name") or "your child"))
    st.markdown("### 👪 Parent & teacher reports")
    with st.expander("Share progress with a parent or teacher", expanded=False):
        st.write(
            f"A report shows what {name} has practised, strengths and the areas to work on, with simple tips for helping. "
            "It never includes their writing. The grown-up must press a confirm button in an email before any report is sent."
        )
        msg = st.session_state.pop("_reports_msg", None)
        if msg:
            (st.success if msg[0] == "ok" else st.error)(msg[1])

        recipients = report_delivery.list_recipients(db, student_id) if db is not None else []
        for r in recipients:
            with st.container(border=True):
                c1, c2, c3 = st.columns([4, 2, 2], vertical_alignment="center")
                who = html.escape(r.get("recipient_name") or r.get("email"))
                c1.markdown(f"**{who}** ({html.escape(str(r.get('role', 'parent')))})  \n{html.escape(r.get('email', ''))}")
                c2.caption(STATUS_TEXT.get(r.get("status"), r.get("status", "")))
                with c3:
                    if r.get("status") == "confirmed":
                        st.button("Send a report now", key=f"rep_now_{r['id']}", use_container_width=True,
                                  on_click=_send_now, args=(db, r))
                    st.button("Remove", key=f"rep_rm_{r['id']}", use_container_width=True,
                              on_click=_remove, args=(db, student_id, r["id"]))

        if not emailer.email_ready():
            st.info("Emailing is not switched on yet, so reports can't be sent. You can still download this week's report below.")
        else:
            with st.form("add_report_recipient", clear_on_submit=True):
                st.markdown("**Add a parent or teacher**")
                a, b = st.columns(2)
                rname = a.text_input("Their name")
                role = b.selectbox("They are a", ["parent", "teacher"])
                email = st.text_input("Their email address")
                agreed = st.checkbox("A grown-up (parent, carer or teacher) is filling this in and agrees to receive reports.")
                if st.form_submit_button("Send the confirmation email", use_container_width=True):
                    if not agreed:
                        st.warning("Please tick the box first. A grown-up needs to agree.")
                    else:
                        ok, text = report_delivery.request_recipient(
                            db, student_id, str(profile.get("display_name") or "Your child"), email, rname, role)
                        (st.success if ok else st.warning)(text)

        st.markdown("---")
        st.markdown("**Download a report**")
        st.caption("A PDF of this week's progress that you can print or share yourself.")
        if db is None:
            st.caption("Reports need a saved-progress connection, which isn't available right now.")
        else:
            st.button("Prepare this week's report", key="rep_prepare", on_click=_prepare_pdf, args=(db, student_id))
            if st.session_state.get("_report_pdf"):
                st.download_button(
                    "📄 Download the report (PDF)", data=st.session_state["_report_pdf"],
                    file_name="progress-report.pdf", mime="application/pdf", key="rep_download",
                )
