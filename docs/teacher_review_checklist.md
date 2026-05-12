# Teacher Review Checklist

This file is a short review path for a course grader or demo viewer.

## What to Open

Run:

```bash
python3 -m http.server 8765
python3 server/data_relay.py
python3 server/llm_relay.py
```

Then open:

```text
http://localhost:8765
```

The app works with the checked-in demo corpus even if the relays are not running. With the relays running, `Analyze` refreshes public sources and routes analysis through the backend model adapter.

## What to Test

Ask:

```text
What changed in the AI, rates, and regulation narrative?
```

Expected behavior:

- The interface only asks for a question and an `Analyze` click.
- No API key is requested in the browser.
- The answer is an analyst memo, not a trade recommendation.
- The memo separates direct claims, possible implications, source tension, risk flags, missing evidence, and watch items.
- `Evidence and sources` expands to show the passages used for the answer.

## Why This Fits Text as Data

The project treats public documents as a corpus. It performs:

- source collection and normalization,
- dictionary-based theme scoring,
- risk-language scoring,
- sentence-level evidence retrieval,
- source comparison,
- structured evidence-grounded interpretation,
- reproducible packaging and documentation.

## Secret Handling

Provider keys are read only by `server/llm_relay.py` from local environment variables. `.env` is ignored by Git. The frontend never displays or stores model keys.
