const THEMES = {
  "AI & semiconductors": [
    "ai",
    "artificial intelligence",
    "chip",
    "semiconductor",
    "gpu",
    "data center",
    "compute",
    "technology",
    "nvidia",
  ],
  "Rates & inflation": [
    "rate",
    "rates",
    "inflation",
    "monetary",
    "federal reserve",
    "treasury",
    "yield",
    "deficit",
    "debt",
  ],
  "China & trade": [
    "china",
    "tariff",
    "trade",
    "export",
    "supply chain",
    "geopolitical",
    "taiwan",
    "manufacturing",
  ],
  "Regulation & antitrust": [
    "regulation",
    "regulatory",
    "antitrust",
    "sec",
    "ftc",
    "doj",
    "compliance",
    "law",
    "legal",
  ],
  "Demand & margins": [
    "demand",
    "margin",
    "revenue",
    "growth",
    "customer",
    "pricing",
    "earnings",
    "profit",
  ],
  "Risk & uncertainty": [
    "risk",
    "uncertain",
    "volatility",
    "concern",
    "pressure",
    "challenge",
    "exposure",
    "material",
  ],
};

const RISK_WORDS = [
  "risk",
  "uncertain",
  "volatility",
  "decline",
  "loss",
  "pressure",
  "challenge",
  "litigation",
  "regulatory",
  "slowdown",
  "tariff",
  "shortage",
];

const POSITIVE_WORDS = [
  "growth",
  "opportunity",
  "improve",
  "strong",
  "benefit",
  "innovation",
  "demand",
  "resilient",
  "investment",
];

const DATA_SOURCE_ENGINES = [
  {
    name: "SEC EDGAR",
    coverage: "10-K, 10-Q, 8-K, XBRL facts, filing history",
    auth: "No key",
    url: "https://data.sec.gov/",
    status: "stable",
  },
  {
    name: "GDELT DOC 2.0",
    coverage: "Global news search over a rolling news window",
    auth: "No key",
    url: "https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/",
    status: "rate-sensitive",
  },
  {
    name: "Federal Reserve RSS",
    coverage: "Speeches, testimony, policy releases, research feeds",
    auth: "No key",
    url: "https://www.federalreserve.gov/feeds/",
    status: "stable",
  },
  {
    name: "Federal Register",
    coverage: "Rules, proposed rules, notices, agency actions",
    auth: "Public API",
    url: "https://www.federalregister.gov/developers/documentation/api/v1",
    status: "stable",
  },
  {
    name: "Congress.gov",
    coverage: "Bills, members, Congressional Record, committee data",
    auth: "Free key",
    url: "https://api.congress.gov/",
    status: "needs key",
  },
  {
    name: "FRED",
    coverage: "Macro time series for joining text with rates/inflation context",
    auth: "Free key",
    url: "https://fred.stlouisfed.org/docs/api/fred/",
    status: "needs key",
  },
  {
    name: "NY Fed Blog",
    coverage: "Research posts on macro, credit, markets, and financial stability",
    auth: "No key",
    url: "https://libertystreeteconomics.newyorkfed.org/feed/",
    status: "stable",
  },
  {
    name: "FTC Competition",
    coverage: "Competition and antitrust press releases",
    auth: "No key",
    url: "https://www.ftc.gov/feeds/press-release-competition.xml",
    status: "stable",
  },
  {
    name: "DOJ Antitrust",
    coverage: "Antitrust press releases, speeches, and videos",
    auth: "No key",
    url: "https://www.justice.gov/atr/news-feeds",
    status: "stable",
  },
  {
    name: "CFTC",
    coverage: "Derivatives market press releases, enforcement, speeches",
    auth: "No key",
    url: "https://www.cftc.gov/RSS/index.htm",
    status: "stable",
  },
];

const ANALYSIS_ENGINE = "auto";
const LLM_RELAY_ENDPOINT = "http://127.0.0.1:8787/api/analyze";
const DATA_RELAY_ENDPOINT = "http://127.0.0.1:8790/api/live-sources";
const ANALYSIS_CONTRACT = {
  pipeline: [
    "classify_question",
    "refresh_public_sources",
    "retrieve_evidence",
    "score_source_conflicts",
    "call_analysis_engine",
    "validate_json_shape",
    "render_memo_with_evidence",
  ],
  required_fields: [
    "executive_read",
    "explicit_claims",
    "implicit_signals",
    "source_conflicts",
    "source_tensions",
    "contradictions",
    "risk_flags",
    "missing_evidence",
    "watch_items",
    "confidence",
    "evidence_citations",
  ],
  answer_rules: [
    "Use retrieved evidence only.",
    "Tie implications to source text.",
    "Separate direct claims from interpretation.",
    "Lower confidence when evidence is thin or source coverage is narrow.",
    "Do not provide trading recommendations, price targets, or portfolio instructions.",
  ],
};

let corpus = [];
let activeEvidence = [];
let latestLiveHealth = [];

const $ = (id) => document.getElementById(id);

function tokenize(text) {
  return (text || "")
    .toLowerCase()
    .replace(/[^a-z0-9$\s-]/g, " ")
    .split(/\s+/)
    .filter((word) => word.length > 2);
}

function sentences(text) {
  return (text || "")
    .replace(/\s+/g, " ")
    .split(/(?<=[.!?])\s+/)
    .filter(Boolean);
}

function countPhrase(text, phrase) {
  const escaped = phrase.toLowerCase().replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return (text.toLowerCase().match(new RegExp(`\\b${escaped}\\b`, "g")) || [])
    .length;
}

function scoreTheme(doc, theme) {
  const text = `${doc.title || ""} ${doc.text || ""}`.toLowerCase();
  const hits = THEMES[theme].reduce((sum, term) => sum + countPhrase(text, term), 0);
  const lengthNorm = Math.max(1, tokenize(text).length / 220);
  return hits / lengthNorm;
}

function scoreWords(doc, words) {
  const text = `${doc.title || ""} ${doc.text || ""}`.toLowerCase();
  const hits = words.reduce((sum, term) => sum + countPhrase(text, term), 0);
  return hits / Math.max(1, tokenize(text).length / 220);
}

