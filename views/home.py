
import streamlit as st

from ui import theme

st.title("🏔️ Welcome to DzongkhaGPT")

st.markdown("""
### Your AI Assistant for Bhutan

DzongkhaGPT helps you communicate in English and Dzongkha
using artificial intelligence and machine translation.

### What you can do

- 💬 **AI Chat:** Ask questions in English or Dzongkha.
- 📝 **Summarize Text:** Summarize long text.
- 📄 **Documents:** Work with uploaded documents.
- 🕘 **History:** Review previous conversations.

Select **AI Chat** from the sidebar to start a conversation.
""")

st.divider()

st.info("Developed to make AI assistance more accessible in Bhutan.")
