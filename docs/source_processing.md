# Source-Aware Processing

Market Narrative Radar does not treat every text source the same way. The app first assigns each document a `source_profile`, then applies shared NLP and model analysis.

## Principle

```text
source-specific cleaning
  -> normalized document schema
  -> shared NLP scoring and retrieval
  -> source-aware LLM interpretation
  -> fixed JSON validation
```

The LLM participates in interpretation, but it does not replace the source processing pipeline. Evidence retrieval, source roles, source profiles, citations, confidence limits, and JSON shape are controlled by the app.

## Source Profiles

| Profile | Used for | Reading rule |
|---|---|---|
| `company_filing` | 10-K, 10-Q, 8-K, annual reports | Keep risk factors, business language, MD&A, and filing summaries; discount boilerplate. |
| `executive_interview` | executive interviews, earnings calls, transcripts | Preserve speaker turns when available; separate management answers from interviewer questions. |
| `regulator_text` | Federal Register, FTC, DOJ, CFTC, SEC-style text | Focus on rules, notices, enforcement, compliance, and legal uncertainty. |
| `policymaker_speech` | Congress, Senate, House, committee language | Preserve speaker and party metadata; watch policy salience and ideological framing. |
| `macro_research` | Federal Reserve, NY Fed, research posts | Focus on causal claims, uncertainty language, and macro risk channels. |
| `news_report` | news and media text | Treat as secondary evidence unless claims are attributed to named sources. |
| `blog_or_commentary` | blogs, commentary, research notes | Separate argument, evidence, and opinion. |
| `video_transcript` | captions, subtitles, video transcripts | Remove timestamps and caption artifacts; preserve speaker turns when available. |
| `generic_text` | unknown public text | Use conservative handling and lower confidence when source context is weak. |

## Where It Runs

- Frontend source profiles: `src/app.js`
- Source-aware prompt context: `server/llm_relay.py`
- Unified document schema: `docs/data_dictionary.md`
- Course method mapping: `docs/course_methods_map.md`

## Why This Matters

A filing, a regulator notice, a news article, and a video transcript can all mention the same company or theme, but they do not mean the same thing. The app therefore asks different questions of different sources before producing one daily brief.
