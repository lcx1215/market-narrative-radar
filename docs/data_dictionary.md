# Data Dictionary

Each document in `data/corpus.json` is a JSON object with the following fields.

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Stable document identifier within the demo or live corpus. |
| `date` | string | Publication date or source date when available. |
| `source_type` | string | Broad source category, such as `Congress`, `Company filing`, `Federal Reserve`, `Research blog`, `News`, or `Executive transcript`. |
| `speaker` | string | Speaker name when the text has an identifiable person. |
| `organization` | string | Organization associated with the text. |
| `party` | string | Political party for congressional text when available. |
| `ticker` | string | Ticker or ticker basket used for filtering. This field can contain more than one ticker. |
| `title` | string | Human-readable source title. |
| `source_url` | string | Public URL or local provenance note. |
| `text` | string | Raw text analyzed by the app. |

For imported CSV files, the app accepts the same field names. If a column is missing, the app fills a conservative default.
