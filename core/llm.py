import requests
from . import config


class LLMError(Exception):
    """Raised when the AI model cannot be reached or fails."""


def generate(system: str, messages: list[dict]) -> str:
    """messages = [{"role": "user" or "assistant", "content": "..."}]"""
    if config.LLM_BACKEND == "ollama":
        return _ollama(system, messages)
    if config.LLM_BACKEND == "gemini":
        return _gemini(system, messages)
    raise LLMError(f"Unknown LLM_BACKEND: {config.LLM_BACKEND}")


def _ollama(system, messages):
    payload = {
        "model": config.OLLAMA_MODEL,
        "stream": False,
        "keep_alive": "30m",                       # keep the model in memory
        "options": {
            "temperature": 0.3,
            "num_predict": 250,                    # limit answer length (faster)
        },
        "messages": [{"role": "system", "content": system}] + messages,
    }
    try:
        r = requests.post(f"{config.OLLAMA_URL}/api/chat", json=payload, timeout=300)
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
        raise LLMError("The AI took too long to answer. Try a shorter question.")
    except requests.exceptions.RequestException as e:
        raise LLMError(f"Ollama error: {e}")


def _gemini(system, messages):
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
                max_output_tokens=400,
            ),
        )
        return (response.text or "").strip()
    except Exception as e:
        raise LLMError(f"Gemini error: {e}")