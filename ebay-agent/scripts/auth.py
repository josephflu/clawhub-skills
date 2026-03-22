"""
eBay OAuth 2.0 authentication module.

Supports the client credentials flow (app-level, no user consent required)
for Browse API access, and the Authorization Code flow for seller-level
operations (Inventory, Fulfillment, Account APIs).

Tokens are cached to ~/.ebay-agent/token.json to avoid hitting the eBay token
endpoint on every CLI invocation.
"""

import json
import os
import base64
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import httpx
from dotenv import load_dotenv

load_dotenv()

SANDBOX_TOKEN_URL = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
PRODUCTION_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"

SANDBOX_AUTH_URL = "https://auth.sandbox.ebay.com/oauth2/authorize"
PRODUCTION_AUTH_URL = "https://auth.ebay.com/oauth2/authorize"

# Default scope for Browse API (no user auth required)
BROWSE_SCOPE = "https://api.ebay.com/oauth/api_scope"

# Default scopes for seller features
SELL_SCOPES = [
    "https://api.ebay.com/oauth/api_scope/sell.inventory",
    "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
    "https://api.ebay.com/oauth/api_scope/sell.account",
]

TOKEN_CACHE_PATH = Path.home() / ".ebay-agent" / "token.json"
TOKEN_BUFFER = timedelta(minutes=5)


def _get_credentials() -> tuple[str, str]:
    """
    Load eBay App ID and Cert ID from environment variables.

    Returns:
        Tuple of (app_id, cert_id)

    Raises:
        EnvironmentError: If credentials are not set in .env
    """
    app_id = os.getenv("EBAY_APP_ID")
    cert_id = os.getenv("EBAY_CERT_ID")

    if not app_id or not cert_id:
        raise EnvironmentError(
            "Missing eBay credentials. Set EBAY_APP_ID and EBAY_CERT_ID in your .env file."
        )

    return app_id, cert_id


def _get_token_url() -> str:
    """Return the appropriate OAuth token endpoint based on EBAY_ENVIRONMENT."""
    env = os.getenv("EBAY_ENVIRONMENT", "sandbox").lower()
    return SANDBOX_TOKEN_URL if env == "sandbox" else PRODUCTION_TOKEN_URL


def _get_auth_url() -> str:
    """Return the appropriate OAuth authorization URL based on EBAY_ENVIRONMENT."""
    env = os.getenv("EBAY_ENVIRONMENT", "sandbox").lower()
    return SANDBOX_AUTH_URL if env == "sandbox" else PRODUCTION_AUTH_URL


# --- Token cache helpers ---


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


# --- Client Credentials flow (app-level) ---


def get_app_access_token(scope: str = BROWSE_SCOPE) -> str:
    """
    Obtain a client credentials (app-level) OAuth access token.

    Checks the token cache first. If a valid cached token exists, returns it.
    Otherwise fetches a new one and updates the cache.

    Args:
        scope: OAuth scope string. Defaults to the public Browse API scope.

    Returns:
        Bearer access token string.
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


# --- Refresh Token flow (user-level) ---


def refresh_user_token(refresh_token: str, scope: str = BROWSE_SCOPE) -> str:
    """
    Exchange a refresh token for a new user-level access token.

    Caches the returned token. Preserves the refresh_token in the cache.

    Args:
        refresh_token: Long-lived refresh token from the initial OAuth flow.
        scope: OAuth scope string for the desired API access.

    Returns:
        New bearer access token string.
    """
    cache = _load_token_cache()
    user_entry = cache.get("user_token", {})
    if _is_token_valid(user_entry):
        return user_entry["access_token"]

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
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": scope,
        },
    )
    response.raise_for_status()
    data = response.json()

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"]) - TOKEN_BUFFER
    cache["user_token"] = {
        "access_token": data["access_token"],
        "expires_at": expires_at.isoformat(),
        "refresh_token": refresh_token,
    }
    _save_token_cache(cache)

    return data["access_token"]


# --- Authorization Code flow (user OAuth) ---


def get_user_consent_url(scopes: list[str] | None = None) -> str:
    """Build the eBay OAuth consent URL for the Authorization Code flow."""
    app_id, _ = _get_credentials()
    ru_name = os.getenv("EBAY_RU_NAME")
    if not ru_name:
        raise EnvironmentError("Missing EBAY_RU_NAME. Set it in your .env file.")

    if scopes is None:
        scopes = SELL_SCOPES

    auth_url = _get_auth_url()
    params = (
        f"?client_id={app_id}"
        f"&response_type=code"
        f"&redirect_uri={ru_name}"
        f"&scope={' '.join(scopes)}"
    )
    return auth_url + params


def exchange_auth_code(code: str) -> dict:
    """
    Exchange an authorization code for access + refresh tokens.

    Saves the result to the token cache as user_token.

    Returns:
        Token response dict (access_token, refresh_token, expires_in).
    """
    app_id, cert_id = _get_credentials()
    ru_name = os.getenv("EBAY_RU_NAME")
    if not ru_name:
        raise EnvironmentError("Missing EBAY_RU_NAME. Set it in your .env file.")

    token_url = _get_token_url()
    credentials = base64.b64encode(f"{app_id}:{cert_id}".encode()).decode()

    response = httpx.post(
        token_url,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": ru_name,
        },
    )
    response.raise_for_status()
    data = response.json()

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"]) - TOKEN_BUFFER
    cache = _load_token_cache()
    cache["user_token"] = {
        "access_token": data["access_token"],
        "expires_at": expires_at.isoformat(),
        "refresh_token": data.get("refresh_token", ""),
    }
    _save_token_cache(cache)

    return data


def start_local_auth_server(port: int = 8080) -> str:
    """
    Start a minimal HTTP server on localhost:{port} that waits for a callback with an auth code.

    Returns the captured auth code. Times out after 120 seconds.
    """
    captured_code: list[str] = []

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            code = params.get("code", [None])[0]
            if code:
                captured_code.append(code)
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<h1>Authorization successful!</h1>"
                    b"<p>You can close this tab and return to the terminal.</p>"
                )
            else:
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Missing authorization code.</h1>")

        def log_message(self, format, *args):
            pass  # suppress server logs

    server = HTTPServer(("localhost", port), CallbackHandler)
    server.timeout = 120

    # Handle one request (with timeout)
    server.handle_request()
    server.server_close()

    if not captured_code:
        raise TimeoutError("No authorization code received within 120 seconds.")

    return captured_code[0]
