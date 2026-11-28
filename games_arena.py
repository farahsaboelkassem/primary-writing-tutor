"""The Game Arena: a hub of learning mini-games. Add a new game by adding one entry to GAMES."""
import html

import streamlit as st

import ink_quest

GAMES = [
    {
        "id": "ink_quest", "icon": "🦉", "title": "Inky's Ink-Quest", "tag": "Platform adventure",
        "blurb": "Run, jump and power up by answering grammar, spelling and word questions. Beat the boss at the end of each world!",
    },
]

ARENA_CSS = """
<style>
[class*="st-key-gamecard_"] { background:#fffdf7; border:2px solid #d9d2f5; border-top:7px solid var(--accent, #6d28d9); border-radius:18px;
  padding:.6rem .9rem .8rem; box-shadow:0 6px 18px rgba(0,0,0,.25); }
.gc-icon { font-size:2.2rem; line-height:1; }
.gc-title { font-family:'Fredoka','Baloo 2',sans-serif; font-weight:700; font-size:1.15rem; color:#2b2a4a; margin-top:.2rem; }
.gc-tag { display:inline-block; background:#efe9ff; color:#3d3499; font-size:.72rem; font-weight:800; border-radius:999px; padding:.05rem .6rem; margin:.15rem 0 .35rem; }
.gc-blurb { color:#5b5a73; font-size:.95rem; line-height:1.4; min-height:3.6rem; }
.gc-soon { opacity:.8; }
</style>
"""


def _open(game_id):
    st.session_state["games_current"] = game_id


def _close():
    st.session_state.pop("games_current", None)


def render_games_arena(db, student_id, age_band, bubble=None, award_xp=None, log_activity=None):
    current = st.session_state.get("games_current")
    if current not in {g["id"] for g in GAMES}:
        current = None

    if current is None:
        if callable(bubble):
            bubble("Welcome to the Game Arena! Pick a game, practise your skills and win bonus XP.", "🎮")
        st.markdown(ARENA_CSS, unsafe_allow_html=True)
        st.markdown("### 🎮 Choose a game")
        cols = st.columns(3)
        for n, game in enumerate(GAMES):
            with cols[n % 3]:
                with st.container(key=f"gamecard_{game['id']}"):
                    st.markdown(
                        f'<div class="gc-icon">{game["icon"]}</div><div class="gc-title">{html.escape(game["title"])}</div>'
                        f'<div class="gc-tag">{html.escape(game["tag"])}</div><div class="gc-blurb">{html.escape(game["blurb"])}</div>',
                        unsafe_allow_html=True,
                    )
                    st.button("▶ Play", key=f"play_{game['id']}", type="primary", use_container_width=True,
                              on_click=_open, args=(game["id"],))
        with cols[len(GAMES) % 3]:
            with st.container(key="gamecard_soon"):
                st.markdown(
                    '<div class="gc-soon"><div class="gc-icon">✨</div><div class="gc-title">More games coming soon</div>'
                    '<div class="gc-blurb">New challenges are on their way. Check back often!</div></div>',
                    unsafe_allow_html=True,
                )
        st.caption(f"You can earn up to {ink_quest.DAILY_GAME_XP} bonus XP from games each day. "
                   "The lessons are still the best way to build your skills!")
        return

    st.button("← Back to all games", key="games_back", on_click=_close)
    game = next(g for g in GAMES if g["id"] == current)
    st.markdown(f"### {game['icon']} {html.escape(game['title'])}")
    if current == "ink_quest":
        ink_quest.render_ink_quest(db, student_id, age_band, award_xp=award_xp, log_activity=log_activity)
