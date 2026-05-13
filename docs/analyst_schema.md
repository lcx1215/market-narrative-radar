# Analyst Schema

The analyst mode is for deeper interpretation of public text evidence. It separates direct evidence from interpretation.

```json
{
  "question_intent": "",
  "analysis_plan": {},
  "source_profiles": [],
  "executive_read": "",
  "explicit_claims": [],
  "implicit_signals": [],
  "source_conflicts": [],
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

Core idea: the app should not only summarize what people said. It should first classify the question, build a fixed analysis route, then examine what wording may imply, where source groups disagree, what has changed, and what evidence is missing.

`question_intent` is one of the app's bounded intent labels. `analysis_plan` records focus terms, evidence count, source groups, route steps, and answer limits. This is what keeps odd or broad user questions inside a reproducible text-analysis workflow.

`source_profiles` records how the retrieved evidence should be read by source type. For example, company filings, executive interviews, regulator text, policy speech, macro research, news, commentary, and video transcripts each have different cleaning rules, signal extraction targets, and confidence penalties.

`source_conflicts` is the P1 conflict detector field. It is for cases where company, executive, regulator, policymaker, macro research, or media sources frame the same theme differently. A conflict does not have to mean a factual contradiction. It can mean an incentive-aware framing gap, such as company language emphasizing growth while regulator language emphasizes compliance or risk.

Every important analytical claim should cite retrieved evidence when possible.
