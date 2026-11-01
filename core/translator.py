import re
from functools import lru_cache
from . import config
from .glossary import lookup

EN = "eng_Latn"
DZ = "dzo_Tibt"

_CACHE: dict = {}      # (sentence, src, tgt) -> translation


def contains_dzongkha(text: str) -> bool:
    """True if the text has any Tibetan-script characters."""
    return any("\u0F00" <= ch <= "\u0FFF" for ch in text)


def clean_dzongkha(text: str) -> str:
    """Make sure a Dzongkha sentence ends with the proper sentence mark །"""
    text = re.sub(r"\s+།", "།", text.strip())    # no space before །
    text = re.sub(r"[.?!]+$", "།", text)           # swap Latin end marks
    if text and not text.endswith("།"):
        text += "།"
    return text


@lru_cache(maxsize=1)
def _load():
    """Loads the fast translator once."""
    import ctranslate2
    from transformers import AutoTokenizer

    if not config.NLLB_CT2_DIR.exists():
        raise RuntimeError(
            f"Converted model not found at {config.NLLB_CT2_DIR}. "
            "Run the ct2-transformers-converter command from the instructions."
        )
    translator = ctranslate2.Translator(
        str(config.NLLB_CT2_DIR),
        device="cpu",
        compute_type="int8",
        inter_threads=1,
        intra_threads=config.CPU_THREADS,
    )
    tokenizer = AutoTokenizer.from_pretrained(config.NLLB_MODEL)
    return translator, tokenizer


def _split_sentences(line: str, lang: str) -> list[str]:
    if lang == DZ:
        parts = re.split(r"(?<=།)\s*", line)
    else:
        parts = re.split(r"(?<=[.!?])\s+", line)
    return [p.strip() for p in parts if p.strip()]


def _run_model(sentences: list[str], src: str, tgt: str) -> list[str]:
    """Translate many sentences in one batch."""
    translator, tokenizer = _load()
    tokenizer.src_lang = src
    sources = [
        tokenizer.convert_ids_to_tokens(
            tokenizer.encode(s, truncation=True, max_length=200)
        )
        for s in sentences
    ]
    longest = max(len(s) for s in sources)
    results = translator.translate_batch(
        sources,
        target_prefix=[[tgt]] * len(sources),
        beam_size=config.CT2_BEAM,
        max_decoding_length=min(300, longest * 2 + 20),
        max_batch_size=16,
    )
    outputs = []
    for r in results:
        tokens = r.hypotheses[0][1:]          # drop the language tag
        ids = tokenizer.convert_tokens_to_ids(tokens)
        outputs.append(tokenizer.decode(ids, skip_special_tokens=True).strip())
    return outputs


def _translate_many(sentences: list[str], src: str, tgt: str) -> list[str]:
    """Glossary first, then cache, then the model (one batch for everything left)."""
    results = [None] * len(sentences)
    todo: dict[str, list[int]] = {}

    for i, s in enumerate(sentences):
        key = (s, src, tgt)
        if key in _CACHE:
            results[i] = _CACHE[key]
            continue
        override = lookup(s, src)                  # your verified glossary wins
        if override:
            _CACHE[key] = override
            results[i] = override
            continue
        todo.setdefault(s, []).append(i)

    if todo:
        unique = list(todo)
        for s, out in zip(unique, _run_model(unique, src, tgt)):
            if tgt == DZ:
                out = clean_dzongkha(out)
            _CACHE[(s, src, tgt)] = out
            for i in todo[s]:
                results[i] = out
    return results


def translate(text: str, src: str, tgt: str) -> str:
    """Translate text, keeping line breaks."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    per_line = [_split_sentences(l, src) for l in lines]
    flat = [s for sents in per_line for s in sents]
    translated = _translate_many(flat, src, tgt)

    out, k = [], 0
    for sents in per_line:
        out.append(" ".join(translated[k:k + len(sents)]))
        k += len(sents)
    return "\n".join(out)


def _content_words(text: str) -> set:
    return {w for w in re.findall(r"[a-z0-9']+", text.lower()) if len(w) > 3}


def translate_checked(text: str) -> list[dict]:
    """English -> Dzongkha, then back to English to estimate quality.
    Returns [{"en": ..., "dz": ..., "score": 0..1}]. Score = share of the
    original's main words that survive the round trip (a rough guide only)."""
    sentences = [s for l in text.splitlines() for s in _split_sentences(l.strip(), EN)]
    dz = _translate_many(sentences, EN, DZ)
    back = _translate_many(dz, DZ, EN)

    rows = []
    for en, d, b in zip(sentences, dz, back):
        original = _content_words(en)
        score = 1.0 if not original else len(original & _content_words(b)) / len(original)
        rows.append({"en": en, "dz": d, "score": score})
    return rows