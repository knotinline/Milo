from datetime import datetime

import streamlit as st
from model_adapter import call_model
from policy_engine import build_system_prompt, decide_for_input, decide_for_output, make_rewrite_prompt
from theme import THEMES, hide_page_nav, html_block, inject_base_styles, logo_html

st.set_page_config(page_title="Milo", page_icon="🤖", layout="wide")
inject_base_styles()
hide_page_nav()

if "provider" not in st.session_state:
    st.session_state.provider = "chatgpt"
if "age_band" not in st.session_state:
    st.session_state.age_band = "11-13"

provider = st.session_state.provider
engine = THEMES[provider]
age_band = st.session_state.age_band

html_block(
    f"""
    <div class="hero-card">
        <div class="brand-row">
            <div class="brand-left">
                {logo_html()}
                <div class="main-title">Milo</div>
            </div>
            <div class="live-indicator"><span class="live-dot"></span>System active</div>
        </div>
        <div class="muted">
            Your AI homework buddy — a protected chat experience for kids.
        </div>
        <div class="status-row">
            <span class="status-pill">{engine['icon']} {engine['label']} engine</span>
        </div>
    </div>
    """
)
st.page_link("pages/1_Parent_Dashboard.py", label="🔒 Parent Dashboard")

html_block(
    """
    <div class="chat-header">
        <div class="chat-header-title">💬 Live session</div>
        <div class="live-indicator"><span class="live-dot"></span>Active</div>
    </div>
    """
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "logs" not in st.session_state:
    st.session_state.logs = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_message = st.chat_input("Ask Milo...")

if user_message:
    with st.chat_message("user"):
        st.write(user_message)
    st.session_state.messages.append({"role": "user", "content": user_message})

    input_decision = decide_for_input(user_message, age_band)
    st.session_state.logs.append({
        "stage": "Input",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "context": user_message,
        **input_decision.__dict__,
    })

    if input_decision.action in {"BLOCK", "ESCALATE"}:
        final_answer = input_decision.message
    else:
        system_prompt = build_system_prompt(age_band)
        model_messages = [{"role": "system", "content": system_prompt}]
        model_messages += st.session_state.messages[-6:]
        draft_answer = call_model(model_messages, provider)

        output_decision = decide_for_output(draft_answer, age_band)
        st.session_state.logs.append({
            "stage": "Output",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "context": draft_answer,
            **output_decision.__dict__,
        })

        if output_decision.action == "BLOCK":
            final_answer = output_decision.message
        elif input_decision.action == "REWRITE" or output_decision.action == "REWRITE":
            rewrite_prompt = make_rewrite_prompt(age_band, user_message, draft_answer)
            final_answer = call_model([
                {"role": "system", "content": build_system_prompt(age_band)},
                {"role": "user", "content": rewrite_prompt},
            ], provider)
        else:
            final_answer = draft_answer

    with st.chat_message("assistant"):
        st.write(final_answer)
    st.session_state.messages.append({"role": "assistant", "content": final_answer})
