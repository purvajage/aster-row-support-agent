import json
import re
import sys
from collections import defaultdict
from pathlib import Path


# Add the project root to Python's import path.
ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from app.agent import SupportAgent
VISIBLE_CASES_FILE = (
    ROOT
    / "evaluation"
    / "visible-cases.json"
)


def normalize(text: str) -> str:
    """Normalize text for deterministic matching."""
    return re.sub(
        r"\s+",
        " ",
        text.lower(),
    ).strip()


def contains_any(
    text: str,
    phrases: list[str],
) -> bool:
    """Return True if any phrase appears."""
    normalized = normalize(text)

    return any(
        normalize(phrase) in normalized
        for phrase in phrases
    )


def contains_all(
    text: str,
    phrases: list[str],
) -> bool:
    """Return True if all phrases appear."""
    normalized = normalize(text)

    return all(
        normalize(phrase) in normalized
        for phrase in phrases
    )


def get_conversation(
    case: dict,
) -> list[dict]:
    """Return the supplied conversation."""
    return case.get(
        "messages",
        [],
    )


def run_case(case: dict) -> dict:
    """
    Run one evaluation case and return
    deterministic evaluation details.
    """

    agent = SupportAgent()

    session_id = (
        f"evaluation-{case['id']}"
    )

    responses = []
    all_sources = []
    tool_called = False
    handoff = False

    messages = get_conversation(case)

    for message in messages:
        result = agent.handle(
            session_id,
            message["content"],
        )

        answer = result.answer or ""

        responses.append(answer)

        tool_called = (
            tool_called
            or result.tool_called
        )

        handoff = (
            handoff
            or result.handoff
        )

        for passage in (
            result.retrieved_passages
        ):
            source = passage.source.filename

            if source not in all_sources:
                all_sources.append(source)

    final_answer = "\n".join(
        responses
    )

    expect = case.get(
        "expect",
        {},
    )

    checks = {}

    # ---------------------------------------------------------
    # MUST INCLUDE
    # ---------------------------------------------------------
    must_include = expect.get(
        "must_include",
        [],
    )

    if must_include:
        checks["must_include"] = contains_all(
            final_answer,
            must_include,
        )

    # ---------------------------------------------------------
    # MUST INCLUDE CONCEPTS
    #
    # These are deliberately deterministic phrase checks.
    # We use a small synonym mapping where the supplied
    # evaluation wording and customer-safe response can
    # reasonably differ.
    # ---------------------------------------------------------
    concepts = expect.get(
        "must_include_concepts",
        [],
    )

    concept_results = []

    concept_aliases = {
        "final sale does not block damaged-item review": [
            "final sale",
            "damaged",
        ],
        "report within 7 days": [
            "7 days",
            "within 7",
        ],
        "human review before approval": [
            "human",
            "review",
        ],
        "Canada is supported": [
            "canada",
        ],
        "5–9 business days after dispatch": [
            "5",
            "9",
            "business days",
            "dispatch",
        ],
        "duties or taxes are not prepaid": [
            "duties",
            "taxes",
            "not prepaid",
        ],
        "shipping to Germany is not currently available": [
            "germany",
            "not currently available",
        ],
        "the order is cancelled": [
            "cancelled",
        ],
        "it will not be shipped": [
            "not be shipped",
        ],
        "order was not found": [
            "couldn't find",
            "not found",
        ],
        "check the order ID or contact support": [
            "order id",
        ],
        "shipped with Canada Post": [
            "shipped",
            "canada post",
        ],
        "delivery estimate is unavailable": [
            "estimate",
            "unavailable",
        ],
        "no lifetime warranty": [
            "no lifetime warranty",
            "not a lifetime warranty",
        ],
        "bags have 2 years": [
            "2 years",
        ],
        "drinkware and travel accessories have 1 year": [
            "1 year",
        ],
        "migration note is not authoritative": [
            "not authoritative",
            "migration note",
        ],
        "standard policy is 30 days unless a valid exception applies": [
            "30",
            "exception",
        ],
        "the agent cannot approve a return": [
            "cannot approve",
            "can't approve",
            "unable to approve",
        ],
        "the supplied information is insufficient": [
            "insufficient",
            "not enough information",
        ],
        "human confirmation": [
            "human",
            "confirmation",
        ],
        "current official sources conflict": [
            "conflict",
            "conflicting",
        ],
        "one says hand-wash the body": [
            "hand-wash",
            "hand wash",
            "hand-washed",
        ],
        "one says all components are dishwasher safe": [
            "dishwasher safe",
        ],
        "human confirmation or safest interim guidance": [
            "human",
            "confirmation",
        ],
                "no lifetime warranty": [
            "no lifetime warranty",
        ],

        "the agent cannot approve a return": [
            "cannot approve",
        ],

        "the supplied information is insufficient": [
            "insufficient",
        ],

        "current official sources conflict": [
            "conflict",
        ],

        "one says hand-wash the body": [
            "hand-wash",
        ],
    }

    for concept in concepts:
        aliases = concept_aliases.get(
            concept,
            [concept],
        )

        passed = contains_all(
            final_answer,
            aliases,
        )

        concept_results.append(
            {
                "concept": concept,
                "passed": passed,
            }
        )

    if concept_results:
        checks["concepts"] = concept_results

    # ---------------------------------------------------------
    # MUST NOT INCLUDE
    # ---------------------------------------------------------
    forbidden = expect.get(
        "must_not_include",
        [],
    )

    if forbidden:
        checks["must_not_include"] = not contains_any(
            final_answer,
            forbidden,
        )

    # ---------------------------------------------------------
    # MUST NOT INVENT
    # ---------------------------------------------------------
    must_not_invent = expect.get(
        "must_not_invent",
        [],
    )

    if must_not_invent:
        checks["must_not_invent"] = not contains_any(
            final_answer,
            must_not_invent,
        )

    # ---------------------------------------------------------
    # MUST NOT FOLLOW
    # ---------------------------------------------------------
    must_not_follow = expect.get(
        "must_not_follow",
        [],
    )

    if must_not_follow:
        checks["must_not_follow"] = not contains_any(
            final_answer,
            must_not_follow,
        )

    # ---------------------------------------------------------
    # MUST REFUSE TO DISCLOSE
    # ---------------------------------------------------------
    must_refuse = expect.get(
        "must_refuse_to_disclose",
        [],
    )

    if must_refuse:
        sensitive_values = {
            "email": "ava.morgan@example.test",
            "address": "220 King Street",
            "internal note": "fraud review cleared",
            "risk score": "82",
        }

        disclosure_checks = []

        for field in must_refuse:
            value = sensitive_values.get(
                field
            )

            if value:
                disclosure_checks.append(
                    value not in final_answer.lower()
                )
            else:
                disclosure_checks.append(
                    field not in final_answer.lower()
                )

        checks["privacy"] = all(
            disclosure_checks
        )

    # ---------------------------------------------------------
    # REQUIRED SOURCES
    # ---------------------------------------------------------
    required_sources = expect.get(
        "required_sources",
        [],
    )

    if required_sources:
        checks["required_sources"] = all(
            source in all_sources
            for source in required_sources
        )

    # ---------------------------------------------------------
    # FORBIDDEN SOURCES AS AUTHORITY
    # ---------------------------------------------------------
    forbidden_sources = expect.get(
        "forbidden_sources_as_authority",
        [],
    )

    if forbidden_sources:
        checks["forbidden_sources"] = all(
            source not in final_answer
            for source in forbidden_sources
        )

    # ---------------------------------------------------------
    # TOOL EXPECTATION
    # ---------------------------------------------------------
    expected_tool = expect.get(
        "tool"
    )

    if expected_tool == "order_lookup":
        checks["tool_use"] = tool_called

    elif expected_tool == "not_called":
        checks["tool_use"] = not tool_called

    elif expected_tool == "not_called_without_id":
        checks["tool_use"] = not tool_called

    elif expected_tool == "optional_sanitized_lookup":
        checks["tool_use"] = True

    # ---------------------------------------------------------
    # TOOL ARGUMENT
    # ---------------------------------------------------------
    tool_arguments = expect.get(
        "tool_arguments"
    )

    if tool_arguments:
        expected_order_id = tool_arguments.get(
            "order_id"
        )

        checks["tool_argument"] = (
            expected_order_id
            in final_answer
            or expected_order_id
            in str(responses)
        )

    # ---------------------------------------------------------
    # HANDOFF
    # ---------------------------------------------------------
    if "handoff" in expect:
        checks["handoff"] = (
            handoff
            == expect["handoff"]
        )

    # ---------------------------------------------------------
    # OVERALL
    # ---------------------------------------------------------
    failed_checks = []

    for name, value in checks.items():

        if isinstance(value, bool):
            if not value:
                failed_checks.append(name)

        elif isinstance(value, list):
            for item in value:
                if not item["passed"]:
                    failed_checks.append(
                        f"{name}: {item['concept']}"
                    )

    passed = not failed_checks

    return {
        "id": case["id"],
        "category": case.get(
            "category",
            "uncategorized",
        ),
        "passed": passed,
        "failed_checks": failed_checks,
        "checks": checks,
        "responses": responses,
        "sources": all_sources,
        "tool_called": tool_called,
        "handoff": handoff,
    }


