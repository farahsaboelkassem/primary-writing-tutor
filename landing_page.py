"""The Home screen: tells each child where to go and what to do next.

  * A friendly hello using the student's name.
  * "Your To-Do List": a few tasks chosen from the student's own progress. Weak spots come from
    their marked writing (the lowest skill) and from lesson questions they keep getting wrong.
    Tasks tick off for the day once the student has done something in that section.
  * A map of every section, including Spelling & Phonics, each with a Go button.

Nothing here calls the writing helper, so it costs no requests. If the database is unreachable
the page still works with sensible starter tasks.

The section names below are also used by app.py for the sidebar menu, so the two always match.
"""
import html
import re
import time
from datetime import datetime, timedelta, timezone

import streamlit as st

# ------------------------------------------------------------------
# Section names (the sidebar menu uses these too)
# ------------------------------------------------------------------
NAV_HOME = "🏠 Home"
NAV_DOJO = "🥋 The Writing Dojo"
NAV_ARENA = "🏟️ Marking Arena"
NAV_READING = "📖 Reading"
NAV_VAULT = "📚 Vocabulary Vault"
NAV_GRAMMAR = "✏️ Grammar & Punctuation"
NAV_LANGUAGE = "🎭 Language Arts"
NAV_SPELLING = "🐝 Spelling & Phonics"
NAV_GAMES = "🎮 Game Arena"
NAV_PROGRESS = "🏆 Progress & Badges"

NAV_OPTIONS = [
    NAV_HOME, NAV_DOJO, NAV_ARENA, NAV_READING, NAV_VAULT,
    NAV_GRAMMAR, NAV_LANGUAGE, NAV_SPELLING, NAV_GAMES, NAV_PROGRESS,
]

# Words found in the activity log's section_name for each section.
SECTION_WORD = {
    NAV_ARENA: "marking arena", NAV_READING: "reading", NAV_VAULT: "vocabulary",
    NAV_GRAMMAR: "grammar", NAV_LANGUAGE: "language", NAV_SPELLING: "spell",
}

TILES = [
    (NAV_DOJO, "🥋", "The Writing Dojo", "Build a story or text, one step at a time."),
    (NAV_ARENA, "🏟️", "Marking Arena", "Get feedback on your writing and watch your skills grow."),
    (NAV_READING, "📖", "Reading", "Read short passages and answer questions."),
    (NAV_VAULT, "📚", "Vocabulary Vault", "Collect new words and play word games."),
    (NAV_GRAMMAR, "✏️", "Grammar & Punctuation", "Practise sentences, nouns, verbs and punctuation."),
    (NAV_LANGUAGE, "🎭", "Language Arts", "Explore word meanings, synonyms, prefixes and more."),
    (NAV_SPELLING, "🐝", "Spelling & Phonics", "Learn spelling rules and phonics, then buzz through a practice drill."),
    (NAV_GAMES, "🎮", "Game Arena", "Play learning games and win bonus XP."),
    (NAV_PROGRESS, "🏆", "Progress & Badges", "See your badges and how far you have come."),
]

# Writing skill -> where to practise it, in words a child understands.
SKILL_TIPS = {
    "Wc": (NAV_DOJO, "✨", "Grow your ideas", "Build your next piece step by step and add exciting details."),
    "Wv": (NAV_VAULT, "🎨", "Power up your words", "Collect new words and phrases to make your writing sparkle."),
    "Wg": (NAV_GRAMMAR, "✏️", "Sharpen your grammar and punctuation", "A few quick lessons will help your sentences shine."),
    "Ws": (NAV_DOJO, "🧱", "Strengthen how your writing is built", "Practise how paragraphs and ideas fit together."),
    "Ww": (NAV_SPELLING, "🐝", "Work on spelling patterns", "Learn a spelling rule, then try the practice drill."),
}
SKILL_KEYS = {"Wc": "wc_score", "Wv": "wv_score", "Wg": "wg_score", "Ws": "ws_score", "Ww": "ww_score"}
SKILL_MAX = {"Wc": 5, "Wv": 3, "Wg": 7, "Ws": 7, "Ww": 3}

