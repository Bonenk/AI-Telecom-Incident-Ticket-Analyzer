import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd

from app.components.styles import severity_badge, category_badge
from app.components.page_loader import render_skeleton
from app.services.database import TicketDatabase


@st.cache_data
def load_data():
    db = TicketDatabase()
    analyses = db.list_analyses(limit=500)
    return pd.DataFrame(analyses)


def render():
    placeholder = st.empty()
    with placeholder:
        render_skeleton("Loading dashboard...")

    df = load_data()
    placeholder.empty()

    st.title(" Dashboard")
    st.markdown("Overview of analyzed telecom incident tickets.")

    if df.empty:
        db = TicketDatabase()
        synthetic = db.list_synthetic_tickets()
        if synthetic:
            st.info("No analyzed tickets yet. Run an analysis on the **Ticket Analysis** page first.")
        else:
            st.warning("No data found. Run `uv run python scripts/generate_data.py` to seed.")
        return

    total = len(df)
    active = int(df["human_decision"].isna().sum()) if "human_decision" in df.columns else 0
    critical = int((df["severity"] == "Critical").sum()) if "severity" in df.columns else 0
    resolved = int(df["human_decision"].isin(["approved", "edited"]).sum()) if "human_decision" in df.columns else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="value">{total}</div>
            <div class="label">Analyzed Tickets</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="value">{active}</div>
            <div class="label">Pending / Open</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="value">{critical}</div>
            <div class="label">Critical</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="value">{resolved}</div>
            <div class="label">Resolved</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    if "severity" in df.columns and df["severity"].notna().any():
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("### Severity Distribution")
            sev_data = df["severity"].value_counts().reindex(
                ["Critical", "High", "Medium", "Low"], fill_value=0
            ).reset_index()
            sev_data.columns = ["Severity", "Count"]
            st.bar_chart(sev_data, x="Severity", y="Count", height=300)
        with col_right:
            st.markdown("### Category Distribution")
            cat_data = df["category"].value_counts().reset_index()
            cat_data.columns = ["Category", "Count"]
            st.bar_chart(cat_data, x="Category", y="Count", height=300)
        st.divider()

    st.markdown("### Recent Tickets")
    display_count = min(5, len(df))
    recent = df.head(display_count)
    for _, row in recent.iterrows():
        hd = row.get("human_decision")
        if pd.isna(hd) or not hd:
            status_label = "Pending"
        else:
            status_label = str(hd).title()
        label = f"[{row['ticket_id']}] {row['subject'][:70]} — {status_label}"
        with st.expander(label, expanded=False):
            cc = st.columns([2, 1, 1, 1])
            with cc[0]:
                if row.get("severity"):
                    st.markdown(severity_badge(row["severity"]), unsafe_allow_html=True)
                if row.get("category"):
                    st.markdown(category_badge(row["category"]), unsafe_allow_html=True)
            with cc[1]:
                st.markdown(f"**Score:** {row.get('severity_score', 'N/A')}/100")
                st.markdown(f"**ETA:** {row.get('resolution_eta', 'N/A')}")
            with cc[2]:
                st.markdown(f"**Decision:** {status_label.title()}")
                if row.get("human_feedback"):
                    st.markdown(f"*{row['human_feedback']}*")
            with cc[3]:
                st.markdown(f"**Confidence:** {row.get('confidence', 0):.0%}")
            if row.get("resolution"):
                st.markdown(f"**Resolution:** {row['resolution']}")
            st.caption(f"Analyzed at: {row.get('created_at', 'N/A')}")

    if len(df) > 5:
        st.markdown("—")
        st.page_link("pages/tickets.py", label=" View all tickets →", icon="📋")


render()
