import time
from . import config, llm
from .translator import translate, contains_dzongkha, EN, DZ

SYSTEM_PROMPT = """You are DzongkhaGPT, a helpful and honest assistant for people in Bhutan.
Rules:
- Write in plain, short, simple English sentences. Your answer will be machine-translated into Dzongkha, so do NOT use markdown, tables, emojis or special symbols. If you must list steps, use plain lines like "Step 1: ...".
- Do not invent facts. If you are not sure, say clearly that you are not sure.
- Keep answers short: at most 4 short sentences unless the user asks for more."""


class ChatSession:
    """Keeps the conversation. Internally we think in English."""

    def __init__(self):
        self.turns: list[dict] = []

    def ask(self, user_text: str, answer_lang: str = "dz", on_step=None) -> dict:
        """Returns {"reply", "english", "t_ai", "t_translate"}.
        on_step(message) is called so the page can show progress."""
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
            english_out = llm.generate(SYSTEM_PROMPT, recent)
        except Exception:
            self.turns.pop()
            raise
        t_ai = time.time() - t0
        self.turns.append({"role": "assistant", "content": english_out})

        if answer_lang == "en":
            return {"reply": english_out, "english": english_out,
                    "t_ai": t_ai, "t_translate": 0.0}

        t1 = time.time()
        reply = translate(
            english_out, EN, DZ,
            on_progress=lambda d, n: step(f"Translating to Dzongkha... ({d}/{n} sentences)"),
        )
        return {"reply": reply, "english": english_out,
                "t_ai": t_ai, "t_translate": time.time() - t1}

    def clear(self):
        self.turns = []