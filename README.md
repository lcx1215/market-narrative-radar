# Market Narrative Radar

Market Narrative Radar is a browser-based app for public financial and policy text analysis. It studies how companies, regulators, policymakers, research blogs, and news sources frame market-relevant narratives.

It is not a trading system. It does not forecast returns, produce price targets, or recommend trades. The core object is text.

## What It Does

- Gives the user one main action: generate a daily public-text narrative brief.
- Ships with a reproducible demo corpus so the app works immediately.
- Refreshes live public sources through a backend data relay during analysis.
- Normalizes all documents into one schema.
- Scores themes such as AI and semiconductors, rates and inflation, China and trade, regulation and antitrust, demand and margins, and risk and uncertainty.
- Tracks watchlist terms and flags source/risk concentration.
- Extracts lightweight entities and tickers from the filtered corpus.
- Reports token volume, lexical diversity, readability, source diversity, and freshness.
- Retrieves evidence passages for the daily market/policy narrative focus.
- Classifies the daily brief into a bounded text-analysis intent before calling the model.
- Builds an analysis route with focus terms, source coverage, evidence count, and answer limits.
- Supports structured analyst mode for explicit claims, implicit signals, contradictions, narrative shifts, source tensions, risk flags, hedging language, missing evidence, and watch items.
- Detects source conflicts where companies, executives, regulators, policymakers, macro research, and media frame the same theme differently.
- Normalizes LLM output back into the fixed analyst JSON schema if a provider omits fields.
- Audits each brief by counting cited passages, documents, source types, and references.
- Keeps advanced import, export, filter, and source diagnostics in the code path without making the main interface busy.
- Keeps LLM providers behind a replaceable backend relay.

## Quick Demo

Start the three local processes:

```bash
python3 -m http.server 8765
python3 server/data_relay.py
python3 server/llm_relay.py
```

Open:

```text
http://localhost:8765
```

Click `Generate brief`. The app refreshes public sources in the background, retrieves evidence passages, and produces an analyst memo with confidence, direct claims, implied signals, source tensions, risk flags, missing evidence, and watch items.

## Live Public Sources

The live data relay currently connects:

- SEC EDGAR
- Federal Register
- Federal Reserve RSS
- New York Fed Liberty Street Economics
- FTC Competition
- DOJ Antitrust
- CFTC
- GDELT
- Congress.gov, optional with `CONGRESS_API_KEY`

The demo corpus in `data/corpus.json` is only a fallback and reproducibility dataset. The main architecture is live-ready.

## LLM and Key Handling

The main workflow never asks the user for an API key. The frontend calls a local backend relay at `/api/analyze`. Provider keys live only in local environment variables such as `.env`, which is ignored by Git.

The relay uses an `auto` engine:

1. Try MiniMax if configured.
2. Try OpenAI-compatible APIs if configured.
3. Try Anthropic if configured.
4. Try Ollama if running locally.
5. Fall back to the local transparent analyst engine.

This means the project can be opened publicly on GitHub without exposing private keys, and the model provider can be replaced later without rewriting the app.

There is also a closed-by-default model sandbox for open-source users who want to test their own provider key. It is a demo path: the key is used for the current request and is not stored. A future custom-question version can put checkout in front of the same relay while keeping the analysis contract unchanged.

The current product shape is a daily brief. A hosted version could charge per generated daily brief, for example a simple `$1` demo unit, but payment is intentionally not implemented in this local course build.

## Analysis Contract

The app is not a free-form chatbot. It teaches whichever model is connected to follow the same process:

1. Set the daily narrative focus.
2. Classify the brief into a bounded text-analysis intent.
3. Build an analysis route with evidence and source guardrails.
4. Refresh public sources.
5. Retrieve evidence.
6. Detect source conflicts.
7. Fill and validate the fixed analyst JSON schema.
8. Render a concise memo and keep evidence auditable.

See `docs/analysis_contract.md` for the full contract.

## Run Locally

Run the static app:

```bash
python3 -m http.server 8765
```

Open:

```text
http://localhost:8765
```

Run the live data relay:

```bash
python3 server/data_relay.py
```

The app refreshes live public sources automatically when the user clicks `Analyze`.

Run the optional LLM relay:

```bash
python3 server/llm_relay.py
```

The browser app calls the local relay automatically. If no private model key is configured,
the relay falls back to the local transparent analyst engine.

## API Keys and Secrets

Secrets stay local. Copy `.env.example` to `.env` for private keys. `.env` is ignored by Git.

Supported optional keys:

- `CONGRESS_API_KEY`
- `OPENAI_API_KEY`
- `MINIMAX_API_KEY`
- `ANTHROPIC_API_KEY`

The frontend never stores provider keys.

## Course Fit

This is a text-as-data project. The core work is corpus construction, public-source normalization, dictionary scoring, evidence retrieval, source comparison, structured interpretation, and reproducible documentation. The financial use case is a domain application, not a trading recommender.

## Validate

```bash
python3 scripts/validate_project.py
```

## Project Files

- `index.html`: app shell.
- `src/styles.css`: visual design.
- `src/app.js`: browser NLP, retrieval, and UI logic.
- `data/corpus.json`: reproducible demo corpus.
- `data/live_corpus.json`: sample live-source output.
- `server/data_relay.py`: live public-source relay.
- `server/llm_relay.py`: optional replaceable LLM relay.
- `scripts/build_corpus.py`: corpus builder.
- `scripts/fetch_live_sources.py`: command-line live-source fetcher.
- `scripts/validate_project.py`: package validation.
- `report/project_report.md`: research report.
- `docs/teacher_review_checklist.md`: short grading/demo checklist.
- `docs/analysis_contract.md`: fixed RAG/tool/DAG reasoning contract.
- `docs/replication_package.md`: replication instructions.
- `docs/data_dictionary.md`: data schema.
- `docs/engines.md`: data and LLM engine documentation.
- `docs/analyst_schema.md`: structured analyst output schema.
- `docs/roadmap.md`: upgrade plan.
