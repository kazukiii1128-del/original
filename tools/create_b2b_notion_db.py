# -*- coding: utf-8 -*-
"""
Google Sheets B2Bリスト → Notion データベースへインポート
- Notionに管理DBを新規作成（既存同名DBはアーカイブ）
- ステータス・優先度・次のアクション列を追加（かんばんボード用）
"""
import os, sys, json, time, requests
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from google.oauth2 import service_account
from googleapiclient.discovery import build

# ── 認証 ────────────────────────────────────────────────────────────────────
NOTION_TOKEN = os.getenv("NOTION_API_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

gcreds = service_account.Credentials.from_service_account_file(
    "credentials/google_service_account.json",
    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
)
gsvc = build("sheets", "v4", credentials=gcreds)

SHEET_ID    = "1wAtotUgxyaUP4C-JTGMyDPurjfv5QC_q9N8l9M8nafE"
PARENT_PAGE = "34386c6dc0468034b2a6e637bd398d41"
DB_TITLE    = "grosmimi B2B リスト"

# ── Google Sheets からデータ取得 ─────────────────────────────────────────────
result = gsvc.spreadsheets().values().get(
    spreadsheetId=SHEET_ID, range="B2Bリスト!A1:M100"
).execute()
rows = result.get("values", [])
data = rows[1:]
print(f"取得: {len(data)} 社")

# ── 既存DBをアーカイブ ────────────────────────────────────────────────────────
r = requests.post("https://api.notion.com/v1/search",
    headers=HEADERS,
    json={"query": DB_TITLE, "filter": {"value": "database", "property": "object"}}
)
for item in r.json().get("results", []):
    t = item.get("title", [])
    name = t[0]["plain_text"] if t else ""
    if name == DB_TITLE:
        requests.patch(f"https://api.notion.com/v1/databases/{item['id']}",
            headers=HEADERS, json={"archived": True})
        print(f"旧DB削除: {item['id']}")

# ── DB作成 ───────────────────────────────────────────────────────────────────
CAT_COLOR = {
    "A. 大手ベビー専門チェーン":     "red",
    "B. 百貨店（ベビー売場）":       "orange",
    "C. セレクトショップ":           "blue",
    "D. EC・通販":                   "green",
    "E. 小規模セレクトショップ":     "purple",
    "F. 卸売・ディストリビューター": "brown",
    "G. その他ベビー専門":           "gray",
}

db_body = {
    "parent": {"type": "page_id", "page_id": PARENT_PAGE},
    "title": [{"type": "text", "text": {"content": DB_TITLE}}],
    "icon": {"type": "emoji", "emoji": "🍼"},
    "properties": {
        "会社名":           {"title": {}},
        "カテゴリ":         {"select": {"options": [
            {"name": k, "color": v} for k, v in CAT_COLOR.items()
        ]}},
        "ステータス":       {"select": {"options": [
            {"name": "未着手",        "color": "gray"},
            {"name": "コンタクト済み","color": "blue"},
            {"name": "返信待ち",      "color": "yellow"},
            {"name": "商談中",        "color": "orange"},
            {"name": "取引成立",      "color": "green"},
            {"name": "見送り",        "color": "red"},
        ]}},
        "優先度":           {"select": {"options": [
            {"name": "高", "color": "red"},
            {"name": "中", "color": "yellow"},
            {"name": "低", "color": "gray"},
        ]}},
        "規模・店舗数":     {"rich_text": {}},
        "主要エリア":       {"rich_text": {}},
        "本社所在地":       {"rich_text": {}},
        "電話番号":         {"phone_number": {}},
        "卸・問合URL":      {"url": {}},
        "公式URL":          {"url": {}},
        "SNS":              {"rich_text": {}},
        "担当者情報":       {"rich_text": {}},
        "アプローチメモ":   {"rich_text": {}},
        "次のアクション":   {"rich_text": {}},
        "フォローアップ日": {"date": {}},
    },
}

r = requests.post("https://api.notion.com/v1/databases",
    headers=HEADERS, json=db_body)
r.raise_for_status()
db_id = r.json()["id"]
print(f"DB作成: {db_id}")

# ── ヘルパー ──────────────────────────────────────────────────────────────────
def rt(text):
    if not text:
        return []
    return [{"type": "text", "text": {"content": str(text)[:2000]}}]

def safe_url(text):
    if not text:
        return None
    t = str(text).strip()
    return t if t.startswith("http://") or t.startswith("https://") else None

def safe_phone(text):
    if not text:
        return None
    t = str(text).strip()
    return None if t.startswith("http") or "@" in t else t

def g(row, i):
    return row[i].strip() if i < len(row) else ""

# ── ページ投入 ────────────────────────────────────────────────────────────────
for i, row in enumerate(data):
    company  = g(row, 2)
    category = g(row, 0)

    props = {
        "会社名":         {"title": rt(company)},
        "ステータス":     {"select": {"name": "未着手"}},
        "規模・店舗数":   {"rich_text": rt(g(row, 3))},
        "主要エリア":     {"rich_text": rt(g(row, 4))},
        "本社所在地":     {"rich_text": rt(g(row, 5))},
        "SNS":            {"rich_text": rt(g(row, 10))},
        "担当者情報":     {"rich_text": rt(g(row, 11))},
        "アプローチメモ": {"rich_text": rt(g(row, 12))},
    }

    if category:
        props["カテゴリ"] = {"select": {"name": category}}

    phone = safe_phone(g(row, 6))
    if phone:
        props["電話番号"] = {"phone_number": phone}

    url_toiawase = safe_url(g(row, 7))
    if url_toiawase:
        props["卸・問合URL"] = {"url": url_toiawase}

    url_official = safe_url(g(row, 8))
    if url_official:
        props["公式URL"] = {"url": url_official}

    page_body = {
        "parent": {"database_id": db_id},
        "properties": props,
    }

    r = requests.post("https://api.notion.com/v1/pages",
        headers=HEADERS, json=page_body)
    if r.status_code != 200:
        print(f"  [{i+1:02d}] ERROR {r.status_code}: {company}")
        print("  ", r.text[:300])
    else:
        print(f"  [{i+1:02d}] OK: {company}")

    time.sleep(0.35)   # Notion API レート制限対策

print(f"\n完成！ Notion: https://www.notion.so/{db_id.replace('-','')}")
