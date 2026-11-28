"""The Writing Adventure - Base Streamlit App, UI, Database & API Routing"""

import base64
from datetime import datetime
from io import BytesIO
import json
import math
import os
import random
import re
import time

from openai import OpenAI
from PIL import Image
import streamlit as st

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

from writing_tutor import (
    AGE_BANDS,
    BLOCK_ICONS,
    CATEGORY_COLORS,
    CATEGORY_ICONS,
    CATEGORY_LABELS,
    FICTION_STYLES,
    GRAMMAR_TOPICS,
    LANGUAGE_EXAMPLES,
    NON_FICTION_SUBGENRES,
    PERSUASIVE_LAYOUTS,
    RUBRICS,
    SINGLE_LINE_BLOCKS,
    STAGE6_CODES,
    SUBGENRE_ICONS,
    SUBGENRE_KEY,
    apply_word_count_rules,
    block_ai_guide_prompt,
    block_extra_help_prompt,
    block_feedback_prompt,
    canonical_subgenre,
    get_blocks,
    get_carousel_cards,
    get_step_blueprint_and_wagoll,
    piece_marking_prompt,
    quiz_prompt,
    toolkit_prompt,
    transcription_messages,
    whole_prompt_idea_prompt,
    word_count,
    worksheet_content_prompt,
)
def get_openrouter_api_key() -> str:
    # 1. Check top-level keys first
    for key_name in ("OPENROUTER_API_KEY", "openrouter_api_key"):
        if key_name in st.secrets and str(st.secrets[key_name]).strip():
            return str(st.secrets[key_name]).strip()

    # 2. Check [openrouter] section
    if "openrouter" in st.secrets:
        or_section = st.secrets["openrouter"]
        for key_name in ("api_key", "OPENROUTER_API_KEY", "key"):
            if key_name in or_section and str(or_section[key_name]).strip():
                return str(or_section[key_name]).strip()

    # 3. Fallback to environment variable
    return os.getenv("OPENROUTER_API_KEY", "").strip()
# ------------------------------------------------------------------
# Page & Theme
# ------------------------------------------------------------------
st.set_page_config(
    page_title="The Writing Adventure",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="expanded",
)

from reading_section import render_reading_section, READING_UNIVERSE_CSS
from dictation import dictation_button, join_text
from games_arena import render_games_arena
from lesson_catalog import catalog_for
from parent_reports import handle_report_links, render_parent_reports
from next_steps import build_next_steps, render_next_steps
from spelling_arena import SPELLING_UNIVERSE_CSS, render_spelling_arena
from landing_page import (
    HOME_UNIVERSE_CSS, NAV_ARENA, NAV_DOJO, NAV_GAMES, NAV_GRAMMAR, NAV_HOME, NAV_LANGUAGE, NAV_OPTIONS,
    NAV_PROGRESS, NAV_READING, NAV_SPELLING, NAV_VAULT, render_home,
)
from session_store import (
    autosave_state, drop_invalid_choice, end_session, ensure_session, restore_state, resume_session, saved_note,
)
from safeguarding import (
    blocked_for, check_model_flags, clear_block, is_overridden, render_block, set_block, take_force,
)
from auth_progress import (
    render_auth_page,
    render_profile_progress_tab,
    sign_out_student,
    get_student_dashboard_data,
    log_student_activity,
    upsert_student_vocabulary,
    add_xp,
)

profile = st.session_state.get("student_profile")

# LOCAL TESTING ONLY: run `DEV_SKIP_LOGIN=1 streamlit run app.py` (Mac/Linux) or
# `$env:DEV_SKIP_LOGIN=1; streamlit run app.py` (Windows PowerShell) to skip sign-in.
# It uses an environment variable, so it can never switch on in the deployed app.
if not profile and os.environ.get("DEV_SKIP_LOGIN") == "1":
    profile = {
        "student_id": "dev-test-student",
        "display_name": "Test Student",
        "current_title": "Novice Scribbler",
        "xp_points": 0,
        "badges": [],
    }
    st.session_state["student_profile"] = profile

def get_db():
    """The database connection, or None. Never raises."""
    try:
        from auth_progress import get_supabase_client
        return get_supabase_client()
    except Exception as exc:
        print(f"[inky] no database connection: {exc}")
        return None


# Links in report emails (confirm / stop) work without signing in.
if handle_report_links(get_db()):
    st.stop()

if not profile:
    profile = resume_session()

if not profile:
    render_auth_page()
    st.stop()

# Stay signed in after a refresh, and put back any work in progress.
ensure_session(profile["student_id"])
restore_state(profile["student_id"])
# ------------------------------------------------------------------
# Theme: shared look + one atmosphere (background universe) per section
# ------------------------------------------------------------------
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;600;700;800&family=Fredoka:wght@400;600;700&family=Nunito:wght@400;600;700;800&family=Patrick+Hand&display=swap');

:root {
  --ink: #2b2a4a; --muted: #64637f; --paper: #fffdf7; --line: #e8e4f3;
  --accent: #6b63d9; --accent-light: #7a72e6; --accent-dark: #4a43b0; --accent-soft: #eeecff;
  --hero-a: #3d3499; --hero-b: #8a63d8;
}

/* ---------- Base type ---------- */
html, body, [class*="css"] { font-family: 'Nunito', system-ui, sans-serif !important; }
[data-testid="stIconMaterial"], [class*="material-symbols"], .material-icons {
  font-family: 'Material Symbols Rounded', 'Material Icons' !important;
}
h1, h2, h3, h4, h5, [data-testid="stHeading"] {
  font-family: 'Baloo 2', cursive !important; color: var(--ink) !important; letter-spacing: .1px;
}
h1 { font-size: clamp(2rem, 4vw, 2.7rem) !important; font-weight: 800 !important; }
h2 { font-size: clamp(1.6rem, 3vw, 2.1rem) !important; font-weight: 800 !important; }
h3 { font-size: 1.4rem !important; font-weight: 700 !important; }
p, li, label, [data-testid="stMarkdownContainer"] { color: var(--ink); font-size: 1.03rem; line-height: 1.6; }
small, .stCaption, [data-testid="stCaptionContainer"] { color: var(--muted) !important; font-size: .94rem !important; }

/* ---------- Page shell: universe behind, paper panel in front ---------- */
.stApp { isolation: isolate; color: var(--ink); }
.stApp::before, .stApp::after { content: ""; position: fixed; pointer-events: none; z-index: -1; }
.stApp::before { inset: 0; }
.stApp::after { left: 0; right: 0; bottom: 0; }
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stToolbar"] {
  background: rgba(255,255,255,.92); border-radius: 999px; padding: 2px 8px;
  top: .55rem !important; right: 1rem !important; box-shadow: 0 2px 12px rgba(20,16,60,.22);
}
.block-container, [data-testid="stMainBlockContainer"] {
  width: min(1060px, calc(100% - 2.5rem)) !important; max-width: none !important;
  margin: 3.4rem auto 3rem !important; padding: 1.6rem 2.2rem 2.6rem !important;
  background: rgba(255,253,248,.98); border: 1px solid rgba(255,255,255,.75); border-radius: 28px;
  box-shadow: 0 26px 60px rgba(10,8,40,.30), inset 0 2px 0 rgba(255,255,255,.7);
}
/* The style block itself should not take up space in the layout */
[data-testid="stElementContainer"]:has(style), .element-container:has(style) { display: none !important; }

/* ---------- Section banner ---------- */
.uni-hero {
  position: relative; overflow: hidden; display: flex; align-items: center; gap: 1.1rem;
  padding: 1.15rem 1.4rem; margin: 0 0 1.4rem; border-radius: 22px; color: #fff;
  background: linear-gradient(120deg, var(--hero-a), var(--hero-b));
  box-shadow: 0 10px 24px rgba(20,16,60,.20);
}
.uni-hero::after {
  content: ""; position: absolute; right: -50px; top: -70px; width: 240px; height: 240px;
  border-radius: 50%; background: radial-gradient(circle, rgba(255,255,255,.28), transparent 68%); pointer-events: none;
}
.uni-hero .uni-hero-badge {
  flex: 0 0 auto; width: 58px; height: 58px; display: grid; place-items: center; font-size: 1.9rem;
  background: rgba(255,255,255,.2); border: 2px solid rgba(255,255,255,.55); border-radius: 18px;
}
.uni-hero .uni-hero-title {
  font-family: 'Baloo 2', cursive; font-weight: 800; font-size: clamp(1.55rem, 3vw, 2.1rem);
  line-height: 1.1; color: #fff !important;
}
.uni-hero .uni-hero-sub { color: rgba(255,255,255,.94) !important; font-size: 1rem; margin-top: .25rem; line-height: 1.4; }

