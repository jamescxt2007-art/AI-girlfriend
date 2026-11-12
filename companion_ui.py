"""Streamlit presentation; local model requests remain in ollama_local.py."""
import base64
import os
import time
from html import escape
from pathlib import Path

import streamlit as st

from companion_logic import AVATARS, BIOS, DEMO, LOCAL, PERSONALITIES, STARTERS
from companion_logic import chat_text, companion_instructions, conversation_text, demo_reply, reply_expression
from ollama_local import DEFAULT_MODEL, OllamaError, chat_reply, installed_models, local_model_name

ROOT = Path(__file__).resolve().parent
EXPRESSIONS = ("happy", "thoughtful", "playful")


@st.cache_data
def portrait_sources():
    return {expression: base64.b64encode(
        (ROOT / "assets" / "character" / f"mika-{expression}.png").read_bytes()
    ).decode("ascii") for expression in EXPRESSIONS}


@st.cache_data
def full_body_source():
    return base64.b64encode((ROOT / "assets" / "character" / "mika-full-body.png").read_bytes()).decode("ascii")


def typing_html(name):
    return (f'<div class="typing-status" role="status" aria-live="polite">'
            f'<span>{escape(name)} is typing…</span>'
            '<span class="typing-dots" aria-hidden="true"><i></i><i></i><i></i></span></div>')


def portrait_html(name, expression, blinking=True, view="Portrait"):
    """All expressions share a fixed canvas and are preloaded, avoiding reflow."""
    if view == "Full body":
        return ('<div class="portrait-stage full-body-stage"><div class="portrait-float">'
                f'<img class="full-body-image" src="data:image/png;base64,{full_body_source()}" '
                f'alt="{escape(name, quote=True)} — full body, head to toe" width="400" height="1040">'
                '</div></div>')
    layers = []
    for state, source in portrait_sources().items():
        active = state == expression
        layers.append(
            f'<img class="portrait-layer {"is-active" if active else ""}" '
            f'src="data:image/png;base64,{source}" '
            f'alt="{escape(name, quote=True)} — {state} expression" '
            f'aria-hidden="{"false" if active else "true"}" width="420" height="420">'
        )
    blink_path = ROOT / "assets" / "character" / "mika-blink.png"
    if blinking and expression == "happy" and blink_path.is_file():
        source = base64.b64encode(blink_path.read_bytes()).decode("ascii")
        layers.append(f'<img class="portrait-blink" src="data:image/png;base64,{source}" '
                      'alt="" aria-hidden="true" width="420" height="420">')
    return ('<div class="portrait-stage"><div class="portrait-float">'
            + "".join(layers) + '</div></div>')


