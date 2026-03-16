"""
調査マン: 競合・参考ブランドのTwitter運用を週次で調査しTeamsに報告する。

Flow:
  Firecrawlで各ブランドの最新ツイートを収集
  → Claudeで投稿傾向・カテゴリ・戦略を分析
  → Teams Webhookに調査レポートを送信
"""

import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

PROJECT_ROOT = Path(__file__).parent.parent
TMP_DIR = PROJECT_ROOT / ".tmp"
FIRECRAWL_DIR = PROJECT_ROOT / ".firecrawl"
JST = timezone(timedelta(hours=9))
MODEL = "claude-sonnet-4-20250514"

# ── 調査対象ブランド ──────────────────────────────────────────────────────────

BRANDS = {
    "競合": [
        {"name": "ピジョン",      "handle": "pigeon_official_jp", "query": "ピジョン 育児 site:x.com"},
        {"name": "コンビ",        "handle": "combi_jp",           "query": "コンビ ベビー site:x.com"},
        {"name": "リッチェル",    "handle": "richell_jp",         "query": "リッチェル マグ site:x.com"},
        {"name": "NUKジャパン",   "handle": "nuk_japan",          "query": "NUK 赤ちゃん site:x.com"},
        {"name": "マンチキン",    "handle": "munchkin_japan",     "query": "マンチキン ベビー site:x.com"},
    ],
    "参考": [
        {"name": "アカチャンホンポ", "handle": "akachanhonpo",     "query": "アカチャンホンポ 育児 site:x.com"},
        {"name": "西松屋",          "handle": "nishimatsuya_com", "query": "西松屋 赤ちゃん site:x.com"},
        {"name": "BABYBJORN",       "handle": "babybjorn",        "query": "BabyBjorn baby site:x.com"},
    ],
}


# ── Firecrawl検索 ─────────────────────────────────────────────────────────────

def search_brand_tweets(brand: dict, limit: int = 10) -> list[dict]:
    """Firecrawlでブランドの最新ツイートを検索する。"""
    output_file = FIRECRAWL_DIR / "research_tmp.json"
    FIRECRAWL_DIR.mkdir(parents=True, exist_ok=True)

    query = brand["query"]
    cmd = f'firecrawl search "{query}" --limit {limit} -o "{output_file}" --json'

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30,
            cwd=str(PROJECT_ROOT),
        )
        if output_file.exists():
            with open(output_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            tweets = []
            for item in data.get("data", {}).get("web", []):
                url = item.get("url", "")
                if "x.com" in url and "/status/" in url:
                    tweets.append({
                        "url": url,
                        "title": item.get("title", ""),
                        "description": item.get("description", ""),
                    })
            return tweets
    except Exception as e:
        logger.warning(f"Search failed for {brand['name']}: {e}")

    return []


# ── Claude分析 ────────────────────────────────────────────────────────────────

def analyze_brand(brand: dict, tweets: list[dict]) -> str:
    """Claudeでブランドのツイート傾向を分析する。"""
    import anthropic

    if not tweets:
        return "ツイートが見つかりませんでした。"

    tweet_texts = "\n".join([
        f"- {t.get('description', t.get('title', ''))[:100]}"
        for t in tweets[:8]
    ])

    prompt = f"""以下は「{brand['name']}」(@{brand['handle']})の最近のツイートです。

{tweet_texts}

以下の観点で簡潔に分析してください（日本語、各項目1〜2行）：
1. **投稿テーマ**: どんな内容が多いか
2. **トーン**: 硬い/柔らかい、感情的/情報的など
3. **ハッシュタグ戦略**: よく使うタグのパターン
4. **グロミミへの示唆**: 参考にできる点・差別化できる点

箇条書きで簡潔に。"""

    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        resp = client.messages.create(
            model=MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()
    except Exception as e:
        logger.warning(f"Claude analysis failed for {brand['name']}: {e}")
        return "分析できませんでした。"


# ── Teams報告 ─────────────────────────────────────────────────────────────────

def send_report(results: dict) -> None:
    """調査レポートをTeamsに送信する。"""
    import requests

    webhook_url = os.getenv("TEAMS_WEBHOOK_URL") or os.getenv("TEAMS_MASTER_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("TEAMS_WEBHOOK_URL not set")
        return

    today = datetime.now(JST).strftime("%Y-%m-%d（%a）")
    lines = [f"🔍 **調査マン週次レポート** {today}\n"]

    for category, brand_results in results.items():
        lines.append(f"## {category}ブランド")
        for brand_name, data in brand_results.items():
            tweet_count = data.get("tweet_count", 0)
            analysis = data.get("analysis", "")
            lines.append(f"\n### {brand_name}（直近{tweet_count}件）")
            lines.append(analysis)
        lines.append("")

    message = "\n".join(lines)

    try:
        resp = requests.post(webhook_url, json={"text": message}, timeout=15)
        resp.raise_for_status()
        logger.info("Research report sent to Teams")
    except Exception as e:
        logger.error(f"Teams send failed: {e}")


# ── メイン ────────────────────────────────────────────────────────────────────

def run_research() -> None:
    """全ブランドを調査してTeamsに報告する。"""
    logger.info("=== 調査マン START ===")
    results = {}

    for category, brands in BRANDS.items():
        results[category] = {}
        for brand in brands:
            logger.info(f"Searching: {brand['name']}")
            tweets = search_brand_tweets(brand, limit=10)
            logger.info(f"  Found {len(tweets)} tweets")

            analysis = analyze_brand(brand, tweets)

            results[category][brand["name"]] = {
                "tweet_count": len(tweets),
                "analysis": analysis,
                "sample_urls": [t["url"] for t in tweets[:3]],
            }

            time.sleep(3)  # Firecrawl rate limit

    # ローカル保存
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(JST).strftime("%Y-%m-%d")
    out_path = TMP_DIR / f"twitter_research_{date_str}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved: {out_path}")

    send_report(results)
    logger.info("=== 調査マン DONE ===")


if __name__ == "__main__":
    run_research()
