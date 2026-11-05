
import streamlit as st

from core.chat_engine import ChatSession

st.title("💬 DzongkhaGPT AI Chat")

st.caption("Ask your questions in English or Dzongkha.")

# Keep the conversation session between Streamlit reruns
if "chat_session" not in st.session_state:
    st.session_state.chat_session = ChatSession()

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

session = st.session_state.chat_session

# Sidebar settings
with st.sidebar:
    st.subheader("Chat Settings")

    answer_language = st.selectbox(
        "Response language",
        options=["Dzongkha", "English"],
        index=0
    )

    verify_translation = st.checkbox(
        "Check translation quality",
        value=False
    )

    if st.button("Clear conversation"):
        session.clear()
        st.session_state.chat_messages = []
        st.rerun()

# Display previous messages
for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
user_input = st.chat_input("Type your message here...")

if user_input:
    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        status = st.status("Processing your message...", expanded=True)

        try:
            def show_step(message):
                status.write(message)

            result = session.ask(
                user_input,
                answer_lang="dz" if answer_language == "Dzongkha" else "en",
                verify=verify_translation,
                on_step=show_step
            )

            status.update(
                label="Response generated successfully!",
                state="complete",
                expanded=False
            )

            st.markdown(result["reply"])

            if result["flags"]:
                with st.expander("Translation quality warnings"):
                    for flag in result["flags"]:
                        st.write(flag)

            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": result["reply"]
            })

        except Exception as error:
            status.update(
                label="Unable to generate response",
                state="error"
            )
            st.error(str(error))
