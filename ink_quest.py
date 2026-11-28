"""Inky's Ink-Quest: a platform game where answering questions powers you up.

How it differs from a plain game embed:
  * The game runs in a small component (ink_quest_component/index.html) and sends its result BACK to
    the app. The child never types XP in, so it cannot be faked by typing a bigger number.
  * The app decides the XP: it is capped per game and per day, and logged to the student's account.
  * Questions come from the app's own lessons (grammar, language and spelling, plus the Supabase
    question bank), matched to the child's stage. A built-in set of starter questions fills any gaps.
  * Questions the child gets right or wrong are recorded in their question history, so the Home page
    and parent reports can see what they find tricky.
"""
import json
import os
import random
import uuid
from datetime import datetime, timezone

import streamlit as st
import streamlit.components.v1 as components

_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ink_quest_component")
_component = None
if os.path.isdir(_DIR):
    try:
        _component = components.declare_component("inky_ink_quest", path=_DIR)
    except Exception as exc:
        print(f"[inky] ink-quest component unavailable: {exc}")

MAX_RUN_XP = 160        # most XP one game can ever pay out
DAILY_GAME_XP = 300     # most game XP per student per day
RUN_SIZE = 14

# ---------------------------------------------------------------------------
# Built-in starter questions (used when a world has too few lesson questions)
# ---------------------------------------------------------------------------
W1 = [
    {"q": "Fix the missing punctuation: 'After the storm ended we walked outside.'",
     "options": ["After the storm ended, we walked outside.", "After the storm, ended we walked outside.", "After, the storm ended we walked outside."],
     "answer": 0, "hint": "Put a comma after an opening clause ('After the storm ended,')."},
    {"q": "Which sentence fixes this run-on correctly? 'Leo ran fast he missed the bus.'",
     "options": ["Leo ran fast, he missed the bus.", "Leo ran fast, yet he missed the bus.", "Leo ran fast yet, he missed the bus."],
     "answer": 1, "hint": "Join two full sentences with a comma plus a joining word (and, but, or, yet, so)."},
    {"q": "Choose the correct possessive apostrophe for ONE puppy's toy:",
     "options": ["The puppys' ball rolled away.", "The puppies ball rolled away.", "The puppy's ball rolled away."],
     "answer": 2, "hint": "For one puppy, add 's after the word."},
    {"q": "Where do the quotation marks belong?",
     "options": ["\"Watch out for the puddle!\" shouted Maya.", "\"Watch out for the puddle! shouted Maya.\"", "Watch out for the puddle! \"shouted Maya.\""],
     "answer": 0, "hint": "Quotation marks wrap only the exact spoken words and their end punctuation."},
    {"q": "Which sentence uses commas in a list properly?",
     "options": ["We packed apples, sandwiches and, juice.", "We packed, apples, sandwiches, and juice.", "We packed apples, sandwiches, and juice."],
     "answer": 2, "hint": "Put commas between the items in a list, not straight after the verb."},
    {"q": "BOSS CHALLENGE: Fix the comma splice: 'The dragon roared, the bridge shook.'",
     "options": ["The dragon roared; the bridge shook.", "The dragon roared, the bridge, shook.", "The dragon, roared the bridge shook."],
     "answer": 0, "hint": "Two full sentences can be joined with a semicolon (;) or split with a full stop, never just a comma."},
]
W2 = [
    {"q": "Which word doubles the final consonant before adding -ed?", "options": ["jumpped", "hopped", "walkked"],
     "answer": 1, "hint": "Short vowel plus one final consonant ('hop') doubles it: hopped."},
    {"q": "Choose the correct spelling when adding '-ing' to 'bake':", "options": ["bakeing", "baking", "bakking"],
     "answer": 1, "hint": "Drop the silent 'e' before adding -ing."},
    {"q": "Which word uses '-tch' right after a single short vowel?", "options": ["cach", "catch", "catsh"],
     "answer": 1, "hint": "Use '-tch' straight after one short vowel sound (catch, match, pitch)."},
    {"q": "Which word follows the doubling rule for f, l, s and z?", "options": ["fluf", "fluff", "flufe"],
     "answer": 1, "hint": "One-syllable words ending in f, l, s or z after a short vowel double the last letter."},
    {"q": "BOSS CHALLENGE: Choose the correct spelling for 'hoping' (wishing for something):", "options": ["hopping", "hoping", "hopeing"],
     "answer": 1, "hint": "'Hope' drops the silent 'e' before -ing. 'Hopping' comes from 'hop'."},
    {'q': 'Which spelling is correct?', 'options': ['waite', 'wait', 'wate'], 'answer': 1, 'hint': "The 'ai' sound in wait is spelled with ai."},
    {'q': "Which is the correct spelling of the word that means 'the opposite of day'?", 'options': ['nite', 'night', 'nyte'], 'answer': 1, 'hint': 'Night has a silent gh after the i.'},
    {'q': "Choose the correct plural of 'box':", 'options': ['boxs', 'boxes', 'boxies'], 'answer': 1, 'hint': 'Words ending in x add -es.'},
    {'q': "Choose the correct plural of 'baby':", 'options': ['babys', 'babies', 'babyes'], 'answer': 1, 'hint': 'After a consonant, change the y to i and add -es.'},
    {'q': 'Which spelling is correct for the sound you make when you tap on a door?', 'options': ['nock', 'knock', 'knok'], 'answer': 1, 'hint': 'Some words start with a silent k: knock, knee, knife.'},
    {'q': 'Which spelling is correct?', 'options': ['friend', 'freind', 'frend'], 'answer': 0, 'hint': "Friend ends with 'end'."},
]
W3 = [
    {"q": "Which verb best upgrades 'walked quietly' in a mystery story?", "options": ["strolled", "marched", "crept"],
     "answer": 2, "hint": "'Crept' shows stealth and careful, quiet movement."},
    {"q": "Choose the strongest sensory detail for a stormy night:",
     "options": ["rain hitting the window loudly", "icy rain drumming against the rattling glass", "a lot of wet rain outside"],
     "answer": 1, "hint": "Combine touch ('icy') with sharp sound verbs ('drumming', 'rattling')."},
    {"q": "Which word means 'extremely surprised or amazed'?", "options": ["astonished", "reluctant", "weary"],
     "answer": 0, "hint": "'Astonished' is a vivid word for amazed or shocked."},
    {"q": "Upgrade the weak adjective in: 'The old castle stood on the hill.'", "options": ["nice", "crumbling", "big"],
     "answer": 1, "hint": "'Crumbling' paints a clear picture of age."},
    {"q": "BOSS CHALLENGE: Which verb best replaces 'said angrily'?", "options": ["whispered", "snapped", "murmured"],
     "answer": 1, "hint": "'Snapped' shows sharp anger in one strong verb."},
    {'q': "Which word is the best synonym (word with a similar meaning) for 'big'?", 'options': ['tiny', 'enormous', 'quiet'], 'answer': 1, 'hint': 'Enormous means very big.'},
    {'q': "Which word is the opposite of 'ancient'?", 'options': ['modern', 'old', 'dusty'], 'answer': 0, 'hint': 'Ancient means very old, so modern is the opposite.'},
    {'q': "Choose the best word: 'The cat crept ___ towards the bird.'", 'options': ['silently', 'silent', 'silence'], 'answer': 0, 'hint': 'An adverb that ends in -ly tells us how the cat crept.'},
    {'q': "Which word means 'very tired'?", 'options': ['exhausted', 'energetic', 'curious'], 'answer': 0, 'hint': 'Exhausted means completely worn out.'},
    {'q': 'Which simile is written correctly?', 'options': ['as brave as a lion', 'as brave like a lion', 'brave as lion'], 'answer': 0, 'hint': "A simile compares using 'as ... as' or 'like'."},
    {'q': "Add the prefix un- to make the opposite of 'happy':", 'options': ['unhappy', 'dishappy', 'nonhappy'], 'answer': 0, 'hint': "The prefix un- means 'not'."},
]
W4 = [
    {"q": "'Mara zipped her coat and checked the rain gauge before opening the door.' What can you infer?",
     "options": ["It is hot and sunny outside.", "Wet or rainy weather is likely.", "Mara is going swimming."],
     "answer": 1, "hint": "Zipping a coat and checking a rain gauge are clues for rainy weather."},
    {"q": "'Tariq kept glancing at the clock and tapping his pencil while waiting for his test paper.' How does Tariq feel?",
     "options": ["Nervous or impatient", "Sleepy and bored", "Excited for lunch"],
     "answer": 0, "hint": "Clock-watching and pencil-tapping show nervous waiting."},
    {"q": "Which detail best shows a story is set in winter?",
     "options": ["Leaves turned bright orange on the oak trees.", "Breath hung like white smoke in the freezing air.", "Crickets chirped beside the warm pond."],
     "answer": 1, "hint": "Seeing your breath in freezing air is direct evidence of winter."},
    {"q": "What is the main job of a topic sentence in a paragraph?",
     "options": ["To list every minor detail at the end", "To introduce the main idea of the paragraph", "To thank the reader"],
     "answer": 1, "hint": "A topic sentence states the central idea that the other sentences explain."},
    {"q": "BOSS CHALLENGE: 'Even though the map was torn, Nadia traced the coastline until she spotted the hidden cove.' What trait does Nadia show?",
     "options": ["Carelessness", "Determination", "Shyness"],
     "answer": 1, "hint": "Carrying on despite a torn map shows determination."},
    {'q': "'Sam's umbrella was dripping and his boots left puddles by the door.' What had the weather been like?", 'options': ['Dry and sunny', 'Rainy', 'Snowy and icy'], 'answer': 1, 'hint': 'A dripping umbrella and puddles are clues for rain.'},
    {'q': '\'Priya hugged her cat tightly and whispered, "Don\'t worry, I\'m not leaving."\' How does Priya feel about her cat?', 'options': ['She loves it and wants to comfort it', 'She is angry with it', 'She is bored of it'], 'answer': 0, 'hint': 'Hugging tightly and whispering shows care.'},
    {'q': "'The shop lights were off, the door was locked and a sign hung in the window.' What can you infer?", 'options': ['The shop is closed', 'The shop is very busy', 'The shop sells umbrellas'], 'answer': 0, 'hint': 'Lights off and a locked door are clues that it is closed.'},
    {'q': 'Which detail is a clue that a character is brave?', 'options': ['She trembled and froze', 'She stepped forward calmly', 'She hid behind the door'], 'answer': 1, 'hint': 'Stepping forward calmly shows courage.'},
    {'q': "'Mum smiled, pulled out a camera and told everyone to say cheese.' What is happening?", 'options': ['A photo is being taken', 'A meal is being cooked', 'A race is starting'], 'answer': 0, 'hint': "A camera and 'say cheese' are clues."},
    {'q': 'What does a heading in a non-fiction text tell you?', 'options': ['What the section is about', 'How the author feels', 'Who the characters are'], 'answer': 0, 'hint': 'A heading names the topic of the part below it.'},
    {'q': "'The puppy's tail wagged and he leapt up, barking happily at the door.' Why is the puppy excited?", 'options': ['Someone he loves has arrived', 'He is feeling ill', 'It is bedtime'], 'answer': 0, 'hint': 'A wagging tail and happy barking show excitement.'},
    {'q': 'Which sentence is a FACT?', 'options': ['Dogs are the best pets.', 'Spiders have eight legs.', 'Winter is the nicest season.'], 'answer': 1, 'hint': 'A fact can be checked and proved true.'},
]
W5 = W1[:2] + W2[:2] + W3[:2] + W4[:2]

