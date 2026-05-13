#!/usr/bin/env python3
"""Minimal LLM relay for Market Narrative Radar.

The browser app can call this server at /api/analyze. Provider keys stay in
environment variables and never enter frontend code.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


def load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()


SYSTEM_PROMPT = """You summarize market narratives from retrieved evidence.
Use only the provided evidence. Do not make trade recommendations, forecasts,
price targets, or portfolio instructions. Mention uncertainty and source gaps."""

ANALYST_SCHEMA = {
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
    "confidence": {"level": "low|medium|high", "reason": ""},
    "evidence_citations": [],
}

ALLOWED_INTENTS = {
    "source_conflict_check",
    "policy_and_regulatory_read",
    "macro_narrative_read",
    "company_language_read",
    "sector_theme_read",
    "broad_market_narrative_scan",
}

ANALYST_PROMPT = f"""You are a public financial and policy text analyst.
Use only the retrieved evidence. Do not provide trading advice, price targets,
return forecasts, portfolio instructions, or unsupported claims.

First classify the question into a narrow text-analysis intent. Then analyze what the sources explicitly say, what they may imply, whether source
groups frame the issue differently, whether there are source conflicts,
contradictions or tensions, what wording is hedged, and what evidence is
missing.

Return valid JSON only. Use this exact schema:
{json.dumps(ANALYST_SCHEMA, indent=2)}

Each important claim should include an evidence_index when it is grounded in a
retrieved passage. If the evidence is too thin, say so in missing_evidence and
lower confidence. Apply source-specific reading rules from source_profiles:
filings, transcripts, regulator text, news, research blogs, video transcripts,
and congressional speech should not be interpreted the same way. Treat source_conflicts as differences in institutional
framing across company, regulator, policymaker, macro research, and media
sources; do not invent conflict if the evidence only supports weak tension."""

MINIMAX_ANALYST_PROMPT = f"""You are a public financial and policy text analyst.
Return compact valid JSON only. Do not use markdown.
Use only retrieved evidence. Do not provide trading advice, price targets,
return forecasts, or portfolio instructions.

Required schema:
{json.dumps(ANALYST_SCHEMA, indent=2)}

