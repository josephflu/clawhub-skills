# ebay-agent v0.6 Roadmap

**Repo:** `clawhub-skills`
**Branch:** `dev`
**Target skill:** `ebay-agent`
**Status:** planned
**Date:** 2026-03-24

---

## Goal

Make `ebay-agent` meaningfully more useful as a **buyer-side research assistant** while staying safely within the current product boundary:

- read-only
- no seller automation
- no listing creation
- no inventory writes
- no order flow

The focus for v0.6 is to help a user answer:

1. **Is this listing a good deal?**
2. **What price range is fair?**
3. **Which results are actually relevant, not accessories/noise?**
4. **When should I wait vs buy now?**

---

## Scope

### In scope
- `deal` command
- search relevance cleanup
- valuation improvements
- confidence / explanation improvements
- docs and examples

### Out of scope
- seller auth
- listing generation
- inventory / offer APIs
- dropshipping workflows
- posting to eBay
- persistent watchlists (unless implemented purely as stateless examples)

---

## Proposed Releases

### v0.6.0
- `deal` command
- search cleanup / relevance improvements
- valuation confidence + fair range

### v0.6.1
- alerts / saved watches (optional, only if we decide to re-introduce safe persistence or a stateless webhook pattern)

### v0.7.0
- `analyze` command for market overview

---

## Feature 1 — `deal` command

### User stories
- "Is this Sony 85mm lens a good deal?"
- "Evaluate this eBay listing URL"
- "What's a good price for this item?"

### Command shapes

```bash
ebay-agent deal "Sony FE 85mm f/1.8"
ebay-agent deal "Sony FE 85mm f/1.8" --condition used
ebay-agent deal "https://www.ebay.com/itm/..."
```

### Expected output

- estimated fair range
- recommended buy threshold
- listing price vs fair range
- recommendation label:
  - `great deal`
  - `good deal`
  - `fair`
  - `overpriced`
  - `suspicious`
- concise explanation
- comparable listings used

### Implementation notes

#### Query mode
- search top relevant listings
- remove obvious accessories / unrelated items
- compute valuation stats from cleaned results
- derive a fair range

#### URL mode
- parse item id from eBay URL if possible
- fetch listing details
- search comparable listings by title/model keywords
- compare current listing vs comp set

### Simple scoring rubric

Example thresholds:
- `great deal`: <= 85% of median comp price
- `good deal`: <= 93% of median comp price
- `fair`: within ±10% of fair range
- `overpriced`: > 110% of fair range
- `suspicious`: very cheap + low seller signal / vague title / stock-photo pattern

---

## Feature 2 — Search relevance cleanup

### Problem
Current search can still surface accessories or near-matches for some queries.

### Goals
- prefer the actual product over accessories
- prefer exact / near-exact title matches
- reduce junk in comps and search tables

### Tactics

#### 1. Negative keyword filtering
Start with a simple blocklist for common accessory terms:
- case
- cover
- protector
- charger
- cable
- skin
- decal
- sticker
- holster
- screen protector
- keyboard cover
- replacement strap
- empty box

#### 2. Exact-model bonus
Boost items whose title contains the core query tokens in order.

#### 3. Category heuristics
Where possible, favor likely product categories inferred from the query.

#### 4. Query normalization
Strip noise terms and preserve product model anchors:
- `Sony FE 85mm f/1.8`
- `iPad Air M2`
- `MacBook Pro M3`

#### 5. Explain filtering in debug mode
Add optional `--debug` output later to explain why results were filtered.

---

## Feature 3 — Valuation improvements

### Problem
Current valuation is better than before but still simplistic.

### Goals
- more trustworthy fair value output
- less skew from extreme outliers
- clearer confidence and assumptions

### Improvements

#### 1. Outlier trimming
Use trimmed stats instead of raw mean when enough results exist.

Options:
- trim top/bottom 10%
- or IQR-based filtering

#### 2. Range output
Instead of only average/median, output:
- fair range low
- fair range high
- median
- confidence

#### 3. Condition-aware range
Map result conditions into a normalized score and weight them appropriately.

#### 4. Signal quality detection
If too few relevant comps survive filtering, say so clearly:
- `confidence: low`
- `market signal is sparse`

#### 5. Source labeling
Continue to prefer sold/insight data when available; otherwise clearly label browse-based estimates as active-listing-derived.

---

## Feature 4 — Confidence and explanations

### Goal
Make outputs feel less like raw stats and more like an assistant judgment.

### Additions
- confidence level: `low / medium / high`
- reason summary:
  - comp count
  - relevance quality
  - condition consistency
  - price spread width

### Example

```text
Fair value: $330–$380
Confidence: medium
Why: 12 relevant comps, modest spread, mostly used copies, one low-price outlier removed.
Recommendation: good deal below $325.
```

---

## Optional Feature — Saved alerts (defer unless clearly worth it)

Potential commands:

```bash
ebay-agent alert add "Sony FE 85mm f/1.8" --below 325
ebay-agent alert check
```

### Caution
This may reintroduce persistence / security-review concerns if implemented via disk writes. If we do it, prefer:
- explicit opt-in
- clear file location
- maybe defer until product direction is clearer

---

## Technical notes

### Current repo reality
`ebay-agent` is now a self-contained uv package and published on ClawHub.

### Files likely to change
- `ebay-agent/scripts/cli.py`
- `ebay-agent/scripts/search.py`
- `ebay-agent/scripts/scoring.py`
- `ebay-agent/scripts/valuation.py`
- `ebay-agent/README.md`
- `ebay-agent/SKILL.md`

### Suggested new module
Potentially add:
- `ebay-agent/scripts/deal.py`

Responsibilities:
- evaluate listing/query
- compute fair range
- assign rating
- summarize rationale

---

## Acceptance criteria for v0.6.0

### `deal`
- user can run `ebay-agent deal "query"`
- receives fair range + recommendation + explanation
- output is stable and understandable

### relevance
- obvious accessories are filtered for common product searches
- `Sony 85mm lens` returns lenses, not caps/skins
- `MacBook Pro M3` returns computers, not keyboard covers

### valuation
- outputs fair range, not just average
- reports confidence
- trims obvious outliers

### quality
- no new disk writes unless explicitly intended
- no new security scanner regressions on ClawHub
- README updated with examples

---

## Recommended next step

Implement **Feature 1 (`deal`)** first, but do it together with the relevance cleanup so the comps are trustworthy.

That gives the most visible user value for the least conceptual sprawl.
