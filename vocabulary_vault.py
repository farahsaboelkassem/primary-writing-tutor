"""The Vocabulary Vault for The Writing Adventure.

Three areas, all driven by buttons:

  💎 Words         word lists by genre, "All-round" words, word upgrades and "My words"
  ✨ Key Phrases   phrase lists by genre and "My phrases"
  🎯 Quizzes       a built-in Vault quiz, a quiz on your own list, and an AI quiz

Where the lists come from
-------------------------
The Supabase table vault_items (see vault_setup.sql). If that table is empty or cannot be
reached, the app uses the starter lists in vault_starter.py, so the Vault always works.

Where a student's own list is kept
----------------------------------
The student_vocabulary table, one row per word or phrase, linked to the student's account.

Other parts of the app can add to a student's list with vault_add(), or show add buttons with
render_guide_extras() (Writing Dojo) and render_arena_suggestions() (Marking Arena).
"""
import html
import random
import re
from datetime import datetime, timezone

import streamlit as st

import lesson_hub
from vault_starter import starter_items

QUIZ_SIZE = 6
CACHE_SECONDS = 300
SECTIONS = [("words", "💎 Words"), ("phrases", "✨ Key Phrases"), ("quiz", "🎯 Quizzes")]
AI_FOCUSES = ["Mixed Vocabulary", "Shades of Meaning", "Powerful Verbs",
              "Powerful Adjectives", "Adverbs", "Common Collective Nouns"]
MASTERY_RANK = {"Learning": 0, "Reviewed": 1, "Mastered": 2}
QUIZ_CFG = {"prefix": "vq"}  # session-key prefix used by the shared question screen

VAULT_CSS = """
<style>
.vv-hero { display:flex; align-items:center; gap:1rem; padding:1rem 1.3rem; border-radius:22px; margin:0 0 1rem;
  background:linear-gradient(135deg,#0a5d6b 0%,#22b99c 68%,#f6c453 135%); color:#fff; box-shadow:0 10px 26px rgba(4,37,47,.35); }
.vv-hero-icon { font-size:2.6rem; line-height:1; }
.vv-hero-title { font-family:'Fredoka',sans-serif; font-weight:700; font-size:1.75rem; line-height:1.1; }
.vv-hero-sub { opacity:.93; font-size:.98rem; margin-top:.15rem; }
.vv-card { background:#fffdf7; color:#2b2a4a; border:2px solid #f1dfae; border-left:8px solid #f6c453;
  border-radius:16px; padding:.65rem 1rem; margin-bottom:.4rem; box-shadow:0 3px 10px rgba(0,0,0,.08); }
.vv-card.phrase { border-color:#bfe9df; border-left-color:#22b99c; }
.vv-term { font-family:'Fredoka',sans-serif; font-size:1.2rem; font-weight:700; color:#0a5d6b; }
.vv-meaning { font-size:.98rem; }
.vv-example { font-style:italic; color:#5b5a73; font-size:.93rem; margin-top:.15rem; }
.vv-chip { display:inline-block; font-size:.7rem; font-weight:700; padding:.1rem .55rem; margin-left:.45rem;
  border-radius:999px; background:#e2f7f3; color:#086256; vertical-align:middle; }
.vv-chip.gold { background:#fff0c2; color:#8a5a00; }
.vv-group { color:#e9fff9; font-weight:800; margin:.6rem 0 .2rem; letter-spacing:.02em; }
</style>
"""

HERO_HTML = (
    '<div class="vv-hero"><div class="vv-hero-icon">🏛️</div><div>'
    '<div class="vv-hero-title">The Vocabulary Vault</div>'
    '<div class="vv-hero-sub">Collect powerful words and key phrases, build your own lists, then test yourself.</div>'
    '</div></div>'
)


# ------------------------------------------------------------------
# Small helpers
# ------------------------------------------------------------------
def _client():
    from auth_progress import get_supabase_client  # imported here so tests can replace _client
    return get_supabase_client()


def _student_id():
    return (st.session_state.get("student_profile") or {}).get("student_id")


def _level_for(age_band):
    return "lower" if str(age_band or "").lower().startswith("lower") else "upper"


def _band(c):
    getter = c.get("age_band")
    return getter() if callable(getter) else ""


def _for_level(items, level):
    return [i for i in items if i["level"] in ("both", level)]


