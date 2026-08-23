import re
from collections import Counter
from typing import Iterable

from app.document_parser import load_knowledge_base
from app.models import RetrievedPassage


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "be",
    "can",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "when",
    "where",
    "will",
    "with",
    "you",
}

SYNONYMS = {
    "regular": {"standard"},
    "ordinary": {"standard"},
    "normal": {"standard"},
    "internationally": {"international"},
    "ship": {"shipping"},
    "ships": {"shipping"},
    "delivery": {"deliver"},
    "arrive": {"delivery"},
    "arrives": {"delivery"},
}


def _tokenize(text: str) -> list[str]:
    """Convert text into searchable tokens."""
    return [
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if token not in STOP_WORDS
    ]


def _expanded_tokens(text: str) -> list[str]:
    """Add small, deterministic synonym expansions."""
    tokens = _tokenize(text)
    expanded = list(tokens)

    for token in tokens:
        expanded.extend(SYNONYMS.get(token, set()))

    return expanded


def _term_score(query: str, text: str) -> float:
    """Calculate normalized term overlap."""
    query_tokens = _expanded_tokens(query)
    text_tokens = set(_expanded_tokens(text))

    if not query_tokens or not text_tokens:
        return 0.0

    query_counts = Counter(query_tokens)
    matched = 0

    for token, count in query_counts.items():
        if token in text_tokens:
            matched += min(count, 1)

    return matched / len(query_counts)


def _phrase_bonus(query: str, text: str) -> float:
    """Reward useful query/source phrase matches."""
    query_lower = query.lower()
    text_lower = text.lower()

    bonus = 0.0

    phrase_pairs = [
        ("regular customer", "standard plan", 0.50),
        ("standard customer", "standard plan", 0.50),
        ("regular customer", "trailplus", -0.30),
        ("standard customer", "trailplus", -0.30),
        ("international", "international shipping", 0.30),
        ("canada", "canada", 0.25),
        ("delivery", "delivery estimate", 0.20),
        ("breeze tumbler", "breeze tumbler", 0.40),
        ("return window", "return window", 0.20),
        ("final sale", "final sale", 0.30),
        ("price adjustment", "price adjustment", 0.30),
        ("human assistance", "human", 0.20),
    ]

    for query_phrase, source_phrase, value in phrase_pairs:
        if query_phrase in query_lower and source_phrase in text_lower:
            bonus += value

    return bonus


def _authority_boost(passage: RetrievedPassage) -> float:
    """Prefer active official customer-facing sources."""
    metadata = passage.metadata

    status = metadata.get("status")
    authority = metadata.get("policy_authority")
    audience = metadata.get("audience")

    boost = 0.0

    if status == "active":
        boost += 0.30
    elif status == "superseded":
        boost -= 0.60
    elif status == "draft":
        boost -= 0.50

    if authority == "official":
        boost += 0.20
    elif authority == "none":
        boost -= 0.30

    if audience == "customer":
        boost += 0.10
    elif audience == "internal":
        boost -= 0.10

    return boost


def _score_passage(
    query: str,
    passage: RetrievedPassage,
) -> float:
    """Combine relevance, phrase, and authority signals."""
    relevance = _term_score(query, passage.text)

    source_text = (
        f"{passage.source.filename} "
        f"{passage.source.heading}"
    )

    source_relevance = _term_score(
        query,
        source_text,
    )

    phrase_bonus = _phrase_bonus(
        query,
        passage.text,
    )

    authority = _authority_boost(passage)

    return (
        relevance
        + (0.20 * source_relevance)
        + phrase_bonus
        + authority
    )


def retrieve(
    query: str,
    passages: Iterable[RetrievedPassage] | None = None,
    top_k: int = 5,
) -> list[RetrievedPassage]:
    """
    Retrieve relevant passages while encouraging source diversity.
    """
    if passages is None:
        passages = load_knowledge_base()

    scored: list[RetrievedPassage] = []

    for passage in passages:
        score = _score_passage(
            query,
            passage,
        )

        # Ignore passages with essentially no query relevance.
        if score <= 0.45:
            continue

        scored.append(
            passage.model_copy(
                update={"score": score}
            )
        )

    scored.sort(
        key=lambda item: item.score,
        reverse=True,
    )

    selected: list[RetrievedPassage] = []
    source_counts: Counter[str] = Counter()

    # First pass: prioritize different source files.
    for passage in scored:
        filename = passage.source.filename

        if source_counts[filename] >= 2:
            continue

        selected.append(passage)
        source_counts[filename] += 1

        if len(selected) >= top_k:
            break

    return selected