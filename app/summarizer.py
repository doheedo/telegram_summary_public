import html
import httpx
import logging
import re
import threading
import time
from typing import Protocol

from app.models import ChatBatch, ChatSummary

LOGGER = logging.getLogger(__name__)

MESSAGE_CHAR_LIMIT = 400
CHAT_PROMPT_CHAR_LIMIT = 10_000
DEFAULT_MAX_COMPLETION_TOKENS = 1024
NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


class SummarizerClient(Protocol):
    def create_summary(self, prompt: str) -> str: ...


class OpenAICompatibleSummarizerClient:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        requests_per_minute: float,
        *,
        max_completion_tokens: int = DEFAULT_MAX_COMPLETION_TOKENS,
        timeout_seconds: float = 30.0,
        tokens_per_minute: int = 0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.requests_per_minute = max(float(requests_per_minute), 1.0)
        self.max_completion_tokens = max(256, int(max_completion_tokens))
        self.timeout_seconds = max(10.0, float(timeout_seconds))
        self.tokens_per_minute = max(0, int(tokens_per_minute))
        self._min_request_interval_seconds = 60.0 / self.requests_per_minute
        self._rate_limit_lock = threading.Lock()
        self._last_request_at: float | None = None
        self._token_window_start: float | None = None
        self._token_window_used = 0

    def _wait_for_rate_limit_slot(self) -> None:
        with self._rate_limit_lock:
            now = time.monotonic()
            if self._last_request_at is not None:
                elapsed = now - self._last_request_at
                remaining = self._min_request_interval_seconds - elapsed
                if remaining > 0:
                    time.sleep(remaining)
                    now += remaining
            self._last_request_at = now

    def _estimate_tokens_for_text(self, text: str) -> int:
        return max(32, len(text) // 4)

    def _wait_for_token_limit_slot(self, tokens_for_call: int) -> None:
        if self.tokens_per_minute <= 0 or tokens_for_call <= 0:
            return
        with self._rate_limit_lock:
            now = time.monotonic()
            if self._token_window_start is None or now - self._token_window_start >= 60.0:
                self._token_window_start = now
                self._token_window_used = 0
            if self._token_window_used + tokens_for_call > self.tokens_per_minute:
                wait_seconds = 60.0 - (now - self._token_window_start)
                if wait_seconds > 0:
                    time.sleep(max(0.05, wait_seconds))
                self._token_window_start = time.monotonic()
                self._token_window_used = 0
            self._token_window_used += tokens_for_call

    def create_summary(self, prompt: str) -> str:
        self._wait_for_rate_limit_slot()
        self._wait_for_token_limit_slot(
            self._estimate_tokens_for_text(prompt) + self.max_completion_tokens
        )
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model_name,
                "temperature": 0.6,
                "max_tokens": self.max_completion_tokens,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "당신은 텔레그램 채팅방 다이제스트 작성기다. "
                            "항상 한국어로만 답하고, 최종 bullet digest를 출력하라. "
                            "특정 메시지 하나를 길게 풀어쓰지 말고 채팅방 전체 흐름을 주제별로 압축하라. "
                            "채팅방이나 커뮤니티 소개 같은 일반론은 쓰지 말고, 기업명·실적·예상 상회/하회·가이던스·핵심 이벤트 같은 "
                            "구체적인 사실을 우선 bullet로 정리하라."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        message = payload["choices"][0]["message"]
        raw_content = message.get("content", "") or ""
        
        # Remove <think>...</think> blocks from content (CoT)
        raw_content = re.sub(r"<think>.*?</think>", "", raw_content, flags=re.DOTALL).strip()
        
        return html.unescape(raw_content)


class NvidiaSummarizerClient(OpenAICompatibleSummarizerClient):
    def __init__(
        self,
        api_key: str,
        model_name: str = "deepseek-ai/deepseek-v4-pro",
        requests_per_minute: float = 40.0,
    ):
        super().__init__(
            api_key=api_key,
            base_url="https://integrate.api.nvidia.com/v1",
            model_name=model_name,
            requests_per_minute=requests_per_minute,
            timeout_seconds=120.0,
        )


class GroqSummarizerClient(OpenAICompatibleSummarizerClient):
    def __init__(
        self,
        api_key: str,
        model_name: str = "llama-3.1-8b-instant",
        requests_per_minute: float = 30.0,
        tokens_per_minute: int = 10_000,
    ):
        super().__init__(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
            model_name=model_name,
            requests_per_minute=requests_per_minute,
            tokens_per_minute=tokens_per_minute,
        )


class FallbackSummarizerClient:
    def __init__(self, clients: list[SummarizerClient]):
        if not clients:
            raise ValueError("At least one summarizer client is required.")
        self.clients = clients

    def create_summary(self, prompt: str) -> str:
        last_error: Exception | None = None
        for client in self.clients:
            try:
                return client.create_summary(prompt)
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning("Summarizer client %s failed: %s", client.__class__.__name__, exc)
                last_error = exc
        if last_error is not None:
            raise last_error
        raise RuntimeError("No summarizer client available.")


def _sanitize_message_text(text: str) -> str:
    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.fullmatch(r"https?://\S+", line):
            continue
        if re.fullmatch(r"[\d\s]+", line):
            continue
        if re.fullmatch(r"[✦✧☆★•\-\_=~🧘✅🟢🔹🔸]+", line):
            continue
        cleaned_lines.append(line)

    return " ".join(cleaned_lines).strip()


_GENERIC_INTRO_PATTERNS = re.compile(
    r"(?:"
    r"이\s*채팅방은"
    r"|이\s*방은"
    r"|채팅방[은이]?\s*(?:주식|투자|경제|금융|시장)"
    r"|채팅(?:방)?(?:은|이)?\s*(?:대한|관한|관련)"
    r"|논의\s*중인\s*주제는\s*다음과\s*같습니다"
    r"|관심\s*있(?:는)?\s*주제와\s*분석에\s*초점을\s*두고\s*있습니다"
    r")",
    re.IGNORECASE,
)


def _looks_like_generic_intro(line: str) -> bool:
    return bool(_GENERIC_INTRO_PATTERNS.search(line))


def _normalize_summary_text(summary_text: str, summary_max_chars: int) -> str:
    summary_text = html.unescape(summary_text)
    raw_lines = [line.strip() for line in summary_text.splitlines() if line.strip()]
    normalized_lines: list[str] = []

    for raw_line in raw_lines:
        line = raw_line.strip()
        line = re.sub(r"^\s*(?:[-•*]|\d+[.)])\s*", "", line)
        line = line.strip("\"'“”")
        line = " ".join(line.split()).strip()
        if not line:
            continue
        if _looks_like_generic_intro(line):
            continue
        if len(line) > summary_max_chars:
            line = line[:summary_max_chars].rstrip(" ,;:") + "…"
        normalized_lines.append(line)

    if not normalized_lines:
        fallback = " ".join(summary_text.split()).strip().strip("\"'“”")
        if len(fallback) > summary_max_chars:
            fallback = fallback[:summary_max_chars].rstrip(" ,;:") + "…"
        return f"1️⃣ {fallback}" if fallback else "1️⃣ 새로 요약할 실질 메시지가 없습니다."

    return "\n".join(
        f"{NUMBER_EMOJIS[index]} {line}"
        for index, line in enumerate(normalized_lines[:4])
    )


def build_summary_prompt(batch: ChatBatch, summary_max_chars: int) -> str:
    speaker_labels: dict[str, str] = {}
    conversation_lines: list[str] = []
    remaining_chars = CHAT_PROMPT_CHAR_LIMIT

    for message in batch.messages:
        sender_name = message.sender_name.strip() or "unknown"
        sanitized_text = _sanitize_message_text(message.text)
        if not sanitized_text:
            continue
        truncated_text = sanitized_text[:MESSAGE_CHAR_LIMIT]
        if sender_name not in speaker_labels:
            speaker_labels[sender_name] = f"#Person{len(speaker_labels) + 1}#"
        line = f"{speaker_labels[sender_name]}: {truncated_text}"
        line_length = len(line) + 1
        if remaining_chars < line_length:
            if not conversation_lines:
                conversation_lines.append(line[: max(0, remaining_chars - 1)])
            break
        conversation_lines.append(line)
        remaining_chars -= line_length

    lines = [
        "다음 텔레그램 안읽은 메시지를 항상 한국어로 요약하세요.",
        "이 작업은 특정 메시지 하나의 요약이 아니라 채팅방 전체의 흐름을 요약하는 작업입니다.",
        "출력은 2~4개 bullet로 제한하세요.",
        f"출력은 주요 주제별로 bullet 형식으로 작성하고, 각 bullet은 {summary_max_chars}자 안팎으로 유지하세요.",
        "여러 주제가 있으면 핵심 주제들을 모두 누락 없이 압축해 bullet로 나누세요.",
        "링크, 숫자 카운터, 홍보 문구, 반복 장식 문자는 무시하세요.",
        "특정 메시지 하나를 길게 재서술하지 말고, 방 전체에서 반복되거나 중요한 주제만 남기세요.",
        "채팅방이나 커뮤니티의 성격을 소개하는 일반론 문장은 금지합니다.",
        "기업명, 분기, 예상 상회/하회, 가이던스 변화, 인수설, 핵심 수치 같은 구체적인 사실을 우선 적으세요.",
        "맥락이 다른 주제는 bullet을 분리하세요.",
        "최종 요약을 bullet 형식으로 깔끔하게 출력하세요.",
        f"채팅방: {batch.chat_title}",
        "등장인물 매핑:",
    ]
    lines.extend(f"- {label} = {name}" for name, label in speaker_labels.items())
    lines.extend(
        [
        "메시지:",
        *conversation_lines,
        ]
    )
    return "\n".join(lines)


def summarize_chat_batch(batch: ChatBatch, summary_max_chars: int, summarizer_client: SummarizerClient) -> ChatSummary:
    prompt = build_summary_prompt(batch=batch, summary_max_chars=summary_max_chars)
    summary_text = _normalize_summary_text(summarizer_client.create_summary(prompt), summary_max_chars)
    return ChatSummary(chat_title=batch.chat_title, summary_text=summary_text)