PUNCTUATION_WORDS = (
    "punctuation", "comma", "apostrophe", "capital", "full stop", "question", "exclamation", "speech", "inverted",
    "bracket", "dash", "hyphen", "colon", "semi", "ellipsis", "sentence",
)

WORLDS = {
    "World 1: Punctuation Peaks": {"boss": "Run-On Rex", "fallback": W1, "kind": "grammar"},
    "World 2: Phonics Fortress": {"boss": "The Misspeller", "fallback": W2, "kind": "spelling"},
    "World 3: Vocab Volcano": {"boss": "Captain Cliché", "fallback": W3, "kind": "language"},
    "World 4: Clue Caverns": {"boss": "Riddle Sphinx", "fallback": W4, "kind": "clues"},
    "World 5: Grand Ink Gauntlet (All Skills Mix)": {"boss": "Lord Lexicon", "fallback": W5, "kind": "mix"},
}


# ---------------------------------------------------------------------------
# Building a question set from the app's own lessons
# ---------------------------------------------------------------------------
def _clean(text):
    return str(text or "").replace("**", "").replace("`", "").strip()


def _game_question(q, lesson_id):
    """Convert a question-bank style question into the game's format (None if it isn't a choice question)."""
    kind = q.get("type")
    correct = str(q.get("correct", "")).strip()
    if kind == "true_false":
        options = ["True", "False"]
    elif kind == "multiple_choice":
        wrong = [o for o in q.get("options", []) if o != correct]
        random.shuffle(wrong)
        options = [correct] + wrong[:2]
        random.shuffle(options)
    else:
        return None
    if correct not in options or len(options) < 2:
        return None
    return {
        "q": _clean(q.get("q")), "options": options, "answer": options.index(correct),
        "hint": _clean(q.get("why")) or "Look closely at the pattern and try again.",
        "code": q.get("code"), "lesson_id": lesson_id,
    }


