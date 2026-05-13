# Product Readiness Notes

This project is a local course build with a product-shaped operating loop.

## What Is Product-Ready Locally

- One-click macOS launcher: `Open Market Narrative Radar.command`.
- Clean process management through `scripts/mnr.py`.
- PID files and logs are isolated under `.mnr-runtime/`.
- Private model keys stay server-side in `.env` or environment variables.
- LLM relay exposes `/api/health` without leaking keys.
- Analysis requests are rate-limited with `MNR_MAX_ANALYSES_PER_MINUTE`.
- Public source fetches are cached with `MNR_DATA_CACHE_TTL_SECONDS`.
- Public source health is returned per adapter, so one failed source does not break the whole brief.
- The UI falls back to local structured NLP if the model relay fails.

## What Still Belongs To A Hosted SaaS Build

- User accounts and authentication.
- Stripe or another checkout provider.
- Persistent database-backed source cache.
- Background scheduler for daily refresh.
- Observability, alerts, and uptime checks.
- Abuse prevention beyond the local rate limiter.
- Production legal pages and stronger financial-disclaimer review.

## Instructor Demo Positioning

For course review, this should be presented as a public text analysis app, not as investment advice. The instructor can run the app with local MiniMax credentials if `.env` is present on the demo machine, but the key is not exposed in the frontend and is not committed to Git.
