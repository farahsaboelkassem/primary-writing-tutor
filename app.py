from google import genai
from PIL import Image
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="AI Primary Writing Tutor", page_icon="📝", layout="centered"
)

st.title("📝 AI Primary Writing Tutor")
st.write(
    "Select your writing type, either paste your work or upload a photo of"
    " your handwriting, and get instant feedback based on official marking"
    " criteria!"
)

# Sidebar for API Key configuration
st.sidebar.header("Configuration")
api_key_input = st.sidebar.text_input(
    "Enter Google AI Studio API Key", type="password"
)

# Predefined Official Rubrics stored safely inside the app code
FICTION_RUBRIC = """
Fiction Writing Rubric (Total: 25 Marks):
1. Creation of Texts (Wc) - 5 Marks:
   - Features of the genre are correct and clear (including target audience if required).
   - Descriptions of settings, characters (using STEAL), and action are developed to engage/entertain (Show, don't tell).
   - Narrative viewpoint is clear (first or third person) and other characters' points of view are presented with clarity.
   - Dialogues are used properly.
   - Specialised vocabulary that accurately suits the genre is used.

2. Vocabulary and Language (Wv) - 3 Marks:
   - Words/phrases conveying shades of meaning, prefixes, suffixes, and powerful sensory details for effect.
   - Figurative language and transforming meaning with vocabulary.

3. Grammar and Punctuation (Wg) - 7 Marks:
   - Relevant, constant, and correct verb tenses.
   - Correct simple sentence structures.
   - Basic punctuation (full stops, capital letters) used correctly.
   - Accurate simple and compound sentences with trials to create complex ones and accurate punctuation.
   - Variety of simple, compound, and complex sentences used for effect with accurate punctuation.
   - Grammatical structures (phrases, clauses including relative ones, adverbs/adjectives of different degrees) manipulated for effect.
   - Various punctuation marks used for effect.

4. Structure of Texts (Ws) - 7 Marks:
   - Basic sequencing of events within each section/paragraph.
   - Sections/paragraphs logically linked using appropriate time sequence.
   - Ideas organised and narrated in a logical sequence / organised to create a certain effect.
   - Ideas developed and linked using devices like connectives, time and place adverbials.
   - Advanced time devices (flashbacks, flashforwards) used accurately for effect.
   - Development of ideas managed throughout and the end linked to the beginning.

5. Word Structure (Ww) - 3 Marks:
   - Correct spelling of common words (-ing, -ed, polysyllabic, prefixes, suffixes, plurals, homophones).
   - Correct spelling of exceptionally-spelled words, compound/silent vowels, wide range of prefixes/suffixes.
   - Correct spelling of words with same pronunciation suffixes (-tion, -tian), commonly confused homophones (aloud, allowed), and consonants sounding the same (ck, k).
"""

NON_FICTION_RUBRIC = """
Non-Fiction Writing Rubric (Total: 25 Marks):
1. Creation of Texts (Wc) - 5 Marks:
   - Features of the genre are correct and clear throughout.
   - Content clearly aimed at a target audience.
   - Purpose of writing is clear and suits the genre.
   - Style is consistent, establishing relationship between reader and writer (formal/friendly/chatty).
   - Viewpoint is clear and maintained throughout.

2. Vocabulary and Language (Wv) - 3 Marks:
   - Vocabulary generally suitable for text type and purpose.
   - Specialised vocabulary used well for effect.
   - Well-chosen words and phrases to convey appropriate tone/mood (plus genre-specific techniques like literary devices for personal recounts, unbiased language for balanced arguments, or persuasive techniques like AFOREST).

3. Grammar and Punctuation (Wg) - 7 Marks:
   - Verb tenses correct and suitable to the genre (present/past as appropriate).
   - Correct simple sentence structures.
   - Basic punctuation (full stops, capital letters) used correctly.
   - Accurate simple and compound sentences with trials for complex ones.
   - Variety of simple, compound, and complex sentences used for effect and variable punctuation.
   - Appropriate register used (formal/informal) according to context, purpose, and audience.
   - Variable punctuation marks used accurately with intended purpose (e.g. to clarify meaning in complex sentences).

4. Structure of Texts (Ws) - 7 Marks:
   - Structure clear using paragraphs/sections with attempts to organise content.
   - Each paragraph/section has related points grouped together.
   - Ideas organised in a logical sequence (e.g. PEEL Method).
   - Ideas linked using connectives; subheadings, bullet points, and lists used where required.
   - Paragraphs/sections linked using connectives to achieve appropriate effect.
   - Ideas well-developed in a logical way, with conclusions fitting the genre and end linked to the beginning.

5. Word Structure (Ww) - 3 Marks:
   - Correct spelling of common words (-ing, -ed, polysyllabic, prefixes, suffixes, plurals, homophones).
   - Correct spelling of exceptionally-spelled words, compound/silent vowels, wide range of prefixes/suffixes.
   - Correct spelling of suffix variations (-tion, -tian), homophones, and consonants.
"""

