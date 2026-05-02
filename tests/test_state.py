from pathlib import Path

from app.state import DeliveryState, load_delivery_state, save_delivery_state


def test_load_delivery_state_returns_empty_when_missing(tmp_path: Path):
    state = load_delivery_state(tmp_path / "missing.json")

    assert state == DeliveryState(last_sent_message_ids={})


def test_save_delivery_state_persists_message_ids(tmp_path: Path):
    state_path = tmp_path / "delivery_state.json"
    save_delivery_state(state_path, DeliveryState(last_sent_message_ids={1: 10, 2: 20}))

    reloaded = load_delivery_state(state_path)

    assert reloaded.last_sent_message_ids == {1: 10, 2: 20}
