import re
import time

from . import config, llm
from .translator import translate, contains_dzongkha, EN, DZ

SYSTEM = (
    "You are a careful summarizer. Always reply in English only, using the Latin alphabet. "
    "Use ONLY information that is in the text you are given. Do not add facts, opinions or advice. "
    "Keep names, numbers and dates exactly as written. If something is unclear, leave it out. "
    "Your summary will be machine-translated into Dzongkha, so use short, simple sentences, "
    "and do not use markdown, bullets, numbering, tables, emojis or special symbols."
)

LENGTHS = {
    "short": ("Write a summary of 2 to 3 sentences.", 150),
    "medium": ("Write one paragraph of 5 to 7 sentences.", 300),
    "detailed": (
        "Write 6 to 10 key points. Put each point on its own line as one complete sentence. "
        "Do not use bullets, numbers or symbols.",
        500,
    ),
}

CHUNK_PROMPT = "Write the key facts of this part of a longer text in 3 to 5 short sentences.\n\nText:\n"
MERGE_PROMPT = "Combine these notes into 4 to 6 short sentences. Use only the notes.\n\nNotes:\n"
NOTES_LIMIT_WORDS = 700


def count_scripts(text: str):
    tibetan = sum(1 for c in text if "\u0F00" <= c <= "\u0FFF")
    latin = sum(1 for c in text if c.isascii() and c.isalpha())
    return tibetan, latin


def detect_language(text: str) -> str:
    """Rough guess: 'en', 'dz', 'mixed' or 'unknown'."""
    tibetan, latin = count_scripts(text)
    if tibetan + latin == 0:
        return "unknown"
    share = tibetan / (tibetan + latin)
    if share > 0.8:
        return "dz"
    if share < 0.05:
        return "en"
    return "mixed"


