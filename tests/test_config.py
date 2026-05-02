from pathlib import Path

import pytest

from app.config import AppConfig, load_config


def test_load_config_reads_env_and_allowlist(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "TG_API_ID=12345",
                "TG_API_HASH=hash-value",
                "TG_PHONE=+821012345678",
                "TG_SESSION_NAME=tg_session",
                "BOT_TOKEN=bot-token",
                "BOT_CHAT_ID=999",
                "NVIDIA_API_KEY=nvidia-key",
                "GROQ_API_KEY=groq-key",
                "TIMEZONE=Asia/Seoul",
                "SUMMARY_MAX_CHARS=1000",
            ]
        ),
        encoding="utf-8",
    )
    chats_file = tmp_path / "chats.yaml"
    chats_file.write_text("allowed_chats:\n  - 팀채팅A\n  - 1234567890\n", encoding="utf-8")

    config = load_config(env_file=env_file, chats_file=chats_file)

    assert isinstance(config, AppConfig)
    assert config.telegram_api_id == 12345
    assert config.allowed_chats == ["팀채팅A", "1234567890"]
    assert config.nvidia_api_key == "nvidia-key"
    assert config.nvidia_model_name == "deepseek-ai/deepseek-v4-pro"
    assert config.summary_max_chars == 1000


def test_load_config_raises_for_missing_secret(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("TG_API_ID=12345\n", encoding="utf-8")
    chats_file = tmp_path / "chats.yaml"
    chats_file.write_text("allowed_chats: []\n", encoding="utf-8")

    with pytest.raises(ValueError, match="TG_API_HASH"):
        load_config(env_file=env_file, chats_file=chats_file)


def test_load_config_allows_missing_nvidia_key(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "TG_API_ID=12345",
                "TG_API_HASH=hash-value",
                "TG_PHONE=+821012345678",
                "TG_SESSION_NAME=tg_session",
                "BOT_TOKEN=bot-token",
                "BOT_CHAT_ID=999",
                "GROQ_API_KEY=groq-key",
            ]
        ),
        encoding="utf-8",
    )
    chats_file = tmp_path / "chats.yaml"
    chats_file.write_text("allowed_chats: []\n", encoding="utf-8")

    config = load_config(env_file=env_file, chats_file=chats_file)

    assert config.nvidia_api_key is None
    assert config.groq_api_key == "groq-key"
