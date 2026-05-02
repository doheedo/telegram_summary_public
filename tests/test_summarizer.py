from datetime import datetime, timezone

from app.models import ChatBatch, CollectedMessage
from app.summarizer import (
    FallbackSummarizerClient,
    GroqSummarizerClient,
    NvidiaSummarizerClient,
    build_summary_prompt,
    summarize_chat_batch,
)


class StubGroqClient:
    def __init__(self, payload: str):
        self.payload = payload
        self.last_prompt = ""

    def create_summary(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.payload


class FailingClient:
    def create_summary(self, prompt: str) -> str:
        raise RuntimeError("provider failed")


class StubResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"choices": [{"message": {"content": "요약"}}]}


def test_build_summary_prompt_includes_messages_and_limit():
    batch = ChatBatch(
        chat_id=1,
        chat_title="팀채팅A",
        unread_count=2,
        messages=[
            CollectedMessage(
                chat_id=1,
                chat_title="팀채팅A",
                message_id=10,
                sender_name="alice",
                sent_at=datetime(2026, 4, 21, 6, 0, tzinfo=timezone.utc),
                text="배포는 수요일입니다.",
            )
        ],
    )

    prompt = build_summary_prompt(batch=batch, summary_max_chars=100)

    assert "항상 한국어" in prompt
    assert "100자 안팎" in prompt
    assert "#Person1#: 배포는 수요일입니다." in prompt
    assert "등장인물 매핑" in prompt


def test_summarize_chat_batch_trims_whitespace():
    batch = ChatBatch(chat_id=1, chat_title="팀채팅A", unread_count=1, messages=[])
    client = StubGroqClient("  배포 일정이 수요일로 조정됐습니다.  ")

    summary = summarize_chat_batch(batch=batch, summary_max_chars=100, summarizer_client=client)

    assert summary.chat_title == "팀채팅A"
    assert summary.summary_text == "1️⃣ 배포 일정이 수요일로 조정됐습니다."


def test_stub_client_receives_prompt_text():
    batch = ChatBatch(chat_id=1, chat_title="팀채팅A", unread_count=1, messages=[])
    client = StubGroqClient("요약")

    summarize_chat_batch(batch=batch, summary_max_chars=100, summarizer_client=client)

    assert "채팅방: 팀채팅A" in client.last_prompt


def test_build_summary_prompt_reuses_same_person_label_for_same_sender():
    batch = ChatBatch(
        chat_id=1,
        chat_title="팀채팅A",
        unread_count=2,
        messages=[
            CollectedMessage(1, "팀채팅A", 10, "alice", datetime(2026, 4, 21, 6, 0, tzinfo=timezone.utc), "첫 메시지"),
            CollectedMessage(1, "팀채팅A", 11, "alice", datetime(2026, 4, 21, 6, 5, tzinfo=timezone.utc), "둘째 메시지"),
        ],
    )

    prompt = build_summary_prompt(batch=batch, summary_max_chars=100)

    assert "#Person1#: 첫 메시지" in prompt
    assert "#Person1#: 둘째 메시지" in prompt


def test_build_summary_prompt_instructs_digest_and_filters_noise_lines():
    batch = ChatBatch(
        chat_id=1,
        chat_title="퀄리티기업연구소",
        unread_count=1,
        messages=[
            CollectedMessage(
                1,
                "퀄리티기업연구소",
                10,
                "alice",
                datetime(2026, 4, 22, 7, 0, tzinfo=timezone.utc),
                "3\nhttps://youtu.be/example\nGE 에어로스페이스 실적이 예상치를 상회했습니다.\n1",
            )
        ],
    )

    prompt = build_summary_prompt(batch=batch, summary_max_chars=100)

    assert "채팅방 전체의 흐름" in prompt
    assert "2~4개 bullet" in prompt
    assert "https://youtu.be/example" not in prompt
    assert "#Person1#: GE 에어로스페이스 실적이 예상치를 상회했습니다." in prompt


def test_build_summary_prompt_requests_fact_focused_topic_bullets():
    batch = ChatBatch(
        chat_id=1,
        chat_title="퀄리티기업연구소",
        unread_count=2,
        messages=[
            CollectedMessage(
                1,
                "퀄리티기업연구소",
                10,
                "alice",
                datetime(2026, 4, 22, 7, 0, tzinfo=timezone.utc),
                "GE Aerospace 1분기 매출과 EPS가 예상치를 상회했습니다.",
            ),
            CollectedMessage(
                1,
                "퀄리티기업연구소",
                11,
                "bob",
                datetime(2026, 4, 22, 7, 5, tzinfo=timezone.utc),
                "SpaceX의 Cursor 인수설과 S-1 재무 수치가 공유됐습니다.",
            ),
        ],
    )

    prompt = build_summary_prompt(batch=batch, summary_max_chars=100)

    assert "채팅방이나 커뮤니티의 성격을 소개하는 일반론 문장은 금지합니다." in prompt
    assert "기업명, 분기, 예상 상회/하회" in prompt
    assert "맥락이 다른 주제는 bullet을 분리하세요." in prompt


def test_build_summary_prompt_truncates_each_message_to_400_chars():
    long_text = "가" * 700
    batch = ChatBatch(
        chat_id=1,
        chat_title="긴글방",
        unread_count=1,
        messages=[
            CollectedMessage(
                1,
                "긴글방",
                10,
                "alice",
                datetime(2026, 4, 22, 7, 0, tzinfo=timezone.utc),
                long_text,
            )
        ],
    )

    prompt = build_summary_prompt(batch=batch, summary_max_chars=100)

    assert f"#Person1#: {'가' * 400}" in prompt
    assert f"#Person1#: {'가' * 401}" not in prompt


