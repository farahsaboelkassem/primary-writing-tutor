import json
import re
from datetime import datetime, timezone
import streamlit as st
from supabase import create_client, Client

def _get_secret_value(*names: str) -> str:
    """Find a secret by any of the given names, at the top level or inside a [supabase] section."""
    try:
        secrets = st.secrets
        for name in names:
            if name in secrets:
                return str(secrets[name]).strip()
        for section in ("supabase", "SUPABASE", "connections"):
            if section in secrets:
                sub = secrets[section]
                for name in names:
                    try:
                        if name in sub:
                            return str(sub[name]).strip()
                    except TypeError:
                        break
    except Exception:
        pass
    raise KeyError(
        f"Missing secret. Expected one of: {', '.join(names)}. "
        "Locally, put them in .streamlit/secrets.toml inside the folder you run 'streamlit run' from."
    )


TITLE_TIERS = [
    (0, "Novice Scribbler"),
    (100, "Word Explorer"),
    (250, "Paragraph Builder"),
    (450, "Story & Fact Crafter"),
    (700, "Master Pen-Wielder"),
]

BADGE_RULES = [
    ("first_step", "First Ink Drop", "Completed your first logged activity"),
    ("marker_pro", "Arena Contender", "Had at least 3 pieces of writing marked"),
    ("vocab_collector", "Vault Keeper", "Saved or practiced at least 10 vocabulary words/phrases"),
    ("quiz_ace", "Quiz Challenger", "Completed at least 3 quizzes or grammar/language drills"),
    ("rising_star", "Rising Quill", "Reached 250+ XP points"),
]


@st.cache_resource
def get_supabase_client() -> Client:
    url = _get_secret_value("SUPABASE_URL", "supabase_url", "url")
    key = _get_secret_value("SUPABASE_KEY", "supabase_key", "SUPABASE_ANON_KEY", "key")
    return create_client(url, key)


