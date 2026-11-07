import streamlit as st

from core.documents import DocumentError, MAX_FILE_MB, extract_text
from core.summarizer import detect_language, summarize
from ui import theme

LENGTHS = {"Short": "short", "Medium": "medium", "Detailed": "detailed"}
LANG_NAMES = {"en": "English", "dz": "Dzongkha", "mixed": "English and Dzongkha", "unknown": "unknown"}

st.markdown("## 📝 Summarize Text")
st.caption("Type, paste or upload text in English or Dzongkha. The summary is written in Dzongkha unless you choose English.")


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

c1, c2 = st.columns(2)
with c1:
    length_label = st.radio("Summary length", list(LENGTHS), index=1, horizontal=True)
with c2:
    out_label = st.radio("Summary language", ["Dzongkha", "English"], horizontal=True)

method = st.radio("Input", ["Type or paste", "Upload a file"], horizontal=True)

source_text, source_name = "", ""
if method == "Type or paste":
    source_text = st.text_area("Your text (English or Dzongkha)", height=260, key="sum_typed")
    source_name = "Typed text"
else:
    uploaded = st.file_uploader(f"PDF, DOCX or TXT file (up to {MAX_FILE_MB} MB)", type=["pdf", "docx", "txt"])
    st.caption("Scanned PDFs (pictures of pages) cannot be read yet. One file at a time for now.")
    if uploaded is not None:
        try:
            source_text = extract_text(uploaded.name, uploaded.getvalue())
            source_name = uploaded.name
            st.success(f"Read {len(source_text):,} characters from {uploaded.name}.")
            st.text_area(
                "Check that the text was read correctly (strange symbols mean the file uses an old Dzongkha font)",
                source_text[:1500], height=150, disabled=True,
            )
        except DocumentError as e:
            st.error(str(e))

if source_text.strip():
    st.caption(f"Detected language: {LANG_NAMES[detect_language(source_text)]}")

if st.button("✨ Summarize", type="primary", disabled=not source_text.strip()):
    bar = st.progress(0.0, text="Starting...")

    def on_progress(frac, msg):
        bar.progress(min(max(frac, 0.0), 1.0), text=msg)

    try:
        result = summarize(
            source_text, LENGTHS[length_label],
            "dz" if out_label == "Dzongkha" else "en",
            on_progress=on_progress,
        )
        result["name"] = source_name
        result["out"] = out_label
        st.session_state["sum_result"] = result
    except Exception as e:
        st.session_state.pop("sum_result", None)
        st.error(str(e))
    bar.empty()

res = st.session_state.get("sum_result")
if res:
    st.markdown("### Summary")
    with st.container(border=True):
        lines = [l for l in res["summary"].split("\n") if l.strip()]
        if len(lines) > 1:
            st.markdown("\n".join(f"- {l}" for l in lines))
        else:
            st.write(lines[0] if lines else "")
    st.caption(
        f"Source: {res['name']} | Language: {LANG_NAMES[res['source_lang']]} | "
        f"Parts read: {res['chunks']} | Time: {res['seconds']:.0f}s"
    )
    for w in res["warnings"]:
        st.warning(w)

    st.download_button(
        "⬇️ Download summary (.txt)", res["summary"].encode("utf-8-sig"),
        file_name="summary.txt", mime="text/plain",
    )
    with st.expander("Copy the text"):
        st.code(res["summary"], language=None)
    if res["out"] == "Dzongkha":
        with st.expander("Show the English version (what the AI wrote)"):
            st.write(res["summary_en"])
    if res.get("source_en"):
        with st.expander("How the AI understood your Dzongkha text (English)"):
            st.write(res["source_en"])
            st.caption("If this English is wrong, the summary will be wrong too.")
    if st.button("Clear result"):
        st.session_state.pop("sum_result", None)
        st.rerun()

theme.notice(
    "<b>Please note:</b> summaries are machine-made and machine-translated. They can miss details "
    "or contain mistakes, so check important facts against the original."
)