@st.cache_data(ttl=300, show_spinner=False)
def _bank_rows(_db, ids):
    if _db is None or not ids:
        return []
    try:
        return (
            _db.table("question_bank").select("*").in_("lesson_id", list(ids)).eq("active", True).execute().data or []
        )
    except Exception as exc:
        print(f"[inky] ink-quest: could not read the question bank: {exc}")
        return []


def _lesson_pool(module_name, band, db, only_titles=None):
    """Questions from every lesson of a section for this stage (built-in plus the Supabase bank)."""
    import question_bank

    try:
        module = __import__(module_name)
        lessons = module.LEVELS[band]["lessons"]
    except Exception:
        return []
    if only_titles:
        lessons = [l for l in lessons if any(w in l["title"].lower() for w in only_titles)]
    pool = []
    for lesson in lessons:
        for q in question_bank.builtin_questions(lesson):
            g = _game_question(q, lesson["id"])
            if g:
                pool.append(g)
    for row in _bank_rows(db, tuple(l["id"] for l in lessons)):
        q = question_bank.row_to_question(row)
        g = _game_question(q, row.get("lesson_id")) if q else None
        if g:
            pool.append(g)
    return pool


def _spelling_pool(band, db):
    if db is None:
        return []
    try:
        from lesson_catalog import spelling_lessons
        from spelling_arena import _parse_json_field

        ids = [r["lesson_id"] for r in spelling_lessons(db, band)]
        if not ids:
            return []
        rows = db.table("spelling_questions").select("*").in_("lesson_id", ids).execute().data or []
    except Exception as exc:
        print(f"[inky] ink-quest: could not read spelling questions: {exc}")
        return []
    pool = []
    for r in rows:
        kind = r.get("question_type")
        correct = str(r.get("correct_answer") or "").strip()
        if kind == "true_false":
            options = ["True", "False"]
        elif kind == "mcq":
            options = [str(o).strip() for o in _parse_json_field(r.get("options"), []) if str(o).strip()]
            wrong = [o for o in options if o != correct]
            random.shuffle(wrong)
            options = [correct] + wrong[:2]
            random.shuffle(options)
        else:
            continue
        if correct in options and len(options) >= 2:
            pool.append({
                "q": _clean(r.get("prompt")), "options": options, "answer": options.index(correct),
                "hint": _clean(r.get("explanation") or r.get("rule_note")) or "Think about the spelling rule you learned.",
                "code": None, "lesson_id": None,   # spelling progress is tracked in the Spelling arena itself
            })
    return pool