Keep the answer concise. Separate direct claims from interpretation. Apply
source-specific reading rules from source_profiles. Treat
source_conflicts as framing gaps unless evidence proves a factual contradiction."""


def post_json(url: str, payload: dict, headers: dict | None = None) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    timeout = float(os.environ.get("MNR_PROVIDER_TIMEOUT", "10"))
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def evidence_text(payload: dict) -> str:
    lines = []
    for index, item in enumerate(payload.get("evidence", []), start=1):
        lines.append(
            f"[{index}] {item.get('date', '')} | {item.get('source_type', '')} | "
            f"{item.get('title', '')} | {item.get('theme', '')}\n{item.get('sentence', '')}"
        )
    return "\n\n".join(lines)


def source_conflict_text(payload: dict) -> str:
    rows = payload.get("source_conflicts") or []
    if not rows:
        return "No precomputed source conflicts."
    return "\n".join(
        f"- {item.get('theme', '')}: {item.get('conflict_type', '')} | "
        f"{', '.join(item.get('source_groups', []))} | {item.get('signal', '')}"
        for item in rows[:5]
    )


def source_profile_text(payload: dict) -> str:
    rows = payload.get("source_profiles") or []
    if not rows:
        profiles = []
        for item in payload.get("evidence", []):
            profile = item.get("source_profile")
            if isinstance(profile, dict):
                profiles.append({**profile, "source_type": item.get("source_type", "")})
        rows = profiles
    if not rows:
        return "No source profiles supplied; use conservative generic text handling."
    lines = []
    seen = set()
    for item in rows[:8]:
        key = f"{item.get('profile_key', '')}:{item.get('source_type', '')}"
        if key in seen:
            continue
        seen.add(key)
        signals = item.get("signals_to_extract") or []
        if isinstance(signals, list):
            signals = ", ".join(str(signal) for signal in signals[:4])
        lines.append(
            f"- {item.get('source_type', item.get('label', 'source'))}: "
            f"{item.get('profile_key', 'generic_text')} | "
            f"cleaning: {item.get('cleaning_strategy', '')} | "
            f"signals: {signals} | "
            f"confidence_penalty: {item.get('confidence_penalty', '')}"
        )
    return "\n".join(lines)


def classify_question_intent(question: str) -> str:
    lower = question.lower()
    if re.search(r"\b(contradict|contradiction|conflict|disagree|tension|mismatch)\b", lower):
        return "source_conflict_check"
    if re.search(r"\b(sec|ftc|doj|cftc|regulat\w*|antitrust|congress|senate|house|policy|law|rule|rules)\b", lower):
        return "policy_and_regulatory_read"
    if re.search(r"\b(rate|rates|inflation|fed|treasury|yield|yields|liquidity|credit|macro)\b", lower):
        return "macro_narrative_read"
    if re.search(r"\b(company|filing|earnings|management|executive|ceo|cfo|margin|revenue|demand)\b", lower):
        return "company_language_read"
    if re.search(r"\b(ai|chip|semiconductor|gpu|data center|tariff|china|supply chain)\b", lower):
        return "sector_theme_read"
    return "broad_market_narrative_scan"


def analysis_plan(payload: dict) -> dict:
    provided = payload.get("analysis_plan")
    if isinstance(provided, dict) and provided:
        return provided
    evidence = payload.get("evidence", [])
    source_conflicts = payload.get("source_conflicts") or []
    source_profiles = payload.get("source_profiles") or []
    source_groups = sorted({item.get("source_type", "") for item in evidence if item.get("source_type")})
    themes = sorted({item.get("theme", "") for item in evidence if item.get("theme")})
    focus_terms = [
        token
        for token in re.findall(r"[a-z0-9$-]{3,}", payload.get("question", "").lower())
        if token not in {"what", "the", "and", "for", "are", "was", "which", "where", "when", "does", "from", "into", "about", "changed", "change", "market", "narrative", "today", "daily", "across", "analysis", "analyze", "public", "source", "sources"}
    ][:8]
    limits = [
        "No trading recommendation, price target, return forecast, or portfolio instruction.",
        "No claim should be stronger than the retrieved evidence.",
    ]
    if len(evidence) < 6:
        limits.append("Evidence set is thin; confidence should stay low.")
    if len(source_groups) < 3:
        limits.append("Source coverage is narrow; compare more source groups before making a stronger read.")
    if not source_conflicts:
        limits.append("No strong precomputed source conflict was found; treat disagreement language cautiously.")
    return {
        "intent": classify_question_intent(payload.get("question", "")),
        "focus_terms": sorted(set(focus_terms), key=focus_terms.index),
        "evidence_count": len(evidence),
        "source_count": len(source_groups),
        "source_groups": source_groups,
        "source_profiles": [
            {
                "profile_key": item.get("profile_key", "generic_text"),
                "source_type": item.get("source_type", ""),
                "confidence_penalty": item.get("confidence_penalty", "medium"),
            }
            for item in source_profiles[:8]
        ],
        "themes": themes[:5],
        "source_conflict_count": len(source_conflicts),
        "steps": [
            "Classify the question into a narrow text-analysis intent.",
            "Retrieve passages from public sources and keep evidence indexes stable.",
            "Compare company, regulator, policymaker, macro research, and media framing.",
            "Separate direct claims from implied narrative signals.",
            "Return missing evidence and confidence limits before any conclusion.",
        ],
        "answer_limits": limits,
    }


def normalize_analysis(raw: dict, payload: dict) -> dict:
    plan = analysis_plan(payload)
    evidence = payload.get("evidence", [])
    source_conflicts = payload.get("source_conflicts") or []
    analysis = dict(raw or {})
    list_fields = [
        "explicit_claims",
        "implicit_signals",
        "source_profiles",
        "source_conflicts",
        "source_tensions",
        "contradictions",
        "narrative_shifts",
        "risk_flags",
        "opportunity_signals",
        "speaker_incentives",
        "hedging_language",
        "missing_evidence",
        "watch_items",
        "source_reliability",
        "market_relevance",
        "evidence_citations",
    ]
    analysis["question_intent"] = (
        analysis["question_intent"] if analysis.get("question_intent") in ALLOWED_INTENTS else plan["intent"]
    )
    if isinstance(analysis.get("analysis_plan"), dict):
        analysis["analysis_plan"] = {**plan, **analysis["analysis_plan"]}
    else:
        analysis["analysis_plan"] = plan
    for field in list_fields:
        value = analysis.get(field, [])
        if value is None or value == "":
            analysis[field] = []
        elif isinstance(value, list):
            analysis[field] = value
        else:
            analysis[field] = [value]
    if not analysis["source_conflicts"]:
        analysis["source_conflicts"] = source_conflicts
    if not analysis["source_profiles"]:
        analysis["source_profiles"] = payload.get("source_profiles") or [
            item.get("source_profile")
            for item in evidence
            if isinstance(item.get("source_profile"), dict)
        ]
    if not analysis.get("executive_read"):
        analysis["executive_read"] = "The answer is limited to retrieved public text evidence and should be treated as a narrative read, not a forecast."
    if not isinstance(analysis.get("confidence"), dict):
        analysis["confidence"] = {"level": "low", "reason": "The model did not return a confidence object, so the relay lowered confidence."}
    analysis["confidence"].setdefault("level", "low")
    analysis["confidence"].setdefault(
        "reason",
        f"Based on {len(evidence)} retrieved passages across {plan['source_count']} source groups.",
    )
    if len(evidence) < 6 and not any("thin" in str(item).lower() for item in analysis["missing_evidence"]):
        analysis["missing_evidence"].append("Evidence set is thin; treat the result as a first-pass read.")
    if plan["source_count"] < 3 and not any("source coverage" in str(item).lower() for item in analysis["missing_evidence"]):
        analysis["missing_evidence"].append("Source coverage is narrow; add more source groups before relying on a stronger conclusion.")
    if not analysis["evidence_citations"]:
        analysis["evidence_citations"] = [
            {
                "evidence_index": index,
                "source_type": item.get("source_type", ""),
                "title": item.get("title", ""),
                "date": item.get("date", ""),
                "url": item.get("source_url", ""),
            }
            for index, item in enumerate(evidence[:8], start=1)
        ]
    return analysis


def parse_json_object(text: str) -> dict:
    """Parse strict JSON, with a fallback for model replies wrapped in fences."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        candidates = []
        for match in re.finditer(r"\{", text):
            try:
                value, _ = decoder.raw_decode(text[match.start():])
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                candidates.append(value)
        for value in candidates:
            if any(key in value for key in ("executive_read", "confidence", "explicit_claims")):
                return value
        if candidates:
            return candidates[-1]
        raise