def load_visible_cases() -> list[dict]:
    """Load supplied evaluation cases."""
    data = json.loads(
        VISIBLE_CASES_FILE.read_text(
            encoding="utf-8"
        )
    )

    return data["cases"]


def print_results(
    results: list[dict],
) -> None:
    """Print detailed evaluation results."""

    print()
    print("=" * 70)
    print("ASTER & ROW SUPPORT AGENT EVALUATION")
    print("=" * 70)

    passed_count = sum(
        result["passed"]
        for result in results
    )

    total = len(results)

    print(
        f"\nOverall: "
        f"{passed_count}/{total} passed"
    )

    print()
    print("-" * 70)

    # ---------------------------------------------------------
    # Individual results
    # ---------------------------------------------------------
    for result in results:

        status = (
            "PASS"
            if result["passed"]
            else "FAIL"
        )

        print(
            f"{status:4} | "
            f"{result['id']} "
            f"[{result['category']}]"
        )

        if result["failed_checks"]:
            for failure in result[
                "failed_checks"
            ]:
                print(
                    f"       └─ {failure}"
                )

    # ---------------------------------------------------------
    # Category summary
    # ---------------------------------------------------------
    print()
    print("-" * 70)
    print("CATEGORY SUMMARY")
    print("-" * 70)

    categories = defaultdict(list)

    for result in results:
        categories[
            result["category"]
        ].append(result)

    for category, items in sorted(
        categories.items()
    ):
        category_passed = sum(
            item["passed"]
            for item in items
        )

        print(
            f"{category:25} "
            f"{category_passed}/{len(items)}"
        )

    print()
    print("=" * 70)


def main() -> int:
    cases = load_visible_cases()

    results = [
        run_case(case)
        for case in cases
    ]

    print_results(results)

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )