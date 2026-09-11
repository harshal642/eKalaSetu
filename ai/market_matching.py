"""
market_matching.py
--------------------
Prototype "AI Market Opportunity" engine.

Matches a product's craft category against the list of markets in
data/markets.json and returns a simple match percentage. This is a
transparent, rule-based prototype (keyword/category overlap), not a
trained recommender -- see project rule "NO FAKE AI CLAIMS".

To upgrade later: replace match_markets() with a real recommender that
also uses location, demand data, and past order history.
"""


def _score_market(craft: str, market: dict) -> int:
    craft = (craft or "").lower().strip()
    market_crafts = [c.lower() for c in market.get("crafts", [])]

    if craft in market_crafts:
        return 90

    # Partial keyword overlap fallback (e.g. "Leather Craft" vs
    # "Kolhapuri Leather Craft").
    craft_words = set(craft.split())
    best_partial = 0
    for mc in market_crafts:
        mc_words = set(mc.split())
        overlap = craft_words & mc_words
        if overlap:
            best_partial = max(best_partial, 60 + 10 * len(overlap))

    return min(best_partial, 85)


def match_markets(product_data: dict, markets: list, top_n: int = 3) -> list:
    """
    Args:
        product_data: dict containing at least "craft"
        markets: list of market dicts (from data/markets.json)
        top_n: number of top matches to return

    Returns:
        list of dicts: [{name, location, match_percent}, ...] sorted by
        match_percent descending, highest first.
    """
    craft = product_data.get("craft", "")
    results = []

    for market in markets:
        score = _score_market(craft, market)
        if score <= 0:
            score = 35  # baseline general-market visibility

        results.append({
            "name": market.get("name", "Market"),
            "location": market.get("location", ""),
            "match_percent": score,
        })

    results.sort(key=lambda m: m["match_percent"], reverse=True)
    return results[:top_n]
