# -*- coding: utf-8 -*-
"""面向对象的爬虫编排：合规检查 → 请求 → 解析 → 持久化 → 质量校验。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .config import (
    DEFAULT_DELAY,
    DEFAULT_OUTPUT,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT,
    DEFAULT_URL,
    USER_AGENT,
)
from .fetcher import FetchResult, NewsFetcher, RobotsDecision, check_robots
from .parser import Article, parse_articles
from .storage import audit_articles, read_csv, write_csv


class RobotsDenied(RuntimeError):
    """robots.txt 明确禁止抓取。"""


@dataclass
class CrawlReport:
    url: str
    status: int
    encoding: str
    elapsed: float
    attempts: int
    total: int
    articles: list[Article]
    csv_path: Path
    warnings: list[str]
    robots_reason: str


class NewsCrawler:
    """把抓取流程封装成一个类，便于替换解析器、注入假 fetcher 做测试。"""

    def __init__(
        self,
        url: str = DEFAULT_URL,
        output_path: Path = DEFAULT_OUTPUT,
        delay: float = DEFAULT_DELAY,
        retries: int = DEFAULT_RETRIES,
        timeout: float = DEFAULT_TIMEOUT,
        limit: int | None = None,
        respect_robots: bool = True,
        fetcher: NewsFetcher | None = None,
        robots_checker: Callable[..., RobotsDecision] = check_robots,
    ) -> None:
        self.url = url
        self.output_path = Path(output_path)
        self.delay = delay
        self.retries = retries
        self.timeout = timeout
        self.limit = limit
        self.respect_robots = respect_robots
        self.fetcher = fetcher or NewsFetcher(timeout=timeout, retries=retries, delay=delay)
        self.robots_checker = robots_checker

    def run(self, verbose: bool = True) -> CrawlReport:
        robots_reason = "已跳过 robots.txt 检查"
        if self.respect_robots:
            decision = self.robots_checker(
                self.url,
                user_agent=USER_AGENT,
                session=self.fetcher.session,
                timeout=min(self.timeout, 10.0),
            )
            robots_reason = decision.reason
            if verbose:
                print("[1/5] 合规检查")
                print(f"  robots：{decision.reason}")
            if not decision.allowed:
                raise RobotsDenied(decision.reason)
        elif verbose:
            print("[1/5] 合规检查")
            print("  robots：已通过 --no-robots 显式跳过")

        if verbose:
            print("[2/5] 发送请求")
        result: FetchResult = self.fetcher.fetch(self.url)
        if verbose:
            print(f"  HTTP {result.status}，{len(result.html)} 字节，编码 {result.encoding}")
            print(f"  用时 {result.elapsed:.2f}s，尝试 {result.attempts} 次")

        if verbose:
            print("[3/5] 解析列表")
        articles = parse_articles(result.html, self.url, limit=self.limit)
        if verbose:
            print(f"  解析到 {len(articles)} 篇文章（已按链接去重）")
            for index, article in enumerate(articles[:3], start=1):
                print(
                    f"  {index}. {article.title[:48]} | "
                    f"{article.published or '日期缺失'} | "
                    f"{article.author or '作者缺失'}"
                )

        if verbose:
            print("[4/5] 写入 CSV")
        csv_path = write_csv(articles, self.output_path)
        if verbose:
            print(f"  文件：{csv_path}")

        warnings = audit_articles(articles)
        if verbose:
            print("[5/5] 质量校验")
            back = read_csv(csv_path)
            print(f"  回读：{len(back)} 行，列名 {'/'.join(back.columns)}")
            if warnings:
                for warning in warnings:
                    print(f"  ! {warning}")
            else:
                print("  未发现空字段或重复链接")

        if verbose:
            print("-" * 68)
            print(f"完成：成功抓取 {len(articles)} 条 → {csv_path}")

        return CrawlReport(
            url=self.url,
            status=result.status,
            encoding=result.encoding,
            elapsed=result.elapsed,
            attempts=result.attempts,
            total=len(articles),
            articles=articles,
            csv_path=csv_path,
            warnings=warnings,
            robots_reason=robots_reason,
        )
