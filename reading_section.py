import html
import random

import streamlit as st

from reading_content import (
    EXAM_TEXTS,
    GROUPS,
    LANGUAGE_SKILLS,
    PRACTICE,
    READING_SKILLS,
    SKILLS,
    SKILL_BY_ID,
)

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

# ------------------------------------------------------------------
# Look and atmosphere for the Reading section: an ocean reef
# (app.py picks this up and applies it when the student opens Reading)
# ------------------------------------------------------------------
READING_UNIVERSE_CSS = """
:root { --accent:#0369a1; --accent-light:#0b84c6; --accent-dark:#075985; --accent-soft:#e0f2fe; --hero-a:#075985; --hero-b:#1aa6c9; }
.stApp { background: linear-gradient(180deg, #082f5c 0%, #0b5a94 38%, #1b97c4 72%, #7fd6e0 100%) !important; }
.stApp::before {
  background:
    radial-gradient(circle 9px at 12% 78%, transparent 58%, rgba(255,255,255,.55) 62% 72%, transparent 76%),
    radial-gradient(circle 6px at 18% 64%, transparent 58%, rgba(255,255,255,.5) 62% 72%, transparent 76%),
    radial-gradient(circle 12px at 84% 70%, transparent 58%, rgba(255,255,255,.55) 62% 72%, transparent 76%),
    radial-gradient(circle 7px at 90% 52%, transparent 58%, rgba(255,255,255,.5) 62% 72%, transparent 76%),
    radial-gradient(circle 5px at 70% 84%, transparent 58%, rgba(255,255,255,.5) 62% 72%, transparent 76%),
    radial-gradient(circle 8px at 30% 90%, transparent 58%, rgba(255,255,255,.5) 62% 72%, transparent 76%),
    repeating-conic-gradient(from 160deg at 50% -12%, rgba(255,255,255,.13) 0deg 4deg, transparent 4deg 13deg);
  -webkit-mask-image: linear-gradient(180deg, #000 0%, #000 55%, transparent 100%);
  mask-image: linear-gradient(180deg, #000 0%, #000 55%, transparent 100%);
}
.stApp::after {
  height: 30vh;
  background:
    radial-gradient(ellipse 16px 110px at 6vw 100%, #1f9d6a 0 98%, transparent 100%),
    radial-gradient(ellipse 14px 80px at 8.4vw 100%, #2fbf80 0 98%, transparent 100%),
    radial-gradient(ellipse 18px 130px at 22vw 100%, #178a5c 0 98%, transparent 100%),
    radial-gradient(circle 46px at 40vw 94%, #ff8fa3 0 98%, transparent 100%),
    radial-gradient(circle 34px at 43.5vw 98%, #ff6f91 0 98%, transparent 100%),
    radial-gradient(ellipse 15px 120px at 62vw 100%, #1f9d6a 0 98%, transparent 100%),
    radial-gradient(ellipse 14px 90px at 64.5vw 100%, #2fbf80 0 98%, transparent 100%),
    radial-gradient(circle 40px at 78vw 96%, #ffb86b 0 98%, transparent 100%),
    radial-gradient(ellipse 18px 140px at 90vw 100%, #178a5c 0 98%, transparent 100%),
    radial-gradient(90% 26% at 30% 100%, #e6c987 0 98%, transparent 100%),
    radial-gradient(80% 22% at 85% 100%, #d9b873 0 98%, transparent 100%);
}
"""

STAGE_MAP = {
    "Lower Primary (Stage 3)": "lower",
    "Upper Primary (Stage 5)": "upper",
}
PAPERS = {
    "Paper 1: Non-fiction": ["non-fiction"],
    "Paper 2: Fiction": ["fiction", "playscript"],
    "Both papers (non-fiction and fiction)": ["non-fiction", "fiction", "playscript"],
}
DIFFICULTY = {"Gentler": 1, "Balanced": 2, "Stretching": 3}


# ------------------------------------------------------------------
# Small helpers
# ------------------------------------------------------------------
def _chip(text: str) -> str:
    return f'<span class="badge-chip">{html.escape(str(text))}</span>'


