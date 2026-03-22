"""Generate optimized eBay listings using an LLM via OpenRouter."""

import json
import os

import httpx


OPENROUTER_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "anthropic/claude-sonnet-4-6"

SYSTEM_PROMPT = """\
You are an expert eBay listing optimizer. Given an item name and condition, \
generate an optimized eBay listing as a JSON object with these fields:

- "title": max 80 characters. Format: [Brand] [Model] [Specs] [Condition] [Key Features]. \
Front-load searchable terms and model numbers. No filler words (WOW, LOOK, L@@K). \
Include color and size if applicable.
- "description": honest, condition-appropriate, 3-5 sentences covering key details.
- "item_specifics": dict of key-value pairs (Brand, Model, Color, Storage, etc.) \
matching eBay's expected item aspects for this category.
- "suggested_category": string with eBay category name and numeric ID if known, \
e.g. "Tablets & eBook Readers (171485)".

Return ONLY valid JSON, no markdown fences or extra text."""


def generate_listing(item_name: str, condition: str) -> dict:
    """Call an LLM via OpenRouter to generate an optimized eBay listing."""
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No LLM API key found. Set OPENROUTER_API_KEY (or ANTHROPIC_API_KEY) in your .env file."
        )

    # Use OpenRouter if key starts with sk-or-, otherwise fall back to Anthropic direct
    if api_key.startswith("sk-or-"):
        base_url = OPENROUTER_BASE
        model = os.getenv("LISTING_GEN_MODEL", DEFAULT_MODEL)
    else:
        base_url = "https://api.anthropic.com/v1"
        model = "claude-sonnet-4-6"

    response = httpx.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/josephflu/clawbay-prototype",
            "X-Title": "ClawBay eBay Agent",
        },
        json={
            "model": model,
            "max_tokens": 1024,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Item: {item_name}\nCondition: {condition}"},
            ],
        },
        timeout=30,
    )
    response.raise_for_status()

    text = response.json()["choices"][0]["message"]["content"].strip()

    # Strip markdown fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0].strip()

    return json.loads(text)