function dominantTheme(doc) {
  return Object.keys(THEMES)
    .map((theme) => [theme, scoreTheme(doc, theme)])
    .sort((a, b) => b[1] - a[1])[0];
}

function normalizePercent(value, max) {
  if (!max) return 0;
  return Math.max(2, Math.round((value / max) * 100));
}

function filteredCorpus() {
  const ticker = $("tickerFilter").value.trim().toLowerCase();
  const source = $("sourceFilter").value;
  const theme = $("themeFilter").value;
  const limit = Number($("docLimit").value || 120);
  return corpus
    .filter((doc) => {
      const haystack = `${doc.ticker || ""} ${doc.title || ""} ${doc.text || ""} ${
        doc.organization || ""
      }`.toLowerCase();
      if (ticker && !haystack.includes(ticker)) return false;
      if (source !== "all" && doc.source_type !== source) return false;
      if (theme !== "all" && dominantTheme(doc)[0] !== theme) return false;
      return true;
    })
    .slice(0, limit);
}

function populateFilters() {
  const sources = [...new Set(corpus.map((doc) => doc.source_type).filter(Boolean))].sort();
  $("sourceFilter").innerHTML =
    '<option value="all">All sources</option>' +
    sources.map((source) => `<option value="${source}">${source}</option>`).join("");

  $("themeFilter").innerHTML =
    '<option value="all">All themes</option>' +
    Object.keys(THEMES).map((theme) => `<option value="${theme}">${theme}</option>`).join("");
}

function renderBars(target, entries, accent = "theme") {
  const max = Math.max(...entries.map(([, value]) => value), 0);
  target.innerHTML = entries
    .map(([label, value]) => {
      const width = normalizePercent(value, max);
      return `<div class="bar-row">
        <span class="bar-label">${label}</span>
        <span class="bar-track"><span class="bar-fill ${accent}" style="width:${width}%"></span></span>
        <span class="bar-value">${value.toFixed(1)}</span>
      </div>`;
    })
    .join("");
}

function summarizeCorpus(docs) {
  const themeScores = Object.keys(THEMES).map((theme) => [
    theme,
    docs.reduce((sum, doc) => sum + scoreTheme(doc, theme), 0),
  ]);
  themeScores.sort((a, b) => b[1] - a[1]);

  const sourceScores = [...new Set(docs.map((doc) => doc.source_type))].map((source) => [
    source,
    docs.filter((doc) => doc.source_type === source).length,
  ]);
  sourceScores.sort((a, b) => b[1] - a[1]);

  const risk = docs.reduce((sum, doc) => sum + scoreWords(doc, RISK_WORDS), 0);
  const positive = docs.reduce((sum, doc) => sum + scoreWords(doc, POSITIVE_WORDS), 0);
  const tension =
    sourceScores.length <= 1
      ? 0
      : Math.max(...sourceScores.map(([, value]) => value)) -
        Math.min(...sourceScores.map(([, value]) => value));

  return { themeScores, sourceScores, risk, positive, tension };
}

function estimateSyllables(word) {
  const cleaned = word.toLowerCase().replace(/[^a-z]/g, "");
  if (!cleaned) return 0;
  const groups = cleaned.match(/[aeiouy]+/g);
  return Math.max(1, groups ? groups.length : 1);
}

function readabilityScore(docs) {
  const text = docs.map((doc) => doc.text || "").join(" ");
  const words = tokenize(text);
  const sentenceCount = Math.max(1, sentences(text).length);
  const syllables = words.reduce((sum, word) => sum + estimateSyllables(word), 0);
  if (!words.length) return 0;
  return 206.835 - 1.015 * (words.length / sentenceCount) - 84.6 * (syllables / words.length);
}

function corpusDiagnostics(docs) {
  const sources = new Set(docs.map((doc) => doc.source_type));
  const tokens = docs.flatMap((doc) => tokenize(doc.text));
  const unique = new Set(tokens);
  const dated = docs
    .map((doc) => Date.parse(doc.date))
    .filter((value) => Number.isFinite(value))
    .sort((a, b) => b - a);
  const newest = dated.length ? new Date(dated[0]).toISOString().slice(0, 10) : "unknown";
  const diversity = tokens.length ? unique.size / tokens.length : 0;
  return {
    sourceCount: sources.size,
    tokenCount: tokens.length,
    diversity,
    readability: readabilityScore(docs),
    newest,
  };
}

function extractEntities(docs) {
  const stop = new Set([
    "The",
    "This",
    "That",
    "There",
    "And",
    "But",
    "For",
    "Other",
    "Total",
    "Item",
    "Speaker",
    "Mr",
    "Mrs",
    "Ms",
    "Madam Speaker",
    "United",
    "States",
    "Congressional",
    "Management",
    "Discussion",
    "Risk",
    "Factors",
  ]);
  const counts = new Map();
  const tickerCounts = new Map();
  for (const doc of docs) {
    for (const ticker of String(doc.ticker || "").split(/\s+/).filter(Boolean)) {
      tickerCounts.set(ticker, (tickerCounts.get(ticker) || 0) + 1);
    }
    const text = `${doc.title || ""} ${doc.organization || ""} ${doc.text || ""}`;
    const matches = text.match(/\b(?:[A-Z][a-z]+|[A-Z]{2,})(?:\s+(?:[A-Z][a-z]+|[A-Z]{2,}|of|and|&)){0,3}\b/g) || [];
    for (const raw of matches) {
      const entity = raw.trim().replace(/\s+/g, " ");
      if (entity.length < 3 || stop.has(entity) || /^\d+$/.test(entity)) continue;
      if (/\b(Mr|Mrs|Ms|Speaker|President|Chairman|Senator|Representative)\b$/.test(entity)) continue;
      if (/^(Mr|Mrs|Ms|Speaker|Madam Speaker|The|And|But|For)\b/.test(entity)) continue;
      if (entity.split(/\s+/).every((part) => stop.has(part))) continue;
      counts.set(entity, (counts.get(entity) || 0) + 1);
    }
  }
  const entities = [...counts.entries()]
    .filter(([, count]) => count >= 2)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 16);
  const tickers = [...tickerCounts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8);
  return { entities, tickers };
}

