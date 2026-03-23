# ebay-agent

> **Alpha — Work in Progress**
> This skill is functional but early. Requires a free eBay Developer API key. Feedback welcome — open an issue on [GitHub](https://github.com/josephflu/clawhub-skills).

eBay research agent for [OpenClaw](https://openclaw.ai). Search for deals, estimate item values, and rank results by price, seller trust, and condition.

Published as **eagerbots/ebay-agent** on [ClawHub](https://clawhub.ai).

## Directory structure

```
ebay-agent/
├── SKILL.md              # Skill manifest with frontmatter + agent instructions
├── pyproject.toml        # Python project config (dependencies, entry point)
├── scripts/              # Python package
│   ├── __init__.py
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