def genre_label(genre):
    return "🌍 All-round" if genre == "General" else genre


def pick_buttons(key_prefix, options, state_key, columns=4, default=None):
    """Rows of buttons. The chosen one is highlighted and kept in session_state[state_key].
    options is a list of (value, label)."""
    if not options:
        return st.session_state.get(state_key, default)
    st.session_state.setdefault(state_key, default if default is not None else options[0][0])
    current = st.session_state[state_key]
    cols = st.columns(min(columns, len(options)))
    for i, (value, label) in enumerate(options):
        with cols[i % len(cols)]:
            if st.button(label, key=f"{key_prefix}_{value}", use_container_width=True,
                         type="primary" if value == current else "secondary"):
                st.session_state[state_key] = value
                st.rerun()
    return st.session_state[state_key]


# ------------------------------------------------------------------
# The Vault lists
# ------------------------------------------------------------------
@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def _fetch_vault_rows():
    res = _client().table("vault_items").select("*").eq("active", True).execute()
    return res.data or []


def _row_to_item(row):
    try:
        item_type = str(row.get("item_type") or "").strip()
        text = str(row.get("term") or "").strip()
        meaning = str(row.get("meaning") or "").strip()
        if item_type not in ("word", "phrase") or not text or not meaning:
            return None
        level = row.get("level") if row.get("level") in ("lower", "upper", "both") else "both"
        return {"code": str(row.get("item_code") or f"db:{text}").strip(), "type": item_type,
                "genre": str(row.get("genre") or "General").strip() or "General", "level": level,
                "text": text, "meaning": meaning, "example": str(row.get("example_sentence") or "").strip()}
    except Exception:
        return None


def load_items():
    """All Vault items: from Supabase if it has any, otherwise the built-in starter lists."""
    try:
        items = [i for i in (_row_to_item(r) for r in _fetch_vault_rows()) if i]
        if items:
            return items
    except Exception as exc:
        print(f"[inky] vault lists unavailable, using the starter lists: {exc}")
    return starter_items()


def genre_groups(items):
    """Genres that have items, grouped like the Writing Dojo: all-round, Fiction, Non-Fiction, more."""
    import writing_tutor as wt
    fiction = [g for cat in wt.FICTION_STYLES.values() for g in cat]
    nonfiction = [g for cat in wt.NON_FICTION_SUBGENRES.values() for g in cat]
    present = {i["genre"] for i in items}
    groups = []
    if "General" in present:
        groups.append(("🌍 Any genre", ["General"]))
    for label, names in (("📖 Fiction", fiction), ("📰 Non-Fiction", nonfiction)):
        found = [g for g in names if g in present]
        if found:
            groups.append((label, found))
    others = sorted(present - set(fiction) - set(nonfiction) - {"General"})
    if others:
        groups.append(("🗂️ More", others))
    return groups


# ------------------------------------------------------------------
# A student's own list
# ------------------------------------------------------------------
def _mine_item(row):
    return {"code": f"mine:{row.get('id', row.get('word_or_phrase'))}", "type": row.get("item_type") or "word",
            "genre": row.get("genre_or_category") or "General", "level": "both",
            "text": str(row.get("word_or_phrase") or "").strip(), "meaning": str(row.get("meaning_or_note") or "").strip(),
            "example": str(row.get("example_sentence") or "").strip(),
            "status": row.get("mastery_status") or "Learning",
            "seen": int(row.get("times_practiced") or 0), "correct": int(row.get("times_correct") or 0), "saved": True}


def load_mine(force=False):
    """The signed-in student's saved words and phrases (kept in the session once loaded)."""
    if st.session_state.get("vv_mine_loaded") and not force:
        return st.session_state["vv_mine"]
    mine = []
    sid = _student_id()
    if sid:
        try:
            res = (_client().table("student_vocabulary").select("*").eq("student_id", sid)
                   .order("updated_at", desc=True).execute())
            mine = [m for m in (_mine_item(r) for r in (res.data or [])) if m["text"]]
        except Exception as exc:
            print(f"[inky] could not load the student's list: {exc}")
    have = {m["text"].lower() for m in mine}
    for old in st.session_state.get("local_vocab", []) or []:  # words saved before the Vault existed
        word = str(old.get("word") or "").strip()
        if word and word.lower() not in have:
            mine.append({"code": f"mine:old:{word}", "type": "word", "genre": "General", "level": "both",
                         "text": word, "meaning": str(old.get("meaning") or ""), "example": str(old.get("example") or ""),
                         "status": "Learning", "seen": 0, "correct": 0, "saved": False})
            have.add(word.lower())
    st.session_state["vv_mine"], st.session_state["vv_mine_loaded"] = mine, True
    return mine