function watchlistTerms() {
  return $("watchlistBox").value
    .split(",")
    .map((term) => term.trim())
    .filter(Boolean);
}

function summarizeWatchlist(docs) {
  return watchlistTerms()
    .map((term) => {
      const matches = docs.filter((doc) => countPhrase(`${doc.title || ""} ${doc.text || ""}`, term));
      const risk = matches.reduce((sum, doc) => sum + scoreWords(doc, RISK_WORDS), 0);
      const sources = [...new Set(matches.map((doc) => doc.source_type))].slice(0, 3);
      return { term, count: matches.length, risk, sources };
    })
    .sort((a, b) => b.count - a.count || b.risk - a.risk);
}

function splitSentences(text) {
  return (text || "")
    .replace(/\s+/g, " ")
    .split(/(?<=[.!?])\s+/)
    .filter((sentence) => sentence.length > 80 && sentence.length < 520);
}

function retrieveEvidence(docs, question = "") {
  const qTokens = new Set(tokenize(question));
  const rows = [];
  for (const doc of docs) {
    const [theme, themeScore] = dominantTheme(doc);
    const sentences = splitSentences(doc.text).slice(0, 12);
    for (const sentence of sentences) {
      const tokens = tokenize(sentence);
      const overlap = tokens.reduce((sum, token) => sum + (qTokens.has(token) ? 1 : 0), 0);
      const score =
        overlap * 2 +
        scoreTheme({ ...doc, text: sentence }, theme) +
        scoreWords({ ...doc, text: sentence }, RISK_WORDS) * 0.4 +
        themeScore * 0.25;
      rows.push({ doc, theme, sentence, score });
    }
  }
  const sorted = rows.sort((a, b) => b.score - a.score);
  const selected = [];
  const usedDocs = new Set();
  const usedSources = new Set();

  for (const row of sorted) {
    if (selected.length >= 12) break;
    if (usedSources.has(row.doc.source_type)) continue;
    selected.push(row);
    usedDocs.add(row.doc.id);
    usedSources.add(row.doc.source_type);
  }

  for (const row of sorted) {
    if (selected.length >= 12) break;
    if (usedDocs.has(row.doc.id)) continue;
    selected.push(row);
    usedDocs.add(row.doc.id);
  }

  for (const row of sorted) {
    if (selected.length >= 12) break;
    if (!selected.includes(row)) selected.push(row);
  }

  return selected;
}

function sourceRole(sourceType = "") {
  const source = sourceType.toLowerCase();
  if (/company|filing|executive|transcript|earnings/.test(source)) return "company";
  if (/regulator|federal register|ftc|doj|cftc|sec/.test(source)) return "regulator";
  if (/federal reserve|fed|research blog|ny fed/.test(source)) return "macro_research";
  if (/congress|senate|house|committee/.test(source)) return "policymaker";
  if (/news|media|gdelt/.test(source)) return "media";
  return "other";
}

function stanceProfile(text = "") {
  const lower = text.toLowerCase();
  const countAny = (terms) => terms.reduce((sum, term) => sum + (lower.includes(term) ? 1 : 0), 0);
  const risk = countAny(["risk", "uncertain", "volatility", "pressure", "challenge", "litigation", "shortage", "slowdown"]);
  const opportunity = countAny(["growth", "opportunity", "strong", "demand", "investment", "benefit", "innovation", "resilient"]);
  const enforcement = countAny(["rule", "regulation", "antitrust", "compliance", "investigation", "enforcement", "proposed"]);
  const discipline = countAny(["margin", "cost", "efficiency", "discipline", "roi", "utilization", "pricing"]);
  return { risk, opportunity, enforcement, discipline };
}

function conflictOverlap(left, right) {
  const stop = new Set([
    "this",
    "that",
    "and",
    "the",
    "for",
    "not",
    "are",
    "was",
    "were",
    "has",
    "had",
    "but",
    "our",
    "you",
    "they",
    "them",
    "into",
    "also",
    "only",
    "more",
    "with",
    "from",
    "have",
    "will",
    "which",
    "their",
    "there",
    "these",
    "those",
    "subject",
    "within",
    "source",
    "statement",
    "statements",
    "forward",
    "looking",
  ]);
  const leftTokens = new Set(tokenize(`${left.doc.title || ""} ${left.sentence || ""}`).filter((token) => !stop.has(token)));
  const rightTokens = tokenize(`${right.doc.title || ""} ${right.sentence || ""}`).filter((token) => !stop.has(token));
  return rightTokens.reduce((sum, token) => sum + (leftTokens.has(token) ? 1 : 0), 0);
}

function hasNamedAnchor(left, right) {
  const anchorPattern = /\b[A-Z][A-Za-z0-9&.-]{2,}(?:\s+[A-Z][A-Za-z0-9&.-]{2,}){0,2}\b/g;
  const leftAnchors = new Set(`${left.doc.title || ""} ${left.sentence || ""}`.match(anchorPattern) || []);
  const rightAnchors = `${right.doc.title || ""} ${right.sentence || ""}`.match(anchorPattern) || [];
  return rightAnchors.some((anchor) => leftAnchors.has(anchor));
}

function hasOpposedFraming(left, right) {
  const leftConstructive = left.stance.opportunity > left.stance.risk + left.stance.enforcement;
  const rightRisk = right.stance.risk + right.stance.enforcement + right.stance.discipline > right.stance.opportunity;
  const leftRisk = left.stance.risk + left.stance.enforcement + left.stance.discipline > left.stance.opportunity;
  const rightConstructive = right.stance.opportunity > right.stance.risk + right.stance.enforcement;
  return (leftConstructive && rightRisk) || (leftRisk && rightConstructive);
}

function isRelevantConflict(left, right) {
  return conflictOverlap(left, right) >= 2 && hasNamedAnchor(left, right) && hasOpposedFraming(left, right);
}