def render_app():
    st.set_page_config(page_title=f"Chat with {st.session_state.get('companion_name') or 'Mika'}",
                       page_icon="🌸", layout="wide")
    st.html(f"<style>{(ROOT / 'style.css').read_text(encoding='utf-8')}</style>")
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("confirm_clear", False)
    st.session_state.setdefault("portrait_expression", "happy")
    st.session_state.setdefault("reply_error", "")

    with st.sidebar:
        st.header("Settings")
        with st.expander("Personalize", expanded=True):
            name = st.text_input("Companion name", value="Mika", max_chars=40,
                                 key="companion_name").strip() or "Mika"
            personality = st.selectbox("Personality", list(PERSONALITIES), key="personality")
            avatar_name = st.selectbox("Chat icon", list(AVATARS), key="avatar")
            st.caption(BIOS[personality])
            view = st.selectbox("Character view", ["Full body", "Portrait"], key="character_view")
            st.caption("Full body shows the reference pose head to toe. Choose Portrait for blinking and facial-expression previews.")
            blinking = st.checkbox("Blink occasionally", value=True, key="portrait_blinking", disabled=view == "Full body")
            st.caption("Choose Portrait to preview facial expressions and blinking." if view == "Full body" else f"Preview an expression. {name} looks thoughtful while typing; the Playful preset can finish with a playful expression.")
            for expression in EXPRESSIONS:
                if st.button(expression.title(), key=f"preview_{expression}", use_container_width=True, disabled=view == "Full body"):
                    st.session_state.portrait_expression = expression

        with st.expander("Connection & model"):
            mode = st.radio("Reply mode", [DEMO, LOCAL],
                            index=1 if st.session_state.get("active_mode") == LOCAL else 0,
                            key="reply_mode")
            model = os.getenv("OLLAMA_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
            ready = mode == DEMO
            if mode == LOCAL:
                model = st.text_input("Ollama model", value=model, key="ollama_model").strip()
                st.caption("Local endpoint: http://localhost:11434 · No key required")
                st.button("Refresh connection", key="refresh_connection", use_container_width=True)
                try:
                    models = installed_models()
                    canonical = local_model_name(model)
                    st.success("Ollama connected")
                    if canonical in models:
                        st.caption(f"Active model: {canonical} · Ready to load locally")
                        ready = True
                    else:
                        st.warning("Selected local model is not installed.")
                        st.code(f"ollama pull {canonical}", language="powershell")
                    if models:
                        st.caption("Installed local models: " + ", ".join(models))
                except OllamaError as error:
                    st.error(str(error))
                st.caption("Connection checked on each interaction. First-time model loading can take longer.")
            else:
                st.caption("Demo is scripted, not model-generated. No requests are sent to Ollama.")
            technical_error = st.empty()
            st.caption("Switching reply modes starts a fresh chat. Download first to keep a copy.")

        with st.expander("About"):
            st.caption(f"{name} is a virtual AI character, not a real person. Local AI uses Ollama on this computer. No paid services are used.")
            st.caption("Session only. Chats are not automatically saved. Keep downloaded conversations private.")

    # Preserve existing session history and provider selection across UI changes.
    if st.session_state.get("active_mode") != mode:
        st.session_state.active_mode = mode
        st.session_state.messages = []
        st.session_state.confirm_clear = False
        st.session_state.reply_error = ""
        st.session_state.portrait_expression = "happy"
    if st.session_state.reply_error:
        technical_error.error(st.session_state.reply_error)

    with st.sidebar:
        st.divider()
        st.download_button("Download conversation", data=conversation_text(
            st.session_state.messages, name, personality,
            mode if mode == DEMO else f"{mode} · Model: {model}"),
            file_name="companion-chat.txt", mime="text/plain", use_container_width=True,
            disabled=not st.session_state.messages)
        if st.button("Clear chat", key="clear_chat", use_container_width=True,
                     disabled=not st.session_state.messages):
            st.session_state.confirm_clear = True
        if st.session_state.confirm_clear:
            st.warning("Clear this conversation? Download it first if you want to keep it.")
            yes, no = st.columns(2)
            if yes.button("Yes, clear", key="confirm_clear_button", use_container_width=True):
                st.session_state.messages = []
                st.session_state.confirm_clear = False
                st.session_state.reply_error = ""
                st.session_state.portrait_expression = "happy"
                st.rerun()
            if no.button("Cancel", key="cancel_clear", use_container_width=True):
                st.session_state.confirm_clear = False
                st.rerun()

    with st.container(key="companion_layout"):
        portrait_column, chat_column = st.columns([0.9, 1.35], gap="large")
        with portrait_column:
            with st.container(key="portrait_panel"):
                portrait = st.empty()
                portrait.markdown(portrait_html(name, st.session_state.portrait_expression, blinking, view), unsafe_allow_html=True)
                st.markdown(f'<div class="portrait-name">{escape(name)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="portrait-bio">{BIOS[personality]}</div>', unsafe_allow_html=True)
        with chat_column:
            st.markdown('<div class="eyebrow">A LITTLE SPACE FOR YOU</div>', unsafe_allow_html=True)
            st.subheader(f"Chat with {name}")
            if mode == DEMO:
                st.caption("Demo · scripted replies")
            if not ready:
                st.warning(f"{name} can't reply just yet. Open Settings → Connection & model for help.")
            if st.session_state.reply_error:
                st.error(f"{name} couldn't reply. Your conversation is safe. See Settings → Connection & model for details, then try again.")

            starter = None
            if not st.session_state.messages:
                st.markdown(
                    f'<div class="welcome"><h2>A moment with {escape(name)}</h2>'
                    '<p>Make yourself comfortable. Share a small win, unpack your day, '
                    'or follow a little curiosity. Where shall we start?</p></div>', unsafe_allow_html=True)
                columns = st.columns(2)
                for index, (label, text) in enumerate(STARTERS.items()):
                    if columns[index % 2].button(label, key=f"starter_{index}",
                                                use_container_width=True, disabled=not ready):
                        starter = text

            for item in st.session_state.messages:
                with st.chat_message(item["role"], avatar=AVATARS[avatar_name] if item["role"] == "assistant" else None):
                    st.caption(name if item["role"] == "assistant" else "You")
                    st.write(chat_text(item["content"], mode))

            prompt = st.chat_input(f"Message {name}…", disabled=not ready, max_chars=4000) or starter
            if prompt and prompt.strip():
                pending = st.session_state.messages + [{"role": "user", "content": prompt.strip()}]
                with st.chat_message("user"):
                    st.caption("You")
                    st.write(prompt.strip())
                typing_status = st.empty()
                st.session_state.reply_error = ""
                technical_error.empty()
                typing_status.markdown(typing_html(name), unsafe_allow_html=True)
                portrait.markdown(portrait_html(name, "thoughtful", blinking, view), unsafe_allow_html=True)
                after_expression = "happy"
                try:
                    if mode == DEMO:
                        # Brief local demo pause lets the status render; no delay for real AI.
                        time.sleep(0.7)
                        reply = demo_reply(prompt, personality, len(st.session_state.messages) // 2)
                    else:
                        reply = chat_reply(pending, companion_instructions(name, personality), model)
                except OllamaError as error:
                    st.session_state.reply_error = str(error)
                except Exception:
                    st.session_state.reply_error = "An unexpected error occurred. Restart the app and local service. The failed message was not added; submit it again. No demo reply was substituted."
                else:
                    st.session_state.messages = pending + [{"role": "assistant", "content": reply}]
                    after_expression = reply_expression(prompt, personality)
                finally:
                    st.session_state.portrait_expression = after_expression
                    portrait.markdown(portrait_html(name, after_expression, blinking, view), unsafe_allow_html=True)
                    typing_status.empty()
                st.rerun()
