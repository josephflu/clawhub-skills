# ebay-agent v0.4.0 — Research-Only Cleanup

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a clean, consistent, working v0.4.0 of the published ebay-agent skill that does eBay research only (search, value, prefs) — no broken docs, no dead code, no phantom features.

**Architecture:** Strip SKILL.md to the 3 implemented commands. Fix cli.py to properly wire args through to search/valuation modules. Remove seller OAuth code from auth.py since v1 is research-only (client credentials only). Sync versions and fix docs.

**Tech Stack:** Python 3.12+, uv, httpx, rich, python-dotenv, argparse

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `ebay-agent/SKILL.md` | Modify | Skill manifest — strip to search/value/prefs, fix invocation style, fix env docs |
| `ebay-agent/scripts/cli.py` | Modify | CLI entry point — fix search_items() call, add --max-price/--condition/--limit/--sort flags |
| `ebay-agent/scripts/auth.py` | Modify | OAuth — remove seller flows, keep client credentials only |
| `ebay-agent/scripts/search.py` | Modify | Remove `sys.path` hack (cli.py already handles it) |
| `ebay-agent/scripts/valuation.py` | Modify | Remove `sys.path` hack |
| `ebay-agent/scripts/scoring.py` | Modify | Remove redundant sys.path hack |
| `ebay-agent/scripts/preferences.py` | No change | Already clean |
| `ebay-agent/pyproject.toml` | Modify | Bump version to 0.4.0 |
| `ebay-agent/README.md` | Modify | Rewrite to match actual structure, remove stale src/skill references |
| `ebay-agent/references/*` | No change | Keep all 3 reference docs (useful for future versions) |

---

### Task 1: Fix cli.py — Wire Up Args and Fix search_items() Call

**Files:**
- Modify: `ebay-agent/scripts/cli.py`

The current cli.py has two bugs:
1. `search_items(args.query, prefs)` passes a UserPreferences object as `max_price` — search.py expects individual params
2. No CLI flags are defined for --max-price, --condition, --limit, --sort despite SKILL.md documenting them

- [ ] **Step 1: Read current cli.py to confirm state**

Run: `cat ebay-agent/scripts/cli.py`

- [ ] **Step 2: Replace cli.py with fixed version**