def chunk_text(text: str, max_words: int) -> list[str]:
    """Split English text into parts of at most max_words, at sentence ends."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]
    chunks, cur, n = [], [], 0
    for s in sentences:
        words = s.split()
        if len(words) > max_words:
            if cur:
                chunks.append(" ".join(cur))
                cur, n = [], 0
            for i in range(0, len(words), max_words):
                chunks.append(" ".join(words[i:i + max_words]))
            continue
        if cur and n + len(words) > max_words:
            chunks.append(" ".join(cur))
            cur, n = [], 0
        cur.append(s)
        n += len(words)
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def to_english(text: str, on_progress=None) -> str:
    """Translate only the lines that contain Dzongkha; keep English lines as they are."""
    lines = text.splitlines()
    idx = [i for i, l in enumerate(lines) if contains_dzongkha(l)]
    if not idx:
        return text
    source = [lines[i].strip() for i in idx]
    out = translate("\n".join(source), DZ, EN, on_progress=on_progress).split("\n")
    if len(out) != len(source):                       # safety: translate line by line
        out = [translate(l, DZ, EN) for l in source]
    for i, t in zip(idx, out):
        lines[i] = t
    return "\n".join(l for l in lines if l.strip())


def tidy_summary(text: str) -> str:
    """Remove markdown marks and list markers the AI may add anyway."""
    lines = []
    for line in text.replace("*", "").splitlines():
        line = re.sub(r"^\s*(?:[-\u2022#]+|\d+[.)])\s+", "", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def unsupported_numbers(source: str, summary: str) -> list[str]:
    """Numbers that appear in the summary but not in the source text."""
    def numbers(t):
        return {n.replace(",", "") for n in re.findall(r"\d+(?:[.,]\d+)*", t)}
    return sorted(numbers(summary) - numbers(source))


def _ai(prompt: str, max_tokens: int) -> str:
    return llm.generate_english(SYSTEM, [{"role": "user", "content": prompt}], max_tokens=max_tokens)


def _summarize_english(text: str, length: str, progress):
    """Returns (summary_en, number_of_parts). progress(fraction 0..1, message)."""
    instruction, max_tokens = LENGTHS[length]
    chunks = chunk_text(text, config.CHUNK_WORDS)
    if not chunks:
        raise ValueError("There is no readable text to summarize.")

    if len(chunks) == 1:
        progress(0.5, "The AI is writing the summary...")
        return tidy_summary(_ai(f"{instruction}\n\nText:\n{chunks[0]}", max_tokens)), 1

    notes = []
    for i, chunk in enumerate(chunks, 1):
        progress(i / (len(chunks) + 1), f"Reading part {i} of {len(chunks)}...")
        notes.append(_ai(CHUNK_PROMPT + chunk, 220))

    rounds = 0
    while len(notes) > 1 and sum(len(n.split()) for n in notes) > NOTES_LIMIT_WORDS and rounds < 4:
        rounds += 1
        groups, cur, n = [], [], 0
        for note in notes:
            w = len(note.split())
            if cur and n + w > NOTES_LIMIT_WORDS // 2:
                groups.append(cur)
                cur, n = [], 0
            cur.append(note)
            n += w
        if cur:
            groups.append(cur)
        if len(groups) == len(notes):
            break
        progress(0.9, "Combining notes...")
        notes = [_ai(MERGE_PROMPT + "\n".join(g), 220) if len(g) > 1 else g[0] for g in groups]

    progress(0.95, "The AI is writing the final summary...")
    final = _ai(
        f"These are notes from consecutive parts of one document. {instruction} Use only the notes.\n\nNotes:\n"
        + "\n".join(notes),
        max_tokens,
    )
    return tidy_summary(final), len(chunks)


def summarize(text: str, length: str = "medium", out_lang: str = "dz", on_progress=None) -> dict:
    """Summarize English or Dzongkha text.
    Returns {"summary", "summary_en", "source_lang", "chunks", "warnings", "seconds"}.
    on_progress(fraction 0..1, message) is called as work goes on."""
    started = time.time()
    progress = on_progress or (lambda frac, msg: None)
    warnings = []

    text = text.strip()
    if len(text) < 40:
        raise ValueError("The text is too short to summarize. Please add more text.")

    if len(text) > config.MAX_INPUT_CHARS:
        cut = text[:config.MAX_INPUT_CHARS]
        end = max(cut.rfind("."), cut.rfind("།"), cut.rfind("\n"))
        if end > config.MAX_INPUT_CHARS * 0.5:
            cut = cut[:end + 1]
        text = cut
        warnings.append(
            f"The text is long, so only the first {len(text):,} characters were summarized. "
            "You can raise MAX_INPUT_CHARS in the .env file if your computer is fast enough."
        )

    source_lang = detect_language(text)
    has_dzongkha = contains_dzongkha(text)

    if has_dzongkha:
        progress(0.02, "Translating the Dzongkha text to English...")
        english = to_english(
            text,
            on_progress=lambda d, n: progress(0.02 + 0.33 * d / n, f"Translating to English... ({d}/{n} sentences)"),
        )
        warnings.append(
            "Your text contained Dzongkha, which was first translated to English by a machine. "
            "Some details may be lost or changed, so please check important facts."
        )
    else:
        english = text

    start = 0.38 if has_dzongkha else 0.05
    end = 0.85 if out_lang == "dz" else 1.0
    summary_en, chunks = _summarize_english(
        english, length, lambda f, m: progress(start + (end - start) * f, m)
    )
    if not summary_en.strip():
        raise ValueError("The AI did not return a summary. Please try again.")

    missing = unsupported_numbers(english, summary_en)
    if missing:
        warnings.append(
            "These numbers are in the summary but were not found in the text: "
            + ", ".join(missing) + ". Please check them."
        )

    if out_lang == "dz":
        progress(0.86, "Translating the summary to Dzongkha...")
        summary = translate(
            summary_en, EN, DZ,
            on_progress=lambda d, n: progress(0.86 + 0.13 * d / n, f"Translating to Dzongkha... ({d}/{n})"),
        )
    else:
        summary = summary_en

    progress(1.0, "Done")
    return {
        "summary": summary,
        "summary_en": summary_en,
        "source_lang": source_lang,
        "chunks": chunks,
        "warnings": warnings,
        "seconds": time.time() - started,
    }
