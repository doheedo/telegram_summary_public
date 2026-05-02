from html import escape

from app.models import ChatSummary


def build_digest(report_time_label: str, summaries: list[ChatSummary]) -> str:
    if not summaries:
        return "오늘은 요약할 새 안읽은 메시지가 없습니다."

    lines = [f"[{report_time_label} 기준 안읽은 메시지 요약]", ""]
    for item in summaries:
        summary_lines = [line.strip() for line in item.summary_text.splitlines() if line.strip()]
        lines.append(f"<b>[{escape(item.chat_title)}]</b>")
        lines.extend(f"\u2002\u2002{escape(line)}" for line in summary_lines)
    return "\n".join(lines)


def split_digest(digest: str, max_length: int = 3500) -> list[str]:
    if len(digest) <= max_length:
        return [digest]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in digest.splitlines():
        extra = len(line) + (1 if current else 0)
        if current and current_len + extra > max_length:
            chunks.append("\n".join(current))
            current = [line]
            current_len = len(line)
            continue

        current.append(line)
        current_len += extra

    if current:
        chunks.append("\n".join(current))

    return chunks
