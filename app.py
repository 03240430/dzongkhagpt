import streamlit as st
from core.chat_engine import ChatSession

st.set_page_config(page_title="DzongkhaGPT", page_icon="🇧🇹")
st.title("DzongkhaGPT: Chat (test version)")
st.caption("Dzongkha is machine-translated and may contain mistakes. "
           "Please check important answers with a Dzongkha speaker.")


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


def show_flags(flags):
    if flags:
        st.warning(
            "These sentences may not be translated well. Please check them:\n\n"
            + "\n".join(f"- {f}" for f in flags)
        )


if "session" not in st.session_state:
    st.session_state.session = ChatSession()
    st.session_state.shown = []

lang_choice = st.radio("Answer language", ["Dzongkha", "English"], horizontal=True)
verify = st.checkbox("Check translation quality (slower)", value=False)

if st.button("Clear chat"):
    st.session_state.session.clear()
    st.session_state.shown = []

for m in st.session_state.shown:
    with st.chat_message(m["role"]):
        st.write(m["text"])
        show_flags(m.get("flags"))
        if m.get("english") and m["english"] != m["text"]:
            with st.expander("Show English original"):
                st.write(m["english"])
        if m.get("timing"):
            st.caption(m["timing"])

prompt = st.chat_input("Type in English or Dzongkha...")
if prompt:
    st.session_state.shown.append({"role": "user", "text": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        english_box = st.empty()
        status = st.status("Working...", expanded=True)
        try:
            result = st.session_state.session.ask(
                prompt,
                "dz" if lang_choice == "Dzongkha" else "en",
                verify=verify,
                on_step=lambda msg: status.write(msg),
                on_english=lambda t: english_box.info(f"English draft (Dzongkha coming...): {t}"),
            )
            english_box.empty()
            status.update(label="Done", state="complete", expanded=False)
            timing = f"AI: {result['t_ai']:.1f}s | Translation: {result['t_translate']:.1f}s"
            st.write(result["reply"])
            show_flags(result["flags"])
            if result["english"] != result["reply"]:
                with st.expander("Show English original"):
                    st.write(result["english"])
            st.caption(timing)
            st.session_state.shown.append({
                "role": "assistant", "text": result["reply"],
                "english": result["english"], "timing": timing,
                "flags": result["flags"],
            })
        except Exception as e:
            english_box.empty()
            status.update(label="Something went wrong", state="error")
            st.error(f"{e}")