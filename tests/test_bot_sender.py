from app.bot_sender import build_bot_api_url, send_digest
from app.summarizer import GroqSummarizerClient


def test_build_bot_api_url_uses_send_message_endpoint():
    url = build_bot_api_url("123:abc")

    assert url == "https://api.telegram.org/bot123:abc/sendMessage"


def test_groq_client_has_expected_model_name():
    client = GroqSummarizerClient(api_key="test-key")

    assert client.model_name == "llama-3.1-8b-instant"


def test_send_digest_uses_html_parse_mode(monkeypatch):
    captured = {}

    class StubResponse:
        def raise_for_status(self):
            return None

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return StubResponse()

    monkeypatch.setattr("app.bot_sender.httpx.post", fake_post)

    send_digest("123:abc", "999", "<b>[방]</b>\n&nbsp;&nbsp;1️⃣ 내용")

    assert captured["url"] == "https://api.telegram.org/bot123:abc/sendMessage"
    assert captured["json"]["parse_mode"] == "HTML"
    assert captured["json"]["chat_id"] == "999"
