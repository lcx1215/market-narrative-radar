# Roadmap

Market Narrative Radar is structured so the static app can grow into a hosted research system.

## Near-Term

- Add a scheduled ingestion worker for SEC EDGAR, Federal Register, Federal Reserve RSS, NY Fed, FTC, DOJ Antitrust, CFTC, and GDELT.
- Add API-key based optional connectors for Congress.gov and FRED.
- Store source health checks with timestamps.
- Add user-defined narrative dictionaries.
- Add saved workspaces for watchlists and ticker baskets.

## NLP Upgrades

- TF-IDF similarity search.
- Topic modeling over selected source groups.
- Embedding index for passage retrieval.
- Named entity recognition through a replaceable local or hosted model.
- Transcript diarization metadata for interviews and videos.
- Small baseline language-model notebook for educational comparison.

## Product Upgrades

- Backend relay authentication.
- Citation export to Markdown.
- Evidence diff between two dates or source groups.
- Hosted daily brief checkout, for example a simple `$1` per generated daily brief demo unit.
- Optional open-ended question mode for personal research use after the daily brief workflow is stable.
- GitHub Pages demo plus optional hosted backend.
- Test suite for ingestion workers and browser functions.
