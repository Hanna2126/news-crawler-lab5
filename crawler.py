# -*- coding: utf-8 -*-
"""新闻列表爬虫入口：合规检查、请求、解析、CSV 落盘与质量校验。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.config import (
    DEFAULT_DELAY,
    DEFAULT_OUTPUT,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT,
    DEFAULT_URL,
    USER_AGENT,
)
from src.crawler import NewsCrawler, RobotsDenied
from src.fetcher import FetchError

LINE = "=" * 68


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="静态新闻列表页爬虫（requests + BeautifulSoup）")
    parser.add_argument("--url", default=DEFAULT_URL, help="列表页 URL")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="CSV 输出路径")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help="请求间隔秒数，不得低于 2")
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES, help="失败重试次数")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="单次请求超时秒数")
    parser.add_argument("--limit", type=int, default=None, help="最多保留多少条，默认全部")
    parser.add_argument("--no-robots", action="store_true", help="跳过 robots.txt 检查（不推荐）")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.delay < 2.0:
        parser.error("请求间隔不得低于 2 秒，这是本实验的合规约束")

    print(LINE)
    print("新闻列表爬虫 | requests + BeautifulSoup")
    print(f"目标：{args.url}")
    print(f"UA：{USER_AGENT[:88]}...")
    print(LINE)

    crawler = NewsCrawler(
        url=args.url,
        output_path=Path(args.output),
        delay=args.delay,
        retries=args.retries,
        timeout=args.timeout,
        limit=args.limit,
        respect_robots=not args.no_robots,
    )
    try:
        crawler.run()
    except RobotsDenied as exc:
        print(f"[拒绝] {exc}")
        return 2
    except FetchError as exc:
        print(f"[错误] {exc}")
        return 1
    except KeyboardInterrupt:
        print("\n[中断] 用户终止抓取")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
