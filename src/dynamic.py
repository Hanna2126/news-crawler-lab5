# -*- coding: utf-8 -*-
"""Selenium 动态渲染：等待 JS 注入卡片后取回真实 DOM。"""
from __future__ import annotations

import time


def render_page(url: str, timeout: float = 20.0) -> tuple[str, float]:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.edge.options import Options
    from selenium.webdriver.support.ui import WebDriverWait

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--no-first-run")
    started = time.perf_counter()
    driver = webdriver.Edge(options=options)
    try:
        driver.get(url)
        WebDriverWait(driver, timeout).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "article.post-card")) >= 10
        )
        return driver.page_source, time.perf_counter() - started
    finally:
        driver.quit()
