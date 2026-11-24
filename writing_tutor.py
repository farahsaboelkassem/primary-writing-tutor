"""The Writing Adventure - Markschemes, Frameworks, Checklists & Prompt Builders"""

from __future__ import annotations

import re

# ------------------------------------------------------------------
# Age Bands, Rubrics & Marking Rules
# ------------------------------------------------------------------
AGE_BANDS = ("Upper Primary (Grades 4-6)", "Lower Primary (Grades 1-3)")

AGE_BAND_GUIDANCE = {
    "Upper Primary (Grades 4-6)": (
        "Use Cambridge Checkpoint-style expectations. Expect full paragraphs, a "
        "range of punctuation, complex sentences, and figurative language."
    ),
    "Lower Primary (Grades 1-3)": (
        "Maintain academic standards scaled for ages 6-9 (Grades 1-3). "
        "Expect shorter structures (approx. 3 simpler paragraphs or sentences) "
        "and basic punctuation (capital letters, full stops). "
        "Be lenient with phonic spelling (reward phonetically plausible attempts) "
        "and minor grammar slips. "
        "CRITICAL: Never suggest drawing or non-writing tasks as a 'wish'. "
        "Wishes must always be actionable writing tips, such as adding a describing word, "
        "checking for a full stop, or expanding a sentence with 'because'."
    ),
}

MARKER_NOTES = """NOTES TO MARKERS (apply strictly):
1. Begin marking from the LOWEST mark in each category and work upward.
2. Best-fit judgement: pick the band, then the mark within it.
3. If SOME criteria in a band are met but not ALL, give the LOWER mark.
4. Award 0 marks where the response fails the lowest band.
5. Word-count rules (Cambridge Stage 5):
   - <=20 words  -> 0 marks total
   - 21-60 words -> max 7 marks total
   - 61+ words   -> full 25-mark range"""