```python
#!/usr/bin/env python3
"""
ebay-agent CLI entry point.

Usage:
    uv run --project <skill_dir> python <skill_dir>/scripts/cli.py search "Sony 85mm lens"
    uv run --project <skill_dir> python <skill_dir>/scripts/cli.py value "iPhone 15 Pro"
    uv run --project <skill_dir> python <skill_dir>/scripts/cli.py prefs
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import argparse


def cmd_search(args):
    from search import search_items
    from preferences import load_preferences
    from scoring import rank_results

    prefs = load_preferences()
    if args.max_price:
        prefs.budget_default = args.max_price

    try:
        items = search_items(
            args.query,
            max_price=args.max_price,
            condition=args.condition,
            limit=args.limit,
        )
        ranked = rank_results(items, prefs)
        if not ranked:
            print("No results found.")
            return

        # Apply sort override
        if args.sort == "price":
            ranked.sort(key=lambda x: x["total_price"])
        elif args.sort == "seller":
            ranked.sort(key=lambda x: float(x.get("seller_feedback_pct") or 0), reverse=True)
        # sort == "score" is the default from rank_results

        try:
            from rich.table import Table
            from rich.console import Console
            console = Console()
            table = Table(title=f"Search: {args.query}")
            table.add_column("#", style="dim", width=3)
            table.add_column("Title", max_width=40)
            table.add_column("Price", justify="right")
            table.add_column("Condition")
            table.add_column("Score", justify="right")
            for i, item in enumerate(ranked[:args.limit], 1):
                table.add_row(
                    str(i),
                    item.get("title", "")[:40],
                    f"${item.get('total_price', 0):.2f}",
                    item.get("condition", ""),
                    str(item.get("score", "")),
                )
            console.print(table)
        except ImportError:
            for i, item in enumerate(ranked[:args.limit], 1):
                print(f"{i}. {item.get('title', '')[:50]} | ${item.get('total_price', 0):.2f} | score={item.get('score', '')}")
    except Exception as e:
        print(f"Search failed: {e}")


def cmd_value(args):
    from valuation import get_valuation

    try:
        result = get_valuation(args.query, condition=args.condition, limit=args.limit)
        if result["count"] == 0:
            print(f"No results found for '{args.query}'.")
            return
        print(f"Valuation for '{args.query}' (condition: {args.condition}):")
        print(f"  Average:           ${result['avg']:.2f}")
        print(f"  Median:            ${result['median']:.2f}")
        print(f"  Range:             ${result['min']:.2f} - ${result['max']:.2f}")
        print(f"  Listings analyzed: {result['count']}")
        print(f"  Source:            {result['source']}")
        print(f"  Condition adj:     {args.condition} ({result['adjusted_avg']:.2f})")
        print(f"  Recommended price: ${result['recommended_price']:.2f}")
    except Exception as e:
        print(f"Valuation failed: {e}")


def cmd_prefs(args):
    from preferences import load_preferences
    prefs = load_preferences()
    print("Current preferences:")
    for k, v in vars(prefs).items():
        print(f"  {k}: {v}")


def main():
    parser = argparse.ArgumentParser(prog="ebay-agent", description="eBay search and valuation agent")
    subparsers = parser.add_subparsers(dest="command")

    p_search = subparsers.add_parser("search", help="Search eBay listings")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--max-price", "-p", type=float, default=None, help="Maximum price in USD")
    p_search.add_argument("--condition", "-c", default=None, help="Condition: new, used, very_good, good, acceptable")
    p_search.add_argument("--limit", "-n", type=int, default=10, help="Number of results (default: 10)")
    p_search.add_argument("--sort", "-s", choices=["score", "price", "seller"], default="score", help="Sort order (default: score)")

    p_value = subparsers.add_parser("value", help="Get market valuation")
    p_value.add_argument("query", help="Item to value")
    p_value.add_argument("--condition", "-c", default="used", help="Condition (default: used)")
    p_value.add_argument("--limit", "-n", type=int, default=20, help="Listings to analyze (default: 20)")

    subparsers.add_parser("prefs", help="Show current preferences")

    args = parser.parse_args()

    if args.command == "search":
        cmd_search(args)
    elif args.command == "value":
        cmd_value(args)
    elif args.command == "prefs":
        cmd_prefs(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Verify syntax**

Run: `cd /Users/jflu/_git/clawhub-skills && python -c "import ast; ast.parse(open('ebay-agent/scripts/cli.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add ebay-agent/scripts/cli.py
git commit -m "fix: ebay-agent cli — wire up args, fix search_items() call"
```

---

### Task 2: Strip auth.py to Client Credentials Only

**Files:**
- Modify: `ebay-agent/scripts/auth.py`

Remove `refresh_user_token()`, `get_user_consent_url()`, `exchange_auth_code()`, `start_local_auth_server()`, and related imports (`http.server`, `urllib.parse`, `webbrowser`). Keep only `get_app_access_token()` and the token cache helpers.

- [ ] **Step 1: Read current auth.py to confirm state**

Run: `cat ebay-agent/scripts/auth.py`

- [ ] **Step 2: Replace auth.py with client-credentials-only version**

```python
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
```

- [ ] **Step 3: Verify syntax**

Run: `cd /Users/jflu/_git/clawhub-skills && python -c "import ast; ast.parse(open('ebay-agent/scripts/auth.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add ebay-agent/scripts/auth.py
git commit -m "fix: ebay-agent auth — remove seller OAuth, keep client credentials only"
```

---

### Task 3: Remove sys.path Hacks from search.py, valuation.py, and scoring.py

**Files:**
- Modify: `ebay-agent/scripts/search.py` (lines 9-10)
- Modify: `ebay-agent/scripts/valuation.py` (lines 8-9)
- Modify: `ebay-agent/scripts/scoring.py` (lines 8-9)

cli.py already does `sys.path.insert(0, os.path.dirname(__file__))`, so the same hack in these modules is redundant. Remove it from all three files.

- [ ] **Step 1: Remove sys.path hack from search.py**

Delete lines 9-10 from `ebay-agent/scripts/search.py`:
```python
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(__file__))
```

- [ ] **Step 2: Remove sys.path hack from valuation.py**

Delete lines 8-9 from `ebay-agent/scripts/valuation.py`:
```python
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(__file__))
```

- [ ] **Step 3: Remove sys.path hack from scoring.py**

Delete lines 8-9 from `ebay-agent/scripts/scoring.py`:
```python
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
```

- [ ] **Step 4: Verify imports resolve via cli.py entry point**

Run:
```bash
cd /Users/jflu/_git/clawhub-skills
uv run --project ebay-agent python ebay-agent/scripts/cli.py prefs
```
Expected: Preferences printed (confirms the full import chain works through cli.py's sys.path setup)

- [ ] **Step 5: Commit**

```bash
git add ebay-agent/scripts/search.py ebay-agent/scripts/valuation.py ebay-agent/scripts/scoring.py
git commit -m "fix: ebay-agent — remove redundant sys.path hacks from search, valuation, scoring"
```

---

### Task 4: Rewrite SKILL.md — Research-Only, Consistent Invocation

**Files:**
- Modify: `ebay-agent/SKILL.md`

Strip to 3 commands (search, value, prefs). All use `uv run --project <skill_dir> python <skill_dir>/scripts/cli.py` consistently. Fix env default doc (sandbox, not production). Bump version to 0.4.0.

- [ ] **Step 1: Read current SKILL.md to confirm state**

Run: `cat ebay-agent/SKILL.md`

- [ ] **Step 2: Replace SKILL.md**

```markdown
---
name: ebay-agent
description: "eBay research agent. Search for deals, value items, and compare prices using eBay REST APIs. No eBay account required — just a free developer API key."
version: 0.4.0
pythonVersion: ">=3.12"
metadata:
  openclaw:
    emoji: "🛒"
    requires:
      env:
        - EBAY_APP_ID
        - EBAY_CERT_ID
      anyBins:
        - uv
    primaryEnv: EBAY_APP_ID
    install:
      - id: brew
        kind: brew
        formula: uv
        bins:
          - uv
        label: "Install uv (Python package manager)"
      - id: pip
        kind: download
        url: https://astral.sh/uv/install.sh
        label: "Install uv via installer script (curl | sh)"
    homepage: https://github.com/josephflu/clawhub-skills