def normalized_provider_analysis(text: str, payload: dict) -> dict:
    try:
        return normalize_analysis(parse_json_object(text), payload)
    except Exception:
        analysis = normalize_analysis(local_analyst(payload), payload)
        analysis["missing_evidence"].append(
            "The remote model returned a response that could not be parsed as the required JSON schema, so the relay used the local structured fallback."
        )
        analysis["confidence"]["level"] = "low"
        return analysis


def analysis_user_content(payload: dict) -> str:
    contract = payload.get("analysis_contract") or {}
    return (
        f"Question: {payload.get('question', '')}\n\n"
        f"Fixed analysis contract:\n{json.dumps(contract, indent=2)}\n\n"
        f"Analysis route selected by app:\n{json.dumps(analysis_plan(payload), indent=2)}\n\n"
        f"Source-specific reading rules:\n{source_profile_text(payload)}\n\n"
        f"Precomputed source conflict signals:\n{source_conflict_text(payload)}\n\n"
        f"Evidence:\n{evidence_text(payload)}"
    )


def local_analyst(payload: dict) -> dict:
    evidence = payload.get("evidence", [])
    source_conflicts = payload.get("source_conflicts") or []
    source_profiles = payload.get("source_profiles") or []
    plan = analysis_plan(payload)
    themes = {}
    source_types = {}
    risk_terms = ["risk", "uncertain", "volatility", "pressure", "challenge", "regulation", "tariff"]
    hedges = ["may", "could", "might", "monitor", "normalization", "subject to", "uncertain"]
    for item in evidence:
        themes[item.get("theme", "Unknown")] = themes.get(item.get("theme", "Unknown"), 0) + 1
        source_types[item.get("source_type", "Unknown")] = source_types.get(item.get("source_type", "Unknown"), 0) + 1
    top_themes = sorted(themes, key=themes.get, reverse=True)[:3]
    top_sources = sorted(source_types, key=source_types.get, reverse=True)[:4]
    explicit = [
        {
            "claim": item.get("sentence", "")[:260],
            "evidence_index": index,
            "source_type": item.get("source_type", ""),
            "title": item.get("title", ""),
        }
        for index, item in enumerate(evidence[:4], start=1)
    ]
    hedge_rows = []
    risk_rows = []
    for index, item in enumerate(evidence, start=1):
        sentence = item.get("sentence", "")
        lower = sentence.lower()
        if any(term in lower for term in hedges):
            hedge_rows.append({"phrase": sentence[:220], "evidence_index": index})
        if any(term in lower for term in risk_terms):
            risk_rows.append({"risk": sentence[:220], "evidence_index": index})
    return {
        "question_intent": plan["intent"],
        "analysis_plan": plan,
        "executive_read": (
            f"The retrieved evidence is concentrated in {', '.join(top_themes) or 'no dominant theme'} "
            f"across {', '.join(top_sources) or 'no source group'}. This is an evidence-grounded text read, not a trading recommendation."
        ),
        "explicit_claims": explicit,
        "implicit_signals": [
            {
                "signal": "Repeated risk or regulatory language may indicate movement from general discussion toward exposure, compliance, or uncertainty framing.",
                "evidence_index": risk_rows[0]["evidence_index"] if risk_rows else None,
            }
        ],
        "source_profiles": source_profiles,
        "source_tensions": [
            {
                "tension": "Compare company filing language with regulator or policymaker language before treating the narrative as one-sided.",
                "source_groups": top_sources,
            }
        ],
        "source_conflicts": source_conflicts,
        "contradictions": [],
        "narrative_shifts": [],
        "risk_flags": risk_rows[:5],
        "opportunity_signals": [],
        "speaker_incentives": [
            {
                "source_group": source,
                "possible_incentive": "This source type may frame the issue according to its institutional role; verify against other source groups.",
            }
            for source in top_sources
        ],
        "hedging_language": hedge_rows[:5],
        "missing_evidence": [
            "The retrieved evidence is not enough to infer market direction, company fundamentals, or investment action."
        ],
        "watch_items": [
            "New SEC filings or 8-K updates",
            "Regulatory releases mentioning the same theme",
            "Executive transcript language that repeats or changes these phrases",
        ],
        "source_reliability": [
            {
                "note": "Official filings and regulator releases are primary sources, but they still reflect institutional incentives and legal framing."
            }
        ],
        "market_relevance": [
            {
                "note": "The narrative may matter because public source framing can reveal risk salience, regulatory attention, or management emphasis."
            }
        ],
        "confidence": {
            "level": "medium" if len(evidence) >= 6 and len(source_types) >= 2 else "low",
            "reason": f"Based on {len(evidence)} passages across {len(source_types)} source types and {len(source_conflicts)} precomputed source conflict signals.",
        },
        "evidence_citations": [
            {
                "claim": item.get("sentence", "")[:120],
                "evidence_index": index,
                "source_type": item.get("source_type", ""),
                "title": item.get("title", ""),
                "date": item.get("date", ""),
            }
            for index, item in enumerate(evidence[:8], start=1)
        ],
    }


