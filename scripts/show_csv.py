# -*- coding: utf-8 -*-
"""逐条打印 result.csv，四列信息完整可读。"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import DEFAULT_OUTPUT


def main() -> None:
    path = Path(DEFAULT_OUTPUT)
    frame = pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    print("=" * 118)
    print(f"{len(frame)} 条记录 | data/result.csv | UTF-8-SIG | 列：标题、发布时间、作者、链接")
    print("-" * 118)
    for index, row in frame.iterrows():
        print(f"[{index + 1:02d}] {row['标题']}")
        print(f"     {row['发布时间']}  |  {row['作者']}")
        print(f"     {row['链接']}")
    print("-" * 118)
    print(f"共 {len(frame)} 行 | 编码：UTF-8-SIG | 文件：data/result.csv")


if __name__ == "__main__":
    main()
