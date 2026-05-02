from app.config import AppConfig
from app.main import build_summarizer_client
from app.summarizer import FallbackSummarizerClient, GroqSummarizerClient, NvidiaSummarizerClient


def test_build_summarizer_client_prefers_nvidia_then_groq():
    config = AppConfig(
        telegram_api_id=1,
        telegram_api_hash="hash",
        telegram_phone="+821012345678",
        telegram_session_name="tg_session",
        bot_token="bot-token",
        bot_chat_id="999",
        nvidia_api_key="nvidia-key",
        nvidia_model_name="openai/gpt-oss-120b",
        groq_api_key="groq-key",
        groq_model_name="llama-3.1-8b-instant",
        timezone_name="Asia/Seoul",
        summary_max_chars=100,
        lookback_hours=24,
        allowed_chats=[],
    )

    client = build_summarizer_client(config)

    assert isinstance(client, FallbackSummarizerClient)
    assert isinstance(client.clients[0], NvidiaSummarizerClient)
    assert isinstance(client.clients[1], GroqSummarizerClient)


def test_build_summarizer_client_uses_groq_only_without_nvidia_key():
    config = AppConfig(
        telegram_api_id=1,
        telegram_api_hash="hash",
        telegram_phone="+821012345678",
        telegram_session_name="tg_session",
        bot_token="bot-token",
        bot_chat_id="999",
        nvidia_api_key=None,
        nvidia_model_name="openai/gpt-oss-120b",
        groq_api_key="groq-key",
        groq_model_name="llama-3.1-8b-instant",
        timezone_name="Asia/Seoul",
        summary_max_chars=100,
        lookback_hours=24,
        allowed_chats=[],
    )

    client = build_summarizer_client(config)

    assert isinstance(client, GroqSummarizerClient)