# Main Student Interface
genre_choice = st.radio(
    "Select Writing Type:", ("Fiction (Story)", "Non-Fiction (Informational)")
)

# Input method tabs: Text vs Image Upload
input_tab1, input_tab2 = st.tabs(["⌨️ Paste Text", "📸 Upload Handwriting Image"])

student_text = ""
uploaded_image = None

with input_tab1:
  student_text = st.text_area(
      "Paste your writing here:",
      placeholder="Type or paste your paragraphs...",
      height=200,
  )

with input_tab2:
  uploaded_image = st.file_uploader(
      "Upload a picture of your handwritten work:",
      type=["png", "jpg", "jpeg", "webp"],
  )
  if uploaded_image:
    st.image(
        uploaded_image,
        caption="Uploaded Student Writing",
        use_container_width=True,
    )

# Evaluation Button
if st.button("Evaluate Writing", type="primary"):
  if not api_key_input:
    st.error("Please enter your Google AI Studio API key in the sidebar.")
  elif not student_text and not uploaded_image:
    st.warning(
        "Please either paste your writing or upload an image before evaluating."
    )
  else:
    # Automatically select the correct rubric based on the radio button choice
    active_rubric = (
        FICTION_RUBRIC if genre_choice == "Fiction (Story)" else NON_FICTION_RUBRIC
    )

    with st.spinner("Analyzing your writing against the official checklist..."):
      try:
        # Initialize the Google GenAI client
        client = genai.Client(api_key=api_key_input)

        # Construct a detailed prompt for the tutor using the comprehensive rubric
        prompt = f"""
                You are an encouraging, warm, and constructive writing tutor for primary school students. 
                Evaluate the student writing strictly based on the comprehensive marking scheme rubric below across all categories (Creation of Texts, Vocabulary & Language, Grammar & Punctuation, Structure of Texts, and Word Structure).
                
                SELECTED GENRE: {genre_choice}
                
                MARKING SCHEME RUBRIC:
                {active_rubric}
                
                Provide your feedback in a child-friendly, supportive format:
                1. Overall Encouragement (A warm, positive opening statement celebrating their effort)
                2. Two Stars (Two things they did really well according to the rubric categories)
                3. One Wish (One clear, actionable tip for improvement based on the rubric criteria)
                """

        # Prepare contents payload (supports text only, image only, or both)
        content_payload = [prompt]
        if uploaded_image:
          img = Image.open(uploaded_image)
          content_payload.append(img)
        if student_text:
          content_payload.append(f"STUDENT WRITING TEXT:\n{student_text}")

        # Call Gemini 3.7 Flash with multimodal payload
        response = client.models.generate_content(
            model="gemini-3.7-flash", contents=content_payload
        )

        # Display Results
        st.success("Evaluation Complete!")
        st.markdown("### 🌟 Tutor Feedback")
        st.write(response.text)

      except Exception as e:
        st.error(f"An error occurred: {e}")