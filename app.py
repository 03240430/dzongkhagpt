import streamlit as st
from core.chat_engine import ChatSession

st.set_page_config(page_title="DzongkhaGPT", page_icon="🇧🇹")
st.title("DzongkhaGPT: Chat (test version)")
st.caption("Dzongkha is machine-translated and may contain mistakes. "
           "Please check important answers with a Dzongkha speaker.")


@st.cache_resource(show_spinner="Loading the Dzongkha translator (first start only, can take a minute)...")
def warm_up():
    from core.translator import _load
    _load()
    return True


warm_up()

if "session" not in st.session_state:
    st.session_state.session = ChatSession()
    st.session_state.shown = []

lang_choice = st.radio("Answer language", ["Dzongkha", "English"], horizontal=True)

if st.button("Clear chat"):
    st.session_state.session.clear()
    st.session_state.shown = []

for m in st.session_state.shown:
    with st.chat_message(m["role"]):
        st.write(m["text"])
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
        status = st.status("Working...", expanded=True)
        try:
            result = st.session_state.session.ask(
                prompt,
                "dz" if lang_choice == "Dzongkha" else "en",
                on_step=lambda msg: status.write(msg),
            )
            status.update(label="Done", state="complete", expanded=False)
            timing = f"AI: {result['t_ai']:.1f}s | Translation: {result['t_translate']:.1f}s"
            st.write(result["reply"])
            if result["english"] != result["reply"]:
                with st.expander("Show English original"):
                    st.write(result["english"])
            st.caption(timing)
            st.session_state.shown.append({
                "role": "assistant", "text": result["reply"],
                "english": result["english"], "timing": timing,
            })
        except Exception as e:
            status.update(label="Something went wrong", state="error")
            st.error(f"{e}")