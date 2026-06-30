import random

import streamlit as st
import pandas as pd

from app.services.database import TicketDatabase


def load_tickets_df() -> pd.DataFrame:
    db = TicketDatabase()
    tickets = db.list_synthetic_tickets()
    if not tickets:
        return pd.DataFrame()
    df = pd.DataFrame(tickets)
    df["display"] = df.apply(lambda r: f"[{r['ticket_id']}] {r['subject'][:60]}", axis=1)
    return df


def ticket_selector():
    st.markdown("### Ticket Input")
    mode = st.radio(
        "Choose input method",
        ["Paste custom ticket", "Select from dataset"],
        index=0,
        horizontal=True,
        label_visibility="collapsed",
    )

    ticket = None

    if mode == "Select from dataset":
        df = load_tickets_df()
        if df.empty:
            st.warning("No synthetic tickets found. Run `python scripts/generate_data.py` first.")
            return None

        options = df["display"].tolist()
        selected = st.selectbox("Browse tickets", options)
        if selected:
            idx = options.index(selected)
            row = df.iloc[idx]
            ticket = row.to_dict()

            with st.expander("Ticket details", expanded=False):
                cols = st.columns(2)
                with cols[0]:
                    st.markdown(f"**ID:** {row['ticket_id']}")
                    st.markdown(f"**Category:** {row['category']}")
                    st.markdown(f"**Severity:** {row['severity']}")
                    st.markdown(f"**Status:** {row['status']}")
                with cols[1]:
                    st.markdown(f"**Customer:** {row['customer_name']}")
                    st.markdown(f"**Account:** {row['customer_account']}")
                    st.markdown(f"**Created:** {row['created_at']}")

                st.markdown(f"**Subject:** {row['subject']}")
                st.markdown(f"**Description:** {row['description']}")

    else:
        gen_id = f"TKT-{random.randint(10000, 99999)}"
        st.text_input("Ticket ID", value=gen_id, disabled=True, key="gen_ticket_id")
        subj = st.text_input("Subject", placeholder="e.g., 5G signal drop in downtown area")
        desc = st.text_area(
            "Description",
            placeholder="Describe the issue in detail...",
            height=150,
        )
        cols = st.columns(2)
        with cols[0]:
            cat = st.selectbox("Category", ["Network", "Billing", "Hardware", "Software", "Customer"])
        with cols[1]:
            sev = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
        ticket = {
            "ticket_id": gen_id,
            "subject": subj,
            "description": desc,
            "category": cat,
            "severity": sev,
            "customer_name": "",
            "customer_account": "",
            "contact_email": "",
            "contact_phone": "",
            "created_at": "",
            "resolved_at": "",
            "resolution": "",
            "priority_score": 0,
            "status": "Open",
        }

    return ticket
