import html
import os

import streamlit as st
from dotenv import load_dotenv

from theme import THEMES, hide_page_nav, html_block, inject_base_styles, logo_html

load_dotenv()

PARENT_PIN = os.getenv("PARENT_PIN", "1234")

st.set_page_config(page_title="Parent Dashboard - Milo", page_icon="🤖", layout="wide")
inject_base_styles()
hide_page_nav()

STATUS_STYLES = {
    "ALLOW": {"color": "#34d399", "bg": "rgba(52, 211, 153, 0.14)", "icon": "✅"},
    "REWRITE": {"color": "#fab219", "bg": "rgba(250, 178, 25, 0.14)", "icon": "✏️"},
    "BLOCK": {"color": "#ec835a", "bg": "rgba(236, 131, 90, 0.16)", "icon": "⛔"},
    "ESCALATE": {"color": "#f87171", "bg": "rgba(208, 59, 59, 0.18)", "icon": "🚨"},
}

if "parent_authenticated" not in st.session_state:
    st.session_state.parent_authenticated = False

if not st.session_state.parent_authenticated:
    html_block(
        f"""
        <div class="hero-card">
            <div class="brand-row">
                <div class="brand-left">
                    {logo_html()}
                    <div class="main-title">Parent Dashboard</div>
                </div>
            </div>
            <div class="muted">Enter the parent PIN to view safety alerts and settings.</div>
        </div>
        """
    )
    pin_input = st.text_input("Parent PIN", type="password")
    if st.button("Unlock"):
        if pin_input == PARENT_PIN:
            st.session_state.parent_authenticated = True
            st.rerun()
        else:
            st.error("Incorrect PIN.")
    st.page_link("app.py", label="🤖 Back to Milo")
    st.stop()

log = st.session_state.get("logs", [])
decision_counts = {"ALLOW": 0, "REWRITE": 0, "BLOCK": 0, "ESCALATE": 0}
for entry in log:
    if entry["action"] in decision_counts:
        decision_counts[entry["action"]] += 1

escalate_entries = [e for e in log if e["action"] == "ESCALATE"]
block_entries = [e for e in log if e["action"] == "BLOCK"]

if st.button("Lock"):
    st.session_state.parent_authenticated = False
    st.rerun()
st.page_link("app.py", label="🤖 Back to Milo")

html_block(
    f"""
    <div class="hero-card">
        <div class="brand-row">
            <div class="brand-left">
                {logo_html()}
                <div class="main-title">Parent Dashboard</div>
            </div>
            <div class="live-indicator"><span class="live-dot"></span>Monitoring</div>
        </div>
        <div class="muted">
            Automated safety feedback from your child's Milo sessions — no need to read every message yourself.
        </div>
        <div class="stats-grid">
            <div class="stat-tile">
                <div class="stat-label">Messages reviewed</div>
                <div class="stat-value" style="color: var(--accent);">{len(log)}</div>
            </div>
            <div class="stat-tile">
                <div class="stat-label">Allowed</div>
                <div class="stat-value" style="color: {STATUS_STYLES['ALLOW']['color']};">{decision_counts['ALLOW']}</div>
            </div>
            <div class="stat-tile">
                <div class="stat-label">Rewritten</div>
                <div class="stat-value" style="color: {STATUS_STYLES['REWRITE']['color']};">{decision_counts['REWRITE']}</div>
            </div>
            <div class="stat-tile">
                <div class="stat-label">Blocked / escalated</div>
                <div class="stat-value" style="color: {STATUS_STYLES['BLOCK']['color']};">{decision_counts['BLOCK'] + decision_counts['ESCALATE']}</div>
            </div>
        </div>
    </div>
    """
)

provider = st.session_state.get("provider", "chatgpt")
engine_line = f"{THEMES[provider]['icon']} Currently running on the {THEMES[provider]['label']} engine"

html_block(
    f"""
    <div class="vision-card">
        <div class="vision-heading">◉ Parents' Vision · Live Mode</div>
        <div class="vision-title">Give your child the benefits of AI, with you still in control.</div>
        <div class="vision-copy">
            Milo is the approved learning space: helpful questions stay available,
            unsafe requests are stopped, and this dashboard gives you live visibility without
            requiring you to read every conversation.
        </div>
        <div class="vision-points">
            <div class="vision-point">🛡️ Age-appropriate answers</div>
            <div class="vision-point">🔒 Engine & settings locked to parent control</div>
            <div class="vision-point">📡 {len(block_entries) + len(escalate_entries)} live alert(s) for your attention</div>
        </div>
        <div class="muted" style="margin-top: 0.8rem;">{engine_line}</div>
    </div>
    """
)

