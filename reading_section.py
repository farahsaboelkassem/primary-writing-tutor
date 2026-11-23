import html
import json
import os

import streamlit as st

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

READING_TAXONOMY_JSON = """
{
  "meta": {
    "purpose": "Refined lower primary (Stage 3) and upper primary (Stage 5) skill taxonomy from Cambridge Primary Progression Test papers",
    "sources": {
      "lower_primary_stage_3": [
        "2014 P1 & P2",
        "2017 P1 & P2",
        "2020 P1 & P2",
        "2022 P1 & P2",
        "2023 P1 & P2"
      ],
      "upper_primary_stage_5": [
        "2017 P1 & P2",
        "2020 P1 & P2",
        "2022 P1 & P2",
        "2023 P1 & P2",
        "2024 P1 & P2",
        "2025 P1 & P2"
      ]
    }
  },
  "bands": {
    "lower_primary_stage_3": {
      "grade_band": "lower_primary",
      "cambridge_stage": 3,
      "reading_skills": [
        {
          "skill_id": "S3-R-01",
          "skill_name": "Literal Retrieval & Fact Identification",
          "question_patterns": [
            "Give two things/kinds/examples from a specific section or lines",
            "Complete a sentence using exact words from the text"
          ]
        },
        {
          "skill_id": "S3-R-02",
          "skill_name": "Word & Phrase Meaning in Context",
          "question_patterns": [
            "Give a word or short phrase that means the same as a given definition/phrase",
            "Identify a word that shows surprise, quantity, or a specific attitude"
          ]
        },
        {
          "skill_id": "S3-R-03",
          "skill_name": "Word Choice, Rhyme & Sound Effects",
          "question_patterns": [
            "Explain why a specific verb, adjective, or phrase is chosen over a simpler alternative",
            "Identify rhyme, onomatopoeia, or powerful words"
          ]
        },
        {
          "skill_id": "S3-R-04",
          "skill_name": "Purpose, Layout & Chronological Order",
          "question_patterns": [
            "Identify text purpose (to inform, instruct, amuse, persuade)",
            "Describe how layout/organisation helps the reader (subheadings, lists, numbered steps, glossary)",
            "Match paragraphs to subheadings/topics or sequence events"
          ]
        },
        {
          "skill_id": "S3-R-05",
          "skill_name": "Inference, Feelings & Prediction",
          "question_patterns": [
            "Infer how a character feels or why a character acts/speaks in a certain way",
            "Predict what happens next or what a character says next",
            "Identify story vs. information features or playscript features"
          ]
        }
      ],
      "grammar_punctuation_vocab_skills": [
        {
          "skill_id": "S3-GPV-01",
          "skill_name": "Word Classes & Verb Forms",
          "focus_areas": [
            "noun, verb, adjective, pronoun, preposition, adverb",
            "singular to plural conversion and irregular past/present tense"
          ]
        },
        {
          "skill_id": "S3-GPV-02",
          "skill_name": "Sentence Types & Conjunctions",
          "focus_areas": [
            "statement, question, instruction, exclamation",
            "simple, compound, complex, conditional sentences",
            "joining clauses with conjunctions (but, so, because, and)"
          ]
        },
        {
          "skill_id": "S3-GPV-03",
          "skill_name": "Punctuation, Contractions & Dialogue",
          "focus_areas": [
            "capital letters, full stops, exclamation marks",
            "apostrophes for contractions/omission and full forms",
            "identifying spoken words in direct speech"
          ]
        }
      ],
      "writing_genres": [
        {
          "genre": "information_text",
          "focus": "Non-chronological facts grouped clearly (e.g., sounds around us, an animal)"
        },
        {
          "genre": "instructions",
          "focus": "Materials/equipment list, sequenced steps, imperative verbs, time/manner cues"
        },
        {
          "genre": "narrative_continuation_or_ending",
          "focus": "Ending or continuing a story/traditional tale with character, setting, and plot"
        },
        {
          "genre": "informal_letter",
          "focus": "Personal letter sharing experiences, feelings, and sensory details"
        }
      ]
    },
    "upper_primary_stage_5": {
      "grade_band": "upper_primary",
      "cambridge_stage": 5,
      "reading_skills": [
        {
          "skill_id": "S5-R-01",
          "skill_name": "Point + Quotation Evidence & Evaluation",
          "question_patterns": [
            "Give two reasons/explanations and support EACH with a quotation",
            "Take a stance (Yes/No or character choice) and back up reasons with quotations",
            "Synthesise across paragraphs or compare texts/versions"
          ]
        },
        {
          "skill_id": "S5-R-02",
          "skill_name": "Figurative Language & Literary Devices",
          "question_patterns": [
            "Explain meaning and effect of metaphors, similes, personification, alliteration, onomatopoeia, or repetition",
            "Identify figurative devices in headings or descriptions"
          ]
        },
        {
          "skill_id": "S5-R-03",
          "skill_name": "Structural Craft, Cohesion & Tension",
          "question_patterns": [
            "Explain structural choices (one-word paragraph, shorter sections, subheadings, new paragraph breaks)",
            "Explain how openings/endings link or how tension/excitement is built"
          ]
        },
        {
          "skill_id": "S5-R-04",
          "skill_name": "Authorial Intent, Tone & Persuasion",
          "question_patterns": [
            "Explain rhetorical questions, evaluative/emotive vocabulary, inverted commas, or italics",
            "Identify paragraph/text purpose and supply supporting quotations"
          ]
        }
      ],
      "grammar_punctuation_vocab_skills": [
        {
          "skill_id": "S5-GPV-01",
          "skill_name": "Clauses, Nouns, Modifiers & Pronoun Reference",
          "focus_areas": [
            "main clause vs. subordinate/relative clause",
            "abstract, proper, countable, uncountable (including dual-use), and collective nouns",
            "comparative adverbs, quantifiers, and resolving pronoun reference"
          ]
        },
        {
          "skill_id": "S5-GPV-02",
          "skill_name": "Connectives & Sentence Comparison",
          "focus_areas": [
            "connectives for contrast, examples, emphasis, and cause/effect",
            "comparing sentence structures across examples"
          ]
        },
        {
          "skill_id": "S5-GPV-03",
          "skill_name": "Comma Functions, Quotation/Italics & Word Building",
          "focus_areas": [
            "comma functions (lists, clauses, parenthetical phrases, adverbials)",
            "inverted commas and italics (speech, titles, irony/unusual use, foreign terms/emphasis)",
            "root words, suffixes, negative prefixes, and reported speech"
          ]
        }
      ],
      "writing_genres": [
        {
          "genre": "report_or_magazine_article",
          "focus": "Non-chronological reports or school magazine/website articles tailored to audience"
        },
        {
          "genre": "persuasive_letter_or_email",
          "focus": "Persuading a recipient (e.g., principal/headteacher or buyer) with reasons and appeal"
        },
        {
          "genre": "constrained_narrative_continuation",
          "focus": "Continuing a story while incorporating mandatory plot/character/object/secret elements"
        }
      ]
    }
  }
}
"""


