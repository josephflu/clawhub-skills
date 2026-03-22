---
name: ebay-agent
description: "eBay research agent. Search for deals, compare prices, value items, and track price drops. Uses eBay REST APIs. No eBay account required."
version: 0.3.1
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

Search eBay for deals, compare prices across platforms, value items, and track price drops — all via eBay's official REST APIs.

## Trigger Phrases

- "Search eBay for [item]"
- "Find me a used [item] on eBay"
- "What's [item] worth on eBay?"
- "How much is [item] selling for?"
- "Compare eBay vs Amazon price for [item]"
- "Watch [item] for me and alert if it drops below $X"
- "Is this a good deal on eBay?"

## Commands

### `search` — Find items on eBay

```bash
uv run --project <skill_dir> python <skill_dir>/scripts/cli.py search "Sony 85mm f/1.8 lens"
uv run --project <skill_dir> python <skill_dir>/scripts/cli.py search "iPad Air"
```

Options: `--max-price/-p`, `--condition/-c`, `--limit/-n`, `--sort/-s` (score/price/seller)

### `value` — Estimate what an item is worth

```bash
uv run --project <skill_dir> python <skill_dir>/scripts/cli.py value "iPad Air 2 64GB"
uv run --project <skill_dir> python <skill_dir>/scripts/cli.py value "Sony 85mm f/1.8 lens"
```

Returns average, median, min, max, listing count, and a recommended price based on current market data.

Options: `--condition/-c` (default: used), `--limit/-n` (default: 20)

### `compare` — Compare eBay vs Amazon prices

```bash
ebay-agent compare "Sony 85mm f/1.8 lens" --condition used
ebay-agent compare "iPad Air 2" --max-price 300
```

Shows side-by-side pricing from eBay and Amazon with a savings recommendation.

### `watch add` — Track an item for price drops

```bash
ebay-agent watch add "Sony 85mm lens" --max-price 300 --condition used
ebay-agent watch add "iPad Air" --max-price 200 --threshold 0.15
```

Options: `--max-price/-p` (required), `--condition/-c`, `--threshold/-t` (default 0.10 = 10% drop)

### `watch list` — Show active watches

```bash
ebay-agent watch list
```

### `watch check` — Check for price drops

```bash
ebay-agent watch check
```

### `watch remove` — Remove a watch

```bash
ebay-agent watch remove abc123
```

### `prefs` — View or update search preferences

```bash
uv run --project <skill_dir> python <skill_dir>/scripts/cli.py prefs
```

## Required Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `EBAY_APP_ID` | Yes | eBay app client ID from developer.ebay.com |
| `EBAY_CERT_ID` | Yes | eBay app client secret from developer.ebay.com |
| `EBAY_ENVIRONMENT` | No | `sandbox` or `production` (default: production) |

### How to get eBay credentials

1. Go to [developer.ebay.com](https://developer.ebay.com) and create a free account
2. Create an application to get your App ID and Cert ID
3. Set `EBAY_APP_ID` and `EBAY_CERT_ID` in your environment

## Example workflow

```bash
# Find deals
ebay-agent search "Sony 85mm f/1.8 lens" --max-price 400 --condition used

# Check fair market value
ebay-agent value "Sony 85mm f/1.8 lens"

# Compare with Amazon
ebay-agent compare "Sony 85mm f/1.8 lens"

# Watch for a better price
ebay-agent watch add "Sony 85mm lens" --max-price 300
```
