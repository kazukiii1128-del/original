#!/usr/bin/env python3
"""
Fetch shipped orders from Rakuten RMS, send review-request emails via Rakuten SMTP relay.

Usage:
  python tools/rakuten_review_workflow.py --dry-run
  python tools/rakuten_review_workflow.py --days 14
"""
import argparse
import json
import os
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SENT_LOG_PATH = "logs/sent_orders.json"


def load_sent(path: str) -> set:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_sent(path: str, sent_set: set) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted(sent_set), f, ensure_ascii=False, indent=2)
from rakuten_rms_client import RakutenRMSClient
from send_rakuten_review_emails import create_message_html, build_review_link
from track_delivery import check_delivered, get_tracking_info

JST = timezone(timedelta(hours=9))


# RMS order progress codes: 100=注文確認待ち, 200=楽天処理中, 300=発送待ち, 400=変更確定待ち, 500=発送済, 600=支払手続き中, 700=支払済
SHIPPED_PROGRESS = [500]


def extract_order_info(order: dict, shop_id: str) -> dict:
    """Pull relevant fields out of an RMS getOrder (version=3) response object."""
    # RMS API v2 version=3 uses PascalCase keys
    packages = order.get("PackageModelList") or []
    item = {}
    if packages:
        items = packages[0].get("ItemModelList") or []
        if items:
            item = items[0]

    orderer = order.get("OrdererModel") or {}
    email = orderer.get("emailAddress", "")
    family = orderer.get("familyName", "")
    first = orderer.get("firstName", "")
    name = (family + first).strip() or "お客様"

    item_id = str(item.get("itemId") or item.get("manageNumber") or "")
    item_name = item.get("itemName") or "ご購入商品"

    # Check if customer opted in to write a review
    opted_in = False
    for pkg in packages:
        for it in (pkg.get("ItemModelList") or []):
            choice = it.get("selectedChoice") or ""
            if "レビューを書く" in choice and "レビューを書かない" not in choice:
                opted_in = True
                break

    return {
        "order_number": order.get("orderNumber", ""),
        "email": email.strip(),
        "name": name,
        "item_id": item_id,
        "item_name": item_name,
        "item_url": "",
        "shop_id": shop_id,
        "opted_in": opted_in,
    }


def send_via_smtp(smtp_cfg: dict, sender: str, to_email: str, subject: str, html_body: str, dry_run: bool = False) -> bool:
    if dry_run:
        print(f"    DRY RUN: would send to {to_email}")
        return True
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_cfg["host"], smtp_cfg["port"]) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(smtp_cfg["user"], smtp_cfg["password"])
        server.sendmail(sender, to_email, msg.as_bytes())
    return True


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="credentials/rakuten_rms_config.json")
    p.add_argument("--days", type=int, default=30, help="Search orders from last N days")
    p.add_argument("--min-ship-days", type=int, default=3, help="Only send to orders shipped at least N days ago (default: 3)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--from", dest="from_email", default=os.getenv("RAKUTEN_FROM_EMAIL") or None)
    p.add_argument("--subject", default="【お願い】ご購入商品のご感想をお聞かせください！")
    args = p.parse_args()

    client = RakutenRMSClient(args.config)
    shop_id = client.cfg.get("shop_id", "")
    smtp_cfg = client.cfg.get("smtp") or {}

    if not smtp_cfg.get("host"):
        raise ValueError("smtp config missing in rakuten_rms_config.json")

    sender = args.from_email or client.cfg.get("from_email")
    if not sender:
        sender = input("Send as (From) email: ").strip()

    print(f"Fetching shipped orders (last {args.days} days)...")
    orders = client.list_orders(days=args.days, order_progress=SHIPPED_PROGRESS)
    print(f"Found {len(orders)} orders")

    if not orders:
        print("No orders to process.")
        return

    cutoff = datetime.now(JST) - timedelta(days=args.min_ship_days)
    sent_set = load_sent(SENT_LOG_PATH)

    sent = 0
    skipped = 0
    for o in orders:
        order_number = o.get("orderNumber", "")

        # --- Duplicate check ---
        if order_number in sent_set:
            print(f"  Skipping {order_number} (already sent)")
            skipped += 1
            continue

        # --- Delivery check ---
        # Step 1: skip if shipped too recently (fast, no HTTP call)
        shipped_str = o.get("shippingCmplRptDatetime") or ""
        if shipped_str:
            try:
                if datetime.fromisoformat(shipped_str) > cutoff:
                    print(f"  Skipping {order_number} (shipped {shipped_str[:10]}, waiting {args.min_ship_days}d)")
                    skipped += 1
                    continue
            except ValueError:
                pass

        # Step 2: confirm delivery via carrier tracking
        tracking_list = get_tracking_info(o)
        if tracking_list:
            t = tracking_list[0]
            delivered = check_delivered(t["carrier_code"], t["tracking_number"])
            if delivered is False:
                print(f"  Skipping {order_number} (not yet delivered, tracking={t['tracking_number']})")
                skipped += 1
                continue
            elif delivered is None:
                print(f"  Skipping {order_number} (tracking check failed, tracking={t['tracking_number']})")
                skipped += 1
                continue
            # delivered is True → proceed

        info = extract_order_info(o, shop_id)
        if not info["email"]:
            print(f"  Skipping {info['order_number']} (no email)")
            skipped += 1
            continue

        if not info["opted_in"]:
            print(f"  Skipping {info['order_number']} (did not opt in to review)")
            skipped += 1
            continue

        review_link = build_review_link(info["shop_id"], info["item_id"], info["item_url"])
        html = create_message_html(info["name"], info["item_name"], review_link, shop_name=client.cfg.get("shop_name"))

        print(f"  {'[DRY]' if args.dry_run else 'Sending'} -> {info['email']} ({info['order_number']})")
        try:
            send_via_smtp(smtp_cfg, sender, info["email"], args.subject, html, dry_run=args.dry_run)
            sent += 1
            if not args.dry_run:
                print(f"    Sent OK")
                sent_set.add(order_number)
                save_sent(SENT_LOG_PATH, sent_set)
        except Exception as e:
            print(f"    ERROR: {e}")
            skipped += 1

    print(f"\nDone. sent={sent}, skipped={skipped}")


if __name__ == "__main__":
    main()