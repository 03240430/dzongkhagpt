import requests
from . import config


class LLMError(Exception):
    """Raised when the AI model cannot be reached or fails."""


def is_english_text(text: str) -> bool:
    """False if the text contains letters outside the Latin alphabet (e.g. Chinese)."""
    return not any(c.isalpha() and ord(c) > 0x024F for c in text)


def generate(system: str, messages: list[dict], max_tokens: int = 250) -> str:
    """messages = [{"role": "user" or "assistant", "content": "..."}]"""
    if config.LLM_BACKEND == "ollama":
        return _ollama(system, messages, max_tokens)
    if config.LLM_BACKEND == "gemini":
        return _gemini(system, messages, max_tokens)
    raise LLMError(f"Unknown LLM_BACKEND: {config.LLM_BACKEND}")


def generate_english(system: str, messages: list[dict], max_tokens: int = 250) -> str:
    """Like generate(), but retries once if the model slips into another language."""
    reply = generate(system, messages, max_tokens)
    if is_english_text(reply):
        return reply
    retry = [dict(m) for m in messages]
    retry[-1]["content"] += "\n\n(Reply in English only, using the Latin alphabet.)"
    reply = generate(system, retry, max_tokens)
    if is_english_text(reply):
        return reply
    raise LLMError("The AI answered in the wrong language twice. Please try again.")


def _ollama(system, messages, max_tokens):
    payload = {
        "model": config.OLLAMA_MODEL,
        "stream": False,
        "keep_alive": "30m",
        "options": {
            "temperature": 0.3,
            "num_predict": max_tokens,
            "num_ctx": 4096,
        },
        "messages": [{"role": "system", "content": system}] + messages,
    }
    try:
        r = requests.post(f"{config.OLLAMA_URL}/api/chat", json=payload, timeout=600)
        if r.status_code == 404:
            raise LLMError(
                f"Model '{config.OLLAMA_MODEL}' not found. "
                f"Run: ollama pull {config.OLLAMA_MODEL}"
            )
        r.raise_for_status()
        return r.json()["message"]["content"].strip()
    except requests.exceptions.ConnectionError:
        raise LLMError("Cannot reach Ollama. Is the Ollama app running?")
    except requests.exceptions.Timeout:
        raise LLMError("The AI took too long to answer. Try a shorter text.")
    except requests.exceptions.RequestException as e:
        raise LLMError(f"Ollama error: {e}")


def _gemini(system, messages, max_tokens):
    if not config.GEMINI_API_KEY:
        raise LLMError("GEMINI_API_KEY is missing in your .env file.")
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=config.GEMINI_API_KEY)
        contents = [
            types.Content(
                role="user" if m["role"] == "user" else "model",
                parts=[types.Part(text=m["content"])],
            )
            for m in messages
        ]
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.3,
                max_output_tokens=max(1024, max_tokens * 3),
            ),
        )
        return (response.text or "").strip()
    except Exception as e:
        raise LLMError(f"Gemini error: {e}")
