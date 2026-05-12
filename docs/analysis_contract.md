# Analysis Contract

Market Narrative Radar is not a free-form chatbot. The user can ask an open-ended question, but the app forces the model through a fixed reasoning contract.

## Pipeline

```text
user question
  -> classify question intent
  -> refresh public sources
  -> retrieve evidence passages
  -> score source conflicts
  -> call analysis engine
  -> validate structured JSON shape
  -> render analyst memo with evidence
```

## Required Behavior

- Use retrieved evidence only.
- Tie every implication to source text.
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

The detector looks for same-theme evidence where one source group emphasizes growth, demand, or opportunity while another emphasizes risk, regulation, enforcement, costs, or uncertainty.

The LLM receives these conflict candidates as structured context. It can accept, weaken, or reject them, but it should not invent conflicts that are not supported by evidence.

## Model Sandbox

The default engine is the backend `auto` relay, which tries configured providers such as MiniMax, OpenAI-compatible APIs, Anthropic, Ollama, and then local fallback.

The optional model sandbox lets an open-source user test a separate provider key for one session. The key is not saved in `localStorage` and is not committed. In a production paid-question version, checkout would sit in front of the relay; the analysis contract would stay the same.
