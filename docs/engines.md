# Engine Architecture

Market Narrative Radar separates the app into three replaceable layers.

## 1. Data Source Engines

Preferred sources are free, public, and broad enough for an open-source project.

| Engine | Coverage | Auth | Use |
| --- | --- | --- | --- |
| SEC EDGAR | Filings, filing history, XBRL facts | No key | Company risk language, MD&A, 8-K events |
| GDELT DOC 2.0 | Global news search | No key | Broad news and media narratives |
| Federal Reserve RSS | Speeches, testimony, policy releases, research feeds | No key | Monetary policy and macro narratives |
| Federal Register | Rules, notices, proposed rules | Public API | Regulation and agency-risk narratives |
| Congress.gov | Bills, members, Congressional Record, committees | Free key | Legislative context and member activity |
| FRED | Macro time series | Free key | Joining text narratives with inflation/rates data |
| NY Fed Blog | Macro and market research posts | No key | Financial-stability and macro narrative context |
| FTC Competition | Competition press releases | No key | Antitrust and platform-regulation narratives |
| DOJ Antitrust | Press releases, speeches, videos | No key | Antitrust enforcement and merger-review narratives |
| CFTC | Press releases and speeches | No key | Derivatives, commodities, and enforcement narratives |

The static app ships with a reproducible demo corpus. The main architecture is the live data relay, which can fetch and normalize continuously updated public sources.

The repository includes `scripts/fetch_live_sources.py` as a starter ingestion worker for SEC EDGAR, GDELT, Federal Register, and Federal Reserve RSS. For interactive use, `server/data_relay.py` exposes `/api/live-sources`, because SEC's public documentation notes that `data.sec.gov` does not support CORS and therefore should be fetched through a backend relay from browser apps.

## 2. NLP Engines

The browser implementation currently includes:

- dictionary theme scoring,
- risk and constructive tone scoring,
- sentence-level retrieval,
- entity and ticker extraction,
- corpus quality diagnostics,
- citation audit counts,
- CSV import,
- plain text import,
- `.srt` and `.vtt` transcript cleaning.

Good future modules:

- TF-IDF and cosine similarity,
- topic modeling,
- embedding search,
- transcript diarization metadata,
- weak supervision for narrative labels,
- a small GPT-2 style model trained on a narrow corpus for demonstration,
- watchdog-style alerts over saved tickers, people, agencies, and risk terms.

## 3. LLM Engines

The app never stores provider keys in the browser. The LLM layer is a relay contract:

```http
POST /api/analyze
Content-Type: application/json
```

Payload shape:

```json
{
  "engine": "openai-compatible",
  "question": "What changed in the AI narrative?",
  "themes": {},
  "evidence": [
    {
      "source_type": "Company filing",
      "date": "2026-02-25",
      "title": "NVDA 10-K Risk Factors",
      "source_url": "https://...",
      "theme": "AI & semiconductors",
      "sentence": "..."
    }
  ]
}
```

Expected response:

```json
{
  "summary": "Evidence-grounded answer with citations to retrieved passages."
}
```

Supported relay types:

The frontend uses an `auto` backend engine. The relay checks configured providers in this order:
MiniMax, OpenAI-compatible, Anthropic, Ollama, then local fallback.

The repository includes `server/llm_relay.py` as a minimal relay implementation. It supports local fallback summaries, OpenAI-compatible chat completions, MiniMax OpenAI-compatible chat completions, Anthropic messages, and Ollama generate endpoints.

The UI also includes a closed-by-default model sandbox for open-source users who want to try their own provider key. That key is sent only with the current request and is not stored by the frontend. The fixed analysis contract still controls the output schema, source conflict handling, and research boundary.

## 4. Long-Task DAG

The app's intended long-task structure is:

| Stage | Purpose |
| --- | --- |
| Question parse | Convert strange or broad user questions into searchable text intent. |
| Source refresh | Pull free public sources through `server/data_relay.py`. |
| RAG retrieval | Rank sentence-level evidence by query overlap, theme match, risk language, and source diversity. |
| Source conflict detection | Compare company, regulator, policymaker, macro research, and media framing. |
| LLM analysis | Ask the selected model to fill the fixed analyst JSON contract. |
| Validation | Fall back to local transparent NLP if the relay or provider fails. |
| Memo rendering | Show a concise analyst memo first; keep raw JSON and evidence available behind disclosures. |

This DAG is the part that teaches a user's LLM how to think. The model provider can change, but the reasoning shape remains fixed.