def _save_rows(rows):
    """Save rows to student_vocabulary. If the new columns have not been added yet (see
    vault_setup.sql), save the older columns so nothing is lost."""
    try:
        _client().table("student_vocabulary").upsert(rows, on_conflict="student_id,word_or_phrase").execute()
        return True
    except Exception as exc:
        print(f"[inky] saving with the new columns failed ({exc}); trying the older columns")
    try:
        old_cols = ("student_id", "word_or_phrase", "genre_or_category", "meaning_or_note",
                    "mastery_status", "times_practiced", "updated_at")
        _client().table("student_vocabulary").upsert([{k: r[k] for k in old_cols if k in r} for r in rows],
                                                     on_conflict="student_id,word_or_phrase").execute()
        return True
    except Exception as exc:
        print(f"[inky] could not save to the student's list: {exc}")
        return False


def _row_for(sid, item):
    return {"student_id": sid, "word_or_phrase": item["text"], "item_type": item["type"],
            "genre_or_category": item["genre"], "meaning_or_note": item["meaning"],
            "example_sentence": item.get("example", ""), "mastery_status": item.get("status", "Learning"),
            "times_practiced": max(1, int(item.get("seen") or 0)), "times_correct": int(item.get("correct") or 0),
            "updated_at": datetime.now(timezone.utc).isoformat()}


def vault_add(item_type, text, meaning="", genre="General", example=""):
    """Add a word or phrase to the student's list. Returns "added", "exists" or "empty"."""
    term = str(text or "").strip()
    if not term:
        return "empty"
    mine = load_mine()
    if any(m["text"].lower() == term.lower() for m in mine):
        return "exists"
    item = {"code": f"mine:new:{len(mine)}:{term}", "type": item_type, "genre": genre or "General", "level": "both",
            "text": term, "meaning": str(meaning or "").strip(), "example": str(example or "").strip(),
            "status": "Learning", "seen": 1, "correct": 0, "saved": False}
    sid = _student_id()
    if sid:
        item["saved"] = _save_rows([_row_for(sid, item)])
    mine.insert(0, item)
    return "added"


def vault_remove(text):
    mine = load_mine()
    st.session_state["vv_mine"] = [m for m in mine if m["text"].lower() != str(text).lower()]
    sid = _student_id()
    if sid:
        try:
            _client().table("student_vocabulary").delete().eq("student_id", sid).eq("word_or_phrase", text).execute()
        except Exception as exc:
            print(f"[inky] could not remove from the student's list: {exc}")


def add_button(award_xp, item_type, text, meaning, genre, example="", key=""):
    """A '➕ Add to my list' button that turns into '✅ In my list' once added."""
    if any(m["text"].lower() == str(text).strip().lower() for m in load_mine()):
        st.button("✅ In my list", key=key, disabled=True, use_container_width=True)
        return
    if st.button("➕ Add to my list", key=key, use_container_width=True):
        if vault_add(item_type, text, meaning, genre, example) == "added":
            if award_xp:
                award_xp(5)
            mine = load_mine()
            st.toast("Saved to your list!" if mine and mine[0].get("saved") else "Added for now. It will save once you are connected.")
            st.rerun()


# ------------------------------------------------------------------
# Cards and list screens
# ------------------------------------------------------------------
def _card_html(item, status=False):
    kind = "phrase" if item["type"] == "phrase" else "word"
    chips = ""
    if item["level"] == "lower":
        chips += '<span class="vv-chip">Grades 1-3</span>'
    elif item["level"] == "upper":
        chips += '<span class="vv-chip">Grades 4-6</span>'
    if status and item.get("status"):
        chips += f'<span class="vv-chip gold">{html.escape(item["status"])}</span>'
    example = f'<div class="vv-example">“{html.escape(item["example"])}”</div>' if item.get("example") else ""
    return (f'<div class="vv-card {kind}"><span class="vv-term">{html.escape(item["text"])}</span>{chips}'
            f'<div class="vv-meaning">{html.escape(item["meaning"])}</div>{example}</div>')


