import html
import json
import re

import streamlit as st


# ============================================================================
# SPELLING & PHONICS ARENA MODULE (Drop-in for primary-writing-tutor)
# ============================================================================
# Wired into app.py: render_spelling_arena(supabase, user_id, bubble, award_xp, log_activity).
# Spelling lessons are logged to the student's account so the Home page and the Progress
# screen can see them, and XP is only paid for improvement, so retaking cannot farm XP.
# ============================================================================


# ----------------------------------------------------------------------------
# THEME: "The Honey Hive" atmosphere (same job as the other UNIVERSE_CSS scenes)
# ----------------------------------------------------------------------------
# The shared look (paper panel, Baloo/Nunito type, chunky buttons, cards,
# metrics, radios, inputs) comes from the app's CUSTOM_CSS. This block only
# sets the section colours and the background scene.
_HEX_TILE = (
    "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='56' height='100' "
    "viewBox='0 0 56 100'%3E%3Cpath d='M28 66L0 50L0 16L28 0L56 16L56 50L28 66L28 100' fill='none' "
    "stroke='rgba(255,220,120,0.16)' stroke-width='2'/%3E%3Cpath d='M28 0L28 34L0 50L0 84L28 100L56 84"
    "L56 50L28 34' fill='none' stroke='rgba(255,220,120,0.16)' stroke-width='2'/%3E%3C/svg%3E\")"
)

SPELLING_UNIVERSE_CSS = (
    """
:root { --accent:#b0500a; --accent-light:#c25f10; --accent-dark:#8a3f05; --accent-soft:#fff3dc; --hero-a:#6b3a00; --hero-b:#e08a12; }
.stApp { background: linear-gradient(180deg, #2e1a05 0%, #6e3f0a 38%, #d58a14 74%, #ffd466 100%) !important; }
.stApp::before {
  background:
    radial-gradient(circle at 96% 12%, #fff2c2 0 32px, rgba(255,242,194,.30) 33px 60px, rgba(255,242,194,.08) 61px 108px, transparent 111px),
    radial-gradient(2.5px 2.5px at 18% 72%, #ffe58a 0 60%, transparent 100%),
    radial-gradient(2.5px 2.5px at 38% 82%, #ffe58a 0 60%, transparent 100%),
    radial-gradient(2.5px 2.5px at 63% 76%, #ffe58a 0 60%, transparent 100%),
    radial-gradient(2.5px 2.5px at 80% 86%, #ffe58a 0 60%, transparent 100%),
    """
    + _HEX_TILE
    + """ 0 0 / 56px 100px;
  -webkit-mask-image: linear-gradient(180deg, #000 0%, #000 60%, transparent 100%);
  mask-image: linear-gradient(180deg, #000 0%, #000 60%, transparent 100%);
}
.stApp::after {
  height: 30vh;
  background:
    radial-gradient(60% 70% at 15% 108%, #f6b21f 0 98%, transparent 100%),
    radial-gradient(70% 60% at 60% 110%, #e29a0d 0 98%, transparent 100%),
    radial-gradient(50% 75% at 100% 108%, #c9800a 0 98%, transparent 100%);
}
"""
)

