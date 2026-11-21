# -*- coding: utf-8 -*-
"""项目级配置：路径、默认目标、请求头与限速参数。"""
from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

DEFAULT_URL = "https://blog.python.org/"
DEFAULT_OUTPUT = DATA_DIR / "result.csv"

# 带用途说明的 UA，方便站点管理员识别流量来源。
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0 Safari/537.36 "
    "CrawlerLab/1.0 (+https://github.com/Hanna2126/news-crawler-lab5)"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
    "Connection": "keep-alive",
}

FIELDS = ("标题", "发布时间", "作者", "链接")
DEFAULT_DELAY = 2.0
DEFAULT_RETRIES = 3
DEFAULT_TIMEOUT = 15.0
RETRY_STATUS = {429, 500, 502, 503, 504}
