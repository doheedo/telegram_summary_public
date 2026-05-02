from datetime import datetime, timedelta

from app.models import ChatBatch, CollectedMessage


def filter_allowlisted_dialogs(dialogs, allowed_chats: list[str]):
    allowed = {str(item) for item in allowed_chats}
    return [
        dialog
        for dialog in dialogs
        if str(getattr(dialog, "id", "")) in allowed or getattr(dialog, "title", "") in allowed
    ]


def select_recent_unread_messages(messages, unread_count: int, now: datetime, lookback_hours: int):
    lower_bound = now - timedelta(hours=lookback_hours)
    recent = [
        message
        for message in messages
        if message.date >= lower_bound and getattr(message, "message", None)
    ]
    if unread_count <= 0:
        return []
    return recent[-unread_count:]


def _message_text(message) -> str:
    return str(getattr(message, "message", "") or getattr(message, "text", "") or "").strip()


def _sender_name(message) -> str:
    sender = getattr(message, "sender", None)
    if sender is not None:
        first_name = getattr(sender, "first_name", None) or ""
        last_name = getattr(sender, "last_name", None) or ""
        full_name = f"{first_name} {last_name}".strip()
        if full_name:
            return full_name
        username = getattr(sender, "username", None)
        if username:
            return username

    sender_id = getattr(message, "sender_id", None)
    return str(sender_id) if sender_id is not None else "unknown"
def build_chat_batches(
    telegram_client,
    allowed_chats: list[str],
    now: datetime,
    lookback_hours: int,
    last_sent_message_ids: dict[int, int],
) -> list[ChatBatch]:
    dialogs = list(telegram_client.iter_dialogs())
    matched_dialogs = filter_allowlisted_dialogs(dialogs, allowed_chats)
    batches: list[ChatBatch] = []

    for dialog in matched_dialogs:
        unread_count = int(getattr(dialog, "unread_count", 0) or 0)
        if unread_count <= 0:
            continue

        raw_messages = list(telegram_client.iter_messages(dialog.entity, limit=max(50, unread_count * 5)))
        raw_messages.reverse()
        selected_messages = select_recent_unread_messages(
            messages=raw_messages,
            unread_count=unread_count,
            now=now,
            lookback_hours=lookback_hours,
        )
        min_message_id = int(last_sent_message_ids.get(dialog.id, 0) or 0)

        collected_messages = [
            CollectedMessage(
                chat_id=dialog.id,
                chat_title=dialog.title,
                message_id=message.id,
                sender_name=_sender_name(message),
                sent_at=message.date,
                text=_message_text(message),
            )
            for message in selected_messages
            if _message_text(message) and message.id > min_message_id
        ]

        if not collected_messages:
            continue

        batches.append(
            ChatBatch(
                chat_id=dialog.id,
                chat_title=dialog.title,
                unread_count=unread_count,
                messages=collected_messages,
            )
        )

    return batches