HOME_UNIVERSE_CSS = """
:root { --accent:#1b8f84; --accent-light:#28a79a; --accent-dark:#136b63; --accent-soft:#e0f6f2; --hero-a:#1b8f84; --hero-b:#6b63d9; }
.stApp { background: linear-gradient(180deg, #2a5fb0 0%, #4aa8dc 42%, #9ee3cf 78%, #fff1bf 100%) !important; }
.stApp::before {
  background:
    radial-gradient(circle at 92% 11%, #fff6d4 0 34px, rgba(255,246,212,.35) 35px 64px, rgba(255,246,212,.1) 65px 112px, transparent 113px),
    radial-gradient(60px 22px at 14% 16%, rgba(255,255,255,.55) 0 60%, transparent 100%),
    radial-gradient(80px 26px at 46% 9%, rgba(255,255,255,.45) 0 60%, transparent 100%),
    radial-gradient(70px 24px at 72% 20%, rgba(255,255,255,.5) 0 60%, transparent 100%);
}
.stApp::after {
  height: 30vh;
  background:
    radial-gradient(70% 90% at 10% 112%, #58c58f 0 98%, transparent 100%),
    radial-gradient(80% 80% at 60% 114%, #3fb27c 0 98%, transparent 100%),
    radial-gradient(60% 70% at 100% 110%, #6bd09f 0 98%, transparent 100%);
}
"""

HOME_CSS = """
<style>
.home-hero { display:flex; align-items:center; gap:1rem; background:linear-gradient(135deg,#3d3499,#1b8f84); color:#fff;
  border-radius:22px; padding:1rem 1.3rem; box-shadow:0 10px 26px rgba(20,30,80,.28); margin-bottom:1rem; }
.home-owl { width:72px; height:72px; flex:none; display:grid; place-items:center; font-size:2.4rem; border-radius:50%;
  background:rgba(255,255,255,.18); border:3px solid rgba(255,255,255,.7); }
.home-hi { font-family:'Fredoka','Baloo 2',sans-serif; font-weight:700; font-size:clamp(1.5rem,4vw,2.1rem); line-height:1.1; }
.home-sub { opacity:.95; font-size:1.02rem; margin-top:.2rem; }
.home-chips { display:flex; flex-wrap:wrap; gap:.4rem; margin-top:.5rem; }
.home-chip { background:rgba(255,255,255,.2); border-radius:999px; padding:.12rem .7rem; font-size:.88rem; font-weight:700; }
.home-h { font-family:'Fredoka','Baloo 2',sans-serif; font-weight:700; font-size:1.35rem; color:#fff; margin:.9rem 0 .2rem;
  text-shadow:0 2px 6px rgba(0,0,0,.25); }
.home-note { color:#fff; opacity:.95; font-size:.95rem; margin-bottom:.4rem; text-shadow:0 1px 4px rgba(0,0,0,.25); }
.home-bar { background:rgba(255,255,255,.35); border-radius:999px; height:14px; overflow:hidden; margin:.2rem 0 .5rem; }
.home-bar > div { height:100%; border-radius:999px; background:linear-gradient(90deg,#ffd45c,#ff9a3c); }
[class*="st-key-hometodo_"], [class*="st-key-hometile_"] { background:#fffdf7; border:2px solid #efe3bd; border-radius:18px;
  padding:.5rem .9rem; margin-bottom:.45rem; box-shadow:0 4px 14px rgba(0,0,0,.1); }
[class*="st-key-hometodo_"] { border-left:8px solid var(--accent, #1b8f84); }
[class*="st-key-hometile_"] { border-top:7px solid var(--tile, #6b63d9); min-height:100%; }
.todo-title { font-family:'Fredoka','Baloo 2',sans-serif; font-weight:700; font-size:1.1rem; color:#2b2a4a; }
.todo-why { color:#5b5a73; font-size:.95rem; line-height:1.35; }
.todo-done .todo-title { text-decoration:line-through; opacity:.6; }
.tile-title { font-family:'Fredoka','Baloo 2',sans-serif; font-weight:700; font-size:1.08rem; color:#2b2a4a; margin-top:.1rem; }
.tile-desc { color:#5b5a73; font-size:.92rem; line-height:1.35; min-height:2.5rem; }
.tile-icon { font-size:1.9rem; line-height:1; }
</style>
"""