function detectSourceConflicts(evidence) {
  const grouped = new Map();
  evidence.forEach((item, index) => {
    const key = item.theme || "Unknown";
    const role = sourceRole(item.doc.source_type);
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key).push({
      ...item,
      evidence_index: index + 1,
      role,
      stance: stanceProfile(`${item.doc.title || ""} ${item.sentence || ""}`),
    });
  });

  const conflicts = [];
  for (const [theme, rows] of grouped.entries()) {
    const company = rows.find((row) => row.role === "company");
    const regulator = rows.find((row) => row.role === "regulator" || row.role === "policymaker");
    const macro = rows.find((row) => row.role === "macro_research");
    const media = rows.find((row) => row.role === "media");
    if (company && regulator && isRelevantConflict(company, regulator)) {
      const companyConstructive = company.stance.opportunity >= company.stance.risk;
      const regulatorRisk = regulator.stance.enforcement + regulator.stance.risk > 0;
      if (companyConstructive || regulatorRisk) {
        conflicts.push({
          theme,
          conflict_type: "company_vs_public_authority_framing_gap",
          source_groups: [company.doc.source_type, regulator.doc.source_type],
          signal: "Company-facing language and public-authority language appear to frame the same anchored topic differently.",
          company_side: company.sentence.slice(0, 260),
          public_authority_side: regulator.sentence.slice(0, 260),
          evidence_index: [company.evidence_index, regulator.evidence_index],
          confidence: "low_to_medium",
          what_to_check_next: "Compare full filing language, regulator release context, and any executive transcript on the same theme.",
        });
      }
    }
    if (macro && (company || media)) {
      const other = company || media;
      const macroRisk =
        isRelevantConflict(macro, other) &&
        macro.stance.risk + macro.stance.discipline > other.stance.risk + other.stance.discipline;
      if (macroRisk) {
        conflicts.push({
          theme,
          conflict_type: "macro_risk_vs_market_story_framing_gap",
          source_groups: [macro.doc.source_type, other.doc.source_type],
          signal: "Macro or research language appears more cautious than market-facing language on the same anchored topic.",
          cautious_side: macro.sentence.slice(0, 260),
          comparison_side: other.sentence.slice(0, 260),
          evidence_index: [macro.evidence_index, other.evidence_index],
          confidence: "low",
          what_to_check_next: "Look for newer speeches, research posts, filings, and news that repeat the same caution terms.",
        });
      }
    }
  }
  return conflicts.slice(0, 5);
}

function renderBrief(docs, evidence) {
  if (!docs.length) {
    $("briefOutput").innerHTML = "<p>Load or import text to generate a research brief.</p>";
    $("analystOutput").innerHTML = "";
    return;
  }
  const { themeScores, risk, positive } = summarizeCorpus(docs);
  const top = themeScores.slice(0, 3).map(([theme]) => theme);
  const tone =
    risk > positive * 1.25
      ? "risk-heavy"
      : positive > risk * 1.25
        ? "constructive"
        : "mixed";
  const sourceList = [...new Set(evidence.slice(0, 6).map((item) => item.doc.source_type))].join(
    ", ",
  );
  const bullets = evidence
    .slice(0, 5)
    .map(
      (item) =>
        `<li><strong>${item.theme}</strong>: ${escapeHtml(item.sentence)} <em>(${escapeHtml(
          item.doc.source_type,
        )}, ${escapeHtml(item.doc.title || "Untitled")})</em></li>`,
    )
    .join("");

  $("briefOutput").innerHTML = `
    <p><strong>Current read:</strong> The loaded corpus is ${tone}. The leading narrative themes are ${top.join(
      ", ",
    )}. Evidence is concentrated in ${sourceList || "the loaded sources"}.</p>
    <p><strong>Research boundary:</strong> This is a text-based narrative summary, not a forecast or trading recommendation.</p>
    <ul>${bullets}</ul>
  `;
  $("analystOutput").innerHTML = "";
  renderCitationAudit(evidence);
}