def _word_upgrades():
    from writing_tutor import LANGUAGE_EXAMPLES
    st.markdown("#### ✨ Power Up Everyday Words")
    for title, basic, vivid, tip in LANGUAGE_EXAMPLES:
        st.markdown(
            f'<div class="vv-card"><span class="vv-term">{html.escape(title)}</span>'
            f'<div class="vv-meaning"><b>Instead of:</b> {html.escape(basic)} &nbsp;➡️&nbsp; <b>Try:</b> {html.escape(vivid)}</div>'
            f'<div class="vv-example">{html.escape(tip)}</div></div>', unsafe_allow_html=True)


def _my_list(c, item_type):
    noun, plural = ("word", "words") if item_type == "word" else ("phrase", "phrases")
    mine = [m for m in load_mine() if m["type"] == item_type]
    st.markdown(f"#### ⭐ My {plural}")
    with st.form(f"vv_add_form_{item_type}", clear_on_submit=True):
        c1, c2, c3 = st.columns([1.3, 2, 2])
        term = c1.text_input(noun.capitalize())
        meaning = c2.text_input("What it means")
        example = c3.text_input("Example sentence (optional)")
        if st.form_submit_button(f"➕ Add my own {noun}"):
            if term.strip() and meaning.strip():
                if vault_add(item_type, term, meaning, "My own", example) == "added":
                    if c.get("award_xp"):
                        c["award_xp"](5)
                    st.success(f"Added “{term.strip()}”!")
                else:
                    st.info("That one is already in your list.")
            else:
                st.warning(f"Type the {noun} and what it means.")
    mine = [m for m in load_mine() if m["type"] == item_type]
    if not mine:
        st.caption(f"Your {plural} will appear here. Tap ➕ on any {noun} in the lists, in the Writing Dojo or after marking.")
        return
    by_genre = {}
    for m in mine:
        by_genre.setdefault(m["genre"], []).append(m)
    for genre, entries in by_genre.items():
        st.markdown(f'<div class="vv-group">{html.escape(genre_label(genre))}</div>', unsafe_allow_html=True)
        for m in entries:
            left, right = st.columns([5, 1])
            left.markdown(_card_html(m, status=True), unsafe_allow_html=True)
            with right:
                if st.button("🗑️ Remove", key=f"vv_rm_{item_type}_{m['code']}", use_container_width=True):
                    vault_remove(m["text"])
                    st.rerun()


def render_list_section(c, item_type):
    plural = "words" if item_type == "word" else "phrases"
    level = _level_for(_band(c))
    items = [i for i in load_items() if i["type"] == item_type]
    shown_items = _for_level(items, level)
    groups = genre_groups(shown_items)
    state_key = f"vv_view_{item_type}"
    mine_count = len([m for m in load_mine() if m["type"] == item_type])

    special = [("__mine__", f"⭐ My {plural} ({mine_count})")]
    if item_type == "word":
        special.append(("__upgrades__", "🎨 Word upgrades"))
    default = groups[0][1][0] if groups else "__mine__"
    pick_buttons(f"vv_{item_type}_special", special, state_key, columns=3, default=default)
    for gi, (group_label, genres) in enumerate(groups):
        st.markdown(f'<div class="vv-group">{html.escape(group_label)}</div>', unsafe_allow_html=True)
        pick_buttons(f"vv_{item_type}_g{gi}", [(g, genre_label(g)) for g in genres], state_key, columns=4, default=default)
    view = st.session_state.get(state_key, default)

    st.markdown("---")
    if view == "__mine__":
        _my_list(c, item_type)
        return
    if view == "__upgrades__":
        _word_upgrades()
        return
    entries = [i for i in shown_items if i["genre"] == view]
    st.markdown(f"#### {genre_label(view)} {plural}")
    st.caption(f"Showing {plural} for {'Lower' if level == 'lower' else 'Upper'} Primary. Change your school stage in the sidebar to see the other level.")
    if not entries:
        st.info("Nothing here yet. Try another genre.")
    for item in entries:
        left, right = st.columns([4.2, 1.3])
        left.markdown(_card_html(item), unsafe_allow_html=True)
        with right:
            add_button(c.get("award_xp"), item_type, item["text"], item["meaning"], item["genre"], item["example"],
                       key=f"vv_add_{item_type}_{item['code']}")


