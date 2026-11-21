# -*- coding: utf-8 -*-
from pathlib import Path

from src.config import FIELDS
from src.parser import Article
from src.storage import audit_articles, read_csv, write_csv


def sample_articles():
    return [
        Article("标题一", "2026-11-10", "作者一", "https://example.com/a"),
        Article("标题二", "2026-11-09", "作者二", "https://example.com/b"),
        Article("标题三", "2026-11-08", "作者三", "https://example.com/c"),
    ]


def test_write_csv_has_bom_and_chinese_headers(tmp_path):
    path = tmp_path / "result.csv"
    write_csv(sample_articles(), path)
    assert path.exists()
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")
    frame = read_csv(path)
    assert list(frame.columns) == list(FIELDS)
    assert len(frame) == 3


def test_csv_values_round_trip(tmp_path):
    path = tmp_path / "result.csv"
    write_csv(sample_articles(), path)
    frame = read_csv(path)
    assert frame.iloc[0]["标题"] == "标题一"
    assert frame.iloc[2]["链接"] == "https://example.com/c"


def test_audit_reports_missing_fields_and_duplicates():
    articles = [
        Article("", "2026-11-10", "", "https://example.com/a"),
        Article("重复", "2026-11-09", "作者", "https://example.com/a"),
    ]
    warnings = audit_articles(articles)
    assert any("标题为空" in item for item in warnings)
    assert any("作者缺失" in item for item in warnings)
    assert any("重复" in item for item in warnings)


def test_audit_empty_result():
    assert audit_articles([]) == ["未解析到任何文章，请检查选择器或页面结构"]


def test_write_csv_creates_parent_directory(tmp_path):
    path = tmp_path / "nested" / "result.csv"
    write_csv(sample_articles(), path)
    assert path.exists()
