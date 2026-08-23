import re

from app.conversation import ConversationManager


FOLLOW_UP_PHRASES = {
    "what about",
    "how about",
    "and what about",
    "what about that",
    "what about it",
    "when will it arrive",
    "when will it get here",
    "when does it arrive",
    "when should it arrive",
    "how long will it take",
    "what about this",
}


def _contains_follow_up_language(message: str) -> bool:
    """Detect common short follow-up phrases."""
    normalized = message.lower().strip()

    return any(
        phrase in normalized
        for phrase in FOLLOW_UP_PHRASES
    )


def _extract_order_id(message: str) -> str | None:
    """Extract an explicit order ID from a user message."""
    match = re.search(
        r"\bORD-\d{4}\b",
        message.upper(),
    )

    if match:
        return match.group(0)

    return None


def resolve_context(
    manager: ConversationManager,
    session_id: str,
    message: str,
) -> dict[str, str | None]:
    """
    Resolve useful context for the current user message.

    Returns:
        order_id:
            Explicitly supplied order ID, or the active session order.
        topic:
            Current or previous topic.
        retrieval_query:
            Query suitable for the retrieval layer.
    """
    explicit_order_id = _extract_order_id(message)

    if explicit_order_id:
        manager.set_order(
            session_id,
            explicit_order_id,
        )

    active_order_id = manager.get_order(
        session_id
    )

    previous_topic = manager.get_topic(
        session_id
    )

    retrieval_query = message

    # Follow-up about an existing order.
    if (
        _contains_follow_up_language(message)
        and active_order_id
    ):
        retrieval_query = (
            f"Order {active_order_id}: "
            f"{message}"
        )

    # Follow-up to a previous non-order topic.
    elif (
        _contains_follow_up_language(message)
        and previous_topic
    ):
        retrieval_query = (
            f"{previous_topic}: "
            f"{message}"
        )

    return {
        "order_id": active_order_id,
        "topic": previous_topic,
        "retrieval_query": retrieval_query,
    }