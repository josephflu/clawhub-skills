# ClawHub Security Scanner — Rules & Guidelines

> Reference for publishing skills that pass ClawHub's security scan cleanly.
> Based on real experience getting `ebay-agent` flagged and fixed (March 2026).

---

## How the Scanner Works

ClawHub runs two checks on every published skill:
1. **VirusTotal** — scans all files in the bundle for known malware signatures
2. **OpenClaw AI analysis** — reviews code patterns for suspicious behavior

Results: **Clean**, **Suspicious** (medium/high confidence), or **Pending** (scan in progress).

A "Suspicious" flag doesn't mean malware — it means the skill matched patterns the scanner considers risky. False positives are common for legitimate skills that handle credentials or make HTTP calls.

---

## What Gets You Flagged

### 🚨 HIGH RISK — Will likely flag

| Pattern | Why it flags | Fix |
|---------|-------------|-----|
| `curl \| sh` installer in SKILL.md | Classic malware delivery vector | Use `brew install` or `pip install` only |
| Writing files to `~/.` (home dir) | Persistence mechanism used by malware | Avoid disk writes; use env vars or in-memory |
| `subprocess.run(["bash", ...])` | Arbitrary shell execution | Use Python stdlib or specific binaries only |
| `os.system(...)` | Same as above | Avoid entirely |
| `eval(...)` | Code injection | Never use |
| Base64 encoding of credentials | Obfuscation pattern | OK if clearly documented (e.g. OAuth Basic auth) |

### ⚠️ MEDIUM RISK — May flag depending on context

| Pattern | Why it flags | Mitigation |
|---------|-------------|------------|
| Writing `token.json` or cache files | Persistence + credential storage | Remove caching; fetch fresh tokens per invocation |
| `import subprocess` | Subprocess abuse | OK if used for known safe bins (e.g. `dig`, `whois`) |
| HTTP calls to external APIs | Data exfiltration concern | Document all external URLs in SKILL.md |
| `.env` file loading via `python-dotenv` | Credential harvesting pattern | Fine, but make sure `.env` isn't in the bundle |
| `base64` module usage | Obfuscation | Fine for OAuth; add a comment explaining why |

### ✅ SAFE — These are fine

- `httpx` / `requests` calls to well-known APIs (eBay, GitHub, Yahoo Finance, etc.)
- Standard library only skills
- Skills with no external network calls
- `brew install` / `pip install` as install method
- Reading env vars via `os.getenv()`

---

## Best Practices for Clean Skills

### 1. No disk writes
Avoid writing files to the user's filesystem unless absolutely necessary. Token caching is convenient but triggers persistence flags. Fetch fresh tokens per invocation — client credential tokens are fast.

### 2. No `curl | sh`
Never use the download installer pattern in SKILL.md `install` entries. Use:
```yaml
install:
  - id: brew
    kind: brew
    formula: your-dep
  - id: pip
    kind: pip
    package: your-dep
```

### 3. Document all external URLs
In SKILL.md, list every external domain the skill calls:
```markdown
## External Services
- `api.ebay.com` — eBay Browse and Taxonomy APIs (HTTPS)
```

### 4. Keep `auth.py` minimal
OAuth code triggers scanner attention. Keep it to the minimum needed. Don't include seller OAuth flows in a read-only skill.

### 5. Never include `.env` in the bundle
Add `.env` to `.gitignore`. ClawHub publishes from the local directory — if `.env` is present it gets uploaded. Use `.env.example` instead with placeholder values.

### 6. Use `--json` flag for agent-friendly output
Skills with `--json` output flags are more useful to agents and show intentional design, which builds trust.

---

## If You Get Flagged

1. Read the security report on the ClawHub skill page
2. Identify which patterns triggered it (curl|sh, disk writes, etc.)
3. Fix the issues and publish a new version
4. File a GitHub issue at https://github.com/openclaw/clawhub/issues using the template in `docs/drafts/clawhub-false-positive-issue.md`
5. The scan runs automatically on each new version — no need to request manually

---

## Related Files
- `docs/drafts/clawhub-false-positive-issue.md` — issue template for requesting rescan
- `docs/postmortems/2026-03-22-ebay-agent-search-bug.md` — post-mortem on search bug
