"""
User preferences for eBay search scoring and filtering.

Loads/saves preferences from ~/.ebay-agent/preferences.json.
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

PREFS_DIR = Path.home() / ".ebay-agent"
PREFS_FILE = PREFS_DIR / "preferences.json"


@dataclass
class UserPreferences:
    min_condition: str = "good"  # acceptable minimum: new, like_new, very_good, good, acceptable
    min_seller_score: float = 95.0  # percent positive feedback
    max_shipping_days: int = 7
    require_free_returns: bool = False
    budget_default: float = 500.0
    price_vs_speed: str = "balanced"  # price, speed, balanced


def load_preferences() -> UserPreferences:
    """Load preferences from disk, or return defaults if none saved."""
    if PREFS_FILE.exists():
        data = json.loads(PREFS_FILE.read_text())
        return UserPreferences(**{k: v for k, v in data.items() if k in UserPreferences.__dataclass_fields__})
    return UserPreferences()


def save_preferences(prefs: UserPreferences) -> None:
    """Save preferences to ~/.ebay-agent/preferences.json."""
    PREFS_DIR.mkdir(parents=True, exist_ok=True)
    PREFS_FILE.write_text(json.dumps(asdict(prefs), indent=2) + "\n")