def normalize_student_id(raw_name: str) -> str:
    cleaned = re.sub(r"[^a-z0-9_]", "_", raw_name.strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned


def compute_title(xp_points: int) -> str:
    current = TITLE_TIERS[0][1]
    for threshold, title in TITLE_TIERS:
        if xp_points >= threshold:
            current = title
    return current


def _parse_badges(raw_badges) -> list[dict]:
    if isinstance(raw_badges, list):
        return raw_badges
    if isinstance(raw_badges, str) and raw_badges.strip():
        try:
            parsed = json.loads(raw_badges)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
    return []


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(raw_email: str) -> str:
    return (raw_email or "").strip().lower()


def sign_up_student(display_name: str, email: str, pin_code: str) -> tuple[bool, str]:
    clean_name = (display_name or "").strip()
    clean_email = normalize_email(email)
    clean_pin = (pin_code or "").strip()

    if len(clean_name) < 2:
        return False, "Please enter your name (at least 2 letters)."
    if len(clean_email) > 254 or not EMAIL_PATTERN.match(clean_email):
        return False, "Please enter a real email address, like name@example.com."
    if not clean_pin.isdigit() or not (4 <= len(clean_pin) <= 8):
        return False, "Please choose a PIN with 4 to 8 numbers (for example, 1234)."

    supabase = get_supabase_client()
    existing = (
        supabase.table("student_profiles")
        .select("student_id")
        .eq("email", clean_email)
        .execute()
    )
    if existing.data:
        return False, "That email already has an account. Please use Sign in instead."

    payload = {
        # The email is unique, so it doubles as the account ID. Two students with the same name never clash.
        "student_id": clean_email,
        "display_name": clean_name,
        "email": clean_email,
        "pin_code": clean_pin,
        "current_title": "Novice Scribbler",
        "xp_points": 0,
        "badges": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_active": datetime.now(timezone.utc).isoformat(),
    }
    res = supabase.table("student_profiles").insert(payload).execute()
    if res.data:
        st.session_state["student_profile"] = res.data[0]
        return True, f"Welcome, {clean_name}! Your account is ready."
    return False, "Could not create the account. Please check your Supabase connection."


def sign_in_student(email_or_name: str, pin_code: str) -> tuple[bool, str]:
    identifier = (email_or_name or "").strip()
    clean_pin = (pin_code or "").strip()

    if not identifier or not clean_pin:
        return False, "Please enter both your email and your PIN."

    supabase = get_supabase_client()
    table = supabase.table("student_profiles").select("*")
    if "@" in identifier:
        res = table.eq("email", normalize_email(identifier)).execute()
    else:
        # Accounts made before emails were added were found by student name; keep them working.
        res = table.eq("student_id", normalize_student_id(identifier)).execute()
    if not res.data:
        return False, "We could not find that account. Check your email, or create a new account."

    profile = res.data[0]
    if str(profile.get("pin_code", "")) != clean_pin:
        return False, "That PIN is not right. Please try again."

    now = datetime.now(timezone.utc).isoformat()
    supabase.table("student_profiles").update({"last_active": now}).eq("student_id", profile["student_id"]).execute()

    profile["last_active"] = now
    st.session_state["student_profile"] = profile
    return True, f"Welcome back, {profile['display_name']}!"


def sign_out_student() -> None:
    # Clear everything so the next student on this device starts fresh
    # (name, XP, badges, word list and history must never carry over).
    st.session_state.clear()


def refresh_student_profile() -> dict | None:
    profile = st.session_state.get("student_profile")
    if not profile:
        return None
    supabase = get_supabase_client()
    res = (
        supabase.table("student_profiles")
        .select("*")
        .eq("student_id", profile["student_id"])
        .execute()
    )
    if res.data:
        st.session_state["student_profile"] = res.data[0]
        return res.data[0]
    return profile


def _recalculate_title_and_badges(student_id: str) -> None:
    supabase = get_supabase_client()

    prof_res = (
        supabase.table("student_profiles")
        .select("xp_points, badges")
        .eq("student_id", student_id)
        .execute()
    )
    if not prof_res.data:
        return

    xp = int(prof_res.data[0].get("xp_points") or 0)
    existing_badges = _parse_badges(prof_res.data[0].get("badges"))
    earned_ids = {b.get("id") for b in existing_badges if isinstance(b, dict)}

    logs = (
        supabase.table("student_activity_log")
        .select("activity_type")
        .eq("student_id", student_id)
        .execute()
        .data
        or []
    )
    vocab = (
        supabase.table("student_vocabulary")
        .select("id")
        .eq("student_id", student_id)
        .execute()
        .data
        or []
    )

    total_logs = len(logs)
    marked_count = sum(1 for row in logs if row.get("activity_type") == "marked_item")
    quiz_count = sum(1 for row in logs if row.get("activity_type") == "quiz")
    vocab_count = len(vocab)

    conditions = {
        "first_step": total_logs >= 1,
        "marker_pro": marked_count >= 3,
        "vocab_collector": vocab_count >= 10,
        "quiz_ace": quiz_count >= 3,
        "rising_star": xp >= 250,
    }

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for badge_id, badge_name, badge_desc in BADGE_RULES:
        if conditions.get(badge_id) and badge_id not in earned_ids:
            existing_badges.append(
                {
                    "id": badge_id,
                    "name": badge_name,
                    "description": badge_desc,
                    "earned_on": now_str,
                }
            )
            earned_ids.add(badge_id)

    new_title = compute_title(xp)
    supabase.table("student_profiles").update(
        {
            "current_title": new_title,
            "badges": existing_badges,
            "last_active": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("student_id", student_id).execute()

    refresh_student_profile()


def log_student_activity(
    activity_type: str,
    section_name: str,
    item_title: str,
    score_or_grade: str = "",
    genre_or_skill: str = "",
    xp_earned: int = 15,
    details: dict | None = None,
) -> bool:
    """
    Call this whenever a student completes:
    - a marked piece of writing ('marked_item', e.g. score_or_grade='17/20')
    - a quiz or grammar/language drill ('quiz', e.g. score_or_grade='4/5')
    - a guided lesson ('lesson', e.g. score_or_grade='Completed')
    - independent reading practice ('reading_practice', e.g. score_or_grade='Completed')
    """
    profile = st.session_state.get("student_profile")
    if not profile:
        return False

    student_id = profile["student_id"]
    supabase = get_supabase_client()

    log_payload = {
        "student_id": student_id,
        "activity_type": activity_type,
        "section_name": section_name,
        "item_title": item_title,
        "genre_or_skill": genre_or_skill,
        "score_or_grade": score_or_grade,
        "xp_earned": int(xp_earned),
        "details": details or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    res = supabase.table("student_activity_log").insert(log_payload).execute()
    if not res.data:
        return False

    current_xp = int(profile.get("xp_points") or 0)
    supabase.table("student_profiles").update({"xp_points": current_xp + int(xp_earned)}).eq(
        "student_id", student_id
    ).execute()

    _recalculate_title_and_badges(student_id)
    return True


def upsert_student_vocabulary(
    word_or_phrase: str,
    genre_or_category: str = "General",
    meaning_or_note: str = "",
    mastery_status: str = "Reviewed",
    xp_earned: int = 5,
) -> bool:
    profile = st.session_state.get("student_profile")
    if not profile:
        return False

    clean_term = word_or_phrase.strip()
    if not clean_term:
        return False

    student_id = profile["student_id"]
    supabase = get_supabase_client()

    existing = (
        supabase.table("student_vocabulary")
        .select("*")
        .eq("student_id", student_id)
        .eq("word_or_phrase", clean_term)
        .execute()
    )

    now_iso = datetime.now(timezone.utc).isoformat()
    if existing.data:
        row = existing.data[0]
        new_times = int(row.get("times_practiced") or 1) + 1
        supabase.table("student_vocabulary").update(
            {
                "genre_or_category": genre_or_category or row.get("genre_or_category", "General"),
                "meaning_or_note": meaning_or_note or row.get("meaning_or_note", ""),
                "mastery_status": mastery_status,
                "times_practiced": new_times,
                "updated_at": now_iso,
            }
        ).eq("id", row["id"]).execute()
    else:
        supabase.table("student_vocabulary").insert(
            {
                "student_id": student_id,
                "word_or_phrase": clean_term,
                "genre_or_category": genre_or_category,
                "meaning_or_note": meaning_or_note,
                "mastery_status": mastery_status,
                "times_practiced": 1,
                "updated_at": now_iso,
            }
        ).execute()

    current_xp = int(profile.get("xp_points") or 0)
    supabase.table("student_profiles").update({"xp_points": current_xp + int(xp_earned)}).eq(
        "student_id", student_id
    ).execute()

    _recalculate_title_and_badges(student_id)
    return True


def get_student_dashboard_data(student_id: str) -> dict:
    supabase = get_supabase_client()
    activities = (
        supabase.table("student_activity_log")
        .select("*")
        .eq("student_id", student_id)
        .order("created_at", desc=True)
        .limit(100)
        .execute()
        .data
        or []
    )
    vocab = (
        supabase.table("student_vocabulary")
        .select("*")
        .eq("student_id", student_id)
        .order("updated_at", desc=True)
        .limit(200)
        .execute()
        .data
        or []
    )
    return {
        "activities": activities,
        "marked_history": [a for a in activities if a.get("activity_type") == "marked_item"],
        "quizzes": [a for a in activities if a.get("activity_type") == "quiz"],
        "lessons": [a for a in activities if a.get("activity_type") in ("lesson", "reading_practice")],
        "vocabulary": vocab,
    }


AUTH_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800&family=Nunito:wght@400;600;700;800&display=swap');
:root { --ink:#2b2a4a; --muted:#64637f; --line:#e8e4f3; --accent:#6b63d9; --accent-dark:#4a43b0; --accent-soft:#eeecff; }
html, body, .stApp, .stApp p, .stApp label, .stApp input, .stApp button { font-family:'Nunito', system-ui, sans-serif; }
[data-testid="stIconMaterial"], [class*="material-symbols"] { font-family:'Material Symbols Rounded','Material Icons' !important; }
[data-testid="stElementContainer"]:has(style), .element-container:has(style) { display:none !important; }

/* ---------- Night-sky scene ---------- */
.stApp { isolation:isolate; background:linear-gradient(180deg,#1b1750 0%,#3a2f86 42%,#8a5fc7 74%,#f5a9b5 100%) !important; }
.stApp::before, .stApp::after { content:""; position:fixed; left:0; right:0; pointer-events:none; z-index:-1; }
.stApp::before {
  top:0; bottom:0;
  background:
    radial-gradient(circle at 92% 12%, #fff6d4 0 30px, rgba(255,246,212,.28) 31px 56px, rgba(255,246,212,.08) 57px 100px, transparent 101px),
    radial-gradient(1.7px 1.7px at 32px 46px, #fff, transparent) 0 0 / 290px 210px,
    radial-gradient(1.2px 1.2px at 118px 88px, rgba(255,255,255,.9), transparent) 0 0 / 290px 210px,
    radial-gradient(1.5px 1.5px at 214px 24px, #fff, transparent) 0 0 / 290px 210px,
    radial-gradient(1px 1px at 70px 160px, rgba(255,255,255,.85), transparent) 0 0 / 290px 210px;
  -webkit-mask-image:linear-gradient(180deg,#000 0%,#000 62%,transparent 100%);
  mask-image:linear-gradient(180deg,#000 0%,#000 62%,transparent 100%);
}
.stApp::after {
  bottom:0; height:26vh;
  background:
    radial-gradient(60% 75% at 16% 112%, #2a1f6b 0 98%, transparent 100%),
    radial-gradient(70% 85% at 68% 114%, #352a7c 0 98%, transparent 100%),
    radial-gradient(48% 62% at 100% 108%, #231a5c 0 98%, transparent 100%);
}
[data-testid="stHeader"] { background:transparent !important; }
[data-testid="stDecoration"] { display:none !important; }

/* ---------- Welcome card ---------- */
.block-container, [data-testid="stMainBlockContainer"] {
  width:min(520px, calc(100% - 2rem)) !important; max-width:none !important;
  margin:2.2rem auto 2.5rem !important; padding:1.6rem 1.8rem 1.9rem !important;
  background:rgba(255,253,248,.97); border:1px solid rgba(255,255,255,.8); border-radius:28px;
  box-shadow:0 26px 60px rgba(10,8,40,.38);
}
.auth-hero { text-align:center; padding:.2rem 0 1rem; }
.auth-owl {
  width:84px; height:84px; margin:0 auto .7rem; display:grid; place-items:center; font-size:2.8rem;
  background:linear-gradient(135deg,#3d3499,#8a63d8); border:4px solid #fff; border-radius:50%;
  box-shadow:0 10px 24px rgba(61,52,153,.35);
}
.auth-title { font-family:'Baloo 2', cursive; font-weight:800; font-size:clamp(1.7rem,5vw,2.25rem); line-height:1.1; color:var(--ink); }
.auth-sub { color:var(--muted); font-size:1rem; margin-top:.35rem; line-height:1.45; }
.auth-note { color:var(--muted); font-size:.85rem; text-align:center; margin-top:.9rem; line-height:1.4; }

/* ---------- Tabs ---------- */
[data-baseweb="tab-list"] { gap:.35rem; background:var(--accent-soft); padding:.3rem; border-radius:999px; }
button[data-baseweb="tab"] { flex:1; height:2.6rem; border-radius:999px !important; background:transparent; }
button[data-baseweb="tab"] p { font-weight:800 !important; color:var(--accent-dark) !important; }
button[data-baseweb="tab"][aria-selected="true"] { background:#fff !important; box-shadow:0 3px 10px rgba(61,52,153,.18); }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display:none !important; }

/* ---------- Form ---------- */
[data-testid="stForm"] { border:none !important; background:transparent !important; padding:.5rem 0 0 !important; }
.stApp label p { font-weight:800 !important; color:var(--ink) !important; }
[data-baseweb="input"] { background:#fff !important; border:2px solid var(--line) !important; border-radius:14px !important; }
[data-baseweb="base-input"] { background:transparent !important; border-radius:14px !important; }
[data-baseweb="input"]:focus-within { border-color:var(--accent) !important; box-shadow:0 0 0 3px rgba(107,99,217,.18); }
.stApp input { color:var(--ink) !important; font-weight:600; }
[data-testid="stFormSubmitButton"] button {
  height:3rem; border:none !important; border-radius:999px !important; color:#fff !important;
  background:linear-gradient(135deg,#6b63d9,#8a63d8) !important; box-shadow:0 8px 18px rgba(74,67,176,.35);
  transition:transform .15s ease, box-shadow .15s ease;
}
[data-testid="stFormSubmitButton"] button p { color:#fff !important; font-family:'Baloo 2', cursive; font-weight:700; font-size:1.1rem; }
[data-testid="stFormSubmitButton"] button:hover { transform:translateY(-2px); box-shadow:0 12px 22px rgba(74,67,176,.42); }
@media (max-width:520px) { .block-container, [data-testid="stMainBlockContainer"] { padding:1.2rem 1.1rem 1.5rem !important; margin-top:1.2rem !important; } }
</style>
"""

AUTH_HERO_HTML = (
    '<div class="auth-hero">'
    '<div class="auth-owl">🦉</div>'
    '<div class="auth-title">The Writing Adventure</div>'
    '<div class="auth-sub">Inky is ready to help you write. Sign in to keep your stars, titles and stories safe.</div>'
    '</div>'
)

AUTH_NOTE_HTML = (
    '<div class="auth-note">Ask a parent or teacher to help with your email if you are not sure. '
    'It is only used to sign you in.</div>'
)

AUTH_ERROR_TEXT = "Could not reach the sign-in service: {kind}: {detail}"


def _auth_error(exc: Exception) -> str:
    detail = str(exc).strip(chr(39) + chr(34))[:300]
    return AUTH_ERROR_TEXT.format(kind=type(exc).__name__, detail=detail)


def render_auth_page() -> None:
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    st.markdown(AUTH_HERO_HTML, unsafe_allow_html=True)

    tab_signin, tab_signup = st.tabs(["🔑 Sign in", "🌟 Create account"])

    with tab_signin:
        with st.form("signin_form", clear_on_submit=False):
            email_input = st.text_input("Email", placeholder="you@example.com")
            pin_input = st.text_input("Secret PIN", type="password", placeholder="••••")
            submitted = st.form_submit_button("Sign in", use_container_width=True)
            if submitted:
                try:
                    ok, msg = sign_in_student(email_input, pin_input)
                except Exception as exc:
                    ok, msg = False, _auth_error(exc)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with tab_signup:
        with st.form("signup_form", clear_on_submit=False):
            new_name = st.text_input("Your name", placeholder="e.g., Maya")
            new_email = st.text_input("Email", placeholder="you@example.com", key="signup_email")
            new_pin = st.text_input("Create a PIN (4 to 8 numbers)", type="password", placeholder="e.g., 2468")
            confirm_pin = st.text_input("Type your PIN again", type="password", placeholder="Same PIN again")
            created = st.form_submit_button("Create my account", use_container_width=True)
            if created:
                if new_pin != confirm_pin:
                    st.error("The two PINs do not match. Please try again.")
                else:
                    try:
                        ok, msg = sign_up_student(new_name, new_email, new_pin)
                    except Exception as exc:
                        ok, msg = False, _auth_error(exc)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    st.markdown(AUTH_NOTE_HTML, unsafe_allow_html=True)


def render_profile_progress_tab(profile: dict) -> None:
    data = get_student_dashboard_data(profile["student_id"])
    xp = int(profile.get("xp_points") or 0)
    title = profile.get("current_title") or compute_title(xp)
    badges = _parse_badges(profile.get("badges"))

    st.subheader(f"🏅 {profile['display_name']} — {title}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("XP Points", xp)
    c2.metric("Current Title", title)
    c3.metric("Badges Earned", len(badges))
    c4.metric("Marked Items", len(data["marked_history"]))

    st.markdown("### 🎖️ Badges")
    if badges:
        for b in badges:
            st.success(f"**{b.get('name', 'Badge')}** — {b.get('description', '')} *(Earned: {b.get('earned_on', '')})*")
    else:
        st.info("No badges earned yet—complete writing marks, vocabulary practice, or quizzes to unlock badges!")

    st.markdown("### 📝 History of Marked Items & Grades")
    if data["marked_history"]:
        for item in data["marked_history"]:
            st.write(
                f"- **{item.get('item_title')}** ({item.get('genre_or_skill') or item.get('section_name')}) "
                f"— **Grade/Score:** `{item.get('score_or_grade') or 'Recorded'}` "
                f"| +{item.get('xp_earned', 0)} XP"
            )
    else:
        st.caption("No marked writing items recorded yet.")

    st.markdown("### 📚 Lessons & Reading Practice")
    if data["lessons"]:
        for item in data["lessons"]:
            st.write(
                f"- **{item.get('item_title')}** ({item.get('section_name')}) "
                f"— Status/Result: `{item.get('score_or_grade') or 'Completed'}`"
            )
    else:
        st.caption("No lessons or reading practice logged yet.")

    st.markdown("### 🧠 Quizzes & Drills")
    if data["quizzes"]:
        for item in data["quizzes"]:
            st.write(
                f"- **{item.get('item_title')}** ({item.get('section_name')}) "
                f"— Score: `{item.get('score_or_grade') or 'Completed'}`"
            )
    else:
        st.caption("No quizzes logged yet.")

    st.markdown("### 📖 Saved & Practiced Vocabulary")
    if data["vocabulary"]:
        for v in data["vocabulary"]:
            st.write(
                f"- **{v.get('word_or_phrase')}** [{v.get('genre_or_category')}] — "
                f"`{v.get('mastery_status')}` (Practiced {v.get('times_practiced', 1)}x)"
            )
    else:
        st.caption("No vocabulary words saved to this profile yet.")