"""
demand_prediction.py
---------------------
Prototype "AI Demand Insights" engine.

For this prototype there is no live analytics pipeline, so we generate
consistent, deterministic dummy engagement numbers (views/wishlist/
cart/orders) per product using a simple hash-based seed, then turn that
into a friendly demand score and message. Because the seed is
deterministic (based on product_id), the same product always shows the
same numbers -- it will not look random/broken on refresh.

To upgrade later: replace _dummy_activity() with real analytics events
read from data/orders.json and page-view logs.
"""

import hashlib


def _seed_from_id(product_id) -> int:
    digest = hashlib.md5(str(product_id).encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _dummy_activity(product_id) -> dict:
    seed = _seed_from_id(product_id)

    views = 80 + (seed % 400)
    wishlist = 10 + (seed % 90)
    cart = 5 + (seed % 60)
    orders = 2 + (seed % 55)

    # Keep the funnel realistic: orders <= cart <= wishlist <= views is not
    # strictly enforced for the prototype, but we soften obvious spikes.
    cart = min(cart, wishlist + 20)
    orders = min(orders, cart + 10)

    return {
        "views": views,
        "wishlist": wishlist,
        "cart": cart,
        "orders": orders,
    }


def _demand_level(score: int) -> str:
    if score >= 75:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


def predict_demand(product_id, data: dict = None) -> dict:
    """
    Args:
        product_id: id of the product
        data: optional dict of real activity data (views/wishlist/cart/orders)
              if not provided, deterministic dummy data is used.

    Returns:
        dict: {views, wishlist, cart, orders, demand_score, demand_level}
    """
    activity = data if data else _dummy_activity(product_id)

    views = activity.get("views", 0)
    wishlist = activity.get("wishlist", 0)
    cart = activity.get("cart", 0)
    orders = activity.get("orders", 0)

    # Simple weighted formula -- deeper funnel actions count more.
    raw_score = (views * 0.1) + (wishlist * 0.5) + (cart * 0.8) + (orders * 1.5)
    demand_score = min(100, int(raw_score / 3))

    return {
        "views": views,
        "wishlist": wishlist,
        "cart": cart,
        "orders": orders,
        "demand_score": demand_score,
        "demand_level": _demand_level(demand_score),
    }
