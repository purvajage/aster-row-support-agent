from app.context_resolver import resolve_context
from app.conversation import ConversationManager


def test_explicit_order_id_is_saved():
    manager = ConversationManager()

    result = resolve_context(
        manager,
        "session-1",
        "Where is ORD-1007?",
    )

    assert result["order_id"] == "ORD-1007"
    assert (
        result["retrieval_query"]
        == "Where is ORD-1007?"
    )


def test_order_follow_up_uses_active_order():
    manager = ConversationManager()

    resolve_context(
        manager,
        "session-1",
        "Where is ORD-1007?",
    )

    result = resolve_context(
        manager,
        "session-1",
        "When will it arrive?",
    )

    assert result["order_id"] == "ORD-1007"
    assert "ORD-1007" in result["retrieval_query"]
    assert "When will it arrive?" in result["retrieval_query"]


def test_topic_follow_up_uses_previous_topic():
    manager = ConversationManager()

    manager.set_topic(
        "session-1",
        "international shipping",
    )

    result = resolve_context(
        manager,
        "session-1",
        "What about Canada?",
    )

    assert (
        result["topic"]
        == "international shipping"
    )

    assert (
        result["retrieval_query"]
        == "international shipping: What about Canada?"
    )


def test_explicit_new_order_replaces_previous_order():
    manager = ConversationManager()

    resolve_context(
        manager,
        "session-1",
        "Where is ORD-1007?",
    )

    result = resolve_context(
        manager,
        "session-1",
        "What about ORD-1010?",
    )

    assert result["order_id"] == "ORD-1010"


def test_sessions_do_not_share_order_context():
    manager = ConversationManager()

    resolve_context(
        manager,
        "session-1",
        "Where is ORD-1007?",
    )

    result = resolve_context(
        manager,
        "session-2",
        "When will it arrive?",
    )

    assert result["order_id"] is None
    assert (
        result["retrieval_query"]
        == "When will it arrive?"
    )