# Components that belong to this arena only. They reuse the app's colour variables,
# so they follow the honey palette automatically.
_ARENA_CSS = """
<style>
/* Tabs (the app's global CSS does not style these) */
[data-baseweb="tab-list"] { gap: .4rem; border-bottom: 2px solid var(--line); }
button[data-baseweb="tab"] {
  border-radius: 14px 14px 0 0; padding: .55rem 1rem; background: transparent;
}
button[data-baseweb="tab"] p {
  font-family: 'Baloo 2', cursive !important; font-weight: 700; font-size: 1.05rem !important; color: var(--muted);
}
button[data-baseweb="tab"]:hover { background: var(--accent-soft); }
button[data-baseweb="tab"][aria-selected="true"] { background: var(--accent-soft); }
button[data-baseweb="tab"][aria-selected="true"] p { color: var(--accent-dark); }
[data-baseweb="tab-highlight"] { background: var(--accent) !important; height: 4px !important; border-radius: 4px; }
[data-baseweb="tab-border"] { background: transparent !important; }

/* Spelling answers are typed in the same handwriting face as the writing pad */
.stTextInput input { font-family: 'Patrick Hand', cursive !important; font-size: 1.3rem !important; letter-spacing: .02em; }

/* Lesson header */
.sp-title { font-family: 'Baloo 2', cursive; font-weight: 800; font-size: 1.5rem; color: var(--ink); line-height: 1.15; margin: .1rem 0 .4rem; }
.sp-meta { color: var(--muted); font-size: .94rem; margin-bottom: .6rem; }
.sp-rule-chip {
  display: inline-block; background: var(--accent-soft); color: var(--accent-dark); border: 1.5px solid var(--line);
  border-radius: 999px; font-weight: 800; font-size: .82rem; padding: .1rem .65rem; margin: 0 .3rem .25rem 0;
}
.sp-tip {
  display: flex; gap: .8rem; align-items: flex-start; background: #fffdf7; border: 1.5px solid var(--line);
  border-radius: 16px; padding: .8rem 1rem; margin: .7rem 0;
}
.sp-tip .sp-tip-icon { font-size: 2rem; line-height: 1; }
.sp-tip .sp-tip-name { font-weight: 800; color: var(--accent-dark); font-size: .9rem; }

/* Say-to-spell tiles */
.sp-say-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: .8rem; margin: .4rem 0 .9rem; }
.sp-say {
  background: #fff; border: 1.5px solid var(--line); border-bottom: 5px solid var(--accent);
  border-radius: 16px; padding: .8rem 1rem; box-shadow: 0 4px 12px rgba(40,34,90,.06);
}
.sp-say-word { font-family: 'Baloo 2', cursive; font-weight: 800; font-size: 1.5rem; color: var(--ink); line-height: 1.1; }
.sp-say-syl { font-family: 'Patrick Hand', cursive; font-size: 1.35rem; color: var(--accent-dark); margin: .15rem 0 .3rem; letter-spacing: .04em; }
.sp-say-cue { color: var(--muted); font-size: .92rem; line-height: 1.4; }

/* Phonogram sound cards */
.sp-ph-sym {
  display: inline-block; min-width: 68px; text-align: center; font-family: 'Baloo 2', cursive; font-weight: 800;
  font-size: 2.6rem; line-height: 1; color: var(--accent-dark); background: var(--accent-soft);
  border: 2px solid var(--line); border-radius: 18px; padding: .4rem .9rem .5rem;
}
.sp-chip {
  display: inline-block; background: var(--accent); color: #fff; font-weight: 800; font-size: .92rem;
  border-radius: 999px; padding: .12rem .65rem; margin: .45rem .25rem 0 0;
}
.sp-examples { color: var(--muted); font-size: .92rem; margin-top: .45rem; line-height: 1.4; }

/* Practice results */
.sp-result { border: 1.5px solid; border-left-width: 6px; border-radius: 16px; padding: .7rem 1rem; margin: .5rem 0; line-height: 1.5; }
.sp-result.ok  { background: #e3f7ec; border-color: #b9e6cf; border-left-color: #2f9e68; color: #1f6b47; }
.sp-result.bad { background: #fff0ee; border-color: #f3c9c2; border-left-color: #d6523c; color: #8f2b1b; }
.sp-result b { color: inherit; }
.sp-result code { background: rgba(255,255,255,.7); border-radius: 8px; padding: .05rem .4rem; font-weight: 800; }
.sp-stars { font-size: 1.7rem; letter-spacing: .1em; }

/* Suffix flowchart */
.sp-flow { display: flex; gap: .9rem; align-items: flex-start; background: #fff; border: 1.5px solid var(--line); border-radius: 16px; padding: .85rem 1rem; margin: .1rem 0 .55rem; }
.sp-flow-num {
  flex: 0 0 auto; width: 40px; height: 40px; border-radius: 50%; display: grid; place-items: center; color: #fff;
  font-family: 'Baloo 2', cursive; font-weight: 800; font-size: 1.2rem;
  background: linear-gradient(135deg, var(--accent-light), var(--accent)); box-shadow: 0 3px 0 var(--accent-dark);
}
.sp-flow-text { padding-top: .1rem; }
</style>
"""


# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------
def _md_inline(text) -> str:
    """Escape text for HTML, then keep simple **bold**, *italic* and `code` from the lesson data."""
    out = html.escape(str(text or ""), quote=False)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", out)
    out = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<i>\1</i>", out)
    return out


def _html(markup: str):
    st.markdown(markup, unsafe_allow_html=True)


def _banner(icon: str, title: str, sub: str):
    _html(
        f"""
        <div class="uni-hero">
          <div class="uni-hero-badge">{icon}</div>
          <div>
            <div class="uni-hero-title">{html.escape(title)}</div>
            <div class="uni-hero-sub">{html.escape(sub)}</div>
          </div>
        </div>
        """
    )


def _step_pill(text: str):
    _html(f'<div class="step-pill">{html.escape(text)}</div>')


def _stars(ratio: float) -> str:
    n = 3 if ratio >= 0.9 else 2 if ratio >= 0.7 else 1 if ratio >= 0.4 else 0
    return "⭐" * n + "☆" * (3 - n)


# ----------------------------------------------------------------------------
# Data access
# ----------------------------------------------------------------------------
@st.cache_data(ttl=600)
def fetch_phonograms(_supabase):
    if _supabase is None:
        return []
    try:
        res = _supabase.table("phonograms").select("*").order("sort_order").execute()
        return res.data or []
    except Exception as exc:
        print(f"[inky] spelling: could not read phonograms: {exc}")
        return []


@st.cache_data(ttl=600)
def fetch_spelling_lessons(_supabase, grade_band: str):
    if _supabase is None:
        return []
    try:
        query = _supabase.table("spelling_lessons").select("*").order("sort_order")
        if grade_band in ("lower", "upper"):
            query = query.eq("grade_band", grade_band)
        res = query.execute()
        return res.data or []
    except Exception as exc:
        print(f"[inky] spelling: could not read lessons: {exc}")
        return []


@st.cache_data(ttl=600)
def fetch_lesson_questions(_supabase, lesson_id: str):
    if _supabase is None:
        return []
    try:
        res = (
            _supabase.table("spelling_questions")
            .select("*")
            .eq("lesson_id", lesson_id)
            .execute()
        )
        return res.data or []
    except Exception as exc:
        print(f"[inky] spelling: could not read questions: {exc}")
        return []


def _parse_json_field(value, default):
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def _award_spelling_xp(supabase, user_id, lesson_id, score, total, xp_earned, award_xp=None,
                       log_activity=None, lesson_title=""):
    """Save the best score for a lesson and pay XP only for improvement.

    First attempt: full XP. Later attempts: XP only for the extra questions answered correctly,
    so retaking a drill cannot be used to farm XP. The best score is never lowered.
    """
    best_before, row_exists = 0, False
    if supabase is not None and user_id:
        try:
            res = (
                supabase.table("spelling_progress").select("best_score,completed")
                .eq("user_id", user_id).eq("lesson_id", lesson_id).execute()
            )
            if res.data:
                row_exists = True
                best_before = int(res.data[0].get("best_score") or 0)
        except Exception as exc:
            print(f"[inky] spelling: could not read earlier score: {exc}")

    if row_exists:
        gained = int(round(xp_earned * max(0, score - best_before) / score)) if score > best_before else 0
    else:
        gained = xp_earned
    if gained > 0:
        if callable(award_xp):
            award_xp(gained)  # the app's own function: updates session XP and the student's account
        else:
            st.session_state["xp"] = st.session_state.get("xp", 0) + gained

    if callable(log_activity):
        try:
            log_activity(
                "quiz", "Spelling & Phonics", lesson_title or str(lesson_id),
                score_or_grade=f"{score}/{total}", genre_or_skill=str(lesson_id), xp_earned=gained,
            )
        except Exception as exc:
            print(f"[inky] spelling: could not log activity: {exc}")

    if supabase is None or not user_id:
        return gained
    try:
        new_best = max(best_before, score)
        supabase.table("spelling_progress").upsert(
            {
                "user_id": user_id,
                "lesson_id": lesson_id,
                "best_score": new_best,
                "total_questions": total,
                "completed": (total > 0) and (new_best / total >= 0.8),
            },
            on_conflict="user_id,lesson_id",
        ).execute()
    except Exception as exc:
        print(f"[inky] spelling: could not save progress: {exc}")
    return gained


