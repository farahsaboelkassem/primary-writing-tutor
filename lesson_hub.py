"""Shared lesson screens for The Writing Adventure.

One screen design, used by both Language Arts and Grammar & Punctuation:

    level buttons  ->  (topic cards)  ->  lesson cards  ->  lesson  ->  practice  ->  results

A level without "topics" (Language Arts) goes straight from level to lesson cards.
A level with "topics" (Grammar & Punctuation) shows topic cards first.

Each section passes a small config dictionary (see render_hub). All progress is kept in
st.session_state under keys that start with the section's prefix.
"""
import random
import re

import streamlit as st

LEVEL_ICONS = {"lower": "🌱", "upper": "🌳"}


def md(text):
    """Lesson text as markdown. Keeps **bold** and protects ___ gaps."""
    return str(text).replace("___", "\\_\\_\\_")


def plain(text):
    """Escape markdown so answer options always show as plain text."""
    return re.sub(r"([\\`*_{}\[\]()#+!|<>~])", r"\\\1", str(text or ""))


def _k(c, name):
    return f"{c['prefix']}_{name}"


def _go(c, topic="keep", lesson="keep", run="keep"):
    """Move to another screen. 'keep' leaves that part of the position as it is."""
    if topic != "keep":
        st.session_state[_k(c, "topic")] = topic
    if lesson != "keep":
        st.session_state[_k(c, "lesson")] = lesson
    if run != "keep":
        st.session_state[_k(c, "run")] = run


def level_key_for(c, level_key, lesson_id):
    return f"{level_key}::{lesson_id}"


TYPE_LABELS = {
    "multiple_choice": "Choose the answer",
    "true_false": "True or false?",
    "fill_blank": "Type your answer",
}


def normalise(text, case_sensitive=False):
    """Make typed answers fair to compare: tidy spaces, treat curly and straight quotes alike."""
    t = str(text or "")
    t = t.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    t = re.sub(r"\s+", " ", t).strip()
    return t if case_sensitive else t.casefold()


def is_correct(q, given):
    if q.get("type") == "fill_blank":
        cs = bool(q.get("case_sensitive"))
        accepted = q.get("accepted") or [q["correct"]]
        return normalise(given, cs) in {normalise(a, cs) for a in accepted}
    return given == q["correct"]


def builtin_questions(lesson):
    """A lesson's own questions. The codes match the question bank seed file (lesson_id-01, -02 ...)."""
    out = []
    for n, q in enumerate(lesson["questions"], start=1):
        out.append({"code": f"{lesson['id']}-{n:02d}", "type": "multiple_choice", "kind": q["kind"], "q": q["q"],
                    "options": list(q["options"]), "correct": q["options"][0], "why": q["why"]})
    return out


def source_questions(c, lesson):
    """Questions for a new run: from the section's question source if it has any, else the built-ins."""
    source = c.get("question_source")
    if source:
        try:
            questions = source(lesson)
            if questions:
                return questions
        except Exception as exc:
            print(f"[inky] question source failed, using built-in questions: {exc}")
    return builtin_questions(lesson)


def prepare_question(q):
    """Copy a question and shuffle its answers (true/false keeps its order; typed answers have none)."""
    out = dict(q)
    out.setdefault("type", "multiple_choice")
    out.setdefault("correct", out["options"][0] if out.get("options") else "")
    if out["type"] == "multiple_choice":
        options = list(out["options"])
        random.shuffle(options)
        out["options"] = options
    elif out["type"] == "true_false":
        out["options"] = ["True", "False"]
    else:
        out["options"] = []
    return out


def new_run(level, lesson, questions):
    """Fresh practice run from the given questions, in a random order."""
    prepared = [prepare_question(q) for q in questions]
    random.shuffle(prepared)
    return {
        "id": "%06x" % random.randrange(16 ** 6), "level": level, "lesson_id": lesson["id"],
        "questions": prepared, "index": 0, "score": 0, "checked": False, "choice": None,
        "answers": [], "saved": False,
    }


