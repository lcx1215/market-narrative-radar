#!/usr/bin/env python3
"""Live public-source relay for Market Narrative Radar.

Browsers cannot reliably call every public data source directly. SEC also
documents that data.sec.gov does not support CORS, so live fetching should go
through a small backend relay. This server uses public no-key sources by
default and keeps any optional API keys in environment variables.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer
from html import unescape


USER_AGENT = os.environ.get(
    "MNR_USER_AGENT",
    "market-narrative-radar open-source research app contact@example.com",
)
DEFAULT_CIKS = {
    "NVDA": "0001045810",
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "GOOGL": "0001652044",
    "AMZN": "0001018724",
    "META": "0001326801",
    "TSLA": "0001318605",
}
CACHE_TTL_SECONDS = int(os.environ.get("MNR_DATA_CACHE_TTL_SECONDS", "300"))
LIVE_CACHE: dict[str, tuple[float, dict]] = {}


def fetch(url: str, accept: str = "application/json,text/html,application/xml,*/*") -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": accept,
            "Accept-Encoding": "identity",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def clean_html(value: str) -> str:
    value = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", value)
    value = re.sub(r"(?is)<br\s*/?>|</p>", "\n", value)
    value = re.sub(r"(?is)<.*?>", " ", value)
    return re.sub(r"\s+", " ", unescape(value)).strip()


def safe_query(query: str) -> str:
    return re.sub(r"\bAI\b", '"artificial intelligence"', query, flags=re.I)


def gdelt(query: str, limit: int) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "query": safe_query(query),
            "mode": "ArtList",
            "format": "json",
            "maxrecords": limit,
            "sort": "HybridRel",
            "timespan": "1month",
        }
    )
    raw = fetch(f"https://api.gdeltproject.org/api/v2/doc/doc?{params}")
    payload = json.loads(raw)
    docs = []
    for index, item in enumerate(payload.get("articles", []), start=1):
        title = item.get("title", "")
        docs.append(
            {
                "id": f"live-gdelt-{index:03d}",
                "date": item.get("seendate", ""),
                "source_type": "News",
                "speaker": "",
                "organization": item.get("domain", ""),
                "party": "",
                "ticker": "",
                "title": title,
                "source_url": item.get("url", ""),
                "text": f"{title}. Source domain: {item.get('domain', '')}. Language: {item.get('language', '')}.",
            }
        )
    return docs


def federal_register(query: str, limit: int) -> list[dict]:
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
    payload = json.loads(fetch(f"https://www.federalregister.gov/api/v1/documents.json?{params}"))
    docs = []
    for item in payload.get("results", []):
        agencies = ", ".join(item.get("agency_names") or [])
        docs.append(
            {
                "id": f"live-fr-{item.get('document_number', len(docs) + 1)}",
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


def fed_rss(limit: int) -> list[dict]:
    raw = fetch("https://www.federalreserve.gov/feeds/speeches.xml", "application/rss+xml,application/xml,*/*")
    root = ET.fromstring(raw)
    docs = []
    for item in root.iter():
        if not item.tag.lower().endswith("item"):
            continue
        fields = {child.tag.split("}", 1)[-1]: "".join(child.itertext()).strip() for child in item}
        docs.append(
            {
                "id": f"live-fed-{len(docs) + 1:03d}",
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


def rss_feed(name: str, url: str, source_type: str, organization: str, ticker: str, limit: int) -> list[dict]:
    raw = fetch(url, "application/rss+xml,application/xml,*/*")
    root = ET.fromstring(raw)
    docs = []
    for item in root.iter():
        if not item.tag.lower().endswith("item"):
            continue
        fields = {child.tag.split("}", 1)[-1]: "".join(child.itertext()).strip() for child in item}
        title = fields.get("title", "")
        description = clean_html(fields.get("description", ""))
        docs.append(
            {
                "id": f"live-{name.lower().replace(' ', '-')}-{len(docs) + 1:03d}",
                "date": fields.get("pubDate", "") or fields.get("date", ""),
                "source_type": source_type,
                "speaker": "",
                "organization": organization,
                "party": "",
                "ticker": ticker,
                "title": title,
                "source_url": fields.get("link", ""),
                "text": clean_html(f"{title}. {description}"),
            }
        )
        if len(docs) >= limit:
            break
    return docs


def nyfed_blog(limit: int) -> list[dict]:
    return rss_feed(
        "NY Fed Blog",
        "https://libertystreeteconomics.newyorkfed.org/feed/",
        "Research blog",
        "Federal Reserve Bank of New York",
        "TLT SPY QQQ",
        limit,
    )


def ftc_competition(limit: int) -> list[dict]:
    return rss_feed(
        "FTC Competition",
        "https://www.ftc.gov/feeds/press-release-competition.xml",
        "Regulator",
        "Federal Trade Commission",
        "SPY QQQ",
        limit,
    )


def doj_antitrust(limit: int) -> list[dict]:
    return rss_feed(
        "DOJ Antitrust",
        "https://www.justice.gov/news/rss?type%5B0%5D=image_gallery&type%5B1%5D=press_release&type%5B2%5D=speech&type%5B3%5D=youtube_video&field_component=376&search_api_language=en&show_public_archived=0&require_all=0",
        "Regulator",
        "U.S. Department of Justice Antitrust Division",
        "SPY QQQ",
        limit,
    )


def cftc(limit: int) -> list[dict]:
    return rss_feed(
        "CFTC",
        "https://www.cftc.gov/RSS/RSSGP/rssgp.xml",
        "Regulator",
        "Commodity Futures Trading Commission",
        "SPY TLT",
        limit,
    )


def sec_latest(limit: int) -> list[dict]:
    docs = []
    for ticker, cik in list(DEFAULT_CIKS.items())[: max(1, min(limit, len(DEFAULT_CIKS)))]:
        payload = json.loads(fetch(f"https://data.sec.gov/submissions/CIK{cik}.json"))
        recent = payload.get("filings", {}).get("recent", {})
        for index, form in enumerate(recent.get("form", [])):
            if form not in {"10-K", "10-Q", "8-K"}:
                continue
            accession = recent["accessionNumber"][index]
            archive = accession.replace("-", "")
            primary = recent["primaryDocument"][index]
            docs.append(
                {
                    "id": f"live-sec-{ticker.lower()}-{accession}",
                    "date": recent["filingDate"][index],
                    "source_type": "Company filing",
                    "speaker": "",
                    "organization": payload.get("name", ticker),
                    "party": "",
                    "ticker": ticker,
                    "title": f"{ticker} {form}",
                    "source_url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{archive}/{primary}",
                    "text": f"{ticker} filed {form} on {recent['filingDate'][index]}. Accession {accession}. This filing can be opened from the SEC archive link.",
                }
            )
            break
    return docs


def congress(query: str, limit: int) -> list[dict]:
    key = os.environ.get("CONGRESS_API_KEY")
    if not key:
        return []
    params = urllib.parse.urlencode({"query": query, "limit": limit, "api_key": key, "format": "json"})
    payload = json.loads(fetch(f"https://api.congress.gov/v3/bill?{params}"))
    docs = []
    for item in payload.get("bills", []):
        title = item.get("title", "")
        docs.append(
            {
                "id": f"live-congress-{item.get('congress', '')}-{item.get('type', '')}-{item.get('number', '')}",
                "date": item.get("updateDate", ""),
                "source_type": "Congress.gov",
                "speaker": "",
                "organization": "U.S. Congress",
                "party": "",
                "ticker": "SPY QQQ TLT",
                "title": title,
                "source_url": item.get("url", ""),
                "text": title,
            }
        )
    return docs


def collect(name: str, fn) -> tuple[list[dict], dict]:
    try:
        docs = fn()
        return docs, {"source": name, "ok": True, "count": len(docs)}
    except Exception as exc:
        return [], {"source": name, "ok": False, "error": str(exc)}


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path not in {"/api/live-sources", "/api/health"}:
            self.send_error(404)
            return
        params = urllib.parse.parse_qs(parsed.query)
        query = params.get("query", ["artificial intelligence semiconductor tariff regulation manufacturing"])[0]
        limit = max(1, min(25, int(params.get("limit", ["8"])[0])))
        if parsed.path == "/api/health":
            body = {
                "ok": True,
                "cache_ttl_seconds": CACHE_TTL_SECONDS,
                "cache_entries": len(LIVE_CACHE),
                "sources": ["SEC EDGAR", "GDELT", "Federal Register", "Federal Reserve RSS", "Congress.gov optional"],
            }
        else:
            cache_key = json.dumps({"query": query, "limit": limit}, sort_keys=True)
            cached = LIVE_CACHE.get(cache_key)
            if cached and time.time() - cached[0] < CACHE_TTL_SECONDS:
                body = {**cached[1], "cached": True}
                payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                try:
                    self.wfile.write(payload)
                except BrokenPipeError:
                    return
                return
            docs = []
            health = []
            for name, fn in [
                ("SEC EDGAR", lambda: sec_latest(min(5, limit))),
                ("Federal Register", lambda: federal_register(query, limit)),
                ("Federal Reserve RSS", lambda: fed_rss(limit)),
                ("NY Fed Blog", lambda: nyfed_blog(limit)),
                ("FTC Competition", lambda: ftc_competition(limit)),
                ("DOJ Antitrust", lambda: doj_antitrust(limit)),
                ("CFTC", lambda: cftc(limit)),
                ("GDELT", lambda: gdelt(query, limit)),
                ("Congress.gov", lambda: congress(query, limit)),
            ]:
                source_docs, status = collect(name, fn)
                docs.extend(source_docs)
                health.append(status)
            body = {
                "documents": docs,
                "sources": [item["source"] for item in health if item.get("ok")],
                "health": health,
                "query": query,
                "cached": False,
            }
            LIVE_CACHE[cache_key] = (time.time(), body)
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        try:
            self.wfile.write(payload)
        except BrokenPipeError:
            return


def main() -> None:
    port = int(os.environ.get("MNR_DATA_PORT", "8790"))
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"Data relay listening on http://127.0.0.1:{port}/api/live-sources")
    server.serve_forever()


if __name__ == "__main__":
    main()