function createLocalAnalystJson(docs, evidence) {
  const summary = summarizeCorpus(docs);
  const sourceConflicts = detectSourceConflicts(evidence);
  const sourceCounts = new Map();
  const themeCounts = new Map();
  const riskTerms = ["risk", "uncertain", "volatility", "pressure", "challenge", "regulation", "tariff", "investigation", "shortage"];
  const hedgeTerms = ["may", "could", "might", "monitor", "uncertain", "expects", "subject to", "approximately", "likely"];

  evidence.forEach((item) => {
    sourceCounts.set(item.doc.source_type, (sourceCounts.get(item.doc.source_type) || 0) + 1);
    themeCounts.set(item.theme, (themeCounts.get(item.theme) || 0) + 1);
  });

  const topSources = [...sourceCounts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 4);
  const topThemes = [...themeCounts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 4);
  const riskFlags = [];
  const hedgingLanguage = [];

  evidence.forEach((item, index) => {
    const sentence = item.sentence || "";
    const lower = sentence.toLowerCase();
    if (riskTerms.some((term) => lower.includes(term))) {
      riskFlags.push({
        risk: sentence.slice(0, 260),
        why_it_matters: "This wording raises uncertainty, regulatory, operational, or policy salience.",
        evidence_index: index + 1,
      });
    }
    if (hedgeTerms.some((term) => lower.includes(term))) {
      hedgingLanguage.push({
        phrase: sentence.slice(0, 260),
        interpretation: "The source leaves room for uncertainty or avoids a firm directional claim.",
        evidence_index: index + 1,
      });
    }
  });

  return {
    executive_read: `The retrieved corpus is led by ${topThemes.map(([theme]) => theme).join(", ") || "no clear theme"} across ${topSources.map(([source]) => source).join(", ") || "limited sources"}. Treat this as text evidence about narrative pressure, not as investment advice.`,
    explicit_claims: evidence.slice(0, 6).map((item, index) => ({
      claim: item.sentence.slice(0, 300),
      source_type: item.doc.source_type,
      title: item.doc.title,
      date: item.doc.date,
      evidence_index: index + 1,
    })),
    implicit_signals: [
      {
        signal: "Narrative concentration may indicate that the issue is becoming more salient across public documents.",
        support: topThemes.map(([theme, count]) => `${theme}: ${count}`).join("; "),
        evidence_index: evidence.length ? 1 : null,
      },
      {
        signal: "Cross-source repetition is more meaningful when filings, regulators, and policymakers use similar language.",
        support: topSources.map(([source, count]) => `${source}: ${count}`).join("; "),
        evidence_index: evidence.length > 1 ? 2 : null,
      },
    ],
    source_tensions: [
      {
        tension: "Company, policymaker, regulator, and media sources can describe the same topic with different incentives and legal constraints.",
        source_groups: topSources.map(([source]) => source),
        what_to_check_next: "Compare whether official filings use risk language while public commentary uses opportunity or policy framing.",
      },
    ],
    source_conflicts: sourceConflicts,
    contradictions: [],
    narrative_shifts: [
      {
        shift: "Current evidence should be compared against future documents for changes in wording, certainty, named actors, and repeated risk terms.",
        evidence_index: evidence.length ? 1 : null,
      },
    ],
    risk_flags: riskFlags.slice(0, 6),
    opportunity_signals: summary.positive > summary.risk
      ? [{
          signal: "Constructive language is currently stronger than risk language in the loaded corpus.",
          caveat: "Positive tone alone does not imply market upside.",
        }]
      : [],
    speaker_incentives: topSources.map(([source]) => ({
      source_group: source,
      possible_incentive: "This source group may emphasize facts that fit its institutional role, disclosure duty, policy goal, or audience.",
    })),
    hedging_language: hedgingLanguage.slice(0, 6),
    missing_evidence: [
      "This evidence does not by itself prove company fundamentals, price impact, or causality.",
      "A stronger read needs more time history, direct transcripts, full filings, and source-group comparison.",
    ],
    watch_items: [
      "New SEC 8-K, 10-Q, and risk-factor language",
      "Regulator releases that reuse the same terms",
      "Executive interviews or earnings calls that shift from confident to hedged wording",
      "Policy speeches, committee statements, or agency blogs that name the same sector",
    ],
    source_reliability: topSources.map(([source, count]) => ({
      source_group: source,
      evidence_count: count,
      reliability_note: "Primary and official sources are stronger for attribution, but still need incentive-aware interpretation.",
    })),
    market_relevance: [
      {
        channel: "Narrative risk",
        relevance: "Public language can reveal which risks, sectors, or policy questions are becoming more visible.",
      },
      {
        channel: "Information timing",
        relevance: "Fresh public text can help build a watchlist before the same themes are widely summarized elsewhere.",
      },
    ],
    confidence: {
      level: evidence.length >= 8 && topSources.length >= 3 ? "medium" : "low",
      reason: `Based on ${evidence.length} retrieved passages, ${topSources.length} source groups, ${sourceConflicts.length} source conflict signals, and transparent local NLP rules.`,
    },
    evidence_citations: evidence.slice(0, 8).map((item, index) => ({
      evidence_index: index + 1,
      source_type: item.doc.source_type,
      title: item.doc.title,
      date: item.doc.date,
      url: item.doc.source_url,
    })),
  };
}

function renderAnalystOutput(analysis) {
  if (!analysis || typeof analysis !== "object") {
    $("analystOutput").innerHTML = "";
    return;
  }
  const humanLabel = (key) => key.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
  const compactText = (value) => {
    if (Array.isArray(value)) return value.join(", ");
    if (value && typeof value === "object") {
      return Object.entries(value)
        .map(([key, itemValue]) => `${humanLabel(key)}: ${Array.isArray(itemValue) ? itemValue.join(", ") : itemValue}`)
        .join(" | ");
    }
    return value || "";
  };
  const renderObject = (item) => {
    const evidenceIndex = item.evidence_index ? `<span class="evidence-tag">Evidence ${escapeHtml(item.evidence_index)}</span>` : "";
    const rows = Object.entries(item)
      .filter(([key]) => key !== "evidence_index")
      .map(([key, value]) => `<div class="analyst-kv">
        <span>${escapeHtml(humanLabel(key))}</span>
        <strong>${escapeHtml(compactText(value))}</strong>
      </div>`)
      .join("");
    return `${evidenceIndex}${rows}`;
  };
  const renderMemoItems = (items, fallback, limit = 3) => {
    const values = Array.isArray(items) ? items.slice(0, limit) : [];
    if (!values.length) return `<p class="empty-note">${escapeHtml(fallback)}</p>`;
    return `<ul>${values
      .map((item) => `<li>${item && typeof item === "object" ? renderObject(item) : escapeHtml(item)}</li>`)
      .join("")}</ul>`;
  };
  const contradictionCount = Array.isArray(analysis.contradictions) ? analysis.contradictions.length : 0;
  const conflictCount = Array.isArray(analysis.source_conflicts) ? analysis.source_conflicts.length : 0;
  const riskCount = Array.isArray(analysis.risk_flags) ? analysis.risk_flags.length : 0;
  const watchCount = Array.isArray(analysis.watch_items) ? analysis.watch_items.length : 0;

  $("briefOutput").innerHTML = `
    <p><strong>Analyst read:</strong> ${escapeHtml(analysis.executive_read || "Structured analysis returned.")}</p>
    <p><strong>Boundary:</strong> This is an evidence-based text read, not a forecast, price target, or trading recommendation.</p>
  `;
  $("analystOutput").innerHTML = `
    <div class="memo-strip">
      <div><span>Confidence</span><strong>${escapeHtml(analysis.confidence?.level || "unknown")}</strong></div>
      <div><span>Risks</span><strong>${riskCount}</strong></div>
      <div><span>Source conflicts</span><strong>${conflictCount}</strong></div>
      <div><span>Contradictions</span><strong>${contradictionCount}</strong></div>
      <div><span>Watch items</span><strong>${watchCount}</strong></div>
    </div>
    <section class="analyst-section highlight">
      <h3>What the text says directly</h3>
      ${renderMemoItems(analysis.explicit_claims, "No direct claim found in current evidence.", 3)}
    </section>
    <section class="analyst-section highlight">
      <h3>What it may imply</h3>
      ${renderMemoItems(analysis.implicit_signals, "No supported implication found in current evidence.", 3)}
    </section>
    <section class="analyst-section">
      <h3>Where sources may disagree</h3>
      ${renderMemoItems(
        conflictCount ? analysis.source_conflicts : (contradictionCount ? analysis.contradictions : analysis.source_tensions),
        "No direct contradiction found; compare source incentives before drawing a stronger conclusion.",
        3,
      )}
    </section>
    <section class="analyst-section">
      <h3>Risk flags and missing evidence</h3>
      ${renderMemoItems([...(analysis.risk_flags || []).slice(0, 2), ...(analysis.missing_evidence || []).slice(0, 2)], "No major risk flag found in current evidence.", 4)}
    </section>
    <section class="analyst-section">
      <h3>What to watch next</h3>
      ${renderMemoItems(analysis.watch_items, "No follow-up item generated.", 4)}
    </section>
    <details class="raw-analysis">
      <summary>Structured JSON fields</summary>
      <pre>${escapeHtml(JSON.stringify(analysis, null, 2))}</pre>
    </details>
  `;
}