---

# ebay-agent — eBay Research Agent

Search eBay for deals, estimate item values, and rank results by price, seller trust, and condition — all via eBay's official REST APIs.

## Trigger Phrases

- "Search eBay for [item]"
- "Find me a used [item] on eBay"
- "What's [item] worth on eBay?"
- "How much is [item] selling for?"
- "Is this a good deal on eBay?"

## Commands

### `search` — Find items on eBay

```bash
uv run --project <skill_dir> python <skill_dir>/scripts/cli.py search "Sony 85mm f/1.8 lens"
uv run --project <skill_dir> python <skill_dir>/scripts/cli.py search "iPad Air" --max-price 300 --condition used
uv run --project <skill_dir> python <skill_dir>/scripts/cli.py search "Nintendo Switch" --sort price --limit 20
```

Options: `--max-price/-p`, `--condition/-c` (new, used, very_good, good, acceptable), `--limit/-n` (default: 10), `--sort/-s` (score, price, seller)

### `value` — Estimate what an item is worth

```bash
uv run --project <skill_dir> python <skill_dir>/scripts/cli.py value "iPad Air 2 64GB"
uv run --project <skill_dir> python <skill_dir>/scripts/cli.py value "Sony 85mm f/1.8 lens" --condition very_good --limit 30
```

Returns average, median, min, max, listing count, and a recommended price based on current market data. Tries eBay Marketplace Insights (sold data) first, falls back to Browse API (active listings).

Options: `--condition/-c` (default: used), `--limit/-n` (default: 20)

### `prefs` — View search preferences

```bash
uv run --project <skill_dir> python <skill_dir>/scripts/cli.py prefs
```

Shows current scoring preferences: min condition, min seller score, budget, strategy (price/speed/balanced).

## Required Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `EBAY_APP_ID` | Yes | eBay app client ID from developer.ebay.com |
| `EBAY_CERT_ID` | Yes | eBay app client secret from developer.ebay.com |
| `EBAY_ENVIRONMENT` | No | `sandbox` or `production` (default: sandbox) |

### How to get eBay credentials

