import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import json

from app.components.styles import severity_badge, category_badge
from app.components.page_loader import render_skeleton
from app.services.database import TicketDatabase


def load_db():
    return TicketDatabase()


def render():
    ph = st.empty()
    with ph:
        render_skeleton("Loading history...")

    db = load_db()
    synthetic_tickets = db.list_synthetic_tickets()
    outage_logs = db.list_outage_logs()
    analyses = db.list_analyses(limit=500)
    ph.empty()

    st.title(" Ticket History & Logs")

    tab_analyses, tab_synthetic, tab_outages = st.tabs([
        "Analyzed Tickets (DB)", "Synthetic Dataset", "Outage Logs",
    ])

    with tab_analyses:
        if analyses:
            st.markdown(f"Showing **{len(analyses)}** analyzed ticket(s)")

            sev_vals = list({r["severity"] for r in analyses if r.get("severity")})
            cat_vals = list({r["category"] for r in analyses if r.get("category")})
            dec_vals = list({r["human_decision"] for r in analyses if r.get("human_decision")})

            cols = st.columns(3)
            with cols[0]:
                sev_filter = st.multiselect("Severity", sev_vals, default=[], key="an_sev")
            with cols[1]:
                cat_filter = st.multiselect("Category", cat_vals, default=[], key="an_cat")
            with cols[2]:
                dec_filter = st.multiselect("Human Decision", dec_vals, default=[], key="an_dec")

            filtered = analyses
            if sev_filter:
                filtered = [r for r in filtered if r.get("severity") in sev_filter]
            if cat_filter:
                filtered = [r for r in filtered if r.get("category") in cat_filter]
            if dec_filter:
                filtered = [r for r in filtered if r.get("human_decision") in dec_filter]

            for r in filtered:
                label = f"[{r.get('ticket_id', '?')}] {r.get('subject', '')[:70]}"
                if r.get("human_decision"):
                    label += f" ({r['human_decision']})"
                with st.expander(label, expanded=False):
                    cc = st.columns(3)
                    with cc[0]:
                        if r.get("category"):
                            st.markdown(category_badge(r["category"]), unsafe_allow_html=True)
                        if r.get("severity"):
                            st.markdown(severity_badge(r["severity"]), unsafe_allow_html=True)
                    with cc[1]:
                        st.markdown(f"**Confidence:** {r.get('confidence', 0):.0%}")
                        st.markdown(f"**Severity Score:** {r.get('severity_score', 0)}/100")
                    with cc[2]:
                        st.markdown(f"**ETA:** {r.get('resolution_eta', 'N/A')}")
                        st.markdown(f"**Decision:** {r.get('human_decision', 'pending')}")
                        if r.get("human_feedback"):
                            st.markdown(f"*Feedback: {r['human_feedback']}*")

                    st.markdown(f"**Subject:** {r.get('subject', '')}")
                    st.markdown(f"**Description:** {r.get('description', '')}")

                    if r.get("resolution"):
                        st.markdown(f"**Resolution:** {r['resolution']}")

                    sources = r.get("resolution_sources", [])
                    if sources:
                        with st.expander("Sources"):
                            for s in sources:
                                st.markdown(f"- {s}")

                    st.caption(f"Analyzed at: {r.get('created_at', 'N/A')}")
        else:
            st.info("No analyzed tickets yet. Run an analysis on the Ticket Analysis page first.")

    with tab_synthetic:
        if synthetic_tickets:
            df = __import__("pandas").DataFrame(synthetic_tickets)

            cols = st.columns(3)
            with cols[0]:
                sev_f = st.multiselect("Severity", df["severity"].unique(), default=[], key="sy_sev")
            with cols[1]:
                cat_f = st.multiselect("Category", df["category"].unique(), default=[], key="sy_cat")
            with cols[2]:
                st_f = st.multiselect("Status", df["status"].unique(), default=[], key="sy_st")

            filtered = df.copy()
            if sev_f:
                filtered = filtered[filtered["severity"].isin(sev_f)]
            if cat_f:
                filtered = filtered[filtered["category"].isin(cat_f)]
            if st_f:
                filtered = filtered[filtered["status"].isin(st_f)]

            st.markdown(f"Showing **{len(filtered)}** of **{len(df)}** synthetic tickets")

            for _, row in filtered.iterrows():
                with st.expander(f"[{row['ticket_id']}] {row['subject'][:70]}", expanded=False):
                    cc = st.columns(3)
                    with cc[0]:
                        st.markdown(severity_badge(row["severity"]), unsafe_allow_html=True)
                        st.markdown(f"**Status:** {row['status']}")
                    with cc[1]:
                        st.markdown(category_badge(row["category"]), unsafe_allow_html=True)
                        st.markdown(f"**Created:** {row['created_at']}")
                    with cc[2]:
                        st.markdown(f"**Customer:** {row['customer_name']}")
                        st.markdown(f"**Account:** {row['customer_account']}")
                    st.markdown(f"**Subject:** {row['subject']}")
                    st.markdown(f"**Description:** {row['description']}")
                    if row.get("resolution") and str(row["resolution"]).strip():
                        st.markdown(f"**Resolution:** {row['resolution']}")
        else:
            st.warning("No synthetic ticket data found. Run `uv run python scripts/generate_data.py` to seed.")

    with tab_outages:
        if outage_logs:
            st.markdown(f"Showing **{len(outage_logs)}** outage logs")
            for log in outage_logs:
                with st.expander(
                    f"[{log['outage_id']}] {log['area']} - {log['root_cause']} ({log['duration_hours']}h)",
                    expanded=False,
                ):
                    cc = st.columns(3)
                    with cc[0]:
                        st.markdown(f"**Area:** {log['area']}")
                        st.markdown(f"**Device:** {log['device']}")
                    with cc[1]:
                        st.markdown(f"**Start:** {log['start_time']}")
                        st.markdown(f"**End:** {log['end_time']}")
                    with cc[2]:
                        st.markdown(f"**Duration:** {log['duration_hours']}h")
                        st.markdown(f"**Affected:** {log['affected_customers']} customers")
                    st.markdown(f"**Root Cause:** {log['root_cause']}")
                    st.markdown(f"**Status:** {log['status']}")
        else:
            st.warning("No outage log data found. Run `uv run python scripts/generate_data.py` to seed.")


render()