function showStatus(message) {
  $("lastUpdated").textContent = message;
  if ($("analysisStatus")) $("analysisStatus").textContent = message;
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderEvidence(evidence) {
  activeEvidence = evidence;
  $("evidenceRows").innerHTML = evidence
    .map(({ doc, theme, sentence }) => {
      const url = doc.source_url && doc.source_url.startsWith("http")
        ? `<a href="${escapeHtml(doc.source_url)}" target="_blank" rel="noreferrer">open</a>`
        : escapeHtml(doc.source_url || "");
      return `<tr>
        <td>${escapeHtml(doc.source_type)}<br>${url}</td>
        <td>${escapeHtml(doc.date || "")}</td>
        <td>${escapeHtml(doc.title || "")}</td>
        <td><span class="theme-chip">${escapeHtml(theme)}</span></td>
        <td>${escapeHtml(sentence)}</td>
      </tr>`;
    })
    .join("");
}

function renderCitationAudit(evidence) {
  const uniqueDocs = new Set(evidence.map((item) => item.doc.id));
  const sourceTypes = new Set(evidence.map((item) => item.doc.source_type));
  const withUrls = evidence.filter((item) => item.doc.source_url).length;
  $("citationAudit").innerHTML = `
    <span>${evidence.length} passages</span>
    <span>${uniqueDocs.size} documents</span>
    <span>${sourceTypes.size} source types</span>
    <span>${withUrls}/${evidence.length} source refs</span>
  `;
}

function renderEntities(docs) {
  const { entities, tickers } = extractEntities(docs);
  const tickerHtml = tickers
    .map(([ticker, count]) => `<span class="chip ticker">${escapeHtml(ticker)} <small>${count}</small></span>`)
    .join("");
  const entityHtml = entities
    .map(([entity, count]) => `<span class="chip">${escapeHtml(entity)} <small>${count}</small></span>`)
    .join("");
  $("entityList").innerHTML = tickerHtml + entityHtml || "<span class=\"empty-note\">No entities yet</span>";
}

function renderQuality(docs) {
  const metrics = corpusDiagnostics(docs);
  const rows = [
    ["Tokens", metrics.tokenCount.toLocaleString()],
    ["Source types", metrics.sourceCount],
    ["Lexical diversity", metrics.diversity.toFixed(3)],
    ["Readability", metrics.readability.toFixed(1)],
    ["Newest date", metrics.newest],
  ];
  $("qualityMetrics").innerHTML = rows
    .map(([label, value]) => `<div class="metric-row"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");
}

function renderSourceHealth() {
  const liveBySource = Object.fromEntries(latestLiveHealth.map((item) => [item.source, item]));
  $("sourceHealth").innerHTML = DATA_SOURCE_ENGINES.map((engine) => {
    const live = liveBySource[engine.name];
    const status = live ? (live.ok ? `live ${live.count}` : "live error") : engine.status;
    return `<div class="health-row ${escapeHtml(status.replace(/\s+/g, "-"))}">
      <span>${escapeHtml(engine.name)}</span>
      <strong>${escapeHtml(status)}</strong>
    </div>`;
  }).join("");
}

function renderEngines() {
  $("engineCards").innerHTML = DATA_SOURCE_ENGINES.map(
    (engine) => `<a class="engine-card" href="${escapeHtml(engine.url)}" target="_blank" rel="noreferrer">
      <span>${escapeHtml(engine.auth)}</span>
      <strong>${escapeHtml(engine.name)}</strong>
      <small>${escapeHtml(engine.coverage)}</small>
    </a>`,
  ).join("");
}

function renderWatchlist(docs) {
  const alerts = summarizeWatchlist(docs);
  $("watchlistAlerts").innerHTML = alerts
    .map((alert) => {
      const level = alert.count >= 8 || alert.risk >= 10 ? "high" : alert.count >= 3 ? "medium" : "low";
      return `<div class="alert-card ${level}">
        <span>${escapeHtml(level)}</span>
        <strong>${escapeHtml(alert.term)}</strong>
        <small>${alert.count} matching documents ${
          alert.sources.length ? `across ${escapeHtml(alert.sources.join(", "))}` : "in current filter"
        }</small>
      </div>`;
    })
    .join("");
}

function providerOverride() {
  const engine = $("overrideEngine")?.value || "auto";
  const apiKey = $("overrideApiKey")?.value.trim() || "";
  if (engine === "auto" || !apiKey) return null;
  return {
    engine,
    api_key: apiKey,
    base_url: $("overrideBaseUrl")?.value.trim() || "",
    model: $("overrideModel")?.value.trim() || "",
  };
}

function render() {
  const docs = filteredCorpus();
  const summary = summarizeCorpus(docs);
  const question = $("questionBox").value;
  const evidence = retrieveEvidence(docs, question);

  $("docCount").textContent = String(docs.length);
  $("sourceMix").textContent = summary.sourceScores
    .slice(0, 3)
    .map(([source, count]) => `${source}: ${count}`)
    .join(" | ");
  $("topTheme").textContent = summary.themeScores[0]?.[0] || "-";
  $("topThemeDetail").textContent = `${(summary.themeScores[0]?.[1] || 0).toFixed(
    1,
  )} normalized hits`;
  $("riskTone").textContent =
    summary.risk > summary.positive * 1.25
      ? "Risk-heavy"
      : summary.positive > summary.risk * 1.25
        ? "Constructive"
        : "Mixed";
  $("riskToneDetail").textContent = `risk ${summary.risk.toFixed(1)} / positive ${summary.positive.toFixed(1)}`;
  $("sourceTension").textContent = summary.tension ? summary.tension.toFixed(0) : "Low";
  $("sourceTensionDetail").textContent = "Spread across source categories";

  renderBars($("themeBars"), summary.themeScores);
  renderBars($("sourceBars"), summary.sourceScores, "source");
  renderEntities(docs);
  renderQuality(docs);
  renderSourceHealth();
  renderWatchlist(docs);
  renderBrief(docs, evidence);
  renderEvidence(evidence);
  $("lastUpdated").textContent = `Updated ${new Date().toLocaleTimeString()}`;
  saveState();
}

async function runSelectedEngine() {
  const analysisMode = $("analysisMode").value;
  const question = $("questionBox").value;
  const askButton = $("askButton");
  askButton.disabled = true;
  askButton.textContent = "Analyzing...";
  showStatus("Refreshing public sources in the background...");
  await refreshLiveCorpusForQuestion(question);
  const docs = filteredCorpus();
  const evidence = retrieveEvidence(docs, question);
  const sourceConflicts = detectSourceConflicts(evidence);
  if (analysisMode === "brief") {
    renderBrief(docs, evidence);
    renderEvidence(evidence);
    askButton.disabled = false;
    askButton.textContent = "Analyze";
    return;
  }
  $("briefOutput").innerHTML = "<p><strong>Running analyst engine:</strong> analyzing retrieved public evidence.</p>";
  $("analystOutput").innerHTML = "";

  const analysisController = new AbortController();
  const analysisTimeout = window.setTimeout(() => analysisController.abort(), 18000);
  try {
    const response = await fetch(LLM_RELAY_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: analysisController.signal,
      body: JSON.stringify({
        engine: ANALYSIS_ENGINE,
        analysis_mode: analysisMode,
        analysis_contract: ANALYSIS_CONTRACT,
        provider_override: providerOverride(),
        question,
        themes: THEMES,
        source_conflicts: sourceConflicts,
        evidence: evidence.slice(0, 12).map(({ doc, theme, sentence }) => ({
          source_type: doc.source_type,
          date: doc.date,
          title: doc.title,
          source_url: doc.source_url,
          theme,
          sentence,
        })),
      }),
    });
    if (!response.ok) throw new Error(`Relay returned ${response.status}`);
    const payload = await response.json();
    if (payload.analysis) {
      if (!Array.isArray(payload.analysis.source_conflicts)) {
        payload.analysis.source_conflicts = sourceConflicts;
      }
      renderAnalystOutput(payload.analysis);
    } else {
      $("briefOutput").innerHTML = `<p>${escapeHtml(payload.summary || payload.text || "")}</p>`;
      $("analystOutput").innerHTML = "";
    }
    renderCitationAudit(evidence);
    renderEvidence(evidence);
    showStatus("Analysis complete.");
  } catch (error) {
    renderAnalystOutput(createLocalAnalystJson(docs, evidence));
    renderEvidence(evidence);
    $("briefOutput").insertAdjacentHTML(
      "afterbegin",
      `<p class="engine-warning"><strong>Relay unavailable:</strong> ${escapeHtml(
        error.message,
      )}. Falling back to local NLP.</p>`,
    );
    showStatus("Used local NLP fallback.");
  } finally {
    window.clearTimeout(analysisTimeout);
    askButton.disabled = false;
    askButton.textContent = "Analyze";
  }
}

async function loadSampleCorpus() {
  const response = await fetch("data/corpus.json");
  corpus = await response.json();
  populateFilters();
  render();
}

async function fetchLiveSources() {
  const query = $("liveQueryBox").value.trim();
  const url = new URL(DATA_RELAY_ENDPOINT);
  if (query) url.searchParams.set("query", query);
  url.searchParams.set("limit", "8");
  showStatus("Fetching live public sources...");
  try {
    const response = await fetch(url.toString());
    if (!response.ok) throw new Error(`Data relay returned ${response.status}`);
    const payload = await response.json();
    const docs = payload.documents || [];
    latestLiveHealth = payload.health || [];
    if (!docs.length) throw new Error("No documents returned");
    corpus = [...docs, ...corpus];
    populateFilters();
    render();
    showStatus(`Fetched ${docs.length} live documents from ${payload.sources?.join(", ") || "public sources"}`);
  } catch (error) {
    showStatus(`Live fetch failed: ${error.message}`);
  }
}

async function refreshLiveCorpusForQuestion(question) {
  const url = new URL(DATA_RELAY_ENDPOINT);
  const query = question.trim() || $("liveQueryBox").value.trim();
  if (query) url.searchParams.set("query", query);
  url.searchParams.set("limit", "8");
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 6500);
  try {
    const response = await fetch(url.toString(), { signal: controller.signal });
    if (!response.ok) throw new Error(`Data relay returned ${response.status}`);
    const payload = await response.json();
    const docs = payload.documents || [];
    latestLiveHealth = payload.health || [];
    if (docs.length) {
      const seen = new Set(corpus.map((doc) => doc.id || doc.source_url || `${doc.title}-${doc.date}`));
      const freshDocs = docs.filter((doc) => {
        const key = doc.id || doc.source_url || `${doc.title}-${doc.date}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
      if (freshDocs.length) {
        corpus = [...freshDocs, ...corpus];
        populateFilters();
      }
    }
    showStatus(docs.length ? `Refreshed ${docs.length} public documents.` : "Using current public corpus.");
  } catch {
    showStatus("Live source refresh unavailable; using current corpus.");
  } finally {
    window.clearTimeout(timeout);
  }
}