# ------------------------------------------------------------------
# Navigation (runs before the page redraws, so it can change the menu choice)
# ------------------------------------------------------------------
def remove_todo(student_id, item_key):
    """The student takes one of their own items off the list."""
    try:
        import todo_store
        from auth_progress import get_supabase_client
        todo_store.set_status(get_supabase_client(), student_id, item_key, "removed")
    except Exception as exc:
        print(f"[inky] home: could not remove the item: {exc}")
    st.session_state.pop("_home_cache", None)
    keys = st.session_state.get("_todo_keys")
    if keys is not None:
        keys.discard(item_key)


def go_to(target, deep=None):
    st.session_state["nav_choice"] = target
    if deep and deep.get("sp"):
        st.session_state["sp_band"] = deep["band"]
        st.session_state["sp_lesson_pick"] = deep["lesson"]
        st.session_state.pop(f"sp_quiz_{deep['lesson']}", None)
    elif deep:
        p = deep["prefix"]
        st.session_state[f"{p}_age_band"] = st.session_state.get("age_band", "")
        st.session_state[f"{p}_level"] = deep["level"]
        st.session_state[f"{p}_topic"] = deep["topic"]
        st.session_state[f"{p}_lesson"] = deep["lesson"]
        st.session_state[f"{p}_run"] = None


# ------------------------------------------------------------------
# Reading the student's progress
# ------------------------------------------------------------------
def _when(row):
    raw = str(row.get("created_at") or "")
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def _load(student_id, dashboard):
    """Activity log, vocabulary count and question history. Cached for a few seconds."""
    cache = st.session_state.get("_home_cache")
    if cache and cache["sid"] == student_id and time.time() - cache["t"] < 20:
        return cache["data"]
    data = {"activities": [], "vocab": 0, "history": [], "spelling_weak": [], "todo": []}
    try:
        d = dashboard(student_id)
        data["activities"] = [a for a in d.get("activities", []) if a.get("activity_type") != "wellbeing_flag"]
        data["vocab"] = len(d.get("vocabulary", []))
    except Exception as exc:
        print(f"[inky] home: could not read progress: {exc}")
    try:
        from auth_progress import get_supabase_client
        res = (
            get_supabase_client().table("student_question_history").select("lesson_id,times_seen,times_correct,last_correct")
            .eq("student_id", student_id).execute()
        )
        data["history"] = res.data or []
    except Exception as exc:
        print(f"[inky] home: could not read question history: {exc}")
    try:
        from auth_progress import get_supabase_client
        db = get_supabase_client()
        prog = (
            db.table("spelling_progress").select("lesson_id,best_score,total_questions,completed")
            .eq("user_id", student_id).execute().data or []
        )
        tried = [r for r in prog if not r.get("completed") and int(r.get("total_questions") or 0) > 0]
        if tried:
            titles = {
                r["lesson_id"]: r
                for r in (db.table("spelling_lessons").select("lesson_id,title,lesson_number,grade_band").execute().data or [])
            }
            tried.sort(key=lambda r: int(r.get("best_score") or 0) / int(r["total_questions"]))
            for r in tried:
                info = titles.get(r["lesson_id"])
                if info:
                    data["spelling_weak"].append({
                        "sp": True, "lesson": r["lesson_id"], "band": info.get("grade_band") or "lower",
                        "title": f"Lesson {info.get('lesson_number')}: {info.get('title')}",
                    })
    except Exception as exc:
        print(f"[inky] home: could not read spelling progress: {exc}")
    try:
        import todo_store
        from auth_progress import get_supabase_client
        db = get_supabase_client()
        today = datetime.now(timezone.utc).date()
        for item in todo_store.load_items(db, student_id):
            finished = todo_store.done_after(item, data["activities"])
            if finished:
                when = _when({"created_at": finished})
                if when and when.date() < today:
                    todo_store.set_status(db, student_id, item["item_key"], "done")   # finished on an earlier day
                    continue
                item["finished_today"] = True
            data["todo"].append(item)
    except Exception as exc:
        print(f"[inky] home: could not read the to-do list: {exc}")
    st.session_state["_home_cache"] = {"sid": student_id, "t": time.time(), "data": data}
    return data


