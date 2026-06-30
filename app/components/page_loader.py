import streamlit as st


def render_skeleton(title: str = "Loading..."):
    st.markdown(f"""
    <div class="page-skeleton">
        <div class="skeleton-title"></div>
        <div class="skeleton-row">
            <div class="skeleton-box"></div>
            <div class="skeleton-box"></div>
            <div class="skeleton-box"></div>
            <div class="skeleton-box"></div>
        </div>
        <div class="skeleton-row">
            <div class="skeleton-chart"></div>
            <div class="skeleton-chart"></div>
        </div>
        <div class="skeleton-table"></div>
    </div>
    """, unsafe_allow_html=True)
