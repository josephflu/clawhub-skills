# ClawHub Skill Package — ebay-agent

This directory contains the ClawHub publish-ready version of the ebay-agent skill.

## Relationship to the prototype

- `src/` — The full CLI prototype (uses typer, rich, etc.)
- `skill/` — The packaged skill for ClawHub (scripts + references + SKILL.md)

The `skill/scripts/` files are copies of `src/` modules. Before publishing, run the publish script to sync the latest source.

## Directory structure

```
skill/
├── SKILL.md              # Skill manifest with frontmatter
├── scripts/              # Python modules copied from src/
│   ├── auth.py
│   ├── search.py
│   ├── scoring.py
│   ├── preferences.py
│   ├── valuation.py
│   └── listing_gen.py
└── references/           # Knowledge packs for the agent
    ├── ebay-selling-guide.md
    ├── ebay-scam-detection.md
    └── ebay-api-cheatsheet.md
```

## Publishing

Publish under the **EagerBots** account (not josephflu):

```bash
bash scripts/publish_skill.sh   # syncs src/ -> skill/scripts/ first
clawhub login                   # login as EagerBots
clawhub publish ./skill --slug ebay-agent --version 0.1.0
```
