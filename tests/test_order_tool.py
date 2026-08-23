from app.order_tool import lookup_order


def test_valid_order_lookup():
    result = lookup_order("ORD-1007")

    assert result.found is True
    assert result.order_id == "ORD-1007"
    assert result.data is not None

    assert result.data["status"] == "shipped"
    assert result.data["carrier"] == "UPS"
    assert result.data["estimated_delivery"] == "2026-08-22"


def test_order_id_normalization():
    result = lookup_order("  ord-1007  ")

    assert result.found is True
    assert result.order_id == "ORD-1007"


def test_unknown_order():
    result = lookup_order("ORD-9999")

    assert result.found is False
    assert result.error == "Order was not found."
    assert result.data is None


def test_cancelled_order_does_not_expose_stale_eta():
    result = lookup_order("ORD-1004")

    assert result.found is True
    assert result.data is not None

    assert result.data["status"] == "cancelled"
    assert result.data["estimated_delivery"] is None
    assert result.data["carrier"] is None
    assert result.data["tracking_number"] is None


def test_internal_customer_data_is_not_exposed():
    result = lookup_order("ORD-1007")

    assert result.data is not None

    serialized = str(result.data)

    assert "ava.morgan@example.test" not in serialized
    assert "220 King Street West" not in serialized
    assert "risk_score" not in serialized
    assert "fraud review" not in serialized
    assert "warehouse_note" not in serialized