def _norm(text):
    """Compare answers fairly: ignore case, spare spaces and curly apostrophes."""
    t = str(text or "").replace("\u2019", "'").replace("\u2018", "'")
    return re.sub(r"\s+", " ", t).strip().lower()


# ----------------------------------------------------------------------------
# Phonogram deck
# ----------------------------------------------------------------------------
def render_phonogram_explorer(supabase, grade_band: str):
    st.subheader("🔤 Otis's 74 Basic Phonogram Sound Cards")
    st.caption(
        "Tap any phonogram card to see all of its sounds, sample words, and where it is allowed to appear."
    )

    phonograms = fetch_phonograms(supabase)
    if not phonograms:
        print("[inky] spelling: phonograms table is empty. Import phonograms_starter.csv.")
        st.info("The sound cards are being got ready. Come back soon!")
        return

    filtered = [p for p in phonograms if p.get("grade_band") in (grade_band, "both")]

    cols = st.columns(4)
    for idx, ph in enumerate(filtered):
        sounds = _parse_json_field(ph.get("sounds"), [])
        samples = _parse_json_field(ph.get("sample_words"), [])
        chips = "".join(f'<span class="sp-chip">{html.escape(str(s))}</span>' for s in sounds)
        with cols[idx % 4]:
            with st.container(border=True):
                _html(
                    f"""
                    <div class="sp-ph-sym">{html.escape(str(ph.get('symbol', '')))}</div>
                    <div>{chips}</div>
                    <div class="sp-examples">Examples: {html.escape(', '.join(str(s) for s in samples))}</div>
                    """
                )
                if ph.get("spelling_aid"):
                    with st.expander("Otis's Spelling Clue"):
                        st.write(ph["spelling_aid"])


