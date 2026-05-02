from datetime import datetime, timedelta, timezone

from app.collector import build_chat_batches, filter_allowlisted_dialogs, select_recent_unread_messages


class StubDialog:
    def __init__(self, dialog_id: int, title: str, unread_count: int):
        self.id = dialog_id
        self.title = title
        self.unread_count = unread_count
        self.entity = self


class StubMessage:
    def __init__(self, message_id: int, text: str, date: datetime):
        self.id = message_id
        self.message = text
        self.date = date


class StubTelegramClient:
    def __init__(self, dialogs=None, messages_by_dialog_id=None):
        self._dialogs = dialogs or []
        self._messages_by_dialog_id = messages_by_dialog_id or {}

    def iter_dialogs(self):
        return self._dialogs

    def iter_messages(self, entity, limit):
        return self._messages_by_dialog_id.get(entity.id, [])[:limit]


def test_filter_allowlisted_dialogs_matches_by_title_and_id():
    dialogs = [
        StubDialog(1, "팀채팅A", 2),
        StubDialog(2, "무시할방", 3),
    ]

    matched = filter_allowlisted_dialogs(dialogs, ["팀채팅A", "2"])

    assert [dialog.title for dialog in matched] == ["팀채팅A", "무시할방"]


def test_select_recent_unread_messages_keeps_only_last_unread_items():
    now = datetime(2026, 4, 21, 7, 0, tzinfo=timezone.utc)
    messages = [
        StubMessage(1, "오래된 메시지", now - timedelta(hours=30)),
        StubMessage(2, "최근 읽은 메시지", now - timedelta(hours=2)),
        StubMessage(3, "안읽은 첫 메시지", now - timedelta(hours=1)),
        StubMessage(4, "안읽은 둘째 메시지", now - timedelta(minutes=30)),
    ]

    selected = select_recent_unread_messages(messages, unread_count=2, now=now, lookback_hours=24)

    assert [message.id for message in selected] == [3, 4]


def test_build_chat_batches_returns_empty_list_for_no_matches():
    batches = build_chat_batches(
        telegram_client=StubTelegramClient(),
        allowed_chats=["팀채팅A"],
        now=datetime(2026, 4, 21, 7, 0, tzinfo=timezone.utc),
        lookback_hours=24,
        last_sent_message_ids={},
    )

    assert batches == []


def test_build_chat_batches_skips_messages_already_sent():
    dialog = StubDialog(1, "팀채팅A", 3)
    now = datetime(2026, 4, 21, 7, 0, tzinfo=timezone.utc)
    messages = [
        StubMessage(1, "오래된 안읽은", now - timedelta(hours=3)),
        StubMessage(2, "이미 보낸 안읽은", now - timedelta(hours=2)),
        StubMessage(3, "새 안읽은", now - timedelta(hours=1)),
    ]
    client = StubTelegramClient(dialogs=[dialog], messages_by_dialog_id={1: list(reversed(messages))})

    batches = build_chat_batches(
        telegram_client=client,
        allowed_chats=["팀채팅A"],
        now=now,
        lookback_hours=24,
        last_sent_message_ids={1: 2},
    )

    assert len(batches) == 1
    assert [message.message_id for message in batches[0].messages] == [3]
