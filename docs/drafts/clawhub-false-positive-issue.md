# GitHub Issue Draft — openclaw/clawhub

**Title:** Security review request: ebay-agent flagged as suspicious — issues addressed, requesting rescan

**Repo:** https://github.com/openclaw/clawhub/issues

---

**Body:**

## Skill

- **Slug:** ebay-agent
- **Publisher:** josephflu
- **URL:** https://clawhub.ai/josephflu/ebay-agent
- **Source:** https://github.com/josephflu/clawhub-skills/tree/main/ebay-agent

## Summary

`ebay-agent` was flagged as suspicious by ClawHub's OpenClaw analysis (VirusTotal scan came back benign). I've reviewed the scan report and addressed both flagged issues. Requesting a rescan.

## What the skill does

- Searches eBay listings via the Browse API
- Estimates item market value using listing/sold data
- Ranks results by a scoring formula (price, seller trust, condition)
- All API calls go to `api.ebay.com` (eBay's official endpoints)
- Requires `EBAY_APP_ID` and `EBAY_CERT_ID` environment variables (free at developer.ebay.com)

## Scanner findings and fixes

### 1. Install Mechanism — `curl | sh` installer (PRIMARY CONCERN)

**What was flagged:** The skill metadata included a `curl | sh` download installer (`https://astral.sh/uv/install.sh`) as an install option for the `uv` dependency.

**Fix:** Removed the `curl | sh` installer entirely. Install options are now limited to Homebrew (`brew install uv`) and pip (`pip install uv`).

**Commit:** https://github.com/josephflu/clawhub-skills/commit/94cc76a

### 2. Persistence & Privilege — Token cache at `~/.ebay-agent/token.json`

**What was flagged:** The skill cached OAuth access tokens to `~/.ebay-agent/token.json` and user preferences to `~/.ebay-agent/preferences.json`, writing files to the user's home directory.

**Fix:** Removed all disk writes. The skill no longer writes any files to the filesystem. Fresh OAuth tokens are fetched per invocation (client credentials tokens are fast and free). Preferences use hardcoded defaults.

**Commit:** https://github.com/josephflu/clawhub-skills/commit/0b1a51d

### 3. Credentials — base64 encoding (not a concern per scanner)

The scanner marked this as ✓ (passing). The `base64.b64encode()` usage is required by eBay's OAuth 2.0 spec for HTTP Basic authentication per [RFC 6749 Section 2.3.1](https://datatracker.ietf.org/doc/html/rfc6749#section-2.3.1). All HTTP requests go only to `api.ebay.com` and `api.sandbox.ebay.com`.

## Current state of the skill

After fixes, the skill:
- Does **not** write any files to disk
- Does **not** cache tokens or credentials
- Does **not** use `curl | sh` or download installers
- Does **not** exfiltrate data — all HTTP requests go only to eBay's official API endpoints
- Does **not** use `exec`, `eval`, `subprocess`, or `os.system`
- Has **no network servers**
- VirusTotal scan: **benign**

## Request

Please rescan and clear the suspicious flag. Both issues identified in the scan report have been addressed. The full source is public at the GitHub link above. Happy to answer any questions.

---

**Labels:** `false-positive`, `security-review`