# ----------------------------------------------------------------------------
# Lessons and practice
# ----------------------------------------------------------------------------
def render_lesson_and_practice(supabase, grade_band: str, user_id: str = None, award_xp=None, log_activity=None):
    lessons = fetch_spelling_lessons(supabase, grade_band)
    if not lessons:
        print("[inky] spelling: no lessons found. Import spelling_schema.sql and spelling_lessons_starter.csv.")
        st.info("The spelling lessons are being got ready. Come back soon!")
        return

    lesson_map = {l["lesson_id"]: l for l in lessons}
    ids = list(lesson_map)
    if st.session_state.get("sp_lesson_pick") not in ids:
        st.session_state.pop("sp_lesson_pick", None)
    picked_id = st.selectbox(
        "Choose a Spelling Rule Lesson:", ids, key="sp_lesson_pick",
        format_func=lambda i: f"Lesson {lesson_map[i]['lesson_number']}: {lesson_map[i]['title']} ({lesson_map[i]['target_grade']})",
    )
    lesson = lesson_map[picked_id]
    lesson_id = lesson["lesson_id"]

    # --- STEP 1: RULE CARD & SAY-TO-SPELL ---
    rules = _parse_json_field(lesson.get("rule_codes"), [])
    rule_chips = "".join(f'<span class="sp-rule-chip">{html.escape(str(r))}</span>' for r in rules)
    with st.container(border=True):
        _step_pill("Step 1 • Learn the rule")
        _html(
            f"""
            <div class="sp-title">🦉 {html.escape(str(lesson['title']))}</div>
            <div class="sp-meta">{rule_chips} &nbsp;Target level: <b>{html.escape(str(lesson['target_grade']))}</b></div>
            <div class="wagoll-box"><b>The Logic Rule:</b> {_md_inline(lesson['rule_statement'])}</div>
            <div class="sp-tip">
              <div class="sp-tip-icon">🦉</div>
              <div>
                <div class="sp-tip-name">Otis's Coach Tip</div>
                <div>{_md_inline(lesson['otis_tip'])}</div>
              </div>
            </div>
            """
        )

        examples = _parse_json_field(lesson.get("say_to_spell_examples"), [])
        if examples:
            st.markdown("#### 🗣️ Say-to-Spell Breakdown")
            tiles = "".join(
                f"""
                <div class="sp-say">
                  <div class="sp-say-word">{html.escape(str(ex.get('word', '')))}</div>
                  <div class="sp-say-syl">{html.escape(str(ex.get('syllables', '')))}</div>
                  <div class="sp-say-cue">{_md_inline(ex.get('cue', ''))}</div>
                </div>
                """
                for ex in examples
            )
            _html(f'<div class="sp-say-grid">{tiles}</div>')

        col_exc, col_dia = st.columns(2)
        with col_exc:
            if lesson.get("exceptions_note"):
                with st.expander("⚠️ True Exceptions to Watch"):
                    st.write(lesson["exceptions_note"])
        with col_dia:
            if lesson.get("dialect_note"):
                with st.expander("🌍 US vs. UK Spelling Note"):
                    st.write(lesson["dialect_note"])

    # --- STEP 2: POST-LESSON PRACTICE DRILL ---
    st.markdown("---")
    st.subheader("🎯 Post-Lesson Practice Drill")

    questions = fetch_lesson_questions(supabase, lesson_id)
    if not questions:
        print(f"[inky] spelling: no questions for lesson {lesson_id}. Add rows in spelling_questions.")
        st.info("The practice questions for this lesson are on their way. Try another lesson for now!")
        return

    quiz_key = f"sp_quiz_{lesson_id}"
    if quiz_key not in st.session_state:
        st.session_state[quiz_key] = {"submitted": False, "awarded": False, "answers": {}}

    state = st.session_state[quiz_key]

    with st.form(key=f"form_{lesson_id}"):
        for idx, q in enumerate(questions, start=1):
            qid = q["question_id"]
            qtype = q["question_type"]
            with st.container(border=True):
                _step_pill(f"Question {idx} of {len(questions)}")
                st.markdown(f"**{q['prompt']}**")

                if qtype in ("mcq", "true_false"):
                    opts = _parse_json_field(q.get("options"), ["True", "False"])
                    choice = st.radio(
                        f"Select answer for Q{idx}:",
                        opts,
                        key=f"ans_{qid}",
                        label_visibility="collapsed",
                    )
                    state["answers"][qid] = choice
                else:
                    typed = st.text_input(
                        f"Type your spelling for Q{idx}:",
                        key=f"ans_{qid}",
                        placeholder="Type the word carefully...",
                    )
                    state["answers"][qid] = typed.strip()

        submitted = st.form_submit_button("✅ Check My Spelling", use_container_width=True)
        if submitted:
            state["submitted"] = True

    if state["submitted"]:
        st.markdown("### 🐝 Your Results")
        score = 0
        xp_total = 0
        for idx, q in enumerate(questions, start=1):
            qid = q["question_id"]
            user_ans = _norm(state["answers"].get(qid, ""))
            correct = _norm(q["correct_answer"])
            explanation = _md_inline(q.get("explanation", ""))

            if user_ans == correct:
                score += 1
                xp_total += int(q.get("xp_value", 5))
                _html(
                    f'<div class="sp-result ok"><b>Q{idx}: Correct!</b> '
                    f'<code>{html.escape(str(q["correct_answer"]))}</code> — {explanation}</div>'
                )
            else:
                wrote = html.escape(str(state["answers"].get(qid, "") or "blank"))
                _html(
                    f'<div class="sp-result bad"><b>Q{idx}: Not quite.</b> You wrote <code>{wrote}</code> | '
                    f'Correct spelling: <code>{html.escape(str(q["correct_answer"]))}</code> — {explanation}</div>'
                )

        total = len(questions)
        ratio = score / total if total else 0
        st.metric("Lesson Score", f"{score} / {total}", f"+{xp_total} XP")
        _html(
            f"""
            <div class="xp-bar-wrap"><div class="xp-bar-fill" style="width:{int(ratio * 100)}%;"></div></div>
            <div class="sp-stars">{_stars(ratio)}</div>
            """
        )
        if ratio >= 0.8:
            st.success("Lesson mastered! Pick the next rule whenever you are ready.")
        else:
            st.info("Nearly there! Read the rule card again, then press Reset and try once more.")

        # Award once per attempt. Streamlit reruns this block on every click, so without
        # the flag the same XP would be added again each time the page refreshed.
        if not state.get("awarded"):
            gained = _award_spelling_xp(
                supabase, user_id, lesson_id, score, total, xp_total, award_xp=award_xp,
                log_activity=log_activity, lesson_title=str(lesson.get("title") or ""),
            )
            state["awarded"] = True
            state["gained"] = gained
        if state.get("gained") == 0 and xp_total > 0:
            st.caption("You have already earned XP for this lesson. Beat your best score to earn more!")

        if st.button("🔄 Reset Practice Drill", key=f"reset_{lesson_id}"):
            del st.session_state[quiz_key]
            st.rerun()


