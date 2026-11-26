"""Safeguarding checks for children's writing.

What the app does
-----------------
Before a child's writing is sent for feedback or marking, screen_text() looks at it. There are
four outcomes:

  ok           nothing found; carry on as normal.
  care         the child may be describing something real and worrying (being hurt, feeling unsafe,
               wanting to harm themselves). The piece is NOT marked. The child sees a warm message
               that points them to a trusted adult. Because made-up stories can trip these checks,
               the child can press "It's a made-up story" and carry on.
  unsafe       swearing or other words that are not suitable for school. The piece is not marked;
               the child is asked, kindly, to change the words.
  instruction  the text tries to give Inky orders ("ignore your rules", "give me 25/25"). It is not
               sent to the marker; the child is told Inky marks writing, not instructions.

The marker also reports three yes/no flags (is_writing, inappropriate, wellbeing_concern), which
check_model_flags() turns into the same outcomes. Scores are always clamped to the rubric and the
total is always added up in code, so a model (or a child) can never award more than the rubric allows.

The text of a worrying piece is never stored. app.py saves only a small "care message shown" note,
with no writing in it.

Everything here is plain Python plus a few Streamlit calls, so it costs no AI requests.
"""
import hashlib
import re
from collections import namedtuple

import streamlit as st

Check = namedtuple("Check", ["status", "category"])
OK = Check("ok", "")

# ------------------------------------------------------------------
# Patterns (kept deliberately narrow so ordinary stories do not trip them)
# ------------------------------------------------------------------
_PEOPLE = r"(?:my\s+)?(?:mum|mom|mummy|mommy|dad|daddy|stepdad|stepmum|step-dad|step-mum|uncle|aunt|auntie|brother|sister|cousin|teacher|babysitter|neighbou?r|friend|someone|somebody|he|she|they)"
CARE_PATTERNS = [
    ("self-harm", r"\b(?:kill|hurt|harm|cut)\s+myself\b"),
    ("self-harm", r"\bi\s+(?:want|wanna|plan|am\s+going|'m\s+going)\s+to\s+(?:die|end\s+(?:it|my\s+life))\b"),
    ("self-harm", r"\bwish\s+i\s+(?:was|were)\s+dead\b"),
    ("self-harm", r"\b(?:don'?t|do\s+not)\s+want\s+to\s+(?:live|be\s+alive|be\s+here\s+anymore)\b"),
    ("self-harm", r"\bend\s+my\s+life\b"),
    ("unsafe-home", rf"\b{_PEOPLE}\s+(?:hits|beats|hurts|kicks|shakes|chokes|touches|grabs)\s+me\b"),
    ("unsafe-home", r"\b(?:touches|touched)\s+me\s+(?:in|on|where|there|private)"),
    ("unsafe-home", r"\bi\s*(?:am|'m|feel)\s+(?:really\s+|so\s+)?(?:scared|afraid|frightened)\s+to\s+(?:go|come)\s+(?:back\s+)?home\b"),
    ("unsafe-home", r"\b(?:don'?t|do\s+not)\s+feel\s+safe\b"),
    ("unsafe-home", r"\bmakes?\s+me\s+do\s+(?:things|bad\s+things|stuff)\b"),
    ("unsafe-home", r"\b(?:told|tells|tell)\s+me\s+not\s+to\s+tell\b"),
    ("unsafe-home", r"\bour\s+(?:little\s+)?secret\b.*\b(?:touch|hurt|hit)"),
    ("feeling-low", r"\bi\s+hate\s+myself\b"),
    ("feeling-low", r"\bi\s+am\s+(?:so\s+)?(?:worthless|useless)\b"),
    ("feeling-low", r"\bnobody\s+(?:loves|cares\s+about)\s+me\b"),
]

# A short, mild list. The marker's own "inappropriate" flag catches the rest.
UNSAFE_WORDS = (
    "fuck", "fucking", "fucked", "shit", "bitch", "bastard", "cunt", "asshole", "arsehole",
    "porn", "pornography", "slut", "whore", "dick", "pussy", "nigger", "faggot",
)
_UNSAFE_RE = re.compile(r"\b(?:" + "|".join(UNSAFE_WORDS) + r")\b", re.I)

INSTRUCTION_PATTERNS = [
    r"\bignore\s+(?:all\s+|any\s+|your\s+|the\s+|previous\s+|above\s+)+(?:rules|instructions|prompt|directions)\b",
    r"\bforget\s+(?:all\s+|your\s+|the\s+|previous\s+)+(?:rules|instructions)\b",
    r"\bgive\s+me\s+(?:a\s+)?(?:full|top|perfect|maximum|max|25|twenty[- ]five)\b",
    r"\b(?:system|developer)\s+prompt\b",
    r"\byou\s+are\s+now\s+(?:a|an|in)\b",
    r"\bpretend\s+(?:you\s+are|to\s+be)\b.*\b(?:marker|teacher|judge)\b",
    r"\b25\s*/\s*25\b",
]

