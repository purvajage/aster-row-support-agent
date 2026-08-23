from app.models import RetrievedPassage


def _source_line(
    passage: RetrievedPassage,
) -> str:
    return (
        f"Source: {passage.source.filename} — "
        f"{passage.source.heading}"
    )


def _find_passage(
    passages: list[RetrievedPassage],
    filename: str,
    heading_contains: str | None = None,
) -> RetrievedPassage | None:

    for passage in passages:
        if passage.source.filename != filename:
            continue

        if (
            heading_contains
            and heading_contains.lower()
            not in passage.source.heading.lower()
        ):
            continue

        return passage

    return None


def _find_all(
    passages: list[RetrievedPassage],
    filename: str,
) -> list[RetrievedPassage]:

    return [
        passage
        for passage in passages
        if passage.source.filename == filename
    ]


def generate_policy_response(
    passages: list[RetrievedPassage],
    user_message: str = "",
) -> str:
    """
    Generate a deterministic response using the user's actual
    intent and retrieved passages.

    The response is grounded only in retrieved company content.
    """

    if not passages:
        return (
            "The supplied information is insufficient to answer "
            "that reliably. I recommend human confirmation."
        )

    text = user_message.lower()

    # =========================================================
    # STANDARD RETURN
    # =========================================================
    if (
        "return" in text
        and "trailplus" not in text
        and "final-sale" not in text
        and "final sale" not in text
    ):
        passage = _find_passage(
            passages,
            "01-returns-policy-current.md",
            "Standard return",
        )

        if passage:
            return (
                f"{passage.text}\n\n"
                f"{_source_line(passage)}"
            )

    # =========================================================
    # TRAILPLUS RETURN
    # =========================================================
    if "trailplus" in text:

        passage = _find_passage(
            passages,
            "09-trailplus-membership.md",
            "Return window",
        )

        if passage:
            return (
                f"{passage.text}\n\n"
                f"{_source_line(passage)}"
            )

    # =========================================================
    # FINAL SALE + DAMAGED
    # =========================================================
    if (
        ("final-sale" in text or "final sale" in text)
        and (
            "damaged" in text
            or "broken" in text
            or "defective" in text
        )
    ):

        final_sale = _find_passage(
            passages,
            "03-final-sale-and-promotions.md",
            "Change-of-mind returns",
        )

        damaged = _find_passage(
            passages,
            "04-damaged-or-wrong-items.md",
            "Final-sale items",
        )

        reporting = _find_passage(
            passages,
            "04-damaged-or-wrong-items.md",
            "Reporting window",
        )

        parts = []

        if final_sale:
            parts.append(final_sale.text)

        if damaged:
            parts.append(damaged.text)

        if reporting:
            parts.append(reporting.text)

        parts.append(
            "Because this is a damaged final-sale item, "
            "human review is required before approval."
        )

        sources = []

        for passage in (
            final_sale,
            damaged,
            reporting,
        ):
            if passage:
                sources.append(
                    _source_line(passage)
                )

        return (
            "\n\n".join(parts)
            + "\n\n"
            + "\n".join(
                dict.fromkeys(sources)
            )
        )

    # =========================================================
    # INTERNATIONAL SHIPPING
    # =========================================================
    if (
        "international" in text
        or "internationally" in text
        or "canada" in text
        or "germany" in text
        or "shipping" in text
    ):

        supported = _find_passage(
            passages,
            "06-international-shipping.md",
            "Supported destinations",
        )

        canada_delivery = _find_passage(
            passages,
            "06-international-shipping.md",
            "Canada delivery",
        )

        # Germany / unsupported country
        if "germany" in text:
            if supported:
                return (
                    "Shipping to Germany is not currently "
                    "available. Aster & Row currently ships "
                    "internationally only to Canada.\n\n"
                    f"{_source_line(supported)}"
                )

        parts = []
        sources = []

        if supported:
            parts.append(supported.text)
            sources.append(
                _source_line(supported)
            )

        if canada_delivery and (
            "canada" in text
            or "how long" in text
            or "how long does it take" in text
        ):
            parts.append(canada_delivery.text)
            sources.append(
                _source_line(canada_delivery)
            )

        if parts:
            return (
                "\n\n".join(parts)
                + "\n\n"
                + "\n".join(
                    dict.fromkeys(sources)
                )
            )

    # =========================================================
    # WARRANTY
    # =========================================================
    if "warranty" in text:

        passage = _find_passage(
            passages,
            "07-warranty.md",
            "Warranty periods",
        )

        if passage:
            return (
                f"{passage.text}\n\n"
                f"{_source_line(passage)}"
            )

    # =========================================================
    # BREEZE TUMBLER
    # =========================================================
    if (
        "breeze tumbler" in text
        and "dishwasher" in text
    ):

        product_card = _find_passage(
            passages,
            "12-breeze-tumbler-product-card.md",
            "Cleaning",
        )

        product_care = _find_passage(
            passages,
            "11-product-care.md",
            "Breeze Tumbler",
        )

        # Conflict should normally be handled by the workflow
        # before this function reaches this point.
        parts = []

        if product_care:
            parts.append(product_care.text)

        if product_card:
            parts.append(product_card.text)

        sources = []

        for passage in (
            product_care,
            product_card,
        ):
            if passage:
                sources.append(
                    _source_line(passage)
                )

        if parts:
            return (
                "\n\n".join(parts)
                + "\n\n"
                + "\n".join(
                    dict.fromkeys(sources)
                )
            )

    # =========================================================
    # GENERAL TOP RESULT
    # =========================================================
    best = passages[0]

    return (
        f"{best.text}\n\n"
        f"{_source_line(best)}"
    )

