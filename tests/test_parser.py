# -*- coding: utf-8 -*-
from pathlib import Path

from src.parser import clean_text, normalize_date, parse_articles

FIXTURE = Path(__file__).parent / "fixtures" / "list_page.html"


def load_articles(limit=None):
    return parse_articles(FIXTURE.read_text(encoding="utf-8"), "https://blog.python.org/", limit)


def test_parses_four_unique_articles():
    articles = load_articles()
    assert len(articles) == 4


def test_extracts_title_date_author_and_link():
    first = load_articles()[0]
    assert first.title == "Python 3.16.0 alpha 2 is now available"
    assert first.published == "2026-11-10"
    assert first.author == "Savannah Ostrowski"
    assert first.link == "https://blog.python.org/2026/11/python-3160-alpha-2"


def test_relative_link_is_resolved_against_base_url():
    third = load_articles()[2]
    assert third.link == "https://blog.python.org/2026/10/no-author"


def test_absolute_link_is_kept():
    second = load_articles()[1]
    assert second.link == "https://blog.python.org/2026/10/steering-council"


def test_missing_author_becomes_empty_string():
    third = load_articles()[2]
    assert third.author == ""


def test_missing_time_becomes_empty_string_but_author_is_kept():
    fourth = load_articles()[3]
    assert fourth.published == ""
    assert fourth.author == "Anonymous"


def test_duplicate_link_is_removed():
    links = [article.link for article in load_articles()]
    assert len(links) == len(set(links))


def test_limit_stops_after_n_records():
    assert len(load_articles(limit=2)) == 2


def test_invalid_html_returns_empty_list():
    assert parse_articles("", "https://example.com") == []
    assert parse_articles("<html><body><p>no cards</p></body></html>", "https://example.com") == []


def test_normalize_date_formats():
    assert normalize_date("2026-11-10T00:00:00.000Z") == "2026-11-10"
    assert normalize_date("November 10, 2026") == "2026-11-10"
    assert normalize_date("2026/11/10") == "2026-11-10"
    assert normalize_date("") == ""


def test_clean_text_collapses_whitespace():
    assert clean_text("  No   author \n post  ") == "No author post"