def _load_reading_taxonomy(json_path: str = "reading_taxonomy.json") -> dict:
    """Loads reading_taxonomy.json if present next to app.py, otherwise uses embedded taxonomy."""
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "bands" in data:
                return data
        except Exception:
            pass
    return json.loads(READING_TAXONOMY_JSON)


def _safe_pdf_text(text: str) -> str:
    """Normalizes common punctuation for standard PDF fonts."""
    replacements = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u2022": "-",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _build_exam_pdf_bytes(
    band_key: str,
    band_data: dict,
    paper_choice: str,
    exam_title: str,
    include_writing_lines: bool,
) -> bytes:
    """Generates a printable exam PDF (Paper 1, Paper 2, or Both Papers)."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    stage_num = band_data.get("cambridge_stage", "")
    grade_label = (
        "Lower Primary (Stage 3)"
        if band_key == "lower_primary_stage_3"
        else "Upper Primary (Stage 5)"
    )

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _safe_pdf_text(exam_title), ln=True)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, _safe_pdf_text(f"Stage: {grade_label}  |  Paper: {paper_choice}"), ln=True)
    pdf.cell(0, 7, "Name: ___________________________    Date: _______________", ln=True)
    pdf.ln(4)

    papers = []
    if paper_choice in ("Paper 1 (Reading & Language)", "Both Papers (Paper 1 & Paper 2)"):
        papers.append("PAPER 1: Reading Comprehension & Language")
    if paper_choice in ("Paper 2 (Extended Reading & Writing)", "Both Papers (Paper 1 & Paper 2)"):
        papers.append("PAPER 2: Extended Reading & Writing")

    for section_title in papers:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, _safe_pdf_text(section_title), ln=True)
        pdf.ln(1)

        if section_title.startswith("PAPER 1"):
            q_num = 1
            for skill in band_data.get("reading_skills", []):
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(0, 7, _safe_pdf_text(f"{skill['skill_name']} ({skill['skill_id']})"), ln=True)
                pdf.set_font("Helvetica", "", 10)
                for pattern in skill.get("question_patterns", []):
                    pdf.multi_cell(0, 6, _safe_pdf_text(f"Q{q_num}. {pattern}"))
                    pdf.cell(0, 6, "Answer: ____________________________________________________________________", ln=True)
                    pdf.ln(2)
                    q_num += 1

            for gpv in band_data.get("grammar_punctuation_vocab_skills", []):
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(0, 7, _safe_pdf_text(f"{gpv['skill_name']} ({gpv['skill_id']})"), ln=True)
                pdf.set_font("Helvetica", "", 10)
                focus_text = ", ".join(gpv.get("focus_areas", []))
                pdf.multi_cell(0, 6, _safe_pdf_text(f"Q{q_num}. Practise: {focus_text}"))
                pdf.cell(0, 6, "Answer: ____________________________________________________________________", ln=True)
                pdf.ln(2)
                q_num += 1

        else:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, _safe_pdf_text("Section A: Extended Reading Questions"), ln=True)
            pdf.ln(1)
            for idx, skill in enumerate(band_data.get("reading_skills", []), start=1):
                patterns = skill.get("question_patterns", [])
                prompt_text = patterns[-1] if patterns else skill["skill_name"]
                pdf.set_font("Helvetica", "B", 10)
                pdf.multi_cell(0, 6, _safe_pdf_text(f"A{idx} ({skill['skill_name']}): {prompt_text}"))
                pdf.set_font("Helvetica", "", 10)
                for _ in range(3):
                    pdf.cell(0, 6, "____________________________________________________________________________", ln=True)
                pdf.ln(2)

            if include_writing_lines:
                pdf.ln(2)
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(0, 8, _safe_pdf_text(f"Section B: Writing Task Options (Stage {stage_num})"), ln=True)
                pdf.set_font("Helvetica", "", 10)
                for genre in band_data.get("writing_genres", []):
                    genre_name = genre["genre"].replace("_", " ").title()
                    pdf.multi_cell(0, 6, _safe_pdf_text(f"- {genre_name}: {genre['focus']}"))
                pdf.ln(3)
                for _ in range(8):
                    pdf.cell(0, 7, "____________________________________________________________________________", ln=True)

        pdf.ln(4)

    out = pdf.output(dest="S")
    if isinstance(out, (bytes, bytearray)):
        return bytes(out)
    return out.encode("latin-1")


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
    "Lower Primary (Stage 3)": "lower_primary_stage_3",
    "Upper Primary (Stage 5)": "upper_primary_stage_5",
}


def _chip(text: str) -> str:
    return f'<span class="badge-chip">{html.escape(str(text))}</span>'


def _skill_card(skill_item: dict, skill_type: str) -> None:
    """One skill, shown as a card that matches the rest of the app."""
    bullets = skill_item.get("question_patterns", []) if skill_type == "reading" else skill_item.get("focus_areas", [])
    items = "".join(f"<li>{html.escape(str(b))}</li>" for b in bullets)
    label = "Reading skill" if skill_type == "reading" else "Grammar, punctuation and vocabulary"
    st.markdown(
        f"""
        <div class="adventure-card">
            <div class="step-pill">{html.escape(str(skill_item.get('skill_id', '')))} &nbsp;•&nbsp; {label}</div>
            <div style="font-weight:800;font-size:1.15rem;margin:.1rem 0 .4rem 0;">{html.escape(str(skill_item.get('skill_name', '')))}</div>
            <ul style="margin:0;padding-left:1.2rem;">{items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_reading_section(taxonomy_path: str = "reading_taxonomy.json", bubble=None) -> None:
    """Renders the Reading section with Skill-by-Skill Practice and Full Exam Creation (PDF).

    bubble: optional function from app.py that shows Inky's speech bubble.
    """
    taxonomy = _load_reading_taxonomy(taxonomy_path)
    bands = taxonomy.get("bands", {})

    intro = "Practise the reading skills from the Cambridge Primary Progression Tests, or build a printable practice exam."
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

    selected_stage_label = st.radio(
        "Stage",
        list(STAGE_MAP.keys()),
        horizontal=True,
        key="reading_section_stage",
    )
    band_key = STAGE_MAP[selected_stage_label]
    band_data = bands.get(band_key, {})

    tab_skill, tab_exam = st.tabs(["Skill-by-Skill", "Full Exam Creation (PDF)"])

    with tab_skill:
        st.subheader("Skill-by-Skill Practice")

        reading_skills = band_data.get("reading_skills", [])
        gpv_skills = band_data.get("grammar_punctuation_vocab_skills", [])
        st.markdown(
            _chip(f"{len(reading_skills)} reading skills") + _chip(f"{len(gpv_skills)} language skills"),
            unsafe_allow_html=True,
        )

        skill_options = {}
        for item in reading_skills:
            key = f"Reading | {item['skill_name']} ({item['skill_id']})"
            skill_options[key] = ("reading", item)
        for item in gpv_skills:
            key = f"Grammar / Punctuation / Vocab | {item['skill_name']} ({item['skill_id']})"
            skill_options[key] = ("gpv", item)

        if not skill_options:
            st.info("No skills were found for this stage.")
        else:
            chosen_label = st.selectbox(
                "Select Skill",
                list(skill_options.keys()),
                key=f"reading_skill_picker_{band_key}",
            )
            skill_type, skill_item = skill_options[chosen_label]
            _skill_card(skill_item, skill_type)

            st.text_area(
                "Practice Notes",
                height=130,
                key=f"reading_skill_notes_{band_key}_{skill_item.get('skill_id', '')}",
            )

    with tab_exam:
        st.subheader("Full Exam Creation (PDF)")
        st.caption("Choose a paper, then create a printable practice exam for this stage.")

        paper_choice = st.selectbox(
            "Exam Paper",
            [
                "Paper 1 (Reading & Language)",
                "Paper 2 (Extended Reading & Writing)",
                "Both Papers (Paper 1 & Paper 2)",
            ],
            key=f"reading_exam_paper_{band_key}",
        )
        exam_title = st.text_input(
            "Title",
            value=f"{selected_stage_label} - {paper_choice}",
            key=f"reading_exam_title_{band_key}",
        )
        include_writing_lines = st.checkbox(
            "Include Paper 2 writing task lines",
            value=True,
            key=f"reading_exam_writing_{band_key}",
        )

        if not FPDF_AVAILABLE:
            st.warning("Install `fpdf2` (`pip install fpdf2`) to generate PDFs.")
        else:
            pdf_key = f"reading_pdf_{band_key}_{paper_choice}"
            if st.button("Generate Exam PDF", key=f"btn_reading_pdf_{band_key}", type="primary"):
                st.session_state[pdf_key] = _build_exam_pdf_bytes(
                    band_key=band_key,
                    band_data=band_data,
                    paper_choice=paper_choice,
                    exam_title=exam_title.strip() or selected_stage_label,
                    include_writing_lines=include_writing_lines,
                )

            if pdf_key in st.session_state:
                st.download_button(
                    label="Download PDF",
                    data=st.session_state[pdf_key],
                    file_name=f"{band_key}_exam.pdf",
                    mime="application/pdf",
                    key=f"dl_reading_pdf_{band_key}_{paper_choice}",
                )