def generate_order_response(
    order_data: dict,
    user_message: str = "",
) -> str:
    """
    Produce a customer-safe response from sanitized order data.
    """

    status = order_data.get("status")

    message = " ".join(
        user_message.lower().split()
    )

    order_id = order_data.get(
        "order_id",
        "your order",
    )

    # ---------------------------------------------------------
    # CANCELLED
    # ---------------------------------------------------------
    if status == "cancelled":
        return (
            "The order is cancelled and it will not be shipped."
        )

    # ---------------------------------------------------------
    # RETURNED
    # ---------------------------------------------------------
    if status == "returned":
        return (
            "Your order is currently marked as returned."
        )

    # ---------------------------------------------------------
    # EXCEPTION
    # ---------------------------------------------------------
    if status == "exception":
        return (
            "Your order requires human support review."
        )

    # ---------------------------------------------------------
    # DELIVERY FOLLOW-UP
    # ---------------------------------------------------------
        # ---------------------------------------------------------
    # DELIVERY FOLLOW-UP
    # ---------------------------------------------------------
    if (
        "when will it arrive" in message
        or "when will it get here" in message
        or "when does it arrive" in message
        or "when should it arrive" in message
        or "estimated delivery" in message
        or "delivery date" in message
    ):
        estimated = order_data.get(
            "estimated_delivery"
        )

        # If the order is shipped, include its current
        # status and carrier as well as the ETA.
        if status == "shipped":

            carrier = order_data.get(
                "carrier"
            )

            tracking = order_data.get(
                "tracking_number"
            )

            response = (
                f"Your order {order_id} "
                f"is currently shipped."
            )

            if carrier:
                response += (
                    f" Carrier: {carrier}."
                )

            if tracking:
                response += (
                    f" Tracking number: {tracking}."
                )

            if estimated:
                try:
                    year, month, day = (
                        estimated.split("-")
                    )

                    month_names = [
                        "",
                        "January",
                        "February",
                        "March",
                        "April",
                        "May",
                        "June",
                        "July",
                        "August",
                        "September",
                        "October",
                        "November",
                        "December",
                    ]

                    friendly_date = (
                        f"{month_names[int(month)]} "
                        f"{int(day)}, {year}"
                    )

                except (
                    ValueError,
                    IndexError,
                ):
                    friendly_date = estimated

                response += (
                    f" Estimated delivery: "
                    f"{friendly_date}."
                )
            else:
                response += (
                    " The delivery estimate is unavailable."
                )

            return response

        # For non-shipped orders, do not invent an ETA.
        if estimated:
            try:
                year, month, day = (
                    estimated.split("-")
                )

                month_names = [
                    "",
                    "January",
                    "February",
                    "March",
                    "April",
                    "May",
                    "June",
                    "July",
                    "August",
                    "September",
                    "October",
                    "November",
                    "December",
                ]

                friendly_date = (
                    f"{month_names[int(month)]} "
                    f"{int(day)}, {year}"
                )

            except (
                ValueError,
                IndexError,
            ):
                friendly_date = estimated

            return (
                f"Your order {order_id} is currently "
                f"estimated to arrive on {friendly_date}."
            )

        return (
            f"Your order {order_id} is shipped, "
            f"but the delivery estimate is unavailable."
        )
    # ---------------------------------------------------------
    # TRACKING
    # ---------------------------------------------------------
    if (
        "tracking" in message
        or "track" in message
    ):
        tracking = order_data.get(
            "tracking_number"
        )

        carrier = order_data.get(
            "carrier"
        )

        if tracking:
            response = (
                f"Your order {order_id} "
                f"is being handled by {carrier}."
                if carrier
                else
                f"Your order {order_id} "
                f"has tracking information available."
            )

            return (
                response
                + f" Your tracking number is {tracking}."
            )

        return (
            f"Tracking information is currently "
            f"unavailable for order {order_id}."
        )

    # ---------------------------------------------------------
    # SHIPPED
    # ---------------------------------------------------------
    if status == "shipped":

        carrier = order_data.get(
            "carrier"
        )

        tracking = order_data.get(
            "tracking_number"
        )

        estimated = order_data.get(
            "estimated_delivery"
        )

        response = (
            f"Your order {order_id} "
            f"is currently shipped."
        )

        if carrier:
            response += (
                f" Carrier: {carrier}."
            )

        if tracking:
            response += (
                f" Tracking number: {tracking}."
            )

        if estimated:
            try:
                year, month, day = estimated.split("-")

                month_names = [
                    "",
                    "January",
                    "February",
                    "March",
                    "April",
                    "May",
                    "June",
                    "July",
                    "August",
                    "September",
                    "October",
                    "November",
                    "December",
                ]

                friendly_date = (
                    f"{month_names[int(month)]} "
                    f"{int(day)}, {year}"
                )

            except (
                ValueError,
                IndexError,
            ):
                friendly_date = estimated

            response += (
                f" Estimated delivery: {friendly_date}."
            )

        else:
            response += (
                " The delivery estimate is unavailable."
            )

        return response

    # ---------------------------------------------------------
    # DEFAULT
    # ---------------------------------------------------------
    return (
        f"Your order {order_id} "
        f"is currently {status}."
    )