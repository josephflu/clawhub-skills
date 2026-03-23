"""
eBay item valuation using Browse API and Marketplace Insights API.

Provides get_valuation() to estimate item market value based on
current/recent eBay listings, with condition-based price adjustment.
"""

import os
import statistics
from typing import Optional

import httpx


# Condition adjustment factors for valuation
# Maps user-facing condition keys to multipliers applied to avg price
CONDITION_ADJUSTMENTS: dict[str, float] = {
    "new": 1.0,
    "like_new": 0.95,
    "very_good": 0.85,
    "good": 0.75,
    "acceptable": 0.6,
    "used": 0.8,
    "for_parts": 0.3,
}

SANDBOX_INSIGHTS_URL = "https://api.sandbox.ebay.com/buy/marketplace_insights/v1/item_sales/search"
PRODUCTION_INSIGHTS_URL = "https://api.ebay.com/buy/marketplace_insights/v1/item_sales/search"


def _get_insights_url() -> str:
    env = os.getenv("EBAY_ENVIRONMENT", "production").lower()
    return SANDBOX_INSIGHTS_URL if env == "sandbox" else PRODUCTION_INSIGHTS_URL


def _try_marketplace_insights(
    query: str, limit: int, access_token: str
) -> tuple[list[float], str]:
    """
    Try Marketplace Insights API for sold item prices.

    Returns (list of prices, source_label). Falls back to empty list
    on 403/404 or any error.
    """
    url = _get_insights_url()
    try:
        response = httpx.get(
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
            },
            params={"q": query, "limit": limit, "sort": "price"},
        )
        response.raise_for_status()
        data = response.json()
        items = data.get("itemSales", [])
        prices = []
        for item in items:
            price_val = item.get("lastSoldPrice", {}).get("value")
            if price_val:
                prices.append(float(price_val))
        if prices:
            return prices, "marketplace_insights"
    except (httpx.HTTPStatusError, httpx.RequestError):
        pass
    return [], ""


def _browse_api_prices(
    query: str, limit: int, access_token: str
) -> list[float]:
    """Get current listing prices from Browse API search."""
    from .search import search_items

    items = search_items(
        query, limit=limit, access_token=access_token
    )
    return [item["price"] for item in items if item.get("price")]


def get_valuation(
    item_name: str,
    condition: str = "used",
    token: Optional[str] = None,
    limit: int = 20,
) -> dict:
    """
    Estimate market value for an item based on eBay data.

    Tries Marketplace Insights API first (sold data), falls back to
    Browse API (current listings). Computes price statistics and
    applies a condition-based adjustment factor.

    Args:
        item_name: Search query for the item.
        condition: Item condition key (new, like_new, very_good, good,
                   acceptable, used, for_parts).
        token: Bearer access token. If None, fetches one automatically.
        limit: Max number of listings to analyze.

    Returns:
        Dict with keys: avg, median, min, max, count, adjusted_avg,
        condition, source, recommended_price.

    Raises:
        EnvironmentError: If credentials are missing and no token provided.
    """
    if token is None:
        from .auth import get_app_access_token
        token = get_app_access_token()

    # Try Marketplace Insights first
    prices, source = _try_marketplace_insights(item_name, limit, token)

    # Fall back to Browse API
    if not prices:
        prices = _browse_api_prices(item_name, limit, token)
        source = "browse_api"

    if not prices:
        return {
            "avg": 0,
            "median": 0,
            "min": 0,
            "max": 0,
            "count": 0,
            "adjusted_avg": 0,
            "condition": condition,
            "source": source,
            "recommended_price": 0,
        }

    avg = statistics.mean(prices)
    median = statistics.median(prices)
    price_min = min(prices)
    price_max = max(prices)

    adjustment = CONDITION_ADJUSTMENTS.get(condition.lower(), 0.8)
    adjusted_avg = avg * adjustment
    recommended = adjusted_avg * 0.95  # 5% below adjusted avg

    return {
        "avg": round(avg, 2),
        "median": round(median, 2),
        "min": round(price_min, 2),
        "max": round(price_max, 2),
        "count": len(prices),
        "adjusted_avg": round(adjusted_avg, 2),
        "condition": condition,
        "source": source,
        "recommended_price": round(recommended, 2),
    }
