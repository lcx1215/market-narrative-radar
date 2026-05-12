# Replication Package

This project is intentionally reproducible with static files and the Python standard library.

## 1. Requirements

- Python 3.9 or newer.
- A local HTTP server, provided by Python.
- Internet access only if rebuilding the public web-source portion of the corpus.

No JavaScript package manager is required.

## 2. Rebuild the Corpus

From the project folder:

```bash
python3 scripts/build_corpus.py
```

The script writes:

```text
data/corpus.json
```

The builder reads the local congressional speech sample when available:

```text
../hw10/us_congress_speeches_sample.csv
```

It also pulls public text from SEC EDGAR, Federal Reserve speech pages, and the New York Fed Liberty Street Economics RSS feed. If a public web source changes or is unavailable, the existing checked-in corpus can still be used for replication of the app behavior.

## 3. Run the App

```bash
python3 -m http.server 8765
```

Open:

```text
http://localhost:8765
```

The demo corpus loads automatically. For live analysis, run `python3 server/data_relay.py`; the app refreshes public sources in the background when the user clicks `Analyze`.

## 4. Reproduce the Analysis

For the demo corpus, the app analysis is deterministic:

1. Documents are tokenized in the browser.
2. Theme dictionaries count normalized phrase hits.
3. Risk and positive tone dictionaries are scored with the same normalization.
4. Evidence passages are split into sentences and ranked by query overlap, theme match, and risk language.
5. The research brief is generated only from retrieved evidence.

The source code implementing these steps is in:

```text
src/app.js
```

## 5. Extend With New Text

To extend the project with current executive interviews, earnings calls, news, blogs, or videos, add rows that match the same document schema:

- CSV-style fields: `date,source_type,title,ticker,source_url,text`
- Transcript text can be cleaned with the app's `cleanTranscript` helper.
- Additional connectors can write documents into `data/corpus.json` or return them through `server/data_relay.py`.

The app does not require a hosted database for static deployment.
