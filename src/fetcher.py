# -*- coding: utf-8 -*-
"""HTTP 抓取层：UA、限速、超时重试与 robots.txt 合规检查。"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import requests

from .config import HEADERS, RETRY_STATUS, USER_AGENT


class FetchError(RuntimeError):
    """请求最终失败时抛出，由 CLI 统一收敛为友好提示。"""


@dataclass
class RobotsDecision:
    allowed: bool
    reason: str
    status: int | None = None


@dataclass
class FetchResult:
    url: str
    status: int
    html: str
    elapsed: float
    attempts: int
    encoding: str


def check_robots(
    url: str,
    user_agent: str = USER_AGENT,
    session: requests.Session | None = None,
    timeout: float = 10.0,
) -> RobotsDecision:
    """读取 robots.txt 并判断当前 URL 是否允许抓取。

    404 表示站点未提供 robots.txt；按 RFC 9309 的约定视为不限制。
    网络异常时同样按“无法读取规则”处理，但会在报告中标注原因。
    """
    parsed = urlparse(url)
    robots_url = urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))
    own_session = session or requests.Session()
    try:
        response = own_session.get(
            robots_url,
            headers={"User-Agent": user_agent},
            timeout=timeout,
        )
    except requests.RequestException as exc:
        return RobotsDecision(True, f"robots.txt 无法获取（{type(exc).__name__}），按无限制处理")

    if response.status_code == 404:
        return RobotsDecision(True, "robots.txt 不存在（404），按无限制处理", 404)
    if response.status_code >= 400:
        return RobotsDecision(
            True,
            f"robots.txt 返回 HTTP {response.status_code}，无法读取规则，按无限制处理",
            response.status_code,
        )

    parser = RobotFileParser()
    parser.parse(response.text.splitlines())
    allowed = parser.can_fetch(user_agent, url)
    reason = "robots.txt 允许抓取" if allowed else "robots.txt 明确禁止该路径"
    return RobotsDecision(allowed, reason, response.status_code)


class NewsFetcher:
    """带限速与重试的 GET 抓取器，可注入 session / sleep 便于测试。"""

    def __init__(
        self,
        session: requests.Session | None = None,
        timeout: float = 15.0,
        retries: int = 3,
        delay: float = 2.0,
        headers: dict[str, str] | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout
        self.retries = max(0, int(retries))
        self.delay = max(0.0, float(delay))
        self.headers = dict(HEADERS if headers is None else headers)
        self.sleep_fn = sleep_fn
        self._last_request_at: float | None = None

    def _respect_delay(self) -> None:
        if self._last_request_at is None or self.delay <= 0:
            return
        remaining = self.delay - (time.monotonic() - self._last_request_at)
        if remaining > 0:
            self.sleep_fn(round(remaining, 2))

    def fetch(self, url: str) -> FetchResult:
        """GET 一个页面；可重试状态码与超时最多重试 self.retries 次。"""
        attempts = 0
        started = time.perf_counter()
        last_error: Exception | None = None

        while attempts <= self.retries:
            self._respect_delay()
            attempts += 1
            try:
                response = self.session.get(url, headers=self.headers, timeout=self.timeout)
                self._last_request_at = time.monotonic()

                if response.status_code in RETRY_STATUS:
                    if attempts <= self.retries:
                        print(
                            f"  [retry] HTTP {response.status_code}，"
                            f"第 {attempts} 次失败，{self.delay:g}s 后重试"
                        )
                        continue
                    raise FetchError(f"HTTP {response.status_code}，重试 {self.retries} 次后仍失败")

                response.raise_for_status()
                if not response.encoding or response.encoding.lower() == "iso-8859-1":
                    response.encoding = response.apparent_encoding or "utf-8"
                return FetchResult(
                    url=url,
                    status=response.status_code,
                    html=response.text,
                    elapsed=time.perf_counter() - started,
                    attempts=attempts,
                    encoding=response.encoding or "utf-8",
                )
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_error = exc
                if attempts <= self.retries:
                    print(
                        f"  [retry] {type(exc).__name__}，"
                        f"第 {attempts} 次失败，{self.delay:g}s 后重试"
                    )
                    continue
                raise FetchError(
                    f"网络请求失败（{type(exc).__name__}），已尝试 {attempts} 次：{exc}"
                ) from exc
            except requests.HTTPError as exc:
                raise FetchError(f"HTTP {response.status_code}：{exc}") from exc
            except requests.RequestException as exc:
                raise FetchError(f"请求异常（{type(exc).__name__}）：{exc}") from exc

        raise FetchError(f"请求失败，已尝试 {attempts} 次：{last_error}")