# ------------------------------------------------------------------
# Quiz questions built from the lists (no AI needed)
# ------------------------------------------------------------------
def _gapped(item):
    core = item["text"].rstrip(",.:;! ").strip()
    example = item.get("example") or ""
    match = re.search(re.escape(core), example, flags=re.IGNORECASE) if core and example else None
    return None if not match else example[:match.start()] + "___" + example[match.end():]


def _distractors(item, universe, field, k, rng):
    pool = [u for u in universe if u["type"] == item["type"] and u["text"].lower() != item["text"].lower()]
    rng.shuffle(pool)
    pool.sort(key=lambda u: 0 if u["genre"] == item["genre"] else 1)  # same genre first, stable after the shuffle
    out, seen = [], {str(item[field]).lower()}
    for u in pool:
        value = str(u[field])
        if value and value.lower() not in seen:
            out.append(value)
            seen.add(value.lower())
        if len(out) == k:
            break
    return out


def kinds_for(item, allow_typing):
    kinds = ["meaning", "which", "gap", "tf"]
    if allow_typing and item["type"] == "word" and re.fullmatch(r"[A-Za-z’'-]+", item["text"]):
        kinds.append("type")
    return kinds


def make_question(item, kind, universe, rng=random):
    """One question about one item, or None if there is not enough material for that style."""
    noun = "word" if item["type"] == "word" else "phrase"
    text, meaning = item["text"], item["meaning"]
    base = {"code": f"vv:{item['code']}:{kind}", "item_code": item["code"],
            "why": f"**{text}** means {meaning}."}
    if kind == "meaning":
        d = _distractors(item, universe, "meaning", 2, rng)
        return None if len(d) < 2 else {**base, "type": "multiple_choice", "kind": "spot",
                                        "q": f"What does the {noun} **{text}** mean?", "options": [meaning] + d, "correct": meaning}
    if kind == "which":
        d = _distractors(item, universe, "text", 2, rng)
        return None if len(d) < 2 else {**base, "type": "multiple_choice", "kind": "spot",
                                        "q": f"Which {noun} means: *{meaning}*?", "options": [text] + d, "correct": text}
    if kind == "gap":
        gapped, d = _gapped(item), _distractors(item, universe, "text", 2, rng)
        return None if (not gapped or len(d) < 2) else {**base, "type": "multiple_choice", "kind": "use",
                                                        "q": f"Choose the {noun} that best completes the sentence: {gapped}",
                                                        "options": [text] + d, "correct": text}
    if kind == "tf":
        d = _distractors(item, universe, "meaning", 1, rng)
        say_true = rng.random() < 0.5 or not d
        shown = meaning if say_true else d[0]
        return {**base, "type": "true_false", "kind": "spot", "options": ["True", "False"],
                "q": f"True or false: **{text}** means “{shown}”.", "correct": "True" if say_true else "False"}
    if kind == "type":
        return {**base, "type": "fill_blank", "kind": "use", "q": f"Type the word that means: *{meaning}*",
                "options": [], "correct": text, "accepted": [text], "case_sensitive": False}
    return None


def build_quiz(items, universe, n=QUIZ_SIZE, allow_typing=False, rng=random, weakest_first=False):
    """n questions from the items: one per item first, then a different style of question about the same
    items if the list is short. weakest_first puts words the student knows least at the front."""
    pool = list(items)
    rng.shuffle(pool)
    if weakest_first:
        pool.sort(key=lambda m: (MASTERY_RANK.get(m.get("status"), 0), int(m.get("seen") or 0)))
    questions, tried = [], {}
    for _ in range(3):  # a second and third pass only matter for short lists
        for item in pool:
            if len(questions) >= n:
                return questions
            used = tried.setdefault(item["code"], set())
            kinds = [k for k in kinds_for(item, allow_typing) if k not in used]
            rng.shuffle(kinds)
            for kind in kinds:
                used.add(kind)
                q = make_question(item, kind, universe, rng)
                if q:
                    questions.append(q)
                    break
    return questions


