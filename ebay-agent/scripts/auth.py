"""
eBay OAuth 2.0 client credentials authentication.

Supports the client credentials flow (app-level, no user consent required)
for Browse API and Marketplace Insights API access.

Tokens are cached to ~/.ebay-agent/token.json to avoid hitting the eBay token
endpoint on every invocation.
"""

import json
import os
import base64
from datetime import datetime, timezone, timedelta
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

SANDBOX_TOKEN_URL = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
PRODUCTION_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"

# Default scope for Browse API (no user auth required)
BROWSE_SCOPE = "https://api.ebay.com/oauth/api_scope"

TOKEN_CACHE_PATH = Path.home() / ".ebay-agent" / "token.json"
TOKEN_BUFFER = timedelta(minutes=5)


def _get_credentials() -> tuple[str, str]:
    """Load eBay App ID and Cert ID from environment variables."""
    app_id = os.getenv("EBAY_APP_ID")
    cert_id = os.getenv("EBAY_CERT_ID")

    if not app_id or not cert_id:
        raise EnvironmentError(
            "Missing eBay credentials. Set EBAY_APP_ID and EBAY_CERT_ID in your environment."
        )

    return app_id, cert_id


def _get_token_url() -> str:
    """Return the appropriate OAuth token endpoint based on EBAY_ENVIRONMENT."""
    env = os.getenv("EBAY_ENVIRONMENT", "sandbox").lower()
    return SANDBOX_TOKEN_URL if env == "sandbox" else PRODUCTION_TOKEN_URL


def _load_token_cache() -> dict:
    """Read ~/.ebay-agent/token.json, return {} if missing or invalid."""
    try:
        return json.loads(TOKEN_CACHE_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _save_token_cache(cache: dict) -> None:
    """Write cache dict to ~/.ebay-agent/token.json (creates dir if needed)."""
    TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_CACHE_PATH.write_text(json.dumps(cache, indent=2))


def _is_token_valid(token_entry: dict) -> bool:
    """Check if a token entry has expires_at more than 5 minutes in the future."""
    expires_at_str = token_entry.get("expires_at")
    if not expires_at_str:
        return False
    try:
        expires_at = datetime.fromisoformat(expires_at_str)
        return expires_at > datetime.now(timezone.utc) + TOKEN_BUFFER
    except (ValueError, TypeError):
        return False


def get_app_access_token(scope: str = BROWSE_SCOPE) -> str:
    """
    Obtain a client credentials (app-level) OAuth access token.

    Checks the token cache first. If a valid cached token exists, returns it.
    Otherwise fetches a new one and updates the cache.
    """
    cache = _load_token_cache()
    app_entry = cache.get("app_token", {})
    if _is_token_valid(app_entry):
        return app_entry["access_token"]

    app_id, cert_id = _get_credentials()
    token_url = _get_token_url()
    credentials = base64.b64encode(f"{app_id}:{cert_id}".encode()).decode()

    response = httpx.post(
        token_url,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "client_credentials",
            "scope": scope,
        },
    )
    response.raise_for_status()
    data = response.json()

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"]) - TOKEN_BUFFER
    cache["app_token"] = {
        "access_token": data["access_token"],
        "expires_at": expires_at.isoformat(),
    }
    _save_token_cache(cache)

    return data["access_token"]
