# Analyst Schema

The analyst mode is for deeper interpretation of public text evidence. It separates direct evidence from interpretation.

```json
{
  "executive_read": "",
  "explicit_claims": [],
  "implicit_signals": [],
  "source_tensions": [],
  "contradictions": [],
  "narrative_shifts": [],
  "risk_flags": [],
  "opportunity_signals": [],
  "speaker_incentives": [],
  "hedging_language": [],
  "missing_evidence": [],
  "watch_items": [],
  "source_reliability": [],
  "market_relevance": [],
  "confidence": {
    "level": "low|medium|high",
    "reason": ""
  },
  "evidence_citations": []
}
```

Core idea: the app should not only summarize what people said. It should also examine what wording may imply, where source groups disagree, what has changed, and what evidence is missing.

Every important analytical claim should cite retrieved evidence when possible.
