#!/usr/bin/env python3
"""
Pulls every RSS feed in feeds.json, merges new items into data/items.json,
and drops anything older than MAX_ITEMS so the file doesn't grow forever.

Run manually with:  python fetch_feeds.py
In production this is called on a schedule by .github/workflows/fetch.yml
"""
import json
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path

import feedparser

ROOT = Path(__file__).parent
FEEDS_FILE = ROOT / "feeds.json"
DATA_FILE = ROOT / "data" / "items.json"
MAX_ITEMS = 800          # total items kept across all sources
REQUEST_TIMEOUT = 20     # seconds, per feed


def item_id(link: str, title: str) -> str:
    """Stable id so we can dedupe across runs even if a feed re-orders entries."""
    return hashlib.sha1(f"{link}|{title}".encode("utf-8")).hexdigest()[:16]


def parse_published(entry) -> str:
    """Best-effort published time as ISO 8601 UTC. Falls back to now."""
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc).isoformat()
    return datetime.now(timezone.utc).isoformat()


def fetch_one(source: dict) -> list[dict]:
    items = []
    try:
        parsed = feedparser.parse(source["url"])
    except Exception as e:
        print(f"[error] {source['name']}: {e}")
        return items

    if parsed.bozo and not parsed.entries:
        print(f"[warn] {source['name']}: feed did not parse cleanly, 0 entries")
        return items

    for entry in parsed.entries:
        link = entry.get("link", "")
        title = entry.get("title", "(untitled)").strip()
        if not link:
            continue
        items.append({
            "id": item_id(link, title),
            "title": title,
            "link": link,
            "source": source["name"],
            "category": source["category"],
            "published": parse_published(entry),
            "summary": (entry.get("summary", "") or "")[:400],
        })
    return items


def load_existing() -> dict:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return {"updated_at": None, "items": []}


def main():
    with open(FEEDS_FILE) as f:
        config = json.load(f)

    existing = load_existing()
    by_id = {item["id"]: item for item in existing["items"]}

    new_count = 0
    for source in config["rss_sources"]:
        fetched = fetch_one(source)
        for item in fetched:
            if item["id"] not in by_id:
                new_count += 1
            by_id[item["id"]] = item  # overwrite = picks up edits too
        print(f"[ok] {source['name']}: {len(fetched)} entries seen")

    merged = sorted(by_id.values(), key=lambda x: x["published"], reverse=True)[:MAX_ITEMS]

    DATA_FILE.parent.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps({
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "items": merged,
    }, ensure_ascii=False, indent=2))

    print(f"\n{new_count} new item(s) this run. {len(merged)} total stored.")


if __name__ == "__main__":
    main()