def build_questions(world, band, db):
    """Returns (questions for the game, a label saying where they came from)."""
    cfg = WORLDS[world]
    kind = cfg["kind"]
    if kind == "grammar":
        pool = _lesson_pool("grammar_lessons", band, db, only_titles=PUNCTUATION_WORDS)
        if len(pool) < 8:
            pool = _lesson_pool("grammar_lessons", band, db)
    elif kind == "language":
        pool = _lesson_pool("language_lessons", band, db)
    elif kind == "spelling":
        pool = _spelling_pool(band, db)
    elif kind == "mix":
        pool = (random.sample(p, min(5, len(p))) if (p := _lesson_pool("grammar_lessons", band, db)) else []) \
            + (random.sample(p, min(5, len(p))) if (p := _lesson_pool("language_lessons", band, db)) else []) \
            + (random.sample(p, min(4, len(p))) if (p := _spelling_pool(band, db)) else [])
    else:
        pool = []
    label = "your lessons" if len(pool) >= 8 else "the starter set"
    random.shuffle(pool)
    questions = pool[:RUN_SIZE]
    if len(questions) < 8:      # top up from the built-in starter questions
        extra = list(cfg["fallback"])
        random.shuffle(extra)
        questions += extra[: 12 - len(questions)]
    return questions, label


