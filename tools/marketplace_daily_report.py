"""
WAT Tool: マーケットプレイス デイリーレポート データ集計

楽天・Amazon の売上・注文・広告データを集計してJSON出力する。

Usage:
  python tools/marketplace_daily_report.py
  python tools/marketplace_daily_report.py --date 2026-04-13
"""
import sys
import io
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import defaultdict

JST = timezone(timedelta(hours=9))
DATAKEEPER = Path(__file__).parent.parent.parent / "Shared" / "datakeeper" / "latest"


def fetch_amazon_sales(report_date: str, data_file: Path = None) -> dict:
    """DataKeeperからAmazon売上を集計して返す。"""
    path = data_file or (DATAKEEPER / "amazon_sales_daily.json")
    if not path.exists():
        return {
            "error": f"DataKeeper file not found: {path}",
            "total_orders": 0,
            "total_units": 0,
            "total_gross": 0.0,
            "total_net": 0.0,
            "brands": {},
        }

    with open(path, encoding="utf-8") as f:
        rows = json.load(f)

    brands = defaultdict(lambda: {"orders": 0, "units": 0, "gross_sales": 0.0, "net_sales": 0.0, "fees": 0.0, "refunds": 0.0})
    for row in rows:
        if row.get("date") != report_date:
            continue
        b = row.get("brand", "Unknown")
        brands[b]["orders"]      += row.get("orders", 0)
        brands[b]["units"]       += row.get("units", 0)
        brands[b]["gross_sales"] += row.get("gross_sales", 0.0)
        brands[b]["net_sales"]   += row.get("net_sales", 0.0)
        brands[b]["fees"]        += row.get("fees", 0.0)
        brands[b]["refunds"]     += row.get("refunds", 0.0)

    brands_dict = dict(brands)
    return {
        "total_orders": sum(b["orders"] for b in brands_dict.values()),
        "total_units":  sum(b["units"]  for b in brands_dict.values()),
        "total_gross":  sum(b["gross_sales"] for b in brands_dict.values()),
        "total_net":    sum(b["net_sales"]   for b in brands_dict.values()),
        "brands": brands_dict,
    }


if __name__ == "__main__":
    # Windows UTF-8 fix — only when running as a script, not on import
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="マーケットプレイス デイリーレポート")
    parser.add_argument("--date", default=datetime.now(JST).strftime("%Y-%m-%d"), help="集計対象日 (YYYY-MM-DD)")
    args = parser.parse_args()

    result = fetch_amazon_sales(args.date)
    print(json.dumps(result, ensure_ascii=False, indent=2))
