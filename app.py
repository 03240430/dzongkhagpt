import streamlit as st

from ui import theme

st.set_page_config(page_title="DzongkhaGPT", page_icon="🏔️", layout="wide")
theme.inject_css()
theme.set_logo()


def summarize_page():
    theme.coming_soon("📝", "Summarize Text",
                      "Paste English or Dzongkha text and get a short, medium or detailed summary.")


def documents_page():
    theme.coming_soon("📄", "Documents",
                      "Upload PDF, DOCX or TXT files and get one summary per file, plus an optional combined one.")


def history_page():
    theme.coming_soon("🕘", "History",
                      "Review earlier chats and delete them whenever you like.")


pages = [
    st.Page("views/home.py", title="Home", icon="🏠", default=True),
    st.Page("views/chat.py", title="AI Chat", icon="💬"),
    st.Page(summarize_page, title="Summarize Text", icon="📝", url_path="summarize"),
    st.Page(documents_page, title="Documents", icon="📄", url_path="documents"),
    st.Page(history_page, title="History", icon="🕘", url_path="history"),
    st.Page("views/about.py", title="About", icon="ℹ️"),
]

page = st.navigation(pages)
theme.sidebar_status()
page.run()