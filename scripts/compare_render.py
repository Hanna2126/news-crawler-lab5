# -*- coding: utf-8 -*-
"""对比两种方案抓取动态渲染页面的效果与耗时。"""
from __future__ import annotations

import sys
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import HEADERS  # noqa: E402
from src.parser import parse_articles  # noqa: E402

SITE = ROOT / "site"
PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return


def timed_static(page: str) -> tuple[int, float]:
    started = time.perf_counter()
    response = requests.get(f"{BASE}/{page}", headers=HEADERS, timeout=10)
    response.raise_for_status()
    articles = parse_articles(response.text, f"{BASE}/{page}")
    return len(articles), time.perf_counter() - started


def main() -> int:
    handler = partial(QuietHandler, directory=str(SITE))
    server = ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"[compare] 本地站点 {BASE}")

    try:
        static_count, static_time = timed_static("index.html")
        dynamic_static_count, dynamic_static_time = timed_static("dynamic.html")

        try:
            from src.dynamic import render_page
            html, render_time = render_page(f"{BASE}/dynamic.html")
            dynamic_count = len(parse_articles(html, f"{BASE}/dynamic.html"))
        except Exception as exc:
            print(f"[compare] Selenium 渲染失败：{type(exc).__name__}: {exc}")
            return 2

        print("-" * 78)
        print(f"{'方案':<28}{'请求方式':<20}{'条数':>6}{'耗时':>12}")
        print("-" * 78)
        print(f"{'静态页 requests+BS4':<28}{'单次 HTTP GET':<20}{static_count:>6}{static_time:>11.3f}s")
        print(f"{'动态页 requests+BS4':<28}{'单次 HTTP GET':<20}{dynamic_static_count:>6}{dynamic_static_time:>11.3f}s")
        print(f"{'动态页 Selenium+BS4':<28}{'浏览器渲染后取源码':<20}{dynamic_count:>6}{render_time:>11.3f}s")
        print("-" * 78)
        print("结论：静态请求快但看不到 JS 注入的数据；浏览器渲染能拿到数据，但多出浏览器启动的秒级固定开销。")
        print(f"      动态方案总耗时约为静态方案的 {render_time / max(static_time, 0.001):.1f} 倍。")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
