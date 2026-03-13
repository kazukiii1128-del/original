#!/usr/bin/env python3
"""
Kazuki Japan Team — Weekly Report Generator
- 매주 월요일 09:00 KST 자동 실행 (launchd)
- Instagram 팔로워/게시물 자동 수집
- work_log/ 의 이번 주 업무 로그와 합산하여 Notion 위클리 리포트 생성
- 실행: python generate_weekly.py [--date YYYY-MM-DD] [--force]
"""

import json
import re
import sys
from datetime import datetime, timedelta, date as date_cls
from pathlib import Path
from typing import Optional

BASE_DIR      = Path(__file__).parent
WORK_LOG_DIR  = BASE_DIR / "work_log"
REPORT_DIR    = BASE_DIR / "reports"
TEMPLATE_PATH = BASE_DIR / "notion_template.md"
CONFIG_PATH   = BASE_DIR / "config.json"
SCRIPT_LOG    = BASE_DIR / "kazuki.log"


# ── Logging ───────────────────────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)


# ── 날짜 ──────────────────────────────────────────────────────────────────────
def get_this_monday() -> date_cls:
    today = date_cls.today()
    return today - timedelta(days=today.weekday())


# ── Config ────────────────────────────────────────────────────────────────────
def load_config() -> dict:
    if not CONFIG_PATH.exists():
        log(f"[ERROR] config.json 없음: {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    if cfg["notion"]["weekly_report_db_id"] == "YOUR_NOTION_DB_ID":
        log("[ERROR] config.json 의 notion.weekly_report_db_id 를 설정하세요.")
        sys.exit(1)
    return cfg


# ── OKR 파싱 ──────────────────────────────────────────────────────────────────
def parse_okr(work_content: str) -> dict:
    """work_log 의 ## OKR_UPDATE 섹션에서 key=value 추출"""
    okr = {}
    m = re.search(r"##\s*OKR_UPDATE\s*\n(.*?)(?=\n##|\Z)", work_content, re.DOTALL)
    if not m:
        return okr
    for line in m.group(1).splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            okr[k.strip()] = v.strip()
    return okr


def calc_progress(val: str, target: int) -> tuple[str, str]:
    try:
        v = float(str(val).replace(",", ""))
        pct = v / target * 100
        emoji = "🟢" if pct >= 70 else ("🟡" if pct >= 30 else "🔴")
        return f"{pct:.1f}%", emoji
    except (ValueError, ZeroDivisionError):
        return "N/A", "🔴"


def build_okr_table(okr: dict, ig_followers: Optional[int]) -> str:
    targets = {"new_skus": 10, "contents": 300, "reviews": 100, "ig_followers": 10000}
    labels  = {
        "new_skus":     "New SKUs PREP",
        "contents":     "Produce 300 contents",
        "reviews":      "Build 100 reviews on Rakuten",
        "ig_followers": "Achieve 10,000 IG Followers",
    }

    # IG 팔로워는 Instagram API에서 가져온 값 우선 사용
    if ig_followers is not None:
        okr["ig_followers_this"] = str(ig_followers)

    rows = [
        "| Key Result | Target | Last Week | This Week | Progress | Status |",
        "|------------|--------|-----------|-----------|----------|--------|",
    ]
    for key, label in labels.items():
        last = okr.get(f"{key}_last", "N/A")
        this = okr.get(f"{key}_this", "N/A")
        pct, emoji = calc_progress(this, targets[key])
        rows.append(f"| {label} | {targets[key]:,} | {last} | {this} | {pct} | {emoji} |")

    return "\n".join(rows)


def build_instagram_section(ig_data: dict, okr: dict) -> str:
    followers      = ig_data.get("followers", "N/A")
    prev_followers = ig_data.get("prev_followers")
    weekly_posts   = ig_data.get("weekly_posts", [])
    top_post       = ig_data.get("top_post")

    if prev_followers is not None:
        diff = followers - prev_followers
        delta_str = f"+{diff}" if diff >= 0 else str(diff)
    else:
        # prev from OKR manual input as fallback
        prev_manual = okr.get("ig_followers_last")
        try:
            diff = followers - int(str(prev_manual).replace(",", ""))
            delta_str = f"+{diff}" if diff >= 0 else str(diff)
        except (TypeError, ValueError):
            delta_str = "N/A"

    followers_str = f"{followers:,}" if isinstance(followers, int) else str(followers)
    lines = [f"- Followers: [{followers_str}] ({delta_str} from last week)"]

    for post in weekly_posts:
        url = post.get("permalink", "")
        if url:
            lines.append(f"- Posts: [{url}]")

    if top_post:
        url   = top_post.get("permalink", "N/A")
        likes = top_post.get("like_count", 0)
        cmts  = top_post.get("comments_count", 0)
        lines.append(f"- Top Post: [{url}] - [{likes}] likes, [{cmts}] comments")

    return "\n".join(lines)


# ── Rich text / Markdown → Notion blocks ─────────────────────────────────────
def parse_rich_text(text: str) -> list:
    parts = []
    pattern = re.compile(r"\*\*(.+?)\*\*|\[(https?://[^\]]+)\]")
    last = 0
    for m in pattern.finditer(text):
        if m.start() > last:
            parts.append({"type": "text", "text": {"content": text[last:m.start()]}})
        if m.group(1) is not None:  # **bold**
            parts.append({
                "type": "text",
                "text": {"content": m.group(1)},
                "annotations": {"bold": True},
            })
        else:  # [https://...]
            url = m.group(2)
            parts.append({
                "type": "text",
                "text": {"content": url, "link": {"url": url}},
            })
        last = m.end()
    if last < len(text):
        parts.append({"type": "text", "text": {"content": text[last:]}})
    return parts if parts else [{"type": "text", "text": {"content": text}}]


def markdown_to_notion_blocks(md: str) -> list:
    blocks = []
    lines = md.split("\n")
    i = 0

    while i < len(lines):
        s = lines[i].rstrip().strip()
        if not s:
            i += 1
            continue

        if s.startswith("#### "):
            blocks.append({"object": "block", "type": "heading_3",
                           "heading_3": {"rich_text": parse_rich_text(s[5:])}})
        elif s.startswith("### "):
            blocks.append({"object": "block", "type": "heading_3",
                           "heading_3": {"rich_text": parse_rich_text(s[4:])}})
        elif s.startswith("## "):
            blocks.append({"object": "block", "type": "heading_2",
                           "heading_2": {"rich_text": parse_rich_text(s[3:])}})
        elif s.startswith("# "):
            blocks.append({"object": "block", "type": "heading_1",
                           "heading_1": {"rich_text": parse_rich_text(s[2:])}})
        elif s == "---":
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        elif s.startswith("[ ] ") or s == "[ ]":
            text = s[4:] if s.startswith("[ ] ") else ""
            blocks.append({"object": "block", "type": "to_do",
                           "to_do": {"rich_text": parse_rich_text(text), "checked": False}})
        elif s.startswith("[x] ") or s.startswith("[X] "):
            text = s[4:]
            blocks.append({"object": "block", "type": "to_do",
                           "to_do": {"rich_text": parse_rich_text(text), "checked": True}})
        elif s.startswith("> "):
            blocks.append({"object": "block", "type": "quote",
                           "quote": {"rich_text": parse_rich_text(s[2:])}})
        elif s.startswith("```"):
            lang = s[3:].strip() or "plain text"
            code_lines, i = [], i + 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            blocks.append({
                "object": "block", "type": "code",
                "code": {
                    "rich_text": [{"type": "text", "text": {"content": "\n".join(code_lines)[:2000]}}],
                    "language": lang,
                },
            })
        elif s.startswith("|"):
            raw_rows, j = [], i
            while j < len(lines) and lines[j].strip().startswith("|"):
                raw_rows.append(lines[j].strip())
                j += 1
            content_rows = [r for r in raw_rows if not re.match(r"^\|[-:| ]+\|$", r)]
            if content_rows:
                parsed = [[c.strip() for c in r.strip("|").split("|")] for r in content_rows]
                max_cols = max(len(r) for r in parsed)
                for row in parsed:
                    while len(row) < max_cols:
                        row.append("")
                blocks.append({
                    "object": "block", "type": "table",
                    "table": {
                        "table_width": max_cols,
                        "has_column_header": True,
                        "has_row_header": False,
                        "children": [{
                            "object": "block", "type": "table_row",
                            "table_row": {"cells": [parse_rich_text(c) for c in row]},
                        } for row in parsed],
                    },
                })
            i = j
            continue
        elif s.startswith("- "):
            text, children, j = s[2:], [], i + 1
            while j < len(lines):
                nl = lines[j]
                indent = len(nl) - len(nl.lstrip())
                ns = nl.strip()
                if indent >= 4 and ns.startswith("- "):
                    children.append({
                        "object": "block", "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": parse_rich_text(ns[2:])},
                    })
                    j += 1
                elif indent >= 4 and ns:
                    children.append({
                        "object": "block", "type": "paragraph",
                        "paragraph": {"rich_text": parse_rich_text(ns)},
                    })
                    j += 1
                else:
                    break
            block = {
                "object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": parse_rich_text(text)},
            }
            if children:
                block["bulleted_list_item"]["children"] = children
            blocks.append(block)
            i = j
            continue
        elif re.match(r"^\d+\.", s):
            text = re.sub(r"^\d+\.\s*", "", s)
            children, j = [], i + 1
            while j < len(lines):
                nl = lines[j]
                indent = len(nl) - len(nl.lstrip())
                ns = nl.strip()
                if indent >= 2 and ns:
                    content = ns[2:] if ns.startswith(("- ", "◦ ")) else ns
                    children.append({
                        "object": "block", "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": parse_rich_text(content)},
                    })
                    j += 1
                else:
                    break
            block = {
                "object": "block", "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": parse_rich_text(text)},
            }
            if children:
                block["numbered_list_item"]["children"] = children
            blocks.append(block)
            i = j
            continue
        else:
            blocks.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": parse_rich_text(s)},
            })
        i += 1

    return blocks