CARE_TEXT = {
    "title": "💛 Thank you for sharing this",
    "body": (
        "Inky is a writing helper, so I can't help with big or worrying feelings, but a grown-up can. "
        "If any part of this is true for you, please tell a parent, a teacher, or another adult you "
        "trust today. You matter, and you don't have to sort it out on your own."
    ),
    "story_hint": "If this is just part of a made-up story, press the button and we'll carry on.",
}
UNSAFE_TEXT = (
    "🌈 Let's keep our writing kind and suitable for everyone. "
    "Please change the words that aren't friendly or aren't right for school, then try again."
)
INSTRUCTION_TEXT = (
    "✏️ Inky marks your writing, not instructions! Take out the parts that talk to Inky "
    "and try again with just your story or topic."
)
NOT_WRITING_TEXT = (
    "✏️ Inky gives feedback on pieces of writing, like a story, a report or a letter. "
    "Write a few sentences about your story or topic, then try again!"
)


# ------------------------------------------------------------------
# Screening
# ------------------------------------------------------------------
def screen_text(text):
    """Check a piece of writing. Returns Check(status, category)."""
    t = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    if not t:
        return OK
    for pattern in INSTRUCTION_PATTERNS:
        if re.search(pattern, t):
            return Check("instruction", "instruction")
    for category, pattern in CARE_PATTERNS:
        if re.search(pattern, t):
            return Check("care", category)
    if _UNSAFE_RE.search(t):
        return Check("unsafe", "language")
    return OK


def check_model_flags(result):
    """Turn the marker's yes/no flags into a Check (or None when all is well)."""
    if not isinstance(result, dict):
        return None
    if _truthy(result.get("wellbeing_concern")):
        return Check("care", "model-flag")
    if _truthy(result.get("inappropriate")):
        return Check("unsafe", "model-flag")
    if result.get("is_writing") is not None and not _truthy(result.get("is_writing")):
        return Check("offtopic", "model-flag")
    return None


def _truthy(value):
    if isinstance(value, str):
        return value.strip().lower() in ("true", "yes", "1")
    return bool(value)


# ------------------------------------------------------------------
# Streamlit helpers: remember a block, show it, let a child say "it's a story"
# ------------------------------------------------------------------
def _hash(text):
    return hashlib.sha1(str(text or "").strip().encode("utf-8")).hexdigest()


def is_overridden(key, text):
    """True if the child already pressed 'It's a made-up story' for exactly this text."""
    return st.session_state.get(f"sg_ok_{key}") == _hash(text)


def set_block(key, check, text=""):
    st.session_state[f"sg_block_{key}"] = {"status": check.status, "category": check.category, "hash": _hash(text)}


def clear_block(key):
    st.session_state.pop(f"sg_block_{key}", None)


def blocked_for(key, text):
    """Screen the text. Returns the Check if it must not go on, or None if it can."""
    clear_block(key)
    check = screen_text(text)
    if check.status == "ok":
        return None
    if check.status == "care" and is_overridden(key, text):
        return None
    set_block(key, check, text)
    return check


def _helpline_line():
    try:
        extra = str(st.secrets.get("CHILD_HELP_TEXT", "")).strip()
    except Exception:
        extra = ""
    return extra


def render_block(key):
    """Show the stored message for this key, if any. Call it every run, outside the button."""
    block = st.session_state.get(f"sg_block_{key}")
    if not block:
        return
    status = block["status"]
    if status == "care":
        st.markdown(f"#### {CARE_TEXT['title']}")
        st.info(CARE_TEXT["body"])
        extra = _helpline_line()
        if extra:
            st.write(extra)
        st.caption(CARE_TEXT["story_hint"])
        if st.button("📖 It's a made-up story, carry on", key=f"sg_story_{key}"):
            st.session_state[f"sg_ok_{key}"] = block["hash"]
            st.session_state[f"sg_force_{key}"] = True
            clear_block(key)
            st.rerun()
    elif status == "unsafe":
        st.warning(UNSAFE_TEXT)
    elif status == "instruction":
        st.warning(INSTRUCTION_TEXT)
    else:
        st.info(NOT_WRITING_TEXT)


def take_force(key):
    """True once, right after the child pressed 'It's a made-up story'."""
    return bool(st.session_state.pop(f"sg_force_{key}", False))