def ai_to_questions(raw):
    """Turn the AI quiz's answer into the same question format the other quizzes use."""
    out = []
    for i, q in enumerate(raw or []):
        options = [str(o) for o in q.get("options", []) if str(o).strip()]
        try:
            index = int(q.get("answer_index", 0))
        except (TypeError, ValueError):
            index = 0
        if len(options) >= 2 and 0 <= index < len(options) and str(q.get("question", "")).strip():
            out.append({"code": f"ai:{q.get('word', 'q')}:{i}", "type": "multiple_choice", "kind": "spot",
                        "q": str(q["question"]), "options": options, "correct": options[index],
                        "why": str(q.get("explanation", ""))})
    return out


# ------------------------------------------------------------------
# Quiz screens
# ------------------------------------------------------------------
def _mastery(correct):
    return "Mastered" if correct >= 3 else "Reviewed" if correct >= 1 else "Learning"


def record_practice(run):
    """After a quiz on the student's own list: update how often each item was practised and got right."""
    sid, rows, touched = _student_id(), [], {}
    for answer in run["answers"]:
        item = run["item_by_code"].get(answer.get("code"))
        if not item or not str(item.get("code", "")).startswith("mine:"):
            continue
        item["seen"] = int(item.get("seen") or 0) + 1
        item["correct"] = int(item.get("correct") or 0) + (1 if answer["correct"] else 0)
        item["status"] = _mastery(item["correct"])
        touched[item["code"]] = item
    if sid and touched:
        rows = [_row_for(sid, it) for it in touched.values()]
        item_saved = _save_rows(rows)
        for it in touched.values():
            it["saved"] = item_saved


def start_run(questions, label, mode, items_by_code=None, again=None):
    run = lesson_hub.new_run("vault", {"id": "vault"}, questions)
    run.update({"label": label, "mode": mode, "item_by_code": items_by_code or {}, "again": again})
    st.session_state["vv_run"] = run


def quiz_results(c, run):
    score, total = run["score"], len(run["questions"])
    if not run["saved"]:
        run["saved"] = True
        gained = score * 8
        if c.get("award_xp") and gained:
            c["award_xp"](gained, "📚 Word Wizard" if total and score / total >= 0.83 else None)
        if c.get("log"):
            c["log"]("quiz", "Vocabulary Vault", run["label"], score_or_grade=f"{score}/{total}",
                     genre_or_skill=run["mode"], xp_earned=gained)
        if run["mode"] == "mine":
            record_practice(run)
        run["xp_message"] = f"+{gained} XP"

    ratio = score / max(total, 1)
    st.progress(1.0, text="Quiz complete")
    if ratio >= 0.83:
        st.success(f"🏅 Brilliant! You scored {score} out of {total}.")
        if not run.get("celebrated"):
            run["celebrated"] = True
            st.balloons()
    elif ratio >= 0.5:
        st.success(f"👏 Well done! You scored {score} out of {total}.")
    else:
        st.info(f"💪 You scored {score} out of {total}. Have another go after a look at the lists.")
    st.caption(run.get("xp_message", ""))

    missed = [a for a in run["answers"] if not a["correct"]]
    if missed:
        st.subheader("Let’s look at these again")
        for a in missed:
            with st.container(border=True):
                st.markdown(f"**{lesson_hub.md(a['q'])}**")
                st.markdown(f"❌ Your answer: {lesson_hub.plain(a['chosen'])}")
                st.markdown(f"✅ Correct answer: **{lesson_hub.plain(a['correct_text'])}**")
                st.caption(a["why"].replace("**", ""))
                item = run["item_by_code"].get(a.get("code"))
                if item and run["mode"] != "mine":
                    add_button(c.get("award_xp"), item["type"], item["text"], item["meaning"], item["genre"],
                               item.get("example", ""), key=f"vv_missed_{run['id']}_{a['code']}")
    c1, c2 = st.columns(2)
    with c1:
        if run.get("again") and st.button("🔁 New quiz, same settings", key=f"vv_again_{run['id']}", use_container_width=True):
            run["again"]()
            st.rerun()
    with c2:
        if st.button("📋 Back to quiz menu", key=f"vv_menu_{run['id']}", use_container_width=True):
            st.session_state["vv_run"] = None
            st.rerun()