# ---------------------------------------------------------------------------
# Results: the app decides the XP
# ---------------------------------------------------------------------------
def _xp_today(db, student_id):
    if db is None:
        return 0
    try:
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        rows = (
            db.table("student_activity_log").select("xp_earned,created_at").eq("student_id", student_id)
            .eq("activity_type", "game").execute().data or []
        )
        return sum(int(r.get("xp_earned") or 0) for r in rows if str(r.get("created_at", "")) >= start)
    except Exception as exc:
        print(f"[inky] ink-quest: could not check today's game XP: {exc}")
        return 0


def _handle_result(result, db, student_id, award_xp, log_activity):
    if not isinstance(result, dict) or not result.get("id"):
        return
    if st.session_state.get("iq_seen") == result["id"]:
        return                                   # already counted on an earlier run
    st.session_state["iq_seen"] = result["id"]

    try:
        claimed = int(result.get("xp") or 0)
    except (TypeError, ValueError):
        claimed = 0
    claimed = max(0, min(claimed, MAX_RUN_XP))
    answers = []
    for a in (result.get("answers") or [])[:60]:
        if isinstance(a, dict):
            answers.append({"code": str(a.get("code") or "")[:80] or None,
                            "lesson_id": str(a.get("lesson_id") or "")[:80] or None, "correct": bool(a.get("correct"))})
    world = str(result.get("world") or "Ink-Quest")[:80]

    left_today = max(0, DAILY_GAME_XP - _xp_today(db, student_id))
    award = min(claimed, left_today)
    if award > 0 and callable(award_xp):
        award_xp(award)
    correct = sum(1 for a in answers if a["correct"])
    if callable(log_activity):
        log_activity(
            "game", "Game Arena", f"Ink-Quest: {world}",
            score_or_grade=f"{correct}/{len(answers)}" if answers else "", genre_or_skill="ink_quest", xp_earned=award,
            details={"won": bool(result.get("won")), "claimed_xp": claimed},
        )
    # Questions answered feed the same history that powers Home to-dos and parent reports.
    try:
        import question_bank

        by_lesson = {}
        for a in answers:
            if a["code"] and a["lesson_id"]:
                by_lesson.setdefault(a["lesson_id"], []).append({"code": a["code"], "correct": a["correct"]})
        for lesson_id, items in by_lesson.items():
            question_bank.bank_record({"id": lesson_id}, items)
    except Exception as exc:
        print(f"[inky] ink-quest: could not save question history: {exc}")

    if award < claimed:
        note = " That is today's game XP limit, so more practice in the other sections will earn more!"
    else:
        note = ""
    st.session_state["iq_message"] = (
        f"{'🏆 You won!' if result.get('won') else '🦉 Good effort!'} +{award} XP added to your profile. "
        f"You answered {correct} of {len(answers)} questions right first time.{note}"
    )


# ---------------------------------------------------------------------------
# The screen
# ---------------------------------------------------------------------------
def _new_set():
    st.session_state.pop("iq_run", None)
    try:
        _bank_rows.clear()
    except Exception:
        pass


def render_ink_quest(db, student_id, age_band, award_xp=None, log_activity=None):
    if _component is None:
        st.info("This game is being set up. Come back soon!")
        print("[inky] ink-quest: the ink_quest_component folder is missing")
        return
    band = "lower" if str(age_band).startswith("Lower") else "upper"

    c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
    world = c1.selectbox("Choose your quest world:", list(WORLDS), key="iq_world")
    c2.button("🔄 New question set", key="iq_new", on_click=_new_set, use_container_width=True)

    run = st.session_state.get("iq_run")
    if not run or run["world"] != world or run["band"] != band:
        questions, label = build_questions(world, band, db)
        run = {
            "world": world, "band": band, "run_id": uuid.uuid4().hex, "label": label,
            "game": {"worldTitle": world, "bossName": WORLDS[world]["boss"], "questions": questions},
        }
        st.session_state["iq_run"] = run

    st.caption(
        f"Questions from {run['label']}. Move with the arrow keys or A / D, jump with Space, fire with F, "
        f"or use the buttons on a tablet. Hit the [?] blocks to power up and beat {WORLDS[world]['boss']}!"
    )
    result = _component(key="ink_quest_game", default=None, game=run["game"], run_id=run["run_id"])
    _handle_result(result, db, student_id, award_xp, log_activity)
    message = st.session_state.get("iq_message")
    if message:
        st.success(message)
