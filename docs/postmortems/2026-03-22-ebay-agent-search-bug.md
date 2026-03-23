# Post-Mortem: ebay-agent Search Returning No Results (v0.4.0)

**Date:** 2026-03-22  
**Fixed in:** v0.4.1  
**Severity:** High — core search command returned "No results found" for all queries

---

## What Happened

After Claude Code's v0.4.0 cleanup, `ebay-agent search "MacBook Pro M3"` returned "No results found" for all queries. The eBay API was returning results fine — the bug was entirely in the scoring/filtering layer.

Two separate bugs combined to filter out every result:

### Bug 1: Condition string mismatch

`CONDITION_SCORES` in `scoring.py` used eBay's internal condition labels (`"Very Good"`, `"Good"`, `"Acceptable"`) but the Browse API returns different strings in the response (`"Used"`, `"Open box"`, `"Pre-owned"`).

Any condition not in the map defaulted to `0.4`, which is below the default `min_condition` floor of `"good"` (0.55). So **every item was filtered out**.

**Fix:** Added the actual API response strings to `CONDITION_SCORES`:
```python
"Open box": 0.85,
"Used": 0.6,
"Pre-owned": 0.6,
"Like New": 0.7,
```

### Bug 2: Seller feedback filter treating missing data as 0%

The Browse API often returns `seller_feedback_pct: 0.0` when feedback data is simply unavailable (not when the seller has 0% positive feedback). The filter treated `0.0` as a real score, which is below the default `min_seller_score` of 95%, filtering out all items without feedback data.

**Fix:** Skip the filter when feedback is `0.0`:
```python
if feedback and float(feedback) > 0 and float(feedback) < prefs.min_seller_score:
    continue
```

### Bug 3 (related): `bestMatch` vs `best_match`

Claude Code changed the eBay API sort param from `"price"` to `"bestMatch"` but the Browse API uses snake_case: `"best_match"`. The invalid param caused eBay to return zero results before our filters even ran.

**Fix:** `"sort": "best_match"`

---

## Root Cause

The skill scripts were originally part of a larger prototype (`clawbay-prototype`) where they were tested against the real eBay API continuously. When extracted into a standalone skill, these integration assumptions weren't re-validated.

The condition string mismatch specifically was a **silent assumption** — the code looked correct but was never tested against live API responses in the new context.

---

## Lessons for Claude Code

1. **Always test against the real API after refactoring** — `uv run --project . ebay-agent search "iPhone" --limit 3` is the smoke test. If it returns "No results found", something is wrong upstream.

2. **eBay Browse API condition strings ≠ eBay condition filter IDs** — The `filter=conditionIds:{...}` parameter uses numeric IDs. The response `condition` field uses human-readable strings like `"Used"`, `"Open box"`. These are different systems.

3. **Missing data ≠ bad data** — When an API field returns `0`, `""`, or `null`, check whether that means "zero" or "not provided" before filtering on it.

4. **Sort params are case-sensitive** — eBay Browse API uses `best_match` not `bestMatch`. Always check the API docs when changing sort parameters.

5. **The scoring layer is a common failure point** — `rank_results()` silently returns an empty list when all items are filtered. Add a debug mode or log how many items were filtered and why.

---

## Suggested Improvement: Debug Mode

Consider adding `--debug` flag to `cli.py` that prints filtering stats:
```
[debug] search_items returned 10 items
[debug] rank_results filtered 10/10 items (condition below floor: 10, feedback too low: 0)
[debug] No results after filtering.
```

This would have made the bug immediately obvious.
