import json
import re
from datetime import datetime, timezone
import streamlit as st
from supabase import create_client, Client

def _get_secret_value(*names: str) -> str:
    for name in names:
        if name in st.secrets:
            return str(st.secrets[name]).strip()
    if "supabase" in st.secrets and isinstance(st.secrets["supabase"], dict):
        sub = st.secrets["supabase"]
        for name in names:
            if name in sub:
                return str(sub[name]).strip()
    raise KeyError(f"Missing secret key. Expected one of: {', '.join(names)}")

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
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
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


def sign_up_student(display_name: str, pin_code: str, grade_level: str = "Grade 5") -> tuple[bool, str]:
    clean_name = display_name.strip()
    clean_pin = pin_code.strip()
    student_id = normalize_student_id(clean_name)

    if len(clean_name) < 2 or not student_id:
        return False, "Please enter a student name with at least 2 letters or numbers."
    if not clean_pin.isdigit() or not (4 <= len(clean_pin) <= 8):
        return False, "Please choose a PIN with 4 to 8 numbers (for example, 1234)."

    supabase = get_supabase_client()
    existing = (
        supabase.table("student_profiles")
        .select("student_id")
        .eq("student_id", student_id)
        .execute()
    )
    if existing.data:
        return False, f"That student name is already taken as ID '{student_id}'. Try adding a number or pick Sign In."

    payload = {
        "student_id": student_id,
        "display_name": clean_name,
        "pin_code": clean_pin,
        "grade_level": grade_level,
        "current_title": "Novice Scribbler",
        "xp_points": 0,
        "badges": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_active": datetime.now(timezone.utc).isoformat(),
    }
    res = supabase.table("student_profiles").insert(payload).execute()
    if res.data:
        st.session_state["student_profile"] = res.data[0]
        return True, f"Welcome, {clean_name}! Your profile is ready."
    return False, "Could not create profile. Please check your Supabase connection."


def sign_in_student(name_or_id: str, pin_code: str) -> tuple[bool, str]:
    lookup_id = normalize_student_id(name_or_id)
    clean_pin = pin_code.strip()

    if not lookup_id or not clean_pin:
        return False, "Please enter both your student name and PIN."

    supabase = get_supabase_client()
    res = (
        supabase.table("student_profiles")
        .select("*")
        .eq("student_id", lookup_id)
        .execute()
    )
    if not res.data:
        return False, "Student profile not found. Check spelling or create a new profile under Sign Up."

    profile = res.data[0]
    if str(profile.get("pin_code", "")) != clean_pin:
        return False, "Incorrect PIN. Please try again."

    supabase.table("student_profiles").update(
        {"last_active": datetime.now(timezone.utc).isoformat()}
    ).eq("student_id", lookup_id).execute()

    profile["last_active"] = datetime.now(timezone.utc).isoformat()
    st.session_state["student_profile"] = profile
    return True, f"Signed in as {profile['display_name']}!"


def sign_out_student() -> None:
    for key in ["student_profile"]:
        st.session_state.pop(key, None)


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


def render_auth_page() -> None:
    st.title("✍️ Primary Writing Tutor — Student Sign In & Sign Up")
    st.write("Sign in with your student name and PIN to keep your title, badges, grades, vocabulary, quizzes, and lessons saved.")

    tab_signin, tab_signup = st.tabs(["🔑 Sign In", "🌟 Sign Up (New Student)"])

    with tab_signin:
        with st.form("signin_form", clear_on_submit=False):
            name_input = st.text_input("Student Name", placeholder="e.g., Leo")
            pin_input = st.text_input("Secret PIN (4–8 digits)", type="password", placeholder="••••")
            submitted = st.form_submit_button("Sign In", use_container_width=True)
            if submitted:
                ok, msg = sign_in_student(name_input, pin_input)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with tab_signup:
        with st.form("signup_form", clear_on_submit=False):
            new_name = st.text_input("Choose Your Student Name", placeholder="e.g., Maya")
            grade_choice = st.selectbox("Grade Level", ["Grade 4", "Grade 5", "Grade 6"], index=1)
            new_pin = st.text_input("Create a PIN (4–8 numbers)", type="password", placeholder="e.g., 2468")
            confirm_pin = st.text_input("Confirm PIN", type="password", placeholder="Type PIN again")
            created = st.form_submit_button("Create My Profile", use_container_width=True)
            if created:
                if new_pin != confirm_pin:
                    st.error("Your two PIN entries do not match.")
                else:
                    ok, msg = sign_up_student(new_name, new_pin, grade_choice)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)


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