# ── Instagram 북마크 주입 ────────────────────────────────────────────────────
_IG_URL_RE = re.compile(r"https://www\.instagram\.com/p/[A-Za-z0-9_-]+/?")


def inject_instagram_bookmarks(blocks: list) -> list:
    """Instagram 포스트 URL이 포함된 불릿 블록 뒤에 bookmark 블록 삽입"""
    result = []
    for block in blocks:
        result.append(block)
        if block.get("type") == "bulleted_list_item":
            for rt in block.get("bulleted_list_item", {}).get("rich_text", []):
                url = rt.get("text", {}).get("link", {}).get("url", "")
                if not url:
                    url = rt.get("text", {}).get("content", "")
                m = _IG_URL_RE.search(url)
                if m:
                    result.append({
                        "object": "block",
                        "type": "bookmark",
                        "bookmark": {"url": m.group(0)},
                    })
                    break
    return result


# ── Claude 리포트 생성 ─────────────────────────────────────────────────────────
def generate_report(api_key: str, template: str, work_content: str,
                    okr_table: str, instagram_section: str, week_label: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""당신은 Japan 팀 위클리 리포트 작성 전문가입니다.
아래 업무 로그와 데이터를 분석하여 Notion 위클리 리포트를 완성해주세요.

## 노션 템플릿 구조
{template}

---

## 업무 로그 (이번 주 작업 내용)
{work_content}

---

## 작성 지침
1. 노션 템플릿의 구조와 섹션 순서를 정확히 따르세요.
2. **언어**: 섹션 제목/소제목/레이블(Followers, Posts, Challenge, Impact, Status 등)은 **영문 그대로** 유지. 실제 내용(성과 설명, 도전 과제 내용, 배움, 계획 등)은 **한국어**로 작성.
3. **서식**: 코드 블록(```)을 절대 사용하지 마세요. 불릿 리스트(`- `), 번호 목록(`1. `), 일반 텍스트를 사용하세요.
4. **Section 1**: 반드시 아래 한국어 5개 항목을 그대로 사용:
   - 목표 SKU 전체 수출 준비 완료 상태 달성
   - 300개 콘텐츠 제작 (형식 무관)
   - 라쿠텐 리뷰 100개 달성
   - 인스타그램 팔로워 10,000명 달성
   - 라쿠텐 슈퍼 로지스틱스(RSL)로 전환
5. **Section 2 (OKRs)**: 아래 사전 계산된 OKR 테이블과 Instagram 데이터를 그대로 사용. 임의로 숫자를 바꾸지 마세요.
6. **Section 3 (Challenges)**: 업무 로그의 challenges 에서 추출. 반드시 Challenges & Obstacles → Blockers (체크박스) → Resource Needs 순서로 작성.
   - Blockers: 없으면 `[ ] None`
   - Resource Needs: 없으면 `- None`
7. **Section 4 (Learnings)**: 업무 로그의 problems solved / learnings 에서 추출
8. **Section 5 (Next Week)**: 업무 로그의 next week 계획에서 추출. Top Priorities는 번호 목록, 체크박스 항목은 `[ ] ` 형식.
9. 기준 주차: {week_label}

## OKR 테이블 (그대로 사용)
{okr_table}

## Instagram 데이터 (그대로 사용)
{instagram_section}

"Team: JAPAN" 줄부터 시작하여 리포트 전체를 마크다운으로 완성하여 출력하세요. 앞에 제목이나 설명을 추가하지 마세요.
"""

    log("Claude API로 리포트 생성 중...")
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


# ── Notion 업로드 ─────────────────────────────────────────────────────────────
def create_notion_page(cfg: dict, title: str, report_date: str, blocks: list) -> str:
    import requests

    n = cfg["notion"]
    headers = {
        "Authorization": f"Bearer {n['api_token']}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    properties = {
        "Report File": {"title": [{"type": "text", "text": {"content": title}}]},
        "Report Date": {"date": {"start": report_date}},
    }

    resp = requests.post(
        "https://api.notion.com/v1/pages",
        headers=headers,
        json={"parent": {"database_id": n["weekly_report_db_id"]}, "properties": properties},
    )
    resp.raise_for_status()
    page_id  = resp.json()["id"]
    page_url = resp.json().get("url", "")
    log(f"Notion 페이지 생성됨: {page_id}")

    for start in range(0, len(blocks), 100):
        batch = blocks[start:start + 100]
        r = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=headers,
            json={"children": batch},
        )
        if r.status_code != 200:
            log(f"[WARN] 블록 업로드 실패 ({start}~{start+len(batch)-1}): {r.text[:200]}")
        else:
            log(f"블록 업로드 완료: {start}~{start+len(batch)-1}")

    return page_url


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date",  help="날짜 override (YYYY-MM-DD). 기본: 이번 주 월요일")
    parser.add_argument("--force", action="store_true", help="이미 리포트가 있어도 재생성")
    args = parser.parse_args()

    log("=" * 60)
    log("Kazuki Japan Team 위클리 리포트 생성 시작")

    if args.date:
        this_monday = datetime.strptime(args.date, "%Y-%m-%d").date()
        log(f"날짜 override: {args.date}")
    else:
        this_monday = get_this_monday()

    # 월요일이 아니면 경고 후 다음 월요일 시도 안내
    if this_monday.weekday() != 0:
        log(f"[WARN] 오늘은 월요일이 아닙니다. 기준 월요일: {this_monday}")

    date_str    = this_monday.strftime("%Y_%m_%d")
    date_dash   = this_monday.strftime("%Y-%m-%d")
    week_label  = this_monday.strftime("%m/%d/%Y")
    week_number = this_monday.isocalendar()[1]
    page_title  = "JP Weekly Report Template-Kazuki"

    log(f"기준 월요일: {date_dash}")

    # 이미 생성된 리포트 확인
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"weekly_{date_str}.md"
    if report_path.exists() and not args.force:
        log(f"이미 존재: {report_path.name} - 건너뜁니다. (재생성: --force)")
        log("=" * 60)
        return

    # work_log 파일 확인
    work_log_path = WORK_LOG_DIR / f"work_{date_str}_log.md"
    if not work_log_path.exists():
        log(f"[ERROR] work_log 파일 없음: {work_log_path.name}")
        log("work_log/work_log_template.md 를 복사·작성 후 다시 실행하세요.")
        log("=" * 60)
        sys.exit(1)

    log(f"Work 로그: {work_log_path.name}")
    cfg = load_config()

    # ── Instagram 데이터 수집 ──────────────────────────────────────────────────
    ig_data = {}
    try:
        from instagram import fetch_instagram_data
        ig_data = fetch_instagram_data(cfg, this_monday)
    except Exception as e:
        log(f"[WARN] Instagram 수집 실패 (수동 입력 값으로 진행): {e}")

    # ── 리포트 생성 ────────────────────────────────────────────────────────────
    template     = TEMPLATE_PATH.read_text(encoding="utf-8")
    work_content = work_log_path.read_text(encoding="utf-8")
    okr          = parse_okr(work_content)

    ig_followers = ig_data.get("followers")
    okr_table         = build_okr_table(okr, ig_followers)
    instagram_section = build_instagram_section(ig_data, okr)
    log(f"OKR 파싱: {len(okr)}개 항목 / IG 팔로워: {ig_followers}")

    try:
        report_md = generate_report(
            cfg["anthropic"]["api_key"],
            template, work_content,
            okr_table, instagram_section, week_label,
        )
    except Exception as e:
        log(f"[ERROR] Claude 리포트 생성 실패: {e}")
        sys.exit(1)

    # 로컬 저장
    report_path.write_text(report_md, encoding="utf-8")
    log(f"리포트 저장: {report_path}")

    # Notion 업로드
    try:
        blocks = markdown_to_notion_blocks(report_md)
        blocks = inject_instagram_bookmarks(blocks)
        log(f"블록 수: {len(blocks)}")
        url = create_notion_page(cfg, page_title, date_dash, blocks)
        log(f"Notion 업로드 완료: {url}")
    except Exception as e:
        log(f"[ERROR] Notion 업로드 실패: {e}")
        log("로컬 파일은 저장되었습니다.")

    log("완료")
    log("=" * 60)


if __name__ == "__main__":
    main()
