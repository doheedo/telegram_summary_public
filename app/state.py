import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class DeliveryState:
    last_sent_message_ids: dict[int, int]


def load_delivery_state(state_path: Path) -> DeliveryState:
    if not state_path.exists():
        return DeliveryState(last_sent_message_ids={})

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    return DeliveryState(
        last_sent_message_ids={int(key): int(value) for key, value in payload.get("last_sent_message_ids", {}).items()}
    )


def save_delivery_state(state_path: Path, state: DeliveryState) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_sent_message_ids": {str(key): value for key, value in state.last_sent_message_ids.items()}
    }
    state_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
