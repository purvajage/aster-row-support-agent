from app.conflict_detector import detect_claim_conflict
from app.local_retrieval import retrieve_local


def test_current_returns_policy_is_retrieved():
    results = retrieve_local(
        "How long does a regular customer have to "
        "return an unused backpack?"
    )

    assert len(results) > 0

    first = results[0]

    assert (
        first.source.filename
        == "01-returns-policy-current.md"
    )

    assert (
        first.source.heading
        == "Standard return window"
    )


def test_legacy_returns_policy_does_not_rank_first():
    results = retrieve_local(
        "How long does a regular customer have to "
        "return an unused backpack?"
    )

    assert len(results) > 0

    assert (
        results[0].source.filename
        == "01-returns-policy-current.md"
    )

    assert (
        results[0].source.filename
        != "02-returns-policy-legacy.md"
    )


def test_canada_shipping_retrieves_international_policy():
    results = retrieve_local(
        "Do you ship to Canada and how long does "
        "delivery take?"
    )

    assert len(results) > 0

    filenames = {
        result.source.filename
        for result in results
    }

    assert "06-international-shipping.md" in filenames


def test_breeze_tumbler_conflict_is_detected():
    results = retrieve_local(
        "Can I put the entire Breeze Tumbler "
        "in the dishwasher?"
    )

    assert detect_claim_conflict(results) is True


def test_regular_return_question_is_not_breeze_conflict():
    results = retrieve_local(
        "How long does a regular customer have "
        "to return an unused backpack?"
    )

    assert detect_claim_conflict(results) is False


def test_retrieval_preserves_source_metadata():
    results = retrieve_local(
        "What is the return window?"
    )

    assert len(results) > 0

    passage = results[0]

    assert passage.source.filename
    assert passage.source.heading
    assert passage.metadata
    assert "status" in passage.metadata
    assert "policy_authority" in passage.metadata