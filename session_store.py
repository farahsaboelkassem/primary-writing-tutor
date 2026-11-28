"""Keep children signed in and keep their writing safe when the page refreshes.

Streamlit forgets everything when a browser tab refreshes, sleeps, or loses its connection.
This module fixes three things:

1. STAY SIGNED IN. After sign-in, a random token is put in the page address (?s=...). Only a
   hash of it is stored in Supabase (student_sessions). If the page reloads, the token is
   found in the address and the child is signed back in. Signing out deletes the token.
   Tokens expire after SESSION_HOURS (default 8) and are renewed while the child is working.

2. AUTOSAVE. After every run, the child's work in progress (Writing Dojo parts, Marking Arena
   text, selections, the last marking result) is saved to Supabase (student_drafts, one row per
   student) whenever it has changed, and is put back on the next sign-in or refresh.

3. SWITCHING SECTIONS. Streamlit throws away a text box's contents when its section is not on
   screen. A copy is kept in memory and put back when the child returns.

Everything is wrapped so that if the two tables do not exist (or Supabase is down) the app
carries on exactly as before. See session_setup.sql for the tables.
"""
import hashlib
import json
import secrets
import time
from datetime import datetime, timedelta, timezone

import streamlit as st

TOKEN_PARAM = "s"
DEV_STUDENT = "dev-test-student"

# What counts as "work in progress".
KEEP_EXACT = (
    "age_band", "nav_choice", "arena_text", "last_marking", "sp_band", "sp_lesson_pick", "todo_items",
)
KEEP_PREFIXES = (
    "dojo_",         # Writing Dojo selections
    "draft_",        # Writing Dojo part text
    "topic_",        # Writing Dojo topic box
    "whole_prompt_", # generated writing prompt
    "fb_",           # feedback on a part
    "guide_",        # extra help for a part
    "arena_",        # Marking Arena selections and text
)
MAX_BYTES = 400_000


# ------------------------------------------------------------------
# Small helpers
# ------------------------------------------------------------------
def _client():
    from auth_progress import get_supabase_client  # imported here to avoid a circular import
    return get_supabase_client()


def _now():
    return datetime.now(timezone.utc)


def _hash(text):
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def _session_hours():
    try:
        return max(1, int(str(st.secrets.get("SESSION_HOURS", 8))))
    except Exception:
        return 8


def _disabled(flag):
    return st.session_state.get(f"_store_off_{flag}", False)


def _fail(flag, exc):
    """Log once, then stop trying so a missing table never slows the app down."""
    if not st.session_state.get(f"_store_off_{flag}"):
        print(f"[inky] {flag} switched off for this visit: {exc}")
    st.session_state[f"_store_off_{flag}"] = True


def _token():
    try:
        value = st.query_params.get(TOKEN_PARAM)
        return str(value) if value else ""
    except Exception:
        return ""


def _set_token(value):
    try:
        if value:
            st.query_params[TOKEN_PARAM] = value
        else:
            st.query_params.pop(TOKEN_PARAM, None)
    except Exception:
        pass


# ------------------------------------------------------------------
# 1. Stay signed in
# ------------------------------------------------------------------
def resume_session():
    """If the page address holds a valid token, sign that student back in. Returns the profile or None."""
    token = _token()
    if not token or _disabled("sessions"):
        return None
    try:
        db = _client()
        res = (
            db.table("student_sessions").select("student_id")
            .eq("token_hash", _hash(token)).gt("expires_at", _now().isoformat()).execute()
        )
        if not res.data:
            _set_token("")
            return None
        student_id = res.data[0]["student_id"]
        prof = db.table("student_profiles").select("*").eq("student_id", student_id).execute()
        if not prof.data:
            _set_token("")
            return None
        profile = prof.data[0]
        st.session_state["student_profile"] = profile
        st.session_state["_sess_for"] = student_id
        st.session_state["_sess_token"] = token
        st.session_state["_resumed"] = True   # a refresh: keep their place
        _extend(token)
        return profile
    except Exception as exc:
        _fail("sessions", exc)
        return None