# ------------------------------------------------------------------
# Level buttons
# ------------------------------------------------------------------
def level_picker(c):
    levels, p = c["levels"], c["prefix"]
    stage = c["stage"]() if callable(c.get("stage")) else ""
    if st.session_state.get(_k(c, "age_band")) != stage:  # start on the student's own level
        st.session_state[_k(c, "age_band")] = stage
        st.session_state[_k(c, "level")] = "lower" if str(stage).lower().startswith("lower") else "upper"
        _go(c, topic=None, lesson=None, run=None)
    st.session_state.setdefault(_k(c, "level"), "upper")
    current = st.session_state[_k(c, "level")]

    cols = st.columns(len(levels))
    for col, (key, lvl) in zip(cols, levels.items()):
        with col:
            label = f"{LEVEL_ICONS.get(key, '📘')} {lvl['label']}"
            if st.button(label, key=f"{p}_levelbtn_{key}", use_container_width=True,
                         type="primary" if key == current else "secondary"):
                if key != current:
                    st.session_state[_k(c, "level")] = key
                    _go(c, topic=None, lesson=None, run=None)
                    st.rerun()
    if levels[current].get("stages"):
        st.caption(f"Framework: {levels[current]['stages']}")
    return st.session_state[_k(c, "level")]


# ------------------------------------------------------------------
# Topic cards and lesson cards
# ------------------------------------------------------------------
def _practised(c, level_key, lessons):
    best = st.session_state.setdefault(_k(c, "best"), {})
    return sum(1 for l in lessons if best.get(level_key_for(c, level_key, l["id"]), {}).get("tries"))


def topic_grid(c, level_key, level):
    p = c["prefix"]
    lessons = level["lessons"]
    done = _practised(c, level_key, lessons)
    st.progress(done / max(len(lessons), 1), text=f"{done} of {len(lessons)} lessons practised")
    st.markdown("#### Choose a topic")
    cols = st.columns(2)
    for i, topic in enumerate(level["topics"]):
        with cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"### {topic['emoji']} {topic['title']}")
                st.caption(topic["blurb"])
                n = len(topic["lessons"])
                d = _practised(c, level_key, topic["lessons"])
                st.progress(d / max(n, 1), text=f"{d} of {n} lessons practised")
                if st.button("Open topic", key=f"{p}_topic_{level_key}_{topic['id']}",
                             use_container_width=True, type="primary"):
                    _go(c, topic=topic["id"], lesson=None, run=None)
                    st.rerun()


def lesson_list(c, level_key, lessons, topic=None):
    p = c["prefix"]
    best = st.session_state.setdefault(_k(c, "best"), {})
    if topic:
        if st.button("← All topics", key=f"{p}_back_topics"):
            _go(c, topic=None, lesson=None, run=None)
            st.rerun()
        st.markdown(f"## {topic['emoji']} {topic['title']}")
        st.caption(topic["blurb"])
    done = _practised(c, level_key, lessons)
    st.progress(done / max(len(lessons), 1), text=f"{done} of {len(lessons)} lessons practised")
    cols = st.columns(2)
    for i, lesson in enumerate(lessons):
        with cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"### {lesson['emoji']} {lesson['title']}")
                st.caption(lesson["blurb"])
                prog = best.get(level_key_for(c, level_key, lesson["id"]))
                if prog and prog.get("tries"):
                    medal = " 🏅" if prog["best"] >= prog["total"] else ""
                    st.markdown(f"⭐ Best score: **{prog['best']} / {prog['total']}**{medal}")
                else:
                    st.caption("Not started yet")
                st.caption("Framework: " + " · ".join(lesson["codes"]))
                if st.button("Open lesson", key=f"{p}_open_{lesson['id']}", use_container_width=True, type="primary"):
                    _go(c, lesson=lesson["id"], run=None)
                    st.rerun()


# ------------------------------------------------------------------
# Lesson page: teach, practise, results
# ------------------------------------------------------------------
def teach(lesson):
    st.markdown(f"**{md(lesson['intro'])}**")
    for rule in lesson["rules"]:
        with st.container(border=True):
            st.markdown(f"**{md(rule['title'])}**")
            st.markdown(md(rule["text"]))
            for example in rule.get("examples", []):
                st.markdown(f"- *{md(example)}*")
    if lesson.get("tip"):
        st.info(f"💡 {lesson['tip']}")


