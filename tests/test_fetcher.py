# -*- coding: utf-8 -*-
import requests
import pytest

from src.config import USER_AGENT
from src.fetcher import FetchError, NewsFetcher, check_robots


class FakeResponse:
    def __init__(self, status_code=200, text="<html>ok</html>", encoding="utf-8"):
        self.status_code = status_code
        self.text = text
        self.encoding = encoding
        self.apparent_encoding = "utf-8"

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}", response=self)


class SequenceSession:
    def __init__(self, items):
        self.items = list(items)
        self.calls = 0

    def get(self, *args, **kwargs):
        item = self.items[min(self.calls, len(self.items) - 1)]
        self.calls += 1
        if isinstance(item, Exception):
            raise item
        return item


def make_fetcher(items, retries=3, delay=0.0):
    return NewsFetcher(session=SequenceSession(items), retries=retries, delay=delay, sleep_fn=lambda _: None)


def test_retries_three_times_then_success():
    fetcher = make_fetcher([FakeResponse(503), FakeResponse(503), FakeResponse(503), FakeResponse(200)])
    result = fetcher.fetch("https://example.com/list")
    assert result.status == 200
    assert result.attempts == 4


def test_raises_fetch_error_after_all_retries():
    fetcher = make_fetcher([FakeResponse(500), FakeResponse(500), FakeResponse(500), FakeResponse(500)])
    with pytest.raises(FetchError):
        fetcher.fetch("https://example.com/list")


def test_timeout_is_retried():
    fetcher = make_fetcher([requests.Timeout(), requests.Timeout(), FakeResponse(200)], retries=2)
    result = fetcher.fetch("https://example.com/list")
    assert result.attempts == 3


def test_delay_is_applied_between_two_requests():
    sleeps = []
    fetcher = NewsFetcher(
        session=SequenceSession([FakeResponse(200), FakeResponse(200)]),
        retries=0,
        delay=2.0,
        sleep_fn=sleeps.append,
    )
    fetcher.fetch("https://example.com/a")
    fetcher.fetch("https://example.com/b")
    assert sleeps and sleeps[0] >= 1.9


def test_check_robots_disallow_rule():
    session = SequenceSession([FakeResponse(200, "User-agent: *\nDisallow: /private\n")])
    decision = check_robots("https://example.com/private/page", user_agent=USER_AGENT, session=session)
    assert decision.allowed is False
    assert "禁止" in decision.reason


def test_check_robots_404_means_allowed():
    session = SequenceSession([FakeResponse(404, "not found")])
    decision = check_robots("https://example.com/list", user_agent=USER_AGENT, session=session)
    assert decision.allowed is True
    assert decision.status == 404
