from app.conversation import ConversationManager


def test_session_stores_conversation_history():
    manager = ConversationManager()

    manager.add_turn(
        "session-1",
        "user",
        "Do you ship internationally?",
    )

    manager.add_turn(
        "session-1",
        "assistant",
        "Yes, Canada is currently supported.",
    )

    history = manager.get_recent_history(
        "session-1"
    )

    assert len(history) == 2
    assert history[0].content == (
        "Do you ship internationally?"
    )


def test_session_stores_active_order():
    manager = ConversationManager()

    manager.set_order(
        "session-1",
        "ORD-1007",
    )

    assert manager.get_order(
        "session-1"
    ) == "ORD-1007"


def test_sessions_are_isolated():
    manager = ConversationManager()

    manager.set_order(
        "session-1",
        "ORD-1007",
    )

    manager.set_order(
        "session-2",
        "ORD-1010",
    )

    assert manager.get_order(
        "session-1"
    ) == "ORD-1007"

    assert manager.get_order(
        "session-2"
    ) == "ORD-1010"


def test_session_stores_last_topic():
    manager = ConversationManager()

    manager.set_topic(
        "session-1",
        "international_shipping",
    )

    assert manager.get_topic(
        "session-1"
    ) == "international_shipping"


def test_history_is_limited():
    manager = ConversationManager(
        max_turns=3
    )

    for number in range(5):
        manager.add_turn(
            "session-1",
            "user",
            f"Message {number}",
        )

    history = manager.get_recent_history(
        "session-1"
    )

    assert len(history) == 3
    assert history[0].content == "Message 2"
    assert history[-1].content == "Message 4"