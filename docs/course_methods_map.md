# Course Methods Map

This project keeps the interface simple, but the app uses text-as-data methods from the homework sequence.

## Visible in the App

- **Tokenization and word frequency**: `src/app.js` tokenizes public documents, counts theme words, and normalizes scores by document length.
- **Named entities and information extraction**: the app extracts organizations, agencies, capitalized actors, and tickers for the entity radar.
- **Dictionary scoring**: the app scores themes such as AI, rates, U.S. policy and trade, regulation, demand, and risk language.
- **Sentence retrieval**: the app ranks evidence sentences by question overlap, theme match, and risk-language intensity.
- **Source-specific preprocessing**: the app switches reading rules for filings, interviews, regulator text, policy speech, macro research, news, commentary, and video transcripts.
- **Source comparison**: the app compares source groups such as company filings, regulators, policymakers, macro research, and media.
- **Structured LLM analysis**: the backend asks MiniMax or another model to fill a fixed JSON schema using retrieved evidence only.

## Homework Connections

| Course topic | Homework connection | Where it appears here |
|---|---|---|
| Loading and inspecting a text corpus | HW01 | `data/corpus.json`, `data/live_corpus.json`, `scripts/build_corpus.py` |
| Document length and word frequency | HW01 | token counts, lexical diversity, normalized theme scores |
| Tokenization and preprocessing | HW02 | `tokenize`, `splitSentences`, transcript cleaning |
| Text cleaning by document type | HW02 | `SOURCE_PROFILES`, source-aware cleaning and confidence rules |
| Named entities and information extraction | HW02 | `extractEntities`, ticker extraction, source metadata |
| Similarity and evidence ranking | HW03 | sentence retrieval by query overlap and theme score |
| Topic/theme modeling idea | HW03, HW07 | interpretable theme dictionaries instead of a black-box topic model |
| Classification-style scoring | HW04 | risk vs constructive language, source-role classification |
| Embeddings and semantic search | HW05, HW07 | listed as a planned upgrade; current app uses transparent lexical retrieval |
| Attention/BERT/transformers | HW06, HW07 | replaceable model relay can use modern LLMs, while local analysis remains interpretable |
| GPT-style generation and fine-tuning | HW08, HW09 | fixed JSON generation through the LLM relay; future custom models can replace MiniMax |
| Reward models and controlled generation | HW10 | answer guardrails: no trading advice, cite evidence, lower confidence when evidence is thin |

## Design Choice

The app does not expose every method as a separate button. That would make the product feel like a homework dashboard. Instead, the visible workflow is one daily brief, while the text-as-data methods run in the background and are documented here for review.
