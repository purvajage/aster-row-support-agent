from collections import defaultdict

from app.models import RetrievedPassage


def _is_authoritative(passage: RetrievedPassage) -> bool:
    """Return whether a passage is an active official source."""
    metadata = passage.metadata

    return (
        metadata.get("status") == "active"
        and metadata.get("policy_authority") == "official"
    )


def _source_key(passage: RetrievedPassage) -> str:
    """Return a stable source identifier."""
    return passage.source.filename


def get_authoritative_sources(
    passages: list[RetrievedPassage],
) -> list[RetrievedPassage]:
    """Return active official retrieved passages."""
    return [
        passage
        for passage in passages
        if _is_authoritative(passage)
    ]


def detect_source_conflict(
    passages: list[RetrievedPassage],
) -> bool:
    """
    Detect whether multiple active official sources are relevant.

    This identifies a conflict candidate, not necessarily a
    proven contradiction.
    """
    authoritative = get_authoritative_sources(passages)

    sources: defaultdict[str, list[RetrievedPassage]] = (
        defaultdict(list)
    )

    for passage in authoritative:
        sources[_source_key(passage)].append(passage)

    return len(sources) >= 2


def detect_claim_conflict(
    passages: list[RetrievedPassage],
) -> bool:
    """
    Detect known contradictory claim patterns in retrieved
    authoritative passages.

    The original source documents remain unchanged. This logic
    only interprets retrieved content.
    """
    authoritative = get_authoritative_sources(passages)

    product_care_claim = False
    product_card_claim = False

    for passage in authoritative:
        filename = passage.source.filename.lower()
        text = passage.text.lower()

        if (
            "product-care" in filename
            and "hand-wash" in text
            and "stainless-steel body" in text
        ):
            product_care_claim = True

        if (
            "breeze-tumbler-product-card" in filename
            and "dishwasher safe" in text
        ):
            product_card_claim = True

    return product_care_claim and product_card_claim


def conflict_reason(
    passages: list[RetrievedPassage],
) -> str | None:
    """
    Return a customer-safe explanation of a detected conflict.
    """
    if not detect_claim_conflict(passages):
        return None

    return (
        "Two current official sources provide conflicting "
        "dishwasher-care guidance for the Breeze Tumbler. "
        "The Product Care Guide says the stainless-steel body "
        "should be hand-washed, while the product card says "
        "the tumbler is dishwasher safe. Human confirmation "
        "is recommended before giving a definitive answer."
    )