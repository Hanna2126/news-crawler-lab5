# -*- coding: utf-8 -*-
from pathlib import Path

import pytest

from src.crawler import NewsCrawler, RobotsDenied
from src.fetcher import FetchResult, RobotsDecision
from src.storage import read_csv

FIXTURE = Path(__file__).parent / "fixtures" / "list_page.html"


class FakeFetcher:
    def __init__(self, html: str):
        self.html = html
        self.session = object()

    def fetch(self, url: str) -> FetchResult:
        return FetchResult(url=url, status=200, html=self.html, elapsed=0.01, attempts=1, encoding="utf-8")


def allow_all(*args, **kwargs):
    return RobotsDecision(True, "测试放行", 200)


def deny_all(*args, **kwargs):
    return RobotsDecision(False, "测试禁止", 200)


def make_crawler(tmp_path, limit=None, robots_checker=allow_all):
    return NewsCrawler(
        url="https://blog.python.org/",
        output_path=tmp_path / "result.csv",
        limit=limit,
        fetcher=FakeFetcher(FIXTURE.read_text(encoding="utf-8")),
        robots_checker=robots_checker,
    )


def test_end_to_end_creates_csv(tmp_path, capsys):
    report = make_crawler(tmp_path).run(verbose=True)
    assert report.total == 4
    assert report.csv_path.exists()
    frame = read_csv(report.csv_path)
    assert len(frame) == 4
    output = capsys.readouterr().out
    assert "[1/5]" in output and "[5/5]" in output


def test_limit_is_respected(tmp_path):
    report = make_crawler(tmp_path, limit=2).run(verbose=False)
    assert report.total == 2
    assert len(read_csv(report.csv_path)) == 2


def test_robots_denied_raises(tmp_path):
    with pytest.raises(RobotsDenied):
        make_crawler(tmp_path, robots_checker=deny_all).run(verbose=False)


def test_warnings_capture_missing_fields(tmp_path):
    report = make_crawler(tmp_path).run(verbose=False)
    assert any("作者缺失" in item for item in report.warnings)
    assert any("发布时间缺失" in item for item in report.warnings)
