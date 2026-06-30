import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd

from app.components.styles import severity_badge, category_badge
from app.components.page_loader import render_skeleton
from app.services.database import TicketDatabase


@st.cache_data
def load_analyses():
    db = TicketDatabase()
    return db.list_analyses(limit=500)


def render():
    ph = st.empty()
    with ph:
        render_skeleton("Loading tickets...")

    analyses = load_analyses()
    ph.empty()

    st.title(" All Tickets")
    st.markdown("Filterable list of all analyzed tickets.")

    if not analyses:
        st.info("No analyzed tickets yet. Run an analysis on the **Ticket Analysis** page first.")
        return

    df = pd.DataFrame(analyses)

    df["status_label"] = df["human_decision"].apply(
        lambda d: "Open" if pd.isna(d) or d == "" else d.title()
    )

    st.markdown(f"Showing **{len(df)}** ticket(s)")

    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        status_options = ["All", "Open", "Approved", "Edited", "Rejected"]
        status_filter = st.selectbox("Status", status_options, index=0)
    with col2:
        sev_values = [s for s in df["severity"].dropna().unique() if s]
        sev_filter = st.multiselect("Severity", sev_values, default=[])
    with col3:
        cat_values = [c for c in df["category"].dropna().unique() if c]
        cat_filter = st.multiselect("Category", cat_values, default=[])

    filtered = df.copy()
    if status_filter == "Open":
        filtered = filtered[filtered["human_decision"].isna() | (filtered["human_decision"] == "")]
    elif status_filter != "All":
        filtered = filtered[filtered["human_decision"] == status_filter.lower()]
    if sev_filter:
        filtered = filtered[filtered["severity"].isin(sev_filter)]
    if cat_filter:
        filtered = filtered[filtered["category"].isin(cat_filter)]

    st.markdown(f"Filtered: **{len(filtered)}** ticket(s)")

    db = TicketDatabase()

    for _, row in filtered.iterrows():
        status_label = row["status_label"]
        label = f"[{row['ticket_id']}] {row['subject'][:70]} — {status_label}"
        is_open = pd.isna(row.get("human_decision")) or row.get("human_decision") == ""
        with st.expander(label, expanded=False):
            cc = st.columns(3)
            with cc[0]:
                if row.get("severity"):
                    st.markdown(severity_badge(row["severity"]), unsafe_allow_html=True)
                if row.get("category"):
                    st.markdown(category_badge(row["category"]), unsafe_allow_html=True)
                st.markdown(f"**Decision:** {status_label}")
            with cc[1]:
                st.markdown(f"**Confidence:** {row.get('confidence', 0):.0%}")
                st.markdown(f"**Severity Score:** {row.get('severity_score', 0)}/100")
                st.markdown(f"**ETA:** {row.get('resolution_eta', 'N/A')}")
            with cc[2]:
                if row.get("human_feedback"):
                    st.markdown(f"**Feedback:** {row['human_feedback']}")
                st.markdown(f"**Analyzed:** {row.get('created_at', 'N/A')}")

            st.markdown(f"**Subject:** {row.get('subject', '')}")
            st.markdown(f"**Description:** {row.get('description', '')}")

            if row.get("classification_reasoning"):
                st.markdown(f"**Classification Reasoning:** {row['classification_reasoning']}")
            if row.get("severity_reasoning"):
                st.markdown(f"**Severity Reasoning:** {row['severity_reasoning']}")
            if row.get("resolution"):
                st.markdown(f"**Resolution:** {row['resolution']}")

            sources = row.get("resolution_sources", [])
            if sources:
                with st.expander("Sources"):
                    for s in sources:
                        st.markdown(f"- {s}")

            if is_open and row.get("resolution"):
                st.divider()
                st.markdown("### Take Action")
                action = st.radio(
                    "Action",
                    ["Approve", "Edit", "Reject"],
                    horizontal=True,
                    key=f"action_{row['id']}",
                    label_visibility="collapsed",
                )
                feedback = None
                edited_res = None
                if action == "Edit":
                    edited_res = st.text_area(
                        "Edit resolution",
                        value=row.get("resolution", ""),
                        height=100,
                        key=f"edit_{row['id']}",
                    )
                elif action == "Reject":
                    feedback = st.text_input(
                        "Reason for rejection",
                        key=f"reject_feedback_{row['id']}",
                        placeholder="Required feedback",
                    )
                btn_label = {"Approve": "✅ Approve", "Edit": "💾 Save Edit", "Reject": "❌ Reject"}[action]
                btn_type = "primary" if action != "Reject" else "secondary"
                if st.button(btn_label, type=btn_type, use_container_width=True, key=f"btn_{row['id']}"):
                    if action == "Reject" and not feedback:
                        st.warning("Please provide feedback for rejection.")
                    else:
                        updates = {"human_decision": action.lower()}
                        if action == "Edit":
                            if not edited_res or not edited_res.strip():
                                st.warning("Edited resolution cannot be empty.")
                            else:
                                updates["human_edited_resolution"] = edited_res
                                updates["resolution"] = edited_res
                        if action == "Reject":
                            updates["human_feedback"] = feedback
                        db.update_analysis(row["id"], updates)
                        st.cache_data.clear()
                        st.success(f"Ticket {row['ticket_id']} marked as **{action}**.")
                        st.rerun()


render()
