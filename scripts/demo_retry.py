# -*- coding: utf-8 -*-
"""用真实 HTTP 响应演示“失败重试 3 次后成功”。"""
from __future__ import annotations

import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.fetcher import FetchError, NewsFetcher

COUNT = {"value": 0}
BODY = (
    "<html><body><article class=\"post-card\">"
    "<a href=\"/ok\"><h3>Retry succeeded</h3></a>"
    "<div class=\"meta\"><span>Tester</span>"
    "<time datetime=\"2026-11-18\">2026-11-18</time></div>"
    "</article></body></html>"
)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/flaky":
            self.send_response(404)
            self.end_headers()
            return
        COUNT["value"] += 1
        if COUNT["value"] <= 3:
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b"temporary failure")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(BODY.encode("utf-8"))

    def log_message(self, format, *args):
        return


def main() -> int:
    server = ThreadingHTTPServer(("127.0.0.1", 8766), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print("[demo] /flaky 前 3 次返回 503，第 4 次返回 200")
    fetcher = NewsFetcher(retries=3, delay=2.0)
    try:
        result = fetcher.fetch("http://127.0.0.1:8766/flaky")
        print(f"[demo] 最终 HTTP {result.status}，共尝试 {result.attempts} 次，耗时 {result.elapsed:.2f}s")
        print("[demo] 重试策略验证通过")
        return 0
    except FetchError as exc:
        print(f"[demo] {exc}")
        return 1
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
