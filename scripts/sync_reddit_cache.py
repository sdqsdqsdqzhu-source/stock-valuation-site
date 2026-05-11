from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
CACHE_PATH = PUBLIC / "data" / "reddit_cache.json"
SUBREDDITS = [
    "wallstreetbets",
    "stocks",
    "investing",
    "StockMarket",
    "options",
    "SecurityAnalysis",
    "ValueInvesting",
    "pennystocks",
]
DEFAULT_TICKERS = [
    "NVDA",
    "AAPL",
    "MSFT",
    "GOOG",
    "GOOGL",
    "META",
    "AMZN",
    "TSLA",
    "AMD",
    "INTC",
    "MU",
    "SNDK",
    "SOFI",
    "NMM",
]
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def read_cache() -> dict:
    if not CACHE_PATH.exists():
        return {"updated_at": None, "records": {}}
    try:
        data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("records"), dict):
            return data
    except Exception:
        pass
    return {"updated_at": None, "records": {}}


def fetch_json(url: str) -> tuple[dict | None, str | None]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            return json.loads(response.read().decode("utf-8")), None
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code}"
    except Exception as exc:
        return None, exc.__class__.__name__


def collect_ticker(ticker: str) -> dict:
    ticker = ticker.upper().strip()
    pattern = re.compile(rf"(?<![A-Z0-9])\$?{re.escape(ticker)}(?![A-Z0-9])")
    posts = []
    errors = []
    successful = 0
    for subreddit in SUBREDDITS:
        params = urllib.parse.urlencode({
            "q": ticker,
            "restrict_sr": 1,
            "sort": "new",
            "t": "week",
            "limit": 25,
        })
        payload, error = fetch_json(f"https://www.reddit.com/r/{subreddit}/search.json?{params}")
        if error:
            errors.append(f"r/{subreddit} {error}")
            continue
        successful += 1
        for child in payload.get("data", {}).get("children", []) or []:
            item = child.get("data", {}) or {}
            title = str(item.get("title") or "")
            text = str(item.get("selftext") or "")
            if not pattern.search(f"{title}\n{text}".upper()):
                continue
            created = float(item.get("created_utc") or 0)
            posts.append({
                "subreddit": item.get("subreddit_name_prefixed") or f"r/{subreddit}",
                "title": title[:180],
                "url": f"https://www.reddit.com{item.get('permalink', '')}",
                "score": round(float(item.get("score") or 0)),
                "comments": round(float(item.get("num_comments") or 0)),
                "upvote_ratio": float(item.get("upvote_ratio") or 0),
                "created_utc": created,
                "created": time.strftime("%Y-%m-%d", time.gmtime(created)) if created else "",
            })
    return {
        "cached_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "Local public Reddit JSON / 本地公开Reddit JSON",
        "successful_subreddits": successful,
        "searched_subreddits": SUBREDDITS,
        "posts": posts,
        "errors": errors[:8],
    }


def run_git(args: list[str]) -> None:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Reddit public search locally and save a Vercel-readable cache.")
    parser.add_argument("tickers", nargs="*", help="Tickers to refresh. Defaults to a core watchlist.")
    parser.add_argument("--commit", action="store_true", help="Commit public/data/reddit_cache.json after refresh.")
    parser.add_argument("--push", action="store_true", help="Push the commit to origin main after refresh.")
    args = parser.parse_args()

    tickers = [item.upper() for item in (args.tickers or DEFAULT_TICKERS)]
    cache = read_cache()
    records = cache.setdefault("records", {})
    for ticker in tickers:
        record = collect_ticker(ticker)
        if record["successful_subreddits"] > 0:
            records[ticker] = record
            print(f"{ticker}: {len(record['posts'])} posts from {record['successful_subreddits']}/{len(SUBREDDITS)} subreddits")
        else:
            print(f"{ticker}: no live Reddit access; existing cache kept")
    cache["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved {CACHE_PATH}")

    if args.commit or args.push:
        run_git(["git", "add", str(CACHE_PATH.relative_to(ROOT))])
        run_git(["git", "commit", "-m", "Update Reddit cache"])
        print("committed Reddit cache")
    if args.push:
        run_git(["git", "push", "origin", "main"])
        print("pushed to origin main")
    return 0


if __name__ == "__main__":
    sys.exit(main())