def _lesson_index():
    """lesson id -> where it lives (section, level, topic, title). Shared with the Marking Arena."""
    from lesson_catalog import lesson_index
    return lesson_index()


def weakest_skill(marked):
    """The writing skill with the lowest share of marks over the last few pieces, or None."""
    totals = {k: [0, 0] for k in SKILL_KEYS}
    used = 0
    for row in marked[:5]:
        details = row.get("details")
        if not isinstance(details, dict) or "wc_score" not in details:
            continue
        used += 1
        for skill, key in SKILL_KEYS.items():
            try:
                totals[skill][0] += int(details.get(key, 0))
            except (TypeError, ValueError):
                pass
            totals[skill][1] += SKILL_MAX[skill]
    if not used:
        return None
    ratios = {k: (v[0] / v[1] if v[1] else 1.0) for k, v in totals.items()}
    skill = min(ratios, key=ratios.get)
    return skill if ratios[skill] < 0.75 else None


def weak_lessons(history, limit=2):
    """Lessons where the student keeps missing questions (kind and fair: needs several tries)."""
    per = {}
    for h in history:
        lid = h.get("lesson_id")
        if not lid:
            continue
        p = per.setdefault(lid, {"seen": 0, "right": 0, "missed_last": 0})
        p["seen"] += int(h.get("times_seen") or 0)
        p["right"] += int(h.get("times_correct") or 0)
        p["missed_last"] += 1 if h.get("last_correct") is False else 0
    index = _lesson_index()
    weak = []
    for lid, p in per.items():
        if lid not in index or p["seen"] < 4:
            continue
        ratio = p["right"] / p["seen"]
        if ratio < 0.6 or p["missed_last"] >= 2:
            weak.append((ratio, lid))
    weak.sort()
    return [index[lid] for _, lid in weak[:limit]]


def _streak(activities):
    days = {w.date() for w in map(_when, activities) if w}
    today = datetime.now(timezone.utc).date()
    day = today if today in days else today - timedelta(days=1)
    count = 0
    while day in days:
        count += 1
        day -= timedelta(days=1)
    return count


# ------------------------------------------------------------------
# Building the to-do list
# ------------------------------------------------------------------
def _work_in_progress():
    """Is there writing the student started but has not finished?"""
    for key, value in st.session_state.items():
        if isinstance(key, str) and key.startswith("draft_") and str(value or "").strip():
            return NAV_DOJO
    if str(st.session_state.get("arena_text", "")).strip() and not st.session_state.get("last_marking"):
        return NAV_ARENA
    return None


