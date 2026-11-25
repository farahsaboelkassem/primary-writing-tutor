"""Starter word and phrase lists for the Vocabulary Vault.

These work straight away, with no database. Once you import the same lists into Supabase
(see vault_setup.sql) the app uses the Supabase copy, which you can edit and extend.

Each entry is: (genre, type, level, text, meaning, example sentence)
  genre   a genre name from the Writing Dojo (or "General" for words useful in any writing)
  type    "word" or "phrase"
  level   "lower" (Grades 1-3), "upper" (Grades 4-6) or "both"
  The example sentence must contain the word or phrase exactly, so quizzes can hide it.
"""

W, P = "word", "phrase"

STARTER = [
    # ---------------- General ----------------
    ("General", W, "both", "enormous", "extremely big", "An enormous oak tree stood in the middle of the field."),
    ("General", W, "lower", "whispered", "said something very quietly", "She whispered the secret to her best friend."),
    ("General", W, "both", "gleaming", "shining brightly", "The gleaming trophy sat on the top shelf."),
    ("General", W, "upper", "hesitated", "paused because you were not sure", "He hesitated at the door before knocking."),
    ("General", W, "both", "determined", "firmly decided to do something", "She was determined to finish the race."),
    ("General", W, "upper", "reluctantly", "in a way that shows you do not want to", "He reluctantly handed back the toy."),
    ("General", P, "both", "All of a sudden,", "begins something unexpected", "All of a sudden, the lights went out."),
    ("General", P, "upper", "Without a second thought,", "acting quickly without stopping to think", "Without a second thought, she dived in to help."),
    ("General", P, "both", "As quick as a flash,", "very fast", "As quick as a flash, the cat leapt onto the wall."),
    ("General", P, "lower", "In the end,", "shows how something finished", "In the end, we found the lost kitten."),

    # ---------------- Adventure ----------------
    ("Adventure", W, "upper", "treacherous", "dangerous and not safe", "The treacherous path wound along the edge of the cliff."),
    ("Adventure", W, "upper", "expedition", "a long journey with a purpose", "The expedition set off at dawn to find the hidden cave."),
    ("Adventure", W, "both", "scrambled", "climbed or moved quickly using hands and feet", "We scrambled up the rocky slope."),
    ("Adventure", W, "both", "daring", "brave and willing to take risks", "The daring explorer crossed the rope bridge."),
    ("Adventure", W, "lower", "startled", "suddenly surprised or frightened", "A rustle in the bushes startled the hikers."),
    ("Adventure", W, "upper", "perilous", "full of danger", "They faced a perilous journey across the frozen lake."),
    ("Adventure", P, "both", "Heart pounding,", "shows fear or excitement", "Heart pounding, Mia stepped onto the narrow bridge."),
    ("Adventure", P, "upper", "Just in the nick of time,", "only just early enough", "Just in the nick of time, they reached the boat."),
    ("Adventure", P, "upper", "Against all odds,", "even though success seemed unlikely", "Against all odds, the team made it to the summit."),
    ("Adventure", P, "lower", "Before long,", "after a short time", "Before long, the sun began to set."),

    # ---------------- Fantasy ----------------
    ("Fantasy", W, "both", "enchanted", "under a magic spell", "They stepped into the enchanted forest."),
    ("Fantasy", W, "both", "shimmering", "shining with a soft, flickering light", "A shimmering doorway appeared in the air."),
    ("Fantasy", W, "upper", "mythical", "from myths and legends and not real", "A mythical dragon guarded the golden treasure."),
    ("Fantasy", W, "upper", "sorcerer", "a person who uses magic", "The sorcerer waved his staff and the door opened."),
    ("Fantasy", W, "lower", "wand", "a thin stick used to cast spells", "She waved her wand and the broom began to sweep."),
    ("Fantasy", W, "both", "mysterious", "strange and hard to explain", "A mysterious light glowed deep in the cave."),
    ("Fantasy", P, "lower", "Once upon a time,", "a classic way to begin a fairy tale", "Once upon a time, a brave girl lived in a tall tower."),
    ("Fantasy", P, "both", "Deep in the heart of the forest,", "sets a scene in a hidden place", "Deep in the heart of the forest, a tiny door glowed."),
    ("Fantasy", P, "both", "With a flick of her wand,", "shows magic happening quickly", "With a flick of her wand, the teapot began to dance."),
    ("Fantasy", P, "upper", "Little did they know,", "hints that something unexpected is coming", "Little did they know, the dragon was watching."),

    # ---------------- Realistic Fiction ----------------
    ("Realistic Fiction", W, "upper", "anxious", "worried or nervous", "Sam felt anxious before his first day at the new school."),
    ("Realistic Fiction", W, "both", "embarrassed", "feeling awkward in front of other people", "She felt embarrassed when she dropped her tray."),
    ("Realistic Fiction", W, "both", "relieved", "happy because a worry has gone", "I was relieved when I found my lost bag."),
    ("Realistic Fiction", W, "lower", "grumbled", "complained in a low, unhappy voice", "Dad grumbled about the heavy traffic."),
    ("Realistic Fiction", W, "both", "nervously", "in a worried or shaky way", "He nervously tapped his pencil on the desk."),
    ("Realistic Fiction", W, "upper", "overjoyed", "extremely happy", "She was overjoyed when she saw her grandmother."),
    ("Realistic Fiction", P, "both", "Her stomach flipped,", "shows nerves or worry", "Her stomach flipped as the teacher called her name."),
    ("Realistic Fiction", P, "upper", "A lump rose in his throat,", "shows he felt like crying", "A lump rose in his throat as he said goodbye."),
    ("Realistic Fiction", P, "lower", "At that moment,", "at exactly that time", "At that moment, the bell rang."),
    ("Realistic Fiction", P, "both", "To her surprise,", "shows something unexpected happened", "To her surprise, the box was empty."),

    # ---------------- Science Fiction ----------------
    ("Science Fiction", W, "both", "futuristic", "like something from the future", "The futuristic city had flying cars and glass towers."),
    ("Science Fiction", W, "lower", "galaxy", "a huge group of stars", "Their spaceship travelled across the galaxy."),
    ("Science Fiction", W, "upper", "android", "a robot that looks like a person", "The android blinked and smiled."),
    ("Science Fiction", W, "both", "advanced", "modern and highly developed", "The visitors had advanced technology."),
    ("Science Fiction", W, "both", "mission", "an important task", "Their mission was to find a new planet."),
    ("Science Fiction", W, "upper", "extraterrestrial", "from another planet", "The extraterrestrial visitor stepped out of the ship."),
    ("Science Fiction", P, "both", "In the year 3000,", "sets the story in the future", "In the year 3000, people lived on Mars."),
    ("Science Fiction", P, "both", "Warning lights flashed,", "shows danger on a spaceship", "Warning lights flashed as the ship shook."),
    ("Science Fiction", P, "upper", "Light years away,", "extremely far away", "Light years away, a new planet waited."),
    ("Science Fiction", P, "both", "In the blink of an eye,", "very quickly", "In the blink of an eye, the robot vanished."),

    # ---------------- Describing a Setting ----------------
    ("Describing a Setting", W, "both", "towering", "very tall", "Towering pine trees surrounded the cabin."),
    ("Describing a Setting", W, "upper", "desolate", "empty and lonely", "The desolate beach was silent and grey."),
    ("Describing a Setting", W, "both", "bustling", "full of busy activity", "The bustling market was full of shouting sellers."),
    ("Describing a Setting", W, "upper", "murky", "dark, cloudy and not clear", "The murky pond hid strange shapes beneath the surface."),
    ("Describing a Setting", W, "upper", "tranquil", "calm and peaceful", "The tranquil lake was perfectly still."),
    ("Describing a Setting", W, "lower", "damp", "slightly wet", "The damp cave smelled of earth."),
    ("Describing a Setting", P, "upper", "The air was thick with", "describes a strong smell or feeling in the air", "The air was thick with the smell of fresh bread."),
    ("Describing a Setting", P, "both", "As far as the eye could see,", "shows a big, wide place", "Fields stretched out as far as the eye could see."),
    ("Describing a Setting", P, "upper", "Nestled between the hills,", "tucked safely into a small space", "Nestled between the hills, the village slept."),
    ("Describing a Setting", P, "lower", "In the distance,", "far away", "In the distance, a church bell rang."),

    # ---------------- Describing a Character ----------------
    ("Describing a Character", W, "upper", "courageous", "very brave when facing something scary", "The courageous firefighter ran into the smoke."),
    ("Describing a Character", W, "both", "stubborn", "refusing to change your mind", "The stubborn donkey would not move."),
    ("Describing a Character", W, "both", "generous", "happy to give and share", "The generous girl shared her lunch."),
    ("Describing a Character", W, "upper", "mischievous", "playful in a naughty way", "The mischievous puppy hid my socks."),
    ("Describing a Character", W, "lower", "timid", "shy and easily frightened", "The timid rabbit hid behind a rock."),
    ("Describing a Character", W, "upper", "arrogant", "too proud of yourself", "The arrogant knight boasted about his sword."),
    ("Describing a Character", P, "both", "With a twinkle in his eye,", "shows a playful or cheeky character", "With a twinkle in his eye, Grandad hid the biscuits."),
    ("Describing a Character", P, "both", "Her eyes sparkled with excitement,", "shows how happy and eager someone is", "Her eyes sparkled with excitement as she opened the gift."),
    ("Describing a Character", P, "upper", "had a heart of gold", "was very kind", "The old baker had a heart of gold."),
    ("Describing a Character", P, "upper", "was known for", "tells us what a person is famous for", "Gran was known for her warm hugs."),

    # ---------------- Writing Dialogue ----------------
    ("Writing Dialogue", W, "both", "exclaimed", "said something suddenly and loudly", "“Look at that!” she exclaimed."),
    ("Writing Dialogue", W, "upper", "murmured", "said something quietly and softly", "“I’m tired,” he murmured."),
    ("Writing Dialogue", W, "upper", "demanded", "asked in a strong way, expecting an answer", "“Where is my hat?” demanded Grandad."),
    ("Writing Dialogue", W, "lower", "replied", "answered", "“Yes, please,” replied Ella."),
    ("Writing Dialogue", W, "upper", "stammered", "spoke with pauses because of nerves", "“I… I didn’t mean to,” he stammered."),
    ("Writing Dialogue", W, "both", "chuckled", "laughed quietly", "“That’s funny,” chuckled Dad."),
    ("Writing Dialogue", P, "lower", "said with a smile", "shows how someone spoke happily", "“Thank you,” she said with a smile."),
    ("Writing Dialogue", P, "both", "whispered urgently", "spoke quietly but in a hurry", "“Run!” he whispered urgently."),
    ("Writing Dialogue", P, "both", "asked curiously", "asked because you want to know more", "“What is inside?” she asked curiously."),
    ("Writing Dialogue", P, "upper", "replied in a shaky voice", "answered while feeling nervous or scared", "“I think so,” he replied in a shaky voice."),

    # ---------------- News Report ----------------
    ("News Report", W, "both", "witnesses", "people who saw something happen", "Witnesses said the car stopped suddenly."),
    ("News Report", W, "upper", "authorities", "the officials who are in charge", "The authorities closed the road."),
    ("News Report", W, "both", "confirmed", "said that something is true", "The school confirmed the trip was cancelled."),
    ("News Report", W, "upper", "incident", "an event, often something unexpected", "Police are investigating the incident."),
    ("News Report", W, "upper", "investigation", "a careful search for the facts", "An investigation is under way."),
    ("News Report", W, "lower", "reported", "told people about something", "The radio reported heavy rain."),
    ("News Report", P, "both", "According to witnesses,", "shows where the information came from", "According to witnesses, the storm began at noon."),
    ("News Report", P, "lower", "Earlier today,", "gives the time something happened", "Earlier today, the town held a parade."),
    ("News Report", P, "upper", "Officials have confirmed that", "shows the facts have been checked", "Officials have confirmed that the bridge is safe."),
    ("News Report", P, "upper", "It is understood that", "shows something is believed but not fully confirmed", "It is understood that the match will go ahead."),

    # ---------------- Persuasive Writing ----------------
    ("Persuasive Writing", W, "both", "essential", "absolutely needed", "Healthy food is essential for growing children."),
    ("Persuasive Writing", W, "both", "convinced", "completely sure", "I am convinced that we need a new playground."),
    ("Persuasive Writing", W, "both", "benefit", "a good result or advantage", "A big benefit of reading is a better vocabulary."),
    ("Persuasive Writing", W, "upper", "urgent", "needing action right now", "It is urgent that we protect our school garden."),
    ("Persuasive Writing", W, "lower", "imagine", "to picture something in your mind", "Imagine a school with no litter at all."),
    ("Persuasive Writing", W, "upper", "undoubtedly", "without any doubt", "Recycling will undoubtedly help our planet."),
    ("Persuasive Writing", P, "both", "Surely you agree that", "invites the reader to agree with you", "Surely you agree that our park deserves better."),
    ("Persuasive Writing", P, "upper", "Without a doubt,", "shows you are completely certain", "Without a doubt, this is the best idea."),
    ("Persuasive Writing", P, "both", "For these reasons,", "begins a summing-up", "For these reasons, we must act now."),
    ("Persuasive Writing", P, "upper", "It is high time that", "says something should have happened already", "It is high time that we cleaned up the beach."),
    ("Persuasive Writing", P, "lower", "Think about it:", "asks the reader to stop and think", "Think about it: how would you feel?"),

    # ---------------- Discussion (Balanced Argument) ----------------
    ("Discussion (Balanced Argument)", W, "both", "advantage", "a good point in favour of something", "One advantage of homework is extra practice."),
    ("Discussion (Balanced Argument)", W, "both", "disadvantage", "a bad point against something", "A disadvantage is that it takes a lot of time."),
    ("Discussion (Balanced Argument)", W, "lower", "opinion", "what you think or feel", "In my opinion, school uniforms are useful."),
    ("Discussion (Balanced Argument)", W, "upper", "consequence", "a result of something", "A consequence of too little sleep can be tiredness."),
    ("Discussion (Balanced Argument)", W, "upper", "controversial", "something people strongly disagree about", "Banning phones is a controversial idea."),
    ("Discussion (Balanced Argument)", W, "upper", "evidence", "facts that show something is true", "There is evidence that exercise helps learning."),
    ("Discussion (Balanced Argument)", P, "upper", "On the one hand,", "introduces the first point of view", "On the one hand, homework builds good habits."),
    ("Discussion (Balanced Argument)", P, "upper", "On the other hand,", "introduces the opposite point of view", "On the other hand, it can be tiring."),
    ("Discussion (Balanced Argument)", P, "both", "However,", "introduces a point that goes against the last one", "However, some people disagree."),
    ("Discussion (Balanced Argument)", P, "both", "In conclusion,", "begins the ending of your writing", "In conclusion, both sides have good points."),
    ("Discussion (Balanced Argument)", P, "lower", "Some people believe that", "introduces what one group thinks", "Some people believe that homework is helpful."),

    # ---------------- Instructional Writing ----------------
    ("Instructional Writing", W, "both", "ingredients", "the foods you use to make something", "Gather all the ingredients before you start."),
    ("Instructional Writing", W, "both", "equipment", "the things you need to do a job", "You will need some equipment, such as scissors."),
    ("Instructional Writing", W, "lower", "carefully", "with care", "Carefully pour the milk into the bowl."),
    ("Instructional Writing", W, "lower", "repeat", "do again", "Repeat these steps three times."),
    ("Instructional Writing", W, "upper", "ensure", "make certain", "Ensure the glue is dry before moving on."),
    ("Instructional Writing", W, "upper", "assemble", "put the parts together", "Assemble the model by joining the two halves."),
    ("Instructional Writing", P, "lower", "First of all,", "starts the first step", "First of all, wash your hands."),
    ("Instructional Writing", P, "lower", "Next,", "shows the following step", "Next, add the flour to the bowl."),
    ("Instructional Writing", P, "both", "Make sure that", "reminds the reader to check something", "Make sure that the oven is switched off."),
    ("Instructional Writing", P, "upper", "Once you have finished,", "shows what to do after a step is complete", "Once you have finished, clear away your equipment."),
    ("Instructional Writing", P, "lower", "Finally,", "shows the last step", "Finally, enjoy your sandwich."),

    # ---------------- Non-chronological Report ----------------
    ("Non-chronological Report", W, "both", "habitat", "the natural home of a plant or animal", "The polar bear’s habitat is cold and icy."),
    ("Non-chronological Report", W, "upper", "species", "a type of living thing", "There are many species of butterfly."),
    ("Non-chronological Report", W, "upper", "nocturnal", "active at night", "Owls are nocturnal."),
    ("Non-chronological Report", W, "upper", "predators", "animals that hunt other animals", "Predators such as lions hunt in groups."),
    ("Non-chronological Report", W, "both", "diet", "what an animal usually eats", "A koala’s diet is mostly eucalyptus leaves."),
    ("Non-chronological Report", W, "upper", "endangered", "at risk of dying out", "The giant panda is an endangered animal."),
    ("Non-chronological Report", P, "both", "is known for", "tells us what something is famous for", "The cheetah is known for its speed."),
    ("Non-chronological Report", P, "lower", "can be found in", "tells us where something lives", "Lions can be found in Africa."),
    ("Non-chronological Report", P, "both", "One interesting fact is that", "introduces a fact that might surprise the reader", "One interesting fact is that octopuses have three hearts."),
    ("Non-chronological Report", P, "upper", "In addition,", "adds another piece of information", "In addition, elephants use their trunks to drink."),
]


def slug(text):
    """A safe short name for a genre, used inside item codes (e.g. 'news-report')."""
    import re
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


def starter_items():
    """The starter lists as item dictionaries, with stable codes like 'adventure-w01' or 'general-p02'."""
    counters, items = {}, []
    for genre, item_type, level, text, meaning, example in STARTER:
        key = (genre, item_type)
        counters[key] = counters.get(key, 0) + 1
        code = f"{slug(genre)}-{'w' if item_type == 'word' else 'p'}{counters[key]:02d}"
        items.append({"code": code, "type": item_type, "genre": genre, "level": level,
                      "text": text, "meaning": meaning, "example": example})
    return items
