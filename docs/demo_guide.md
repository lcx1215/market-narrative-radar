# Demo Guide

Use this guide to demonstrate the app in a few minutes.

## 1. Open the App

On macOS, double-click:

```text
Open Market Narrative Radar.command
```

Or run:

```bash
make open
```

Open:

```text
http://localhost:8765
```

The demo corpus loads automatically. The command also starts the live data relay and the LLM relay.

## 2. Confirm Health

Run:

```bash
make test
```

For the configured private model path:

```bash
make test-provider
```

Expected result: the app HTML loads, live sources return documents, and the LLM relay returns structured analyst JSON.

## 3. Ask a Question

Use:

```text
What changed in the AI, rates, and regulation narrative?
```

Click `Generate brief`.

The answer should cite retrieved passages and separate explicit claims from interpretation.

## 4. Inspect Evidence

Open `Evidence and sources` only if the audience wants to see the source passages behind the answer.

## 5. Explain the Boundary

Say:

```text
This is a public text analysis app. It studies financial and policy narratives. It does not make trading recommendations.
```

## 6. Show Reproducibility

Run:

```bash
python3 scripts/validate_project.py
```

This checks required files, data schemas, banned visible phrases, JavaScript syntax, and Python syntax.

## Private Model Key

The browser never asks for a model key. MiniMax, OpenAI-compatible, Anthropic, or Ollama configuration stays in local environment variables or `.env`, which is ignored by Git.

For a private instructor demo on the same machine, keep `.env` local and run `make open`. The LLM health endpoint reports provider names and rate-limit status, but never returns the secret value.
