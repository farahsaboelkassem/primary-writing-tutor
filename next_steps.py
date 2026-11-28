"""Marking Arena: "Let's fix these" and "Your next steps".

After a piece is marked, the marker names up to 3 real mistakes (checked against the child's own
words) and picks up to 3 lessons from the app's lesson list. Each lesson can be opened straight
away or added to the child's Home to-do list. If the marker's picks are unusable, a lesson is
suggested from the child's weakest writing skill instead, so there is always a sensible next step.
"""
import html

import streamlit as st

import todo_store
from landing_page import SKILL_MAX, SKILL_TIPS, go_to

NEXT_STEPS_CSS = """
<style>
[class*="st-key-nstep_"] { background:#fffdf7; border:2px solid #efe3bd; border-left:8px solid var(--accent, #6b63d9);
  border-radius:16px; padding:.45rem .9rem; margin-bottom:.45rem; box-shadow:0 4px 14px rgba(0,0,0,.1); }
.ns-title { font-family:'Fredoka','Baloo 2',sans-serif; font-weight:700; font-size:1.08rem; color:#2b2a4a; }
.ns-why { color:#5b5a73; font-size:.93rem; line-height:1.35; }
.ns-fix { width:100%; border-collapse:collapse; background:#fffdf7; border-radius:14px; overflow:hidden; box-shadow:0 4px 14px rgba(0,0,0,.1); }
.ns-fix th { background:#efe9ff; color:#3d3499; text-align:left; padding:.45rem .7rem; font-size:.82rem; letter-spacing:.04em; text-transform:uppercase; }
.ns-fix td { padding:.45rem .7rem; color:#2b2a4a; border-top:1px solid #efe3bd; font-size:.98rem; }
.ns-wrote { color:#b3261e; text-decoration:line-through; }
.ns-better { color:#1e7a46; font-weight:800; }
</style>
"""

ICONS = {"grammar": "✏️", "language": "🎭", "spell": "🐝", "vocabulary": "💎"}


def _step(lesson_id, info):
    """One suggestion in the same shape the Home page's to-do items use."""
    if info.get("sp"):
        key = f"spelling_{info['lesson']}"
    elif lesson_id == "vault":
        key = "vault_practise"
    else:
        key = f"lesson_{info['lesson']}"
    deep = None
    if info.get("sp"):
        deep = {"sp": True, "lesson": info["lesson"], "band": info["band"]}
    elif info.get("prefix"):
        deep = {k: info[k] for k in ("prefix", "level", "topic", "lesson")}
    word = info.get("section_word") or ""
    return {
        "key": key, "nav": info["nav"], "icon": ICONS.get(word, "📘"),
        "title": f"Practise: {info['title']}" if lesson_id != "vault" else info["title"],
        "why": "Chosen because of what Inky spotted in your writing.",
        "deep": deep, "match_title": info.get("match_title"), "section_word": word,
    }


def build_next_steps(result, cat_index, writing_text):
    """Returns (steps, fixes). Both are checked against real lessons and the child's real words."""
    raw = result.get("next_lessons") or []
    if isinstance(raw, str):
        raw = [p for p in raw.replace(";", ",").split(",")]
    steps, seen = [], set()
    for lesson_id in raw[:8]:
        lesson_id = str(lesson_id).strip()
        info = cat_index.get(lesson_id)
        if not info:
            continue
        step = _step(lesson_id, info)
        if step["key"] not in seen:
            seen.add(step["key"])
            steps.append(step)
        if len(steps) == 3:
            break

    scores = result.get("scores") or {}
    if not steps and scores:
        ratios = {k: scores.get(k, 0) / SKILL_MAX[k] for k in SKILL_MAX if k in scores}
        if ratios:
            skill = min(ratios, key=ratios.get)
            if ratios[skill] < 0.75:
                nav, icon, title, why = SKILL_TIPS[skill]
                steps.append({"key": f"skill_{skill}", "nav": nav, "icon": icon, "title": title, "why": why,
                              "deep": None, "match_title": None, "section_word": ""})

    fixes = []
    raw_text = str(writing_text or "")
    text = raw_text.lower()
    for f in (result.get("fixes") or [])[:3]:
        if not isinstance(f, dict):
            continue
        wrote = " ".join(str(f.get("wrote", "")).split())[:60]
        better = " ".join(str(f.get("better", "")).split())[:60]
        why = " ".join(str(f.get("why", "")).split())[:90]
        if wrote and better and wrote != better and (wrote in raw_text or wrote.lower() in text):   # capital-letter fixes count
            fixes.append({"wrote": wrote, "better": better, "why": why})
    return steps, fixes


def _added_keys(db, student_id):
    keys = st.session_state.get("_todo_keys")
    if keys is None:
        keys = {i["item_key"] for i in todo_store.load_items(db, student_id)}
        st.session_state["_todo_keys"] = keys
    return keys


def _add(db, student_id, step):
    todo_store.add_item(db, student_id, step)
    keys = st.session_state.get("_todo_keys")
    if keys is not None:
        keys.add(step["key"])
    st.session_state.pop("_home_cache", None)


def render_next_steps(res, student_id, db):
    steps = res.get("next_steps") or []
    fixes = res.get("fixes") or []
    if not steps and not fixes:
        return
    st.markdown(NEXT_STEPS_CSS, unsafe_allow_html=True)

    if fixes:
        st.markdown("### 🔧 Let's fix these")
        rows = "".join(
            f'<tr><td><span class="ns-wrote">{html.escape(f["wrote"])}</span></td>'
            f'<td><span class="ns-better">{html.escape(f["better"])}</span></td><td>{html.escape(f["why"])}</td></tr>'
            for f in fixes
        )
        st.markdown(
            f'<table class="ns-fix"><tr><th>You wrote</th><th>Try this</th><th>Why</th></tr>{rows}</table>',
            unsafe_allow_html=True,
        )

    if steps:
        st.markdown("### 🚀 Your next steps")
        st.caption("Open a lesson now, or add it to your To-Do list on the Home page for later.")
        added = _added_keys(db, student_id)
        for n, step in enumerate(steps):
            with st.container(key=f"nstep_{n}"):
                c1, c2, c3 = st.columns([4, 2, 1.6], vertical_alignment="center")
                c1.markdown(
                    f'<div class="ns-title">{step["icon"]} {html.escape(step["title"])}</div>'
                    f'<div class="ns-why">{html.escape(step["why"])}</div>',
                    unsafe_allow_html=True,
                )
                if step["key"] in added:
                    c2.markdown("✅ On your To-Do list")
                else:
                    c2.button("➕ Add to my To-Do list", key=f"nstep_add_{n}", use_container_width=True,
                              on_click=_add, args=(db, student_id, step))
                c3.button("▶ Go now", key=f"nstep_go_{n}", use_container_width=True, type="primary",
                          on_click=go_to, args=(step["nav"], step["deep"]))
