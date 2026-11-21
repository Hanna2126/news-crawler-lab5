# -*- coding: utf-8 -*-
"""打印目标页的 HTML 结构，确认选择器命中情况。"""
from __future__ import annotations

import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import DEFAULT_URL, HEADERS


def main() -> None:
    response = requests.get(DEFAULT_URL, headers=HEADERS, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    cards = soup.select("article.post-card")
    print(f"HTTP {response.status_code} | HTML {len(response.text)} 字符 | 卡片 {len(cards)} 个")
    print(f"h3 命中 {len(soup.select('article.post-card h3'))} 个 | "
          f"time 命中 {len(soup.select('article.post-card time'))} 个 | "
          f"a 命中 {len(soup.select('article.post-card a[href]'))} 个")
    print("-" * 72)
    if not cards:
        print("未找到卡片")
        return
    card = cards[0]
    for tag in card.find_all(True):
        tag.attrs = {k: v for k, v in tag.attrs.items() if k in ("href", "datetime")}
    print("首个卡片的关键字段：")
    print(f"标题：{card.select_one('h3').get_text(strip=True)}")
    print(f"链接：{card.select_one('a[href]')['href']}")
    print(f"时间：{card.select_one('time')['datetime']}")
    print(f"作者：{card.select_one('span').get_text(strip=True)}")
    print("精简后的 HTML 结构：")
    print(card.prettify()[:600])


if __name__ == "__main__":
    main()