/* ---------- Cards ---------- */
[data-testid="stVerticalBlockBorderWrapper"] {
  border: 1.5px solid var(--line) !important; border-radius: 18px !important; background: #fff;
  box-shadow: 0 4px 14px rgba(40,34,90,.05);
}
[data-testid="stExpander"] {
  border: 1.5px solid var(--line) !important; background: #fff !important; border-radius: 18px !important;
  box-shadow: 0 4px 14px rgba(40,34,90,.05); overflow: hidden;
}
[data-testid="stExpander"] summary { font-family: 'Baloo 2', cursive !important; font-size: 1.06rem !important; font-weight: 700 !important; }
[data-testid="stExpander"] summary:hover { background: var(--accent-soft); }
[data-testid="stMetric"] {
  background: #fff !important; border: 1.5px solid var(--line) !important; border-left: 6px solid var(--accent) !important;
  border-radius: 18px !important; padding: .9rem 1.1rem !important; box-shadow: 0 5px 16px rgba(40,34,90,.06) !important;
}
[data-testid="stMetricValue"] { font-family: 'Baloo 2', cursive !important; color: var(--accent-dark) !important; font-weight: 800 !important; }
.features-card {
  background: #fff; border: 1.5px solid var(--line); border-left: 6px solid var(--accent); border-radius: 18px;
  padding: 1rem 1.3rem; margin: .6rem 0 1rem; box-shadow: 0 5px 16px rgba(40,34,90,.05);
}
.features-card .features-title { font-family: 'Baloo 2', cursive; font-weight: 800; font-size: 1.15rem; color: var(--ink); margin-bottom: .35rem; }
.features-card ul { margin: 0; padding-left: 1.25rem; }
.features-card li { margin: .25rem 0; font-size: 1rem; }
.checklist-done-msg, .checklist-progress-msg { border-radius: 12px; padding: .45rem .8rem; font-weight: 700; font-size: .95rem; margin-top: .4rem; }
.checklist-done-msg { background: #e3f7ec; color: #1f6b47; }
.checklist-progress-msg { background: var(--accent-soft); color: var(--accent-dark); }
.stAlert { border-radius: 16px !important; border-width: 1.5px !important; }
[data-testid="stToast"] { border-radius: 16px !important; }
hr { border-color: var(--line) !important; }
[data-testid="stFileUploaderDropzone"] { border: 2px dashed var(--accent) !important; border-radius: 18px !important; background: var(--accent-soft) !important; }

/* ---------- The writing pad ---------- */
.stTextArea textarea {
  font-family: 'Patrick Hand', cursive !important; font-size: 1.38rem !important; line-height: 1.9 !important;
  color: #292744 !important; background-color: var(--paper) !important;
  background-image:
    linear-gradient(90deg, transparent 54px, rgba(255,135,111,.45) 54px, rgba(255,135,111,.45) 56px, transparent 56px),
    repeating-linear-gradient(transparent 0, transparent 35px, rgba(133,177,220,.27) 35px, rgba(133,177,220,.27) 36px) !important;
  background-attachment: local !important; border: 2px solid #e6dfca !important; border-radius: 18px !important;
  padding: 12px 18px 12px 70px !important;
  box-shadow: inset 0 2px 8px rgba(67,57,92,.06), 0 5px 14px rgba(67,57,92,.05) !important;
  caret-color: var(--accent) !important;
}
.stTextArea textarea:focus { border-color: var(--accent-light) !important; box-shadow: 0 0 0 4px rgba(107,99,217,.14), inset 0 2px 8px rgba(67,57,92,.05) !important; }
.stTextArea textarea::placeholder { color: #a09bb0 !important; opacity: 1 !important; }
.stTextInput input, .stNumberInput input, [data-testid="stDateInput"] input {
  font-family: 'Nunito', sans-serif !important; font-size: 1.02rem !important; background: #fffefb !important;
  color: var(--ink) !important; border: 2px solid #e5e0f2 !important; border-radius: 14px !important; min-height: 46px;
}
.stTextInput input:focus, .stNumberInput input:focus { border-color: var(--accent-light) !important; box-shadow: 0 0 0 3px rgba(107,99,217,.12) !important; }

/* ---------- Buttons ---------- */
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
  font-family: 'Baloo 2', cursive !important; font-size: 1.06rem !important; font-weight: 800 !important;
  border: 0 !important; border-radius: 16px !important; min-height: 48px; padding: .5rem 1.25rem !important;
  background: linear-gradient(135deg, var(--accent-light) 0%, var(--accent) 100%) !important;
  box-shadow: 0 5px 0 var(--accent-dark), 0 9px 18px rgba(20,16,60,.16) !important;
  transition: transform .15s ease, box-shadow .15s ease, filter .15s ease !important;
}
.stButton > button, .stButton > button *, .stDownloadButton > button, .stDownloadButton > button *,
[data-testid="stFormSubmitButton"] > button, [data-testid="stFormSubmitButton"] > button * { color: #fff !important; }
.stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
  transform: translateY(-2px) !important; filter: brightness(1.06);
  box-shadow: 0 7px 0 var(--accent-dark), 0 12px 20px rgba(20,16,60,.2) !important;
}
.stButton > button:active, .stDownloadButton > button:active { transform: translateY(3px) !important; box-shadow: 0 2px 0 var(--accent-dark) !important; }
.stButton > button:disabled { background: #d8d5e7 !important; box-shadow: 0 4px 0 #bcb8cf !important; }
.stButton > button:disabled, .stButton > button:disabled * { color: #7d7992 !important; }

/* ---------- Choice controls ---------- */
[data-testid="stRadio"] > label, [data-testid="stCheckbox"] label, [data-testid="stSelectbox"] label { font-weight: 700 !important; font-size: 1.02rem !important; }
[data-testid="stRadio"] [role="radiogroup"] { gap: .5rem !important; }
[data-testid="stRadio"] [role="radio"] { background: #fff; border: 1.5px solid #e5e0f2; border-radius: 14px; padding: .42rem .8rem; transition: border-color .15s, background .15s; }
[data-testid="stRadio"] [role="radio"]:hover { border-color: var(--accent-light); }
[data-testid="stRadio"] [role="radio"][aria-checked="true"] { border-color: var(--accent); background: var(--accent-soft); }
[data-testid="stRadio"] [role="radio"] p { font-size: 1rem !important; }
[data-testid="stCheckbox"] label { background: #faf9ff; border-radius: 12px; padding: .25rem .5rem; }
[data-testid="stSelectbox"] [data-baseweb="select"] > div, [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
  border: 2px solid #e5e0f2 !important; border-radius: 14px !important; background: #fffefb !important; min-height: 46px;
}
[data-testid="stToggle"] label { font-family: 'Baloo 2', cursive !important; font-size: 1.05rem !important; font-weight: 700 !important; }
.stProgress > div > div > div > div { background: linear-gradient(90deg, var(--accent-light), var(--accent), #ffd66b) !important; border-radius: 20px !important; }

/* ---------- Floating sidebar (hover or focus to open) ---------- */
[data-testid="stSidebar"] {
  position: fixed !important; top: 0 !important; left: 0 !important; height: 100vh !important;
  width: 300px !important; min-width: 300px !important; max-width: 300px !important; z-index: 999990 !important;
  background: #fcfbff !important; border-right: 1px solid #e3e0f1 !important; border-radius: 0 24px 24px 0 !important;
  box-shadow: inset 6px 0 0 var(--accent), 14px 0 40px rgba(20,16,60,.24) !important;
  transform: translateX(calc(-100% + 16px)) !important;
  transition: transform .28s cubic-bezier(.22,1,.36,1) !important;
}
[data-testid="stSidebar"]:hover, [data-testid="stSidebar"]:focus-within { transform: translateX(0) !important; }
[data-testid="stSidebar"]::after {
  content: "Menu"; position: absolute; top: 50%; right: -14px; transform: translateY(-50%);
  width: 30px; height: 92px; writing-mode: vertical-rl; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(180deg, var(--accent-light), var(--accent)); color: #fff;
  font-family: 'Baloo 2', cursive; font-weight: 700; font-size: .9rem; letter-spacing: .06em;
  border: 2px solid #fff; border-left: 0; border-radius: 0 14px 14px 0;
  box-shadow: 4px 4px 14px rgba(20,16,60,.26); cursor: pointer; transition: opacity .2s ease;
}
[data-testid="stSidebar"]:hover::after, [data-testid="stSidebar"]:focus-within::after { opacity: 0; pointer-events: none; }
[data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"], [data-testid="stSidebarHeader"] { display: none !important; }
[data-testid="stSidebarUserContent"] { padding: 1.2rem 1.15rem 1.6rem 1.4rem !important; }
[data-baseweb="popover"], [data-baseweb="menu"] { z-index: 999999 !important; }

.sb-brand { display: flex; align-items: center; gap: .8rem; padding: .1rem 0 1rem; border-bottom: 1px solid var(--line); margin-bottom: .3rem; }
.sb-brand img, .sb-brand svg { width: 54px; height: auto; flex: 0 0 auto; filter: drop-shadow(0 4px 6px rgba(55,48,100,.2)); }
.sb-brand .sb-brand-name { font-family: 'Baloo 2', cursive; font-weight: 800; font-size: 1.12rem; line-height: 1.1; color: var(--ink); }
.sb-brand .sb-brand-sub { font-size: .84rem; color: var(--muted); margin-top: .2rem; line-height: 1.3; }
.sb-label { font-family: 'Baloo 2', cursive; font-weight: 700; font-size: .95rem; color: var(--muted); margin: 1.05rem 0 .35rem; }
.sb-profile { display: flex; align-items: center; gap: .7rem; padding: .65rem .8rem; border-radius: 16px; background: var(--accent-soft); border: 1px solid var(--line); margin-bottom: .55rem; }
.sb-profile .sb-avatar {
  flex: 0 0 auto; width: 40px; height: 40px; border-radius: 50%; display: grid; place-items: center;
  background: linear-gradient(135deg, var(--accent-light), var(--accent)); color: #fff;
  font-family: 'Baloo 2', cursive; font-weight: 800; font-size: 1.2rem;
}
.sb-profile .sb-pname { font-weight: 800; color: var(--ink); line-height: 1.15; overflow-wrap: anywhere; }
.sb-profile .sb-pband { font-size: .82rem; color: var(--muted); line-height: 1.25; }

/* Navigation list (radio restyled) */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] { gap: .25rem !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radio"] {
  width: 100%; margin: 0; padding: .6rem .8rem !important; background: transparent !important;
  border: 1px solid transparent !important; border-radius: 14px !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radio"] > div:first-child:not(:has(p)) { display: none !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radio"]:hover { background: var(--accent-soft) !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radio"][aria-checked="true"] {
  background: var(--accent-soft) !important; border-color: var(--accent) !important; box-shadow: inset 4px 0 0 var(--accent);
}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radio"] p { font-family: 'Baloo 2', cursive; font-weight: 700; font-size: 1.04rem !important; margin: 0; }
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radio"][aria-checked="true"] p { color: var(--accent-dark); }
[data-testid="stSidebar"] label p { font-size: .92rem; font-weight: 700; }
[data-testid="stSidebar"] .stTextInput input { min-height: 42px; font-size: .98rem !important; }
[data-testid="stSidebar"] hr { margin: 1rem 0; }
[data-testid="stSidebar"] .stButton > button { min-height: 42px; font-size: 1rem !important; box-shadow: 0 4px 0 var(--accent-dark), 0 7px 14px rgba(20,16,60,.12) !important; }

/* ---------- Inky ---------- */
.mascot-wrap { display: flex; justify-content: center; align-items: center; padding: .45rem 0; filter: drop-shadow(0 8px 9px rgba(55,48,100,.13)); }
.mascot-wrap svg, .mascot-wrap img { max-width: 100%; height: auto; }

/* ---------- Accessibility and small screens ---------- */
button:focus-visible, input:focus-visible, textarea:focus-visible, [role="radio"]:focus-visible { outline: 3px solid #ff9b83 !important; outline-offset: 3px !important; }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition-duration: .01ms !important; } }
@media (max-width: 700px) {
  .block-container, [data-testid="stMainBlockContainer"] { padding: 1.1rem 1rem 2rem !important; border-radius: 22px; width: calc(100% - 1.5rem) !important; }
  .stTextArea textarea { font-size: 1.2rem !important; padding-left: 56px !important; }
  .uni-hero { flex-wrap: wrap; }
}

/* ---------- This app's own components, in the section colours ---------- */
.hero-banner {
  position: relative; overflow: hidden; display: flex; align-items: center; gap: 1.1rem;
  padding: 1.15rem 1.4rem; margin: 0 0 1.4rem; border-radius: 22px; color: #fff;
  background: linear-gradient(120deg, var(--hero-a), var(--hero-b));
  box-shadow: 0 10px 24px rgba(20,16,60,.20);
}
.hero-banner::after {
  content: ""; position: absolute; right: -50px; top: -70px; width: 240px; height: 240px;
  border-radius: 50%; background: radial-gradient(circle, rgba(255,255,255,.28), transparent 68%); pointer-events: none;
}
.hero-banner h1 { margin: 0 !important; font-size: clamp(1.55rem, 3vw, 2.1rem) !important; color: #fff !important; line-height: 1.1; }
.hero-banner p { margin: .25rem 0 0 0 !important; font-size: 1rem; color: rgba(255,255,255,.94) !important; line-height: 1.4; }
.adventure-card {
  background: #fff; border: 1.5px solid var(--line); border-left: 6px solid var(--accent); border-radius: 18px;
  padding: 1rem 1.3rem; margin-bottom: .9rem; box-shadow: 0 5px 16px rgba(40,34,90,.06);
}
.step-pill {
  display: inline-block; background: var(--accent-soft); color: var(--accent-dark); font-weight: 800;
  padding: .22rem .75rem; border-radius: 999px; font-size: .85rem; margin-bottom: .35rem;
}
.xp-bar-wrap { background: var(--line); border-radius: 999px; height: 14px; overflow: hidden; margin: .4rem 0 .2rem 0; }
.xp-bar-fill { background: linear-gradient(90deg, var(--accent-light), var(--accent), #ffd66b); height: 100%; border-radius: 999px; transition: width .5s ease; }
.badge-chip {
  display: inline-block; background: var(--accent-soft); border: 1.5px solid var(--line); border-radius: 14px;
  padding: .35rem .7rem; margin: .2rem .25rem .2rem 0; font-weight: 800; font-size: .88rem; color: var(--ink) !important;
}
.wagoll-box { background: var(--accent-soft); border-left: 5px solid var(--accent); padding: .75rem 1rem; border-radius: 12px; margin: .5rem 0; }
.rule-carousel-card {
  background: #fff; border: 1.5px solid var(--line); border-radius: 16px; padding: .95rem 1rem; min-height: 155px;
  box-shadow: 0 4px 12px rgba(40,34,90,.07); margin: .35rem 0 .5rem 0;
}
.rule-carousel-kicker {
  display: inline-block; background: var(--accent); color: #fff; font-weight: 800; font-size: .76rem;
  padding: .16rem .55rem; border-radius: 999px; margin-bottom: .45rem;
}
.rule-carousel-body { font-size: .98rem; line-height: 1.45; color: var(--ink); font-weight: 600; }
/* Orange written directly into the page markup follows the section colour instead */
[style*="#FF6F00"], [style*="#ff6f00"], [style*="#B25200"] { color: var(--accent-dark) !important; }
/* Sidebar sections */
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { font-size: 1.15rem !important; margin: .6rem 0 .3rem !important; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: var(--muted) !important; }
</style>
"""

UNIVERSE_CSS = {
    "Writing Dojo": """
:root { --accent:#6b63d9; --accent-light:#7a72e6; --accent-dark:#4a43b0; --accent-soft:#eeecff; --hero-a:#3d3499; --hero-b:#8a63d8; }
.stApp { background: linear-gradient(180deg, #1b1750 0%, #3a2f86 40%, #8a5fc7 72%, #f5a9b5 100%) !important; }
.stApp::before {
  background:
    radial-gradient(circle at 97% 13%, #fff6d4 0 34px, rgba(255,246,212,.28) 35px 62px, rgba(255,246,212,.08) 63px 110px, transparent 111px),
    radial-gradient(2.5px 2.5px at 18% 72%, #ffe58a 0 60%, transparent 100%),
    radial-gradient(2.5px 2.5px at 36% 82%, #ffe58a 0 60%, transparent 100%),
    radial-gradient(2.5px 2.5px at 61% 76%, #ffe58a 0 60%, transparent 100%),
    radial-gradient(2.5px 2.5px at 77% 86%, #ffe58a 0 60%, transparent 100%),
    radial-gradient(1.6px 1.6px at 32px 46px, #fff, transparent) 0 0 / 290px 210px,
    radial-gradient(1.2px 1.2px at 118px 88px, rgba(255,255,255,.9), transparent) 0 0 / 290px 210px,
    radial-gradient(1.4px 1.4px at 210px 30px, #fff, transparent) 0 0 / 290px 210px,
    radial-gradient(1px 1px at 70px 170px, rgba(255,255,255,.85), transparent) 0 0 / 290px 210px,
    radial-gradient(1.3px 1.3px at 150px 120px, #fff, transparent) 0 0 / 370px 260px,
    radial-gradient(1px 1px at 300px 200px, rgba(255,255,255,.8), transparent) 0 0 / 370px 260px;
  -webkit-mask-image: linear-gradient(180deg, #000 0%, #000 62%, transparent 100%);
  mask-image: linear-gradient(180deg, #000 0%, #000 62%, transparent 100%);
}
.stApp::after {
  height: 38vh;
  background:
    radial-gradient(70% 90% at 12% 100%, #2a2268 0 98%, transparent 100%),
    radial-gradient(80% 75% at 62% 100%, #342a7a 0 98%, transparent 100%),
    radial-gradient(60% 60% at 100% 100%, #1f1a56 0 98%, transparent 100%);
}
""",
    "Marking Arena": """
:root { --accent:#d0431c; --accent-light:#de5a32; --accent-dark:#a83214; --accent-soft:#fff0e6; --hero-a:#c4302b; --hero-b:#ff9a3c; }
.stApp { background: linear-gradient(180deg, #ff6b4a 0%, #ff9a3c 42%, #ffd27a 78%, #ffe9b5 100%) !important; }
.stApp::before {
  background:
    radial-gradient(circle at 50% 100%, #fff3b0 0 90px, rgba(255,243,176,.45) 91px 170px, transparent 171px),
    repeating-conic-gradient(from -90deg at 50% 100%, rgba(255,255,255,.20) 0deg 5deg, transparent 5deg 15deg);
  -webkit-mask-image: radial-gradient(circle at 50% 100%, #000 0, #000 35%, transparent 90%);
  mask-image: radial-gradient(circle at 50% 100%, #000 0, #000 35%, transparent 90%);
}
.stApp::after {
  height: 18vh;
  background:
    radial-gradient(circle at 15px 15px, #5a1a3d 0 11px, transparent 12px) 0 0 / 30px 30px repeat-x,
    linear-gradient(#5a1a3d, #5a1a3d) 0 15px / 100% 100% no-repeat,
    radial-gradient(circle at 30px 15px, #8f3350 0 11px, transparent 12px) 0 -12px / 30px 30px repeat-x,
    linear-gradient(#8f3350, #8f3350) 0 3px / 100% 100% no-repeat;
}
""",
    "Vocabulary Vault": """
:root { --accent:#0b7f72; --accent-light:#0f8f7e; --accent-dark:#086256; --accent-soft:#e2f7f3; --hero-a:#0a5d6b; --hero-b:#22b99c; }
.stApp { background: linear-gradient(165deg, #04252f 0%, #0a4f5a 48%, #0f7f6e 100%) !important; }
.stApp::before {
  background:
    radial-gradient(ellipse at 20% 15%, rgba(120,255,230,.22), transparent 45%),
    radial-gradient(ellipse at 85% 30%, rgba(160,200,255,.18), transparent 40%),
    radial-gradient(1.6px 1.6px at 40px 60px, rgba(255,255,255,.9), transparent) 0 0 / 260px 200px,
    radial-gradient(1.2px 1.2px at 170px 140px, rgba(190,255,245,.9), transparent) 0 0 / 260px 200px,
    linear-gradient(60deg, rgba(255,255,255,.03) 25%, transparent 25.5%) 0 0 / 110px 190px,
    linear-gradient(120deg, rgba(255,255,255,.025) 25%, transparent 25.5%) 0 0 / 110px 190px;
}
.stApp::after {
  height: 36vh;
  background:
    linear-gradient(to top left, #1fd1b8 50%, transparent 50%) 4vw 100% / 34px 230px no-repeat,
    linear-gradient(to top right, #12a897 50%, transparent 50%) calc(4vw + 34px) 100% / 34px 230px no-repeat,
    linear-gradient(to top left, #7be3c3 50%, transparent 50%) 18vw 100% / 28px 150px no-repeat,
    linear-gradient(to top right, #3fbf9c 50%, transparent 50%) calc(18vw + 28px) 100% / 28px 150px no-repeat,
    linear-gradient(to top left, #34d4e0 50%, transparent 50%) 36vw 100% / 44px 300px no-repeat,
    linear-gradient(to top right, #1a9db0 50%, transparent 50%) calc(36vw + 44px) 100% / 44px 300px no-repeat,
    linear-gradient(to top left, #5eead4 50%, transparent 50%) 58vw 100% / 30px 190px no-repeat,
    linear-gradient(to top right, #14b8a6 50%, transparent 50%) calc(58vw + 30px) 100% / 30px 190px no-repeat,
    linear-gradient(to top left, #67e8f9 50%, transparent 50%) 74vw 100% / 40px 270px no-repeat,
    linear-gradient(to top right, #22a6c4 50%, transparent 50%) calc(74vw + 40px) 100% / 40px 270px no-repeat,
    linear-gradient(to top left, #86efac 50%, transparent 50%) 90vw 100% / 28px 170px no-repeat,
    linear-gradient(to top right, #34c58a 50%, transparent 50%) calc(90vw + 28px) 100% / 28px 170px no-repeat;
}
""",
    "Grammar & Punctuation": """
:root { --accent:#be185d; --accent-light:#db2777; --accent-dark:#9d174d; --accent-soft:#fdecf4; --hero-a:#9d174d; --hero-b:#f472b6; }
.stApp { background: linear-gradient(180deg, #5b2a86 0%, #b04fa0 36%, #f48fb1 68%, #ffd7b5 100%) !important; }
.stApp::before {
  background:
    radial-gradient(circle at 50% 100%, rgba(255,236,179,.75) 0 90px, rgba(255,236,179,.28) 91px 240px, transparent 241px),
    radial-gradient(3px 3px at 30px 40px, rgba(255,255,255,.9), transparent) 0 0 / 210px 160px,
    radial-gradient(2.5px 2.5px at 120px 100px, rgba(255,214,235,.95), transparent) 0 0 / 210px 160px,
    radial-gradient(3.5px 3.5px at 170px 20px, rgba(255,255,255,.85), transparent) 0 0 / 210px 160px,
    radial-gradient(2.5px 2.5px at 60px 140px, rgba(255,200,225,.9), transparent) 0 0 / 210px 160px,
    radial-gradient(3px 3px at 90px 60px, rgba(255,255,255,.8), transparent) 0 0 / 290px 220px,
    radial-gradient(2.5px 2.5px at 230px 170px, rgba(255,214,235,.9), transparent) 0 0 / 290px 220px;
}
.stApp::after {
  height: 36vh;
  background:
    radial-gradient(circle 52px at 5vw 52%, #f9a8d4 0 98%, transparent 100%),
    radial-gradient(circle 66px at 10vw 40%, #f472b6 0 98%, transparent 100%),
    radial-gradient(circle 48px at 15vw 55%, #fbcfe8 0 98%, transparent 100%),
    linear-gradient(#4a1a3a, #4a1a3a) calc(10vw - 6px) 100% / 12px 46% no-repeat,
    radial-gradient(circle 46px at 35vw 62%, #fbcfe8 0 98%, transparent 100%),
    radial-gradient(circle 60px at 40vw 50%, #ec4899 0 98%, transparent 100%),
    radial-gradient(circle 44px at 45vw 64%, #f9a8d4 0 98%, transparent 100%),
    linear-gradient(#4a1a3a, #4a1a3a) calc(40vw - 6px) 100% / 12px 40% no-repeat,
    radial-gradient(circle 54px at 80vw 50%, #f9a8d4 0 98%, transparent 100%),
    radial-gradient(circle 68px at 86vw 38%, #f472b6 0 98%, transparent 100%),
    radial-gradient(circle 50px at 92vw 54%, #fbcfe8 0 98%, transparent 100%),
    linear-gradient(#4a1a3a, #4a1a3a) calc(86vw - 6px) 100% / 12px 48% no-repeat,
    radial-gradient(90% 38% at 25% 100%, #6b2a5a 0 98%, transparent 100%),
    radial-gradient(80% 32% at 80% 100%, #5a2150 0 98%, transparent 100%);
}
""",
    "Language Arts": """
:root { --accent:#15803d; --accent-light:#178f45; --accent-dark:#0f5f2d; --accent-soft:#e8f6ec; --hero-a:#0f5f2d; --hero-b:#3fae6a; }
.stApp { background: linear-gradient(180deg, #07211c 0%, #0d3b2e 48%, #1d6e48 100%) !important; }
.stApp::before {
  background:
    radial-gradient(circle at 88% 14%, #fff6d4 0 30px, rgba(255,246,212,.26) 31px 58px, rgba(255,246,212,.07) 59px 100px, transparent 101px),
    radial-gradient(3px 3px at 16% 70%, #ffe58a 0 60%, transparent 100%),
    radial-gradient(3px 3px at 30% 80%, #ffe58a 0 60%, transparent 100%),
    radial-gradient(3px 3px at 52% 74%, #ffe58a 0 60%, transparent 100%),
    radial-gradient(3px 3px at 70% 84%, #ffe58a 0 60%, transparent 100%),
    radial-gradient(3px 3px at 84% 66%, #ffe58a 0 60%, transparent 100%),
    radial-gradient(1.5px 1.5px at 30px 40px, rgba(255,255,255,.9), transparent) 0 0 / 250px 190px,
    radial-gradient(1.2px 1.2px at 140px 100px, rgba(220,255,235,.9), transparent) 0 0 / 250px 190px,
    radial-gradient(1.4px 1.4px at 200px 20px, #fff, transparent) 0 0 / 250px 190px;
  -webkit-mask-image: linear-gradient(180deg, #000 0%, #000 70%, transparent 100%);
  mask-image: linear-gradient(180deg, #000 0%, #000 70%, transparent 100%);
}
.stApp::after {
  height: 44vh;
  background-image:
    conic-gradient(from 143.1deg at 50% 0%, #0b3d2e 0deg 73.7deg, transparent 73.7deg),
    conic-gradient(from 146.3deg at 50% 0%, #0b3d2e 0deg 67.4deg, transparent 67.4deg),
    conic-gradient(from 150.6deg at 50% 0%, #0b3d2e 0deg 58.9deg, transparent 58.9deg),
    linear-gradient(#2b1a12, #2b1a12),
    conic-gradient(from 143.1deg at 50% 0%, #0f4a35 0deg 73.7deg, transparent 73.7deg),
    conic-gradient(from 146.3deg at 50% 0%, #0f4a35 0deg 67.4deg, transparent 67.4deg),
    conic-gradient(from 150.6deg at 50% 0%, #0f4a35 0deg 58.9deg, transparent 58.9deg),
    linear-gradient(#2b1a12, #2b1a12),
    conic-gradient(from 143.1deg at 50% 0%, #0c402f 0deg 73.7deg, transparent 73.7deg),
    conic-gradient(from 146.3deg at 50% 0%, #0c402f 0deg 67.4deg, transparent 67.4deg),
    conic-gradient(from 150.6deg at 50% 0%, #0c402f 0deg 58.9deg, transparent 58.9deg),
    linear-gradient(#2b1a12, #2b1a12),
    conic-gradient(from 143.1deg at 50% 0%, #104d37 0deg 73.7deg, transparent 73.7deg),
    conic-gradient(from 146.3deg at 50% 0%, #104d37 0deg 67.4deg, transparent 67.4deg),
    conic-gradient(from 150.6deg at 50% 0%, #104d37 0deg 58.9deg, transparent 58.9deg),
    linear-gradient(#2b1a12, #2b1a12),
    conic-gradient(from 143.1deg at 50% 0%, #0b3d2e 0deg 73.7deg, transparent 73.7deg),
    conic-gradient(from 146.3deg at 50% 0%, #0b3d2e 0deg 67.4deg, transparent 67.4deg),
    conic-gradient(from 150.6deg at 50% 0%, #0b3d2e 0deg 58.9deg, transparent 58.9deg),
    linear-gradient(#2b1a12, #2b1a12),
    conic-gradient(from 143.1deg at 50% 0%, #0f4a35 0deg 73.7deg, transparent 73.7deg),
    conic-gradient(from 146.3deg at 50% 0%, #0f4a35 0deg 67.4deg, transparent 67.4deg),
    conic-gradient(from 150.6deg at 50% 0%, #0f4a35 0deg 58.9deg, transparent 58.9deg),
    linear-gradient(#2b1a12, #2b1a12),
    conic-gradient(from 143.1deg at 50% 0%, #0c402f 0deg 73.7deg, transparent 73.7deg),
    conic-gradient(from 146.3deg at 50% 0%, #0c402f 0deg 67.4deg, transparent 67.4deg),
    conic-gradient(from 150.6deg at 50% 0%, #0c402f 0deg 58.9deg, transparent 58.9deg),
    linear-gradient(#2b1a12, #2b1a12),
    radial-gradient(80% 26% at 20% 100%, #082b21 0 98%, transparent 100%),
    radial-gradient(70% 22% at 82% 100%, #06231b 0 98%, transparent 100%);
  background-position:
    left calc(5vw - 69px) bottom 25px,
    left calc(5vw - 55px) bottom 80px,
    left calc(5vw - 40px) bottom 129px,
    left calc(5vw - 6px) bottom 0px,
    left calc(13vw - 51px) bottom 19px,
    left calc(13vw - 41px) bottom 60px,
    left calc(13vw - 30px) bottom 95px,
    left calc(13vw - 4px) bottom 0px,
    left calc(30vw - 60px) bottom 22px,
    left calc(30vw - 48px) bottom 70px,
    left calc(30vw - 35px) bottom 112px,
    left calc(30vw - 5px) bottom 0px,
    left calc(47vw - 48px) bottom 18px,
    left calc(47vw - 38px) bottom 56px,
    left calc(47vw - 28px) bottom 90px,
    left calc(47vw - 4px) bottom 0px,
    left calc(63vw - 72px) bottom 26px,
    left calc(63vw - 58px) bottom 84px,
    left calc(63vw - 42px) bottom 134px,
    left calc(63vw - 6px) bottom 0px,
    left calc(80vw - 54px) bottom 20px,
    left calc(80vw - 43px) bottom 63px,
    left calc(80vw - 32px) bottom 101px,
    left calc(80vw - 4px) bottom 0px,
    left calc(94vw - 66px) bottom 24px,
    left calc(94vw - 53px) bottom 77px,
    left calc(94vw - 38px) bottom 123px,
    left calc(94vw - 6px) bottom 0px,
    0 0,
    0 0;
  background-size:
    138px 92px,
    110px 83px,
    80px 71px,
    12px 34px,
    102px 68px,
    82px 61px,
    60px 53px,
    8px 26px,
    120px 80px,
    96px 72px,
    70px 62px,
    10px 30px,
    96px 64px,
    77px 58px,
    56px 50px,
    8px 24px,
    144px 96px,
    115px 86px,
    84px 74px,
    12px 36px,
    108px 72px,
    86px 65px,
    63px 56px,
    9px 27px,
    132px 88px,
    106px 79px,
    77px 68px,
    11px 33px,
    100% 100%,
    100% 100%;
  background-repeat: no-repeat;
}
""",
    "Progress & Badges": """
:root { --accent:#5b5bd6; --accent-light:#7c7cf0; --accent-dark:#3e3eab; --accent-soft:#ecedff; --hero-a:#1a2a80; --hero-b:#7a4fd8; }
.stApp {
  background:
    radial-gradient(ellipse at 15% 8%, rgba(120,90,255,.55), transparent 48%),
    radial-gradient(ellipse at 88% 78%, rgba(255,110,170,.30), transparent 45%),
    radial-gradient(ellipse at 50% 100%, rgba(40,160,255,.28), transparent 50%),
    linear-gradient(180deg, #060a2b 0%, #0c1347 55%, #1a1160 100%) !important;
}
.stApp::before {
  background:
    radial-gradient(circle 64px at 100% 66%, #ffe6b0 0, #f2a35f 55%, #c8553d 97%, transparent 100%),
    radial-gradient(circle 26px at 2.5% 84%, #b6fff1 0, #4fd1c5 60%, #1d8f9a 96%, transparent 100%),
    radial-gradient(1.7px 1.7px at 24px 40px, #fff, transparent) 0 0 / 230px 170px,
    radial-gradient(1.2px 1.2px at 130px 90px, rgba(255,255,255,.9), transparent) 0 0 / 230px 170px,
    radial-gradient(1.5px 1.5px at 190px 20px, #fff, transparent) 0 0 / 230px 170px,
    radial-gradient(1px 1px at 60px 140px, rgba(255,255,255,.85), transparent) 0 0 / 230px 170px,
    radial-gradient(1.4px 1.4px at 100px 60px, #fff, transparent) 0 0 / 330px 250px,
    radial-gradient(1px 1px at 260px 190px, rgba(255,255,255,.8), transparent) 0 0 / 330px 250px,
    radial-gradient(1.2px 1.2px at 40px 220px, rgba(200,210,255,.9), transparent) 0 0 / 330px 250px;
}
.stApp::after { height: 30vh; background: radial-gradient(60% 60% at 50% 110%, rgba(255,120,200,.25), transparent 70%); }
""",
}

UNIVERSE_CSS["Reading"] = READING_UNIVERSE_CSS
UNIVERSE_CSS["Home"] = HOME_UNIVERSE_CSS
UNIVERSE_CSS["Spelling"] = SPELLING_UNIVERSE_CSS
UNIVERSE_CSS["Game"] = """
:root { --accent:#6d28d9; --accent-light:#8b5cf6; --accent-dark:#4c1d95; --accent-soft:#f1eaff; --hero-a:#4c1d95; --hero-b:#ec4899; }
.stApp { background: linear-gradient(180deg, #120d3a 0%, #2b1a73 45%, #5b2a9c 80%, #8b3fb0 100%) !important; }
.stApp::before {
  background:
    radial-gradient(2px 2px at 12% 18%, #fff 0 60%, transparent 100%),
    radial-gradient(2px 2px at 28% 42%, #ffe08a 0 60%, transparent 100%),
    radial-gradient(3px 3px at 47% 12%, #fff 0 60%, transparent 100%),
    radial-gradient(2px 2px at 63% 33%, #9be7ff 0 60%, transparent 100%),
    radial-gradient(3px 3px at 79% 16%, #fff 0 60%, transparent 100%),
    radial-gradient(2px 2px at 91% 48%, #ffe08a 0 60%, transparent 100%),
    radial-gradient(circle at 85% 12%, #fff3c4 0 28px, rgba(255,243,196,.3) 29px 56px, transparent 57px);
}
.stApp::after {
  height: 20vh;
  background:
    linear-gradient(135deg, #2a1a66 25%, transparent 25%) -20px 0 / 40px 40px,
    linear-gradient(225deg, #2a1a66 25%, transparent 25%) -20px 0 / 40px 40px,
    linear-gradient(#2a1a66, #2a1a66) 0 24px / 100% 100% no-repeat;
}
"""


def accent_for(nav_choice):
    """The accent colour of a section's theme, for its button on the Home screen."""
    for name, scene in UNIVERSE_CSS.items():
        if name in str(nav_choice):
            m = re.search(r"--accent:\s*(#[0-9a-fA-F]{3,8})", scene)
            if m:
                return m.group(1)
    return "#6b63d9"


def universe_css_for(nav_choice):
    """Background and accent colours for the section the student is in."""
    for name, scene in UNIVERSE_CSS.items():
        if name in str(nav_choice):
            return "<style>" + scene + "</style>"
    return ""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ------------------------------------------------------------------
# OpenRouter Configuration & Model Routing
# ------------------------------------------------------------------
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
APP_TITLE = "The Writing Adventure"
APP_REFERER = "https://the-writing-adventure.streamlit.app"

# FREE MODELS ONLY. The app can never call a paid model: any model that is not on the
# free list is refused by call_openrouter, even if it is passed in by mistake.
FREE_ROUTER = "openrouter/free"

FREE_TEXT_MODELS = [
    FREE_ROUTER,
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "google/gemma-3-27b-it:free",
]
FREE_VISION_MODELS = [
    FREE_ROUTER,
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "google/gemma-3-27b-it:free",
]
MODEL_TIMEOUT = 25.0   # give up on a busy free model quickly and try the next one


def is_free_model(model):
    return model == FREE_ROUTER or str(model).endswith(":free")


def free_only(models):
    """Keep only free models (this is the guard that makes paid models impossible)."""
    return [m for m in models if is_free_model(m)]


MAX_TOKENS = {
    "whole_prompt": 400,
    "block_guide": 650,
    "feedback": 320,
    "toolkit": 700,
    "worksheet": 1300,
    "mark": 1800,
    "quiz": 1200,
    "transcribe": 1500,
}

# ------------------------------------------------------------------
# Secrets / Environment Helpers
# ------------------------------------------------------------------
def get_secret(name, default=""):
    try:
        if name in st.secrets and str(st.secrets[name]).strip():
            return str(st.secrets[name]).strip()
    except Exception:
        pass

    if name in ("OPENROUTER_API_KEY", "openrouter_api_key"):
        try:
            if "openrouter" in st.secrets:
                or_sec = st.secrets["openrouter"]
                for k in ("api_key", "OPENROUTER_API_KEY", "key"):
                    if k in or_sec and str(or_sec[k]).strip():
                        return str(or_sec[k]).strip()
        except Exception:
            pass

    if name in ("SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_KEY"):
        try:
            if "supabase" in st.secrets:
                sb_sec = st.secrets["supabase"]
                alias_map = {
                    "SUPABASE_URL": ("url", "SUPABASE_URL"),
                    "SUPABASE_ANON_KEY": ("key", "anon_key", "SUPABASE_ANON_KEY", "SUPABASE_KEY"),
                    "SUPABASE_KEY": ("key", "SUPABASE_KEY", "SUPABASE_ANON_KEY"),
                }
                for k in alias_map.get(name, (name,)):
                    if k in sb_sec and str(sb_sec[k]).strip():
                        return str(sb_sec[k]).strip()
        except Exception:
            pass

    return os.environ.get(name, default).strip()
# ------------------------------------------------------------------
# OpenRouter Client & Resilient Fallback Loop
# ------------------------------------------------------------------
@st.cache_resource
def get_openrouter_client(api_key):
    return OpenAI(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": APP_REFERER,
            "X-Title": APP_TITLE,
        },
        timeout=45.0,
    )


def call_openrouter(messages, models=None, max_tokens=700, temperature=0.7):
    """Try each free model in turn. Paid models are never used."""
    api_key = get_secret("OPENROUTER_API_KEY")
    if not api_key:
        print("[inky] OPENROUTER_API_KEY is missing")
        raise RuntimeError("Inky can't reach its helper right now. Please tell your teacher or parent.")
    client = get_openrouter_client(api_key)
    requested = list(models or FREE_TEXT_MODELS)
    models = free_only(requested)
    for skipped in set(requested) - set(models):
        print(f"[inky] refused to use non-free model: {skipped}")
    errors = []
    for model in models:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=MODEL_TIMEOUT,
            )
            text = (resp.choices[0].message.content or "").strip()
            if not text:
                raise RuntimeError("Empty response from model.")
            st.session_state["last_model_used"] = model
            return text
        except Exception as exc:
            msg = str(exc)
            errors.append(f"{model}: {msg[:110]}")
            low = msg.lower()
            if "401" in low or "invalid api key" in low:
                print("[inky] OpenRouter rejected the API key")
                raise RuntimeError("Inky can't reach its helper right now. Please tell your teacher or parent.")
    print("[inky] every free model failed: " + " || ".join(errors))
    raise RuntimeError("Inky is very busy right now. Please try again in a moment.")


def _fix_json_line(line):
    """One "key": "value" line: swap stray double quotes inside the value for apostrophes."""
    m = re.match(r'^(\s*"[^"\\]+"\s*:\s*)"(.*)"(\s*,?)\s*$', line)
    if not m:
        return line
    head, body, tail = m.groups()
    body = re.sub(r'(?<!\\)"', "'", body)
    return f'{head}"{body}"{tail}'


def _repair_json(text):
    """Fix the usual slips free models make: smart quotes, stray quotes, missing or extra commas."""
    t = text.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
    t = re.sub(r",\s*([}\]])", r"\1", t)                      # trailing commas
    lines = [_fix_json_line(line) for line in t.splitlines()]
    for i in range(len(lines) - 1):                               # missing commas between lines
        cur, nxt = lines[i].rstrip(), lines[i + 1].lstrip()
        if cur and nxt.startswith('"') and re.search(r'("|\}|\]|\d|true|false|null)$', cur):
            lines[i] = cur + ","
    return "\n".join(lines)


def parse_json_block(raw_text):
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw_text.strip(), flags=re.M).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start:end + 1]
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return json.loads(_repair_json(cleaned))


JSON_SYSTEM_PROMPT = (
    "Return ONLY valid JSON matching the requested schema. No markdown fences. "
    "Use double quotes only around keys and values. Inside any text value use single quotes, "
    "never double quotes, and keep each value on one line."
)


def call_json(prompt_text, task_key, models=None, temperature=0.55):
    """Ask for JSON. If the answer can't be read, repair it, and if that fails ask once more."""
    last_error = None
    for attempt in range(2):
        raw = call_openrouter(
            [
                {"role": "system", "content": JSON_SYSTEM_PROMPT},
                {"role": "user", "content": prompt_text},
            ],
            models=models or FREE_TEXT_MODELS,
            max_tokens=MAX_TOKENS[task_key],
            temperature=temperature if attempt == 0 else max(0.1, temperature - 0.3),
        )
        try:
            return parse_json_block(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = exc
            print(f"[inky] unreadable JSON (attempt {attempt + 1}): {exc} | start of reply: {raw[:200]!r}")
    raise RuntimeError("Inky got in a muddle. Please press the button again.") from last_error


def friendly_error(exc):
    """What a child sees. The real error goes to the logs."""
    print(f"[inky] error: {exc}")
    text = str(exc)
    return text if text.startswith("Inky") else "Something went wrong. Please try again in a moment."


# ------------------------------------------------------------------
# Image Preparation & Handwriting OCR
# ------------------------------------------------------------------
def compress_image_to_base64(uploaded_file, max_side=1280):
    img = Image.open(uploaded_file).convert("RGB")
    w, h = img.size
    if max(w, h) > max_side:
        scale = max_side / float(max(w, h))
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=82, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def transcribe_handwriting(uploaded_files):
    images_b64 = [compress_image_to_base64(f) for f in uploaded_files]
    return call_openrouter(
        transcription_messages(images_b64),
        models=FREE_VISION_MODELS,
        max_tokens=MAX_TOKENS["transcribe"],
        temperature=0.1,
    )


# ------------------------------------------------------------------
# Printable Worksheet HTML Builder
# ------------------------------------------------------------------
def build_worksheet_html(student_name, age_band, genre, subgenre, title, ws_data):
    mission = ws_data.get("mission", "")
    blocks = ws_data.get("blocks", [])
    block_html = []
    for idx, b in enumerate(blocks, 1):
        phrases = " &nbsp;•&nbsp; ".join(b.get("phrases", []))
        vocab_items = "".join(
            f"<li><b>{v.get('word','')}</b>: {v.get('definition','')}</li>"
            for v in b.get("vocab", [])
        )
        block_html.append(f"""
        <div class="block">
          <div class="block-head">Step {idx}: {b.get('label','')}</div>
          <p class="prompt"><b>Your Goal:</b> {b.get('prompt','')}</p>
          <div class="wagoll"><b>Model Example (WAGOLL):</b> {b.get('wagoll','')}</div>
          <div class="helpers">
            <div><b>Sentence Starters:</b> {phrases}</div>
            <ul>{vocab_items}</ul>
          </div>
          <div class="lines">
            <div></div><div></div><div></div><div></div><div></div>
          </div>
        </div>
        """)
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title} - Writing Worksheet</title>
<style>
  body {{ font-family: Arial, sans-serif; color: #1B3B3A; max-width: 780px; margin: 20px auto; padding: 0 18px; }}
  .top {{ border: 2px solid #FF6F00; border-radius: 12px; padding: 14px 18px; background: #FFF9ED; }}
  h1 {{ margin: 0 0 6px 0; color: #FF6F00; font-size: 22px; }}
  .meta {{ font-size: 13px; margin-bottom: 6px; }}
  .block {{ border: 1.5px solid #CFD8DC; border-radius: 10px; padding: 12px 14px; margin-top: 14px; page-break-inside: avoid; }}
  .block-head {{ font-weight: bold; font-size: 16px; color: #1E3F3D; margin-bottom: 4px; }}
  .prompt {{ margin: 4px 0; }}
  .wagoll {{ background: #F1F8E9; border-left: 4px solid #66BB6A; padding: 6px 10px; font-size: 13px; margin: 6px 0; }}
  .helpers {{ font-size: 12.5px; color: #37474F; }}
  .helpers ul {{ margin: 4px 0 6px 18px; padding: 0; }}
  .lines div {{ border-bottom: 1px solid #90A4AE; height: 26px; }}
  @media print {{ body {{ margin: 0; }} }}
</style>
</head>
<body>
  <div class="top">
    <h1>🦉 The Writing Adventure — {title}</h1>
    <div class="meta"><b>Writer:</b> {student_name or '________________'} &nbsp;|&nbsp;
    <b>Level:</b> {age_band} &nbsp;|&nbsp; <b>Genre:</b> {genre} ({subgenre}) &nbsp;|&nbsp;
    <b>Date:</b> {datetime.now().strftime('%d %b %Y')}</div>
    <div><b>Mission:</b> {mission}</div>
  </div>
  {''.join(block_html)}
</body>
</html>"""


# ------------------------------------------------------------------
# Session State Defaults & Gamification Helpers
# ------------------------------------------------------------------
def init_state():
    defaults = {
        "student_name": (st.session_state.get("student_profile") or {}).get("display_name", ""),
        "age_band": AGE_BANDS[0],
        "xp": 0,
        "badges": ["🌱 First Steps"],
        "local_history": [],
        "local_vocab": [
            {"word": "reluctant", "meaning": "unwilling and hesitant to do something",
             "example": "Leo was reluctant to step into the shadowy cave."},
            {"word": "peculiar", "meaning": "strange or unusual in an interesting way",
             "example": "A peculiar ticking sound came from inside the brass box."},
            {"word": "determined", "meaning": "having made a firm decision and not giving up",
             "example": "Maya was determined to finish her story before sunset."},
        ],
        "toolkit_cache": {},
        "last_marking": None,
        "last_worksheet": None,
        "quiz_data": None,
        "quiz_score": None,
        "quiz_word_history": [],
        "arena_text": "",
        "grammar_done": [],
        "grammar_lessons_done": [],
        "language_done": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def award_xp(points, badge=None):
    st.session_state["xp"] += points
    try:
        add_xp(points)  # save to the student's account, so the XP never restarts
    except Exception as exc:
        print(f"[inky] could not save XP to the account: {exc}")
    if badge and badge not in st.session_state["badges"]:
        st.session_state["badges"].append(badge)
    xp = st.session_state["xp"]
    if xp >= 100 and "⭐ Rising Author" not in st.session_state["badges"]:
        st.session_state["badges"].append("⭐ Rising Author")
    if xp >= 250 and "🏆 Master Storyteller" not in st.session_state["badges"]:
        st.session_state["badges"].append("🏆 Master Storyteller")


def safe_log_activity(*args, **kwargs):
    """Save an activity to the student's account without ever breaking the page."""
    kwargs.setdefault("update_profile_xp", False)
    try:
        return log_student_activity(*args, **kwargs)
    except Exception as exc:
        print(f"[inky] could not save activity: {exc}")
        return False


def safe_save_vocab(*args, **kwargs):
    """Save a word to the student's private word list without ever breaking the page."""
    try:
        return upsert_student_vocabulary(*args, **kwargs)
    except Exception as exc:
        print(f"[inky] could not save word: {exc}")
        return False


def level_info(xp):
    levels = [
        (0, "Apprentice Scribe"),
        (60, "Word Explorer"),
        (140, "Paragraph Builder"),
        (250, "Story Crafter"),
        (400, "Grand Wordsmith"),
    ]
    current_name = levels[0][1]
    next_threshold = levels[1][0]
    prev_threshold = 0
    for idx, (thresh, name) in enumerate(levels):
        if xp >= thresh:
            current_name = name
            prev_threshold = thresh
            next_threshold = levels[idx + 1][0] if idx + 1 < len(levels) else thresh + 150
    pct = min(100, int(((xp - prev_threshold) / max(1, next_threshold - prev_threshold)) * 100))
    return current_name, pct, next_threshold


def personal_instruction():
    name = st.session_state.get("student_name", "").strip()
    if name:
        return f"Address the student warmly by their first name ({name})."
    return "Address the student warmly as 'young writer'."


# ------------------------------------------------------------------
# Marking helpers: safe scores, care notes, and the gentle results screen
# ------------------------------------------------------------------
def _score_int(value):
    """Turn whatever the marker returned (3, 3.6, "3", "3/5", None) into a whole number, or 0."""
    try:
        if isinstance(value, str):
            value = value.split("/")[0]
        return int(round(float(value)))
    except Exception:
        return 0


def _log_care(check, section):
    """Remember that a care message was shown. Only the category is saved, never the writing."""
    if check is not None and check.status == "care":
        safe_log_activity(
            "wellbeing_flag", section, "Care message shown", xp_earned=0,
            details={"category": check.category},
        )


def _ratio(score, mx):
    return 0.0 if not mx else max(0.0, min(1.0, score / mx))


def _stars_for(ratio):
    """1 to 5 stars. A child who has tried always gets at least one."""
    return max(1, min(5, math.ceil(ratio * 5)))


def _level_label(ratio):
    if ratio < 0.35:
        return "Just starting 🌱"
    if ratio < 0.6:
        return "Growing 🌿"
    if ratio < 0.8:
        return "Getting strong 🌳"
    return "Shining ✨"


def _stars_html(n, size="1.5rem"):
    return (
        f'<span style="color:#F5A623;font-size:{size};letter-spacing:.08em;">{"★" * n}</span>'
        f'<span style="color:#d6d0bd;font-size:{size};letter-spacing:.08em;">{"★" * (5 - n)}</span>'
    )


def _bar_html(ratio, color):
    pct = max(8, int(round(ratio * 100)))
    return (
        '<div style="background:#e6e0f4;border-radius:999px;height:16px;overflow:hidden;">'
        f'<div style="width:{pct}%;height:100%;background:{color};border-radius:999px;"></div></div>'
    )


def render_marking_feedback(res, rubric_key, age_band):
    """Feedback first, then growth stars or bars. No marks are shown here."""
    max_map = RUBRICS[rubric_key]["max"]
    lower = str(age_band).startswith("Lower")
    cats = ("Wc", "Wv", "Wg", "Ws", "Ww")
    st.markdown("---")
    st.markdown("### 💬 Inky's feedback")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.success(f"**🌟 Two Stars (Strengths)**\n\n{res.get('strengths', '')}")
    with c2:
        st.info(f"**💡 Next Steps**\n\n{res.get('improvements', '')}")
    with c3:
        st.warning(f"**✨ Inky's Wish**\n\n{res.get('wish', '')}")
    if res.get("cap_note"):
        st.info("🌱 Next time, try writing a little more (61 words or more) so Inky can see all of your skills.")

    st.markdown("### 🌱 How your writing skills are growing")
    total_max = sum(max_map[c] for c in cats)
    overall = _ratio(res["total"], total_max)
    if lower:
        st.markdown(
            f'<div class="adventure-card" style="text-align:center;">'
            f'<div style="font-weight:700;">Your whole piece</div>{_stars_html(_stars_for(overall), "2.2rem")}'
            f'<div style="font-weight:700;">{_level_label(overall)}</div></div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(5)
        for col, cat in zip(cols, cats):
            r = _ratio(res["scores"][cat], max_map[cat])
            with col:
                st.markdown(
                    f'<div class="adventure-card" style="text-align:center;padding:0.8rem 0.5rem;">'
                    f'<div style="font-size:1.5rem;">{CATEGORY_ICONS[cat]}</div>'
                    f'<div style="font-weight:700;font-size:0.85rem;">{CATEGORY_LABELS[cat]}</div>'
                    f'{_stars_html(_stars_for(r), "1.2rem")}'
                    f'<div style="font-size:0.8rem;font-weight:700;">{_level_label(r)}</div></div>',
                    unsafe_allow_html=True,
                )
    else:
        rows = [("Your whole piece", "⭐", overall, "#6b63d9")] + [
            (CATEGORY_LABELS[c], CATEGORY_ICONS[c], _ratio(res["scores"][c], max_map[c]), CATEGORY_COLORS[c])
            for c in cats
        ]
        for label, icon, r, color in rows:
            a, b, c = st.columns([2.3, 4.5, 2])
            a.markdown(f"**{icon} {label}**")
            b.markdown(_bar_html(r, color), unsafe_allow_html=True)
            c.markdown(f"**{_level_label(r)}**")

    with st.expander("🔎 Notes on each skill & Stage 6 stretch checklist"):
        comments = res.get("comments", {})
        for cat in cats:
            st.markdown(f"**{CATEGORY_ICONS[cat]} {CATEGORY_LABELS[cat]} ({cat}):** {comments.get(cat, '')}")
        audit = res.get("audit", {})
        if audit:
            st.markdown("#### Stage 6 Stretch Checklist")
            status_icon = {"met": "✅", "partial": "🟡", "not met": "⬜", "na": "➖"}
            for cat, codes in STAGE6_CODES.items():
                lines = []
                for code, meta in codes.items():
                    st_val = str(audit.get(code, "na")).lower()
                    lines.append(f"{status_icon.get(st_val, '➖')} `{code}` {meta['text']}")
                st.markdown(f"**{CATEGORY_LABELS[cat]}**")
                st.markdown("<br>".join(lines), unsafe_allow_html=True)


def render_score_reveal(res, rubric_key):
    """The marks, tucked away at the very bottom until the child chooses to look."""
    max_map = RUBRICS[rubric_key]["max"]
    cats = ("Wc", "Wv", "Wg", "Ws", "Ww")
    st.markdown("---")
    with st.expander("🔓 Show my score"):
        st.caption("This is a snapshot of this one piece. Every piece you write helps you grow.")
        band = str(res.get("band", "")).upper()
        st.markdown(
            f"""
            <div class="adventure-card" style="text-align:center;background:linear-gradient(135deg,#FFFDF7,#FFF3D6);">
                <div style="font-size:1.1rem;font-weight:700;color:#B25200;">YOUR SCORE</div>
                <div style="font-size:3rem;font-weight:700;color:#FF6F00;font-family:'Fredoka',sans-serif;">
                    {res['total']} / {sum(max_map[c] for c in cats)}
                </div>
                <div>Band: <b>{band}</b> &nbsp;•&nbsp; Words: <b>{res['word_count']}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if res.get("cap_note"):
            st.warning(res["cap_note"])
        cols = st.columns(5)
        for col, cat in zip(cols, cats):
            with col:
                st.markdown(
                    f"""
                    <div class="adventure-card" style="text-align:center;padding:0.8rem 0.5rem;">
                        <div style="font-size:1.5rem;">{CATEGORY_ICONS[cat]}</div>
                        <div style="font-weight:700;font-size:0.85rem;">{CATEGORY_LABELS[cat]}</div>
                        <div style="font-size:1.45rem;font-weight:700;color:{CATEGORY_COLORS[cat]};">{res['scores'][cat]}/{max_map[cat]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ------------------------------------------------------------------
# Inky Mascot Helper
# ------------------------------------------------------------------
def render_inky_bubble(message, mood="🦉"):
    st.markdown(
        f"""
        <div class="adventure-card" style="display:flex;align-items:center;gap:0.9rem;background:#FFFDF7;">
            <div style="font-size:2.4rem;line-height:1;">{mood}</div>
            <div>
                <div style="font-weight:700;color:#FF6F00;font-size:0.9rem;">Inky the Owl says:</div>
                <div style="font-size:1.02rem;">{message}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_rule_carousel(subgenre: str, age_band: str):
    """Click-through carousel showing genre rules and framework tips without hover popovers."""
    cards = get_carousel_cards(subgenre, age_band)
    if not cards:
        return

    safe_key = re.sub(r"[^a-zA-Z0-9_]", "_", f"{subgenre}_{age_band}")
    idx_key = f"rule_idx_{safe_key}"
    if idx_key not in st.session_state:
        st.session_state[idx_key] = 0

    total = len(cards)
    idx = st.session_state[idx_key] % total
    title, tip = cards[idx]

    st.markdown("#### 🧭 Genre Rulebook")
    st.markdown(
        f"""
        <div class="rule-carousel-card">
            <div class="rule-carousel-kicker">{title} &nbsp;•&nbsp; {idx + 1}/{total}</div>
            <div class="rule-carousel-body">{tip}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_prev, c_mid, c_next = st.columns([1, 1.4, 1])
    with c_prev:
        if st.button("◀ Prev", key=f"prev_{safe_key}", use_container_width=True):
            st.session_state[idx_key] = (idx - 1) % total
            st.rerun()
    with c_mid:
        st.markdown(
            f"<div style='text-align:center;font-weight:700;font-size:0.85rem;padding-top:0.45rem;color:#B25200;'>Card {idx + 1} of {total}</div>",
            unsafe_allow_html=True,
        )
    with c_next:
        if st.button("Next ▶", key=f"next_{safe_key}", use_container_width=True):
            st.session_state[idx_key] = (idx + 1) % total
            st.rerun()


# ------------------------------------------------------------------
# Lesson sections: Language Arts and Grammar & Punctuation
# The lessons live in language_lessons.py and grammar_lessons.py (same folder as this file).
# Both sections share one screen design, which lives in lesson_hub.py.
# ------------------------------------------------------------------
from lesson_hub import render_hub
from question_bank import bank_questions, bank_record
from vocabulary_vault import render_vocabulary_vault, render_guide_extras, render_arena_suggestions
try:
    from language_lessons import LEVELS as LANGUAGE_LEVELS
except Exception as _la_exc:  # keep the rest of the app working if the file is missing
    LANGUAGE_LEVELS = None
    print(f"[inky] language lessons could not be loaded: {_la_exc}")

try:
    from grammar_lessons import LEVELS as GRAMMAR_LEVELS
except Exception as _gr_exc:
    GRAMMAR_LEVELS = None
    print(f"[inky] grammar lessons could not be loaded: {_gr_exc}")

def render_language_arts():
    render_hub({
        "prefix": "la",
        "levels": LANGUAGE_LEVELS,
        "done_key": "language_done",
        "section": "Language Arts",
        "badge": ("🎭 Language Legend", 5),
        "award_xp": award_xp,
        "log": safe_log_activity,
        "stage": lambda: st.session_state.get("age_band", ""),
        "question_source": bank_questions,
        "record_answers": bank_record,
        "missing": "The language lessons file is missing. Put language_lessons.py in the same folder as app.py, then restart the app.",
    })

def vault_ai_quiz(focus, n, previous_words):
    """Used by the Vocabulary Vault's AI quiz."""
    data = call_json(
        quiz_prompt(st.session_state["age_band"], focus, n=n, previous_words=previous_words),
        "quiz",
        temperature=0.75,
    )
    return data.get("questions", [])
def render_grammar():
    render_hub({
        "prefix": "gr",
        "levels": GRAMMAR_LEVELS,
        "done_key": "grammar_lessons_done",
        "section": "Grammar & Punctuation",
        "badge": ("✏️ Grammar Guardian", 8),
        "award_xp": award_xp,
        "log": safe_log_activity,
        "stage": lambda: st.session_state.get("age_band", ""),
        "question_source": bank_questions,
        "record_answers": bank_record,
        "back_label": "📚 Back to topic",
        "missing": "The grammar lessons file is missing. Put grammar_lessons.py in the same folder as app.py, then restart the app.",
    })

# ------------------------------------------------------------------
# App Init & Sidebar
# ------------------------------------------------------------------
init_state()
# XP lives in the student's account. Load it once per sign-in so it never restarts at zero.
if st.session_state.get("xp_synced_for") != profile["student_id"]:
    st.session_state["xp"] = int(profile.get("xp_points") or 0)
    st.session_state["xp_synced_for"] = profile["student_id"]
with st.sidebar:
    st.markdown(f"**Student:** {profile['display_name']}")
    if st.button("Sign Out", use_container_width=True):
        end_session()
        sign_out_student()
        st.rerun()

    st.divider()

    # --- Your existing sidebar code continues below (keep the same indentation) ---
    st.markdown("## 🦉 Writer Profile")
    student_name = st.text_input(
        "Your Name",
        value=st.session_state["student_name"],
        placeholder="e.g., Maya or Leo",
    )
    if student_name != st.session_state["student_name"]:
        st.session_state["student_name"] = student_name

    age_band = st.selectbox(
        "Your School Stage",
        AGE_BANDS,
        index=AGE_BANDS.index(st.session_state["age_band"]),
    )
    st.session_state["age_band"] = age_band

    xp_panel = st.empty()  # filled in at the very end of the page, so it always shows the latest XP

    st.markdown("---")
    drop_invalid_choice("nav_choice", NAV_OPTIONS)
    nav = st.radio("Choose Your Adventure", NAV_OPTIONS, key="nav_choice")

st.markdown(universe_css_for(nav), unsafe_allow_html=True)

# ------------------------------------------------------------------
# Hero Header
# ------------------------------------------------------------------
st.markdown(
    """
    <div class="hero-banner">
        <div style="font-size:3rem;">🦉</div>
        <div>
            <h1>The Writing Adventure</h1>
            <p>Build bold stories, sharpen facts, and earn stars with Inky your writing coach!</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==================================================================
# VIEW 1: THE WRITING DOJO (Step-by-step guided builder)
# ==================================================================
if nav == NAV_HOME:
    render_home(
        profile,
        {
            "age_band": age_band,
            "xp": st.session_state.get("xp", 0),
            "level_info": level_info,
            "accent": accent_for,
            "dashboard": get_student_dashboard_data,
        },
    )

elif nav == "🥋 The Writing Dojo":
    render_inky_bubble(
        "Pick a style, brainstorm a topic, and build your piece one step at a time. "
        "When you're happy, send the whole piece straight to the Marking Arena!"
    )

    col_g1, col_g2, col_g3 = st.columns([1.2, 1.5, 1.3])
    with col_g1:
        drop_invalid_choice("dojo_genre", ["Fiction", "Non-Fiction"])
        genre = st.radio("1. Writing World", ["Fiction", "Non-Fiction"], horizontal=True, key="dojo_genre")
    with col_g2:
        if genre == "Non-Fiction":
            drop_invalid_choice("dojo_nf_cat", list(NON_FICTION_SUBGENRES.keys()))
            nf_category = st.selectbox("2. Text Category", list(NON_FICTION_SUBGENRES.keys()), key="dojo_nf_cat")
            nf_key = "dojo_nf_type_" + re.sub(r"[^a-zA-Z0-9]", "_", nf_category)
            drop_invalid_choice(nf_key, NON_FICTION_SUBGENRES[nf_category])
            subgenre = st.selectbox("3. Text Type", NON_FICTION_SUBGENRES[nf_category], key=nf_key)
            if subgenre == "Biography/Autobiography":
                drop_invalid_choice("dojo_bio", ["Autobiography", "Biography"])
                bio_choice = st.radio("Focus", ["Autobiography", "Biography"], horizontal=True, key="dojo_bio")
                subgenre = bio_choice
            elif subgenre == "Persuasive Writing":
                drop_invalid_choice("dojo_layout", PERSUASIVE_LAYOUTS)
                layout_choice = st.selectbox("Persuasive Format", PERSUASIVE_LAYOUTS, key="dojo_layout")
                subgenre = f"Persuasive Writing::{layout_choice}"
        else:
            drop_invalid_choice("dojo_fic_cat", list(FICTION_STYLES.keys()))
            fic_category = st.selectbox("2. Story Category", list(FICTION_STYLES.keys()), key="dojo_fic_cat")
            fic_key = "dojo_fic_type_" + re.sub(r"[^a-zA-Z0-9]", "_", fic_category)
            drop_invalid_choice(fic_key, FICTION_STYLES[fic_category])
            subgenre = st.selectbox("3. Story Style / Skill", FICTION_STYLES[fic_category], key=fic_key)

    clean_subgenre = subgenre.replace("::", " — ")
    icon = SUBGENRE_ICONS.get(subgenre.split("::")[0], "✨")
    with col_g3:
        st.markdown(
            f'<div class="adventure-card" style="text-align:center;">'
            f'<div style="font-size:2rem;">{icon}</div>'
            f'<b>{clean_subgenre}</b><br><span style="font-size:0.85rem;">{age_band}</span></div>',
            unsafe_allow_html=True,
        )

    blocks = get_blocks(subgenre)
    state_prefix = re.sub(r"[^a-zA-Z0-9_]", "_", f"{genre}_{subgenre}")

    # 1. Whole-piece Prompt Generator (at the top before sections)
    st.markdown("### 💡 Writing Prompt")
    topic_col, btn_col = st.columns([2.2, 1])
    with topic_col:
        user_topic = st.text_input(
            "Optional topic idea (or leave blank for a surprise!)",
            placeholder="e.g., school library upgrade, local park clean-up, lost treasure...",
            key=f"topic_{state_prefix}",
        )
    with btn_col:
        st.markdown("<div style='height:1.75rem;'></div>", unsafe_allow_html=True)
        gen_prompt_btn = st.button("✨ Generate Writing Prompt", type="primary", use_container_width=True)

    whole_prompt_key = f"whole_prompt_{state_prefix}"
    if gen_prompt_btn:
        with st.spinner("Inky is crafting your writing prompt..."):
            try:
                idea = call_json(
                    whole_prompt_idea_prompt(genre, subgenre, age_band, user_topic),
                    "whole_prompt",
                    temperature=0.8,
                )
                st.session_state[whole_prompt_key] = idea
                award_xp(5)
            except Exception as exc:
                st.error(friendly_error(exc))

    current_idea = st.session_state.get(whole_prompt_key)
    if current_idea:
        title = current_idea.get("topic", user_topic.strip() or f"My {clean_subgenre}")
        writing_prompt_text = current_idea.get("writing_prompt", "")
        st.markdown(
            f"""
            <div class="adventure-card" style="background:#FFFDF7;">
                <div class="step-pill">Topic: {title}</div>
                <div style="font-size:1.05rem;font-weight:700;margin-top:0.25rem;">📝 {writing_prompt_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        title = user_topic.strip() or f"My {clean_subgenre}"
        writing_prompt_text = f"Write a {clean_subgenre.lower()} about {title}."

    # Group single-line / title blocks into the following content block so token effort stays focused
    grouped_steps = []
    idx = 0
    while idx < len(blocks):
        b_name = blocks[idx]
        if b_name in SINGLE_LINE_BLOCKS and idx + 1 < len(blocks):
            next_b = blocks[idx + 1]
            short_first = b_name.split(":", 1)[-1].strip()
            short_second = next_b.split(":", 1)[-1].strip()
            grouped_steps.append({
                "label": f"{short_first} & {short_second}",
                "blocks": [b_name, next_b],
                "merged": True,
            })
            idx += 2
        else:
            grouped_steps.append({
                "label": b_name,
                "blocks": [b_name],
                "merged": False,
            })
            idx += 1

    # Main 2-column layout: Left = Guided Writing Steps, Right = Genre Rulebook Carousel
    main_left, main_right = st.columns([2.25, 1.05], gap="large")

    with main_right:
        render_rule_carousel(subgenre, age_band)

    with main_left:
        st.markdown("### 🧱 Build Your Piece Step by Step")
        draft_parts = []
        for i, step in enumerate(grouped_steps):
            step_label = step["label"]
            target_blocks = step["blocks"]
            is_merged = step["merged"]
            step_slug = re.sub(r"[^a-zA-Z0-9_]", "_", f"{state_prefix}_step_{i}")
            guide_key = f"guide_{step_slug}"
            text_key = f"draft_{step_slug}"
            fb_key = f"fb_{step_slug}"

            blueprint_explanation, builtin_wagoll = get_step_blueprint_and_wagoll(
                subgenre, step_label, age_band
            )

            with st.container():
                st.markdown(f'<div class="step-pill">Part {i + 1} • {step_label}</div>', unsafe_allow_html=True)

                # 1. Built-in concise Blueprint Schema explanation + leading question (0 AI tokens)
                st.markdown(f"🧭 **Blueprint:** {blueprint_explanation}")

                # 2. Built-in WAGOLL example matched to grade level (0 AI tokens)
                st.markdown(
                    f'<div class="wagoll-box"><b>🌟 Example WAGOLL ({age_band.split("(")[0].strip()}):</b><br>{builtin_wagoll}</div>',
                    unsafe_allow_html=True,
                )

                # 3. Extra Help button -> AI-generated vocabulary & key phrases + save to Word Bank
                if st.button(f"✨ Extra Help: Vocabulary & Key Phrases", key=f"btn_guide_{step_slug}"):
                    with st.spinner(f"Finding {age_band} vocabulary & key phrases for {step_label}..."):
                        try:
                            guide_data = call_json(
                                block_extra_help_prompt(
                                    age_band,
                                    genre,
                                    subgenre,
                                    title,
                                    writing_prompt_text,
                                    target_blocks,
                                    step_label,
                                ),
                                "block_guide",
                                temperature=0.65,
                            )
                            st.session_state[guide_key] = guide_data
                            award_xp(5)
                        except Exception as exc:
                            st.error(friendly_error(exc))

                guide = st.session_state.get(guide_key)
                if guide:
                    render_guide_extras(guide, clean_subgenre, title, step_slug, award_xp)

                spoken = dictation_button(step_slug, show_hint=(i == 0))
                if spoken:
                    st.session_state[text_key] = join_text(st.session_state.get(text_key, ""), spoken)
                part_text = st.text_area(
                    f"Write your {step_label}:",
                    key=text_key,
                    height=135 if is_merged else 120,
                    placeholder=(
                        f"Include your opening/title and {step_label.lower()} here..."
                        if is_merged
                        else f"Write your {step_label.lower()} here..."
                    ),
                )
                draft_parts.append((step_label, part_text))

                # 4. Block-by-block feedback (screened for safety first)
                dojo_key = f"dojo_{step_slug}"
                force_check = take_force(dojo_key)
                if st.button(f"🦉 Check {step_label}", key=f"btn_fb_{step_slug}") or force_check:
                    if word_count(part_text) < 4:
                        st.warning("Write at least one sentence first so Inky can help!")
                    else:
                        blocked = blocked_for(dojo_key, part_text)
                        if blocked:
                            st.session_state.pop(fb_key, None)
                            _log_care(blocked, "Writing Dojo")
                        else:
                            with st.spinner("Inky is reading your section..."):
                                try:
                                    fb = call_openrouter(
                                        [{"role": "user", "content": block_feedback_prompt(
                                            age_band, subgenre, step_label, part_text, personal_instruction()
                                        )}],
                                        max_tokens=MAX_TOKENS["feedback"],
                                        temperature=0.6,
                                    )
                                    st.session_state[fb_key] = fb
                                    award_xp(10, "🧱 Block Builder")
                                except Exception as exc:
                                    print(f"[inky] block feedback failed: {exc}")
                                    st.error("Inky couldn't read that just now. Please try again in a moment.")

                render_block(dojo_key)
                if st.session_state.get(fb_key):
                    st.info(st.session_state[fb_key])

    full_draft = "\n\n".join(txt.strip() for _, txt in draft_parts if txt.strip())
    st.markdown("---")
# ==================================================================
# VIEW 2: MARKING ARENA (Cambridge 25-Mark Rubric + OCR + Stage 6 Audit)
# ==================================================================
elif nav == "🏟️ Marking Arena":
    render_inky_bubble(
        "Type, paste, or snap photos of your handwritten work! I'll tell you what is great, "
        "what to try next, and show you how your writing skills are growing."
    )

    col_m1, col_m2 = st.columns([1.2, 1.8])
    with col_m1:
        drop_invalid_choice("arena_genre", ["Fiction", "Non-Fiction"])
        arena_genre = st.radio("Rubric Type", ["Fiction", "Non-Fiction"], horizontal=True, key="arena_genre")
    with col_m2:
        arena_subgenre = st.text_input(
            "Text Type / Topic (optional)",
            key="arena_subgenre",
            placeholder="e.g., Adventure Story, News Report, Persuasive Letter",
        )

    rubric_key = "Fiction (Story)" if arena_genre == "Fiction" else "Non-Fiction"
    with st.expander("📋 View the 25-Mark Rubric"):
        st.text(RUBRICS[rubric_key]["text"])

    with st.expander("📸 Snap & Transcribe Handwritten Work (Optional)"):
        st.caption("Upload clear photos of handwritten pages in order. Handwriting is copied faithfully without auto-correcting spelling.")
        photos = st.file_uploader(
            "Choose page photo(s)",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
        )
        if photos and st.button("🔍 Transcribe My Handwriting"):
            with st.spinner("Reading your handwriting carefully..."):
                try:
                    transcript = transcribe_handwriting(photos)
                    st.session_state["arena_text"] = transcript
                    award_xp(10)
                    st.success("Handwriting transcribed below! Check it and click Mark My Writing.")
                except Exception as exc:
                    print(f"[inky] transcription failed: {exc}")
                    st.error("Inky couldn't read those photos. Try a clearer, well-lit photo.")

    spoken = dictation_button("arena")
    if spoken:
        st.session_state["arena_text"] = join_text(st.session_state.get("arena_text", ""), spoken)
    writing_text = st.text_area(
        "Your Writing",
        value=st.session_state.get("arena_text", ""),
        height=240,
        placeholder="Paste or type your story, report, letter, or essay here (aim for 61+ words so Inky can see all your skills)...",
    )
    st.session_state["arena_text"] = writing_text

    wc = word_count(writing_text)
    if wc <= 60:
        wc_hint = "✍️ Keep going! Pieces with 61 or more words let Inky see all of your skills."
    else:
        wc_hint = "✅ Lovely length. Inky can see lots of your skills!"
    st.caption(f"Word count: **{wc} words**  •  {wc_hint}")

    force_mark = take_force("arena")
    if st.button("🏅 Mark My Writing!", type="primary", use_container_width=True) or force_mark:
        if wc == 0:
            st.warning("Please enter or transcribe some writing first.")
        else:
            blocked = blocked_for("arena", writing_text)
            if blocked:
                st.session_state.pop("last_marking", None)
                _log_care(blocked, "Marking Arena")
            else:
                with st.spinner("Inky is reading your work carefully..."):
                    try:
                        lesson_cat_text, lesson_cat_index = catalog_for(age_band, get_db())
                        result = call_json(
                            piece_marking_prompt(
                                age_band,
                                f"{arena_genre} ({arena_subgenre or rubric_key})",
                                rubric_key,
                                writing_text,
                                wc=wc,
                                personal_instruction=personal_instruction(),
                                lesson_catalog=lesson_cat_text,
                            ),
                            "mark",
                            temperature=0.3,
                        )
                        if not isinstance(result, dict):
                            raise ValueError("The marker did not return a usable answer.")
                        flag = check_model_flags(result)
                        if flag and not (flag.status == "care" and is_overridden("arena", writing_text)):
                            set_block("arena", flag, writing_text)
                            st.session_state.pop("last_marking", None)
                            _log_care(flag, "Marking Arena")
                        else:
                            clear_block("arena")
                            max_map = RUBRICS[rubric_key]["max"]
                            raw_scores = result.get("scores") if isinstance(result.get("scores"), dict) else {}
                            clamped = {
                                k: max(0, min(max_map[k], _score_int(raw_scores.get(k, 0))))
                                for k in ("Wc", "Wv", "Wg", "Ws", "Ww")
                            }
                            final_scores, cap_note = apply_word_count_rules(clamped, wc)
                            total_score = sum(final_scores.values())
                            band_val = str(result.get("band", "")).strip().lower()
                            if band_val not in ("top", "middle", "bottom", "below"):
                                r = total_score / max(1, sum(max_map.values()))
                                band_val = "top" if r >= 0.7 else "middle" if r >= 0.4 else "bottom" if r >= 0.2 else "below"
                            result["band"] = band_val
                            result["scores"] = final_scores
                            result["total"] = total_score
                            result["word_count"] = wc
                            result["cap_note"] = cap_note
                            result["genre"] = arena_genre
                            result["subgenre"] = arena_subgenre or rubric_key
                            result["next_steps"], result["fixes"] = build_next_steps(result, lesson_cat_index, writing_text)
                            result.pop("next_lessons", None)
                            st.session_state["last_marking"] = result

                            summary_fb = (
                                f"Strengths: {result.get('strengths', '')} | "
                                f"Improvements: {result.get('improvements', '')} | "
                                f"Wish: {result.get('wish', '')}"
                            )
                            entry = {
                                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "genre": arena_genre,
                                "subgenre": arena_subgenre or rubric_key,
                                "score": total_score,
                                "wc_score": final_scores["Wc"],
                                "wv_score": final_scores["Wv"],
                                "wg_score": final_scores["Wg"],
                                "ws_score": final_scores["Ws"],
                                "ww_score": final_scores["Ww"],
                                "word_count": wc,
                                "band": result.get("band", ""),
                                "feedback": summary_fb,
                            }
                            st.session_state["local_history"].insert(0, entry)
                            badge = "🏅 First Arena Score"
                            if total_score >= 20:
                                badge = "🌟 High Flyer (20+/25)"
                            award_xp(15 + total_score, badge)
                            safe_log_activity(
                                "marked_item", "Marking Arena", str(arena_subgenre or rubric_key),
                                score_or_grade=f"{total_score}/25", genre_or_skill=str(arena_genre),
                                xp_earned=15 + total_score,
                                details={
                                    "age_band": age_band,
                                    "subgenre": str(arena_subgenre or rubric_key),
                                    "score": int(total_score),
                                    "wc_score": final_scores["Wc"],
                                    "wv_score": final_scores["Wv"],
                                    "wg_score": final_scores["Wg"],
                                    "ws_score": final_scores["Ws"],
                                    "ww_score": final_scores["Ww"],
                                    "word_count": int(wc),
                                    "band": str(result.get("band", "") or ""),
                                    "feedback": summary_fb[:4000],
                                },
                            )
                    except Exception as exc:
                        print(f"[inky] marking failed: {exc}")
                        st.error("Inky had trouble marking this one. Please try again in a moment.")

    render_block("arena")

    res = st.session_state.get("last_marking")
    if res:
        render_marking_feedback(res, rubric_key, age_band)
        render_next_steps(res, profile["student_id"], get_db())
        render_arena_suggestions(
            genre=str(res.get("subgenre") or "").split("::")[0],
            age_band=age_band,
            key_prefix="arena",
            award_xp=award_xp,
        )
        render_score_reveal(res, rubric_key)
# ==================================================================
# VIEW: READING
# ==================================================================
elif nav == "📖 Reading":
    render_reading_section(bubble=render_inky_bubble)

# ==================================================================
# VIEW 3: VOCABULARY & LANGUAGE
# ==================================================================
elif nav == "📚 Vocabulary Vault":
    render_inky_bubble(
        "Welcome to the Vault! Browse word and phrase lists by genre, build your own lists, then test yourself."
    )
    render_vocabulary_vault({
        "award_xp": award_xp,
        "log": safe_log_activity,
        "ai_quiz": vault_ai_quiz,
        "age_band": lambda: st.session_state.get("age_band", ""),
    })
# ==================================================================
# VIEW 4: GRAMMAR & PUNCTUATION
# ==================================================================
elif nav == "✏️ Grammar & Punctuation":
    render_inky_bubble(
        "Pick your level, choose a topic, then learn the rules and practise to earn XP!"
    )
    render_grammar()
# ==================================================================
# VIEW: LANGUAGE ARTS
# ==================================================================
elif nav == "🎭 Language Arts":
    render_inky_bubble(
        "Build your word power! Read a short lesson, then practise with quick questions to earn XP."
    )
    render_language_arts()

# ==================================================================
# VIEW 5: PROGRESS & BADGES
# ==================================================================
elif nav == NAV_GAMES:
    render_games_arena(
        get_db(), profile["student_id"], age_band,
        bubble=render_inky_bubble, award_xp=award_xp, log_activity=safe_log_activity,
    )

elif nav == NAV_SPELLING:
    try:
        from auth_progress import get_supabase_client as _spelling_db
        spelling_db = _spelling_db()
    except Exception as exc:
        print(f"[inky] spelling: no database connection: {exc}")
        spelling_db = None
    render_spelling_arena(
        spelling_db,
        user_id=profile["student_id"],
        bubble=render_inky_bubble,
        award_xp=award_xp,
        log_activity=safe_log_activity,
    )

elif nav == "🏆 Progress & Badges":
    from auth_progress import get_student_dashboard_data, compute_title, _parse_badges, refresh_student_profile

    try:
        profile = refresh_student_profile() or profile
        data = get_student_dashboard_data(profile["student_id"])
    except Exception:
        st.warning("Saved progress could not be loaded right now (no database connection).")
        data = {"activities": [], "marked_history": [], "quizzes": [], "lessons": [], "vocabulary": []}
    xp = int(profile.get("xp_points") or 0)
    title = profile.get("current_title") or compute_title(xp)
    badges = _parse_badges(profile.get("badges"))

    render_inky_bubble(
        f"Look how far you've come, {profile['display_name']}! Your current rank is **{title}**, and every story, block check, lesson, and quiz adds XP."
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Writer Rank", title)
    m2.metric("Total XP", xp)
    m3.metric("Pieces Marked", len(data["marked_history"]))
    m4.metric("Words Collected", len(data["vocabulary"]))

    st.markdown("### 🏅 Your Earned Badges")
    if not badges:
        st.info("No badges earned yet! Complete writing marks, vocabulary practice, or quizzes to unlock your first badge.")
    else:
        st.markdown(
            "".join(
                f'<span class="badge-chip" style="font-size:1rem;" title="{b.get("description", "")}">{b.get("name", b)}</span>'
                for b in badges
            ),
            unsafe_allow_html=True,
        )

    st.markdown("### 📜 Recent Marking History & Grades")
    if not data["marked_history"]:
        st.info("No marked pieces yet! Head over to the Marking Arena to earn your first score.")
    else:
        for h in data["marked_history"]:
            details = h.get("details") or {}
            feedback = details.get("feedback", "")
            word_count = details.get("word_count", "")
            wc_text = f"&nbsp;|&nbsp; {word_count} words" if word_count else ""
            st.markdown(
                f"""
                <div class="adventure-card">
                    <b>{h.get('genre_or_skill') or h.get('section_name')} — {h.get('item_title','')}</b>
                    &nbsp;|&nbsp; <span style="color:#FF6F00;font-weight:700;">{h.get('score_or_grade','Recorded')}</span>
                    {wc_text}
                    &nbsp;|&nbsp; <span style="font-size:0.85rem;">{str(h.get('created_at',''))[:16]}</span>
                    <div style="font-size:0.9rem;margin-top:0.3rem;">{feedback}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### 📚 Completed Lessons & Reading Practice")
    if not data["lessons"]:
        st.caption("No lessons or reading practice logged yet.")
    else:
        for item in data["lessons"]:
            st.markdown(
                f"""
                <div class="adventure-card">
                    <b>{item.get('section_name','')} — {item.get('item_title','')}</b>
                    &nbsp;|&nbsp; <span style="color:#2E7D32;font-weight:700;">{item.get('score_or_grade','Completed')}</span>
                    &nbsp;|&nbsp; <span style="font-size:0.85rem;">{str(item.get('created_at',''))[:16]}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### 🧠 Quizzes & Drills")
    if not data["quizzes"]:
        st.caption("No quizzes or drills completed yet.")
    else:
        for q in data["quizzes"]:
            st.markdown(
                f"""
                <div class="adventure-card">
                    <b>{q.get('section_name','')} — {q.get('item_title','')}</b>
                    &nbsp;|&nbsp; <span style="color:#1565C0;font-weight:700;">{q.get('score_or_grade','Completed')}</span>
                    &nbsp;|&nbsp; <span style="font-size:0.85rem;">{str(q.get('created_at',''))[:16]}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### 📖 Saved & Practiced Vocabulary")
    if not data["vocabulary"]:
        st.caption("No vocabulary saved yet. Practice words in Vocabulary & Language to add them here!")
    else:
        for v in data["vocabulary"]:
            st.markdown(
                f"""
                <div class="adventure-card">
                    <b>{v.get('word_or_phrase','')}</b> ({v.get('genre_or_category','General')})
                    &nbsp;|&nbsp; <b>{v.get('mastery_status','Reviewed')}</b> (Practiced {v.get('times_practiced', 1)}x)
                    <div style="font-size:0.9rem;margin-top:0.2rem;">{v.get('meaning_or_note','')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")
    render_parent_reports(get_db(), profile)

with xp_panel.container():
    live_xp = int(st.session_state["xp"])
    lvl_name, pct, next_xp = level_info(live_xp)
    st.markdown("---")
    st.markdown(f"**Title:** {(st.session_state.get('student_profile') or profile).get('current_title', 'Novice Scribbler')}")
    st.markdown(f"### ✨ {lvl_name}")
    st.markdown(
        f'<div class="xp-bar-wrap"><div class="xp-bar-fill" style="width:{pct}%;"></div></div>',
        unsafe_allow_html=True,
    )
    st.caption(f"{live_xp} XP  •  Next rank at {next_xp} XP")
    st.markdown("### 🏅 Badges")
    st.markdown(
        "".join(f'<span class="badge-chip">{b}</span>' for b in st.session_state["badges"]),
        unsafe_allow_html=True,
    )

with st.sidebar:
    saved_note()

# Save work in progress last, so it always reflects this run.
autosave_state(profile["student_id"])