function saveState() {
  const state = {
    tickerFilter: $("tickerFilter").value,
    sourceFilter: $("sourceFilter").value,
    themeFilter: $("themeFilter").value,
    docLimit: $("docLimit").value,
    watchlistBox: $("watchlistBox").value,
    analysisMode: $("analysisMode").value,
    liveQueryBox: $("liveQueryBox").value,
  };
  try {
    localStorage.setItem("marketNarrativeRadarState", JSON.stringify(state));
  } catch {
    // localStorage can be blocked in strict browser contexts.
  }
}

function restoreState() {
  try {
    const state = JSON.parse(localStorage.getItem("marketNarrativeRadarState") || "{}");
    for (const [key, value] of Object.entries(state)) {
      if ($(key) && value !== undefined) $(key).value = value;
    }
  } catch {
    return;
  }
}

function parseCsvLine(line) {
  const result = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    const next = line[i + 1];
    if (char === '"' && quoted && next === '"') {
      field += '"';
      i += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      result.push(field);
      field = "";
    } else {
      field += char;
    }
  }
  result.push(field);
  return result;
}

function importCsv(text) {
  const lines = text.split(/\r?\n/).filter(Boolean);
  if (lines.length < 2) return;
  const headers = parseCsvLine(lines[0]).map((h) => h.trim());
  const docs = lines.slice(1).map((line, index) => {
    const values = parseCsvLine(line);
    const row = Object.fromEntries(headers.map((header, i) => [header, values[i] || ""]));
    return {
      id: row.id || `import-${Date.now()}-${index}`,
      date: row.date || "",
      source_type: row.source_type || row.source || "Imported text",
      speaker: row.speaker || "",
      organization: row.organization || "",
      party: row.party || "",
      ticker: row.ticker || "",
      title: row.title || `Imported document ${index + 1}`,
      source_url: row.source_url || "",
      text: row.text || row.doc_clean || "",
    };
  });
  corpus = [...docs, ...corpus];
  populateFilters();
  render();
}

