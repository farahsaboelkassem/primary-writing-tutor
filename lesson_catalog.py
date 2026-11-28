"""A list of every lesson the app can recommend, in one place.

Used by the Marking Arena (to let the marker pick lessons that match a child's mistakes, and to
check its answer against real lessons) and by the Home page and reports.

Each entry has the shape the Home page's buttons already understand, so "Go now" opens the
actual lesson. Lesson ids are:
    k1_noun, k2_commas ...     grammar and language lessons (from grammar_lessons / language_lessons)
    sp:<lesson_id>             a spelling lesson (read from Supabase)
    vault                      vocabulary practice in the Vocabulary Vault
"""
import time

import streamlit as st

from landing_page import NAV_GRAMMAR, NAV_LANGUAGE, NAV_SPELLING, NAV_VAULT

_INDEX = {}


def lesson_index():
    """Grammar and language lessons: id -> where each one lives."""
    if _INDEX:
        return _INDEX
    for module_name, nav, prefix, word in (
        ("grammar_lessons", NAV_GRAMMAR, "gr", "grammar"),
        ("language_lessons", NAV_LANGUAGE, "la", "language"),
    ):
        try:
            module = __import__(module_name)
        except Exception:
            continue
        for level_key, level in module.LEVELS.items():
            topic_of = {}
            for topic in level.get("topics") or []:
                for lesson in topic["lessons"]:
                    topic_of[lesson["id"]] = topic["id"]
            for lesson in level["lessons"]:
                _INDEX[lesson["id"]] = {
                    "nav": nav, "prefix": prefix, "level": level_key, "topic": topic_of.get(lesson["id"]),
                    "lesson": lesson["id"], "title": lesson["title"],
                    "match_title": lesson["title"], "section_word": word,
                }
    return _INDEX


def spelling_lessons(db, band):
    """Spelling lessons for a track, cached for ten minutes."""
    key = f"_sp_catalog_{band}"
    cached = st.session_state.get(key)
    if cached and time.time() - cached["t"] < 600:
        return cached["rows"]
    rows = []
    if db is not None:
        try:
            rows = (
                db.table("spelling_lessons").select("lesson_id,title,lesson_number,grade_band")
                .eq("grade_band", band).order("sort_order").execute().data or []
            )
        except Exception as exc:
            print(f"[inky] catalog: could not read spelling lessons: {exc}")
    st.session_state[key] = {"t": time.time(), "rows": rows}
    return rows


def catalog_for(age_band, db=None):
    """Returns (text for the marking prompt, {id: info}) for this child's stage."""
    band = "lower" if str(age_band).startswith("Lower") else "upper"
    entries, lines = {}, []
    for lid, info in lesson_index().items():
        if info["level"] == band:
            entries[lid] = info
            lines.append(f"{lid}={info['title']}")
    for row in spelling_lessons(db, band):
        key = f"sp:{row['lesson_id']}"
        title = f"Lesson {row.get('lesson_number')}: {row.get('title')}"
        entries[key] = {
            "nav": NAV_SPELLING, "sp": True, "lesson": row["lesson_id"], "band": band, "title": title,
            "match_title": str(row.get("title") or ""), "section_word": "spell",
        }
        lines.append(f"{key}=Spelling: {row.get('title')}")
    entries["vault"] = {
        "nav": NAV_VAULT, "title": "Collect and practise new words", "match_title": None, "section_word": "vocabulary",
    }
    lines.append("vault=Vocabulary Vault word practice (for weak or repeated word choices)")
    return "\n".join(lines), entries