def local_summary(payload: dict) -> str:
    evidence = payload.get("evidence", [])
    if not evidence:
        return "No evidence was provided."
    themes = {}
    for item in evidence:
        themes[item.get("theme", "Unknown")] = themes.get(item.get("theme", "Unknown"), 0) + 1
    top = ", ".join(sorted(themes, key=themes.get, reverse=True)[:3])
    first = evidence[0]
    return (
        f"The retrieved evidence is concentrated in {top}. The strongest passage is from "
        f"{first.get('source_type', 'a source')} on {first.get('date', 'an unknown date')}: "
        f"{first.get('sentence', '')} This is an evidence summary only, not investment advice."
    )


def openai_compatible(payload: dict) -> str:
    api_key = os.environ["OPENAI_API_KEY"]
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    result = post_json(
        f"{base_url.rstrip('/')}/chat/completions",
        {
            "model": model,
            "messages": [
                {"role": "system", "content": ANALYST_PROMPT if payload.get("analysis_mode") == "analyst" else SYSTEM_PROMPT},
                {"role": "user", "content": analysis_user_content(payload)},
            ],
            "temperature": 0.2,
        },
        {"Authorization": f"Bearer {api_key}"},
    )
    return result["choices"][0]["message"]["content"]


def minimax_compatible(payload: dict) -> str:
    api_key = os.environ["MINIMAX_API_KEY"]
    base_url = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io/v1")
    primary_model = os.environ.get("MINIMAX_MODEL", "MiniMax-M2.1")
    fallback_models = [
        model.strip()
        for model in os.environ.get("MINIMAX_FALLBACK_MODELS", "MiniMax-M2.1,MiniMax-M2").split(",")
        if model.strip()
    ]
    models = list(dict.fromkeys([primary_model, *fallback_models]))
    max_tokens = int(os.environ.get("MINIMAX_MAX_TOKENS", "1400"))
    last_error: Exception | None = None
    for model in models:
        try:
            result = post_json(
                f"{base_url.rstrip('/')}/chat/completions",
                {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": MINIMAX_ANALYST_PROMPT if payload.get("analysis_mode") == "analyst" else SYSTEM_PROMPT,
                        },
                        {"role": "user", "content": analysis_user_content(payload)},
                    ],
                    "temperature": 0.2,
                    "max_tokens": max_tokens,
                    "response_format": {"type": "json_object"},
                },
                {"Authorization": f"Bearer {api_key}"},
            )
            return result["choices"][0]["message"]["content"]
        except Exception as exc:
            last_error = exc
            continue
    raise last_error or RuntimeError("MiniMax provider failed")


