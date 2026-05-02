import httpx


def build_bot_api_url(bot_token: str) -> str:
    return f"https://api.telegram.org/bot{bot_token}/sendMessage"


def send_digest(bot_token: str, bot_chat_id: str, message_text: str) -> None:
    response = httpx.post(
        build_bot_api_url(bot_token),
        json={"chat_id": bot_chat_id, "text": message_text, "parse_mode": "HTML"},
        timeout=30.0,
    )
    response.raise_for_status()

