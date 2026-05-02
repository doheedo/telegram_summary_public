from app.bot_updates import extract_private_chat_candidates


def test_extract_private_chat_candidates_returns_unique_private_chats():
    payload = {
        "ok": True,
        "result": [
            {
                "update_id": 1,
                "message": {
                    "chat": {
                        "id": 111,
                        "type": "private",
                        "username": "alpha_user",
                        "first_name": "Alpha",
                    }
                },
            },
            {
                "update_id": 2,
                "message": {
                    "chat": {
                        "id": 111,
                        "type": "private",
                        "username": "alpha_user",
                        "first_name": "Alpha",
                    }
                },
            },
            {
                "update_id": 3,
                "message": {
                    "chat": {
                        "id": -999,
                        "type": "group",
                        "title": "ignore-group",
                    }
                },
            },
        ],
    }

    candidates = extract_private_chat_candidates(payload)

    assert candidates == [
        {
            "chat_id": "111",
            "label": "Alpha (@alpha_user)",
        }
    ]


def test_extract_private_chat_candidates_handles_missing_result():
    assert extract_private_chat_candidates({"ok": True}) == []