def openai_style_with_key(payload: dict, override: dict) -> str:
    api_key = override["api_key"]
    base_url = override.get("base_url") or (
        "https://api.minimax.io/v1"
        if override.get("engine") == "minimax-compatible"
        else "https://api.openai.com/v1"
    )
    model = override.get("model") or (
        os.environ.get("MINIMAX_MODEL", "MiniMax-M2.7")
        if override.get("engine") == "minimax-compatible"
        else os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    )
    result = post_json(
        f"{base_url.rstrip('/')}/chat/completions",
        {
            "model": model,
            "messages": [
                {"role": "system", "content": ANALYST_PROMPT if payload.get("analysis_mode") == "analyst" else SYSTEM_PROMPT},
                {"role": "user", "content": analysis_user_content(payload)},
            ],
            "temperature": 0.2,
        },
        {"Authorization": f"Bearer {api_key}"},
    )
    return result["choices"][0]["message"]["content"]


def anthropic_with_key(payload: dict, override: dict) -> str:
    model = override.get("model") or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
    result = post_json(
        "https://api.anthropic.com/v1/messages",
        {
            "model": model,
            "max_tokens": 1200,
            "system": ANALYST_PROMPT if payload.get("analysis_mode") == "analyst" else SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": analysis_user_content(payload)}],
        },
        {"x-api-key": override["api_key"], "anthropic-version": "2023-06-01"},
    )
    return "".join(part.get("text", "") for part in result.get("content", []))


def provider_override(payload: dict) -> tuple[str | None, str | None]:
    override = payload.get("provider_override") or {}
    engine = override.get("engine")
    api_key = override.get("api_key")
    if not engine or engine == "auto" or not api_key:
        return None, None
    if engine in {"minimax-compatible", "openai-compatible"}:
        return engine, openai_style_with_key(payload, override)
    if engine == "anthropic-compatible":
        return engine, anthropic_with_key(payload, override)
    return None, None


