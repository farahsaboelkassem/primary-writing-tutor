"""Write the starter files for the Vocabulary Vault lists.

Run it from the project folder:   python export_vault_seed.py

It creates two files:
  vault_seed.csv              the starter words and phrases, ready to import into Supabase
  vault_genre_reference.csv   the exact genre names to use in your own rows

Import vault_seed.csv into the vault_import table (see vault_setup.sql).
"""
import csv

import writing_tutor
from vault_starter import starter_items

COLUMNS = ["item_code", "item_type", "genre", "level", "term", "meaning", "example_sentence", "active"]


def main():
    items = starter_items()
    with open("vault_seed.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        for i in items:
            writer.writerow([i["code"], i["type"], i["genre"], i["level"], i["text"], i["meaning"], i["example"], "TRUE"])
    have = {}
    for i in items:
        have.setdefault(i["genre"], {"word": 0, "phrase": 0})[i["type"]] += 1
    with open("vault_genre_reference.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["genre", "world", "starter_words", "starter_phrases"])
        writer.writerow(["General", "Any genre", have.get("General", {}).get("word", 0), have.get("General", {}).get("phrase", 0)])
        for world, groups in (("Fiction", writing_tutor.FICTION_STYLES), ("Non-Fiction", writing_tutor.NON_FICTION_SUBGENRES)):
            for names in groups.values():
                for g in names:
                    writer.writerow([g, world, have.get(g, {}).get("word", 0), have.get(g, {}).get("phrase", 0)])
    print(f"vault_seed.csv: {len(items)} items")
    print("vault_genre_reference.csv: written")


if __name__ == "__main__":
    main()
