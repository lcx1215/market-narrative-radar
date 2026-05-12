#!/usr/bin/env python3
"""Fetch a small live corpus from free public sources.

This script is separate from the static demo corpus. It gives the open-source
project a real ingestion lane that can be expanded without changing the UI.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "live_corpus.json"
USER_AGENT = "market-narrative-radar open-source research app contact@example.com"


def fetch(url: str, accept: str = "application/json,text/html,*/*") -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def clean_html(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
    raw = re.sub(r"(?is)<br\s*/?>|</p>", "\n", raw)
    raw = re.sub(r"(?is)<.*?>", " ", raw)
    raw = html.unescape(raw)
    return re.sub(r"\s+", " ", raw).strip()


def gdelt_docs(query: str, limit: int) -> list[dict]:
    safe_query = re.sub(r"\bAI\b", '"artificial intelligence"', query, flags=re.I)
    params = urllib.parse.urlencode(
        {
            "query": safe_query,
            "mode": "ArtList",
            "format": "json",
            "maxrecords": limit,
            "sort": "HybridRel",
        }
    )
    url = f"https://api.gdeltproject.org/api/v2/doc/doc?{params}"
    raw = fetch(url)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        raise RuntimeError(f"GDELT returned non-JSON response: {raw[:160]}")
    docs = []
    for index, article in enumerate(payload.get("articles", []), start=1):
        title = article.get("title", "")
        docs.append(
            {
                "id": f"gdelt-{index:03d}",
                "date": article.get("seendate", ""),
                "source_type": "News",
                "speaker": "",
                "organization": article.get("domain", ""),
                "party": "",
                "ticker": "",
                "title": title,
                "source_url": article.get("url", ""),
                "text": f"{title}. {article.get('domain', '')}. {article.get('language', '')}",
            }
        )
    return docs


def collect(name: str, fn) -> list[dict]:
    try:
        docs = fn()
        print(f"{name}: {len(docs)} documents")
        return docs
    except Exception as exc:
        print(f"warning: {name} failed: {exc}")
        return []


def federal_register_docs(query: str, limit: int) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "conditions[term]": query,
            "per_page": limit,
            "order": "newest",
            "fields[]": [
                "document_number",
                "publication_date",
                "title",
                "html_url",
                "abstract",
                "agency_names",
            ],
        },
        doseq=True,
    )
    url = f"https://www.federalregister.gov/api/v1/documents.json?{params}"
    payload = json.loads(fetch(url))
    docs = []
    for item in payload.get("results", []):
        agencies = ", ".join(item.get("agency_names", []) or [])
        docs.append(
            {
                "id": f"federal-register-{item.get('document_number', len(docs) + 1)}",
                "date": item.get("publication_date", ""),
                "source_type": "Federal Register",
                "speaker": "",
                "organization": agencies,
                "party": "",
                "ticker": "",
                "title": item.get("title", ""),
                "source_url": item.get("html_url", ""),
                "text": clean_html(f"{item.get('title', '')}. {item.get('abstract', '')}. {agencies}"),
            }
        )
    return docs


def fed_rss_docs(limit: int) -> list[dict]:
    url = "https://www.federalreserve.gov/feeds/speeches.xml"
    raw = fetch(url, "application/rss+xml,application/xml,*/*")
    root = ET.fromstring(raw)
    docs = []
    for item in root.iter():
        if not item.tag.lower().endswith("item"):
            continue
        fields = {child.tag.split("}", 1)[-1]: "".join(child.itertext()).strip() for child in item}
        docs.append(
            {
                "id": f"fed-rss-{len(docs) + 1:03d}",
                "date": fields.get("pubDate", ""),
                "source_type": "Federal Reserve",
                "speaker": "",
                "organization": "Federal Reserve",
                "party": "",
                "ticker": "TLT SPY QQQ",
                "title": fields.get("title", ""),
                "source_url": fields.get("link", ""),
                "text": clean_html(f"{fields.get('title', '')}. {fields.get('description', '')}"),
            }
        )
        if len(docs) >= limit:
            break
    return docs


def sec_latest_docs(cik: str, limit: int) -> list[dict]:
    cik_padded = str(cik).zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    payload = json.loads(fetch(url))
    recent = payload.get("filings", {}).get("recent", {})
    docs = []
    for index, form in enumerate(recent.get("form", [])):
        if form not in {"10-K", "10-Q", "8-K"}:
            continue
        accession = recent["accessionNumber"][index]
        primary = recent["primaryDocument"][index]
        archive = accession.replace("-", "")
        docs.append(
            {
                "id": f"sec-{cik}-{accession}",
                "date": recent["filingDate"][index],
                "source_type": "Company filing",
                "speaker": "",
                "organization": payload.get("name", ""),
                "party": "",
                "ticker": payload.get("tickers", [""])[0] if payload.get("tickers") else "",
                "title": f"{payload.get('name', 'Company')} {form}",
                "source_url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{archive}/{primary}",
                "text": f"{payload.get('name', 'Company')} filed {form} on {recent['filingDate'][index]}. Accession {accession}.",
            }
        )
        if len(docs) >= limit:
            break
    return docs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="AI semiconductor tariff rates regulation")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--sec-cik", default="1045810", help="Default is NVIDIA.")
    args = parser.parse_args()

    docs = []
    docs.extend(collect("GDELT", lambda: gdelt_docs(args.query, args.limit)))
    docs.extend(collect("Federal Register", lambda: federal_register_docs(args.query, args.limit)))
    docs.extend(collect("Federal Reserve RSS", lambda: fed_rss_docs(args.limit)))
    docs.extend(collect("SEC EDGAR", lambda: sec_latest_docs(args.sec_cik, args.limit)))

    OUT.write_text(json.dumps(docs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(docs)} live documents to {OUT}")


if __name__ == "__main__":
    main()
