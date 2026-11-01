import re
from functools import lru_cache
from . import config
from .glossary import lookup

EN = "eng_Latn"
DZ = "dzo_Tibt"


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
    """Loads the translator once (slow the first time)."""
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

    tokenizer = AutoTokenizer.from_pretrained(config.NLLB_MODEL)
    model = AutoModelForSeq2SeqLM.from_pretrained(config.NLLB_MODEL)
    model.eval()
    return tokenizer, model


def _split_sentences(line: str, lang: str) -> list[str]:
    if lang == DZ:
        parts = re.split(r"(?<=།)\s*", line)
    else:
        parts = re.split(r"(?<=[.!?])\s+", line)
    return [p.strip() for p in parts if p.strip()]


@lru_cache(maxsize=512)
def _translate_piece(text: str, src: str, tgt: str) -> str:
    """Translate one sentence. Cached: the same sentence is never translated twice."""
    override = lookup(text, src)               # glossary wins over the AI translator
    if override:
        return override

    import torch

    tokenizer, model = _load()
    tokenizer.src_lang = src
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=200)
    max_new = int(inputs["input_ids"].shape[1] * 2) + 20
    with torch.no_grad():
        output = model.generate(
            **inputs,
            forced_bos_token_id=tokenizer.convert_tokens_to_ids(tgt),
            num_beams=1,
            do_sample=False,
            max_new_tokens=max_new,
        )
    result = tokenizer.batch_decode(output, skip_special_tokens=True)[0].strip()
    return clean_dzongkha(result) if tgt == DZ else result


def translate(text: str, src: str, tgt: str, on_progress=None) -> str:
    """Translate line by line, sentence by sentence.
    on_progress(done, total) is called after each sentence (optional)."""
    work = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for i, line in enumerate(lines):
        for s in _split_sentences(line, src):
            work.append((i, s))

    results = [[] for _ in lines]
    for done, (i, sentence) in enumerate(work, start=1):
        results[i].append(_translate_piece(sentence, src, tgt))
        if on_progress:
            on_progress(done, len(work))
    return "\n".join(" ".join(r) for r in results)