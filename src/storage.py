# -*- coding: utf-8 -*-
"""CSV 持久化与质量校验。"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import FIELDS
from .parser import Article


def build_frame(articles: list[Article]) -> pd.DataFrame:
    rows = [article.to_row() for article in articles]
    return pd.DataFrame(rows, columns=list(FIELDS))


def write_csv(articles: list[Article], path: Path) -> Path:
    """以 UTF-8-SIG 写入，保证 Excel 直接打开时中文不乱码。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    build_frame(articles).to_csv(
        path,
        index=False,
        encoding="utf-8-sig",
        lineterminator="\n",
    )
    return path


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)


def audit_articles(articles: list[Article]) -> list[str]:
    """检查空字段与重复链接，返回可读的告警列表。"""
    warnings: list[str] = []
    if not articles:
        return ["未解析到任何文章，请检查选择器或页面结构"]

    seen_links: dict[str, int] = {}
    for index, article in enumerate(articles, start=1):
        if not article.title:
            warnings.append(f"第 {index} 条标题为空")
        if not article.link:
            warnings.append(f"第 {index} 条链接为空")
        if not article.published:
            warnings.append(f"第 {index} 条发布时间缺失，已留空")
        if not article.author:
            warnings.append(f"第 {index} 条作者缺失，已留空")
        if article.link:
            if article.link in seen_links:
                warnings.append(f"第 {index} 条链接与第 {seen_links[article.link]} 条重复")
            else:
                seen_links[article.link] = index
    return warnings
