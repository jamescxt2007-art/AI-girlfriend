"""Offline regression checks; Ollama HTTP requests are simulated."""
import unittest
from unittest.mock import patch

import requests
from streamlit.testing.v1 import AppTest
import app
import ollama_local as local
import companion_ui
from pathlib import Path
from PIL import Image

MODELS = {"models": [{"name": local.DEFAULT_MODEL}]}


class CompanionTests(unittest.TestCase):
    def setUp(self):
        mock = patch("ollama_local.request_json", return_value=MODELS)
        self.http = mock.start()
        self.addCleanup(mock.stop)

    def test_demo_history_and_clear_confirmation(self):
        page = AppTest.from_file("app.py").run()
        self.assertEqual(page.radio[0].value, app.DEMO)
        page.chat_input[0].set_value("hello").run()
        page.chat_input[0].set_value("I feel tired").run()
        self.assertEqual(len(page.chat_message), 4)
        self.assertNotIn("Scripted demo reply", page.session_state.messages[-1]["content"])
        self.http.assert_not_called()
        page.button(key="clear_chat").click().run()
        self.assertEqual(len(page.chat_message), 4)
        page.button(key="cancel_clear").click().run()
        self.assertEqual(len(page.chat_message), 4)
        page.button(key="clear_chat").click().run()
        page.button(key="confirm_clear_button").click().run()
        self.assertEqual(page.session_state.messages, [])
        self.assertFalse(page.exception)

    def test_personalization_and_starters(self):
        page = AppTest.from_file("app.py").run()
        page.button(key="starter_3").click().run()
        self.assertEqual(page.session_state.messages[0]["content"], app.STARTERS["Talk music & movies"])
        page.text_input(key="companion_name").set_value("Nova").run()
        self.assertEqual(len(page.session_state.messages), 2)
        page.chat_input[0].set_value("hello").run()
        self.assertIn("Hello!", page.session_state.messages[-1]["content"])
        page.radio[0].set_value(app.LOCAL).run()
        self.assertEqual(page.session_state.messages, [])
        self.assertFalse(page.exception)

    def test_stopped_missing_and_refresh(self):
        page = AppTest.from_file("app.py").run()
        self.http.side_effect = local.OllamaError("Cannot connect. Run ollama serve.")
        page.radio[0].set_value(app.LOCAL).run()
        self.assertTrue(page.chat_input[0].disabled)
        self.assertIn("Cannot connect", page.error[0].value)
        self.http.side_effect = None
        self.http.return_value = {"models": []}
        page.button(key="refresh_connection").click().run()
        self.assertTrue(page.chat_input[0].disabled)
        self.assertTrue(any("not installed" in item.value for item in page.warning))
        self.http.return_value = MODELS
        page.button(key="refresh_connection").click().run()
        self.assertFalse(page.chat_input[0].disabled)
        self.assertFalse(page.exception)

    def test_local_reply_and_failure_without_demo_fallback(self):
        def reply(method, path, **kwargs):
            return MODELS if method == "GET" else {"message": {"content": "A real local reply"}}
        self.http.side_effect = reply
        page = AppTest.from_file("app.py").run()
        page.radio[0].set_value(app.LOCAL).run()
        page.chat_input[0].set_value("hello").run()
        self.assertEqual(page.session_state.messages[-1]["content"], "A real local reply")
        def failure(method, path, **kwargs):
            if method == "GET":
                return MODELS
            raise local.OllamaError("Ollama took too long to respond.")
        self.http.side_effect = failure
        page.chat_input[0].set_value("second message").run()
        self.assertEqual(len(page.session_state.messages), 2)
        self.assertTrue(any("too long" in item.value for item in page.error))
        self.assertEqual(page.session_state.portrait_expression, "happy")
        self.assertFalse(page.exception)

    def test_default_name_preview_and_waiting_expression(self):
        with patch("companion_ui.portrait_html", wraps=companion_ui.portrait_html) as render, patch("companion_ui.typing_html", wraps=companion_ui.typing_html) as typing:
            page = AppTest.from_file("app.py").run()
            self.assertEqual(page.subheader[0].value, "Chat with Mika")
            page.selectbox(key="character_view").select("Portrait").run()
            page.button(key="preview_playful").click().run()
            self.assertEqual(page.session_state.portrait_expression, "playful")
            page.text_input(key="companion_name").set_value("Nova").run()
            self.assertEqual(page.subheader[0].value, "Chat with Nova")
            render.reset_mock()
            page.chat_input[0].set_value("Hello!").run()
            typing.assert_called_once_with("Nova")
            self.assertIn("Nova is typing…", companion_ui.typing_html("Nova"))
            states = [call.args[1] for call in render.call_args_list]
            self.assertIn("thoughtful", states)
            self.assertEqual(states[-1], "happy")
            self.assertEqual(page.session_state.portrait_expression, "happy")
            self.assertEqual(page.chat_message[-1].caption[0].value, "Nova")
            self.assertFalse(page.exception)

    def test_full_body_is_default_and_portrait_remains_available(self):
        page = AppTest.from_file("app.py").run()
        self.assertEqual(page.selectbox(key="character_view").value, "Full body")
        with Image.open("assets/character/mika-full-body.png") as image:
            self.assertEqual(image.size, (400, 1040))
            self.assertEqual(image.mode, "RGBA")
        html = companion_ui.portrait_html("Mika", "happy", view="Full body")
        self.assertIn("full-body-image", html)
        self.assertIn("head to toe", html)
        self.assertNotIn("portrait-blink", html)
        page.selectbox(key="character_view").select("Portrait").run()
        self.assertFalse(page.exception)

    def test_pin_and_movement_settings_preserve_chat(self):
        page = AppTest.from_file("app.py").run()
        self.assertTrue(page.checkbox(key="pin_character").value)
        self.assertEqual(page.selectbox(key="character_motion").value, "Gentle depth (2.5D)")
        page.chat_input[0].set_value("Hello").run()
        history = list(page.session_state.messages)
        page.checkbox(key="pin_character").uncheck().run()
        page.selectbox(key="character_motion").select("Still").run()
        self.assertEqual(page.session_state.messages, history)
        html = companion_ui.portrait_html("Mika", "happy", pinned=False, motion="Still")
        self.assertNotIn("pinned-character", html)
        self.assertIn("motion-still", html)
        self.assertNotIn('class="portrait-blink"', html)
        self.assertFalse(page.exception)

    def test_auto_scroll_is_triggered_by_messages_not_settings(self):
        with patch("companion_ui.scroll_to_latest") as scroll:
            page = AppTest.from_file("app.py").run()
            scroll.assert_not_called()
            page.chat_input[0].set_value("Hello Mika").run()
            event = page.session_state.scroll_event
            self.assertGreaterEqual(scroll.call_count, 2)
            self.assertEqual(scroll.call_args.args[0], event)
            page.text_input(key="companion_name").set_value("Nova").run()
            self.assertEqual(page.session_state.scroll_event, event)
            page.chat_input[0].set_value("How about a fun weekend?").run()
            self.assertNotEqual(page.session_state.scroll_event, event)
            self.assertFalse(page.exception)

    def test_mika_face_is_the_message_avatar(self):
        with Image.open(companion_ui.CHAT_AVATAR) as image:
            self.assertEqual(image.size, (256, 256))
        page = AppTest.from_file("app.py").run()
        self.assertNotIn("Chat icon", [item.label for item in page.selectbox])
        page.chat_input[0].set_value("Hello Mika").run()
        message = page.chat_message[-1]
        self.assertEqual(message.caption[0].value, "Mika")
        self.assertRegex(page.session_state.messages[-1]["time"], r"^\d{2}:\d{2}$")
        self.assertEqual(message.caption[-1].value, page.session_state.messages[-1]["time"])
        self.assertTrue(message.proto.avatar)
        self.assertIn("media/", message.proto.avatar)
        self.assertFalse(page.exception)

    def test_existing_session_provider_and_history_survive(self):
        page = AppTest.from_file("app.py")
        history = [{"role": "user", "content": "An existing message"},
                   {"role": "assistant", "content": "An existing reply"}]
        page.session_state["active_mode"] = app.LOCAL
        page.session_state["messages"] = history
        page.session_state["companion_name"] = "Existing name"
        page.session_state["ollama_model"] = local.DEFAULT_MODEL
        page.session_state["personality"] = "Playful"
        page.run()
        self.assertEqual(page.radio[0].value, app.LOCAL)
        self.assertEqual(page.session_state.messages, history)
        self.assertEqual(page.subheader[0].value, "Chat with Existing name")
        self.assertEqual(page.text_input(key="ollama_model").value, local.DEFAULT_MODEL)
        self.assertNotIn("Personality", [item.label for item in page.selectbox])
        self.assertFalse(page.exception)

    def test_portrait_assets_share_canvas_and_remove_labels(self):
        for expression in companion_ui.EXPRESSIONS:
            with Image.open(Path("assets/character") / f"mika-{expression}.png") as image:
                self.assertEqual(image.size, (420, 420))
                self.assertEqual(image.mode, "RGBA")
                self.assertEqual(image.getpixel((0, 0))[3], 0)
                # Labels begin below the shared shoulder cut; no alpha there.
                self.assertIsNone(image.getchannel("A").crop((0, 380, 420, 420)).getbbox())

    def test_download_and_consistent_personality(self):
        text = app.conversation_text([{"role": "user", "content": "Hello!"}], "Nova", app.LOCAL)
        self.assertIn("Nova (AI)", text)
        self.assertIn("You:\nHello!", text)
        self.assertNotIn("Personality:", text)
        system = app.companion_instructions("Nova")
        self.assertIn(app.PERSONALITY, system)
        self.assertIn("warm, playful, thoughtful, and supportive", system)
        self.assertIn("Nova", system)
        self.assertIn("You are an AI", system)
        self.assertEqual(app.reply_expression("I'm upset, please don't joke"), "happy")

    def test_old_demo_labels_are_cosmetic_and_disclosure_remains(self):
        text = "[Scripted demo reply] Hello!"
        self.assertEqual(app.chat_text(text, app.DEMO), "Hello!")
        self.assertEqual(app.chat_text(text, app.LOCAL), text)
        page = AppTest.from_file("app.py").run()
        self.assertTrue(any("virtual AI character" in c.value for c in page.caption))
        self.assertTrue(any("Demo · scripted replies" == c.value for c in page.caption))

    def test_blink_control_and_playful_response(self):
        with Image.open("assets/character/mika-blink.png") as image:
            self.assertEqual(image.size, (420, 420))
            self.assertEqual(image.mode, "RGBA")
        self.assertIn('class="portrait-blink"', companion_ui.portrait_html("Mika", "happy"))
        self.assertNotIn('class="portrait-blink"', companion_ui.portrait_html("Mika", "happy", False))
        self.assertNotIn('class="portrait-blink"', companion_ui.portrait_html("Mika", "thoughtful"))
        page = AppTest.from_file("app.py").run()
        page.selectbox(key="character_view").select("Portrait").run()
        page.checkbox(key="portrait_blinking").uncheck().run()
        page.chat_input[0].set_value("Let's imagine a fun weekend").run()
        self.assertEqual(page.session_state.portrait_expression, "playful")
        self.assertFalse(page.exception)


