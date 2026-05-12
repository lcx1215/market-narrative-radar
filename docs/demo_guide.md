# Demo Guide

Use this guide to demonstrate the app in a few minutes.

## 1. Open the App

```bash
python3 -m http.server 8765
```

Open:

```text
http://localhost:8765
```

The demo corpus loads automatically.

## 2. Start Live Ingestion

Start the data relay:

```bash
python3 server/data_relay.py
```

No extra UI step is needed. The next `Analyze` click refreshes public sources in the background.

Expected result: the answer cites a mix of demo and live SEC, Federal Register, Federal Reserve, NY Fed, FTC, DOJ, CFTC, or GDELT documents when those sources return relevant text.

## 3. Ask a Question

Use:

```text
What changed in the AI, rates, and regulation narrative?
```

Click `Analyze`.

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
