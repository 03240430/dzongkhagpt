import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama").lower()   # "ollama" or "gemini"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Translator (the tokenizer comes from NLLB_MODEL, the fast model from NLLB_CT2_DIR)
NLLB_MODEL = os.getenv("NLLB_MODEL", "facebook/nllb-200-distilled-600M")
NLLB_CT2_DIR = Path(os.getenv("NLLB_CT2_DIR", str(BASE_DIR / "models" / "nllb-600m-ct2")))
CT2_BEAM = int(os.getenv("CT2_BEAM", "2"))            # 1 = fastest, 4 = most careful
CPU_THREADS = int(os.getenv("CPU_THREADS", str(max(1, (os.cpu_count() or 4) // 2))))

MAX_HISTORY_TURNS = 10   # how many past messages the AI remembers

MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "30000"))   # longest text to summarize
CHUNK_WORDS = int(os.getenv("CHUNK_WORDS", "600"))                # words per part for long texts