def question(c, run):
    p = c["prefix"]
    questions, idx = run["questions"], run["index"]
    q = questions[idx]
    qtype = q.get("type", "multiple_choice")
    st.progress(idx / len(questions), text=f"Question {idx + 1} of {len(questions)}")
    skill = "🔍 Spot it" if q["kind"] == "spot" else "✍️ Use it"
    st.caption(f"{skill} · {TYPE_LABELS.get(qtype, '')}")
    st.markdown(f"#### {md(q['q'])}")
    widget_key = f"{p}_choice_{run['id']}_{idx}"

    if not run["checked"]:
        if qtype == "fill_blank":
            choice = st.text_input("Type your answer", key=widget_key, label_visibility="collapsed",
                                   placeholder="Type your answer here")
            empty = not str(choice or "").strip()
        else:
            choice = st.radio("Choose your answer", q["options"], index=None, key=widget_key,
                              label_visibility="collapsed")
            empty = choice is None
        if st.button("Check answer", type="primary", use_container_width=True, key=f"{p}_check_{run['id']}_{idx}"):
            if empty:
                st.warning("Type an answer first." if qtype == "fill_blank" else "Choose an answer first.")
                return
            correct = is_correct(q, choice)
            run["answers"].append({"q": q["q"], "chosen": choice, "correct_text": q["correct"], "correct": correct,
                                   "why": q["why"], "code": q.get("code"), "type": qtype})
            if correct:
                run["score"] += 1
            run["checked"], run["choice"] = True, choice
            st.rerun()
        return

    last = run["answers"][-1]
    if qtype == "fill_blank":
        if last["correct"]:
            st.markdown(f"✅ **{plain(run['choice'])}**")
        else:
            st.markdown(f"❌ {plain(run['choice'])}")
            st.markdown(f"✅ Correct answer: **{plain(q['correct'])}**")
    else:
        for opt in q["options"]:
            if opt == q["correct"]:
                st.markdown(f"✅ **{plain(opt)}**")
            elif opt == run["choice"]:
                st.markdown(f"❌ {plain(opt)}")
            else:
                st.markdown(f"◻️ {plain(opt)}")
    if last["correct"]:
        st.success(f"🎉 Correct! {q['why']}")
    else:
        st.error(f"Not quite. {q['why']}")
    is_last = idx + 1 >= len(questions)
    if st.button("See my results" if is_last else "Next question →", type="primary", use_container_width=True,
                 key=f"{p}_next_{run['id']}_{idx}"):
        run["index"] += 1
        run["checked"], run["choice"] = False, None
        st.rerun()


def results(c, level_key, lesson, pool, run):
    p = c["prefix"]
    score, total = run["score"], len(run["questions"])
    if not run["saved"]:
        run["saved"] = True
        best = st.session_state.setdefault(_k(c, "best"), {})
        key = level_key_for(c, level_key, lesson["id"])
        cur = best.get(key)
        if cur is None:
            best[key] = {"best": score, "total": total, "tries": 1}
        else:
            cur["tries"] += 1
            if score / max(total, 1) > cur["best"] / max(cur["total"], 1):
                cur["best"], cur["total"] = score, total
        done = st.session_state.setdefault(c["done_key"], [])
        if lesson["id"] not in done:  # XP only the first time through each lesson
            done.append(lesson["id"])
            gained = 10 + score * 2
            badge_name, badge_after = c.get("badge", (None, 0))
            c["award_xp"](gained, badge_name if badge_name and len(done) >= badge_after else None)
            if c.get("log"):
                c["log"]("quiz", c["section"], str(lesson.get("title") or lesson["id"]),
                         score_or_grade=f"{score}/{total}", genre_or_skill=str(level_key), xp_earned=gained)
            run["xp_message"] = f"+{gained} XP for finishing this lesson for the first time!"
        if c.get("record_answers"):  # remember which questions were seen, so the next run is fresh
            try:
                c["record_answers"](lesson, run["answers"])
            except Exception as exc:
                print(f"[inky] could not record answers: {exc}")

    ratio = score / max(total, 1)
    st.progress(1.0, text="Practice complete")
    if ratio >= 0.85:
        st.success(f"🏅 Brilliant! You scored {score} out of {total}.")
        if not run.get("celebrated"):
            run["celebrated"] = True
            st.balloons()
    elif ratio >= 0.6:
        st.success(f"👏 Well done! You scored {score} out of {total}.")
    else:
        st.info(f"💪 You scored {score} out of {total}. Read the rules again, then try once more.")
    if run.get("xp_message"):
        st.caption(run["xp_message"])

    wrong = [a for a in run["answers"] if not a["correct"]]
    if wrong:
        st.subheader("Let’s look at these again")
        for a in wrong:
            with st.container(border=True):
                st.markdown(f"**{md(a['q'])}**")
                st.markdown(f"❌ Your answer: {plain(a['chosen'])}")
                st.markdown(f"✅ Correct answer: **{plain(a['correct_text'])}**")
                st.caption(a["why"])
    else:
        st.markdown("Every answer was right. Try another lesson to keep the stars coming!")

    ids = [l["id"] for l in pool]
    pos = ids.index(lesson["id"]) if lesson["id"] in ids else -1
    nxt = ids[pos + 1] if 0 <= pos and pos + 1 < len(ids) else None
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🔁 Try again", use_container_width=True, key=f"{p}_again_{run['id']}"):
            _go(c, run=new_run(level_key, lesson, source_questions(c, lesson)))
            st.rerun()
    with c2:
        if st.button(c.get("back_label", "📚 All lessons"), use_container_width=True, key=f"{p}_all_{run['id']}"):
            _go(c, lesson=None, run=None)
            st.rerun()
    with c3:
        if nxt and st.button("➡️ Next lesson", use_container_width=True, key=f"{p}_nextlesson_{run['id']}"):
            _go(c, lesson=nxt, run=None)
            st.rerun()