def _setup_vault_quiz(c, level, universe):
    st.caption("Questions are made from the Vault lists, so this quiz is quick and uses no AI.")
    qtype = pick_buttons("vv_qt", [("word", "💎 Words"), ("phrase", "✨ Phrases"), ("both", "🔀 Both")],
                         "vv_quiz_type", columns=3, default="word")
    types = ("word", "phrase") if qtype == "both" else (qtype,)
    pool_all = [i for i in _for_level(load_items(), level) if i["type"] in types]
    options = [("*", "🌍 All genres")] + [(g, genre_label(g)) for g in sorted({i["genre"] for i in pool_all})]
    genre = pick_buttons("vv_qg", options, "vv_quiz_genre", columns=4, default="*")
    if genre not in dict(options):
        genre = "*"
    items = pool_all if genre == "*" else [i for i in pool_all if i["genre"] == genre]
    st.markdown(f"**{len(items)}** items to be quizzed on.")

    def launch():
        qs = build_quiz(items, universe, QUIZ_SIZE, allow_typing=(level == "upper"))
        by_code = {q["code"]: next(i for i in items if i["code"] == q["item_code"]) for q in qs}
        label = f"Vault quiz: {'all genres' if genre == '*' else genre}"
        start_run(qs, label, "vault", by_code, again=launch)

    if st.button("🎲 Start the Vault quiz", type="primary", use_container_width=True, key="vv_go_vault"):
        if len(items) < 3:
            st.warning("There are not enough items here for a quiz yet. Try All genres or another type.")
        else:
            launch()
            st.rerun()


def _setup_mine_quiz(c, level, universe):
    st.caption("Questions come from the words and phrases you saved. The ones you know least come up first.")
    qtype = pick_buttons("vv_mt", [("word", "💎 My words"), ("phrase", "✨ My phrases"), ("both", "🔀 Both")],
                         "vv_mine_type", columns=3, default="word")
    types = ("word", "phrase") if qtype == "both" else (qtype,)
    mine = [m for m in load_mine() if m["type"] in types and m["meaning"]]
    st.markdown(f"You have **{len(mine)}** saved to be quizzed on.")
    if not mine:
        st.info("Add some words or phrases first. Tap ➕ in the Words and Key Phrases lists, the Writing Dojo, or after marking.")
        return

    def launch():
        fresh = [m for m in load_mine() if m["type"] in types and m["meaning"]]
        qs = build_quiz(fresh, universe + fresh, QUIZ_SIZE, allow_typing=(level == "upper"), weakest_first=True)
        by_code = {q["code"]: next(i for i in fresh if i["code"] == q["item_code"]) for q in qs}
        start_run(qs, "My list quiz", "mine", by_code, again=launch)

    if st.button("🎲 Start my list quiz", type="primary", use_container_width=True, key="vv_go_mine"):
        launch()
        st.rerun()


def _setup_ai_quiz(c):
    st.caption("The AI writes a brand-new quiz each time. It uses more of your AI allowance, so the Vault quiz is the quicker choice.")
    focus = pick_buttons("vv_af", [(f, f) for f in AI_FOCUSES], "vv_ai_focus", columns=3, default=AI_FOCUSES[0])

    def launch():
        history = st.session_state.setdefault("quiz_word_history", [])
        try:
            with st.spinner("Preparing a fresh vocabulary challenge..."):
                raw = c["ai_quiz"](focus, QUIZ_SIZE, history)
        except Exception as exc:
            st.error(str(exc))
            return False
        questions = ai_to_questions(raw)
        if not questions:
            st.error("The AI did not return a usable quiz. Please try again.")
            return False
        history.extend(str(q.get("word")) for q in (raw or []) if q.get("word"))
        start_run(questions, f"AI quiz: {focus}", "ai", {}, again=lambda: launch())
        return True

    if st.button("🎲 New AI quiz", type="primary", use_container_width=True, key="vv_go_ai"):
        if launch():
            st.rerun()


