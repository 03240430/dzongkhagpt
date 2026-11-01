import csv
import re
from functools import lru_cache
from pathlib import Path

GLOSSARY_PATH = Path(__file__).resolve().parent.parent / "data" / "glossary.csv"


def normalize(text: str) -> str:
    """Lowercase, trim, collapse spaces, drop trailing punctuation."""
    text = re.sub(r"\s+", " ", text.strip().lower())
    return text.rstrip(".!?,།་ ").strip()


@lru_cache(maxsize=1)
def load_glossary():
    """Returns (english->dzongkha, dzongkha->english). Restart the app after editing the CSV."""
    en_to_dz, dz_to_en = {}, {}
    if not GLOSSARY_PATH.exists():
        return en_to_dz, dz_to_en

    with open(GLOSSARY_PATH, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    for row in rows[1:]:                       # skip the header row
        if len(row) < 2:
            continue
        english, dzongkha = row[0].strip(), row[1].strip()
        if not english or not dzongkha or english.startswith("#"):
            continue
        en_to_dz[normalize(english)] = dzongkha
        dz_to_en[normalize(dzongkha)] = english
    return en_to_dz, dz_to_en


def lookup(sentence: str, src: str):
    """Exact whole-sentence match. Returns the glossary translation or None."""
    en_to_dz, dz_to_en = load_glossary()
    key = normalize(sentence)
    if src == "eng_Latn":
        return en_to_dz.get(key)
    return dz_to_en.get(key)