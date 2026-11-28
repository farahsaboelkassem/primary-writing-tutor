"""Builds a student's progress report for a parent or teacher.

collect(db, student_id)   reads the student's records from the database
build_report(raw)         turns them into a tidy report: progress, strengths, weak points, how to help
report_html / report_text / report_pdf   the report as an email, plain text or a PDF

What is NOT in a report, on purpose: the child's own writing, and any safeguarding notes. Those
need a proper school or family process, not an automatic email.
"""
import html
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape as xml_escape

from landing_page import NAV_SPELLING, SKILL_KEYS, SKILL_MAX, _streak
from writing_tutor import CATEGORY_LABELS

SECTION_GROUPS = [
    ("Writing (marked pieces)", "marked_item", None),
    ("Grammar & Punctuation", None, "grammar"),
    ("Language Arts", None, "language"),
    ("Spelling & Phonics", None, "spell"),
    ("Reading", None, "reading"),
    ("Vocabulary Vault", None, "vocabulary"),
    ("Game Arena", None, "game arena"),
]

PARENT_TIPS = {
    "Wc": "Before writing, ask your child to tell the story or ideas out loud, with a beginning, middle and end.",
    "Wv": "While reading together, collect interesting words and try swapping tired words (nice, said, big) for stronger ones.",
    "Wg": "Read their writing aloud together and listen for sentences that sound wrong. Practise one grammar rule at a time.",
    "Ws": "Ask them to plan paragraphs first, and to join short sentences using because, although or when.",
    "Ww": "Practise a few tricky words little and often: say the word in chunks, then write it from memory.",
    "lesson": "Revisit this lesson together for 10 minutes, then ask them to explain the rule in their own words.",
    "spelling": "Re-read the rule card together, then do the practice drill again to beat the best score.",
    "practice": "Short, regular sessions (about 10 minutes, 3 or 4 times a week) work better than one long session.",
}


