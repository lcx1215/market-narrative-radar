# Market Narrative Radar

Market Narrative Radar is a small web app for reading public market language.

It pulls together filings, policy updates, central bank language, research notes, and news, then turns the current source set into a short evidence-backed brief. The project was built for NYU Text as Data, but the structure is practical enough to publish and extend.

It is not a trading system. It does not predict prices, recommend trades, or tell anyone what to buy. The point is narrower: show what public sources are saying, where the tone is shifting, and which passages support the read.

## Try It Locally

On macOS, double-click:

```text
Market Narrative Radar.app
```

If the services are already running, `Market Narrative Radar.webloc` opens the page directly.

Command line:

```bash
make open
```

Then open:

```text
http://127.0.0.1:8765
```

Click `Pay $1 & generate`.

This is only a local demo flow. No card is charged.

## What You See

The app keeps the main screen simple:

- one daily brief action,
- a short market-language read,
- confidence and caveats,
- coverage, freshness, and source-health status,
- narrative shifts versus the starting corpus,
- source-group comparison across company, regulator, policy, research, and news text,
- watchlist alerts with matching source evidence,
- evidence passages behind the answer,
- source links where available,
- exportable Markdown briefs for sharing or archiving.

The visible themes are:

- AI and semiconductors,
- rates and inflation,
- regulation,
- U.S. policy and trade,
- demand and margins,
- risk language.

## How It Works

The browser loads a reproducible corpus from `data/corpus.json`.

When the local relays are running, the app also refreshes live public sources through `server/data_relay.py`. Current connectors include SEC EDGAR, Federal Register, Federal Reserve RSS, New York Fed posts, FTC, DOJ Antitrust, CFTC, GDELT, and optional Congress.gov.

The analysis path is intentionally constrained:

1. normalize each document into one schema,
2. score themes and risk language with transparent dictionaries,
3. retrieve source passages,
4. compare source groups,
5. render a brief with citations and confidence limits.

`server/llm_relay.py` can call a private model provider when configured, but keys stay in `.env` or environment variables. The frontend never stores or displays secrets. If no provider is available, the app falls back to local evidence-based analysis.

## Validation

Run:

```bash
python3 scripts/validate_project.py
python3 scripts/mnr.py test
```

To test the configured private provider on the local machine:

```bash
python3 scripts/mnr.py test --provider
```

To clean local artifacts:

```bash
make clean
```

Runtime files live under `.mnr-runtime/`, which is ignored by Git. Secrets live in `.env`, also ignored by Git.

## Course Fit

This is a text-as-data project because the core object is a corpus, not a stock chart.

The app demonstrates:

- corpus construction,
- document normalization,
- dictionary scoring,
- source comparison,
- sentence-level evidence retrieval,
- simple entity and ticker extraction,
- structured, evidence-grounded interpretation,
- reproducible local packaging.

See `docs/course_methods_map.md` for the direct course-method mapping.

## Limits

This project is deliberately modest.

- Dictionary scoring is transparent, but it misses synonyms and context.
- The entity extractor is lightweight and can miss or over-count names.
- Public sources can be slow, sparse, rate-limited, or temporarily unavailable.
- GDELT and news results are useful for breadth, but they are weaker evidence than official filings or agency releases.
- Live source freshness depends on the public APIs responding during the demo.
- The brief summarizes public language; it does not prove causality, market impact, or future returns.
- The local `$1` button is a product-flow mock. Payments are not implemented.

## Product Direction

The next product work should improve the app itself before cloud deployment:

1. keep the daily brief format stable,
2. make every claim traceable to evidence,
3. show data coverage and source health clearly,
4. harden narrative-shift tracking versus a prior corpus,
5. harden source-group comparison,
6. harden watchlists and exportable briefs.

## Project Map

- `index.html`: app shell.
- `src/styles.css`: visual design.
- `src/app.js`: browser scoring, retrieval, rendering, and interaction logic.
- `data/corpus.json`: reproducible demo corpus.
- `data/live_corpus.json`: sample live-source output.
- `server/data_relay.py`: live public-source relay.
- `server/llm_relay.py`: optional private analysis relay.
- `scripts/mnr.py`: local start, stop, status, test, and clean loop.
- `scripts/validate_project.py`: package validation.
- `report/project_report.md`: written report.
- `docs/submission_checklist.md`: what to submit and what to show.
- `docs/replication_package.md`: reproducibility notes.
- `docs/data_dictionary.md`: data schema.
- `docs/source_registry.md`: public-source registry.
- `docs/product_readiness.md`: local readiness and hosted gaps.