def build_todo(data, lower):
    acts = data["activities"]
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    today = now.date()

    def seen_in(target, since=None, today_only=False):
        word = SECTION_WORD.get(target)
        for a in acts:
            w = _when(a)
            if not w:
                continue
            if today_only and w.date() != today:
                continue
            if since and w < since:
                continue
            if target == NAV_DOJO:
                if a.get("activity_type") == "marked_item":
                    return True
            elif word and word in str(a.get("section_name", "")).lower():
                return True
        return False

    marked = [a for a in acts if a.get("activity_type") == "marked_item"]
    items, used = [], set()

    def add(key, nav, icon, title, why, deep=None, stored=False, done=None):
        if key in used:
            return
        used.add(key)
        if done is None:
            done = seen_in(nav, today_only=True) if nav != NAV_DOJO else (
                seen_in(NAV_DOJO, today_only=True) or any(str(k).startswith("fb_") and v for k, v in st.session_state.items()))
        items.append({"key": key, "nav": nav, "icon": icon, "title": title, "why": why, "deep": deep,
                      "done": done, "stored": stored})

    # 1. Pick up where they left off
    wip = _work_in_progress()
    if wip == NAV_DOJO:
        add("resume", NAV_DOJO, "✏️", "Finish your piece", "You started writing. Pick up right where you left off!")
    elif wip == NAV_ARENA:
        add("resume", NAV_ARENA, "🏅", "Get feedback on your writing", "Your writing is ready. Let Inky read it and tell you what is great.")

    # 1b. Lessons the student added from their marking
    for it in data.get("todo", [])[:3]:
        add(it["item_key"], it["nav"], "📌", it["title"], it.get("why") or "You added this from your marking.",
            deep=it.get("deep"), stored=True, done=bool(it.get("finished_today")))

    # 2. First piece, or the next skill to grow
    if not marked:
        add("first", NAV_DOJO, "🥋", "Write your first piece", "Pick a style, then write one part at a time with Inky.")
    else:
        skill = weakest_skill(marked)
        if skill:
            nav, icon, title, why = SKILL_TIPS[skill]
            add(f"skill_{skill}", nav, icon, title, why)

    # 3. Lessons they keep finding tricky
    for info in weak_lessons(data["history"]):
        add(f"lesson_{info['lesson']}", info["nav"], "🔁", f"Try again: {info['title']}",
            "A little more practice here will make it feel easy.", deep=info)

    for info in data.get("spelling_weak", [])[:1]:
        add(f"spelling_{info['lesson']}", NAV_SPELLING, "🐝", f"Try again: {info['title']}",
            "Read the rule once more, then beat your best score in the drill.", deep=info)

    # 4. Words
    if data["vocab"] < 5:
        add("vault_start", NAV_VAULT, "💎", "Collect 5 new words", "Add words to your list and use them in your writing.")
    elif not seen_in(NAV_VAULT, since=week_ago):
        add("vault_practise", NAV_VAULT, "🎯", "Practise your word list", "A quick quiz helps new words stick.")

    # 5. Variety this week
    if not seen_in(NAV_SPELLING, since=week_ago) and not any(i["nav"] == NAV_SPELLING for i in items):
        add("spelling", NAV_SPELLING, "🔤", "Practise spelling and phonics", "Sound words out and learn tricky patterns.")
    if not seen_in(NAV_READING, since=week_ago):
        add("reading", NAV_READING, "📖", "Read a short passage", "Read, then answer a few questions about it.")
    if not seen_in(NAV_GRAMMAR, since=week_ago):
        add("grammar", NAV_GRAMMAR, "🧩", "Do a grammar lesson", "Short lessons on sentences, nouns, verbs and more.")
    if not seen_in(NAV_LANGUAGE, since=week_ago):
        add("language", NAV_LANGUAGE, "🎭", "Explore language", "Word meanings, synonyms, prefixes and more.")

    cap = 4 if lower else 5
    keep, auto = [], 0
    stored_count = sum(1 for i in items if i["stored"])
    for i in items:
        if i["stored"]:
            keep.append(i)
        elif auto < max(1, cap - stored_count):
            keep.append(i)
            auto += 1
    keep.sort(key=lambda i: i["done"])      # unfinished tasks first
    return keep


