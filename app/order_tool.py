import json
import re
from pathlib import Path
from typing import Any

from app.models import OrderLookupResult


ORDERS_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "orders.json"
)


def _normalize_order_id(order_id: str) -> str:
    """Normalize harmless formatting differences in an order ID."""
    value = order_id.strip().upper()

    # Remove harmless punctuation such as spaces or hyphens
    # around the identifier.
    value = re.sub(r"[\s]+", "", value)

    return value


def _load_orders() -> list[dict[str, Any]]:
    """Load the mock orders from disk."""
    with ORDERS_FILE.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    return payload["orders"]


def lookup_order(order_id: str) -> OrderLookupResult:
    """
    Look up an order and return only customer-safe information.

    Internal fields, customer contact details, and addresses are
    deliberately excluded from the result.
    """
    if not isinstance(order_id, str):
        return OrderLookupResult(
            found=False,
            order_id="",
            error="Order ID must be a string.",
        )

    normalized_id = _normalize_order_id(order_id)

    if not normalized_id:
        return OrderLookupResult(
            found=False,
            order_id="",
            error="Order ID is required.",
        )

    # Basic format validation.
    if not re.fullmatch(r"ORD-\d{4}", normalized_id):
        return OrderLookupResult(
            found=False,
            order_id=normalized_id,
            error="Malformed order ID.",
        )

    orders = _load_orders()

    order = next(
        (
            item
            for item in orders
            if item.get("order_id") == normalized_id
        ),
        None,
    )

    if order is None:
        return OrderLookupResult(
            found=False,
            order_id=normalized_id,
            error="Order was not found.",
        )

    status = order.get("status")

    safe_data: dict[str, Any] = {
        "order_id": order["order_id"],
        "membership_tier": order.get("membership_tier"),
        "items": [
            {
                "name": item.get("name"),
                "quantity": item.get("quantity"),
                "final_sale": item.get("final_sale"),
            }
            for item in order.get("items", [])
        ],
        "placed_at": order.get("placed_at"),
        "status": status,
        "status_updated_at": order.get("status_updated_at"),
        "shipped_at": order.get("shipped_at"),
        "delivered_at": order.get("delivered_at"),
        "carrier": order.get("carrier"),
        "tracking_number": order.get("tracking_number"),
        "customer_safe_message": order.get("customer_safe_message"),
    }

    # Never expose stale delivery information for cancelled
    # or returned orders.
    if status in {"cancelled", "returned"}:
        safe_data["carrier"] = None
        safe_data["tracking_number"] = None
        safe_data["estimated_delivery"] = None
    else:
        safe_data["estimated_delivery"] = order.get(
            "estimated_delivery"
        )

    # For shipped orders with no ETA, preserve the absence of
    # an estimate. Never calculate or invent one.
    if status == "shipped" and order.get("estimated_delivery") is None:
        safe_data["estimated_delivery"] = None

    return OrderLookupResult(
        found=True,
        order_id=normalized_id,
        data=safe_data,
    )