#!/usr/bin/env python3
"""Build the Market Narrative Radar demo corpus.

The script uses only the Python standard library so the project can be
reproduced in a simple local environment.
"""

from __future__ import annotations

import csv
import html
import json
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COURSE_CONGRESS_CSV = ROOT.parent / "hw10" / "us_congress_speeches_sample.csv"
OUT = ROOT / "data" / "corpus.json"

MARKET_TERMS = [
    "inflation",
    "interest rate",
    "federal reserve",
    "china",
    "trade",
    "tariff",
    "technology",
    "artificial intelligence",
    "chip",
    "semiconductor",
    "bank",
    "energy",
    "manufacturing",
    "regulation",
    "market",
    "investment",
    "supply chain",
]

SEC_FILINGS = [
    (
        "NVDA",
        "10-K",
        "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm",
        "2026-02-25",
    ),
    (
        "AAPL",
        "10-Q",
        "https://www.sec.gov/Archives/edgar/data/320193/000032019326000013/aapl-20260328.htm",
        "2026-05-01",
    ),
    (
        "MSFT",
        "10-Q",
        "https://www.sec.gov/Archives/edgar/data/789019/000119312526191507/msft-20260331.htm",
        "2026-04-29",
    ),
]

FED_SPEECHES = [
    "https://www.federalreserve.gov/newsevents/speech/kugler20241203a.htm",
    "https://www.federalreserve.gov/newsevents/speech/waller20241202a.htm",
    "https://www.federalreserve.gov/newsevents/speech/bowman20241122a.htm",
    "https://www.federalreserve.gov/newsevents/speech/powell20241114a.htm",
    "https://www.federalreserve.gov/newsevents/speech/cook20241120a.htm",
]

NYFED_RSS = "https://libertystreeteconomics.newyorkfed.org/feed/"


def fetch(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "market-narrative-radar academic project contact@example.com",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def clean_html(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
    raw = re.sub(r"(?is)<br\s*/?>", "\n", raw)
    raw = re.sub(r"(?is)</p>", "\n", raw)
    raw = re.sub(r"(?is)<.*?>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"\s+", " ", raw)
    return raw.strip()


def short(text: str, max_chars: int = 5000) -> str:
    return text[:max_chars].strip()


def contains_market_language(text: str) -> bool:
    lower = text.lower()
    return any(term in lower for term in MARKET_TERMS)


def build_congress_docs() -> list[dict]:
    if not COURSE_CONGRESS_CSV.exists():
        print(f"warning: missing {COURSE_CONGRESS_CSV}", file=sys.stderr)
        return []

    docs: list[dict] = []
    with COURSE_CONGRESS_CSV.open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            text = row.get("speech", "") or row.get("text", "") or row.get("doc_clean", "")
            if not text or not contains_market_language(text):
                continue
            docs.append(
                {
                    "id": f"congress-{len(docs) + 1:03d}",
                    "date": row.get("date", ""),
                    "source_type": "Congress",
                    "speaker": row.get("speaker", "") or row.get("speaker_name", ""),
                    "organization": "U.S. Congress",
                    "party": row.get("party", ""),
                    "ticker": "SPY QQQ TLT",
                    "title": row.get("title", "") or f"Congressional speech {len(docs) + 1}",
                    "source_url": "Congress speech sample",
                    "text": short(text, 4500),
                }
            )
            if len(docs) >= 90:
                break
    return docs


def extract_section(text: str, marker: str) -> str:
    lower = text.lower()
    start = lower.find(marker.lower())
    if start < 0:
        start = 0
    return short(text[start : start + 5200])


def build_sec_docs() -> list[dict]:
    docs: list[dict] = []
    for ticker, form, url, date in SEC_FILINGS:
        try:
            text = clean_html(fetch(url))
        except Exception as exc:
            print(f"warning: SEC fetch failed for {ticker}: {exc}", file=sys.stderr)
            continue
        docs.append(
            {
                "id": f"sec-{ticker.lower()}-risk",
                "date": date,
                "source_type": "Company filing",
                "speaker": "",
                "organization": ticker,
                "party": "",
                "ticker": ticker,
                "title": f"{ticker} {form} Risk Factors",
                "source_url": url,
                "text": extract_section(text, "risk factors"),
            }
        )
        docs.append(
            {
                "id": f"sec-{ticker.lower()}-mda",
                "date": date,
                "source_type": "Company filing",
                "speaker": "",
                "organization": ticker,
                "party": "",
                "ticker": ticker,
                "title": f"{ticker} {form} Management Discussion",
                "source_url": url,
                "text": extract_section(text, "management"),
            }
        )
        time.sleep(0.2)
    return docs


def title_from_text(text: str) -> str:
    for pattern in [r"Speech by [^.]{8,120}", r"Governor [^.]{8,120}", r"Vice Chair [^.]{8,120}"]:
        match = re.search(pattern, text)
        if match:
            return match.group(0).strip()
    return "Board of Governors of the Federal Reserve System"


def build_fed_docs() -> list[dict]:
    docs: list[dict] = []
    for index, url in enumerate(FED_SPEECHES, start=1):
        try:
            text = clean_html(fetch(url))
        except Exception as exc:
            print(f"warning: Fed fetch failed for {url}: {exc}", file=sys.stderr)
            continue
        date_match = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}", text)
        docs.append(
            {
                "id": f"fed-speech-{index:02d}",
                "date": date_match.group(0) if date_match else "",
                "source_type": "Federal Reserve",
                "speaker": "",
                "organization": "Federal Reserve",
                "party": "",
                "ticker": "TLT QQQ SPY",
                "title": title_from_text(text),
                "source_url": url,
                "text": short(text, 5200),
            }
        )
        time.sleep(0.2)
    return docs


def strip_namespace(tag: str) -> str:
    return tag.split("}", 1)[-1]


def item_child_text(item: ET.Element, name: str) -> str:
    for child in item:
        if strip_namespace(child.tag) == name:
            return "".join(child.itertext()).strip()
    return ""


def build_blog_docs(limit: int = 8) -> list[dict]:
    try:
        raw = fetch(NYFED_RSS)
    except Exception as exc:
        print(f"warning: NY Fed RSS fetch failed: {exc}", file=sys.stderr)
        return []
    root = ET.fromstring(raw)
    docs: list[dict] = []
    for item in root.iter():
        if strip_namespace(item.tag) != "item":
            continue
        title = item_child_text(item, "title")
        link = item_child_text(item, "link")
        date = item_child_text(item, "pubDate")
        description = clean_html(item_child_text(item, "description"))
        docs.append(
            {
                "id": f"nyfed-blog-{len(docs) + 1:02d}",
                "date": date,
                "source_type": "Research blog",
                "speaker": "",
                "organization": "Federal Reserve Bank of New York",
                "party": "",
                "ticker": "TLT SPY QQQ",
                "title": title,
                "source_url": link,
                "text": short(f"{title}. {description}", 4500),
            }
        )
        if len(docs) >= limit:
            break
    return docs


def schema_examples() -> list[dict]:
    return [
        {
            "id": "schema-executive-transcript",
            "date": "2026-05-12",
            "source_type": "Executive transcript",
            "speaker": "Example CEO",
            "organization": "User supplied company",
            "party": "",
            "ticker": "UPLOAD",
            "title": "Schema example for uploaded executive interview",
            "source_url": "Replace with uploaded transcript source",
            "text": "Paste or import executive interview text here. The app will score narratives around demand, margins, regulation, AI investment, supply chain exposure, and risk language.",
        },
        {
            "id": "schema-news",
            "date": "2026-05-12",
            "source_type": "News",
            "speaker": "",
            "organization": "User supplied news source",
            "party": "",
            "ticker": "UPLOAD",
            "title": "Schema example for imported market news",
            "source_url": "Replace with article URL when rights allow",
            "text": "Paste or import a news excerpt here. The project keeps redistribution limited and lets the user analyze text that they have permission to use.",
        },
    ]


def main() -> None:
    docs = []
    docs.extend(build_congress_docs())
    docs.extend(build_sec_docs())
    docs.extend(build_fed_docs())
    docs.extend(build_blog_docs())
    docs.extend(schema_examples())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(docs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(docs)} documents to {OUT}")


if __name__ == "__main__":
    main()