def anthropic_compatible(payload: dict) -> str:
    api_key = os.environ["ANTHROPIC_API_KEY"]
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
    result = post_json(
        "https://api.anthropic.com/v1/messages",
        {
            "model": model,
            "max_tokens": 900,
            "system": ANALYST_PROMPT if payload.get("analysis_mode") == "analyst" else SYSTEM_PROMPT,
            "messages": [
                {
                    "role": "user",
                    "content": analysis_user_content(payload),
                }
            ],
        },
        {"x-api-key": api_key, "anthropic-version": "2023-06-01"},
    )
    return "".join(part.get("text", "") for part in result.get("content", []))


def ollama(payload: dict) -> str:
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    model = os.environ.get("OLLAMA_MODEL", "llama3.1")
    result = post_json(
        f"{host.rstrip('/')}/api/generate",
        {
            "model": model,
            "prompt": f"{ANALYST_PROMPT if payload.get('analysis_mode') == 'analyst' else SYSTEM_PROMPT}\n\n{analysis_user_content(payload)}",
            "stream": False,
        },
    )
    return result.get("response", "")


def auto_provider(payload: dict) -> tuple[str | None, str | None]:
    candidates = []
    if os.environ.get("MINIMAX_API_KEY"):
        candidates.append(("minimax-compatible", minimax_compatible))
    if os.environ.get("OPENAI_API_KEY"):
        candidates.append(("openai-compatible", openai_compatible))
    if os.environ.get("ANTHROPIC_API_KEY"):
        candidates.append(("anthropic-compatible", anthropic_compatible))
    if os.environ.get("OLLAMA_MODEL"):
        candidates.append(("ollama", ollama))
    for name, provider in candidates:
        try:
            return name, provider(payload)
        except Exception:
            continue
    return None, None


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.end_headers()

    def do_POST(self) -> None:
        if self.path != "/api/analyze":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        engine = payload.get("engine", "local")
        try:
            analyst = payload.get("analysis_mode") == "analyst"
            override_provider, override_summary = provider_override(payload)
            if override_summary:
                result = {"analysis": normalized_provider_analysis(override_summary, payload), "provider": override_provider} if analyst else {
                    "summary": override_summary,
                    "provider": override_provider,
                }
            elif engine == "auto":
                provider, summary = auto_provider(payload)
                if summary:
                    result = {"analysis": normalized_provider_analysis(summary, payload), "provider": provider} if analyst else {
                        "summary": summary,
                        "provider": provider,
                    }
                else:
                    result = {"analysis": normalize_analysis(local_analyst(payload), payload), "provider": "local"} if analyst else {
                        "summary": local_summary(payload),
                        "provider": "local",
                    }
            elif engine == "local" and analyst:
                result = {"analysis": normalize_analysis(local_analyst(payload), payload)}
            elif engine == "openai-compatible":
                summary = openai_compatible(payload)
                result = {"analysis": normalized_provider_analysis(summary, payload)} if analyst else {"summary": summary}
            elif engine == "minimax-compatible":
                summary = minimax_compatible(payload)
                result = {"analysis": normalized_provider_analysis(summary, payload)} if analyst else {"summary": summary}
            elif engine == "anthropic-compatible":
                summary = anthropic_compatible(payload)
                result = {"analysis": normalized_provider_analysis(summary, payload)} if analyst else {"summary": summary}
            elif engine == "ollama":
                summary = ollama(payload)
                result = {"analysis": normalized_provider_analysis(summary, payload)} if analyst else {"summary": summary}
            else:
                summary = local_summary(payload)
                result = {"summary": summary}
            body = json.dumps(result).encode("utf-8")
            self.send_response(200)
        except Exception as exc:
            body = json.dumps({"error": str(exc)}).encode("utf-8")
            self.send_response(500)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            return


def main() -> None:
    port = int(os.environ.get("MNR_RELAY_PORT", "8787"))
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"LLM relay listening on http://127.0.0.1:{port}/api/analyze")
    server.serve_forever()


if __name__ == "__main__":
    main()
