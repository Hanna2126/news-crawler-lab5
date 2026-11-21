# news-crawler-lab5

Python 爬虫开发实验：用 `requests + BeautifulSoup` 抓取公开静态列表页，提取 **标题、发布时间、作者、链接**，写入 UTF-8 CSV，并完成限速、重试、robots 检查、字段容错与面向对象重构。

- 目标站点：<https://blog.python.org/>（Python 官方博客列表页）
- 正式结果：8 条记录，四字段完整，重复链接 0
- 测试：26 条 pytest 全部通过
- 进阶：Selenium headless Edge 渲染动态页，并与静态请求对比

## 目录结构

```text
news-crawler-lab5/
├─ crawler.py              # 命令行入口
├─ src/
│  ├─ config.py            # URL、UA、列名、默认参数
│  ├─ fetcher.py           # robots、GET、限速、重试
│  ├─ parser.py            # 卡片解析与字段清洗
│  ├─ storage.py           # CSV 写入与回读审计
│  ├─ crawler.py           # NewsCrawler 五阶段编排
│  └─ dynamic.py           # Selenium 动态渲染
├─ scripts/
│  ├─ inspect_page.py      # 打印 HTML 结构与选择器命中
│  ├─ show_csv.py          # 四字段完整展示
│  ├─ demo_retry.py        # 503×3 后成功
│  ├─ compare_render.py    # 静态 vs 动态渲染对比
│  └─ serve_demo.py        # 本地演示站点
├─ site/                   # 本地静态页与 JS 动态页
├─ tests/                  # 26 条 pytest 用例
├─ data/result.csv         # 正式抓取结果
├─ 截图/                   # 8 张真实运行截图
├─ blog/                   # Markdown 博客与配图
└─ 实验报告.docx
```

## 快速开始

```powershell
python -m pip install -r requirements.txt
python crawler.py
```

正式运行会请求 `https://blog.python.org/`，检查 robots、抓取列表页、写入 `data/result.csv`，并在终端打印五阶段输出。

常用命令：

```powershell
# 只抓 3 条，验证最小链路
python crawler.py --limit 3 --output output/demo_limit.csv

# 查看 CSV 的四字段内容
python scripts/show_csv.py

# 结构检查
python scripts/inspect_page.py

# 测试
python -m pytest -v --no-header

# 重试演示：前 3 次 503，第 4 次 200
python scripts/demo_retry.py

# 静态请求与 Selenium 动态渲染对比
python scripts/compare_render.py
```

命令行参数：

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--url` | `https://blog.python.org/` | 目标列表页 |
| `--output` | `data/result.csv` | CSV 输出路径 |
| `--delay` | `2.0` | 连续页面请求的最小间隔，小于 2 会被拒绝 |
| `--retries` | `3` | 首次失败后的重试次数，总尝试上限为 4 |
| `--timeout` | `15.0` | 单次请求超时（秒） |
| `--limit` | 无 | 最多保留多少条 |
| `--no-robots` | 关闭 | 显式跳过 robots 检查，仅用于本地调试 |

## 真实运行结果

```text
[1/5] 合规检查
  robots：robots.txt 不存在（404），按无限制处理
[2/5] 发送请求
  HTTP 200，31463 字节，编码 utf-8
  用时 1.48s，尝试 1 次
[3/5] 解析列表
  解析到 8 篇文章（已按链接去重）
[4/5] 写入 CSV
  文件：.../data/result.csv
[5/5] 质量校验
  回读：8 行，列名 标题/发布时间/作者/链接
  未发现空字段或重复链接
```

抓到的 8 条记录：

| 标题 | 发布时间 | 作者 |
|---|---|---|
| Python 3.16.0 alpha 2 is now available | 2026-11-10 | Savannah Ostrowski |
| Python 3.15.2, 3.14.10, 3.13.18, 3.12.16 and 3.11.18 are out | 2026-10-26 | Hugo van Kemenade |
| Python 3.15.1, 3.14.9 and 3.13.17 are out | 2026-10-21 | Hugo van Kemenade |
| Python 3.16.0 alpha 1 is now available | 2026-10-13 | Savannah Ostrowski |
| Python 3.15.0 (final) is here! | 2026-10-09 | Hugo van Kemenade |
| Python 3.15.0 candidate 3 is here! | 2026-10-02 | Hugo van Kemenade |
| Python 3.10.22, 3.11.17, 3.12.15, 3.13.16 and 3.14.8 are now available! | 2026-10-01 | Pablo Galindo |
| Python Language Summit 2026 | 2026-09-30 | Seth Larson |

## 关键实现

- **请求层**：UA 带 Chrome 标识与 `CrawlerLab/1.0` 联系方式；`time.monotonic` 保证连续页面请求间隔 ≥ 2 秒；503/429/超时/连接错误最多重试 3 次。
- **合规层**：先读 `robots.txt`；404 按 RFC 9309 视为未提供规则，Disallow 抛 `RobotsDenied` 并以退出码 2 结束。
- **解析层**：`article.post-card` 选卡片，`h3` 取标题，`time[datetime]` 取时间，meta 行首个 `span` 取作者，`urljoin` 补全相对链接；空标题/空链接跳过，重复链接去重。
- **持久化**：`utf-8-sig` + `lineterminator="\n"`；回读时 `dtype=str, keep_default_na=False`，避免空字段变成 NaN。
- **工程化**：`NewsCrawler` 把五阶段收进一个类，支持注入假 fetcher / 假 robots，测试不联网。
- **动态渲染**：Selenium headless Edge 等待 `article.post-card` 出现后取 `page_source`，继续复用同一个解析器。

## 静态 vs 动态

本地演示页对比结果：

| 方案 | 请求方式 | 条数 | 耗时 |
|---|---|---|---|
| 静态页 requests+BS4 | 单次 HTTP GET | 12 | 0.165s |
| 动态页 requests+BS4 | 单次 HTTP GET | 0 | 0.016s |
| 动态页 Selenium+BS4 | 浏览器渲染后取源码 | 12 | 4.007s |

动态方案总耗时约为静态方案的 24.3 倍。能静态抓就静态抓；只有数据确实由 JS 注入、且没有可用 JSON 接口时，才上浏览器。

## 测试

```text
26 passed in 1.22s
```

覆盖：四字段解析、链接补全、缺作者、缺时间、重复链接、limit、日期归一化、UTF-8-SIG、读写回环、审计、503 重试、500 耗尽、超时、限速、robots 禁止/404、端到端 CSV、robots 拒绝、warnings。

## 合规说明

- 只抓公开列表页的标题、时间、作者、链接，不抓正文、不抓图片、不并发翻页。
- 单次运行只请求一个列表页；连续页面请求由限速器保证至少 2 秒间隔。
- 遵守 robots.txt；`robots.txt` 不存在时按 RFC 9309 视为未提供规则，并在输出中记录原因。
- 抓取内容仅用于课程实验演示，不用于商业分发。

## 博客与报告

- 博客：[`blog/lab5-news-crawler.md`](blog/lab5-news-crawler.md)
- 实验报告：[`实验报告.docx`](实验报告.docx)
- 截图：[`截图/`](截图)
