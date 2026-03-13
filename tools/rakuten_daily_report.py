"""
WAT Tool: Rakuten daily order report → Teams RAKUTEN channel.

Fetches previous day's orders from RMS and posts SKU-level summary.

Usage:
  python tools/rakuten_daily_report.py
  python tools/rakuten_daily_report.py --days 1   # yesterday only (default)
  python tools/rakuten_daily_report.py --days 30  # 30-day summary
"""
import sys
import io
import os
import json
import argparse
import requests
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent))
from rakuten_rms_client import RakutenRMSClient

JST = timezone(timedelta(hours=9))
CONFIG = Path(__file__).parent.parent / "credentials" / "rakuten_rms_config.json"
WEBHOOK = os.getenv("TEAMS_RAKUTEN_WEBHOOK_URL")


def fetch_and_aggregate(days: int):
    client = RakutenRMSClient(str(CONFIG))
    order_numbers = client.search_order_numbers(days=days)
    if not order_numbers:
        return None, None, None, None, None, None

    orders = client.get_orders(order_numbers)

    today = datetime.now(JST).date()
    target_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")

    sku_orders = defaultdict(int)
    sku_units = defaultdict(int)
    sku_sales = defaultdict(float)
    sku_name = {}
    sku_daily = defaultdict(lambda: defaultdict(int))

    for o in orders:
        order_date = (o.get("orderDatetime") or "")[:10]
        for pkg in (o.get("PackageModelList") or []):
            for item in (pkg.get("ItemModelList") or []):
                sku = item.get("manageNumber") or str(item.get("itemId") or "unknown")
                units = int(item.get("units") or 1)
                price = float(item.get("priceTaxIncl") or item.get("price") or 0)
                name_full = item.get("itemName") or ""
                name_short = name_full.split("/")[0].replace("【グロミミ公式】", "").strip()[:30]
                sku_orders[sku] += units  # count as units for period summary
                sku_units[sku] += units
                sku_sales[sku] += price * units
                sku_name[sku] = name_short
                if order_date:
                    sku_daily[sku][order_date] += units

    skus_sorted = sorted(sku_units.keys(), key=lambda s: sku_units[s], reverse=True)
    return skus_sorted, sku_units, sku_sales, sku_name, sku_daily, target_date


def post_to_teams(skus, sku_units, sku_sales, sku_name, sku_daily, report_date, days):
    today = datetime.now(JST).date()
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    date_labels = [(today - timedelta(days=i)).strftime("%m/%d") for i in range(6, -1, -1)]

    total_units = sum(sku_units.values())
    total_sales = sum(sku_sales.values())

    # Yesterday totals
    yday_units = sum(sku_daily[s].get(report_date, 0) for s in skus)
    yday_sales = sum(
        sku_daily[s].get(report_date, 0) * (sku_sales[s] / sku_units[s] if sku_units[s] else 0)
        for s in skus
    )

    period_label = f"前日 ({report_date})" if days <= 2 else f"直近{days}日間"

    body = [
        {
            "type": "TextBlock",
            "text": f"🛒 楽天 日次レポート — {report_date}",
            "weight": "Bolder",
            "size": "Large",
        },
        {
            "type": "TextBlock",
            "text": f"集計: {period_label} | 報告時刻: {datetime.now(JST).strftime('%H:%M')} JST",
            "isSubtle": True,
            "spacing": "None",
        },
        {"type": "TextBlock", "text": "━━━━━━━━━━━━━━━━━━━━", "spacing": "Small"},
        {
            "type": "FactSet",
            "facts": [
                {"title": "前日 注文数", "value": f"{yday_units} 個"},
                {"title": "前日 売上", "value": f"¥{yday_sales:,.0f}"},
                {"title": f"直近{days}日 累計", "value": f"{total_units}個 / ¥{total_sales:,.0f}"},
            ],
            "spacing": "Small",
        },
        {"type": "TextBlock", "text": "━━━━━━━━━━━━━━━━━━━━", "spacing": "Medium"},
        {"type": "TextBlock", "text": f"📦 SKU別集計（直近{days}日）", "weight": "Bolder"},
    ]

    for sku in skus:
        body.append({
            "type": "TextBlock",
            "text": f"**{sku}**",
            "weight": "Bolder",
            "spacing": "Medium",
            "wrap": True,
        })
        body.append({
            "type": "FactSet",
            "facts": [
                {"title": "商品名", "value": sku_name[sku]},
                {"title": "前日", "value": f"{sku_daily[sku].get(report_date, 0)}個"},
                {"title": f"直近{days}日累計", "value": f"{sku_units[sku]}個 / ¥{sku_sales[sku]:,.0f}"},
            ],
            "spacing": "Small",
        })

    # 7-day trend
    body.append({"type": "TextBlock", "text": "━━━━━━━━━━━━━━━━━━━━", "spacing": "Medium"})
    body.append({"type": "TextBlock", "text": "📅 7日間推移（個）", "weight": "Bolder"})
    trend_lines = []
    for sku in skus:
        vals = "  ".join(f"{date_labels[i]}:{sku_daily[sku].get(d, 0)}" for i, d in enumerate(dates))
        trend_lines.append(f"{sku}: {vals}")
    body.append({
        "type": "TextBlock",
        "text": "\n".join(trend_lines),
        "wrap": True,
        "spacing": "Small",
        "fontType": "Monospace",
    })

    payload = {
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "contentUrl": None,
            "content": {"type": "AdaptiveCard", "version": "1.4", "body": body},
        }],
    }

    resp = requests.post(WEBHOOK, json=payload, timeout=15)
    if resp.status_code == 202:
        print(f"Teams posted OK ({report_date})")
    else:
        print(f"Teams error: {resp.status_code} {resp.text[:200]}", file=sys.stderr)
        sys.exit(1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=30, help="Days to aggregate (default: 30)")
    args = p.parse_args()

    if not WEBHOOK:
        print("ERROR: TEAMS_RAKUTEN_WEBHOOK_URL not set in .env", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching Rakuten orders (last {args.days} days)...")
    skus, sku_units, sku_sales, sku_name, sku_daily, report_date = fetch_and_aggregate(args.days)

    if skus is None:
        print("No orders found.")
        # Post empty notice
        today = datetime.now(JST).date()
        report_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        payload = {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": {
                    "type": "AdaptiveCard", "version": "1.4",
                    "body": [
                        {"type": "TextBlock", "text": f"🛒 楽天 日次レポート — {report_date}", "weight": "Bolder", "size": "Large"},
                        {"type": "TextBlock", "text": "本日の注文はありません。", "spacing": "Medium"},
                    ],
                },
            }],
        }
        requests.post(WEBHOOK, json=payload, timeout=15)
        return

    post_to_teams(skus, sku_units, sku_sales, sku_name, sku_daily, report_date, args.days)


if __name__ == "__main__":
    main()