def _norm(text: str) -> str:
    return (
        str(text or "")
        .lower()
        .replace("\u2019", "'").replace("\u2018", "'")
        .replace("\u201c", '"').replace("\u201d", '"')
        .strip()
    )


def _html_text(text: str) -> str:
    return html.escape(text).replace("\n", "<br>")


def _passage_card(title: str, genre: str, text: str) -> None:
    st.markdown(
        f"""
        <div class="adventure-card">
            <div class="step-pill">{html.escape(genre.title())}</div>
            <div style="font-weight:800;font-size:1.15rem;margin:.1rem 0 .5rem 0;">{html.escape(title)}</div>
            <div style="line-height:1.7;">{_html_text(text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _model_answer(q: dict) -> str:
    kind = q["kind"]
    if kind == "multi":
        return "; ".join(q["ans"])
    if kind == "order":
        pairs = sorted(zip(q["ans"], q["opts"]))
        return "  ".join(f"{n}. {item}" for n, item in pairs)
    if kind == "match":
        left, _right = q["opts"]
        return "; ".join(f"{a} → {b}" for a, b in zip(left, q["ans"]))
    return str(q["ans"])


# ------------------------------------------------------------------
# Asking and marking questions
# ------------------------------------------------------------------
def _ask(q: dict, number: int, prefix: str):
    """Shows one question and returns the student's answer."""
    key = f"{prefix}_{q['id']}"
    marks = q["marks"]
    st.markdown(f"**{number}.** {q['q']}  <span style='opacity:.7'>[{marks} mark{'s' if marks != 1 else ''}]</span>",
                unsafe_allow_html=True)
    kind = q["kind"]
    if kind == "mcq":
        return st.radio("Answer", q["opts"], index=None, key=key, label_visibility="collapsed")
    if kind == "multi":
        return st.multiselect("Answer", q["opts"], key=key, label_visibility="collapsed")
    if kind == "order":
        picks = []
        choices = ["-"] + list(range(1, len(q["opts"]) + 1))
        for i, item in enumerate(q["opts"]):
            picks.append(st.selectbox(item, choices, key=f"{key}_{i}"))
        return picks
    if kind == "match":
        left, right = q["opts"]
        picks = []
        for i, item in enumerate(left):
            picks.append(st.selectbox(item, ["-"] + right, key=f"{key}_{i}"))
        return picks
    if marks >= 2:
        return st.text_area("Answer", key=key, height=80, label_visibility="collapsed")
    return st.text_input("Answer", key=key, label_visibility="collapsed")


def _grade(q: dict, ans):
    """Returns (marks earned, verdict). Verdict is correct / partly / wrong / check / right-looking."""
    marks, kind = q["marks"], q["kind"]
    if kind == "mcq":
        ok = ans == q["ans"]
        return (marks, "correct") if ok else (0, "wrong")
    if kind == "multi":
        picked = set(ans or [])
        good = len(picked & set(q["ans"]))
        bad = len(picked - set(q["ans"]))
        earned = max(0, good - bad)
        return earned, ("correct" if earned == marks else "partly" if earned else "wrong")
    if kind in ("order", "match"):
        expected = q["ans"]
        got = list(ans or [])
        right = sum(1 for a, b in zip(got, expected) if a == b)
        if right == len(expected):
            return marks, "correct"
        earned = int(marks * right / len(expected))
        return earned, ("partly" if earned else "wrong")
    hit = any(k.lower() in _norm(ans) for k in q["acc"])
    return (marks, "looks right") if hit else (0, "check")


def _feedback(q: dict, earned: int, verdict: str) -> None:
    model = _model_answer(q)
    if verdict == "correct":
        st.success(f"✅ Correct! {earned}/{q['marks']}")
    elif verdict == "looks right":
        st.success(f"✅ Looks right. Check it against the model answer: {model}")
    elif verdict == "partly":
        st.warning(f"🟡 Partly right: {earned}/{q['marks']}. Model answer: {model}")
    elif verdict == "check":
        st.info(f"🔎 Compare your answer with the model answer: {model}. Written answers should be checked by a teacher or parent.")
    else:
        st.error(f"❌ Not quite. Model answer: {model}")


def _run_quiz(blocks: list, prefix: str, state_prefix: str, button_label: str):
    """Shows blocks (each with optional heading, text and questions) as one form and marks it.

    Returns (earned, total, checked)."""
    ver = st.session_state.setdefault(f"{state_prefix}_ver", 0)
    checked_key = f"{state_prefix}_checked"
    checked = st.session_state.get(checked_key, False)
    form_prefix = f"{prefix}_{ver}"

    summary = st.container()
    earned_total, marks_total = 0, 0

    with st.form(form_prefix):
        number = 0
        for block in blocks:
            if block.get("heading"):
                st.markdown(f"### {block['heading']}")
            if block.get("text"):
                _passage_card(block.get("title", ""), block.get("genre", "text"), block["text"])
            for q in block["qs"]:
                number += 1
                ans = _ask(q, number, form_prefix)
                marks_total += q["marks"]
                if checked:
                    earned, verdict = _grade(q, ans)
                    earned_total += earned
                    _feedback(q, earned, verdict)
                st.markdown("---")
        submitted = st.form_submit_button(button_label, type="primary")

    if submitted:
        st.session_state[checked_key] = True
        st.rerun()

    if checked:
        with summary:
            pct = round(100 * earned_total / marks_total) if marks_total else 0
            st.markdown(f"#### Score: {earned_total} / {marks_total} ({pct}%)")
            st.caption("Written answers are marked by matching key words, so please check them against the model answers.")
    if checked and st.button("Start again", key=f"{form_prefix}_reset"):
        st.session_state[f"{state_prefix}_ver"] = ver + 1
        st.session_state[checked_key] = False
        st.rerun()
    return earned_total, marks_total, checked


# ------------------------------------------------------------------
# Subsection 1: Skill practice
# ------------------------------------------------------------------
def _render_skill_practice(band: str, stage_label: str) -> None:
    st.subheader("Skill Practice")
    st.caption("Pick a skill, read the tips, then try a short reading with questions.")

    group_labels = {"all": "All skills"}
    group_labels.update({gid: name for gid, name in GROUPS})
    group = st.selectbox("Skill group", list(group_labels), format_func=lambda g: group_labels[g], key=f"rd_group_{band}")
    options = [s for s in SKILLS if group == "all" or s["group"] == group]
    skill_id = st.selectbox(
        "Skill",
        [s["id"] for s in options],
        format_func=lambda i: f"{SKILL_BY_ID[i]['icon']} {SKILL_BY_ID[i]['name']}",
        key=f"rd_skill_{band}_{group}",
    )
    skill = SKILL_BY_ID[skill_id]
    best = st.session_state.get("reading_best", {}).get((skill_id, band))

    chips = _chip("From my Year 4 guide" if skill["src"] == "guide" else "Added from the Cambridge framework")
    chips += _chip(f"Objectives: {skill['objs'][band]}")
    if best is not None:
        chips += _chip(f"Best score: {best}%")
    st.markdown(
        f"""
        <div class="adventure-card">
            <div class="step-pill">{html.escape(stage_label)}</div>
            <div style="font-weight:800;font-size:1.2rem;margin:.1rem 0 .3rem 0;">{skill['icon']} {html.escape(skill['name'])}</div>
            <div>{html.escape(skill['blurb'])}</div>
            <div style="margin-top:.5rem;">{chips}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("How to tackle it", expanded=True):
        for tip in skill["tips"][band]:
            st.markdown(f"- {tip}")

    sets = PRACTICE.get((skill_id, band), [])
    if not sets:
        st.info("No practice readings for this skill and stage yet.")
        return
    if len(sets) > 1:
        idx = st.radio("Reading", range(len(sets)), format_func=lambda i: sets[i]["title"], horizontal=True,
                       key=f"rd_set_{skill_id}_{band}")
    else:
        idx = 0
    chosen = sets[idx]

    blocks = [{"title": chosen["title"], "genre": chosen["genre"], "text": chosen["text"], "qs": chosen["qs"]}]
    earned, total, checked = _run_quiz(
        blocks, prefix=f"pr_{chosen['id']}", state_prefix=f"pr_{chosen['id']}", button_label="Check my answers"
    )
    if checked and total:
        scores = st.session_state.setdefault("reading_best", {})
        pct = round(100 * earned / total)
        scores[(skill_id, band)] = max(pct, scores.get((skill_id, band), 0))


# ------------------------------------------------------------------
# Subsection 2: Mock exams
# ------------------------------------------------------------------
def _pick_questions(candidates: list, budget: int, desired_level: int, rng: random.Random) -> list:
    """Picks questions (text_index, question) up to a mark budget, preferring the wanted difficulty."""
    ranked = sorted(candidates, key=lambda c: abs(c[1]["level"] - desired_level) + rng.random() * 0.9)
    chosen, used = [], 0
    for item in ranked:
        marks = item[1]["marks"]
        if used + marks <= budget:
            chosen.append(item)
            used += marks
    return chosen


def build_mock_exam(band: str, paper: str, target_marks: int, skills: list, difficulty: str,
                    language_marks: int, seed: int) -> dict:
    """Builds a mock exam from the question banks and returns blocks plus summary numbers."""
    rng = random.Random(seed)
    desired = DIFFICULTY[difficulty]
    reading_skills = [s for s in skills if s in READING_SKILLS]
    language_skills = [s for s in skills if s in LANGUAGE_SKILLS]
    if not language_skills:
        language_marks = 0
    if not reading_skills:
        language_marks = target_marks
    reading_budget = max(0, target_marks - language_marks)

    sections = []
    wanted_genres = PAPERS[paper]
    groups = [("Paper 1: Non-fiction", ["non-fiction"]), ("Paper 2: Fiction", ["fiction", "playscript"])]
    groups = [g for g in groups if set(g[1]) & set(wanted_genres)]
    per_group = reading_budget // len(groups) if groups else 0

    for name, genres in groups:
        texts = [t for t in EXAM_TEXTS[band] if t["genre"] in genres]
        cands = [(ti, q) for ti, t in enumerate(texts) for q in t["qs"] if q["skill"] in reading_skills]
        picked = _pick_questions(cands, per_group, desired, rng) if reading_skills else []
        blocks = []
        for ti, t in enumerate(texts):
            qs = [q for (i, q) in picked if i == ti]
            if qs:
                blocks.append({"title": t["title"], "genre": t["genre"], "text": t["text"], "qs": qs})
        if blocks:
            for k, b in enumerate(blocks):
                b["heading"] = (f"{name}: Text {chr(65 + k)}" if len(groups) > 1 else f"Text {chr(65 + k)}")
            sections.extend(blocks)

    if language_marks and language_skills:
        sets = [s for sk in language_skills for s in PRACTICE.get((sk, band), [])]
        rng.shuffle(sets)
        cands = [(si, q) for si, s in enumerate(sets) for q in s["qs"]]
        picked = _pick_questions(cands, language_marks, desired, rng)
        first = True
        for si, s in enumerate(sets):
            qs = [q for (i, q) in picked if i == si]
            if qs:
                sections.append({
                    "heading": "Language Section" if first else "",
                    "title": s["title"], "genre": s["genre"], "text": s["text"], "qs": qs,
                })
                first = False

    total = sum(q["marks"] for b in sections for q in b["qs"])
    count = sum(len(b["qs"]) for b in sections)
    minutes = max(10, int(round(total * 0.9 / 5.0) * 5))
    used = sorted({q["skill"] for b in sections for q in b["qs"]})
    return {"blocks": sections, "total": total, "count": count, "minutes": minutes, "skills": used,
            "requested": target_marks, "band": band, "paper": paper}


def _safe_pdf_text(text: str) -> str:
    replacements = {
        "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2026": "...", "\u2022": "-", "\u2192": "->",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _build_mock_pdf(spec: dict, title: str, include_key: bool) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def line(text: str, size: int = 10, style: str = "", h: float = 5.5):
        pdf.set_font("Helvetica", style, size)
        pdf.multi_cell(0, h, _safe_pdf_text(text), new_x="LMARGIN", new_y="NEXT")

    stage_label = "Lower Primary (Stage 3)" if spec["band"] == "lower" else "Upper Primary (Stage 5)"
    line(title, 16, "B", 9)
    line(f"{stage_label}  |  {spec['paper']}", 11)
    line(f"Time allowed: {spec['minutes']} minutes    Total marks: {spec['total']}", 11)
    line("Name: ___________________________    Date: _______________", 11)
    line("Answer all the questions. Read each text carefully before you answer.", 10, "I")
    pdf.ln(3)

    number = 0
    for block in spec["blocks"]:
        if block.get("heading"):
            pdf.ln(2)
            line(block["heading"], 13, "B", 8)
        line(block["title"], 11, "B", 7)
        line(block["text"], 10, "", 5.5)
        pdf.ln(3)
        for q in block["qs"]:
            number += 1
            line(f"{number}. {q['q']}  [{q['marks']} mark{'s' if q['marks'] != 1 else ''}]", 10, "B", 6)
            kind = q["kind"]
            if kind in ("mcq", "multi"):
                hint = "Tick ONE box." if kind == "mcq" else f"Tick {len(q['ans'])} boxes."
                line(hint, 9, "I", 5)
                for opt in q["opts"]:
                    line(f"[   ]  {opt}", 10, "", 6)
            elif kind == "order":
                for item in q["opts"]:
                    line(f"[   ]  {item}", 10, "", 6)
            elif kind == "match":
                left, right = q["opts"]
                line("Choose from: " + " / ".join(right), 9, "I", 5)
                for item in left:
                    line(f"{item}  ->  ______________________", 10, "", 7)
            else:
                for _ in range(q["marks"] + 1):
                    line("_" * 86, 10, "", 7)
            pdf.ln(3)

    if include_key:
        pdf.add_page()
        line("Answer key and marking guide", 15, "B", 9)
        number = 0
        for block in spec["blocks"]:
            for q in block["qs"]:
                number += 1
                line(f"{number}. [{q['marks']}]  {_model_answer(q)}", 10, "", 6)
                if q["kind"] == "short" and q["acc"]:
                    line("    Accept answers such as: " + ", ".join(q["acc"]), 9, "I", 5)

    out = pdf.output()
    return bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode("latin-1")


def _render_mock_exams(band: str, stage_label: str) -> None:
    st.subheader("Mock Exams")
    st.caption("Set the exam up, build it, then take it on screen or download it as a printable PDF.")

    c1, c2 = st.columns(2)
    with c1:
        paper = st.selectbox("Paper", list(PAPERS), key=f"mock_paper_{band}")
        target = st.slider("Total marks", 10, 50, 30, step=5, key=f"mock_marks_{band}",
                           help="The question bank may hold fewer matching marks than you ask for.")
        difficulty = st.select_slider("Difficulty", list(DIFFICULTY), value="Balanced", key=f"mock_diff_{band}")
    with c2:
        quick = st.selectbox("Skills", ["All skills", "Reading skills only", "Language skills only", "Pick my own"],
                             key=f"mock_quick_{band}")
        if quick == "All skills":
            skills = [s["id"] for s in SKILLS]
        elif quick == "Reading skills only":
            skills = list(READING_SKILLS)
        elif quick == "Language skills only":
            skills = list(LANGUAGE_SKILLS)
        else:
            skills = st.multiselect("Choose skills", [s["id"] for s in SKILLS],
                                    default=[s["id"] for s in SKILLS],
                                    format_func=lambda i: f"{SKILL_BY_ID[i]['icon']} {SKILL_BY_ID[i]['name']}",
                                    key=f"mock_pick_{band}")
        lang_marks = st.slider("Marks for the Language Section", 0, 15, 10, step=5, key=f"mock_lang_{band}",
                               help="Grammar, punctuation, vocabulary and sentence questions.")
        seed = st.number_input("Version number", 1, 999, 1, key=f"mock_seed_{band}",
                               help="Change this to get a different mix of questions.")
    title = st.text_input("Exam title", value=f"{stage_label} Reading Mock Exam", key=f"mock_title_{band}")
    include_key = st.checkbox("Include the answer key in the PDF", value=True, key=f"mock_key_{band}")

    state_key = f"reading_mock_{band}"
    if st.button("Build mock exam", type="primary", key=f"mock_build_{band}"):
        if not skills:
            st.warning("Choose at least one skill.")
        else:
            st.session_state[state_key] = build_mock_exam(band, paper, target, skills, difficulty, lang_marks, int(seed))
            st.session_state[f"{state_key}_n"] = st.session_state.get(f"{state_key}_n", 0) + 1
            st.session_state.pop(f"mock_{band}_checked", None)

    spec = st.session_state.get(state_key)
    if not spec:
        return
    if not spec["blocks"]:
        st.warning("No questions match those choices. Try more skills or a different paper.")
        return

    st.markdown(
        _chip(f"{spec['count']} questions") + _chip(f"{spec['total']} marks") + _chip(f"{spec['minutes']} minutes"),
        unsafe_allow_html=True,
    )
    if spec["total"] < spec["requested"]:
        st.caption(
            f"This exam has {spec['total']} marks, fewer than the {spec['requested']} you asked for, because that is all the "
            "question bank holds for these choices. Add more texts to EXAM_TEXTS in reading_content.py to raise it."
        )
    st.caption("Skills covered: " + ", ".join(SKILL_BY_ID[s]["name"] for s in spec["skills"]))

    if FPDF_AVAILABLE:
        pdf_bytes = _build_mock_pdf(spec, title.strip() or "Reading Mock Exam", include_key)
        st.download_button("Download printable PDF", pdf_bytes, file_name=f"reading_mock_{band}.pdf",
                           mime="application/pdf", key=f"mock_dl_{band}_{st.session_state.get(state_key + '_n', 0)}")
    else:
        st.warning("Install `fpdf2` (`pip install fpdf2`) to download the exam as a PDF.")

    st.markdown("---")
    st.markdown(f"## {title.strip() or 'Reading Mock Exam'}")
    _run_quiz(spec["blocks"], prefix=f"mock_{band}_{st.session_state.get(state_key + '_n', 0)}",
              state_prefix=f"mock_{band}", button_label="Mark my exam")


# ------------------------------------------------------------------
# Entry point (called from app.py)
# ------------------------------------------------------------------
def render_reading_section(taxonomy_path: str = "reading_taxonomy.json", bubble=None) -> None:
    """Renders the Reading section with two subsections: Skill Practice and Mock Exams.

    taxonomy_path is kept so existing calls in app.py keep working; it is no longer used.
    bubble: optional function from app.py that shows Inky's speech bubble.
    """
    intro = "Practise one reading skill at a time, or build a mock exam to test them all."
    if bubble:
        bubble(intro)
    else:
        st.info(intro)
    st.markdown("## 📖 Reading")

    # start on the student's own stage; they can still switch
    age = str(st.session_state.get("age_band", "")).lower()
    if st.session_state.get("reading_age_band") != age:
        st.session_state["reading_age_band"] = age
        st.session_state["reading_section_stage"] = (
            "Lower Primary (Stage 3)" if age.startswith("lower") else "Upper Primary (Stage 5)"
        )
    st.session_state.setdefault("reading_section_stage", "Upper Primary (Stage 5)")

    stage_label = st.radio("Stage", list(STAGE_MAP.keys()), horizontal=True, key="reading_section_stage")
    band = STAGE_MAP[stage_label]

    tab_skill, tab_mock = st.tabs(["🎯 Skill Practice", "📝 Mock Exams"])
    with tab_skill:
        _render_skill_practice(band, stage_label)
    with tab_mock:
        _render_mock_exams(band, stage_label)
