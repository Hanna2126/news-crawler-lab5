# -*- coding: utf-8 -*-
"""启动本地演示站点，供静态/动态抓取对比使用。"""
from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parents[1] / "site"


def main() -> None:
    parser = argparse.ArgumentParser(description="本地演示站点")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    handler = partial(SimpleHTTPRequestHandler, directory=str(SITE_DIR))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"[serve] http://127.0.0.1:{args.port}/  (Ctrl+C 停止)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[serve] 已停止")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