function downloadText(filename, text, type = "text/plain") {
  const blob = new Blob([text], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function toCsvValue(value) {
  return `"${String(value || "").replace(/"/g, '""')}"`;
}

function exportJson() {
  downloadText(
    `market-narrative-radar-${new Date().toISOString().slice(0, 10)}.json`,
    JSON.stringify(filteredCorpus(), null, 2),
    "application/json",
  );
}

function exportCsv() {
  const rows = filteredCorpus();
  const headers = [
    "id",
    "date",
    "source_type",
    "speaker",
    "organization",
    "party",
    "ticker",
    "title",
    "source_url",
    "text",
  ];
  const csv = [headers.join(",")]
    .concat(rows.map((row) => headers.map((header) => toCsvValue(row[header])).join(",")))
    .join("\n");
  downloadText(`market-narrative-radar-${new Date().toISOString().slice(0, 10)}.csv`, csv, "text/csv");
}

function cleanTranscript(text) {
  return text
    .replace(/\r/g, "")
    .split("\n")
    .filter((line) => {
      const trimmed = line.trim();
      if (!trimmed || trimmed === "WEBVTT") return false;
      if (/^\d+$/.test(trimmed)) return false;
      if (/^\d{2}:\d{2}:\d{2}[,.]\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}[,.]\d{3}/.test(trimmed)) {
        return false;
      }
      return true;
    })
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
}

function addTextDocument(text, meta = {}) {
  if (!text) return;
  corpus.unshift({
    id: meta.id || `text-${Date.now()}`,
    date: new Date().toISOString().slice(0, 10),
    source_type: meta.source_type || "User supplied",
    speaker: "",
    organization: meta.organization || "Imported source",
    party: "",
    ticker: $("tickerFilter").value.trim(),
    title: meta.title || "User supplied market narrative text",
    source_url: meta.source_url || "User import",
    text,
  });
  populateFilters();
  render();
}

function addPastedText() {
  const raw = $("pasteBox").value.trim();
  const text = cleanTranscript(raw);
  if (!text) return;
  addTextDocument(text, {
    source_type: raw.includes("-->") || raw.startsWith("WEBVTT") ? "Video transcript" : "User supplied",
    organization: "Pasted source",
    title: "User supplied market narrative text",
    source_url: "User paste",
  });
  $("pasteBox").value = "";
}

$("loadSample").addEventListener("click", loadSampleCorpus);
$("askButton").addEventListener("click", runSelectedEngine);
$("fetchLive").addEventListener("click", fetchLiveSources);
$("pasteButton").addEventListener("click", addPastedText);
$("copyBrief").addEventListener("click", async () => {
  await navigator.clipboard.writeText($("briefOutput").innerText);
});
$("exportJson").addEventListener("click", exportJson);
$("exportCsv").addEventListener("click", exportCsv);
$("tickerFilter").addEventListener("input", render);
$("sourceFilter").addEventListener("change", render);
$("themeFilter").addEventListener("change", render);
$("docLimit").addEventListener("input", render);
$("watchlistBox").addEventListener("input", render);
$("analysisMode").addEventListener("change", saveState);
$("liveQueryBox").addEventListener("input", saveState);
$("csvUpload").addEventListener("change", async (event) => {
  const [file] = event.target.files;
  if (!file) return;
  const text = await file.text();
  if (file.name.toLowerCase().endsWith(".csv")) {
    importCsv(text);
  } else {
    addTextDocument(cleanTranscript(text), {
      source_type: file.name.match(/\.(srt|vtt)$/i) ? "Video transcript" : "Imported text",
      organization: "Uploaded file",
      title: file.name,
      source_url: "Local upload",
    });
  }
});

renderEngines();
restoreState();
loadSampleCorpus();