def _when(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def _rows(db, table, student_col, student_id, columns="*", limit=None, order=None):
    try:
        q = db.table(table).select(columns).eq(student_col, student_id)
        if order:
            q = q.order(order, desc=True)
        if limit:
            q = q.limit(limit)
        return q.execute().data or []
    except Exception as exc:
        print(f"[inky] report: could not read {table}: {exc}")
        return []


def collect(db, student_id):
    profile = (_rows(db, "student_profiles", "student_id", student_id) or [{}])[0]
    spelling_titles = {}
    try:
        spelling_titles = {
            r["lesson_id"]: r for r in (db.table("spelling_lessons").select("lesson_id,title,lesson_number").execute().data or [])
        }
    except Exception as exc:
        print(f"[inky] report: could not read spelling lessons: {exc}")
    return {
        "profile": profile,
        "activities": _rows(db, "student_activity_log", "student_id", student_id, limit=500, order="created_at"),
        "history": _rows(db, "student_question_history", "student_id", student_id,
                         "lesson_id,times_seen,times_correct,last_correct"),
        "vocab": _rows(db, "student_vocabulary", "student_id", student_id, limit=500),
        "spelling": _rows(db, "spelling_progress", "user_id", student_id),
        "spelling_titles": spelling_titles,
    }


def _level(pct):
    return "Strong" if pct >= 80 else "Growing" if pct >= 60 else "Needs support"


def build_report(raw, days=7, now=None):
    from lesson_catalog import lesson_index

    now = now or datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    profile = raw.get("profile") or {}
    acts_all = [a for a in raw.get("activities", []) if a.get("activity_type") != "wellbeing_flag"]
    acts = [a for a in acts_all if (_when(a.get("created_at")) or start) >= start]
    active_days = len({_when(a.get("created_at")).date() for a in acts if _when(a.get("created_at"))})

    sections = []
    for label, atype, word in SECTION_GROUPS:
        if atype:
            n = sum(1 for a in acts if a.get("activity_type") == atype)
        else:
            n = sum(1 for a in acts if word in str(a.get("section_name", "")).lower())
        sections.append({"name": label, "count": n})

    marked_all = [a for a in acts_all if a.get("activity_type") == "marked_item"]
    pieces = []
    for a in sorted((a for a in acts if a.get("activity_type") == "marked_item"), key=lambda a: a.get("created_at", "")):
        when = _when(a.get("created_at"))
        pieces.append({
            "date": when.strftime("%d %b") if when else "",
            "title": str(a.get("item_title") or "Piece of writing"),
            "score": str(a.get("score_or_grade") or ""),
        })

    totals = {k: [0, 0] for k in SKILL_KEYS}
    used = 0
    for a in marked_all[:5]:
        d = a.get("details")
        if not isinstance(d, dict) or "wc_score" not in d:
            continue
        used += 1
        for skill, key in SKILL_KEYS.items():
            try:
                totals[skill][0] += int(d.get(key, 0))
            except (TypeError, ValueError):
                pass
            totals[skill][1] += SKILL_MAX[skill]
    skills = []
    if used:
        for skill in SKILL_KEYS:
            pct = int(round(100 * totals[skill][0] / totals[skill][1])) if totals[skill][1] else 0
            skills.append({"code": skill, "label": CATEGORY_LABELS[skill], "pct": pct, "level": _level(pct)})

    scores = []
    for a in reversed(marked_all[:6]):
        d = a.get("details")
        if isinstance(d, dict) and isinstance(d.get("score"), int):
            scores.append(d["score"])
    trend = "steady"
    if len(scores) >= 4:
        half = len(scores) // 2
        diff = sum(scores[half:]) / len(scores[half:]) - sum(scores[:half]) / half
        trend = "improving" if diff >= 1.5 else "dipping" if diff <= -1.5 else "steady"

    index = lesson_index()
    per = {}
    for h in raw.get("history", []):
        lid = h.get("lesson_id")
        if lid in index:
            p = per.setdefault(lid, {"seen": 0, "right": 0})
            p["seen"] += int(h.get("times_seen") or 0)
            p["right"] += int(h.get("times_correct") or 0)

    weak, strengths = [], []
    for s in skills:
        if s["pct"] < 60:
            weak.append({"area": "Writing", "text": f"{s['label']} needs support ({s['pct']}% of the marks available).",
                         "tip": PARENT_TIPS[s["code"]]})
        elif s["pct"] >= 80:
            strengths.append(f"{s['label']} is a real strength in their writing.")
    tricky = sorted(((p["right"] / p["seen"], lid) for lid, p in per.items() if p["seen"] >= 4 and p["right"] / p["seen"] < 0.6))
    for ratio, lid in tricky[:3]:
        info = index[lid]
        weak.append({"area": "Grammar" if info["section_word"] == "grammar" else "Language",
                     "text": f"'{info['title']}' is still tricky ({int(round(ratio * 100))}% of questions correct).",
                     "tip": PARENT_TIPS["lesson"]})
    mastered = 0
    for r in raw.get("spelling", []):
        total = int(r.get("total_questions") or 0)
        if r.get("completed"):
            mastered += 1
        elif total:
            info = raw.get("spelling_titles", {}).get(r.get("lesson_id"), {})
            if len(weak) < 6:
                weak.append({"area": "Spelling", "text": f"'{info.get('title', 'A spelling lesson')}' not yet mastered "
                                                          f"(best {int(r.get('best_score') or 0)}/{total}).",
                             "tip": PARENT_TIPS["spelling"]})
    if mastered:
        strengths.append(f"{mastered} spelling lesson{'s' if mastered != 1 else ''} mastered.")
    if active_days <= 1:
        weak.append({"area": "Practice", "text": f"Practised on {active_days} day this week." if active_days == 1
                     else "No practice recorded this week.", "tip": PARENT_TIPS["practice"]})
    streak = _streak(acts_all)
    if streak >= 3:
        strengths.append(f"A {streak}-day practice streak. Well done!")
    new_words = sum(1 for v in raw.get("vocab", []) if (_when(v.get("updated_at") or v.get("created_at")) or start) >= start)
    if new_words >= 5:
        strengths.append(f"{new_words} new words saved to their word list this week.")
    if trend == "improving":
        strengths.append("Their writing marks are going up.")

    focus, seen_tips = [], set()
    for w in weak:
        if w["tip"] not in seen_tips:
            seen_tips.add(w["tip"])
            focus.append(f"{w['area']}: {w['tip']}")
    return {
        "name": str(profile.get("display_name") or "Your child"),
        "title": str(profile.get("current_title") or ""),
        "xp": int(profile.get("xp_points") or 0),
        "days": days,
        "period": f"{start.strftime('%d %b')} to {now.strftime('%d %b %Y')}",
        "active_days": active_days,
        "activities": len(acts),
        "streak": streak,
        "sections": sections,
        "pieces": pieces,
        "skills": skills,
        "trend": trend,
        "vocab_total": len(raw.get("vocab", [])),
        "vocab_new": new_words,
        "spelling_mastered": mastered,
        "strengths": strengths[:5],
        "weak_points": weak[:6],
        "focus": focus[:3],
    }


# ------------------------------------------------------------------
# Email (HTML + plain text)
# ------------------------------------------------------------------
_PURPLE, _INK, _MUTED, _LINE = "#4a43b0", "#2b2a4a", "#5b5a73", "#e8e4f3"


def _h(text):
    return html.escape(str(text))


def report_html(r, unsubscribe_url=""):
    def rows(items):
        return "".join(f'<tr><td style="padding:6px 10px;border-top:1px solid {_LINE};">{c1}</td>'
                       f'<td style="padding:6px 10px;border-top:1px solid {_LINE};text-align:right;">{c2}</td></tr>'
                       for c1, c2 in items)

    def block(title, inner):
        return (f'<h3 style="font-family:Arial,sans-serif;color:{_PURPLE};margin:22px 0 6px;font-size:17px;">{title}</h3>{inner}')

    parts = [
        f'<div style="font-family:Arial,Helvetica,sans-serif;color:{_INK};max-width:640px;margin:auto;line-height:1.5;">',
        f'<div style="background:{_PURPLE};color:#fff;padding:18px 22px;border-radius:14px;">'
        f'<div style="font-size:22px;font-weight:bold;">{_h(r["name"])}\'s progress report</div>'
        f'<div style="opacity:.9;">{_h(r["period"])}</div></div>',
        f'<p style="margin:14px 0 0;">{_h(r["name"])} practised on <b>{r["active_days"]} day{"s" if r["active_days"] != 1 else ""}</b> '
        f'and completed <b>{r["activities"]} activit{"ies" if r["activities"] != 1 else "y"}</b>'
        + (f' (current streak: {r["streak"]} days)' if r["streak"] >= 2 else "") + ".</p>",
        block("Practice this week", f'<table style="width:100%;border-collapse:collapse;">{rows([(_h(s["name"]), s["count"]) for s in r["sections"]])}</table>'),
    ]
    if r["pieces"]:
        parts.append(block("Writing marked this week", '<table style="width:100%;border-collapse:collapse;">' +
                           rows([(f'{_h(p["date"])} &middot; {_h(p["title"])}', _h(p["score"])) for p in r["pieces"]]) + "</table>"))
    if r["skills"]:
        parts.append(block("Writing skills (last 5 pieces)", '<table style="width:100%;border-collapse:collapse;">' +
                           rows([(_h(s["label"]), f'{_h(s["level"])} ({s["pct"]}%)') for s in r["skills"]]) + "</table>"))
    if r["strengths"]:
        parts.append(block("Going well", "<ul style='margin:0;padding-left:20px;'>" + "".join(f"<li>{_h(s)}</li>" for s in r["strengths"]) + "</ul>"))
    if r["weak_points"]:
        parts.append(block("Areas to practise", "<ul style='margin:0;padding-left:20px;'>" +
                           "".join(f"<li><b>{_h(w['area'])}:</b> {_h(w['text'])}</li>" for w in r["weak_points"]) + "</ul>"))
    if r["focus"]:
        parts.append(block("How you can help at home", "<ul style='margin:0;padding-left:20px;'>" +
                           "".join(f"<li>{_h(f)}</li>" for f in r["focus"]) + "</ul>"))
    foot = ("This report comes from The Writing Adventure. It shows progress and practice areas only. "
            "It does not include your child's writing.")
    if unsubscribe_url:
        foot += f' <a href="{_h(unsubscribe_url)}" style="color:{_MUTED};">Stop these emails</a>.'
    parts.append(f'<p style="color:{_MUTED};font-size:12px;margin-top:26px;">{foot}</p></div>')
    return "".join(parts)


def report_text(r, unsubscribe_url=""):
    lines = [f"{r['name']}'s progress report ({r['period']})", "",
             f"Practised on {r['active_days']} day(s); {r['activities']} activities completed."]
    lines += ["", "PRACTICE THIS WEEK"] + [f"- {s['name']}: {s['count']}" for s in r["sections"]]
    if r["pieces"]:
        lines += ["", "WRITING MARKED"] + [f"- {p['date']} {p['title']}: {p['score']}" for p in r["pieces"]]
    if r["skills"]:
        lines += ["", "WRITING SKILLS"] + [f"- {s['label']}: {s['level']} ({s['pct']}%)" for s in r["skills"]]
    if r["strengths"]:
        lines += ["", "GOING WELL"] + [f"- {s}" for s in r["strengths"]]
    if r["weak_points"]:
        lines += ["", "AREAS TO PRACTISE"] + [f"- {w['area']}: {w['text']}" for w in r["weak_points"]]
    if r["focus"]:
        lines += ["", "HOW YOU CAN HELP AT HOME"] + [f"- {f}" for f in r["focus"]]
    lines += ["", "From The Writing Adventure. Progress and practice areas only; no writing is included."]
    if unsubscribe_url:
        lines.append(f"Stop these emails: {unsubscribe_url}")
    return "\n".join(lines)


# ------------------------------------------------------------------
# PDF
# ------------------------------------------------------------------
def report_pdf(r):
    """The report as PDF bytes. Plain text only (no emoji), so it prints cleanly anywhere."""
    from io import BytesIO

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    base = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=base["BodyText"], fontSize=10, leading=14, textColor=colors.HexColor(_INK))
    h1 = ParagraphStyle("h1", parent=base["Title"], fontSize=20, textColor=colors.HexColor(_PURPLE), alignment=0, spaceAfter=2)
    h2 = ParagraphStyle("h2", parent=base["Heading2"], fontSize=13, textColor=colors.HexColor(_PURPLE), spaceBefore=12, spaceAfter=4)
    small = ParagraphStyle("small", parent=body, fontSize=8.5, textColor=colors.HexColor(_MUTED))

    def P(text, style=body):
        return Paragraph(xml_escape(str(text)), style)

    def table(data, widths, header=True):
        t = Table([[P(c) if not hasattr(c, "wrap") else c for c in row] for row in data], colWidths=widths, repeatRows=1 if header else 0)
        style = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(_LINE)), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                 ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
        if header:
            style.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#efe9ff")))
        t.setStyle(TableStyle(style))
        return t

    story = [P(f"{r['name']}'s progress report", h1), P(f"{r['period']}   |   {r['title']}   |   {r['xp']} XP", small), Spacer(1, 6)]
    story.append(P(f"{r['name']} practised on {r['active_days']} day(s) and completed {r['activities']} activities."
                   + (f" Current streak: {r['streak']} days." if r["streak"] >= 2 else "")))
    story += [P("Practice this week", h2), table([["Section", "Activities"]] + [[s["name"], s["count"]] for s in r["sections"]], [110 * mm, 40 * mm])]
    if r["pieces"]:
        story += [P("Writing marked this week", h2),
                  table([["Date", "Piece", "Mark"]] + [[p["date"], p["title"], p["score"]] for p in r["pieces"]], [25 * mm, 100 * mm, 25 * mm])]
    if r["skills"]:
        story += [P("Writing skills (last 5 pieces)", h2),
                  table([["Skill", "Level", "Share of marks"]] + [[s["label"], s["level"], f"{s['pct']}%"] for s in r["skills"]], [80 * mm, 40 * mm, 30 * mm])]
    if r["strengths"]:
        story += [P("Going well", h2)] + [P(f"- {s}") for s in r["strengths"]]
    if r["weak_points"]:
        story += [P("Areas to practise", h2),
                  table([["Area", "What we noticed", "How to help"]] + [[w["area"], w["text"], w["tip"]] for w in r["weak_points"]],
                        [24 * mm, 63 * mm, 63 * mm])]
    story += [Spacer(1, 14), P("From The Writing Adventure. This report shows progress and practice areas only. "
                               "It does not include your child's writing.", small)]
    buffer = BytesIO()
    SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
                      title=f"{r['name']} progress report").build(story)
    return buffer.getvalue()