st.subheader("🔔 Automated Feedback")

if not escalate_entries and not block_entries:
    html_block(
        """
        <div class="alert-banner clear">
            <div class="alert-title">✅ No safety concerns detected</div>
            <div class="muted">Every message so far was either allowed or safely rewritten. You'll see an alert here the moment something needs your attention.</div>
        </div>
        """
    )

if escalate_entries:
    items = "".join(
        f"""
        <div class="alert-item">
            <div class="alert-meta">{html.escape(e.get('timestamp', ''))} · {html.escape(e['stage'])} · {html.escape(e['category'])}</div>
            <div class="alert-message">&ldquo;{html.escape(e.get('context', ''))}&rdquo;</div>
        </div>
        """
        for e in reversed(escalate_entries)
    )
    html_block(
        f"""
        <div class="alert-banner critical">
            <div class="alert-title">🚨 {len(escalate_entries)} urgent alert(s) — your child may need support</div>
            <div class="muted">These messages matched self-harm or crisis language and were redirected to trusted-adult guidance instead of a normal answer.</div>
            {items}
        </div>
        """
    )

if block_entries:
    items = "".join(
        f"""
        <div class="alert-item">
            <div class="alert-meta">{html.escape(e.get('timestamp', ''))} · {html.escape(e['stage'])} · {html.escape(e['category'])}</div>
            <div class="alert-message">&ldquo;{html.escape(e.get('context', ''))}&rdquo;</div>
        </div>
        """
        for e in reversed(block_entries)
    )
    html_block(
        f"""
        <div class="alert-banner warning">
            <div class="alert-title">⛔ {len(block_entries)} blocked attempt(s)</div>
            <div class="muted">Your child asked for something outside the allowed topics, or tried to bypass Milo (including switching to another AI). Nothing unsafe was sent or shown.</div>
            {items}
        </div>
        """
    )

with st.container(key="sidebar_settings"):
    st.markdown("<div class='sidebar-eyebrow'>⚙️ Settings</div>", unsafe_allow_html=True)

    current_provider = st.session_state.get("provider", "chatgpt")
    st.caption("AI engine")
    eng_col1, eng_col2 = st.columns(2)
    with eng_col1:
        if st.button("💬 ChatGPT engine", use_container_width=True, disabled=(current_provider == "chatgpt")):
            st.session_state.provider = "chatgpt"
            st.rerun()
    with eng_col2:
        if st.button("🐋 DeepSeek engine", use_container_width=True, disabled=(current_provider == "deepseek")):
            st.session_state.provider = "deepseek"
            st.rerun()

    age_options = ["8-10", "11-13", "14-16"]
    current_age = st.session_state.get("age_band", "11-13")
    age_band = st.selectbox("Child age band", age_options, index=age_options.index(current_age))
    if age_band != current_age:
        st.session_state.age_band = age_band
        st.success(f"Age band updated to {age_band}.")

    if st.button("Clear safety log"):
        st.session_state.logs = []
        st.rerun()

st.divider()
st.subheader("🛰️ Full Safety Telemetry Log")
if log:
    legend_chips = "".join(
        f"<span class='legend-chip'>{style['icon']} "
        f"<span style='color:{style['color']};'>{action}</span></span>"
        for action, style in STATUS_STYLES.items()
    )
    st.markdown(f"<div class='telemetry-legend'>{legend_chips}</div>", unsafe_allow_html=True)

    rows = ""
    for entry in reversed(log):
        style = STATUS_STYLES.get(entry["action"], {"color": "#a8b6d3", "bg": "rgba(148,163,184,0.12)", "icon": "•"})
        badge = (
            f"<span class='decision-badge' style='color:{style['color']}; background:{style['bg']};'>"
            f"{style['icon']} {html.escape(entry['action'])}</span>"
        )
        rows += (
            "<tr>"
            f"<td>{html.escape(entry.get('timestamp', ''))}</td>"
            f"<td>{html.escape(entry['stage'])}</td>"
            f"<td>{badge}</td>"
            f"<td>{html.escape(entry['category'])}</td>"
            f"<td>{html.escape(entry['severity'])}</td>"
            f"<td>{html.escape(entry['explanation'])}</td>"
            "</tr>"
        )

    html_block(
        f"""
        <table class="telemetry-table">
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Stage</th>
                    <th>Decision</th>
                    <th>Category</th>
                    <th>Severity</th>
                    <th>Explanation</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        """
    )
else:
    st.write("No safety decisions yet.")
