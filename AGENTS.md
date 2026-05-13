# AGENTS.md

Guidance for future coding agents working on Market Narrative Radar.

## Product Standard

Build this as a paid, evidence-first market narrative product, not as a homework dashboard or a generic chat interface.

The app should feel quiet, fast, and trustworthy:

- concise product copy,
- one clear daily brief action,
- source passages visible behind every important claim,
- confidence and missing evidence shown plainly,
- no trading advice, price targets, or portfolio instructions.

## Core Principle

Every brief must answer three questions:

1. What changed in public market language?
2. Which sources support that read?
3. What is missing or uncertain?

If evidence is thin, say that directly. Do not make the answer sound stronger than the source set.

## Current Product Direction

Priority order:

1. Make the daily brief reliable and easy to trust.
2. Improve source coverage, freshness, and source-health visibility.
3. Harden narrative-shift tracking against a prior corpus or baseline.
4. Add source-group comparison views.
5. Add watchlists and exportable briefs.
6. Only then expand into hosted accounts, payments, or cloud deployment.

## UI Rules

- Keep the main screen simple.
- Prefer short Apple-like product copy over explanatory paragraphs.
- Do not expose internal labels such as provider routing, JSON schema, prompts, or debugging terms in the visible app.
- Do not add busy dashboards to the first viewport.
- Evidence, method, and diagnostics can exist, but they should not compete with the brief.

## Data and Evidence Rules

- Keep source dates, source types, and source URLs attached to evidence.
- Show coverage, freshness, evidence count, and source health near the brief.
- Show narrative shifts as theme movement against a stated baseline.
- Do not hide source failures. Show lower confidence or a limited-source state.
- Treat news as weaker evidence than official filings, agencies, central banks, or primary research posts.

## Security Rules

- Never commit `.env`, `.mnr-runtime/`, local logs, screenshots, caches, or private keys.
- Provider keys must stay in local environment variables or `.env`.
- The frontend must never ask users to paste private provider keys into the main workflow.

## Validation Commands

Run these before claiming the app is ready:

```bash
python3 scripts/validate_project.py
python3 scripts/mnr.py test
python3 scripts/mnr.py test --provider
```

For rendered UI changes, also open:

```text
http://127.0.0.1:8765
```

Then click `Pay $1 & generate` and verify:

- page is not blank,
- button returns from `Generating...`,
- console has no relevant errors or warnings,
- coverage summary updates,
- evidence table supports the brief,
- no `.env`, `.mnr-runtime`, pycache, or screenshots appear in `git status --short`.
