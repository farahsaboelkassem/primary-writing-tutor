"""Question bank for The Writing Adventure.

Lessons keep their own built-in questions (in grammar_lessons.py and language_lessons.py).
This module adds a Supabase question bank on top:

  * bank_questions(lesson)         -> a fresh set of questions for one practice run
  * bank_record(lesson, answers)   -> remembers what the student has now seen and got right

How a run is chosen
-------------------
1. Active questions for the lesson are read from the question_bank table (cached for 5 minutes,
   so a change you publish shows up within a few minutes).
2. If the bank has fewer questions than a run needs, the lesson's built-in questions top it up.
3. Questions this student has NOT seen come first, then ones they got wrong last time, then
   the ones they have seen least recently. Different question styles are mixed.
4. If anything goes wrong (no connection, empty bank) the app quietly uses the built-in
   questions instead, so a lesson never breaks.
"""
import random
from datetime import datetime, timezone

import streamlit as st

RUN_SIZE = 7
CACHE_SECONDS = 300
QUESTION_TYPES = ("multiple_choice", "true_false", "fill_blank")


def _client():
    from auth_progress import get_supabase_client  # imported here so tests can replace _client
    return get_supabase_client()


def _student_id():
    profile = st.session_state.get("student_profile") or {}
    return profile.get("student_id")


# ------------------------------------------------------------------
# Reading the bank
# ------------------------------------------------------------------
@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def _fetch_bank_rows(lesson_id):
    res = (
        _client().table("question_bank")
        .select("*")
        .eq("lesson_id", lesson_id)
        .eq("active", True)
        .execute()
    )
    return res.data or []


def row_to_question(row):
    """Turn one question_bank row into the question format the lesson screens use.
    Returns None if the row is not usable (the app skips it rather than crashing)."""
    try:
        qtype = (row.get("question_type") or "multiple_choice").strip()
        text = str(row.get("question") or "").strip()
        correct = str(row.get("correct_answer") or "").strip()
        if qtype not in QUESTION_TYPES or not text or not correct or not row.get("question_code"):
            return None
        q = {
            "code": str(row["question_code"]).strip(),
            "type": qtype,
            "kind": row.get("skill_kind") if row.get("skill_kind") in ("spot", "use") else "use",
            "q": text,
            "why": str(row.get("explanation") or "").strip(),
            "difficulty": int(row.get("difficulty") or 1),
            "case_sensitive": bool(row.get("case_sensitive")),
        }
        if qtype == "fill_blank":
            accepted = [correct] + [str(a).strip() for a in (row.get("accepted_answers") or []) if str(a).strip()]
            q.update(correct=correct, options=[], accepted=accepted)
        elif qtype == "true_false":
            q.update(correct="True" if correct.lower() == "true" else "False", options=["True", "False"])
        else:
            wrong = [str(w).strip() for w in (row.get("wrong_answers") or []) if str(w).strip() and str(w).strip() != correct]
            options = [correct] + list(dict.fromkeys(wrong))  # correct answer first; the screen shuffles
            if len(options) < 2:
                return None
            q.update(correct=correct, options=options)
        return q
    except Exception:
        return None


def builtin_questions(lesson):
    """The lesson's own questions in the same format. Codes match the seed CSV (lesson_id-01, -02 ...)."""
    out = []
    for i, q in enumerate(lesson.get("questions", []), start=1):
        out.append({
            "code": f"{lesson['id']}-{i:02d}", "type": "multiple_choice", "kind": q["kind"], "q": q["q"],
            "correct": q["options"][0], "options": list(q["options"]), "why": q["why"],
            "difficulty": 1, "case_sensitive": False,
        })
    return out


# ------------------------------------------------------------------
# What the student has already seen
# ------------------------------------------------------------------
def _fetch_history(student_id, lesson_id):
    res = (
        _client().table("student_question_history")
        .select("*")
        .eq("student_id", student_id)
        .eq("lesson_id", lesson_id)
        .execute()
    )
    return {r["question_code"]: r for r in (res.data or [])}


def _tier(history_row):
    if not history_row:
        return 0                      # never seen
    if history_row.get("last_correct") is False:
        return 1                      # got it wrong last time
    return 2                          # seen and got it right


def _priority(history_row, rng):
    h = history_row or {}
    return (_tier(history_row), int(h.get("times_seen") or 0), str(h.get("last_seen") or ""), rng.random())


def pick_questions(candidates, history, n=RUN_SIZE, rng=random):
    """Choose n questions: unseen first, then missed, then least recently seen, mixing styles."""
    by_type = {}
    for q in candidates:
        by_type.setdefault(q["type"], []).append(q)
    for group in by_type.values():
        group.sort(key=lambda q: _priority(history.get(q["code"]), rng))

    chosen = []
    # Round 1: take fresh questions (never seen, or missed last time) from each style in turn.
    types = list(by_type)
    rng.shuffle(types)
    progress = True
    while len(chosen) < n and progress:
        progress = False
        for t in types:
            group = by_type[t]
            if group and _tier(history.get(group[0]["code"])) <= 1 and len(chosen) < n:
                chosen.append(group.pop(0))
                progress = True
    # Round 2: if more are needed, use the best of what is left, whatever the style.
    leftovers = sorted((q for g in by_type.values() for q in g), key=lambda q: _priority(history.get(q["code"]), rng))
    chosen += leftovers[: max(0, n - len(chosen))]
    rng.shuffle(chosen)
    return chosen


# ------------------------------------------------------------------
# What the lesson screens call
# ------------------------------------------------------------------
def bank_questions(lesson, n=RUN_SIZE):
    """A fresh set of questions for one practice run, or None to use the lesson's built-ins."""
    try:
        rows = _fetch_bank_rows(lesson["id"])
        pool = [q for q in (row_to_question(r) for r in rows) if q]
        if not pool:
            return None
        if len(pool) < n:  # top up with built-ins that are not already in the bank
            have = {q["q"].strip().lower() for q in pool}
            pool += [q for q in builtin_questions(lesson) if q["q"].strip().lower() not in have]
        history = {}
        sid = _student_id()
        if sid:
            try:
                history = _fetch_history(sid, lesson["id"])
            except Exception as exc:
                print(f"[inky] could not read question history: {exc}")
        return pick_questions(pool, history, n)
    except Exception as exc:
        print(f"[inky] question bank unavailable, using built-in questions: {exc}")
        return None


def bank_record(lesson, answers):
    """Remember which questions the student has now seen and whether they got them right."""
    sid = _student_id()
    if not sid:
        return False
    try:
        history = _fetch_history(sid, lesson["id"])
        now = datetime.now(timezone.utc).isoformat()
        rows, done = [], set()
        for a in answers:
            code = a.get("code")
            if not code or code in done:
                continue
            done.add(code)
            h = history.get(code) or {}
            rows.append({
                "student_id": sid,
                "question_code": code,
                "lesson_id": lesson["id"],
                "times_seen": int(h.get("times_seen") or 0) + 1,
                "times_correct": int(h.get("times_correct") or 0) + (1 if a.get("correct") else 0),
                "last_correct": bool(a.get("correct")),
                "last_seen": now,
            })
        if rows:
            _client().table("student_question_history").upsert(rows, on_conflict="student_id,question_code").execute()
        return True
    except Exception as exc:
        print(f"[inky] could not save question history: {exc}")
        return False
