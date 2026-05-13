# Analysis Contract

Market Narrative Radar is not a free-form chatbot. The user can ask an open-ended question, but the app forces the model through a fixed reasoning contract.

## Pipeline

```text
user question
  -> classify question intent
  -> build fixed analysis route
  -> refresh public sources
  -> retrieve evidence passages
  -> attach source-specific processing rules
  -> score source conflicts
  -> call analysis engine
  -> validate structured JSON shape
  -> render analyst memo with evidence
```

## Required Behavior

- Use retrieved evidence only.
- Classify the user question before interpreting evidence.
- Keep the answer inside the selected analysis route.
- Tie every implication to source text.
- Apply source-specific reading rules before drawing implications.
- Separate direct claims from interpretation.
- Compare source incentives across company, regulator, policymaker, macro research, and media text.
- Lower confidence when evidence is thin or source coverage is narrow.
- State missing evidence instead of guessing.
- Do not provide trading recommendations, price targets, return forecasts, or portfolio instructions.

## Source Conflict Detector

The app precomputes source conflict candidates before the LLM call. It compares framing by source role:

- `company`: filings, executive transcripts, earnings language
- `regulator`: Federal Register, FTC, DOJ, CFTC, SEC-style public authority text
- `policymaker`: Congress and committee language
- `macro_research`: Federal Reserve and research blog language
- `media`: news and broad public coverage

The detector looks for same-theme evidence where one source group emphasizes growth, demand, or opportunity while another emphasizes risk, regulation, enforcement, costs, or uncertainty. To avoid noisy matches, a candidate must share a named anchor, share at least two non-generic terms, and show opposed framing.

The LLM receives these conflict candidates as structured context. It can accept, weaken, or reject them, but it should treat them as framing gaps, not proven factual contradictions.

## Source-Aware Processing

The app does not read every document type the same way. Before interpretation, each evidence item receives a `source_profile` such as `company_filing`, `executive_interview`, `regulator_text`, `policymaker_speech`, `macro_research`, `news_report`, `blog_or_commentary`, or `video_transcript`.

Those profiles tell the analysis engine what to emphasize: filings need risk-factor and obligation language, interviews need hedges and unscripted claims, regulator text needs legal authority and compliance scope, policy speech needs constituency and committee framing, research posts need assumptions and uncertainty, news needs attribution quality, commentary needs viewpoint bias, and transcripts need speaker turns and verbal hedges. See `docs/source_processing.md`.

## Open-Ended Questions

The app accepts open-ended user questions, but it does not let the model answer freely. The app first assigns one intent:

- `source_conflict_check`
- `policy_and_regulatory_read`
- `macro_narrative_read`
- `company_language_read`
- `sector_theme_read`
- `broad_market_narrative_scan`

It then builds an `analysis_plan` with focus terms, evidence count, source count, source groups, themes, steps, and answer limits. The frontend and backend both normalize the final JSON so missing model fields do not break the research memo.

## Model Sandbox

The default engine is the backend `auto` relay, which tries configured providers such as MiniMax, OpenAI-compatible APIs, Anthropic, Ollama, and then local fallback.

The optional model sandbox lets an open-source user test a separate provider key for one session. The key is not saved in `localStorage` and is not committed. In a production paid-question version, checkout would sit in front of the relay; the analysis contract would stay the same.