def ensure_session(student_id):
    """Make sure this signed-in student has a token in the page address."""
    if student_id == DEV_STUDENT or _disabled("sessions"):
        return
    try:
        if st.session_state.get("_sess_for") == student_id:
            if time.time() - st.session_state.get("_sess_touch", 0) > 1800:
                _extend(st.session_state.get("_sess_token") or _token())
            return
        db = _client()
        token = _token()
        if token:
            res = (
                db.table("student_sessions").select("student_id")
                .eq("token_hash", _hash(token)).gt("expires_at", _now().isoformat()).execute()
            )
            if res.data and res.data[0]["student_id"] == student_id:
                st.session_state["_sess_for"] = student_id
                st.session_state["_sess_token"] = token
                return
        token = secrets.token_urlsafe(32)
        db.table("student_sessions").delete().lt("expires_at", _now().isoformat()).execute()  # tidy up
        db.table("student_sessions").insert({
            "token_hash": _hash(token),
            "student_id": student_id,
            "expires_at": (_now() + timedelta(hours=_session_hours())).isoformat(),
        }).execute()
        _set_token(token)
        st.session_state["_sess_for"] = student_id
        st.session_state["_sess_token"] = token
        st.session_state["_sess_touch"] = time.time()
    except Exception as exc:
        _fail("sessions", exc)


def _extend(token):
    if not token:
        return
    try:
        _client().table("student_sessions").update(
            {"expires_at": (_now() + timedelta(hours=_session_hours())).isoformat()}
        ).eq("token_hash", _hash(token)).execute()
        st.session_state["_sess_touch"] = time.time()
    except Exception as exc:
        _fail("sessions", exc)


def end_session():
    """Sign out: delete the token so the old address no longer works."""
    token = st.session_state.get("_sess_token") or _token()
    if token and not _disabled("sessions"):
        try:
            _client().table("student_sessions").delete().eq("token_hash", _hash(token)).execute()
        except Exception as exc:
            _fail("sessions", exc)
    _set_token("")


# ------------------------------------------------------------------
# 2 and 3. Work in progress
# ------------------------------------------------------------------
def _wanted(key):
    return isinstance(key, str) and (key in KEEP_EXACT or key.startswith(KEEP_PREFIXES))


def _snapshot():
    out = {}
    for key, value in list(st.session_state.items()):
        if _wanted(key):
            try:
                json.dumps(value)
            except (TypeError, ValueError):
                continue
            out[key] = value
    return out


def _digest(data):
    return _hash(json.dumps(data, sort_keys=True, default=str))


def restore_state(student_id):
    """Call once per run, right after sign-in and before any widgets are drawn."""
    if student_id == DEV_STUDENT:
        return
    if st.session_state.get("_drafts_loaded") != student_id:
        st.session_state["_drafts_loaded"] = student_id
        saved = {}
        if not _disabled("drafts"):
            try:
                res = _client().table("student_drafts").select("data").eq("student_id", student_id).execute()
                if res.data and isinstance(res.data[0].get("data"), dict):
                    saved = res.data[0]["data"]
            except Exception as exc:
                _fail("drafts", exc)
        for key, value in saved.items():
            if key == "nav_choice" and not st.session_state.get("_resumed"):
                continue                  # a fresh sign-in starts on Home
            if _wanted(key) and key not in st.session_state:
                st.session_state[key] = value
        st.session_state["_draft_digest"] = _digest(_snapshot())
        st.session_state["_keep"] = _snapshot()
        return
    # Same visit: put back anything Streamlit dropped because its section was off screen.
    for key, value in st.session_state.get("_keep", {}).items():
        if key not in st.session_state:
            st.session_state[key] = value


def autosave_state(student_id):
    """Call at the very end of every run."""
    if student_id == DEV_STUDENT:
        return
    data = _snapshot()
    st.session_state["_keep"] = data          # in-memory copy for section switching
    if _disabled("drafts"):
        return
    digest = _digest(data)
    if digest == st.session_state.get("_draft_digest"):
        return
    payload = data
    if len(json.dumps(payload)) > MAX_BYTES:
        payload = {k: v for k, v in payload.items() if not k.startswith(("guide_", "fb_"))}
    if len(json.dumps(payload)) > MAX_BYTES:
        payload = {k: v for k, v in payload.items() if k != "last_marking"}
    try:
        _client().table("student_drafts").upsert(
            {"student_id": student_id, "data": payload, "updated_at": _now().isoformat()},
            on_conflict="student_id",
        ).execute()
        st.session_state["_draft_digest"] = digest
    except Exception as exc:
        _fail("drafts", exc)


def drop_invalid_choice(key, options):
    """Stop a restored choice from crashing a menu whose options have changed."""
    if key in st.session_state and st.session_state[key] not in list(options):
        st.session_state.pop(key, None)


def saved_note():
    """A small reassurance for the sidebar."""
    if st.session_state.get("_drafts_loaded") and not _disabled("drafts"):
        st.caption("💾 Your writing saves automatically. Click outside the box when you finish a part.")
