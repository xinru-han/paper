#!/usr/bin/env python3
"""Crawl national agricultural product GI registration data.

Source page:
http://www.greenfood.agri.cn/xxcx/dlbzcx/

The site exposes the table through:
POST http://www.greenfood.agri.cn/api/product/productSearch
"""

from __future__ import annotations

import argparse
import csv
import http.client
import json
import math
import shutil
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


HOST = "www.greenfood.agri.cn"
API_PATH = "/api/product/productSearch"
SOURCE_PAGE = f"http://{HOST}/xxcx/dlbzcx/"
API_URL = f"http://{HOST}{API_PATH}"

CSV_FIELDS = [
    "序号",
    "接口ID",
    "登记年份",
    "产品名称",
    "省（区市）",
    "证书持有人名称",
    "产品类别",
    "登记证书编号",
]


def build_payload(page_index: int, page_size: int) -> dict[str, Any]:
    return {
        "date": "",
        "productName": "",
        "address": "",
        "certificatePossessor": "",
        "certificateId": "",
        # These names follow the website JavaScript: pageSize is page index,
        # pageNum is records per page.
        "pageSize": page_index,
        "pageNum": page_size,
    }


def post_json(payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    headers = {
        "User-Agent": "curl/8.7.1",
        "Accept": "*/*",
        "Content-Type": "application/json;charset=UTF-8",
        "Referer": SOURCE_PAGE,
        "Content-Length": str(len(body)),
    }
    conn = http.client.HTTPConnection(HOST, 80, timeout=timeout)
    try:
        conn.request("POST", API_PATH, body=body, headers=headers)
        response = conn.getresponse()
        raw = response.read()
    finally:
        conn.close()

    text = raw.decode("utf-8", errors="replace")
    if response.status != 200:
        raise RuntimeError(f"HTTP {response.status}: {text[:300]}")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON response: {text[:300]}") from exc
    if not parsed.get("success"):
        raise RuntimeError(f"API returned unsuccessful response: {parsed}")
    return parsed


def fetch_page(page_index: int, page_size: int, timeout: int, retries: int) -> tuple[int, list[dict[str, Any]]]:
    payload = build_payload(page_index, page_size)
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            parsed = post_json(payload, timeout=timeout)
            data = parsed.get("data") or {}
            total = int(data.get("total") or 0)
            rows = data.get("data") or []
            if not isinstance(rows, list):
                raise RuntimeError(f"Unexpected row payload: {type(rows)!r}")
            return total, rows
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < retries:
                time.sleep(min(2 * attempt, 8))
    raise RuntimeError(f"Failed page {page_index} after {retries} attempts: {last_error}")


def to_csv_row(index: int, row: dict[str, Any]) -> dict[str, Any]:
    def clean(value: Any) -> Any:
        if not isinstance(value, str):
            return value
        return value.replace("\r", "").replace("\n", "").replace("\t", "").strip()

    return {
        "序号": index,
        "接口ID": row.get("id", ""),
        "登记年份": clean(row.get("date", "")),
        "产品名称": clean(row.get("productName", "")),
        "省（区市）": clean(row.get("address", "")),
        "证书持有人名称": clean(row.get("certificatePossessor", "")),
        "产品类别": clean(row.get("category", "")),
        "登记证书编号": clean(row.get("certificateId", "")),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for index, row in enumerate(rows, start=1):
            writer.writerow(to_csv_row(index, row))


def write_json(path: Path, rows: list[dict[str, Any]], total: int, page_size: int, crawl_time: str) -> None:
    payload = {
        "source_page": SOURCE_PAGE,
        "api_url": API_URL,
        "crawl_time": crawl_time,
        "total_reported": total,
        "row_count": len(rows),
        "page_size": page_size,
        "data": rows,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def format_counter(counter: Counter[str], limit: int | None = None) -> str:
    items = counter.most_common(limit)
    return "\n".join(f"| {key} | {value} |" for key, value in items)


def write_report(path: Path, rows: list[dict[str, Any]], total: int, page_size: int, crawl_time: str) -> None:
    years = Counter(str(row.get("date", "") or "空值") for row in rows)
    provinces = Counter(str(row.get("address", "") or "空值") for row in rows)
    categories = Counter(str(row.get("category", "") or "空值") for row in rows)

    lines = [
        "# 全国农产品地理标志登记数据抓取报告",
        "",
        f"- 数据源页面：{SOURCE_PAGE}",
        f"- 接口地址：{API_URL}",
        f"- 抓取时间：{crawl_time}",
        f"- 接口返回总数：{total}",
        f"- 实际写入条数：{len(rows)}",
        f"- 每页请求条数：{page_size}",
        "",
        "## 按登记年份统计",
        "",
        "| 登记年份 | 条数 |",
        "| --- | ---: |",
        *format_counter(Counter(dict(sorted(years.items())))).splitlines(),
        "",
        "## 按省（区市）统计",
        "",
        "| 省（区市） | 条数 |",
        "| --- | ---: |",
        *format_counter(provinces).splitlines(),
        "",
        "## 按产品类别统计",
        "",
        "| 产品类别 | 条数 |",
        "| --- | ---: |",
        *format_counter(categories).splitlines(),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def validate_rows(rows: list[dict[str, Any]], total: int) -> None:
    if len(rows) != total:
        raise RuntimeError(f"Row count mismatch: collected {len(rows)}, API total {total}")

    ids = [row.get("id") for row in rows]
    duplicate_ids = [item for item, count in Counter(ids).items() if count > 1]
    if duplicate_ids:
        preview = ", ".join(map(str, duplicate_ids[:10]))
        raise RuntimeError(f"Duplicate API IDs found: {preview}")

    cert_ids = [row.get("certificateId") for row in rows if row.get("certificateId")]
    duplicate_cert_ids = [item for item, count in Counter(cert_ids).items() if count > 1]
    if duplicate_cert_ids:
        preview = ", ".join(map(str, duplicate_cert_ids[:10]))
        print(f"Warning: duplicate certificate IDs found: {preview}", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="processed", help="Output directory.")
    parser.add_argument("--page-size", type=int, default=200, help="Records per API request.")
    parser.add_argument("--sleep", type=float, default=0.3, help="Seconds to sleep between requests.")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds.")
    parser.add_argument("--retries", type=int, default=4, help="Retries per page.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.page_size <= 0:
        raise SystemExit("--page-size must be positive")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    crawl_time = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S %Z")
    stamp = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d_%H%M%S")

    total, first_rows = fetch_page(1, args.page_size, args.timeout, args.retries)
    pages = math.ceil(total / args.page_size)
    rows = list(first_rows)
    print(f"Page 1/{pages}: {len(first_rows)} rows, total={total}", file=sys.stderr)

    for page_index in range(2, pages + 1):
        if args.sleep:
            time.sleep(args.sleep)
        page_total, page_rows = fetch_page(page_index, args.page_size, args.timeout, args.retries)
        if page_total != total:
            print(f"Warning: API total changed from {total} to {page_total} on page {page_index}", file=sys.stderr)
            total = page_total
            pages = math.ceil(total / args.page_size)
        rows.extend(page_rows)
        print(f"Page {page_index}/{pages}: {len(page_rows)} rows", file=sys.stderr)

    validate_rows(rows, total)

    csv_path = out_dir / f"agri_gi_registration_{stamp}.csv"
    json_path = out_dir / f"agri_gi_registration_{stamp}.json"
    report_path = out_dir / f"agri_gi_registration_report_{stamp}.md"
    write_csv(csv_path, rows)
    write_json(json_path, rows, total, args.page_size, crawl_time)
    write_report(report_path, rows, total, args.page_size, crawl_time)

    latest_csv = out_dir / "agri_gi_registration_latest.csv"
    latest_json = out_dir / "agri_gi_registration_latest.json"
    latest_report = out_dir / "agri_gi_registration_report_latest.md"
    shutil.copyfile(csv_path, latest_csv)
    shutil.copyfile(json_path, latest_json)
    shutil.copyfile(report_path, latest_report)

    print(f"Wrote {len(rows)} rows")
    print(f"CSV: {csv_path}")
    print(f"JSON: {json_path}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
