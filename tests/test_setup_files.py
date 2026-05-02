from pathlib import Path

from app.setup_files import render_allowed_chats_yaml, render_env_file, write_setup_files


def test_render_env_file_includes_expected_keys():
    content = render_env_file(
        telegram_api_id="12345",
        telegram_api_hash="hash-value",
        telegram_phone="+821012345678",
        telegram_session_name="tg_session",
        bot_token="bot-token",
        bot_chat_id="999",
        nvidia_api_key="nvidia-key",
        nvidia_model_name="deepseek-ai/deepseek-v4-pro",
        groq_api_key="groq-key",
        timezone_name="Asia/Seoul",
        summary_max_chars=1000,
        lookback_hours=24,
    )

    assert "TG_API_ID=12345" in content
    assert "BOT_TOKEN=bot-token" in content
    assert "NVIDIA_API_KEY=nvidia-key" in content
    assert "NVIDIA_MODEL_NAME=deepseek-ai/deepseek-v4-pro" in content
    assert "TIMEZONE=Asia/Seoul" in content


def test_render_allowed_chats_yaml_lists_every_chat():
    content = render_allowed_chats_yaml(["팀채팅A", "1234567890"])

    assert "allowed_chats:" in content
    assert '  - "팀채팅A"' in content
    assert '  - "1234567890"' in content


def test_write_setup_files_creates_env_and_chat_files(tmp_path: Path):
    env_path = tmp_path / ".env"
    chats_path = tmp_path / "chats.yaml"

    write_setup_files(
        env_path=env_path,
        chats_path=chats_path,
        telegram_api_id="12345",
        telegram_api_hash="hash-value",
        telegram_phone="+821012345678",
        telegram_session_name="tg_session",
        bot_token="bot-token",
        bot_chat_id="999",
        nvidia_api_key="nvidia-key",
        nvidia_model_name="deepseek-ai/deepseek-v4-pro",
        groq_api_key="groq-key",
        timezone_name="Asia/Seoul",
        summary_max_chars=1000,
        lookback_hours=24,
        allowed_chats=["팀채팅A", "1234567890"],
    )

    assert env_path.exists()
    assert chats_path.exists()
    assert "TG_API_HASH=hash-value" in env_path.read_text(encoding="utf-8")
    assert "NVIDIA_API_KEY=nvidia-key" in env_path.read_text(encoding="utf-8")
    assert '  - "팀채팅A"' in chats_path.read_text(encoding="utf-8")
