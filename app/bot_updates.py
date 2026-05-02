import argparse
import json

import httpx


def build_get_updates_url(bot_token: str) -> str:
    return f"https://api.telegram.org/bot{bot_token}/getUpdates"


def extract_private_chat_candidates(payload: dict) -> list[dict[str, str]]:
    seen_chat_ids: set[str] = set()
    candidates: list[dict[str, str]] = []

    for item in payload.get("result", []):
        message = item.get("message") or item.get("edited_message") or {}
        chat = message.get("chat") or {}
        if chat.get("type") != "private":
            continue

        chat_id = str(chat.get("id", "")).strip()
        if not chat_id or chat_id in seen_chat_ids:
            continue

        username = chat.get("username")
        first_name = chat.get("first_name") or ""
        last_name = chat.get("last_name") or ""
        full_name = f"{first_name} {last_name}".strip() or "Private chat"
        label = f"{full_name} (@{username})" if username else full_name

        seen_chat_ids.add(chat_id)
        candidates.append({"chat_id": chat_id, "label": label})

    return candidates


def fetch_private_chat_candidates(bot_token: str) -> list[dict[str, str]]:
    response = httpx.get(build_get_updates_url(bot_token), timeout=30.0)
    response.raise_for_status()
    payload = response.json()
    return extract_private_chat_candidates(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Find private Telegram chat ids from bot updates")
    parser.add_argument("--bot-token", required=True)
    args = parser.parse_args(argv)

    candidates = fetch_private_chat_candidates(bot_token=args.bot_token)
    print(json.dumps(candidates, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

