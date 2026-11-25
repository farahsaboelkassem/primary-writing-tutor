"""Write the starter files for the Supabase question bank.

Run it from the project folder:   python export_question_seed.py

It creates two files:
  question_bank_seed.csv    every built-in question, plus a few example questions in the newer styles
  lesson_id_reference.csv   the list of valid lesson_id values to use in your own questions

Import question_bank_seed.csv into the question_import table (see question_bank_setup.sql).
"""
import csv

import grammar_lessons
import language_lessons

COLUMNS = [
    "question_code", "lesson_id", "question_type", "skill_kind", "question", "correct_answer",
    "wrong_answers", "accepted_answers", "explanation", "difficulty", "case_sensitive", "active",
]

# Example questions in the newer styles. Codes from 101 up never clash with the built-in ones.
# (code, lesson_id, type, kind, question, correct, wrong, accepted, explanation, case_sensitive)
EXAMPLES = [
    ("k1_noun-101", "k1_noun", "true_false", "spot", "A noun is a naming word.", "True", "", "",
     "Nouns name people, animals, places and things.", False),
    ("k1_noun-102", "k1_noun", "true_false", "spot", "The word quickly is a noun.", "False", "", "",
     "Quickly tells us how something happens. It is not a naming word.", False),
    ("k1_noun-103", "k1_noun", "fill_blank", "spot", "Type the noun in this sentence: **The frog jumped.**", "frog", "", "",
     "Frog names an animal, so it is the noun.", False),
    ("k1_plural-101", "k1_plural", "fill_blank", "use", "Write the plural of **fox**.", "foxes", "", "",
     "Words ending in x add -es.", False),
    ("k1_proper-101", "k1_proper", "fill_blank", "use",
     "Rewrite this sentence with the correct capital letters: **my friend lives in cairo.**",
     "My friend lives in Cairo.", "", "",
     "The sentence starts with a capital letter, and Cairo is the name of one particular city.", True),
    ("k1_verb-101", "k1_verb", "fill_blank", "spot", "Type the verb in this sentence: **The birds sing.**", "sing", "", "",
     "Sing is the doing word.", False),
    ("k2_countable-101", "k2_countable", "true_false", "spot", "Water is a countable noun.", "False", "", "",
     "You cannot count water one by one, so it is uncountable.", False),
    ("k2_tenses-101", "k2_tenses", "fill_blank", "use", "Write the past tense of **swim**.", "swam", "", "",
     "Swim is an irregular verb. The past tense is swam.", False),
    ("k2_past_participle-101", "k2_past_participle", "fill_blank", "use",
     "Write the past participle of **write** to complete the sentence: I have ___ a letter.", "written", "", "",
     "After have we use the past participle, written.", False),
    ("k2_apostrophes-101", "k2_apostrophes", "fill_blank", "use",
     "Write **she is** as one word with an apostrophe.", "she's", "", "",
     "The apostrophe takes the place of the missing letter i.", False),
    ("k2_commas-101", "k2_commas", "true_false", "spot",
     "A comma is needed after the opening phrase in: **Later that day we went home.**", "True", "", "",
     "A comma follows an opening phrase like Later that day.", False),
]


def lesson_rows():
    for section, module in (("grammar", grammar_lessons), ("language", language_lessons)):
        for level_key, level in module.LEVELS.items():
            ks = "KS1" if level_key == "lower" else "KS2"
            topics = level.get("topics")
            topic_of = {l["id"]: t["title"] for t in topics for l in t["lessons"]} if topics else {}
            for lesson in level["lessons"]:
                yield section, ks, topic_of.get(lesson["id"], ""), lesson


def main():
    seed, reference = [], []
    for section, ks, topic, lesson in lesson_rows():
        reference.append([lesson["id"], section, ks, topic, lesson["title"], len(lesson["questions"])])
        for n, q in enumerate(lesson["questions"], start=1):
            seed.append([
                f"{lesson['id']}-{n:02d}", lesson["id"], "multiple_choice", q["kind"], q["q"],
                q["options"][0], "|".join(q["options"][1:]), "", q["why"], 1, "FALSE", "TRUE",
            ])
    for code, lid, qtype, kind, q, correct, wrong, accepted, why, case in EXAMPLES:
        seed.append([code, lid, qtype, kind, q, correct, wrong, accepted, why, 1, "TRUE" if case else "FALSE", "TRUE"])

    with open("question_bank_seed.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerows(seed)
    with open("lesson_id_reference.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["lesson_id", "section", "level", "topic", "title", "built_in_questions"])
        writer.writerows(reference)
    print(f"question_bank_seed.csv: {len(seed)} questions")
    print(f"lesson_id_reference.csv: {len(reference)} lessons")


if __name__ == "__main__":
    main()