def test_build_summary_prompt_caps_total_conversation_text_at_10000_chars():
    body = "나" * 400
    batch = ChatBatch(
        chat_id=1,
        chat_title="긴글방",
        unread_count=40,
        messages=[
            CollectedMessage(
                1,
                "긴글방",
                index,
                "alice",
                datetime(2026, 4, 22, 7, 0, tzinfo=timezone.utc),
                body,
            )
            for index in range(1, 41)
        ],
    )

    prompt = build_summary_prompt(batch=batch, summary_max_chars=100)
    conversation_section = prompt.split("메시지:\n", 1)[1]

    assert len(conversation_section) <= 10000


def test_summarize_chat_batch_normalizes_bullet_output():
    batch = ChatBatch(chat_id=1, chat_title="팀채팅A", unread_count=1, messages=[])
    client = StubGroqClient(
        '  1. "가치투자 원칙 공유"\n2. "ROIC와 자본회전율 분석"\n3. "SpaceX와 Cursor 인수설"\n4. "Anthropic 가격 정책 변경 언급"\n5. "초과 줄"  '
    )

    summary = summarize_chat_batch(batch=batch, summary_max_chars=30, summarizer_client=client)

    assert summary.summary_text.splitlines() == [
        "1️⃣ 가치투자 원칙 공유",
        "2️⃣ ROIC와 자본회전율 분석",
        "3️⃣ SpaceX와 Cursor 인수설",
        "4️⃣ Anthropic 가격 정책 변경 언급",
    ]


def test_summarize_chat_batch_drops_generic_intro_bullets():
    batch = ChatBatch(chat_id=1, chat_title="퀄리티기업연구소", unread_count=1, messages=[])
    client = StubGroqClient(
        "\n".join(
            [
                "• 퀄리티기업연구소는 주식 시장에 대한 관심있는 주제와 분석에 초점을 두고 있습니다.",
                "• GE Aerospace: 1분기 매출과 EPS가 예상치를 상회했습니다.",
                "• UNH: 매출과 조정 EPS가 예상치를 웃돌고 연간 가이던스를 상향했습니다.",
            ]
        )
    )

    summary = summarize_chat_batch(batch=batch, summary_max_chars=120, summarizer_client=client)

    assert summary.summary_text.splitlines() == [
        "1️⃣ GE Aerospace: 1분기 매출과 EPS가 예상치를 상회했습니다.",
        "2️⃣ UNH: 매출과 조정 EPS가 예상치를 웃돌고 연간 가이던스를 상향했습니다.",
    ]


def test_summarize_chat_batch_filters_broader_chat_intro_patterns():
    batch = ChatBatch(chat_id=1, chat_title="리서치방", unread_count=1, messages=[])
    client = StubGroqClient(
        "\n".join(
            [
                "• 이 채팅방은 주식과 거시경제 관련 내용을 다룹니다.",
                "• TSMC: 2분기 매출 전망이 시장 기대를 상회했습니다.",
            ]
        )
    )

    summary = summarize_chat_batch(batch=batch, summary_max_chars=120, summarizer_client=client)

    assert summary.summary_text.splitlines() == [
        "1️⃣ TSMC: 2분기 매출 전망이 시장 기대를 상회했습니다.",
    ]


def test_summarize_chat_batch_unescapes_html_entities_from_llm_output():
    batch = ChatBatch(chat_id=1, chat_title="팀채팅A", unread_count=1, messages=[])
    client = StubGroqClient("1. EPS &lt; 예상 &amp; 가이던스 &gt; 상향")

    summary = summarize_chat_batch(batch=batch, summary_max_chars=120, summarizer_client=client)

    assert summary.summary_text == "1️⃣ EPS < 예상 & 가이던스 > 상향"


def test_nvidia_client_has_expected_model_name():
    client = NvidiaSummarizerClient(api_key="test-key")

    assert client.model_name == "deepseek-ai/deepseek-v4-pro"


def test_groq_client_has_expected_model_name():
    client = GroqSummarizerClient(api_key="test-key")

    assert client.model_name == "llama-3.1-8b-instant"


def test_fallback_client_uses_secondary_when_primary_fails():
    client = FallbackSummarizerClient([FailingClient(), StubGroqClient("보조 요약")])

    assert client.create_summary("프롬프트") == "보조 요약"


def test_nvidia_client_waits_to_respect_40_rpm(monkeypatch):
    client = NvidiaSummarizerClient(api_key="test-key")
    monotonic_values = iter([100.0, 101.0])
    sleep_calls: list[float] = []

    monkeypatch.setattr("app.summarizer.time.monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr("app.summarizer.time.sleep", sleep_calls.append)
    monkeypatch.setattr("app.summarizer.httpx.post", lambda *args, **kwargs: StubResponse())

    client.create_summary("첫 호출")
    client.create_summary("두 번째 호출")

    assert sleep_calls == [0.5]


def test_groq_client_waits_to_respect_30_rpm(monkeypatch):
    client = GroqSummarizerClient(api_key="test-key")
    monotonic_values = iter([100.0, 100.0, 101.0, 101.0])
    sleep_calls: list[float] = []

    monkeypatch.setattr("app.summarizer.time.monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr("app.summarizer.time.sleep", sleep_calls.append)
    monkeypatch.setattr("app.summarizer.httpx.post", lambda *args, **kwargs: StubResponse())

    client.create_summary("첫 호출")
    client.create_summary("두 번째 호출")

    assert sleep_calls == [1.0]
