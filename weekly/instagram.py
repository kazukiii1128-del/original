#!/usr/bin/env python3
"""
Instagram Graph API helper — Kazuki Japan Team
- 토큰 유효기간 확인 및 자동 갱신 (2주 미만 시)
- 팔로워 수 조회
- 주간 게시물 및 Top Post 자동 수집
- 팔로워 이력 로그 기록
"""

import json
import time
from datetime import datetime, timedelta, date as date_cls, timezone
from pathlib import Path
from typing import Optional

BASE_DIR      = Path(__file__).parent
CONFIG_PATH   = BASE_DIR / "config.json"
FOLLOWER_LOG  = BASE_DIR / "log" / "grosmimi_jp_instagram_fw_log.md"
GRAPH_BASE    = "https://graph.facebook.com/v22.0"


# ── Config I/O ────────────────────────────────────────────────────────────────
def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


# ── Token 관리 ─────────────────────────────────────────────────────────────────
def check_token_expiry(token: str, app_id: str, app_secret: str) -> float:
    """토큰 남은 유효기간(일) 반환. 만료 없으면 9999.
    access_token으로 토큰 자체를 사용 (app_id|app_secret 조합이 실패할 경우 대비)."""
    import requests
    # 1차: 토큰 자체를 access_token으로 사용 (앱이 달라도 동작)
    resp = requests.get(
        f"{GRAPH_BASE}/debug_token",
        params={"input_token": token, "access_token": token},
    )
    if not resp.ok:
        # 2차: app_id|app_secret 방식 재시도
        resp = requests.get(
            f"{GRAPH_BASE}/debug_token",
            params={"input_token": token, "access_token": f"{app_id}|{app_secret}"},
        )
        resp.raise_for_status()
    data = resp.json().get("data", {})
    # PAGE 토큰은 영구적 — 갱신 불필요
    if data.get("type") == "PAGE":
        return 9999.0
    expires_at = data.get("expires_at", 0)
    if not expires_at:
        return 9999.0
    return max(0.0, (expires_at - time.time()) / 86400)


def refresh_long_lived_token(token: str, app_id: str, app_secret: str) -> str:
    """장기 토큰으로 갱신 (60일 연장)"""
    import requests
    resp = requests.get(
        "https://graph.facebook.com/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": token,
        },
    )
    resp.raise_for_status()
    new_token = resp.json().get("access_token")
    if not new_token:
        raise RuntimeError(f"토큰 갱신 실패: {resp.json()}")
    return new_token


# ── IG User ID 자동 감지 ───────────────────────────────────────────────────────
def detect_ig_user_id(token: str) -> str:
    """Facebook Page → Instagram Business Account ID 자동 감지"""
    import requests

    # 1. Facebook Page 목록 조회
    resp = requests.get(
        f"{GRAPH_BASE}/me/accounts",
        params={"access_token": token},
    )
    resp.raise_for_status()
    pages = resp.json().get("data", [])

    for page in pages:
        r = requests.get(
            f"{GRAPH_BASE}/{page['id']}",
            params={"fields": "instagram_business_account", "access_token": token},
        )
        ig = r.json().get("instagram_business_account")
        if ig:
            return ig["id"]

    raise RuntimeError(
        "Instagram Business Account를 찾을 수 없습니다.\n"
        "Facebook Page에 Instagram 계정이 연결되어 있는지 확인하세요."
    )


# ── 팔로워 수 조회 ─────────────────────────────────────────────────────────────
def get_followers(ig_user_id: str, token: str) -> int:
    import requests
    resp = requests.get(
        f"{GRAPH_BASE}/{ig_user_id}",
        params={"fields": "followers_count", "access_token": token},
    )
    resp.raise_for_status()
    return int(resp.json().get("followers_count", 0))


# ── 주간 게시물 조회 ───────────────────────────────────────────────────────────
def get_weekly_media(ig_user_id: str, token: str,
                     start: date_cls, end: date_cls) -> list:
    """start ~ end 기간(포함) 게시물 반환. like_count, comments_count 포함."""
    import requests

    results = []
    url = f"{GRAPH_BASE}/{ig_user_id}/media"
    params = {
        "fields": "id,timestamp,like_count,comments_count,permalink,media_type",
        "limit": 50,
        "access_token": token,
    }

    while url:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("data", []):
            ts_str = item.get("timestamp", "")
            if not ts_str:
                continue
            ts_str = ts_str.replace("Z", "+00:00")
            # Python 3.9: +0000 형식 → +00:00 으로 정규화
            if len(ts_str) > 5 and ts_str[-5] in ('+', '-') and ':' not in ts_str[-5:]:
                ts_str = ts_str[:-2] + ':' + ts_str[-2:]
            ts = datetime.fromisoformat(ts_str)
            post_date = ts.astimezone(timezone.utc).date()

            if post_date < start:
                return results  # 조회 범위 이전 → 중단
            if start <= post_date <= end:
                results.append(item)

        next_url = data.get("paging", {}).get("next")
        url = next_url
        params = {}  # next URL에 파라미터 포함됨

    return results


