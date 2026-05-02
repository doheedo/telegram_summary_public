from app.reporter import build_digest, split_digest
from app.models import ChatSummary


def test_build_digest_includes_header_and_chat_lines():
    digest = build_digest(
        report_time_label="2026-04-21 07:00",
        summaries=[
            ChatSummary(chat_title="팀채팅A", summary_text="1️⃣ 배포 일정이 수요일로 미뤄졌습니다."),
            ChatSummary(chat_title="뉴스방B", summary_text="1️⃣ 금리 기사 세 건이 공유됐습니다."),
        ],
    )

    assert "[2026-04-21 07:00 기준 안읽은 메시지 요약]" in digest
    assert "<b>[팀채팅A]</b>" in digest
    assert "\u2002\u20021️⃣ 배포 일정이 수요일로 미뤄졌습니다." in digest
    assert "<b>[뉴스방B]</b>" in digest
    assert "\u2002\u20021️⃣ 금리 기사 세 건이 공유됐습니다." in digest


def test_build_digest_returns_default_message_when_empty():
    digest = build_digest(report_time_label="2026-04-21 07:00", summaries=[])

    assert digest == "오늘은 요약할 새 안읽은 메시지가 없습니다."


def test_split_digest_preserves_order_when_message_is_long():
    digest = "\n".join([f"- 방{i}: 요약" for i in range(50)])

    chunks = split_digest(digest, max_length=100)

    assert len(chunks) > 1
    assert chunks[0].startswith("- 방0")
    assert chunks[-1].endswith("요약")


def test_build_digest_formats_multiline_chat_summary():
    digest = build_digest(
        report_time_label="2026-04-22 08:22",
        summaries=[
            ChatSummary(
                chat_title="퀄리티기업연구소",
                summary_text="1️⃣ 가치투자 원칙 공유\n2️⃣ ROIC와 자본회전율 분석",
            )
        ],
    )

    assert "<b>[퀄리티기업연구소]</b>" in digest
    assert "\u2002\u20021️⃣ 가치투자 원칙 공유" in digest
    assert "\u2002\u20022️⃣ ROIC와 자본회전율 분석" in digest


def test_build_digest_escapes_html_in_titles_and_summaries():
    digest = build_digest(
        report_time_label="2026-04-22 08:22",
        summaries=[
            ChatSummary(
                chat_title="A&B<test>",
                summary_text="1️⃣ EPS < 예상 & 가이던스 > 상향",
            )
        ],
    )

    assert "<b>[A&amp;B&lt;test&gt;]</b>" in digest
    assert "\u2002\u20021️⃣ EPS &lt; 예상 &amp; 가이던스 &gt; 상향" in digest
