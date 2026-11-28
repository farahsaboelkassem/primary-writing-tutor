"""Speech-to-text for the writing boxes.

The microphone button uses the browser's own speech recognition (the Web Speech API in Chrome,
Edge and Safari). It does not use the writing helper, so it costs no AI requests.

Good to know:
  * The browser, not this app, does the listening. Chrome sends the audio to Google's speech
    service and Safari to Apple's. Mention this in your privacy notice for parents.
  * It needs HTTPS and the child's permission to use the microphone.
  * It does not work in Firefox. The button is greyed out and the child can still type.

How it works: the button runs in a small component (dictation_component/index.html). When the
child presses Stop, the words come back here, are tidied (spoken punctuation, capital letters)
and added to the end of the text box. Nothing is sent for feedback until the child chooses to.

Use it BEFORE the text box is drawn, because Streamlit only lets you change a box's text before
it appears on the page:

    spoken = dictation_button("part1")
    if spoken:
        st.session_state["draft_part1"] = join_text(st.session_state.get("draft_part1", ""), spoken)
    st.text_area(..., key="draft_part1")
"""
import os
import re

import streamlit as st
import streamlit.components.v1 as components

_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dictation_component")
_component = None
if os.path.isdir(_DIR):
    try:
        _component = components.declare_component("inky_dictation", path=_DIR)
    except Exception as exc:  # never stop the app because of the microphone button
        print(f"[inky] dictation component unavailable: {exc}")

SPOKEN_PUNCTUATION = [
    (r"\bfull stop\b", "."),
    (r"\bquestion mark\b", "?"),
    (r"\bexclamation (?:mark|point)\b", "!"),
    (r"\bcomma\b", ","),
    (r"\bnew paragraph\b", "\n\n"),
    (r"\bnew line\b", "\n"),
]


def tidy_dictation(text, start_sentence=True):
    """Turn spoken words into neat writing: punctuation words become symbols, capitals are added."""
    t = " " + str(text or "").strip() + " "
    for pattern, symbol in SPOKEN_PUNCTUATION:
        t = re.sub(pattern, symbol, t, flags=re.I)
    t = re.sub(r"[ \t]+([.,!?;:])", r"\1", t)            # no space before punctuation
    t = re.sub(r"([.,!?;:])(?=[A-Za-z])", r"\1 ", t)     # a space after it
    t = re.sub(r"[ \t]*\n[ \t]*", "\n", t)               # tidy around line breaks
    t = re.sub(r"[ \t]{2,}", " ", t).strip()
    t = re.sub(r"\bi\b", "I", t)                          # the word 'I'
    t = re.sub(r"([.!?][ ]+|\n)([a-z])", lambda m: m.group(1) + m.group(2).upper(), t)
    if start_sentence and t:
        t = t[0].upper() + t[1:]
    return t


def join_text(existing, spoken):
    """Add dictated words to what the child has already written."""
    existing = str(existing or "")
    stripped = existing.rstrip(" \t")
    if not stripped.strip():
        return tidy_dictation(spoken, start_sentence=True)
    at_sentence_start = stripped.endswith(("\n", ".", "!", "?"))
    piece = tidy_dictation(spoken, start_sentence=at_sentence_start)
    if not at_sentence_start and piece and piece[0].isupper() and not re.match(r"I\b", piece):
        piece = piece[0].lower() + piece[1:]               # carrying on mid-sentence
    glue = "" if stripped.endswith("\n") or piece.startswith(("\n", ".", ",", "?", "!", ";", ":")) else " "
    return stripped + glue + piece


def _enabled():
    try:
        return str(st.secrets.get("ENABLE_DICTATION", "true")).strip().lower() not in ("false", "0", "no", "off")
    except Exception:
        return True


def _language():
    try:
        return str(st.secrets.get("SPEECH_LANG", "en-GB"))
    except Exception:
        return "en-GB"


def dictation_button(key, show_hint=True):
    """Draw the microphone button. Returns tidy text the child just dictated, or '' if nothing new."""
    if _component is None or not _enabled():
        return ""
    try:
        result = _component(
            key=f"dictation_{key}",
            default=None,
            lang=_language(),
            show_hint=bool(show_hint),
            start_label="🎤 Talk to write",
            stop_label="⏹️ Stop and add my words",
        )
    except Exception as exc:
        print(f"[inky] dictation button failed: {exc}")
        return ""
    if not isinstance(result, dict) or not result.get("text"):
        return ""
    seen_key = f"_dict_seen_{key}"
    if st.session_state.get(seen_key) == result.get("id"):
        return ""                      # already added on an earlier run
    st.session_state[seen_key] = result.get("id")
    return str(result["text"])