1. Go to [developer.ebay.com](https://developer.ebay.com) and create a free account
2. Create an application to get your App ID and Cert ID
3. Set `EBAY_APP_ID` and `EBAY_CERT_ID` in your environment

## Example workflow

```bash
# Search for deals
uv run --project <skill_dir> python <skill_dir>/scripts/cli.py search "Sony 85mm f/1.8 lens" --max-price 400 --condition used

# Check fair market value
uv run --project <skill_dir> python <skill_dir>/scripts/cli.py value "Sony 85mm f/1.8 lens"

# View preferences
uv run --project <skill_dir> python <skill_dir>/scripts/cli.py prefs
```
```

- [ ] **Step 3: Commit**

```bash
git add ebay-agent/SKILL.md
git commit -m "fix: ebay-agent SKILL.md — strip to research-only, consistent uv run invocation"
```

---

### Task 5: Sync pyproject.toml Version

**Files:**
- Modify: `ebay-agent/pyproject.toml`

- [ ] **Step 1: Update version to 0.4.0**

Change line 3 of `ebay-agent/pyproject.toml`:
```
version = "0.4.0"
```

- [ ] **Step 2: Commit**

```bash
git add ebay-agent/pyproject.toml
git commit -m "chore: ebay-agent — bump version to 0.4.0"
```

---

### Task 6: Rewrite README.md

**Files:**
- Modify: `ebay-agent/README.md`

The current README references stale `src/`, `skill/`, `listing_gen.py`, and a publish script that don't exist. Rewrite to reflect the actual published structure.

- [ ] **Step 1: Replace README.md**

```markdown
# ebay-agent

> **Alpha — Work in Progress**
> This skill is functional but early. Requires a free eBay Developer API key. Feedback welcome — open an issue on [GitHub](https://github.com/josephflu/clawhub-skills).

eBay research agent for [OpenClaw](https://openclaw.ai). Search for deals, estimate item values, and rank results by price, seller trust, and condition.

Published as **eagerbots/ebay-agent** on [ClawHub](https://clawhub.ai).

## Directory structure

```
ebay-agent/
├── SKILL.md              # Skill manifest with frontmatter + agent instructions
├── pyproject.toml        # Python project config (dependencies)
├── scripts/              # Python modules
│   ├── cli.py            # CLI entry point (argparse)
│   ├── auth.py           # eBay OAuth client credentials
│   ├── search.py         # Browse API search
│   ├── valuation.py      # Market valuation via Insights + Browse APIs
│   ├── scoring.py        # Result ranking by price/trust/condition
│   └── preferences.py    # User preferences (~/.ebay-agent/preferences.json)
└── references/           # Knowledge packs for the agent
    ├── ebay-api-cheatsheet.md
    ├── ebay-scam-detection.md
    └── ebay-selling-guide.md
```

## Quick start

```bash
clawhub install eagerbots/ebay-agent
export EBAY_APP_ID=your_app_id
export EBAY_CERT_ID=your_cert_id
```

Then ask your agent: "Search eBay for Sony 85mm lens under $400"

## Publishing

```bash
clawhub login
clawhub publish ./ebay-agent --slug ebay-agent
```
```

- [ ] **Step 2: Commit**

```bash
git add ebay-agent/README.md
git commit -m "docs: ebay-agent — rewrite README to match actual structure"
```

---

### Task 7: Smoke Test the Full Skill

- [ ] **Step 1: Verify all Python files parse cleanly**

Run:
```bash
cd /Users/jflu/_git/clawhub-skills
for f in ebay-agent/scripts/*.py; do python -c "import ast; ast.parse(open('$f').read()); print('OK: $f')"; done
```
Expected: `OK` for all 6 files

- [ ] **Step 2: Verify CLI help works**

Run:
```bash
cd /Users/jflu/_git/clawhub-skills
uv run --project ebay-agent python ebay-agent/scripts/cli.py --help
uv run --project ebay-agent python ebay-agent/scripts/cli.py search --help
uv run --project ebay-agent python ebay-agent/scripts/cli.py value --help
```
Expected: Help text showing correct args for each command

- [ ] **Step 3: Verify search runs (requires EBAY_APP_ID/EBAY_CERT_ID)**

Run:
```bash
cd /Users/jflu/_git/clawhub-skills
uv run --project ebay-agent python ebay-agent/scripts/cli.py search "test" --limit 3
```
Expected: Either results table or a clear credentials error — NOT a Python traceback from bad args

- [ ] **Step 4: Verify value runs**

Run:
```bash
cd /Users/jflu/_git/clawhub-skills
uv run --project ebay-agent python ebay-agent/scripts/cli.py value "test" --condition used --limit 5
```
Expected: Either valuation output or a clear credentials error

- [ ] **Step 5: Verify prefs runs**

Run:
```bash
cd /Users/jflu/_git/clawhub-skills
uv run --project ebay-agent python ebay-agent/scripts/cli.py prefs
```
Expected: Preferences printed with defaults
