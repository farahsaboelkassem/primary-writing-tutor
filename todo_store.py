"""The student's own to-do items (lessons added from the Marking Arena).

Stored in the student_todo table. If the table is missing or the database is down, items are
kept in the session instead (and saved with the child's drafts), so the button still works.
"""
import json
from datetime import datetime, timedelta, timezone

import streamlit as st

KEEP_DAYS = 21


def _now():
    return datetime.now(timezone.utc)


def _clean(item):
    return {
        "item_key": str(item["key"]), "nav": item["nav"], "title": item["title"], "why": item.get("why", ""),
        "deep": item.get("deep"), "match_title": item.get("match_title"), "section_word": item.get("section_word"),
        "source": item.get("source", "marking"),
    }


def add_item(db, student_id, item):
    """Add (or re-open) an item. Returns True if it was saved somewhere."""
    row = _clean(item)
    if db is not None and student_id:
        try:
            db.table("student_todo").upsert(
                {**row, "student_id": student_id, "status": "open", "created_at": _now().isoformat(), "done_at": None},
                on_conflict="student_id,item_key",
            ).execute()
            return True
        except Exception as exc:
            print(f"[inky] todo: could not save to the database, keeping it for this visit: {exc}")
    items = [i for i in st.session_state.get("todo_items", []) if i.get("item_key") != row["item_key"]]
    items.append({**row, "status": "open", "created_at": _now().isoformat()})
    st.session_state["todo_items"] = items
    return True


def load_items(db, student_id):
    """Open items that are not too old."""
    rows = []
    if db is not None and student_id:
        try:
            rows = (
                db.table("student_todo").select("*").eq("student_id", student_id).eq("status", "open")
                .order("created_at", desc=True).execute().data or []
            )
        except Exception as exc:
            print(f"[inky] todo: could not read the database: {exc}")
    have = {r["item_key"] for r in rows}
    rows += [i for i in st.session_state.get("todo_items", []) if i["item_key"] not in have and i.get("status") == "open"]
    cutoff = (_now() - timedelta(days=KEEP_DAYS)).isoformat()
    out = []
    for r in rows:
        if str(r.get("created_at", "")) >= cutoff:
            deep = r.get("deep")
            if isinstance(deep, str):
                try:
                    deep = json.loads(deep)
                except Exception:
                    deep = None
            out.append({**r, "deep": deep})
    return out


def set_status(db, student_id, item_key, status):
    """status: 'done' or 'removed'."""
    if db is not None and student_id:
        try:
            db.table("student_todo").update(
                {"status": status, "done_at": _now().isoformat() if status == "done" else None}
            ).eq("student_id", student_id).eq("item_key", item_key).execute()
        except Exception as exc:
            print(f"[inky] todo: could not update the database: {exc}")
    st.session_state["todo_items"] = [
        i for i in st.session_state.get("todo_items", []) if i.get("item_key") != item_key
    ]


def done_after(item, activities):
    """The time the student completed this item's lesson (after it was added), or None."""
    created = str(item.get("created_at", ""))
    word = str(item.get("section_word") or "").lower()
    title = str(item.get("match_title") or "").lower()
    for a in activities:
        if str(a.get("created_at", "")) <= created:
            continue
        if word and word not in str(a.get("section_name", "")).lower():
            continue
        if title and title not in str(a.get("item_title", "")).lower() and str(a.get("item_title", "")).lower() not in title:
            continue
        if a.get("activity_type") in ("quiz", "lesson", "reading_practice"):
            return a.get("created_at")
    return None
