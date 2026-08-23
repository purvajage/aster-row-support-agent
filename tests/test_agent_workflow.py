from app.agent_workflow import run_workflow
from app.agent import SupportAgent
from app.conversation import ConversationManager


def test_order_id_alone_routes_to_order_tool():
    manager = ConversationManager()

    result = run_workflow(
        manager,
        "session-1",
        "Where is ORD-1007?",
    )

    assert result.action == "order_lookup"
    assert result.order_id == "ORD-1007"
    assert result.tool_called is True


def test_valid_order_gets_customer_safe_response():
    manager = ConversationManager()

    result = run_workflow(
        manager,
        "session-1",
        "Where is ORD-1007?",
    )

    assert result.answer is not None
    assert "ORD-1007" in result.answer
    assert "shipped" in result.answer.lower()
    assert "UPS" in result.answer
    assert "2026-08-22" in result.answer


def test_missing_order_id_requests_order_id():
    manager = ConversationManager()

    result = run_workflow(
        manager,
        "session-1",
        "Where is my order?",
    )

    assert result.action == "ask_for_order_id"
    assert result.tool_called is False
    assert result.answer is not None
    assert "order ID" in result.answer


def test_unknown_order_is_handled_safely():
    manager = ConversationManager()

    result = run_workflow(
        manager,
        "session-1",
        "Where is ORD-9999?",
    )

    assert result.action == "order_lookup_failed"
    assert result.tool_called is True
    assert result.answer is not None
    assert "couldn't find" in result.answer.lower()


def test_cancelled_order_does_not_show_eta():
    manager = ConversationManager()

    result = run_workflow(
        manager,
        "session-1",
        "What happened to ORD-1004?",
    )

    assert result.action == "order_lookup"
    assert result.tool_called is True
    assert result.answer is not None
    assert "cancelled" in result.answer.lower()
    assert "estimated delivery" not in result.answer.lower()


def test_returns_question_uses_knowledge_base():
    manager = ConversationManager()

    result = run_workflow(
        manager,
        "session-1",
        "How long can I return an unused backpack?",
    )

    assert result.action == "knowledge_retrieval"
    assert result.retrieved_passages


def test_breeze_conflict_requires_handoff():
    manager = ConversationManager()

    result = run_workflow(
        manager,
        "session-1",
        "Can I put the entire Breeze Tumbler in the dishwasher?",
    )

    assert result.action == "source_conflict"
    assert result.handoff is True
    assert result.retrieved_passages
    assert result.answer is not None
    assert "conflicting" in result.answer.lower()


def test_international_shipping_does_not_trigger_breeze_conflict():
    manager = ConversationManager()

    result = run_workflow(
        manager,
        "session-1",
        "Do you ship internationally?",
    )

    assert result.action == "knowledge_retrieval"
    assert result.handoff is False
    assert result.retrieved_passages

    assert any(
        "06-international-shipping.md"
        in passage.source.filename
        for passage in result.retrieved_passages
    )


def test_canada_follow_up_uses_international_shipping_context():
    agent = SupportAgent()

    first = agent.handle(
        "shipping-session",
        "Do you ship internationally?",
    )

    second = agent.handle(
        "shipping-session",
        "What about Canada?",
    )

    assert first.action == "knowledge_retrieval"
    assert second.action == "knowledge_retrieval"

    assert second.answer is not None
    assert "Canada" in second.answer

    assert (
        "06-international-shipping.md"
        in second.answer
    )