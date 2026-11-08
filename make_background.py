import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = {}

# ------------------------------------------------------- .streamlit/config.toml
FILES[".streamlit/config.toml"] = r'''[theme]
base = "dark"
primaryColor = "#4DA3FF"
backgroundColor = "#05080F"
secondaryBackgroundColor = "#0C1424"
textColor = "#F2F5FA"
font = "sans serif"

[theme.sidebar]
backgroundColor = "#000000"
secondaryBackgroundColor = "#0A0A0A"
textColor = "#FFFFFF"
primaryColor = "#4DA3FF"

[client]
toolbarMode = "minimal"

[browser]
gatherUsageStats = false
'''

# ------------------------------------------------------------------ ui/theme.py
FILES["ui/theme.py"] = r'''import base64
from pathlib import Path

import requests
import streamlit as st

from core import config

ASSETS = Path(__file__).resolve().parent.parent / "assets"
LOGO_PATH = ASSETS / "logo.svg"

BACKGROUND_NAMES = ("background.jpeg", "background.jpg", "background.png", "background.webp")
MIME_TYPES = {".jpeg": "image/jpeg", ".jpg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}

OVERLAY = 0.50     # darkness over the picture: 0 = none, 1 = black. Raise it if text is hard to read.

_bg_cache: dict = {}

FONT_IMPORT = """@import url('https://fonts.googleapis.com/css2?family=Lora:wght@500;700&family=Noto+Serif+Tibetan:wght@400;600&family=Poppins:wght@400;500;600&display=swap');
"""

CSS = """
:root {
  --accent: #4DA3FF;
  --accent-soft: rgba(77, 163, 255, .20);
  --glass: rgba(8, 14, 26, .74);
  --glass-edge: rgba(255, 255, 255, .12);
  --text: #F2F5FA;
  --muted: #AEB9CA;
}

/* let the background picture show through Streamlit's own layers */
[data-testid="stAppViewContainer"], [data-testid="stMain"], .main,
[data-testid="stHeader"], [data-testid="stBottom"], [data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"] { background: transparent !important; }

.stApp {
  font-family: 'Poppins', 'Segoe UI', 'Noto Serif Tibetan', 'Jomolhari', 'Microsoft Himalaya', sans-serif;
  color: var(--text);
}
h1, h2, h3, h4 {
  font-family: 'Lora', Georgia, 'Noto Serif Tibetan', 'Microsoft Himalaya', serif;
  color: #FFFFFF;
}
.block-container { max-width: 1100px; padding-top: 2rem; }
.stMarkdown p, [data-testid="stChatMessage"] p { line-height: 1.9; }

[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li, [data-testid="stWidgetLabel"] p, label { color: var(--text); }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: var(--muted); }

/* ---------------------------------------------------------------- sidebar */
[data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child,
[data-testid="stSidebarContent"], [data-testid="stSidebarHeader"],
[data-testid="stSidebarUserContent"] { background: #000000 !important; background-image: none !important; }
[data-testid="stSidebar"] { border-right: 1px solid #1C1C1C; }
[data-testid="stSidebar"] * { color: #FFFFFF !important; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color: #8FA0B8 !important; }
[data-testid="stSidebar"] .status small { color: #9FB0C7 !important; }

[data-testid="stSidebarNav"] a, a[data-testid="stSidebarNavLink"] {
  border-radius: 10px; border-left: 3px solid transparent;
}
[data-testid="stSidebarNav"] a:hover, a[data-testid="stSidebarNavLink"]:hover {
  background: rgba(255, 255, 255, .09) !important;
}
[data-testid="stSidebarNav"] a[aria-current="page"], a[data-testid="stSidebarNavLink"][aria-current="page"] {
  background: var(--accent-soft) !important; border-left-color: var(--accent);
}
[data-testid="stSidebarNav"] a[aria-current="page"] span,
a[data-testid="stSidebarNavLink"][aria-current="page"] span { font-weight: 600; }

/* ------------------------------------------------------------- components */
.hero {
  background: linear-gradient(135deg, rgba(10, 18, 34, .84) 0%, rgba(10, 18, 34, .60) 100%);
  border: 1px solid var(--glass-edge); border-radius: 24px; padding: 2rem 2.2rem;
  display: flex; align-items: center; gap: 1.6rem; margin-bottom: 1.5rem;
  backdrop-filter: blur(6px);
}
.hero h1 { margin: 0; font-size: 2.4rem; color: #FFFFFF; }
.hero .tag { margin: .4rem 0 0; color: var(--muted); font-size: 1.05rem; }
.hero .dz { font-size: 1.5rem; color: var(--accent); line-height: 1.9; font-family: 'Noto Serif Tibetan', 'Jomolhari', 'Microsoft Himalaya', serif; }

.card {
  background: var(--glass); border: 1px solid var(--glass-edge); border-radius: 20px;
  padding: 1.3rem 1.4rem; height: 100%; min-height: 190px; backdrop-filter: blur(6px);
}
.card .ico { font-size: 1.8rem; }
.card h3 { margin: .4rem 0 .3rem; font-size: 1.2rem; }
.card p { color: var(--muted); font-size: .93rem; margin-bottom: .8rem; }
.badge { display: inline-block; padding: .15rem .7rem; border-radius: 999px; font-size: .75rem; font-weight: 600; }
.badge.ok { background: rgba(62, 155, 58, .25); color: #9BE896; }
.badge.soon { background: rgba(255, 255, 255, .10); color: #C9D3E3; }

.steps { display: flex; gap: 1rem; margin: 1rem 0 1.5rem; flex-wrap: wrap; }
.step {
  flex: 1; min-width: 200px; background: var(--glass); border: 1px dashed rgba(77, 163, 255, .45);
  border-radius: 16px; padding: 1rem 1.1rem; color: #E8EEF8; font-size: .93rem;
}
.step b { color: var(--accent); font-size: 1.1rem; }

.notice {
  border-left: 4px solid var(--accent); background: var(--glass); border-radius: 8px;
  padding: .9rem 1.1rem; color: #E8EEF8; margin: .8rem 0; backdrop-filter: blur(6px);
}

[data-testid="stChatMessage"] {
  background: var(--glass); border: 1px solid var(--glass-edge); border-radius: 18px;
  padding: 1rem 1.2rem; backdrop-filter: blur(6px);
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { background: rgba(20, 40, 72, .72); }

[data-testid="stChatInput"] { background: transparent !important; }
[data-testid="stChatInput"] > div {
  background: rgba(8, 14, 26, .92) !important; border: 1px solid var(--glass-edge) !important; border-radius: 16px;
}
[data-testid="stChatInput"] > div:focus-within { border-color: var(--accent) !important; }
[data-testid="stChatInput"] textarea { color: #FFFFFF !important; }

[data-testid="stExpander"] {
  background: var(--glass); border: 1px solid var(--glass-edge); border-radius: 14px; backdrop-filter: blur(6px);
}
[data-testid="stAlert"] { border-radius: 12px; backdrop-filter: blur(6px); }

div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="textarea"],
div[data-baseweb="select"] > div {
  background-color: rgba(8, 14, 26, .86) !important; border-color: var(--glass-edge) !important; border-radius: 12px;
}
div[data-baseweb="input"]:focus-within, div[data-baseweb="textarea"]:focus-within,
div[data-baseweb="select"] > div:focus-within { border-color: var(--accent) !important; }
textarea, input { color: #FFFFFF !important; }
textarea:disabled, input:disabled { color: #C9D3E3 !important; -webkit-text-fill-color: #C9D3E3 !important; }
textarea::placeholder, input::placeholder { color: #8895A8 !important; }

[data-testid="stFileUploaderDropzone"] {
  background: rgba(8, 14, 26, .80) !important; border: 1px dashed rgba(255, 255, 255, .30) !important; border-radius: 14px;
}
[data-testid="stCode"] pre { background: rgba(8, 14, 26, .92) !important; }

.stButton > button, .stDownloadButton > button {
  border-radius: 999px; border: 1px solid rgba(255, 255, 255, .22);
  background: rgba(8, 14, 26, .78); color: #FFFFFF;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  border-color: var(--accent); background: var(--accent-soft); color: #FFFFFF;
}
.stButton > button[kind="primary"], button[data-testid="stBaseButton-primary"] {
  background: var(--accent); border-color: var(--accent); color: #031020; font-weight: 600;
}
.stButton > button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover {
  background: var(--accent); filter: brightness(1.12); color: #031020;
}
button [data-testid="stMarkdownContainer"] p { color: inherit; }

.status { font-size: .85rem; color: #FFFFFF; margin: .3rem 0; }
.status small { color: #9FB0C7; display: block; margin-left: 1.3rem; }
.dot { display: inline-block; width: .65rem; height: .65rem; border-radius: 50%; margin-right: .55rem; }
.dot.good { background: #3E9B3A; }
.dot.bad { background: #E5534B; }

/* ------------------------------------------------------------ small screens */
@media (max-width: 768px) {
  .stApp { background-attachment: scroll; }
  .hero { flex-direction: column; text-align: center; padding: 1.4rem; }
  .hero h1 { font-size: 1.9rem; }
}
"""


def _background_url() -> str:
    """The background picture as a data address, so it works on every page with no extra setup."""
    if "url" in _bg_cache:
        return _bg_cache["url"]
    for name in BACKGROUND_NAMES:
        path = ASSETS / name
        if path.exists():
            data = base64.b64encode(path.read_bytes()).decode("ascii")
            url = f"data:{MIME_TYPES[path.suffix.lower()]};base64,{data}"
            _bg_cache["url"] = url
            return url
    return ""


def _background_css() -> str:
    url = _background_url()
    shade = f"linear-gradient(rgba(2, 5, 12, {OVERLAY}), rgba(2, 5, 12, {OVERLAY}))"
    image = f'{shade}, url("{url}")' if url else "linear-gradient(160deg, #0B1424 0%, #03060C 70%)"
    return (
        ".stApp { background-color: #03060C; background-image: " + image + "; "
        "background-size: cover; background-position: center; "
        "background-repeat: no-repeat; background-attachment: fixed; }\n"
    )


def inject_css():
    st.markdown("<style>" + FONT_IMPORT + _background_css() + CSS + "</style>", unsafe_allow_html=True)


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
'''

# ------------------------------------------------------------------ write files
theme = ROOT / "ui" / "theme.py"
backup = theme.with_name("theme.py.bak")
if theme.exists() and not backup.exists():
    shutil.copy(theme, backup)
    print("backup  ui/theme.py.bak")

for rel, content in FILES.items():
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print("created ", rel)

# ------------------------------------------------------------ background image
assets = ROOT / "assets"
assets.mkdir(exist_ok=True)
names = ("background.jpeg", "background.jpg", "background.png", "background.webp")

if any((assets / n).exists() for n in names):
    print("found    the background image in assets")
else:
    home = Path.home()
    exts = (".jpeg", ".jpg", ".png", ".webp")
    found = []
    for folder in (home / "Downloads", home / "Desktop", home / "Pictures", ROOT, ROOT.parent):
        if folder.exists():
            found += [p for p in sorted(folder.glob("blue_flower.*")) if p.suffix.lower() in exts]
    if found:
        dest = assets / ("background" + found[0].suffix.lower())
        shutil.copy(found[0], dest)
        print("copied  ", found[0], "->", dest)
    else:
        print("NOTE     Copy your picture into the assets folder and name it background.jpeg")

print("\nDone. You can delete make_background.py now.")