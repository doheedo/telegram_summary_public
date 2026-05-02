from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class CollectedMessage:
    chat_id: int
    chat_title: str
    message_id: int
    sender_name: str
    sent_at: datetime
    text: str


@dataclass(slots=True)
class ChatBatch:
    chat_id: int
    chat_title: str
    unread_count: int
    messages: list[CollectedMessage]


@dataclass(slots=True)
class ChatSummary:
    chat_title: str
    summary_text: str