def get_top_post(media_list: list) -> Optional[dict]:
    """좋아요 + 댓글 수 합계가 가장 높은 게시물 반환"""
    if not media_list:
        return None
    return max(
        media_list,
        key=lambda p: p.get("like_count", 0) + p.get("comments_count", 0),
    )


# ── 팔로워 로그 기록 ───────────────────────────────────────────────────────────
def append_follower_log(followers: int, date_str: str) -> Optional[int]:
    """팔로워 수를 로그에 추가. 직전 기록 팔로워 수 반환."""
    FOLLOWER_LOG.parent.mkdir(parents=True, exist_ok=True)

    if FOLLOWER_LOG.exists():
        content = FOLLOWER_LOG.read_text(encoding="utf-8")
    else:
        content = (
            "# Grosmimi JP Instagram 팔로워 로그\n\n"
            "| Date | Followers | Change |\n"
            "|------|-----------|--------|\n"
        )

    # 마지막 팔로워 수 파싱
    prev_count = None
    for line in content.splitlines():
        if line.startswith("|") and "Date" not in line and "---" not in line:
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 2:
                try:
                    prev_count = int(cols[1].replace(",", ""))
                except ValueError:
                    pass

    if prev_count is not None:
        diff = followers - prev_count
        change = f"+{diff}" if diff >= 0 else str(diff)
    else:
        change = "N/A"

    content += f"| {date_str} | {followers:,} | {change} |\n"
    FOLLOWER_LOG.write_text(content, encoding="utf-8")
    return prev_count


# ── 메인 진입점 ────────────────────────────────────────────────────────────────
def fetch_instagram_data(cfg: dict, this_monday: date_cls) -> dict:
    """
    토큰 관리 → IG 데이터 수집 → 팔로워 로그 기록
    반환값: {followers, prev_followers, weekly_posts, top_post}
    """
    ig = cfg.get("instagram", {})
    token     = ig.get("access_token", "")
    app_id    = ig.get("app_id", "")
    app_secret = ig.get("app_secret", "")

    if not token:
        raise RuntimeError("config.json 에 instagram.access_token 이 없습니다.")

    # 1. 토큰 유효기간 확인 및 갱신
    print("[Instagram] 토큰 유효기간 확인 중...")
    days_left = check_token_expiry(token, app_id, app_secret)
    print(f"[Instagram] 토큰 유효기간: {days_left:.0f}일 남음")

    if days_left < 14:
        print("[Instagram] 토큰 갱신 중 (60일 연장)...")
        token = refresh_long_lived_token(token, app_id, app_secret)
        ig["access_token"] = token
        cfg["instagram"] = ig
        save_config(cfg)
        print("[Instagram] 토큰 갱신 완료 → config.json 저장됨")

    # 2. IG User ID 확인 (없으면 자동 감지)
    ig_user_id = ig.get("ig_user_id", "")
    if not ig_user_id:
        print("[Instagram] Instagram User ID 자동 감지 중...")
        ig_user_id = detect_ig_user_id(token)
        ig["ig_user_id"] = ig_user_id
        cfg["instagram"] = ig
        save_config(cfg)
        print(f"[Instagram] IG User ID 저장됨: {ig_user_id}")

    # 3. 팔로워 수 조회
    followers = get_followers(ig_user_id, token)
    print(f"[Instagram] 팔로워: {followers:,}")

    # 4. 팔로워 로그 기록
    date_str = this_monday.strftime("%Y-%m-%d")
    prev_followers = append_follower_log(followers, date_str)
    print(f"[Instagram] 팔로워 로그 기록 완료 ({FOLLOWER_LOG.name})")

    # 5. 지난주 월~금 게시물 조회
    last_monday = this_monday - timedelta(days=7)
    last_friday = last_monday + timedelta(days=4)
    print(f"[Instagram] {last_monday} ~ {last_friday} 게시물 조회 중...")
    weekly_posts = get_weekly_media(ig_user_id, token, last_monday, last_friday)
    top_post = get_top_post(weekly_posts)
    print(f"[Instagram] 게시물 {len(weekly_posts)}개 발견")

    return {
        "followers": followers,
        "prev_followers": prev_followers,
        "weekly_posts": weekly_posts,
        "top_post": top_post,
    }
