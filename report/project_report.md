# Market Narrative Radar: Live Public Text Analysis for Financial and Policy Narratives

## Abstract

Market Narrative Radar is an interactive text-as-data application for analyzing how public institutions, companies, regulators, researchers, and news sources describe market-relevant issues. The app is not a trading model. Its purpose is to collect public text, normalize it into one corpus, apply interpretable NLP methods, retrieve evidence, and show how different source groups frame themes such as artificial intelligence, interest rates, U.S. policy and trade, regulation, demand, margins, and uncertainty.

The project includes a reproducible demo corpus, but the main design is live-ready: a backend relay can fetch continuously updated public sources such as SEC EDGAR, the Federal Register, Federal Reserve feeds, New York Fed research posts, FTC competition releases, DOJ antitrust releases, CFTC releases, and GDELT news search. The browser interface then applies the same text analysis pipeline to both static and live documents.

## Research Motivation

Financial and economic narratives are distributed across many public texts. A firm may describe supply chain risk in a 10-K, a regulator may describe the same sector through a proposed rule, a central banker may discuss macro conditions in a speech, and news or research blogs may add a different frame. These sources are usually read separately. That makes it difficult to compare which institutions are emphasizing which risks, and whether the public narrative is coming mainly from companies, regulators, policymakers, or media.

This project treats those documents as text data. The goal is to build a tool that supports public financial and policy text analysis: collect documents, clean them, classify themes, retrieve evidence, and make the output auditable.

## Data

The app ships with a reproducible demo corpus of 111 public documents. This corpus is used as a fallback and demonstration dataset so the app can run immediately without credentials or network access. It contains congressional speeches, SEC filing excerpts, Federal Reserve speeches, New York Fed posts, and normalized examples of imported news or transcript text.

The live data relay extends the corpus with continuously updated public sources:

- SEC EDGAR company filing metadata and filing links.
- Federal Register rules, notices, and proposed rules.
- Federal Reserve RSS feeds.
- New York Fed Liberty Street Economics posts.
- FTC competition press releases.
- DOJ Antitrust press releases, speeches, and video metadata.
- CFTC press releases and speeches.
- GDELT news search.
- Congress.gov as an optional keyed source.

All sources are normalized into the same schema: `id`, `date`, `source_type`, `speaker`, `organization`, `party`, `ticker`, `title`, `source_url`, and `text`.

## Methods

The app uses an interpretable NLP pipeline. Documents are tokenized and scored with transparent theme dictionaries. The current themes are AI and semiconductors, rates and inflation, U.S. policy and trade, regulation and antitrust, demand and margins, and risk and uncertainty. Scores are normalized by document length.

The app also computes a simple risk/constructive tone measure, extracts lightweight entities and tickers, reports corpus diagnostics, and ranks evidence passages. Corpus diagnostics include token volume, source diversity, lexical diversity, readability, and newest document date. The retrieval layer ranks sentences using query overlap, theme match, and risk-language intensity, while also favoring source diversity so that results do not come from only one document class.

The current build also adds source-aware processing. Filings, executive interviews, regulator text, policy speech, macro research posts, news, commentary, and video transcripts are assigned different source profiles before model interpretation. These profiles define cleaning strategy, signal extraction targets, and confidence penalties. This matters because a prepared 10-K risk factor, an unscripted executive interview, a regulator notice, and a news summary should not carry the same evidentiary meaning.

The brief is evidence-grounded. Every generated summary is paired with an evidence table and a citation audit that counts passages, documents, source types, and source references. This makes the app more transparent than a black-box summary.

## App Design

The browser interface is deliberately simple. The visible workflow is:

1. The user generates one daily market and policy narrative brief.
2. The app refreshes public sources in the background when the data relay is running.
3. The retrieval layer selects relevant evidence passages from the combined corpus.
4. The analyst layer returns a memo with direct claims, implied signals, source tensions, risk flags, missing evidence, watch items, and confidence.
5. The evidence drawer lets the user inspect source passages only when needed.

More technical controls such as import, export, filter state, source diagnostics, source health, and custom question mode are kept in the code path, but they are not exposed as the main user experience. This makes the project work like a narrow product rather than a dashboard of course components.

The LLM layer is optional and replaceable. The static app runs with local transparent NLP. A backend relay can connect OpenAI-compatible models, MiniMax, Anthropic, or Ollama without exposing API keys in browser code. This design supports model comparison while keeping the analysis reproducible and auditable.

The app also includes a defensive answer pattern for open-ended or unusual user questions. If retrieval evidence is thin, the system should lower confidence, state what the evidence does not support, and list missing source material rather than turning weak text matches into strong conclusions.

The P1 build adds a source conflict detector. Before the LLM layer runs, the app compares evidence by source role: company or executive text, regulator text, policymaker text, macro research text, and media text. A conflict signal is created when the same theme is framed differently across these roles, for example when a company-facing source emphasizes growth or opportunity while a public authority source emphasizes risk, enforcement, compliance, or uncertainty. The detector does not claim that one side is correct. It marks the framing gap as something the analyst memo should discuss and verify.

The analysis layer is therefore not allowed to start from a blank page. It receives a fixed contract, retrieved evidence, precomputed conflict candidates, and strict output fields. This keeps the output comparable across local fallback and private provider runs.

The same contract now includes source profiles. Source classification, evidence retrieval, conflict candidates, citations, confidence defaults, and JSON validation are controlled by the app before any generated wording is shown.

The P2/P3 build keeps the scope narrow and strengthens that contract. Open-ended questions are first classified into a bounded intent such as policy/regulatory read, macro narrative read, company language read, sector theme read, or source conflict check. The app then builds an analysis plan with focus terms, evidence count, source groups, themes, route steps, and answer limits. Both the browser and backend relay normalize model output back into the fixed JSON schema. If a model omits fields, returns weak confidence metadata, or fails to include citations, the app fills the missing structure conservatively and lowers the practical strength of the answer.

The final product framing is a daily brief. A future hosted version could put a lightweight checkout in front of each generated daily brief while preserving the same public-source retrieval and fixed JSON analysis contract.

## Findings From the Current Build

The demo corpus initially emphasizes congressional and policy language, which pushes macro and regulation themes to the top. After live fetching, the source mix expands to include company filings, regulators, central banks, and research blogs. This changes the evidence table: the top retrieved passages include policy text, Federal Register text about data center growth, SEC filing language, and Federal Reserve speech text. The app therefore demonstrates one of its main analytical goals: source composition changes the observed narrative.

## Limitations

The current NLP methods are intentionally transparent but simple. Dictionary scoring will miss synonyms, sarcasm, and context. The entity extractor is lightweight and should eventually be replaced or supplemented with a stronger NER model. GDELT and other public sources can rate-limit or return sparse results, so source health needs to be reported rather than hidden.

The app does not forecast returns, recommend trades, or produce price targets. It is a public text analysis tool for studying financial and policy narratives.

## Replication

Run the static app:

```bash
python3 -m http.server 8765
```

Run the live data relay:

```bash
python3 server/data_relay.py
```

Run the optional LLM relay:

```bash
python3 server/llm_relay.py
```

Validate the project package:

```bash
python3 scripts/validate_project.py
```

The replication package includes the static app, the demo corpus, live-source relay, LLM relay, corpus builder, validation script, data dictionary, engine documentation, and roadmap.