class OllamaClientTests(unittest.TestCase):
    def test_payload_and_history(self):
        history = [{"role": "user" if i % 2 == 0 else "assistant", "content": str(i)} for i in range(25)]
        with patch("ollama_local.request_json", side_effect=[MODELS, {"message": {"content": " Hello! "}}]) as request:
            self.assertEqual(local.chat_reply(history, "You are Nova, an AI.", local.DEFAULT_MODEL), "Hello!")
            payload = request.call_args.kwargs["payload"]
            self.assertEqual(payload["messages"][0]["content"], "You are Nova, an AI.")
            self.assertEqual(payload["messages"][-1], history[-1])
            self.assertLessEqual(len(payload["messages"]), 13)
            self.assertFalse(payload["stream"])
            self.assertEqual(payload["options"]["num_ctx"], 4096)

    def test_missing_and_cloud_models_never_generate(self):
        with patch("ollama_local.request_json", return_value={"models": []}) as request:
            with self.assertRaisesRegex(local.OllamaError, "ollama pull"):
                local.chat_reply([], "AI", "missing:1b")
            self.assertEqual(request.call_count, 1)
            with self.assertRaisesRegex(local.OllamaError, "Cloud"):
                local.chat_reply([], "AI", "gemma4:cloud")
            self.assertEqual(request.call_count, 1)

    def test_remote_models_excluded(self):
        with patch("ollama_local.request_json", return_value={"models": [
            {"name": "alias:latest", "remote_host": "https://ollama.com"},
            {"name": "model:cloud"}, {"name": local.DEFAULT_MODEL}]}):
            self.assertEqual(local.installed_models(), [local.DEFAULT_MODEL])

    def test_connection_timeout_and_loopback(self):
        for error, text in [(requests.ConnectionError(), "Cannot connect"), (requests.Timeout(), "too long")]:
            with self.subTest(error=error), patch("ollama_local.requests.Session") as factory:
                session = factory.return_value.__enter__.return_value
                session.request.side_effect = error
                with self.assertRaisesRegex(local.OllamaError, text):
                    local.request_json("GET", "/api/tags")
                self.assertFalse(session.trust_env)
                self.assertEqual(session.request.call_args.args[1], "http://localhost:11434/api/tags")
                self.assertFalse(session.request.call_args.kwargs["allow_redirects"])

    def test_missing_http_model_and_empty_reply(self):
        with patch("ollama_local.requests.Session") as factory:
            factory.return_value.__enter__.return_value.request.return_value.status_code = 404
            with self.assertRaisesRegex(local.OllamaError, "model is missing"):
                local.request_json("POST", "/api/chat")
        with patch("ollama_local.request_json", side_effect=[MODELS, {"message": {"content": ""}}]):
            with self.assertRaisesRegex(local.OllamaError, "no reply text"):
                local.chat_reply([{"role": "user", "content": "Hi"}], "AI", local.DEFAULT_MODEL)


if __name__ == "__main__":
    unittest.main()
