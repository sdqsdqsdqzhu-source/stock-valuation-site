from __future__ import annotations

import json
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.sync_reddit_cache import CACHE_PATH, collect_ticker, read_cache  # noqa: E402
from server import build_reddit_attention_payload  # noqa: E402


PORT = 8788


def save_record(ticker: str, record: dict) -> None:
    cache = read_cache()
    records = cache.setdefault("records", {})
    records[ticker.upper()] = record
    cache["updated_at"] = record.get("cached_at")
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


class Handler(BaseHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path not in ("/api/reddit", "/reddit"):
            self.send_json({"ok": True, "service": "local Reddit bridge", "endpoint": "/api/reddit?ticker=NVDA"})
            return
        ticker = urllib.parse.parse_qs(parsed.query).get("ticker", [""])[0].upper().strip()
        if not ticker:
            self.send_json({"error": "ticker is required"}, status=400)
            return
        try:
            record = collect_ticker(ticker)
            if record.get("successful_subreddits", 0) > 0:
                save_record(ticker, record)
                payload = build_reddit_attention_payload(
                    record.get("posts") or [],
                    f"Local live Reddit bridge / 本地实时Reddit桥接 ({record.get('cached_at')})",
                    record.get("successful_subreddits", 0),
                    record.get("errors") or [],
                    {"cached": False, "cached_at": record.get("cached_at"), "local_bridge": True},
                )
                self.send_json(payload)
                return
            self.send_json({
                "connected": False,
                "source": "Local Reddit bridge unavailable / 本地Reddit桥接不可用",
                "posts": None,
                "top_posts": [],
                "daily": [],
                "error": "; ".join(record.get("errors") or []) or "No successful subreddit requests",
            }, status=502)
        except Exception as exc:
            self.send_json({"connected": False, "error": str(exc)}, status=500)

    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        print(fmt % args)


def main() -> int:
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Local Reddit bridge running at http://127.0.0.1:{PORT}")
    print("Keep this window open while using the Vercel site.")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
