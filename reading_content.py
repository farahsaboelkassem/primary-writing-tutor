"""
reading_content.py
Content for the Reading hub: skill definitions, practice sets and mock-exam texts.

Bands:  "lower" = Cambridge Primary Stage 3 (up to about age 8)
        "upper" = Cambridge Primary Stage 5 (up to 6th grade)

Question kinds (all questions share the same shape, see the helpers below):
    mcq    - pick one option
    multi  - tick several options
    short  - written answer; auto-checked with keywords, model answer always shown
    order  - give each item its position (1, 2, 3 ...)
    match  - match each item on the left with an option on the right

To add more practice, append another set to PRACTICE[(skill_id, band)].
To add more mock-exam texts, append another set to EXAM_TEXTS[band].
"""

# ---------------------------------------------------------------------------
# Question helpers
# ---------------------------------------------------------------------------


def _q(skill, kind, q, ans, marks, level, opts=None, acc=None):
    return {
        "skill": skill, "kind": kind, "q": q, "ans": ans,
        "marks": marks, "level": level, "opts": opts or [], "acc": acc or [],
    }


def mcq(skill, q, opts, ans, m=1, lv=1):
    return _q(skill, "mcq", q, ans, m, lv, opts=opts)


def short(skill, q, model, acc, m=1, lv=1):
    return _q(skill, "short", q, model, m, lv, acc=acc)


def multi(skill, q, opts, ans, lv=1):
    return _q(skill, "multi", q, ans, len(ans), lv, opts=opts)