def render_quiz_section(c):
    run = st.session_state.get("vv_run")
    if run:
        if st.button("← Back to quiz menu", key="vv_quit"):
            st.session_state["vv_run"] = None
            st.rerun()
        st.markdown(f"### 🎯 {run['label']}")
        if run["index"] >= len(run["questions"]):
            quiz_results(c, run)
        else:
            lesson_hub.question(QUIZ_CFG, run)
        return

    level = _level_for(_band(c))
    universe = _for_level(load_items(), level)
    modes = [("bank", "📚 Vault quiz"), ("mine", "⭐ My list quiz")]
    if c.get("ai_quiz"):
        modes.append(("ai", "🤖 AI quiz"))
    mode = pick_buttons("vv_mode", modes, "vv_quiz_mode", columns=3, default="bank")
    st.markdown("---")
    if mode == "bank":
        _setup_vault_quiz(c, level, universe)
    elif mode == "mine":
        _setup_mine_quiz(c, level, universe)
    else:
        _setup_ai_quiz(c)


# ------------------------------------------------------------------
# Entry point and the helpers other screens use
# ------------------------------------------------------------------
def render_vocabulary_vault(c):
    """Draw the whole Vocabulary Vault.

    c is a dictionary with:
      award_xp   function(points, badge_or_None)
      log        function that saves an activity to the student's account (optional)
      ai_quiz    function(focus, n, previous_words) -> list of AI quiz questions (optional)
      age_band   function returning the student's school stage text
    """
    st.markdown(VAULT_CSS, unsafe_allow_html=True)
    st.markdown(HERO_HTML, unsafe_allow_html=True)
    section = pick_buttons("vv_section", SECTIONS, "vv_section_choice", columns=3, default="words")
    st.markdown("---")
    if section == "words":
        render_list_section(c, "word")
    elif section == "phrases":
        render_list_section(c, "phrase")
    else:
        render_quiz_section(c)


def render_guide_extras(guide, genre, title, key_prefix, award_xp=None):
    """Writing Dojo: show a block guide's phrases and vocabulary, each with an add-to-my-list button."""
    phrases = [str(p).strip() for p in (guide.get("point_scoring_phrases") or [])[:4] if str(p).strip()]
    if phrases:
        st.markdown("**✨ Point-Scoring Phrases:**")
        for i, phrase in enumerate(phrases):
            left, right = st.columns([4, 1.4])
            left.markdown(f"- `{phrase}`")
            with right:
                add_button(award_xp, "phrase", phrase, f"A useful phrase for {genre} writing", genre,
                           key=f"vv_gp_{key_prefix}_{i}")
    vocab = [v for v in (guide.get("suggested_vocabulary") or [])[:4] if str(v.get("word", "")).strip()]
    if vocab:
        st.markdown("**💎 Suggested Vocabulary:**")
        for i, v in enumerate(vocab):
            left, right = st.columns([4, 1.4])
            left.markdown(f"- **{v.get('word', '')}** — {v.get('meaning', '')}")
            with right:
                add_button(award_xp, "word", v.get("word", ""), v.get("meaning", ""), genre,
                           f"Used in {title}", key=f"vv_gv_{key_prefix}_{i}")


def render_arena_suggestions(genre, age_band, key_prefix="arena", award_xp=None):
    """Marking Arena: a few words and phrases to try next time, taken from the Vault (no AI needed)."""
    level = _level_for(age_band)
    items = _for_level(load_items(), level)
    have = {m["text"].lower() for m in load_mine()}
    state_key = f"vv_arena_{key_prefix}_{genre}_{level}"
    if state_key not in st.session_state:
        rng = random.Random()
        chosen = []
        for item_type, count in (("word", 4), ("phrase", 3)):
            pool = [i for i in items if i["type"] == item_type and i["genre"] == genre and i["text"].lower() not in have]
            extra = [i for i in items if i["type"] == item_type and i["genre"] == "General" and i["text"].lower() not in have]
            rng.shuffle(pool)
            rng.shuffle(extra)
            chosen += (pool + extra)[:count]
        st.session_state[state_key] = [i["code"] for i in chosen]
    by_code = {i["code"]: i for i in items}
    picks = [by_code[c] for c in st.session_state[state_key] if c in by_code]
    if not picks:
        return
    st.markdown("### 🔑 Words and phrases to try next time")
    st.caption("Tap ➕ to keep one in your list. You can practise them in the Vocabulary Vault.")
    for item in picks:
        left, right = st.columns([4.2, 1.4])
        left.markdown(_card_html(item), unsafe_allow_html=True)
        with right:
            add_button(award_xp, item["type"], item["text"], item["meaning"], item["genre"], item["example"],
                       key=f"vv_{key_prefix}_{item['code']}")
