# -*- coding: utf-8 -*-
"""
Google Sheets B2B 리서치(한국어 시트) → Notion 데이터베이스 임포트
- 모든 항목을 한국어로 기입
- 상태·우선순위·다음 액션 열 추가 (칸반 보드용)
"""
import os, sys, json, time, requests
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from google.oauth2 import service_account
from googleapiclient.discovery import build

# ── 인증 ─────────────────────────────────────────────────────────────────────
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
KR_SHEET    = "B2B 베이비 리서치"
PARENT_PAGE = "34386c6dc0468034b2a6e637bd398d41"
DB_TITLE    = "grosmimi B2B 리스트"

# ── Google Sheets 한국어 시트에서 데이터 취득 ──────────────────────────────────
result = gsvc.spreadsheets().values().get(
    spreadsheetId=SHEET_ID, range=f"'{KR_SHEET}'!A1:M100"
).execute()
rows = result.get("values", [])
data = rows[1:]   # 헤더 제외
print(f"취득: {len(data)} 사")

# ── 기존 DB 아카이브 ──────────────────────────────────────────────────────────
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
        print(f"기존 DB 삭제: {item['id']}")

# ── DB 생성 ───────────────────────────────────────────────────────────────────
CAT_COLOR = {
    "A. 대형 베이비 전문 체인": "red",
    "B. 백화점 (베이비 매장)":  "orange",
    "C. 셀렉트샵":              "blue",
    "D. EC·통신판매":           "green",
    "E. 소규모 셀렉트샵":       "purple",
    "F. 도매·디스트리뷰터":     "brown",
    "G. 기타 베이비 전문":      "gray",
}

db_body = {
    "parent": {"type": "page_id", "page_id": PARENT_PAGE},
    "title": [{"type": "text", "text": {"content": DB_TITLE}}],
    "icon": {"type": "emoji", "emoji": "🍼"},
    "properties": {
        "회사명":         {"title": {}},
        "카테고리":       {"select": {"options": [
            {"name": k, "color": v} for k, v in CAT_COLOR.items()
        ]}},
        "상태":           {"select": {"options": [
            {"name": "미착수",        "color": "gray"},
            {"name": "컨택 완료",     "color": "blue"},
            {"name": "답변 대기",     "color": "yellow"},
            {"name": "상담 중",       "color": "orange"},
            {"name": "거래 성사",     "color": "green"},
            {"name": "보류",          "color": "red"},
        ]}},
        "우선순위":       {"select": {"options": [
            {"name": "높음", "color": "red"},
            {"name": "보통", "color": "yellow"},
            {"name": "낮음", "color": "gray"},
        ]}},
        "규모·점포수":    {"rich_text": {}},
        "주요 지역":      {"rich_text": {}},
        "본사 소재지":    {"rich_text": {}},
        "전화번호":       {"phone_number": {}},
        "도매·문의처":    {"url": {}},
        "공식 URL":       {"url": {}},
        "SNS 계정":       {"rich_text": {}},
        "담당자 정보":    {"rich_text": {}},
        "어프로치 메모":  {"rich_text": {}},
        "다음 액션":      {"rich_text": {}},
        "팔로업 날짜":    {"date": {}},
    },
}

r = requests.post("https://api.notion.com/v1/databases",
    headers=HEADERS, json=db_body)
r.raise_for_status()
db_id = r.json()["id"]
print(f"DB 생성: {db_id}")

# ── 헬퍼 ─────────────────────────────────────────────────────────────────────
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

# ── 페이지 추가 ───────────────────────────────────────────────────────────────
# 한국어 시트 컬럼 순서:
# 0:카테고리 1:# 2:회사명 3:규모 4:에리어 5:본사 6:TEL 7:도매URL 8:공식URL
# 9:정보출처 10:SNS 11:담당자 12:어프로치

for i, row in enumerate(data):
    company  = g(row, 2)
    category = g(row, 0)

    props = {
        "회사명":        {"title": rt(company)},
        "상태":          {"select": {"name": "미착수"}},
        "규모·점포수":   {"rich_text": rt(g(row, 3))},
        "주요 지역":     {"rich_text": rt(g(row, 4))},
        "본사 소재지":   {"rich_text": rt(g(row, 5))},
        "SNS 계정":      {"rich_text": rt(g(row, 10))},
        "담당자 정보":   {"rich_text": rt(g(row, 11))},
        "어프로치 메모": {"rich_text": rt(g(row, 12))},
    }

    if category:
        props["카테고리"] = {"select": {"name": category}}

    phone = safe_phone(g(row, 6))
    if phone:
        props["전화번호"] = {"phone_number": phone}

    url_toiawase = safe_url(g(row, 7))
    if url_toiawase:
        props["도매·문의처"] = {"url": url_toiawase}

    url_official = safe_url(g(row, 8))
    if url_official:
        props["공식 URL"] = {"url": url_official}

    r = requests.post("https://api.notion.com/v1/pages",
        headers=HEADERS,
        json={"parent": {"database_id": db_id}, "properties": props},
    )
    if r.status_code != 200:
        print(f"  [{i+1:02d}] ERROR {r.status_code}: {company}")
        print("  ", r.text[:300])
    else:
        print(f"  [{i+1:02d}] OK: {company}")

    time.sleep(0.35)

print(f"\n완성！ Notion: https://www.notion.so/{db_id.replace('-', '')}")
