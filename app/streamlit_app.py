import sys
from pathlib import Path

# Ensure project root is on sys.path for all page scripts
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import streamlit as st

st.set_page_config(
    page_title="Telecom Incident Ticket Analyzer",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from app.components.styles import inject_css

if "theme" not in st.session_state:
    st.session_state["theme"] = "light"

inject_css(theme=st.session_state["theme"])

charts = st.Page("pages/dashboard.py", title="Dashboard", icon="📊", default=True)
analysis = st.Page("pages/ticket_analysis.py", title="Ticket Analysis", icon="🔍")
tickets = st.Page("pages/tickets.py", title="Tickets", icon="🎫")
pdfs = st.Page("pages/pdf_viewer.py", title="Knowledge Base", icon="📚")
logs = st.Page("pages/history.py", title="History", icon="📋")

pg = st.navigation([charts, analysis, tickets, pdfs, logs], position="sidebar")

with st.sidebar:
    st.markdown("## 📡 Telecom Analyzer")
    st.markdown("AI-powered incident ticket analysis with LangGraph agent workflow.")
    st.divider()
    st.markdown("**Pipeline:** Classification → Severity → Resolution → Human Approval")
    st.markdown("**RAG:** Telecom Knowledge Base (ChromaDB)")
    st.divider()
    st.selectbox(
        "Theme",
        options=["light", "dark"],
        index=0 if st.session_state["theme"] == "light" else 1,
        key="theme",
        label_visibility="collapsed",
    )

pg.run()