def lesson_page(c, level_key, lesson, pool, topic=None):
    p = c["prefix"]
    back = f"← Back to {topic['title']}" if topic else "← All lessons"
    if st.button(back, key=f"{p}_back"):
        _go(c, lesson=None, run=None)
        st.rerun()
    st.markdown(f"## {lesson['emoji']} {lesson['title']}")
    st.caption("Framework: " + " · ".join(lesson["codes"]))

    run = st.session_state.get(_k(c, "run"))
    if run and (run["lesson_id"] != lesson["id"] or run["level"] != level_key):
        run = None
        _go(c, run=None)
    if run is None:
        teach(lesson)
        if st.button("✏️ Start practice", type="primary", use_container_width=True, key=f"{p}_start_{lesson['id']}"):
            _go(c, run=new_run(level_key, lesson, source_questions(c, lesson)))
            st.rerun()
        return

    with st.expander("📘 Remind me of the rules", expanded=False):
        teach(lesson)
    if run["index"] >= len(run["questions"]):
        results(c, level_key, lesson, pool, run)
    else:
        question(c, run)


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------
def render_hub(c):
    """Draw a whole lesson section.

    c is a dictionary with:
      prefix     short text used to name this section's session keys, e.g. "la" or "gr"
      levels     the LEVELS dictionary from the lessons file
      done_key   session key holding the list of finished lesson ids
      section    name used when saving activity, e.g. "Grammar & Punctuation"
      badge      (badge name, lessons needed) or (None, 0)
      award_xp   function(points, badge_or_None)
      log        function that saves an activity to the student's account (optional)
      stage      function returning the student's school stage text (optional)
      question_source  function(lesson) -> list of questions for a fresh run, or None (optional)
      record_answers   function(lesson, answers) that remembers what was seen (optional)
      missing    message to show if the lessons file could not be loaded
    """
    levels = c.get("levels")
    if not levels:
        st.error(c.get("missing", "The lessons file is missing. Put it in the same folder as app.py, then restart the app."))
        return
    level_key = level_picker(c)
    level = levels[level_key]
    topics = level.get("topics")
    by_id = {l["id"]: l for l in level["lessons"]}

    lesson_id = st.session_state.get(_k(c, "lesson"))
    topic_id = st.session_state.get(_k(c, "topic"))
    topic = next((t for t in (topics or []) if t["id"] == topic_id), None)

    if lesson_id in by_id:
        if topics:
            topic = next((t for t in topics if any(l["id"] == lesson_id for l in t["lessons"])), topic)
        pool = topic["lessons"] if topic else level["lessons"]
        lesson_page(c, level_key, by_id[lesson_id], pool, topic)
        return

    _go(c, lesson=None, run=None)
    if topics and topic is None:
        topic_grid(c, level_key, level)
        return
    lesson_list(c, level_key, topic["lessons"] if topic else level["lessons"], topic)
