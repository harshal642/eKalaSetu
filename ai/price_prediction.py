"""
price_prediction.py
-------------------

KalaSetu prototype selling-price recommendation engine.

This is a transparent heuristic system.
It is NOT presented as a trained ML model.

Inputs:
- Making cost
- Making time
- Material

Output:
- Minimum suggested selling price
- Maximum suggested selling price
- Recommended price
"""


def _parse_cost(value):

    try:
        return float(value)

    except (
        TypeError,
        ValueError
    ):

        return 0.0


def _time_multiplier(making_time):

    text = str(
        making_time or ""
    ).lower().strip()

    # Days
    if "day" in text or "दिवस" in text or "दिन" in text:

        numbers = []

        for word in text.replace(
            ",",
            " "
        ).split():

            try:
                numbers.append(
                    float(word)
                )
            except ValueError:
                pass

        if numbers:

            days = max(
                numbers
            )

            if days >= 7:
                return 1.15

            if days >= 4:
                return 1.10

            if days >= 2:
                return 1.05

    # Hours
    if "hour" in text or "तास" in text or "घंट" in text:

        return 1.02

    return 1.00


def _material_multiplier(material):

    text = str(
        material or ""
    ).lower()

    premium_materials = [
        "silk",
        "silver",
        "brass",
        "copper",
        "wood",
        "handloom",
        "paithani",
        "रेशीम",
        "चांदी",
        "पितळ",
        "तांबे",
        "लाकूड",
    ]

    for keyword in premium_materials:

        if keyword in text:

            return 1.10

    return 1.00


def suggest_price(product_data: dict) -> dict:

    making_cost = _parse_cost(
        product_data.get(
            "making_cost"
        )
    )

    material = product_data.get(
        "material",
        ""
    )

    making_time = product_data.get(
        "making_time",
        ""
    )

    if making_cost <= 0:

        return {
            "min_price": 0,
            "max_price": 0,
            "recommended_price": 0
        }

    time_factor = _time_multiplier(
        making_time
    )

    material_factor = _material_multiplier(
        material
    )

    # Base markup
    base_min = making_cost * 1.60
    base_max = making_cost * 2.10

    # Skill/time/material adjustments
    min_price = (
        base_min
        * time_factor
        * material_factor
    )

    max_price = (
        base_max
        * time_factor
        * material_factor
    )

    # Round to nearest ₹10
    min_price = (
        round(min_price / 10)
        * 10
    )

    max_price = (
        round(max_price / 10)
        * 10
    )

    if max_price <= min_price:

        max_price = (
            min_price + 100
        )

    recommended_price = (
        (min_price + max_price)
        / 2
    )

    recommended_price = (
        round(
            recommended_price / 10
        )
        * 10
    )

    return {

        "min_price":
            int(min_price),

        "max_price":
            int(max_price),

        "recommended_price":
            int(recommended_price)
    }