import time

import streamlit as st

from core import config
from core.documents import DocumentError, MAX_FILE_MB, extract_text
from core.summarizer import count_scripts, to_english
from core.translator import DZ, EN, contains_dzongkha, translate, translate_checked
from ui import theme

DIRECTIONS = {
    "Auto-detect": "auto",
    "English → Dzongkha": "en2dz",
    "Dzongkha → English": "dz2en",
}
LABELS = {"en2dz": "English → Dzongkha", "dz2en": "Dzongkha → English"}
LOW_SCORE = 0.4     # sentences scoring below this are flagged by the quality check


def resolve_direction(choice: str, text: str) -> str:
    if choice != "auto":
        return choice
    tibetan, latin = count_scripts(text)
    if tibetan + latin == 0:
        return "en2dz"
    return "dz2en" if tibetan / (tibetan + latin) >= 0.5 else "en2dz"


def to_dzongkha(text: str, on_progress=None) -> str:
    """Translate only the lines that are not already Dzongkha."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    idx = [i for i, l in enumerate(lines) if not contains_dzongkha(l)]
    if not idx:
        return "\n".join(lines)
    source = [lines[i] for i in idx]
    out = translate("\n".join(source), EN, DZ, on_progress=on_progress).split("\n")
    if len(out) != len(source):                       # safety: translate line by line
        out = [translate(l, EN, DZ) for l in source]
    for i, t in zip(idx, out):
        lines[i] = t
    return "\n".join(lines)


st.markdown("## 🌐 Translator")
st.caption("Translate between English and Dzongkha. Type, paste or upload a file.")


@st.cache_resource(show_spinner="Loading the Dzongkha translator (first start only)...")
def warm_up():
    from core.translator import _load
    _load()
    return True


try:
    warm_up()
except Exception as e:
    st.error(f"The translator is not ready: {e}")
    st.stop()

direction_label = st.radio("Direction", list(DIRECTIONS), horizontal=True)
check = st.checkbox("Check translation quality (English → Dzongkha, slower)", value=False)
method = st.radio("Input", ["Type or paste", "Upload a file"], horizontal=True)

source_text, source_name = "", ""
if method == "Type or paste":
    source_text = st.text_area("Your text", height=240, key="tr_typed")
    source_name = "Typed text"
else:
    uploaded = st.file_uploader(f"PDF, DOCX or TXT file (up to {MAX_FILE_MB} MB)", type=["pdf", "docx", "txt"], key="tr_file")
    st.caption("Scanned PDFs (pictures of pages) cannot be read yet.")
    if uploaded is not None:
        try:
            source_text = extract_text(uploaded.name, uploaded.getvalue())
            source_name = uploaded.name
            st.success(f"Read {len(source_text):,} characters from {uploaded.name}.")
            st.text_area(
                "Check that the text was read correctly (strange symbols mean the file uses an old Dzongkha font)",
                source_text[:1500], height=140, disabled=True,
            )
        except DocumentError as e:
            st.error(str(e))

direction = resolve_direction(DIRECTIONS[direction_label], source_text)
if source_text.strip():
    st.caption(f"Will translate: {LABELS[direction]}")

if st.button("🌐 Translate", type="primary", disabled=not source_text.strip()):
    warnings = []
    text = source_text.strip()
    if len(text) > config.MAX_INPUT_CHARS:
        cut = text[:config.MAX_INPUT_CHARS]
        end = max(cut.rfind("."), cut.rfind("།"), cut.rfind("\n"))
        if end > config.MAX_INPUT_CHARS * 0.5:
            cut = cut[:end + 1]
        text = cut
        warnings.append(
            f"The text is long, so only the first {len(text):,} characters were translated. "
            "You can raise MAX_INPUT_CHARS in the .env file."
        )

    bar = st.progress(0.0, text="Translating...")

    def on_progress(done, total):
        bar.progress(min(done / total, 1.0), text=f"Translating... ({done}/{total} sentences)")

    started = time.time()
    try:
        if direction == "en2dz":
            if contains_dzongkha(text):
                warnings.append("Some lines already contain Dzongkha. Those lines were kept as they are.")
            output = to_dzongkha(text, on_progress)
            flags = []
            if check:
                bar.progress(1.0, text="Checking quality...")
                english_lines = "\n".join(l for l in text.splitlines() if l.strip() and not contains_dzongkha(l))
                if english_lines:
                    rows = translate_checked(english_lines)
                    flags = [r["en"] for r in rows if r["score"] < LOW_SCORE]
        else:
            output = to_english(text, on_progress)
            flags = []
            warnings.append("Dzongkha to English is machine translation too. Please check important details.")

        st.session_state["tr_result"] = {
            "out": output, "src": text, "direction": direction, "name": source_name,
            "flags": flags, "warnings": warnings, "seconds": time.time() - started,
        }
    except Exception as e:
        st.session_state.pop("tr_result", None)
        st.error(str(e))
    bar.empty()

res = st.session_state.get("tr_result")
if res:
    st.markdown(f"### Translation ({LABELS[res['direction']]})")
    with st.container(border=True):
        st.write("\n\n".join(l for l in res["out"].split("\n") if l.strip()))
    st.caption(f"Source: {res['name']} | Time: {res['seconds']:.0f}s")

    if res["flags"]:
        st.warning(
            "These sentences may not be translated well. Please check them:\n\n"
            + "\n".join(f"- {f}" for f in res["flags"])
        )
    for w in res["warnings"]:
        st.warning(w)

    st.download_button(
        "⬇️ Download translation (.txt)", res["out"].encode("utf-8-sig"),
        file_name="translation.txt", mime="text/plain",
    )
    with st.expander("Copy the text"):
        st.code(res["out"], language=None)

    src_lines = [l.strip() for l in res["src"].splitlines() if l.strip()]
    out_lines = [l for l in res["out"].split("\n") if l.strip()]
    if len(src_lines) == len(out_lines) and len(src_lines) > 1:
        with st.expander("Compare line by line"):
            for s, o in zip(src_lines, out_lines):
                a, b = st.columns(2)
                a.write(s)
                b.write(o)

    if st.button("Clear result"):
        st.session_state.pop("tr_result", None)
        st.rerun()

theme.notice(
    "<b>Please note:</b> this is machine translation. Dzongkha is a low-resource language, "
    "so mistakes happen, especially in greetings and technical words. "
    "Please check important text with a Dzongkha speaker."
)