def order(skill, q, items, nums, lv=1):
    return _q(skill, "order", q, nums, max(1, len(items) // 2), lv, opts=items)


def match(skill, q, left, right, ans, lv=1):
    return _q(skill, "match", q, ans, max(1, (len(left) + 1) // 2), lv, opts=[left, right])


def S(title, genre, text, qs):
    return {"title": title, "genre": genre, "text": text.strip(), "qs": qs}


# ---------------------------------------------------------------------------
# Skills
#   src  "guide"     = from the Year 4 Reading Comprehension Skills document
#        "framework" = added from the Cambridge Primary English 0058 framework
# ---------------------------------------------------------------------------

GROUPS = [
    ("understand", "Understanding the text"),
    ("craft", "Language and the writer's craft"),
    ("structure", "Structure and finding information"),
    ("language", "Grammar, punctuation and vocabulary"),
]

SKILLS = [
    {
        "id": "retrieval", "group": "understand", "src": "guide", "icon": "🔍",
        "name": "Explicit Retrieval: Reading for Facts",
        "blurb": "Find facts that are written directly in the text.",
        "objs": {"lower": "3Ri.06 · 3Ri.14 · 3Ri.16", "upper": "5Ri.06 · 5Ri.14 · 5Ri.15"},
        "tips": {
            "lower": ["Read the question twice and circle the key words.",
                      "Scan the text for those words. The answer is usually in the same sentence.",
                      "Copy the facts from the text and check how many answers you need."],
            "upper": ["Underline the question word and key words, and note how many answers or marks it wants.",
                      "Look for synonyms of your key words as well as exact matches.",
                      "Answer with facts from the text only, then re-check against the sentence you found."],
        },
    },
    {
        "id": "inference", "group": "understand", "src": "guide", "icon": "🕵️",
        "name": "Inference: Reading Between the Lines",
        "blurb": "Work out what the writer suggests but does not say.",
        "objs": {"lower": "3Ri.10 · 3Ri.12", "upper": "5Ri.09 · 5Ri.11"},
        "tips": {
            "lower": ["Find the clues: what a character says, does or looks like.",
                      "Ask: how would a real person feel if they did this?",
                      "Answer: “I think … because the text says …”."],
            "upper": ["Gather clues from actions, speech, expressions and events.",
                      "Link the clues to what you know about people and the world to reach a logical inference.",
                      "Prove it: use a short quotation, then explain what it shows."],
        },
    },
    {
        "id": "evidence", "group": "understand", "src": "framework", "icon": "📌",
        "name": "Using Evidence and Quotations",
        "blurb": "Back up your answer with the exact words from the text.",
        "objs": {"lower": "3Ri.16", "upper": "4Ri.15 · 5Ri.15"},
        "tips": {
            "lower": ["Decide your answer first.",
                      "Find the one part of the text that proves it.",
                      "Copy the words exactly and put them in speech marks."],
            "upper": ["State your point clearly, then find the best quotation to support it.",
                      "Keep quotations short: only the words that prove your point.",
                      "Explain how the quotation supports your point (Point, Quote, Explain)."],
        },
    },
    {
        "id": "main_idea", "group": "understand", "src": "framework", "icon": "🗺️",
        "name": "Main Idea and Summary",
        "blurb": "Say what a text is mostly about, in a few words.",
        "objs": {"lower": "3Ri.07", "upper": "5Ri.07"},
        "tips": {
            "lower": ["Ask: what is this text mostly about?",
                      "The main idea is bigger than any single detail.",
                      "A good title sums up the whole text."],
            "upper": ["Pick out the main point of each sentence or paragraph, then group the links between them.",
                      "A summary is short, uses your own words and leaves out small details.",
                      "Check that your summary covers the whole text, not just one part."],
        },
    },
    {
        "id": "predict", "group": "understand", "src": "framework", "icon": "🔮",
        "name": "Predicting What Happens Next",
        "blurb": "Use clues in the story to say what will probably happen.",
        "objs": {"lower": "3Ri.11", "upper": "5Ri.10"},
        "tips": {
            "lower": ["Look for clues in what characters do and in the setting.",
                      "Think about other stories you know.",
                      "Say: “I predict … because …”."],
            "upper": ["Use different kinds of clues: personality, setting, warnings and earlier events.",
                      "Choose the prediction that fits the most clues.",
                      "Support your prediction with evidence from the text."],
        },
    },
    {
        "id": "theme", "group": "understand", "src": "framework", "icon": "💡",
        "name": "Themes and Comparing Texts",
        "blurb": "Spot the big message of a story and compare texts.",
        "objs": {"lower": "3Ri.17", "upper": "5Ri.16 · 5Rs.01"},
        "tips": {
            "lower": ["Ask: what lesson does the story teach?",
                      "Think about how the main character changes or what goes wrong.",
                      "Different stories can teach the same lesson."],
            "upper": ["A theme is a big idea (such as honesty or generosity), not a plot summary.",
                      "Look at what characters learn, gain or lose.",
                      "When comparing, say what is the same and what is different."],
        },
    },
    {
        "id": "language", "group": "craft", "src": "guide", "icon": "🧰",
        "name": "Language and Structure: The Writer's Toolbox",
        "blurb": "Spot the tools writers use and explain their effect.",
        "objs": {"lower": "3Rv.04 · 3Rv.05 · 3Rv.07", "upper": "4Rv.07 · 5Rv.05 · 5Rv.06 · 5Rv.07"},
        "tips": {
            "lower": ["Name the tool: simile (like or as), sound word, or a powerful word.",
                      "Find it in the text.",
                      "Say what picture or feeling it gives the reader."],
            "upper": ["Identify the device: simile, metaphor, personification, alliteration, hyperbole, short sentence or rhetorical question.",
                      "Quote the example exactly.",
                      "Explain the effect: what image or mood does it create, and why did the writer choose it?"],
        },
    },
    {
        "id": "viewpoint", "group": "craft", "src": "guide", "icon": "🎯",
        "name": "Purpose, Audience and Viewpoint",
        "blurb": "Why was it written, who is it for, and who is telling it?",
        "objs": {"lower": "3Ri.05", "upper": "5Ri.05 · 5Ri.17"},
        "tips": {
            "lower": ["Does it tell a story (entertain), give facts (inform), give steps (instruct) or sell something (persuade)?",
                      "Think about who it is written for.",
                      "Find words that show the writer's feelings."],
            "upper": ["Decide the purpose from the clues: entertain, inform, instruct or persuade.",
                      "Tone is the writer's attitude; mood is how the reader feels. Check the word choice.",
                      "First person (I) shows one character's thoughts; third person (he, she) is an outside narrator."],
        },
    },
    {
        "id": "text_features", "group": "structure", "src": "framework", "icon": "🎭",
        "name": "Playscripts and Text Features",
        "blurb": "Read playscripts and use the features of different texts.",
        "objs": {"lower": "3Rs.02 · 3Ri.09", "upper": "5Ri.08 · 5Rs.02"},
        "tips": {
            "lower": ["In a playscript, names show who speaks and brackets show how to act.",
                      "Scene headings tell you where the action happens.",
                      "Follow instructions in order, one step at a time."],
            "upper": ["Stage directions guide actors and create atmosphere.",
                      "Compare a playscript with a story: what is shown through speech and what is described?",
                      "Say how each feature helps the reader or the performer."],
        },
    },
    {
        "id": "sequencing", "group": "structure", "src": "guide", "icon": "🔢",
        "name": "Sequencing and Matching",
        "blurb": "Put events in order and match paragraphs to topics.",
        "objs": {"lower": "3Rs.01 · 3Rs.03 · 3Rs.04", "upper": "4Rs.03 · 5Rs.01 · 5Rs.03"},
        "tips": {
            "lower": ["Look for time words: first, next, then, after, finally.",
                      "Say the story to yourself in order.",
                      "Match each paragraph to the heading that sums it up."],
            "upper": ["Use time and sequence words, but also cause and effect, to order events.",
                      "Work out the main topic of each paragraph before matching.",
                      "Check your final order makes sense from start to finish."],
        },
    },
    {
        "id": "skim_scan", "group": "structure", "src": "framework", "icon": "🔦",
        "name": "Skim, Scan and Find Information",
        "blurb": "Use headings, contents, indexes and glossaries to find things fast.",
        "objs": {"lower": "3Ri.14 · 3Ri.15 · 3Rv.03", "upper": "4Ri.13 · 5Ri.13 · 5Rv.04"},
        "tips": {
            "lower": ["Contents and index pages tell you where to look.",
                      "Scan for a key word. Don't read every word.",
                      "Glossaries and dictionaries are in alphabetical order."],
            "upper": ["Skim to get the general idea (headings, first sentences). Scan to find a specific detail.",
                      "Use headings, contents, indexes and glossaries to go straight to the right part.",
                      "Check that the detail you found answers the exact question."],
        },
    },
    {
        "id": "fact_opinion", "group": "structure", "src": "framework", "icon": "⚖️",
        "name": "Fact or Opinion",
        "blurb": "Tell what can be proved from what someone thinks.",
        "objs": {"lower": "3Ri.13", "upper": "5Ri.12"},
        "tips": {
            "lower": ["A fact can be checked and proved.",
                      "An opinion tells what someone thinks or feels.",
                      "Opinion clues: I think, best, worst, horrible, lovely."],
            "upper": ["Ask: could I check this in a reliable source? If yes, it is a fact.",
                      "Opinion clues include evaluative words (best, dazzling) and phrases such as surely or frankly.",
                      "Writers often mix facts and opinions to persuade, so look at each sentence."],
        },
    },
    {
        "id": "grammar", "group": "language", "src": "guide", "icon": "🧩",
        "name": "Word Classes and Sentence Types",
        "blurb": "Name word classes, clauses, connectives and sentence types.",
        "objs": {"lower": "3Rg.05 · 3Rg.08 · 3Rg.09", "upper": "5Rg.02 · 5Rg.03"},
        "tips": {
            "lower": ["Noun = person, place or thing. Verb = action. Adjective describes a noun. Adverb describes a verb.",
                      "Statements tell, questions ask, commands give orders.",
                      "Connectives such as and, but and because join ideas."],
            "upper": ["Decide a word's job in its sentence, not just how it looks.",
                      "A main clause stands alone. A subordinate clause starts with a word like although or because. A relative clause adds detail (who, which).",
                      "Check connectives: do they add, contrast, give a reason or show time?"],
        },
    },
    {
        "id": "sentence_change", "group": "language", "src": "guide", "icon": "🔧",
        "name": "Sentence Manipulation",
        "blurb": "Change tense, combine clauses, move adverbs, fix agreement.",
        "objs": {"lower": "3Wg.05 · 3Wg.06 · 3Wg.07", "upper": "5Wg.04 · 5Wg.07 · 5Wg.08"},
        "tips": {
            "lower": ["To change tense, change the verb (play → played).",
                      "Join sentences with a connective such as because, but or and.",
                      "Check the verb matches who is doing it (the dogs run)."],
            "upper": ["When you change tense, change every verb that needs it.",
                      "Combine sentences with a connective. If the subordinate clause comes first, add a comma.",
                      "An adverb can often move, but check the meaning stays the same."],
        },
    },
    {
        "id": "punctuation", "group": "language", "src": "guide", "icon": "✏️",
        "name": "Punctuation",
        "blurb": "Speech marks, apostrophes and commas.",
        "objs": {"lower": "3Rg.02 · 3Rg.03 · 3Rg.04", "upper": "5Wg.01 · 5Wg.02 · 5Wg.03"},
        "tips": {
            "lower": ["Speech marks go round the words that are spoken.",
                      "An apostrophe shows missing letters (it's = it is).",
                      "Use a capital letter to start and a full stop, question mark or exclamation mark to end."],
            "upper": ["Punctuate direct speech: speech marks, a comma or end mark inside them, a new line for a new speaker.",
                      "Apostrophes show omission (don't) or possession (the dog's bone, the dogs' bones).",
                      "Commas separate list items, follow openers and mark extra information."],
        },
    },
    {
        "id": "vocabulary", "group": "language", "src": "guide", "icon": "📚",
        "name": "Vocabulary in Context",
        "blurb": "Work out word meanings from clues, prefixes and suffixes.",
        "objs": {"lower": "3Rv.01 · 3Rv.02", "upper": "5Rv.01 · 5Rv.02"},
        "tips": {
            "lower": ["Read the whole sentence. The other words are clues.",
                      "Try your word in place of the tricky one. Does it still make sense?",
                      "Look for a smaller word you know inside the word."],
            "upper": ["Use context: definitions, opposites and examples near the word.",
                      "Break the word into prefix, root and suffix (un-, -ful, -ment).",
                      "Idioms don't mean what the words say. Work out the meaning from how it is used."],
        },
    },
    {
        "id": "speech_pronoun_modal", "group": "language", "src": "framework", "icon": "💬",
        "name": "Speech, Pronouns and Modal Verbs",
        "blurb": "Direct and reported speech, pronoun reference, modal verbs.",
        "objs": {"lower": "3Rg.04 · 3Rg.08", "upper": "5Rg.01 · 5Rg.04 · 5Rg.05"},
        "tips": {
            "lower": ["Words inside speech marks are what the person really said.",
                      "A pronoun (he, she, it, they) stands in for a noun. Find who or what it means.",
                      "Look back at the sentence before to find the noun."],
            "upper": ["Reported speech has no speech marks and usually moves the verb back (will → would).",
                      "Possessive pronouns (mine, yours, theirs) stand alone. Check what each pronoun refers to.",
                      "Modal verbs show certainty: will is certain, might is only possible."],
        },
    },
]

SKILL_BY_ID = {s["id"]: s for s in SKILLS}

# Skills whose questions are sentence-level language work. In a mock exam these form the
# separate "Language" section; all other skills are read against the main texts.
LANGUAGE_SKILLS = ["grammar", "sentence_change", "punctuation", "vocabulary", "speech_pronoun_modal"]
READING_SKILLS = [s["id"] for s in SKILLS if s["id"] not in LANGUAGE_SKILLS]

# ---------------------------------------------------------------------------
# Practice sets: PRACTICE[(skill_id, band)] -> list of sets
# ---------------------------------------------------------------------------

PRACTICE = {}


def _add(skill, band, s):
    PRACTICE.setdefault((skill, band), []).append(s)


# ========================= LOWER PRIMARY (Stage 3) =========================

_add("retrieval", "lower", S("The Honey Bee", "non-fiction", """
Honey bees live together in a hive. A hive can hold thousands of bees. The queen bee lays the eggs. Worker bees collect nectar from flowers and carry it back to the hive. They turn the nectar into honey. A bee has two pairs of wings, six legs and two big eyes. In winter the bees stay inside the hive and eat the honey they stored.
""", [
    short("retrieval", "Where do honey bees live?", "In a hive.", ["hive"]),
    multi("retrieval", "Tick two things that worker bees do.",
          ["Lay the eggs", "Collect nectar", "Turn nectar into honey", "Sleep all summer"],
          ["Collect nectar", "Turn nectar into honey"]),
    short("retrieval", "Name one part of a bee's body that the text mentions.", "Wings, legs or eyes.", ["wing", "leg", "eye"]),
]))

_add("inference", "lower", S("At the Pool", "fiction", """
Mia stood at the edge of the pool. Her toes curled over the tiles and her hands shook. “I will just watch for now,” she said quietly, looking at the floor. Behind her, Dad smiled and said, “Take your time.”
""", [
    mcq("inference", "How does Mia feel about jumping in?", ["Nervous", "Excited", "Angry", "Bored"], "Nervous"),
    short("inference", "Write one clue from the text that shows this.",
          "Her hands shook / she looked at the floor / she spoke quietly.", ["hand", "shook", "floor", "quiet", "toes"]),
    mcq("inference", "Why do you think Dad says “Take your time”?",
        ["He wants her to hurry", "He wants her to feel safe and not rushed", "He is bored", "He wants to go home"],
        "He wants her to feel safe and not rushed", lv=2),
]))

_add("evidence", "lower", S("Grandpa's Garden", "fiction", """
Grandpa's garden was full of life. Bees hummed over the lavender and a robin hopped along the fence. Grandpa hummed too as he watered the beans. “This is the best part of my day,” he said.
""", [
    mcq("evidence", "Does Grandpa enjoy his garden?", ["Yes", "No"], "Yes"),
    short("evidence", "Copy words from the text that show this.",
          "“Grandpa hummed too” or “the best part of my day”.", ["hummed", "best part"], m=1, lv=2),
    short("evidence", "Name one animal in the garden. Copy the words from the text.", "Bees or a robin.", ["bees", "robin"]),
]))

_add("main_idea", "lower", S("Super Swimmers", "non-fiction", """
Penguins are birds that cannot fly. Instead, they are brilliant swimmers. Their wings work like flippers and their smooth bodies slip through the water. Emperor penguins can stay underwater for many minutes while they hunt for fish.
""", [
    mcq("main_idea", "What is this text mostly about?",
        ["Penguins are great swimmers", "Penguins live in the snow", "How to catch fish", "Why birds can fly"],
        "Penguins are great swimmers"),
    short("main_idea", "Give one reason penguins swim well.", "Their wings work like flippers / their bodies are smooth.", ["flipper", "smooth"]),
    mcq("main_idea", "Which is the best title?", ["Super Swimmers", "Flying High", "A Penguin's Dinner", "Snowy Homes"], "Super Swimmers"),
]))

_add("predict", "lower", S("Ravi's Bag", "fiction", """
Ravi packed his bag for the school trip. He put in a towel, a swimming costume and his goggles. Outside, dark grey clouds rolled across the sky and a big drop of rain landed on the window.
""", [
    mcq("predict", "Where is Ravi probably going?", ["To the swimming pool", "To a library", "To bed", "To the dentist"], "To the swimming pool"),
    mcq("predict", "What do you think will happen next?",
        ["It will start to pour with rain", "A dragon will appear", "Ravi will unpack and go to sleep"],
        "It will start to pour with rain"),
    short("predict", "Write one clue that helped you predict.", "Dark grey clouds / a drop of rain / towel and goggles.",
          ["cloud", "rain", "towel", "goggle", "costume"]),
]))

_add("theme", "lower", S("Kip and Pip", "fiction", """
Kip the rabbit boasted that he was the fastest animal in the wood. Pip the snail said, “I will race you.” Kip laughed and took a nap under a tree. Slowly, Pip crept past him and crossed the line first.
""", [
    mcq("theme", "What lesson does the story teach?",
        ["Slow and steady can win, and you should not boast", "Rabbits are fast", "Never race", "Naps are bad for you"],
        "Slow and steady can win, and you should not boast"),
    short("theme", "How did Kip's behaviour help Pip to win?", "Kip took a nap.", ["nap", "slept", "asleep"]),
    mcq("theme", "Which word best describes Kip at the start?", ["Boastful", "Shy", "Kind", "Sad"], "Boastful"),
]))

_add("language", "lower", S("Windy Night", "fiction", """
The wind howled around the cottage. Whoosh! The door banged shut. Inside, the fire was as warm as a hug. Crackle, crackle, went the logs.
""", [
    multi("language", "Tick the two words that sound like the noise they describe.",
          ["Whoosh", "cottage", "Crackle", "inside"], ["Whoosh", "Crackle"]),
    short("language", "Find the simile (a comparison using “as … as” or “like”).", "as warm as a hug", ["warm as a hug"]),
    mcq("language", "Why does the writer use “howled” instead of “blew”?",
        ["It makes the wind sound loud and wild", "It is shorter", "It rhymes", "It sounds quiet"],
        "It makes the wind sound loud and wild", lv=2),
]))

_add("viewpoint", "lower", S("Splash Park", "non-fiction", """
Come to Splash Park! Slide down our giant, twisty slides, float on our lazy river and eat yummy ice cream. Open every day in summer. Bring your family and have the best day ever!
""", [
    mcq("viewpoint", "What is the purpose of this text?",
        ["To tell a story", "To persuade people to visit", "To give instructions", "To teach about water"],
        "To persuade people to visit"),
    mcq("viewpoint", "Who is this text mostly aimed at?", ["Families with children", "Scientists", "Pilots", "Doctors"], "Families with children"),
    short("viewpoint", "Write one word or phrase that tries to persuade the reader.", "For example: giant, yummy, best day ever.",
          ["giant", "twisty", "lazy", "yummy", "best day", "come"]),
]))

_add("text_features", "lower", S("Soup for Tea", "playscript", """
SCENE 1: The kitchen.
MUM: (stirring a pot) Who wants soup?
TOM: (jumping up) Me!
SAM: (frowning) Not me. I hate carrots.
""", [
    mcq("text_features", "What do the words in brackets tell the actor?",
        ["How to act or speak", "Where the scene is", "Who is speaking", "What time it is"], "How to act or speak"),
    short("text_features", "Who says “Me!”?", "Tom.", ["tom"]),
    mcq("text_features", "Where is Scene 1 set?", ["The kitchen", "The garden", "A school", "A shop"], "The kitchen"),
]))

_add("sequencing", "lower", S("Planting a Seed", "fiction", """
First, Ben filled a pot with soil. Next, he pushed a seed into the soil. Then he gave it a little water. After a week, a tiny green shoot appeared.
""", [
    order("sequencing", "Number the events 1 to 4 in the order they happened.",
          ["A tiny shoot appeared.", "Ben gave the seed some water.", "Ben filled the pot with soil.", "Ben pushed a seed into the soil."],
          [4, 3, 1, 2]),
    mcq("sequencing", "Which word shows what happened second?", ["First", "Next", "Then", "After a week"], "Next"),
    mcq("sequencing", "What happened last?",
        ["A shoot appeared", "Ben watered the seed", "Ben filled the pot", "Ben bought a seed"], "A shoot appeared"),
]))

_add("skim_scan", "lower", S("Wild Weather Book", "non-fiction", """
CONTENTS: 1 Volcanoes (page 2) | 2 Earthquakes (page 6) | 3 Storms (page 10) | 4 Floods (page 14)

GLOSSARY: crater – the bowl-shaped hole at the top of a volcano; lava – hot melted rock; magma – melted rock under the ground.
""", [
    mcq("skim_scan", "On which page would you read about storms?", ["Page 2", "Page 6", "Page 10", "Page 14"], "Page 10"),
    mcq("skim_scan", "What does “crater” mean?",
        ["A bowl-shaped hole at the top of a volcano", "Hot melted rock", "A big storm", "A kind of flood"],
        "A bowl-shaped hole at the top of a volcano"),
    order("skim_scan", "Put these glossary words in alphabetical order (1 to 3).", ["magma", "crater", "lava"], [3, 1, 2]),
]))

_add("fact_opinion", "lower", S("Frogs", "non-fiction", """
Frogs are amphibians. They lay eggs in water. I think frogs are the cutest animals in the pond. Their skin feels slimy, which is horrible. A frog can jump many times its own length.
""", [
    multi("fact_opinion", "Tick two sentences that are facts.",
          ["Frogs are amphibians.", "Frogs are the cutest animals in the pond.", "They lay eggs in water.", "Slimy skin is horrible."],
          ["Frogs are amphibians.", "They lay eggs in water."]),
    mcq("fact_opinion", "Which word shows an opinion?", ["cutest", "water", "eggs", "jump"], "cutest"),
    short("fact_opinion", "Write one opinion from the text.", "Frogs are the cutest / slimy skin is horrible.", ["cutest", "horrible", "i think"]),
]))

_add("grammar", "lower", S("The Small Dog", "fiction", """
The small dog ran quickly across the garden. Can you see him? Close the gate, please! Dad was happy because the dog was safe.
""", [
    match("grammar", "Match each word to its word class.", ["dog", "ran", "small", "quickly"],
          ["noun", "verb", "adjective", "adverb"], ["noun", "verb", "adjective", "adverb"]),
    match("grammar", "What type of sentence is each one?",
          ["Can you see him?", "Close the gate, please!", "The small dog ran quickly across the garden."],
          ["statement", "question", "command"], ["question", "command", "statement"]),
    short("grammar", "Find the connective (joining word) in the last sentence.", "because", ["because"]),
]))

_add("sentence_change", "lower", S("Sentence Workshop", "fiction", """
The children play in the park. Sam was cold. He put on a coat. The dogs runs fast.
""", [
    short("sentence_change", "Rewrite in the past tense: “The children play in the park.”", "The children played in the park.", ["played"]),
    short("sentence_change", "Join “Sam was cold.” and “He put on a coat.” using because.",
          "Sam put on a coat because he was cold.", ["because"], lv=2),
    short("sentence_change", "Correct the mistake in “The dogs runs fast.”", "The dogs run fast.", ["dogs run"]),
]))

_add("punctuation", "lower", S("A Cold Day", "fiction", """
Lily asked, “Can we go to the beach?” Mum smiled. “It's too cold today,” she said. “We'll go on Saturday.”
""", [
    mcq("punctuation", "Which sentence is punctuated correctly?",
        ["“Can we go to the park?” asked Tom.", "“Can we go to the park” asked Tom?",
         "Can we go to the park? asked “Tom.”", "“Can we go to the park?” Asked Tom."],
        "“Can we go to the park?” asked Tom."),
    mcq("punctuation", "“It's” in the passage is short for …", ["it is", "it was", "its", "in the"], "it is"),
    mcq("punctuation", "Why does “We'll” have an apostrophe?",
        ["To show letters are missing", "To show something belongs to someone", "To show it is a question"],
        "To show letters are missing"),
]))

_add("vocabulary", "lower", S("The Cave", "fiction", """
The gloomy cave was enormous. Tara crept inside, feeling brave but a little nervous. Her torch lit up glittering crystals on the walls.
""", [
    short("vocabulary", "Write a word that means the same as “enormous”.", "Huge, giant, massive …", ["huge", "giant", "massive", "big", "gigantic", "large"]),
    mcq("vocabulary", "“Gloomy” means …", ["Dark and sad-looking", "Bright", "Noisy", "Warm"], "Dark and sad-looking"),
    short("vocabulary", "Find one word that tells you the crystals were sparkly.", "glittering", ["glittering"]),
]))

_add("speech_pronoun_modal", "lower", S("The Apple", "fiction", """
Zara told her brother, “I am hungry.” He said, “You can have my apple.” She thanked him and ate it.
""", [
    short("speech_pronoun_modal", "Which words did Zara say? Copy them.", "I am hungry.", ["i am hungry"]),
    mcq("speech_pronoun_modal", "Who does “He” mean?", ["Zara's brother", "Zara", "Dad", "The apple"], "Zara's brother"),
    mcq("speech_pronoun_modal", "What does “it” mean in the last sentence?", ["The apple", "The brother", "Zara", "Hunger"], "The apple"),
]))

# ========================= UPPER PRIMARY (Stage 5) =========================

_add("retrieval", "upper", S("The Mangrove Forest", "non-fiction", """
Mangroves are trees that grow where rivers meet the sea. Their tangled roots rise above the muddy water, trapping sediment and slowing the waves that crash towards the shore. In Vietnam, communities have replanted thousands of hectares of mangroves to protect villages from storm surges. Fish, crabs and prawns shelter among the roots when they are young, which is why local fishers describe the forests as “nurseries of the sea”. However, large areas have been cleared to make room for fish farms and buildings.
""", [
    short("retrieval", "Give two ways mangrove roots protect the coast.", "They trap sediment and slow the waves.", ["sediment", "wave"], m=2),
    short("retrieval", "Why do local fishers call mangroves “nurseries of the sea”?",
          "Young fish, crabs and prawns shelter among the roots.", ["young", "shelter", "fish", "crab", "prawn"], lv=2),
    mcq("retrieval", "Which reason for clearing mangroves is NOT mentioned in the text?",
        ["To make room for fish farms", "To make room for buildings", "To collect firewood"], "To collect firewood", lv=2),
]))

_add("inference", "upper", S("Behind the Curtain", "fiction", """
Elena had rehearsed the speech forty times in her bedroom. Now, standing behind the curtain, she folded the paper into a tiny square, then unfolded it, then folded it again. Through the gap she could see rows of faces. “You'll be wonderful,” whispered Mr Okoro. Elena nodded, though her throat felt as dry as chalk, and she did not let go of the paper.
""", [
    mcq("inference", "How does Elena feel?",
        ["Calm and relaxed", "Anxious about performing", "Angry with Mr Okoro", "Bored"], "Anxious about performing"),
    short("inference", "Give two pieces of evidence from the text that show this.",
          "She keeps folding and unfolding the paper; her throat is dry.", ["fold", "throat", "dry", "paper"], m=2, lv=2),
    short("inference", "What does rehearsing forty times suggest about Elena?", "She cares a lot and wants to do well.",
          ["care", "important", "determined", "want", "perfect", "worr", "hard"], lv=3),
]))

_add("evidence", "upper", S("The Match", "fiction", """
Amir folded his arms and glared at the ground. “I don't care about the stupid match,” he muttered. But when the whistle blew, he was the first one on the pitch, shirt tucked in, boots laced so tightly his toes ached.
""", [
    mcq("evidence", "Does Amir really not care about the match?",
        ["He cares more than he says", "He really doesn't care", "He is afraid of the ball", "He is angry with the referee"],
        "He cares more than he says"),
    short("evidence", "Support your answer with a short quotation.", "“he was the first one on the pitch” or “boots laced so tightly”.",
          ["first one on the pitch", "laced", "tucked"], lv=2),
    short("evidence", "Explain how your quotation shows this.", "It shows he is eager and prepared, so he does care.",
          ["eager", "keen", "prepared", "care", "ready", "excited"], m=2, lv=3),
]))

_add("main_idea", "upper", S("Why Sleep Matters", "non-fiction", """
Sleep is not wasted time. While children sleep, their brains sort the day's memories and their bodies repair muscles. Tired pupils find it harder to concentrate and are more likely to feel grumpy. Experts recommend that children aged ten should sleep for at least nine hours a night, which means switching off screens an hour before bedtime.
""", [
    mcq("main_idea", "Which sentence best sums up the text?",
        ["Sleep helps children's brains and bodies, so they need enough of it.", "Screens are bad for everyone.",
         "Tired children are always grumpy.", "Muscles need exercise to grow."],
        "Sleep helps children's brains and bodies, so they need enough of it."),
    short("main_idea", "Summarise two benefits of sleep from the text.", "Brains sort memories and bodies repair muscles; concentration improves.",
          ["memor", "repair", "muscle", "concentrat", "grumpy"], m=2),
    short("main_idea", "Give one piece of advice from the text.", "Sleep at least nine hours / switch off screens an hour before bed.",
          ["screen", "nine hours", "9 hours"]),
]))

_add("predict", "upper", S("The Dare", "fiction", """
Jonah had never once backed away from a dare. When the older boys dared him to climb the crumbling lighthouse, he grinned, tightened his laces and ignored Priya's warning. “Don't be silly,” she called. “The stairs have been closed for years.” Jonah was already at the door, and the rusty padlock had come loose in his hand.
""", [
    mcq("predict", "What is most likely to happen next?",
        ["Jonah will go into the lighthouse", "Jonah will go home", "Priya will climb it instead", "The older boys will apologise"],
        "Jonah will go into the lighthouse"),
    short("predict", "Give two clues from the text that support your prediction.", "He has never backed away from a dare; the padlock has come loose.",
          ["never once", "dare", "grinned", "padlock", "loose", "ignored"], m=2, lv=2),
    mcq("predict", "What does “the stairs have been closed for years” suggest?",
        ["The stairs may be unsafe", "The lighthouse is new", "Priya owns the lighthouse", "The stairs are painted"],
        "The stairs may be unsafe", lv=2),
]))

_add("theme", "upper", S("Two Gifts", "fiction", """
Text A: A king owned a thousand golden cups but drank only from his cracked clay mug, for it had been made by his daughter.

Text B: Marcus saved his pocket money for months to buy the latest trainers. When he finally had them, he gave them to his friend Dev, whose own shoes had split in the rain. Nothing had ever felt so good.
""", [
    mcq("theme", "Which theme do both texts share?",
        ["Kindness and love matter more than expensive things", "Rich people are unhappy", "Saving money is difficult", "Clay is better than gold"],
        "Kindness and love matter more than expensive things"),
    short("theme", "Explain how the theme is shown in Text B.", "Marcus gives up his new trainers to help his friend and it feels good.",
          ["gave", "friend", "nothing had ever felt", "generous", "kind"], m=2, lv=2),
    mcq("theme", "How are the two texts different?",
        ["Text A is a traditional-style tale; Text B has a modern setting", "Text A is non-fiction", "Text B has no characters", "They have opposite themes"],
        "Text A is a traditional-style tale; Text B has a modern setting", lv=3),
]))

_add("language", "upper", S("The Storm", "fiction", """
The storm was a hungry beast. Its claws of lightning tore at the sky while the wind screamed through the streets. Shutters shuddered; slates slid from the roof. Rain drummed on the windows like a thousand impatient fingers.
""", [
    short("language", "Identify the metaphor in the first sentence.", "The storm was a hungry beast.", ["hungry beast"]),
    mcq("language", "Which phrase is a simile?",
        ["The storm was a hungry beast", "Shutters shuddered; slates slid", "Rain drummed on the windows like a thousand impatient fingers", "Its claws of lightning"],
        "Rain drummed on the windows like a thousand impatient fingers"),
    multi("language", "Tick two examples of alliteration.",
          ["Shutters shuddered", "slates slid", "tore at the sky", "through the streets"], ["Shutters shuddered", "slates slid"], lv=2),
    short("language", "Explain the effect of comparing the storm to a “hungry beast”.", "It makes the storm seem alive, fierce and dangerous.",
          ["dangerous", "violent", "frighten", "destroy", "alive", "animal", "fierce", "scary"], m=2, lv=3),
]))

_add("viewpoint", "upper", S("Dig In!", "non-fiction", """
Some people say that school gardens are just muddy distractions. Surely, though, nobody can seriously believe that pupils learn nothing from growing their own food? Children who plant, water and harvest vegetables understand where meals come from, and they are far more likely to try them. It is time every school dug in.
""", [
    mcq("viewpoint", "What is the purpose of this text?", ["To persuade", "To entertain", "To instruct", "To describe a person"], "To persuade"),
    short("viewpoint", "Explain how the rhetorical question helps to persuade the reader.",
          "It makes the reader think the answer is obvious so they agree with the writer.", ["obvious", "agree", "think", "no answer", "makes the reader"], m=2, lv=2),
    mcq("viewpoint", "Which words best describe the writer's tone?",
        ["Hesitant and unsure", "Confident and persuasive", "Gloomy and sad", "Neutral and factual"], "Confident and persuasive"),
]))

_add("text_features", "upper", S("The Lantern", "playscript", """
ACT 1, SCENE 2: A ruined castle at midnight.
(Thunder rumbles. ELLA enters, holding a lantern.)
ELLA: (whispering) Hello? Is anyone there?
(A cold breeze blows out the lantern.)
VOICE: (from the shadows) I have been waiting a very long time.
""", [
    mcq("text_features", "What is the purpose of the text in brackets?",
        ["Stage directions telling the actors and director what to do", "Words the audience must say", "The title of the play", "The author's opinion"],
        "Stage directions telling the actors and director what to do"),
    short("text_features", "Give one example of how the writer creates a spooky atmosphere.", "Thunder, midnight, the ruined castle, the lantern blowing out, a voice in the shadows.",
          ["thunder", "midnight", "shadow", "breeze", "lantern", "ruined"], lv=2),
    mcq("text_features", "How would this moment look in a novel?",
        ["The narrator would describe actions and feelings in paragraphs, instead of using names and brackets",
         "It would be exactly the same", "It would have no dialogue", "It would be a list of steps"],
        "The narrator would describe actions and feelings in paragraphs, instead of using names and brackets", lv=3),
]))

_add("sequencing", "upper", S("The Journey of a Letter", "non-fiction", """
1. Every letter begins its journey in a post box, where it waits to be collected by a postal worker.
2. At the sorting office, machines read the postcode and sort the letters by area.
3. Next, the letters are loaded onto vans, trains or planes for the long journey.
4. Finally, a local postal worker delivers the letter to the right door.
""", [
    order("sequencing", "Number the events 1 to 4 in the order they happen.",
          ["The letter is delivered to the door.", "Machines read the postcode.", "The letter is posted.", "Vans or planes carry the letters."],
          [4, 2, 1, 3]),
    match("sequencing", "Match each paragraph to its main topic.", ["Paragraph 1", "Paragraph 2", "Paragraph 4"],
          ["Posting and collection", "Sorting by machine", "Delivery"], ["Posting and collection", "Sorting by machine", "Delivery"], lv=2),
    mcq("sequencing", "Which word in paragraph 3 links it to the earlier paragraphs and shows time order?", ["Next", "Planes", "Long", "Loaded"], "Next"),
]))

_add("skim_scan", "upper", S("Ocean Zones", "non-fiction", """
SUNLIGHT ZONE (0–200 m): Most sea life lives here because light reaches it.
TWILIGHT ZONE (200–1,000 m): Only faint light reaches here. Many fish glow.
MIDNIGHT ZONE (below 1,000 m): Total darkness and crushing pressure. Anglerfish use glowing lures.

INDEX: Coral reefs 12–15 | Currents 8 | Jellyfish 20–21 | Octopus 22 | Sharks 18–19
""", [
    short("skim_scan", "Scan the text. At what depth does the Midnight Zone begin?", "Below 1,000 m.", ["1,000", "1000"]),
    mcq("skim_scan", "Which heading would you skim to find out why most sea life lives near the surface?",
        ["Sunlight Zone", "Twilight Zone", "Midnight Zone", "Index"], "Sunlight Zone"),
    mcq("skim_scan", "Use the index. On which pages would you find information on sharks?", ["8", "12–15", "18–19", "22"], "18–19"),
]))

_add("fact_opinion", "upper", S("Museum Review", "non-fiction", """
The Maritime Museum opened in 1998 and has over two hundred ships' models. Frankly, it is the most thrilling museum in the country, and anyone who disagrees is simply wrong. Entry is free for under-twelves. Surely nobody could resist the dazzling blue whale skeleton in the main hall?
""", [
    multi("fact_opinion", "Tick two statements that are facts.",
          ["The museum opened in 1998.", "It is the most thrilling museum in the country.", "Entry is free for under-twelves.", "The skeleton is dazzling."],
          ["The museum opened in 1998.", "Entry is free for under-twelves."]),
    short("fact_opinion", "Write two words or phrases that signal opinion rather than fact.", "For example: Frankly, most thrilling, simply, Surely, dazzling.",
          ["frankly", "thrilling", "simply", "surely", "dazzling"], m=2, lv=2),
    mcq("fact_opinion", "Why is “it is the most thrilling museum” an opinion?",
        ["People can disagree and it cannot be proved", "It contains a date", "It is a question", "It is very short"],
        "People can disagree and it cannot be proved", lv=2),
]))

_add("grammar", "upper", S("The Tunnel", "fiction", """
Although the tunnel was dark, Kai, who was very brave, crept forward. “Is anyone there?” he whispered. The echo answered mockingly. Quickly, he lit a match.
""", [
    short("grammar", "Copy the subordinate clause from the first sentence.", "Although the tunnel was dark", ["although the tunnel was dark"], lv=2),
    match("grammar", "Match each word to its word class.", ["whispered", "mockingly", "brave", "anyone"],
          ["verb", "adverb", "adjective", "pronoun"], ["verb", "adverb", "adjective", "pronoun"]),
    mcq("grammar", "What is the job of “who was very brave”?",
        ["A relative clause giving extra information about Kai", "The main clause", "A question", "An adverb"],
        "A relative clause giving extra information about Kai", lv=3),
]))

_add("sentence_change", "upper", S("Sentence Workshop: Expedition", "fiction", """
The explorers climb the mountain and carry heavy packs. The guide was tired. He kept walking. Suddenly, the ice cracked.
""", [
    short("sentence_change", "Rewrite in the past tense: “The explorers climb the mountain and carry heavy packs.”",
          "The explorers climbed the mountain and carried heavy packs.", ["climbed"]),
    short("sentence_change", "Combine “The guide was tired.” and “He kept walking.” into one sentence using a suitable connective.",
          "Although the guide was tired, he kept walking.", ["although", "even though", "though", "but", "yet", "despite"], lv=2),
    short("sentence_change", "Move the adverb in “Suddenly, the ice cracked.” without changing the meaning.", "The ice suddenly cracked.",
          ["ice suddenly cracked", "ice cracked suddenly"], lv=2),
    mcq("sentence_change", "Which sentence has correct subject-verb agreement?",
        ["The team of explorers was ready.", "The team of explorers were ready is.", "The explorers was ready.", "The explorers is ready."],
        "The team of explorers was ready.", lv=3),
]))

_add("punctuation", "upper", S("At the Harbour", "fiction", """
“Where have you been?” demanded Aunt Rosa. “I've been at the harbour,” replied Marco, “watching the boats come in.” My neighbour, who lives next door, is a pilot.
""", [
    mcq("punctuation", "Which version punctuates direct speech correctly?",
        ["“Where have you been?” demanded Aunt Rosa.", "“Where have you been” demanded Aunt Rosa?",
         "Where have you been? “demanded Aunt Rosa.”", "“Where have you been?” Demanded Aunt Rosa."],
        "“Where have you been?” demanded Aunt Rosa."),
    mcq("punctuation", "Which phrase uses the apostrophe correctly?",
        ["the children's toys", "the childrens' toys", "the childrens toys", "the children's' toys"], "the children's toys", lv=2),
    mcq("punctuation", "Why are commas used around “who lives next door”?",
        ["To add extra information that could be removed", "To separate items in a list", "To show someone is speaking", "To show letters are missing"],
        "To add extra information that could be removed", lv=3),
]))

_add("vocabulary", "upper", S("The Expedition", "fiction", """
The explorer's unwavering determination impressed everyone. Despite the treacherous terrain, she refused to abandon the expedition. Her companions were exhausted, but her optimism never faltered.
""", [
    short("vocabulary", "Write a word or phrase that could replace “treacherous”.", "Dangerous, risky, hazardous …", ["dangerous", "hazard", "risky", "perilous", "unsafe"]),
    mcq("vocabulary", "“Unwavering” means …", ["Steady and not changing", "Shaky", "Secret", "Noisy"], "Steady and not changing"),
    mcq("vocabulary", "What does the prefix “un-” do in “unwavering”?", ["It means “not”", "It means “again”", "It means “before”", "It means “very”"], "It means “not”", lv=2),
    mcq("vocabulary", "The idiom “it's raining cats and dogs” means …", ["It is raining very heavily", "Pets are falling", "It is a sunny day", "A storm is over"],
        "It is raining very heavily", lv=2),
]))

_add("speech_pronoun_modal", "upper", S("The Project", "fiction", """
“I will finish my project tonight,” said Leila. Her teacher replied that she might need more time, but the choice was Leila's. “Mine is nearly done,” added Ben, “though yours looks better.”
""", [
    short("speech_pronoun_modal", "Rewrite Leila's words in reported speech: “I will finish my project tonight,” said Leila.",
          "Leila said that she would finish her project that night.", ["she would"], lv=3),
    mcq("speech_pronoun_modal", "Which word is a possessive pronoun?", ["project", "Mine", "Her", "tonight"], "Mine", lv=2),
    mcq("speech_pronoun_modal", "Which modal verb shows something is only possible, not certain?", ["will", "might", "said", "was"], "might"),
]))

# ---------------------------------------------------------------------------
# Mock exam texts: EXAM_TEXTS[band] -> list of texts. Each text has tagged questions.
# Paper 1 = non-fiction, Paper 2 = fiction (as in the Cambridge Primary tests).
# ---------------------------------------------------------------------------

EXAM_TEXTS = {"lower": [], "upper": []}

EXAM_TEXTS["lower"] += [
    S("The Lighthouse Cat", "fiction", """
Old Mr Finn lived alone in a lighthouse at the end of a rocky cliff. Every evening he climbed the spiral stairs to switch on the great lamp. One stormy night, a thin orange cat appeared at his door, soaked and shivering. “Well, hello,” said Mr Finn, rubbing her wet fur with a towel. “You look as cold as an ice cube!” The cat purred loudly. Mr Finn made her a bowl of warm milk. After that, she followed him up the stairs every night. From the top, her bright green eyes watched the ships sail safely past. Mr Finn no longer felt lonely.
""", [
        short("retrieval", "Where did Mr Finn live?", "In a lighthouse.", ["lighthouse"]),
        mcq("retrieval", "What did Mr Finn give the cat to drink?", ["Water", "Warm milk", "Tea", "Juice"], "Warm milk"),
        short("inference", "How can you tell the cat liked being with Mr Finn? Give one clue.", "She purred loudly / she followed him up the stairs.", ["purr", "follow"]),
        short("language", "Find the simile in the text.", "as cold as an ice cube", ["cold as an ice cube"]),
        short("inference", "Why do you think Mr Finn no longer felt lonely?", "The cat kept him company.", ["cat", "company", "friend", "not alone", "together"], m=2, lv=2),
        order("sequencing", "Number the events 1 to 4 in the order they happened.",
              ["The cat watched the ships.", "A wet cat knocked at the door.", "Mr Finn gave the cat warm milk.", "Mr Finn climbed the stairs to light the lamp."],
              [4, 2, 3, 1]),
        short("vocabulary", "Find a word in the text that means “very wet”.", "soaked", ["soaked"]),
    ]),
    S("The Mystery of the Missing Lunch", "fiction", """
Nina opened her lunchbox and gasped. Her sandwich had vanished! Only a few crumbs and a single muddy paw print were left. “Someone has stolen my lunch!” she cried. Mr Dale, her teacher, bent down to look at the paw print. “It's too big for a mouse,” he said, “and too small for a horse.” Just then, a loud burp came from under the desk. Out crawled Biscuit, the class dog, with ham on his whiskers and a very guilty look on his face. Everyone burst out laughing, even Nina.
""", [
        short("retrieval", "What was left in Nina's lunchbox?", "A few crumbs and a muddy paw print.", ["crumb", "paw"]),
        mcq("inference", "Who took the sandwich?", ["Mr Dale", "Biscuit the dog", "A mouse", "A horse"], "Biscuit the dog"),
        short("inference", "What clue shows Biscuit had eaten the sandwich?", "The burp / ham on his whiskers.", ["burp", "ham", "whisker"], lv=2),
        mcq("language", "Why does the writer use “gasped” instead of “said”?", ["It shows she was shocked", "It is quieter", "It is longer", "It rhymes"], "It shows she was shocked", lv=2),
        mcq("viewpoint", "What is the main purpose of this text?", ["To entertain", "To instruct", "To persuade", "To give facts"], "To entertain"),
        mcq("predict", "Why did everyone laugh?", ["The dog's guilty look was funny", "The teacher told a joke", "Nina dropped the lunchbox", "The paw print was big"],
            "The dog's guilty look was funny", lv=2),
        short("vocabulary", "Find a word that means “disappeared”.", "vanished", ["vanished"]),
    ]),
    S("Why Do We Brush Our Teeth?", "non-fiction", """
Your teeth are strong, but they can be damaged by sugar. When you eat sweet food, tiny germs in your mouth turn the sugar into acid. The acid makes small holes in your teeth. These holes are called cavities.

How to keep your teeth healthy
1. Brush for two minutes, twice a day.
2. Use toothpaste with fluoride.
3. Eat fewer sweets and drink water.
4. Visit the dentist every year.
""", [
        short("retrieval", "What do germs turn sugar into?", "Acid.", ["acid"]),
        multi("retrieval", "Tick two things you should do to keep your teeth healthy.",
              ["Brush for two minutes", "Eat more sweets", "Use toothpaste with fluoride", "Visit the dentist once every five years"],
              ["Brush for two minutes", "Use toothpaste with fluoride"]),
        mcq("viewpoint", "What is the purpose of this text?", ["To inform and give advice", "To tell a story", "To make you laugh", "To sell toothpaste"], "To inform and give advice"),
        short("text_features", "How does the numbered list help the reader?", "It shows the steps clearly and in order.", ["order", "step", "easy", "clear", "find"]),
        mcq("vocabulary", "Which word means “small holes in teeth”?", ["cavities", "acid", "fluoride", "germs"], "cavities"),
        mcq("main_idea", "Which is the best title for this text?", ["Looking After Your Teeth", "A Visit to the Zoo", "Sweet Treats", "How Dentists Learn"], "Looking After Your Teeth"),
        short("inference", "Why is drinking water better for your teeth than eating sweets?", "Water has no sugar, so no acid is made.", ["sugar", "acid", "not sweet"], m=2, lv=2),
    ]),
    S("Pandas", "non-fiction", """
Giant pandas live in the mountains of China. They are famous for their black-and-white fur. A panda spends about twelve hours every day eating bamboo! It has a special bone in its paw that works like a thumb to hold the stems. Baby pandas are tiny and pink, and about as long as a pencil when they are born. Pandas are in danger because the bamboo forests where they live are getting smaller. People all over the world are working to protect them.
""", [
        short("retrieval", "Where do giant pandas live?", "In the mountains of China.", ["mountain", "china"]),
        short("retrieval", "How many hours a day does a panda spend eating?", "About twelve.", ["twelve", "12"]),
        mcq("vocabulary", "What does “protect” mean?", ["Keep safe", "Hunt", "Count", "Feed"], "Keep safe"),
        mcq("main_idea", "What is the last sentence mostly about?", ["People helping pandas", "Baby pandas", "Eating bamboo", "Black-and-white fur"], "People helping pandas"),
        short("retrieval", "Why are pandas in danger?", "Their bamboo forests are getting smaller.", ["bamboo", "forest", "smaller"]),
        short("inference", "Why do you think a panda needs to eat for so many hours?", "Bamboo does not give much energy, so it must eat a lot.", ["energy", "food", "big", "hungry", "bamboo"], m=2, lv=3),
        mcq("language", "Why is there an exclamation mark after “bamboo”?", ["To show surprise at how long pandas eat", "To show a question", "To show someone is speaking", "To end a list"],
            "To show surprise at how long pandas eat", lv=2),
    ]),
]

EXAM_TEXTS["upper"] += [
    S("The Clockmaker's Apprentice", "fiction", """
The shop smelled of oil and old brass. Inside, a hundred clocks ticked out of time with one another, like rain on a tin roof. Tomas, hunched over the workbench, held a watch no bigger than a coin. His hands, usually so steady, were trembling.

“Breathe,” said Mrs Varga, the clockmaker, without looking up from her own work. “Panic is the enemy of precision.”

Tomas swallowed. Yesterday he had dropped a priceless pocket watch, and the memory still stung. He had hidden the pieces in his coat, hoping no one would notice; but Mrs Varga noticed everything. She had said nothing — not yet.

A tiny spring leapt free and pinged across the floor. Tomas froze. Slowly, he lifted his eyes to meet hers. To his surprise, she was smiling.
""", [
        short("retrieval", "What was Tomas holding?", "A watch no bigger than a coin.", ["watch", "coin"]),
        short("retrieval", "Where had Tomas hidden the pieces of the watch he dropped?", "In his coat.", ["coat"]),
        short("language", "What does the simile “like rain on a tin roof” tell you about the sound of the clocks?", "It was constant, noisy and not together.",
              ["noisy", "constant", "many", "patter", "busy", "not together", "out of time", "loud"], m=2, lv=2),
        short("inference", "What does “Mrs Varga noticed everything” suggest about her?", "She is observant and sharp.", ["observ", "clever", "sharp", "aware", "notice"], m=2, lv=2),
        short("inference", "Why do you think Mrs Varga smiles at the end?", "She forgives him / understands that mistakes happen.", ["forgiv", "understand", "kind", "proud", "patient", "not angry", "mistake"], m=2, lv=3),
        mcq("language", "Why is “Tomas froze.” such a short sentence?", ["To build tension at an important moment", "To give information about clocks", "Because it is unimportant", "To slow the story down"],
            "To build tension at an important moment", lv=2),
        mcq("viewpoint", "From whose viewpoint is the story told?", ["A third-person narrator mostly following Tomas", "Tomas in the first person", "Mrs Varga in the first person", "The clocks"],
            "A third-person narrator mostly following Tomas", lv=2),
        short("evidence", "Quote a short phrase that shows Tomas is nervous.", "“hands … were trembling” / “Tomas swallowed” / “Tomas froze”.", ["trembling", "swallowed", "froze", "hunched"], m=2, lv=2),
    ]),
    S("Message in a Bottle", "fiction", """
I found the bottle on the third day after the storm, half-buried in seaweed and glinting like a fallen star. My fingers shook as I prised out the cork. Inside was a scrap of paper, brittle as a dead leaf. The message was written in uneven capitals: HELP. LIGHTHOUSE. DAY SEVEN.

Dad laughed when I showed him. “Some joker,” he said, ruffling my hair. But Dad had not seen the paper up close. The ink was still wet.

I did not argue. Instead, I slipped the paper into my pocket, pulled on my boots, and crept out of the back door. The lighthouse was a mile away across the sand. If I ran, I could be there before the tide came in.
""", [
        short("retrieval", "How long after the storm did the narrator find the bottle?", "Three days.", ["three", "3"]),
        short("retrieval", "What did the message say?", "HELP. LIGHTHOUSE. DAY SEVEN.", ["help", "lighthouse"]),
        short("language", "Find two similes in the first paragraph.", "“glinting like a fallen star” and “brittle as a dead leaf”.", ["fallen star", "dead leaf"], m=2),
        mcq("viewpoint", "From which point of view is the story told?", ["First person", "Third person", "Second person"], "First person"),
        short("inference", "Why do you think the narrator does not argue with Dad?", "The narrator has seen the ink is wet and believes the message is real; they decide to go alone.",
              ["wet", "ink", "believe", "proof", "secret", "alone", "rescue", "real"], m=2, lv=2),
        short("inference", "Why does the writer reveal that “The ink was still wet”?", "It shows the message is recent, so someone may need help now.",
              ["recent", "someone", "danger", "suspense", "real", "urgent", "now"], m=2, lv=3),
        mcq("predict", "What will the narrator probably do next?", ["Run to the lighthouse", "Go back to bed", "Throw the bottle away", "Phone the police"], "Run to the lighthouse"),
        short("language", "How does the last sentence build tension?", "It adds a time limit: the narrator must get there before the tide comes in.", ["tide", "time", "hurry", "run", "race"], m=2, lv=3),
    ]),
    S("The Hidden Cost of Cheap Clothes", "non-fiction", """
Many shoppers buy a top for the price of a sandwich and wear it only a few times. But cheap clothing has to be made quickly, so factories often use harmful dyes that pollute rivers. Meanwhile, workers may be paid very little. Surely we should ask who really pays for a bargain?

Some shoppers are fighting back by swapping clothes with friends or buying from charity shops. Experts say that wearing a garment for just nine months longer can noticeably reduce its environmental impact. It is time we all thought twice before we buy.
""", [
        short("retrieval", "What do some factories use that pollutes rivers?", "Harmful dyes.", ["dye"]),
        multi("retrieval", "Tick two ways shoppers are fighting back.",
              ["Swapping clothes with friends", "Buying from charity shops", "Wearing no clothes", "Making their own dyes"],
              ["Swapping clothes with friends", "Buying from charity shops"]),
        short("viewpoint", "Give one example of how the writer tries to persuade the reader.", "The rhetorical question “Surely we should ask…?” / “It is time we all thought twice”.",
              ["surely", "rhetorical", "question", "bargain", "time we all"], m=2, lv=2),
        mcq("fact_opinion", "Which sentence is an opinion?", ["Surely we should ask who really pays for a bargain?", "Factories often use harmful dyes.", "Workers may be paid very little.", "Some shoppers swap clothes."],
            "Surely we should ask who really pays for a bargain?", lv=2),
        mcq("main_idea", "Which sentence best sums up the text?", ["Cheap clothes harm people and the environment, so we should buy more carefully.", "Everyone should wear only charity-shop clothes.",
            "Dyes are dangerous to touch.", "Clothes cost too much."], "Cheap clothes harm people and the environment, so we should buy more carefully.", lv=2),
        short("vocabulary", "Write a word that means the same as “pollute”.", "Contaminate, poison, dirty, harm.", ["contaminat", "poison", "dirty", "spoil", "harm"]),
        mcq("viewpoint", "What is the purpose of this text?", ["To persuade", "To entertain", "To instruct", "To tell a story"], "To persuade"),
    ]),
    S("How Do Volcanoes Erupt?", "non-fiction", """
Under the surface
Deep underground, rock is so hot that it melts into a thick liquid called magma. Because magma is lighter than the solid rock around it, it slowly rises and collects in a chamber beneath the volcano.

Pressure builds
Gases dissolved in the magma try to escape, just as bubbles fizz when a fizzy-drink bottle is opened. When the pressure becomes too great, the magma bursts out through a crack, or vent, at the top of the volcano.

After the eruption
Once magma reaches the surface it is called lava. As it cools, lava hardens into new rock, so volcanoes can slowly build up into mountains. Although eruptions can be dangerous, volcanic soil is rich in minerals, which is why farmers often grow crops nearby.
""", [
        short("retrieval", "What is melted rock under the ground called?", "Magma.", ["magma"]),
        short("retrieval", "What is magma called once it reaches the surface?", "Lava.", ["lava"]),
        short("inference", "Why do you think farmers grow crops near volcanoes, even though they are dangerous?", "Volcanic soil is rich in minerals, so crops grow well.",
              ["soil", "mineral", "rich", "fertile", "grow"], m=2, lv=2),
        match("sequencing", "Match each heading to the main idea of its paragraph.", ["Under the surface", "Pressure builds", "After the eruption"],
              ["Rock melts and rises", "Gas forces magma out", "Lava cools into new rock and soil"],
              ["Rock melts and rises", "Gas forces magma out", "Lava cools into new rock and soil"], lv=2),
        mcq("language", "Why does the writer compare the volcano to a fizzy-drink bottle?", ["To help the reader picture gas pressure escaping", "To show volcanoes are tasty", "To make the text funny", "To describe the colour of lava"],
            "To help the reader picture gas pressure escaping", lv=2),
        short("vocabulary", "Which word in the text means “a crack where magma escapes”?", "Vent.", ["vent"]),
        short("skim_scan", "Under which heading would you look to find out what happens when lava cools?", "After the eruption.", ["after"]),
    ]),
]

# ---------------------------------------------------------------------------
# Finalise: give every question a stable id
# ---------------------------------------------------------------------------


def _finalise():
    for (skill, band), sets in PRACTICE.items():
        for i, s in enumerate(sets):
            s["id"] = f"p-{skill}-{band}-{i}"
            s["band"] = band
            for j, q in enumerate(s["qs"]):
                q["id"] = f"{s['id']}-q{j}"
    for band, sets in EXAM_TEXTS.items():
        for i, s in enumerate(sets):
            s["id"] = f"x-{band}-{i}"
            s["band"] = band
            for j, q in enumerate(s["qs"]):
                q["id"] = f"{s['id']}-q{j}"


_finalise()
