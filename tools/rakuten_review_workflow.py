#!/usr/bin/env python3
"""
Workflow: fetch orders from Rakuten RMS, send delivery+review emails, mark orders processed.

Requires:
 - `credentials/rakuten_rms_config.json` (see `rakuten_rms_client.py`)
 - Gmail OAuth credentials (`GMAIL_OAUTH_CREDENTIALS_PATH`) and token path

This script is intentionally conservative: it uses the RMS config to call list and update
endpoints. Adapt `orders_mapping` in the config or below to match the RMS response shape.
"""
import argparse
import os
from pprint import pprint

from rakuten_rms_client import RakutenRMSClient

from send_rakuten_review_emails import get_credentials, create_message_html, send_email, build_review_link
from googleapiclient.discovery import build


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="credentials/rakuten_rms_config.json")
    p.add_argument("--gmail-credentials", default=os.getenv("GMAIL_OAUTH_CREDENTIALS_PATH", "credentials/gmail_oauth_credentials.json"))
    p.add_argument("--gmail-token", default=os.getenv("GMAIL_TOKEN_PATH", "credentials/gmail_token.json"))
    p.add_argument("--status", default=None, help="Filter orders by status (e.g., '発送済')")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--from", dest="from_email", default=os.getenv("GORGIAS_EMAIL") or None)
    p.add_argument("--subject", default="【お願い】ご購入商品のご感想をお聞かせください！")
    args = p.parse_args()

    client = RakutenRMSClient(args.config)

    print("Fetching orders from RMS...")
    orders = client.list_orders(status=args.status)
    print(f"Found {len(orders)} orders (raw)")

    # Define how to extract fields from each order item. Adjust as needed.
    # Typical expected keys (customize to match your RMS response):
    # email_key, order_id_key, shop_id_key, item_id_key, item_name_key, item_url_key, customer_name_key
    mapping = client.cfg.get("orders_mapping", {
        "email_key": "customer_email",
        "order_id_key": "order_id",
        "shop_id_key": "shop_id",
        "item_id_key": "item_id",
        "item_name_key": "item_name",
        "item_url_key": "item_url",
        "customer_name_key": "customer_name",
    })

    creds = get_credentials(args.gmail_credentials, args.gmail_token)
    service = build("gmail", "v1", credentials=creds)
    sender = args.from_email or client.cfg.get("from_email")
    if not sender:
        sender = input("Send as (From) email: ").strip()

    for o in orders:
        # allow nested keys with dot notation
        def getkey(obj, key):
            if not key:
                return None
            parts = key.split(".")
            cur = obj
            for p in parts:
                if isinstance(cur, dict):
                    cur = cur.get(p)
                else:
                    return None
            return cur

        to_email = (getkey(o, mapping["email_key"]) or "").strip()
        if not to_email:
            print("Skipping order (no email)")
            continue
        order_id = getkey(o, mapping["order_id_key"]) or getkey(o, "id")
        shop_id = getkey(o, mapping["shop_id_key"]) or client.cfg.get("shop_id")
        item_id = getkey(o, mapping["item_id_key"]) or None
        item_name = getkey(o, mapping["item_name_key"]) or "ご購入商品"
        item_url = getkey(o, mapping["item_url_key"]) or None
        customer_name = getkey(o, mapping["customer_name_key"]) or "お客様"

        review_link = build_review_link(shop_id, item_id, item_url)
        html = create_message_html(customer_name, item_name, review_link, shop_name=client.cfg.get("shop_name"))

        print(f"Sending email to {to_email} for order {order_id} (dry_run={args.dry_run})")
        res = send_email(service, sender, to_email, args.subject, html, dry_run=args.dry_run)
        if res:
            print(f"Email sent: id={res.get('id')}")

        # After sending, optionally update order status in RMS
        if not args.dry_run:
            update_payload = client.cfg.get("delivered_payload") or {"status": client.cfg.get("delivered_status", "配送完了")}
            try:
                resp = client.update_order_status(order_id=str(order_id), shop_id=shop_id, payload=update_payload, method=client.cfg.get("update_method", "post"))
                print(f"Updated order {order_id}: {resp}")
            except Exception as e:
                print(f"Failed to update order {order_id}: {e}")


if __name__ == "__main__":
    main()