RUBRICS = {
    "Fiction (Story)": {
        "max": {"Wc": 5, "Wv": 3, "Wg": 7, "Ws": 7, "Ww": 3},
        "bands": {
            "top": {
                "range": {
                    "Wc": (4, 5),
                    "Wv": (3, 3),
                    "Wg": (6, 7),
                    "Ws": (6, 7),
                    "Ww": (3, 3),
                },
                "Wc": "Narrative has ideas and content with detail "
                "developed using well-chosen vocabulary for the "
                "genre. Main features of the genre are clear. "
                "Viewpoint is consistent and may include a "
                "character's opinions of events / settings / other "
                "characters. Writing may develop a given narrative "
                "with new scenes/characters. Playscripts include "
                "production notes / stage directions.",
                "Wv": "A relevant response with well-chosen ideas and "
                "content. Some ideas and material are developed in "
                "detail. Descriptions of characters include details "
                "that help to develop story. Descriptions of settings "
                "and characters show detail using enhanced vocabulary "
                "to engage the reader. Playscripts are based upon "
                "original ideas.",
                "Wg": "Grammar almost always accurate including simple, "
                "compound and complex sentences. Multi-clause "
                "sentences combine simple sentences and/or re-order "
                "clauses. Pronouns and possessive pronouns, modal "
                "verbs, adjectives and adverbs "
                "(comparative/superlative) all used correctly. "
                "Punctuation accurate to demarcate sentences and for "
                "direct speech. Apostrophes accurate. Commas always "
                "used in lists and often to mark clauses.",
                "Ws": "Content organised so that ideas are developed "
                "cohesively throughout most of a sustained piece. "
                "Paragraphs and sections are organised to achieve an "
                "appropriate effect for the genre.",
                "Ww": "Correct spelling of words with less common letter "
                "strings. Some successful attempts to spell "
                "exceptions to known spelling rules. Correctly spell "
                "words with silent vowels and syllables in a range of "
                "polysyllabic words. Spell common homonyms correctly. "
                "Spell words with a wide range of prefixes and "
                "suffixes including opposites. Spell words with "
                "double consonants correctly.",
            },
            "middle": {
                "range": {
                    "Wc": (3, 3),
                    "Wv": (3, 3),
                    "Wg": (4, 5),
                    "Ws": (4, 5),
                    "Ww": (3, 3),
                },
                "Wc": "A relevant response with well-chosen ideas and "
                "content. Some ideas and material are developed in "
                "detail. Descriptions of characters include "
                "details that help to develop story. Descriptions of "
                "settings and characters show detail using "
                "enhanced vocabulary to engage the reader. "
                "Playscripts are based upon original ideas.",
                "Wv": "Purpose of writing is clear and appropriate to "
                "the given genre where features are clearly "
                "evident. A straightforward viewpoint which is "
                "generally consistent and appropriate. Words and "
                "phrases chosen to convey mood and feeling so that "
                "the writing sustains the reader's interest. "
                "Specialised vocabulary used. Figurative language "
                "developed to include alliteration and similes. "
                "Good attempts to use synonyms and "
                "adjectives/adverbs for shades of meaning.",
                "Wg": "Uses an increasing range of sentence types "
                "accurately, including good attempts at complex "
                "structures. Use of expanded phrases to develop "
                "ideas. Punctuation used consistently and "
                "accurately to demarcate sentences. Direct speech "
                "punctuation includes other punctuation. "
                "Apostrophes correct for possession. Commas always "
                "used in lists and often to clarify meaning.",
                "Ws": "Paragraphs and sections used consistently to "
                "organise ideas. Chronological or logical links "
                "between paragraphs help the development of ideas. "
                "Cohesion achieved using connectives to establish "
                "links.",
                "Ww": "Correct spelling of words with less common letter "
                "strings. Some successful attempts to spell "
                "exceptions to known spelling rules. Correctly "
                "spell words with silent vowels and syllables in "
                "polysyllabic words. Spell common homonyms "
                "correctly. Spell words with a wide range of "
                "prefixes and suffixes. Spell words with double "
                "consonants correctly.",
            },
            "bottom": {
                "range": {
                    "Wc": (1, 1),
                    "Wv": (1, 1),
                    "Wg": (1, 1),
                    "Ws": (1, 1),
                    "Ww": (1, 1),
                },
                "Wc": "Some basic material included that is relevant to "
                "the genre. Some elements of the genre can be "
                "seen. (A maximum of 1 mark can be awarded if not "
                "the given genre.)",
                "Wv": "Vocabulary is simple and relevant.",
                "Wg": "Some simple sentence structures are used "
                "successfully. Some correct use of punctuation, "
                "such as full stops and capital letters. Note: do "
                "not discriminate if learners write with good "
                "English but there are punctuation errors. If "
                "ambitious structures are used, begin marking at "
                "2-3 marks, provided there is variation in "
                "sentence openings.",
                "Ws": "Paragraphs/sections are generally used to help "
                "organise and develop a story.",
                "Ww": "Spelling of common inflections is usually "
                "accurate. All simple high frequency words are "
                "spelt correctly. Spelling of high frequency words "
                "is generally correct. Some successful attempts to "
                "phonetically spell polysyllabic and compound "
                "words.",
            },
        },
        "text": "Fiction Writing Rubric (Total: 25 Marks):\n"
        "1. Creation of Texts (Wc) - 5 Marks: Genre features, "
        "character/setting development, narrative viewpoint.\n"
        "2. Vocabulary & Language (Wv) - 3 Marks: Sensory details, figurative "
        "language.\n"
        "3. Grammar & Punctuation (Wg) - 7 Marks: Verb tenses, sentence "
        "structures, punctuation.\n"
        "4. Structure of Texts (Ws) - 7 Marks: Sequencing, paragraphs, "
        "linking devices.\n"
        "5. Word Structure (Ww) - 3 Marks: Spelling, prefixes, suffixes.",
    },
    "Non-Fiction": {
        "max": {"Wc": 5, "Wv": 3, "Wg": 7, "Ws": 7, "Ww": 3},
        "bands": {
            "top": {
                "range": {
                    "Wc": (4, 5),
                    "Wv": (3, 3),
                    "Wg": (6, 7),
                    "Ws": (6, 7),
                    "Ww": (3, 3),
                },
                "Wc": "A relevant response with well-chosen ideas and content. "
                "Some ideas and material are developed in detail. Main "
                "features of the text type are clear. Consistent "
                "viewpoint well-presented and justified. A relationship "
                "between writer and reader is established and maintained "
                "throughout.",
                "Wv": "Words and phrases chosen to convey mood and feeling so "
                "that the writing sustains the reader's interest. "
                "Specialised vocabulary used. Good attempts to use "
                "synonyms for shades of meaning.",
                "Wg": "Grammar almost always accurate including simple, "
                "compound and complex sentences. Multi-clause sentences "
                "combine simple sentences and/or re-order clauses. "
                "Pronouns, modal verbs, adjectives and adverbs all used "
                "correctly. Punctuation accurate for sentences and direct "
                "speech. Apostrophes accurate. Commas always used in "
                "lists and often to mark clauses.",
                "Ws": "Content organised so that ideas are developed cohesively "
                "throughout most of a sustained piece. Paragraphs and "
                "sections are organised to achieve an appropriate effect "
                "for the text type.",
                "Ww": "Correct spelling of words with less common letter "
                "strings. Some successful attempts to spell exceptions to "
                "spelling rules. Silent vowels and syllables correct. "
                "Common homonyms correct. Wide range of prefixes and "
                "suffixes correct. Double consonants correct.",
            },
            "middle": {
                "range": {
                    "Wc": (