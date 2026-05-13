# Public Source Registry

Market Narrative Radar uses public text sources that can be swapped or extended without changing the frontend. This registry records the current source posture.

| Source | Status | Key | Current Use | Notes |
|---|---:|---:|---|---|
| SEC EDGAR data APIs | active | no | company filings and filing metadata | SEC `data.sec.gov` provides JSON APIs for submissions and XBRL company facts. |
| Federal Register REST API | active | no | rules, notices, agencies, publication dates | Good for regulator and agency language. |
| Federal Reserve RSS | active | no | central-bank speeches | Good for macro and rates language. |
| New York Fed Liberty Street Economics RSS | active | no | research blog posts | Good for macro research framing. |
| FTC Competition releases | active | no | antitrust and competition text | Good for regulator/source-conflict evidence. |
| DOJ Antitrust releases | active | no | antitrust releases, speeches, videos | Good for regulator and enforcement language. |
| CFTC releases | active | no | derivatives and market-structure policy text | Good for financial regulation language. |
| GDELT DOC 2.0 | active but rate-sensitive | no | broad news search | Useful for news breadth, but should be treated as secondary evidence. |
| Congress.gov API | optional | yes | bills, committee and member text | Official source for legislative data; keep optional because it needs `CONGRESS_API_KEY`. |

## Product Rule

The app should never fail just because one public source is down or slow. Source adapters should return source-level health, keep partial successful results, and let the brief show lower confidence when source coverage is thin.

## Upgrade Candidates

- SEC company facts and bulk archives for richer company-level financial context.
- Full filing text extraction for risk factors and MD&A.
- More official RSS feeds from regulators and central banks.
- Transcript adapters for uploaded `.srt` and `.vtt` files.
