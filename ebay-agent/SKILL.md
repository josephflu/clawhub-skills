---
name: ebay-agent
description: "Personal eBay buying and selling agent. Search for deals, compare prices, value items, and generate optimized listings. Uses eBay REST APIs."
version: 0.1.0
metadata:
  openclaw:
    emoji: "🛒"
    requires:
      env:
        - EBAY_APP_ID
        - EBAY_CERT_ID
      optionalEnv:
        - EBAY_USER_TOKEN
        - OPENROUTER_API_KEY
      anyBins:
        - uv
    primaryEnv: EBAY_APP_ID
    install:
      - id: brew
        kind: brew
        formula: uv
        bins:
          - uv
        label: "Install uv (Python package manager, required for ClawBay)"
      - id: pip
        kind: download
        url: https://astral.sh/uv/install.sh
        label: "Install uv via installer script (curl | sh)"
    homepage: https://github.com/josephflu/clawbay-prototype
---

# ebay-agent — eBay Shopping & Selling Agent

Personal eBay buying and selling agent for OpenClaw. Searches for deals, values items, generates optimized listings, and manages the full buyer/seller workflow via eBay REST APIs.

Published under **eagerbots/ebay-agent** on ClawHub.

## Trigger Phrases

Use this skill when the user says things like:

- "Search eBay for [item]"
- "Find me a used [item] on eBay"
- "What's my [item] worth?"
- "How much is [item] selling for on eBay?"
- "Generate an eBay listing for [item]"
- "List my [item] on eBay"
- "What condition should I list my [item] as?"
- "Help me sell [item]"

## Commands

### `search` — Find items on eBay

```bash
ebay-agent search "Sony 85mm f/1.8 lens" --max-price 400 --condition very_good
ebay-agent search "iPad Air 2" --limit 20 --sort price --json
```

Options: `--max-price/-p`, `--condition/-c`, `--limit/-n`, `--sort/-s` (score/price/seller), `--json`

### `value` — Estimate what an item is worth

```bash
ebay-agent value "iPad Air 2 64GB" --condition good
ebay-agent value "Sony 85mm f/1.8 lens" --limit 30
```

Options: `--condition/-c` (default: used), `--limit/-n` (default: 20)

Returns average, median, min, max, listing count, and a recommended price (5% below condition-adjusted average).

### `compare` — Compare eBay vs Amazon prices

```bash
ebay-agent compare "Sony 85mm f/1.8 lens" --condition used
ebay-agent compare "iPad Air 2" --max-price 300
```

Shows side-by-side pricing from eBay and Amazon with a savings recommendation.
No additional API key required.

Options: `--max-price/-p`, `--condition/-c`

### `generate-listing` — Create an optimized eBay listing with AI

```bash
ebay-agent generate-listing "Apple iPad Air 2 64GB Space Gray" --condition good
```

Uses an LLM via OpenRouter to generate an SEO-optimized title (80 char max), description, item specifics, and suggested category.

Requires `OPENROUTER_API_KEY` (optional — set to enable this command).

### `watch add` — Add a price watch

```bash
ebay-agent watch add "Sony 85mm lens" --max-price 300 --condition used
ebay-agent watch add "iPad Air" --max-price 200 --threshold 0.15
```

Saves a search to the watchlist for price tracking. Options: `--max-price/-p` (required), `--condition/-c`, `--threshold/-t` (default 0.1 = 10%)

### `watch list` — Show all active watches

```bash
ebay-agent watch list
```

Displays a table of all watched searches with last checked time and best price.

### `watch remove` — Remove a watch

```bash
ebay-agent watch remove abc123
```

Removes a watch by ID prefix.

### `watch check` — Check for price drops

```bash
ebay-agent watch check
```

Searches eBay for each watched item and alerts on price drops exceeding the threshold. Requires eBay credentials.

### `auth login` — Authenticate with eBay

```bash
ebay-agent auth login
```

Opens the eBay OAuth consent page in your browser. Required for seller operations (inventory, offers).

### `auth status` — Check token status

```bash
ebay-agent auth status
```

Shows whether app and user tokens are cached and valid.

### `prefs` — View or update preferences

```bash
ebay-agent prefs
ebay-agent prefs --strategy price --budget 300 --min-condition very_good
```

Options: `--min-condition`, `--min-seller-score`, `--max-shipping-days`, `--budget`, `--strategy` (price/speed/balanced)

## Required Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `EBAY_APP_ID` | Yes | eBay app client ID from developer.ebay.com |
| `EBAY_CERT_ID` | Yes | eBay app client secret from developer.ebay.com |
| `EBAY_RU_NAME` | For auth login | eBay redirect URL name (RuName) for OAuth |
| `EBAY_USER_TOKEN` | For selling | User OAuth token (obtained via `auth login`) |
| `EBAY_ENVIRONMENT` | No | `sandbox` or `production` (default) |
| `OPENROUTER_API_KEY` | For listings | Optional. Enables `generate-listing` via OpenRouter LLMs |

### How to get eBay credentials

1. Go to [developer.ebay.com](https://developer.ebay.com) and create a free account
2. Create an application to get your App ID (client_id) and Cert ID (client_secret)
3. Copy `.env.example` to `.env` and fill in the values
4. For seller features, configure an RuName and run `ebay-agent auth login`

## Usage Examples

**Buyer workflow:**
```bash
# Find deals on a specific item
ebay-agent search "Sony 85mm f/1.8 lens" --max-price 400 --condition used

# Check what it's worth before buying
ebay-agent value "Sony 85mm f/1.8 lens"

# Adjust your preferences for future searches
ebay-agent prefs --strategy price --budget 350
```

**Seller workflow:**
```bash
# Check market value before listing
ebay-agent value "iPad Air 2 64GB" --condition good

# Generate an optimized listing
ebay-agent generate-listing "Apple iPad Air 2 64GB Space Gray" --condition good

# Authenticate for seller operations
ebay-agent auth login
```

## Note

Published under **eagerbots/ebay-agent** on [ClawHub](https://clawhub.ai). The first eBay API automation skill on ClawHub -- a fully functional agent that calls real eBay REST APIs, not just a static reference guide.
