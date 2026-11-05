from pathlib import Path

import requests
import streamlit as st

from core import config

ASSETS = Path(__file__).resolve().parent.parent / "assets"
LOGO_PATH = ASSETS / "logo.svg"

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Lora:wght@500;700&family=Noto+Serif+Tibetan:wght@400;600&family=Poppins:wght@400;500;600&display=swap');

.stApp {
  font-family: 'Poppins', 'Segoe UI', 'Noto Serif Tibetan', 'Jomolhari', 'Microsoft Himalaya', sans-serif;
}
h1, h2, h3 { font-family: 'Lora', Georgia, 'Noto Serif Tibetan', 'Microsoft Himalaya', serif; color: #4A3420; }
.block-container { max-width: 1100px; padding-top: 2rem; }
.stMarkdown p, [data-testid="stChatMessage"] p { line-height: 1.9; }

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #F8F0DF 0%, #F1E4C8 100%);
  border-right: 1px solid #E6D3A8;
}

.hero {
  background: linear-gradient(135deg, #FFF6E0 0%, #F3E3C3 55%, #E9CF98 100%);
  border: 1px solid #E6D3A8; border-radius: 24px; padding: 2rem 2.2rem;
  display: flex; align-items: center; gap: 1.6rem;
  box-shadow: 0 8px 30px rgba(168, 122, 30, .12); margin-bottom: 1.5rem;
}
.hero h1 { margin: 0; font-size: 2.4rem; }
.hero .tag { margin: .4rem 0 0; color: #6B5438; font-size: 1.05rem; }
.hero .dz { font-size: 1.5rem; color: #A97A1E; line-height: 1.9; font-family: 'Noto Serif Tibetan', 'Jomolhari', 'Microsoft Himalaya', serif; }

.card {
  background: #FFFFFF; border: 1px solid #EEE0BF; border-radius: 20px;
  padding: 1.3rem 1.4rem; height: 100%; min-height: 190px;
  box-shadow: 0 4px 16px rgba(168, 122, 30, .08);
}
.card .ico { font-size: 1.8rem; }
.card h3 { margin: .4rem 0 .3rem; font-size: 1.2rem; }
.card p { color: #6B5438; font-size: .93rem; margin-bottom: .8rem; }
.badge { display: inline-block; padding: .15rem .7rem; border-radius: 999px; font-size: .75rem; font-weight: 600; }
.badge.ok { background: #E4F2E1; color: #2F6B2A; }
.badge.soon { background: #F6EEDD; color: #8A6D2F; }

.steps { display: flex; gap: 1rem; margin: 1rem 0 1.5rem; flex-wrap: wrap; }
.step {
  flex: 1; min-width: 200px; background: #FFF9EA; border: 1px dashed #D9BC72;
  border-radius: 16px; padding: 1rem 1.1rem; color: #4A3420; font-size: .93rem;
}
.step b { color: #A97A1E; font-size: 1.1rem; }

.notice {
  border-left: 4px solid #B8892B; background: #FFF8E8; border-radius: 8px;
  padding: .9rem 1.1rem; color: #5A4630; margin: .8rem 0;
}

[data-testid="stChatMessage"] {
  background: #FFFFFF; border: 1px solid #EEE0BF; border-radius: 18px;
  padding: 1rem 1.2rem; box-shadow: 0 2px 10px rgba(168, 122, 30, .06);
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { background: #FBF3E1; }

.stButton > button, .stDownloadButton > button {
  border-radius: 999px; border: 1px solid #D9BC72; background: #FFF9EA; color: #4A3420;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  border-color: #B8892B; background: #F6E6BC; color: #3A2E26;
}

.status { font-size: .85rem; color: #4A3420; margin: .3rem 0; }
.status small { color: #8A6D2F; display: block; margin-left: 1.3rem; }
.dot { display: inline-block; width: .65rem; height: .65rem; border-radius: 50%; margin-right: .55rem; }
.dot.good { background: #3E9B3A; }
.dot.bad { background: #C0392B; }
"""


def inject_css():
    st.markdown("<style>" + CSS + "</style>", unsafe_allow_html=True)


def logo_svg() -> str:
    try:
        return " ".join(LOGO_PATH.read_text(encoding="utf-8").split())
    except OSError:
        return ""


def set_logo():
    try:
        st.logo(str(LOGO_PATH))
    except Exception:
        pass            # older Streamlit versions: the app still works without it


def hero():
    st.markdown(
        '<div class="hero">' + logo_svg() + "<div>"
        '<div class="dz">རྫོང་ཁ</div>'
        "<h1>DzongkhaGPT</h1>"
        '<p class="tag">Your AI language assistant for Bhutan. Ask in English or Dzongkha '
        "and read the answers in Dzongkha.</p>"
        "</div></div>",
        unsafe_allow_html=True,
    )


def card(icon: str, title: str, text: str, status: str):
    cls = "ok" if status == "Available" else "soon"
    st.markdown(
        f'<div class="card"><div class="ico">{icon}</div><h3>{title}</h3>'
        f'<p>{text}</p><span class="badge {cls}">{status}</span></div>',
        unsafe_allow_html=True,
    )


def steps(items: list[tuple[str, str]]):
    boxes = "".join(f'<div class="step"><b>{n}</b><br>{t}</div>' for n, t in items)
    st.markdown(f'<div class="steps">{boxes}</div>', unsafe_allow_html=True)


def notice(text: str):
    st.markdown(f'<div class="notice">{text}</div>', unsafe_allow_html=True)


def coming_soon(icon: str, title: str, planned: str):
    st.markdown(f"## {icon} {title}")
    notice(f"<b>Coming soon.</b> {planned} This feature is not built yet.")


@st.cache_data(ttl=5)
def _ollama_ok() -> bool:
    try:
        return requests.get(config.OLLAMA_URL, timeout=1).ok
    except Exception:
        return False


def _row(label: str, ok: bool, detail: str) -> str:
    cls = "good" if ok else "bad"
    return f'<div class="status"><span class="dot {cls}"></span>{label}<small>{detail}</small></div>'


def sidebar_status():
    with st.sidebar:
        st.caption("SYSTEM STATUS")
        if config.LLM_BACKEND == "ollama":
            ok = _ollama_ok()
            st.markdown(
                _row("AI model", ok, config.OLLAMA_MODEL if ok else "Ollama is not running"),
                unsafe_allow_html=True,
            )
        else:
            ok = bool(config.GEMINI_API_KEY)
            st.markdown(
                _row("AI model (Gemini)", ok, config.GEMINI_MODEL if ok else "API key missing"),
                unsafe_allow_html=True,
            )
        ready = config.NLLB_CT2_DIR.exists()
        st.markdown(
            _row("Translator", ready, "Ready" if ready else "Converted model not found"),
            unsafe_allow_html=True,
        )