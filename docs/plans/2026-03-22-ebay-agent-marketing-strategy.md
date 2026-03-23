# ebay-agent Marketing & Growth Strategy

**Goal:** Drive organic adoption of eagerbots/ebay-agent on ClawHub, establish EagerBots as a credible skill publisher, and build toward a full eBay agent product.

**Current state:** v0.4.1 published, research-only (search, value, prefs). First eBay API skill on ClawHub. ~3,300 skills on the platform, 13,000+ total in the registry.

---

## 1. Pre-Launch Checklist (Before Marketing)

### Verify Skill Quality
- [ ] Run a full test with 10+ diverse search queries (electronics, clothing, collectibles, vehicles) and document results
- [ ] Confirm error messages are clear for all failure modes (bad credentials, no results, API rate limits)
- [ ] Check that the skill passes ClawHub's VirusTotal scanning cleanly
- [ ] Test installation from scratch on a clean machine: `clawhub install eagerbots/ebay-agent`
- [ ] Verify the ClawHub listing page looks good (description, emoji, metadata)

### Strengthen the Skill Before Promoting
- [ ] Add 2-3 more example queries to SKILL.md trigger phrases (collectibles, clothing, specific electronics)
- [ ] Consider adding `--json` output flag for power users who want to pipe results
- [ ] Write a short "What makes this different" section — this is the first skill that calls real eBay REST APIs, not just a static reference guide

---

## 2. Content Marketing

### Blog Post / README Writeup
Write a post: **"Building the First eBay API Skill for OpenClaw"**
- The problem: no existing skill actually calls eBay APIs
- The architecture: client credentials OAuth, Browse API, Marketplace Insights
- Lessons learned: bestMatch vs price sorting, condition string mapping, scoring trade-offs
- What's coming next (buy/sell, Amazon comparison)
- Publish on: Medium, dev.to, personal blog, and link from the GitHub README

### Twitter / X Thread
Thread idea: "I just published the first eBay API skill on ClawHub. Here's what it does:"
- Tweet 1: Hook — "Your AI agent can now search eBay, value items, and find deals. No account needed."
- Tweet 2: Demo GIF or screenshot of search results table in terminal
- Tweet 3: How it works — client credentials, Browse API, scoring algorithm
- Tweet 4: "Try it: `clawhub install eagerbots/ebay-agent`"
- Tweet 5: What's next — buy/sell, Amazon price comparison, watchlists
- Tag: @OpenClaw, @ClawHub, relevant AI agent accounts
- Hashtags: #OpenClaw #AIAgents #ClawHub #eBayAPI

### Short Demo Video (60-90 seconds)
- Show: install, set credentials, run search, run value, explain the scoring
- Post on: Twitter, YouTube Shorts, LinkedIn
- Tool: asciinema for terminal recording, or screen capture with voiceover

---

## 3. Community Marketing

### OpenClaw / ClawHub Community
- [ ] Post in OpenClaw Discord (if one exists) announcing the skill
- [ ] Submit to any "awesome-openclaw-skills" lists on GitHub (VoltAgent/awesome-openclaw-skills exists)
- [ ] Open a discussion or showcase post in the OpenClaw GitHub repo
- [ ] Check if ClawHub has a "featured skills" or "new skills" section and request inclusion

### Reddit
- Post in: r/OpenClaw, r/AIAgents, r/LocalLLaMA, r/SideProject
- Frame as: "I built an eBay research agent as an OpenClaw skill — here's what I learned"
- Don't just drop a link — share the story, the technical decisions, what surprised you

### Hacker News
- "Show HN: eBay research agent for OpenClaw — search, value, score deals via real APIs"
- Best posted on a weekday morning (US time)
- Focus on the technical angle: real API integration vs wrapper skills

### GitHub
- [ ] Add topics to the repo: `openclaw`, `clawhub`, `ebay-api`, `ai-agent`, `skill`
- [ ] Star your own repo (legitimate, shows activity)
- [ ] Cross-link from clawbay-prototype repo

---

## 4. ClawHub Platform Optimization

### Listing Quality
- [ ] Ensure description is compelling and keyword-rich (already good)
- [ ] Verify emoji displays correctly
- [ ] Check that trigger phrases cover common natural language queries
- [ ] Add more trigger phrases for edge cases: "find cheap [item]", "what should I pay for [item]"

### SEO for ClawHub Vector Search
ClawHub uses vector search — users describe what they need in plain English. Optimize for:
- "eBay search", "eBay price check", "eBay deals"
- "compare prices", "item valuation", "market value"
- "shopping agent", "deal finder"
- These should appear naturally in the SKILL.md description and trigger phrases

---

## 5. Feature Roadmap (For Marketing Momentum)

Each new version is a reason to post again. Plan releases to sustain attention:

| Version | Feature | Marketing Hook |
|---------|---------|---------------|
| v0.5.0 | `--json` output, more robust error handling | "Now with JSON output for pipelines" |
| v0.6.0 | Watchlist (`watch add/list/check/remove`) | "Your agent now tracks prices for you" |
| v0.7.0 | Amazon price comparison (`compare`) | "eBay vs Amazon — your agent finds the best deal" |
| v1.0.0 | Stable release, full research suite | "v1.0 — the complete eBay research agent" |
| v1.1.0 | Listing generation (AI-powered) | "Your agent now writes eBay listings for you" |
| v2.0.0 | Buy/sell with seller OAuth | "Full eBay automation — search, buy, sell" |

Each release gets a tweet, a changelog, and a ClawHub version bump.

---

## 6. Metrics to Track

- ClawHub install count (check publisher dashboard)
- GitHub stars and forks
- Twitter impressions on announcement thread
- Inbound issues/PRs on GitHub (signals real usage)
- Search ranking on ClawHub for "eBay" queries

---

## 7. Partnerships & Outreach

- [ ] Reach out to OpenClaw team — first eBay API skill is notable, they may feature it
- [ ] Connect with other ClawHub skill publishers for cross-promotion
- [ ] If eBay has a developer community or newsletter, submit the skill as a showcase project
- [ ] Consider writing for the eBay Developer Blog about building AI agent integrations

---

## 8. Things NOT to Do

- **Don't inflate download stats with fake accounts.** ClawHub partners with VirusTotal and actively removes suspicious activity. Getting flagged would hurt the EagerBots brand.
- **Don't spam communities.** One thoughtful post per community is better than repeated low-effort links.
- **Don't market before it's ready.** First impressions matter — make sure the install-to-first-search experience is smooth.
- **Don't oversell v0.4.** Be honest that it's research-only and alpha. Users respect transparency and will come back for v1.0.