# ------------------------------------------------------------------
# The page
# ------------------------------------------------------------------
def render_home(profile, ctx):
    """ctx: age_band, xp, level_info(xp), accent(nav) and dashboard(student_id)."""
    name = html.escape(str(profile.get("display_name") or "friend").strip() or "friend")
    lower = str(ctx.get("age_band", "")).startswith("Lower")
    data = _load(profile["student_id"], ctx["dashboard"])
    items = build_todo(data, lower)
    streak = _streak(data["activities"])
    is_new = not data["activities"]

    xp = int(ctx.get("xp") or 0)
    rank, _pct, next_xp = ctx["level_info"](xp)
    st.markdown(HOME_CSS, unsafe_allow_html=True)

    hello = f"Welcome, {name}!" if is_new else f"Welcome back, {name}!"
    sub = ("I'm Inky. Let's start your writing adventure!" if is_new
           else "Here is your plan for today. Pick a task, or explore the map below.")
    chips = f'<span class="home-chip">✨ {html.escape(str(rank))}</span><span class="home-chip">⭐ {xp} XP</span>'
    if streak >= 2:
        chips += f'<span class="home-chip">🔥 {streak}-day streak</span>'
    st.markdown(
        f'<div class="home-hero"><div class="home-owl">🦉</div><div><div class="home-hi">{hello}</div>'
        f'<div class="home-sub">{sub}</div><div class="home-chips">{chips}</div></div></div>',
        unsafe_allow_html=True,
    )

    # ---- To-do list
    st.markdown('<div class="home-h">📝 Your To-Do List</div>', unsafe_allow_html=True)
    done_count = sum(1 for i in items if i["done"])
    if items:
        pct = int(round(100 * done_count / len(items)))
        st.markdown(
            f'<div class="home-note">{done_count} of {len(items)} done today</div>'
            f'<div class="home-bar"><div style="width:{max(pct, 4)}%"></div></div>',
            unsafe_allow_html=True,
        )
    if items and done_count == len(items):
        st.success(f"🎉 Brilliant, {name}! You finished your list today. Explore the map below for more.")
    for n, item in enumerate(items):
        with st.container(key=f"hometodo_{n}"):
            c1, c2, c3 = st.columns([5, 1.7, 0.7], vertical_alignment="center")
            tick = "✅" if item["done"] else item["icon"]
            cls = "todo-done" if item["done"] else ""
            c1.markdown(
                f'<div class="{cls}"><div class="todo-title">{tick} {html.escape(item["title"])}</div>'
                f'<div class="todo-why">{html.escape(item["why"])}</div></div>',
                unsafe_allow_html=True,
            )
            c2.button(
                "Done today" if item["done"] else "Let's go ➜", key=f"home_todo_btn_{n}", use_container_width=True,
                type="secondary" if item["done"] else "primary",
                on_click=go_to, args=(item["nav"], item["deep"]),
            )
            if item["stored"] and not item["done"]:
                c3.button("✕", key=f"home_todo_rm_{n}", help="Take this off my list", use_container_width=True,
                          on_click=remove_todo, args=(profile["student_id"], item["key"]))

    # ---- Map of every section
    st.markdown('<div class="home-h">🧭 Where do you want to go?</div>', unsafe_allow_html=True)
    tile_css = "".join(
        f".st-key-hometile_{re.sub(r'[^A-Za-z0-9]', '', nav)} {{ border-top-color:{ctx['accent'](nav)} !important; }}"
        for nav, *_ in TILES
    )
    st.markdown(f"<style>{tile_css}</style>", unsafe_allow_html=True)
    per_row = 3
    for start in range(0, len(TILES), per_row):
        cols = st.columns(per_row)
        for col, (nav, icon, title, desc) in zip(cols, TILES[start:start + per_row]):
            safe = re.sub(r"[^A-Za-z0-9]", "", nav)
            with col:
                with st.container(key=f"hometile_{safe}"):
                    st.markdown(
                        f'<div><div class="tile-icon">{icon}</div>'
                        f'<div class="tile-title">{html.escape(title)}</div>'
                        f'<div class="tile-desc">{html.escape(desc)}</div></div>',
                        unsafe_allow_html=True,
                    )
                    st.button("Open", key=f"home_tile_btn_{safe}", use_container_width=True, on_click=go_to, args=(nav,))
