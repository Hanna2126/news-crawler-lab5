# -*- coding: utf-8 -*-
"""HTML 解析层：从列表页卡片提取标题、发布时间、作者和绝对链接。"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .config import FIELDS

DATE_PATTERN = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
SEPARATORS = {"·", "•", "-", "|", "/"}
MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
}


@dataclass(frozen=True)
class Article:
    title: str
    published: str
    author: str
    link: str

    def to_row(self) -> dict[str, str]:
        values = (self.title, self.published, self.author, self.link)
        return dict(zip(FIELDS, values))


def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_date(value: str | None) -> str:
    """把 ISO 时间或英文日期统一成 YYYY-MM-DD；无法识别时保留原文。"""
    text = clean_text(value)
    if not text:
        return ""
    match = DATE_PATTERN.search(text)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y/%m/%d", "%Y年%m月%d日"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return text


def parse_articles(html: str, base_url: str, limit: int | None = None) -> list[Article]:
    """解析列表页中的 article 卡片，按链接去重并保持原顺序。"""
    soup = BeautifulSoup(html or "", "html.parser")
    cards = soup.select("article.post-card") or soup.select("article")
    articles: list[Article] = []
    seen: set[str] = set()

    for card in cards:
        heading = card.select_one("h3") or card.select_one("h2")
        link_tag = None
        if heading is not None:
            link_tag = heading.find_parent("a")
        if link_tag is None:
            link_tag = card.select_one("a[href]")

        title = clean_text(heading.get_text(" ", strip=True)) if heading else ""
        if not title and link_tag is not None:
            title = clean_text(link_tag.get_text(" ", strip=True))
        raw_link = link_tag.get("href", "") if link_tag is not None else ""
        link = urljoin(base_url, raw_link) if raw_link else ""

        time_tag = card.select_one("time")
        published = normalize_date(time_tag.get("datetime") or time_tag.get_text()) if time_tag else ""

        author = ""
        meta = time_tag.parent if time_tag is not None else card.select_one(".meta")
        if meta is None:
            meta = card.select_one("div")
        if meta is not None:
            for span in meta.select("span"):
                candidate = clean_text(span.get_text(" ", strip=True))
                if candidate and candidate not in SEPARATORS and not candidate.replace(",", "").isdigit():
                    author = candidate
                    break
        if not author:
            author_tag = card.select_one(".post-author")
            author = clean_text(author_tag.get_text(" ", strip=True)) if author_tag else ""

        key = link or title
        if not key or key in seen:
            continue
        seen.add(key)
        articles.append(Article(title=title, published=published, author=author, link=link))
        if limit is not None and len(articles) >= limit:
            break

    return articles


def parse_file(path: Path, base_url: str, limit: int | None = None) -> list[Article]:
    return parse_articles(path.read_text(encoding="utf-8"), base_url, limit)


def article_dicts(articles: list[Article]) -> list[dict[str, str]]:
    return [asdict(item) for item in articles]
