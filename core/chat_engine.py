import time
from . import config, llm
from .translator import translate, translate_checked, contains_dzongkha, EN, DZ

SYSTEM_PROMPT = """Always reply in English only, using the Latin alphabet. Never use Chinese or any other language.
You are DzongkhaGPT, a helpful and honest assistant for people in Bhutan.
Your answer will be machine-translated into Dzongkha, so:
- Use short, simple sentences. One idea per sentence.
- No idioms, markdown, tables, emojis or special symbols.
- Do not invent facts. If you are not sure, say so.
- Keep answers to at most 4 sentences unless asked for more."""

REMINDER = "\n\n(Reply in English only, using the Latin alphabet.)"

LOW_SCORE = 0.4   # sentences scoring below this are flagged


def is_english_text(text: str) -> bool:
    """False if the text contains letters outside the Latin alphabet (e.g. Chinese)."""
    return not any(c.isalpha() and ord(c) > 0x024F for c in text)


class ChatSession:
    """Keeps the conversation. Internally we think in English."""

    def __init__(self):
        self.turns: list[dict] = []

    def _ask_ai(self, recent: list[dict]) -> str:
        reply = llm.generate(SYSTEM_PROMPT, recent)
        if is_english_text(reply):
            return reply

        # The model slipped into another language: retry once with a reminder
        retry = [dict(m) for m in recent]
        retry[-1]["content"] += REMINDER
        reply = llm.generate(SYSTEM_PROMPT, retry)
        if is_english_text(reply):
            return reply
        raise RuntimeError(
            "The AI answered in the wrong language twice. "
            "Please try again or switch to another model (see README)."
        )

    def ask(self, user_text: str, answer_lang: str = "dz", verify: bool = False,
            on_step=None, on_english=None) -> dict:
        """Returns {"reply", "english", "t_ai", "t_translate", "flags"}."""
        step = on_step or (lambda msg: None)

        english_in = user_text
        if contains_dzongkha(user_text):
            step("Translating your Dzongkha message to English...")
            english_in = translate(user_text, DZ, EN)

        self.turns.append({"role": "user", "content": english_in})
        recent = self.turns[-config.MAX_HISTORY_TURNS:]
        if recent and recent[0]["role"] == "assistant":
            recent = recent[1:]

        step("The AI is writing the answer...")
        t0 = time.time()
        try:
            english_out = self._ask_ai(recent)
        except Exception:
            self.turns.pop()
            raise
        t_ai = time.time() - t0
        self.turns.append({"role": "assistant", "content": english_out})

        if answer_lang == "en":
            return {"reply": english_out, "english": english_out,
                    "t_ai": t_ai, "t_translate": 0.0, "flags": []}

        if on_english:
            on_english(english_out)

        t1 = time.time()
        flags = []
        if verify:
            step("Translating and checking quality...")
            rows = translate_checked(english_out)
            reply = " ".join(r["dz"] for r in rows)
            flags = [r["en"] for r in rows if r["score"] < LOW_SCORE]
        else:
            step("Translating to Dzongkha...")
            reply = translate(english_out, EN, DZ)

        return {"reply": reply, "english": english_out, "t_ai": t_ai,
                "t_translate": time.time() - t1, "flags": flags}

    def clear(self):
        self.turns = []