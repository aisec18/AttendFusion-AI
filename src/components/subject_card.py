import streamlit as st


def subject_card(name, code, section, stats=None, footer_callback=None):
    stats_html = ""
    if stats:
        items = []
        for icon, label, value in stats:
            items.append(
                f'<div style="background:#EB459E10; padding:5px 12px; border-radius:12px; font-size:0.9rem; display:inline-flex; align-items:center; gap:4px;">{icon} <b>{value}</b> {label}</div>'
            )
        stats_html = f'<div style="display:flex; gap:8px; flex-wrap:wrap; margin-top:12px;">{"".join(items)}</div>'

    html = f"""
    <div style="background:white; border-left:8px solid #EB459E; padding:25px; border-radius:20px; border:1px solid #e2e8f0; margin-bottom:20px; box-shadow:0 2px 8px rgba(15,23,42,0.06);">
        <h3 style="margin:0; color:#1e293b; font-size:1.5rem;">{name}</h3>
        <p style="color:#64748b; margin:10px 0 12px 0;">
            Code: <span style="background:#E0E3FF; color:#5865F2; padding:2px 8px; border-radius:5px;">{code}</span>
            &nbsp;|&nbsp; Section: {section}
        </p>
        {stats_html}
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)

    if footer_callback:
        footer_callback()