# ----------------------------------------------------------------------------
# Suffix helper
# ----------------------------------------------------------------------------
def render_suffix_helper():
    st.subheader("🧭 Otis's 3-Question Suffix Flowchart (Chapter 10)")
    st.write("Before adding any suffix to a base word, ask these 3 questions in order:")
    steps = [
        "**Does the base word end with a Silent Final E?** → Drop E before a *vowel* suffix **only if** C/G rules allow it (Rule 13).",
        "**Does it end with 1 Vowel + 1 Consonant (seen and heard)?** → Double the final consonant before a *vowel* suffix **only if** the syllable before the suffix is accented (Rule 14).",
        "**Does it end with a Single Vowel Y?** → Change Y to I before **any** suffix *unless* the suffix starts with I (Rules 15 & 16).",
    ]
    for n, text in enumerate(steps, start=1):
        _html(
            f'<div class="sp-flow"><div class="sp-flow-num">{n}</div>'
            f'<div class="sp-flow-text">{_md_inline(text)}</div></div>'
        )
    _html(
        '<div class="wagoll-box">If the answer to all three questions is <b>NO</b>, just add the suffix directly!</div>'
    )


# ----------------------------------------------------------------------------
# Arena entry point
# ----------------------------------------------------------------------------
def render_spelling_arena(supabase=None, user_id: str = None, bubble=None, award_xp=None, log_activity=None):
    """
    bubble:   optional render_inky_bubble from app.py, for Inky's welcome message.
    award_xp: optional award_xp from app.py, so XP is saved to the student's account.
    """
    _html(_ARENA_CSS)
    _banner(
        "🐝",
        "Spelling & Phonics Arena",
        "Master the 74 phonograms and 30 spelling rules with Otis. No guessing, no random sight-word memorization!",
    )
    if callable(bubble):
        bubble("Choose your track, read the rule, then buzz through the practice drill to earn XP!")

    if st.session_state.get("sp_band") not in ("lower", "upper"):
        st.session_state["sp_band"] = "upper" if str(st.session_state.get("age_band", "")).startswith("Upper") else "lower"
    band_choice = st.radio(
        "Select Grade Level Track:",
        options=["lower", "upper"],
        key="sp_band",
        format_func=lambda b: "Lower Primary (Grades 1–3: Foundations)"
        if b == "lower"
        else "Upper Primary (Grades 4–6: Multisyllable & Suffix Logic)",
        horizontal=True,
    )

    tab_lessons, tab_phonograms, tab_suffix_checker = st.tabs(
        ["📚 Rule Lessons & Practice", "🔤 74 Phonogram Deck", "🧭 Suffix Decision Helper"]
    )

    with tab_lessons:
        render_lesson_and_practice(supabase, band_choice, user_id=user_id, award_xp=award_xp, log_activity=log_activity)

    with tab_phonograms:
        render_phonogram_explorer(supabase, band_choice)

    with tab_suffix_checker:
        render_suffix_helper()
