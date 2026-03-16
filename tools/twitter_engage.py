"""
WAT Tool: Twitter/X Community Engagement via Firecrawl + API.
Finds relevant parenting tweets via web search, generates contextual replies,
and posts them via Twitter API (Free tier workaround).

Flow: Firecrawl search → extract tweet IDs → Claude generates reply → API posts reply

Usage:
    py -3 tools/twitter_engage.py                          # find & reply to parenting tweets
    py -3 tools/twitter_engage.py --query "ストローマグ"     # custom search query
    py -3 tools/twitter_engage.py --limit 5                 # max replies per session
    py -3 tools/twitter_engage.py --dry-run                 # preview without posting
    py -3 tools/twitter_engage.py --history                 # show reply history

Output: .tmp/twitter_engage_log.json
"""

import os
import sys
import json
import re
import time
import argparse
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

from twitter_utils import (
    create_twitter_clients,
    validate_tweet_text,
    count_weighted_chars,
    TMP_DIR,
    PROJECT_ROOT,
)

# ── Constants ────────────────────────────────────────────────────────────

JST = timezone(timedelta(hours=9))
ENGAGE_LOG_PATH = TMP_DIR / "twitter_engage_log.json"
FIRECRAWL_DIR = PROJECT_ROOT / ".firecrawl"
DAILY_REPLY_LIMIT = 10  # max replies per day
MODEL = "claude-sonnet-4-20250514"
MIN_FOLLOWERS = 100  # minimum follower count

# Competitor / brand accounts to skip (lowercase)
BLOCKED_ACCOUNTS = {
    "pigeon", "pigeon_jp", "combi_jp", "combi", "richell_jp", "richell",
    "nuk_japan", "nuk", "boon_jp", "munchkin_japan", "munchkin",
    "thermos_jp", "thermos", "zojirushi", "tiger_jp", "skater_jp",
    "babybjorn", "ergobaby", "aprica", "aprica_jp", "leapfrog",
    "fisherprice", "graco_jp", "joie_jp", "cybex_jp",
    "grosmimi", "grosmimi_jp", "grosmimi_japan",
}

# Search queries to find relevant tweets (rotated)
DEFAULT_QUERIES = [
    "ストローマグ 育児 site:x.com",
    "ストローマグ 漏れる site:x.com",
    "赤ちゃん マグ おすすめ site:x.com",
    "離乳食 ストロー 練習 site:x.com",
    "育児あるある マグ site:x.com",
    "ストローマグ いつから site:x.com",
    "PPSU マグ site:x.com",
    "育児グッズ おすすめ ストロー site:x.com",
]

# ── Reply Persona Prompt ─────────────────────────────────────────────────

REPLY_SYSTEM_PROMPT = """あなたはグロミミ（Grosmimi）ジャパンの公式Twitter/X中の人です。
他のママのツイートに返信します。

## ペルソナ
- 1歳10ヶ月の女の子のママ。韓国出身、グロミミで開発者として働いてる
- 温かくて共感力が高い。同じママとして話す
- 相手のツイートの内容に本当に共感して返信する

## 返信ルール（超重要）
1. 絶対に宣伝しない。製品名を出さない。リンクを貼らない
2. 同じママとして共感する返信だけ
3. 短く（50〜80文字くらい）
4. 絵文字は1個まで
5. ハッシュタグなし（返信にタグは不自然）
6. 「うちも」「わかります」「同じです」系の共感ワード必須

## 良い返信例
- "わかります〜！うちも最初全然飲んでくれなくて😂 でもある日急にできるようになりますよ！"
- "うちもです！カバンの中びしょびしょ事件、何回やったことか…"
- "それ最高ですね！子どもが自分で飲める瞬間、感動しますよね✨"

## ダメな返信例
- "グロミミのマグなら漏れませんよ！" ← 宣伝。絶対NG
- "プロフィールのリンクから見てください" ← 営業。絶対NG
- "おすすめです！" ← 押し売り。絶対NG

返信テキストだけを出力してください。「」や引用符は不要です。"""


# ── Helper Functions ─────────────────────────────────────────────────────

def extract_tweet_ids(search_results: dict) -> list[dict]:
    """Extract tweet IDs and metadata from Firecrawl search results."""
    tweets = []
    seen_ids = set()

    for item in search_results.get("data", {}).get("web", []):
        url = item.get("url", "")
        # Match x.com/username/status/tweet_id pattern
        match = re.search(r'x\.com/(\w+)/status/(\d+)', url)
        if match:
            username = match.group(1)
            tweet_id = match.group(2)
            if tweet_id not in seen_ids:
                seen_ids.add(tweet_id)
                tweets.append({
                    "tweet_id": tweet_id,
                    "username": username,
                    "url": url,
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                })

    return tweets


def load_engage_log() -> dict:
    """Load engagement log."""
    if ENGAGE_LOG_PATH.exists():
        with open(ENGAGE_LOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"replies": []}


def save_engage_log(log: dict) -> None:
    """Save engagement log."""
    ENGAGE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ENGAGE_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def get_today_reply_count() -> int:
    """Count replies posted today."""
    log = load_engage_log()
    today = datetime.now(JST).strftime("%Y-%m-%d")
    return sum(
        1 for r in log.get("replies", [])
        if r.get("replied_at", "").startswith(today)
    )


def get_replied_tweet_ids() -> set[str]:
    """Get set of tweet IDs we've already replied to."""
    log = load_engage_log()
    return {r.get("target_tweet_id") for r in log.get("replies", [])}


def get_replied_usernames() -> set[str]:
    """Get set of usernames we've already replied to (don't repeat)."""
    log = load_engage_log()
    return {r.get("target_username", "").lower() for r in log.get("replies", [])}


def get_user_info(api, username: str, tweet_info: dict = None) -> dict | None:
    """Build user info from available search data (Free tier: user lookup API not available)."""
    tweet_info = tweet_info or {}
    return {
        "username": username,
        "name": username,
        "description": tweet_info.get("description", "") or tweet_info.get("title", ""),
        "followers": MIN_FOLLOWERS,  # assume OK — follower check not available on Free tier
    }


def is_likely_female_japanese(user_info: dict) -> bool:
    """Use Claude to judge if the account is likely a Japanese female user."""
    import anthropic
    name = user_info.get("name", "")
    bio = user_info.get("description", "")
    username = user_info.get("username", "")

    prompt = f"""以下のTwitterアカウントが「日本人女性（ママ含む）」かどうか判定してください。
名前: {name}
ユーザー名: @{username}
プロフィール: {bio}

判定基準:
- 女性らしい名前・プロフィール → YES
- 男性名・男性っぽい → NO
- 企業・ブランド・bot → NO
- 不明・中性的 → YES（疑わしい場合は送る）

YESまたはNOだけ答えてください。"""

    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        resp = client.messages.create(
            model=MODEL,
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = resp.content[0].text.strip().upper()
        return "NO" not in answer
    except Exception:
        return True  # 判定できない場合は送る


def should_engage(user_info: dict, replied_usernames: set[str]) -> tuple[bool, str]:
    """エンゲージするかどうかを判定する。理由も返す。"""
    username = user_info.get("username", "").lower()
    followers = user_info.get("followers", 0)

    # 同じ人に送らない
    if username in replied_usernames:
        return False, "already replied"

    # 競合・自社アカウントはスキップ
    if username in BLOCKED_ACCOUNTS:
        return False, "blocked account"

    # フォロワー100人未満はスキップ
    if followers < MIN_FOLLOWERS:
        return False, f"too few followers ({followers})"

    # 男性・企業はスキップ
    if not is_likely_female_japanese(user_info):
        return False, "not female/Japanese"

    return True, "ok"


def search_tweets(query: str) -> list[dict]:
    """Search for tweets using Firecrawl."""
    output_file = FIRECRAWL_DIR / "engage_search_tmp.json"
    FIRECRAWL_DIR.mkdir(parents=True, exist_ok=True)

    cmd = f'firecrawl search "{query}" --limit 10 -o "{output_file}" --json'
    logger.info(f"Searching: {query}")

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30,
            cwd=str(PROJECT_ROOT),
        )
        if output_file.exists():
            with open(output_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return extract_tweet_ids(data)
    except Exception as e:
        logger.error(f"Search failed: {e}")

    return []


def generate_reply(tweet_info: dict) -> str | None:
    """Generate a contextual reply using Claude."""
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not found")
        return None

    tweet_context = f"""相手のツイート:
@{tweet_info['username']}
「{tweet_info.get('description', tweet_info.get('title', ''))}」

このツイートに対して、同じママとして共感する短い返信を1つ作成してください。
宣伝は絶対にしないでください。製品名も出さないでください。"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=200,
            system=REPLY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": tweet_context}],
        )
        reply = response.content[0].text.strip()

        # Clean up quotes
        if reply.startswith('"') and reply.endswith('"'):
            reply = reply[1:-1]
        if reply.startswith("「") and reply.endswith("」"):
            reply = reply[1:-1]

        # Validate length
        is_valid, msg = validate_tweet_text(reply)
        if not is_valid:
            logger.warning(f"Reply too long: {msg}")
            return None

        return reply

    except Exception as e:
        logger.error(f"Reply generation failed: {e}")
        return None


def translate_to_korean(text: str) -> str:
    """Quick Korean translation for operator."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=MODEL,
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": f"다음 일본어를 한국어로 번역. 번역만 출력:\n{text}"
            }],
        )
        return response.content[0].text.strip()
    except Exception:
        return "(번역 불가)"


def notify_supervisor(tweet_info: dict, reply_text: str, reply_url: str) -> None:
    """コメント投稿をTeamsに報告する（監督係）。"""
    import requests

    webhook_url = os.getenv("TEAMS_WEBHOOK_URL") or os.getenv("TEAMS_MASTER_WEBHOOK_URL")
    if not webhook_url:
        return

    now = datetime.now(JST).strftime("%H:%M")
    target_url = tweet_info.get("url", "")
    target_text = (tweet_info.get("description", "") or tweet_info.get("title", ""))[:80]
    username = tweet_info.get("username", "")

    message = (
        f"💬 **コメンター報告** {now} JST\n\n"
        f"**送信先:** [@{username}]({target_url})\n"
        f"> {target_text}\n\n"
        f"**送ったコメント:**\n> {reply_text}\n\n"
        f"[投稿を確認]({reply_url})"
    )

    try:
        requests.post(webhook_url, json={"text": message}, timeout=10)
        logger.info("Supervisor notified via Teams")
    except Exception as e:
        logger.warning(f"Teams notify failed: {e}")


def post_reply(tweet_id: str, reply_text: str, username: str = "", dry_run: bool = False) -> dict:
    """Post engagement to a tweet. Tries reply → mention fallback.

    Strategy:
    1. Try in_reply_to (direct reply) — fails if user restricts replies
    2. Fallback to @mention tweet (new tweet mentioning user) — always works
    """
    if dry_run:
        return {"status": "dry_run", "text": reply_text}

    try:
        client, _ = create_twitter_clients()

        # Attempt 1: Direct reply
        try:
            response = client.create_tweet(
                text=reply_text,
                in_reply_to_tweet_id=tweet_id,
            )
            reply_id = response.data["id"]
            logger.info(f"Direct reply posted: {reply_id}")
            return {
                "status": "published",
                "reply_id": reply_id,
                "text": reply_text,
                "method": "reply",
            }
        except Exception as e:
            if "403" in str(e):
                logger.info(f"Reply restricted, falling back to @mention")
            else:
                raise

        # Attempt 2: @mention tweet (always works)
        if username:
            mention_text = f"@{username} {reply_text}"
            # Validate length with mention
            is_valid, msg = validate_tweet_text(mention_text)
            if not is_valid:
                # Trim reply to fit
                mention_text = f"@{username} {reply_text[:100]}"

            response = client.create_tweet(text=mention_text)
            reply_id = response.data["id"]
            logger.info(f"Mention tweet posted: {reply_id}")
            return {
                "status": "published",
                "reply_id": reply_id,
                "text": mention_text,
                "method": "mention",
            }

        return {"status": "failed", "error": "Reply restricted, no username for mention"}

    except Exception as e:
        logger.error(f"Reply failed: {e}")
        return {"status": "failed", "error": str(e)}


# ── Main Engagement Flow ─────────────────────────────────────────────────

def run_engagement(
    query: str | None = None,
    max_replies: int = 3,
    dry_run: bool = False,
) -> dict:
    """Run a full engagement session."""

    # Check daily limit
    today_count = get_today_reply_count()
    remaining = DAILY_REPLY_LIMIT - today_count
    if remaining <= 0 and not dry_run:
        print(f"Daily reply limit reached ({DAILY_REPLY_LIMIT})")
        return {"status": "limit_reached", "today_count": today_count}

    max_replies = min(max_replies, remaining)
    replied_ids = get_replied_tweet_ids()

    # Search for tweets
    if query:
        queries = [f"{query} site:x.com"]
    else:
        # Rotate through default queries based on day
        day_index = datetime.now(JST).timetuple().tm_yday
        q1 = DEFAULT_QUERIES[day_index % len(DEFAULT_QUERIES)]
        q2 = DEFAULT_QUERIES[(day_index + 1) % len(DEFAULT_QUERIES)]
        queries = [q1, q2]

    all_tweets = []
    for q in queries:
        tweets = search_tweets(q)
        all_tweets.extend(tweets)
        time.sleep(2)

    # Filter already replied tweets
    new_tweets = [t for t in all_tweets if t["tweet_id"] not in replied_ids]

    if not new_tweets:
        print("No new tweets found to reply to")
        return {"status": "no_targets", "searched": len(queries)}

    print(f"\nFound {len(new_tweets)} new tweets to engage with")
    print(f"Will reply to max {max_replies}")
    print(f"{'='*60}")

    # Load Twitter API for user info filtering
    _, api = create_twitter_clients()
    replied_usernames = get_replied_usernames()

    results = []
    reply_count = 0

    for tweet in new_tweets[:max_replies * 4]:  # Check more candidates
        if reply_count >= max_replies:
            break

        print(f"\n--- Target Tweet ---")
        print(f"  @{tweet['username']}: {tweet['description'][:80]}...")
        print(f"  URL: {tweet['url']}")

        # Fetch user info and apply filters
        user_info = get_user_info(api, tweet["username"], tweet_info=tweet)
        if not user_info:
            print("  (skipped: could not fetch user info)")
            continue

        ok, reason = should_engage(user_info, replied_usernames)
        if not ok:
            print(f"  (skipped: {reason})")
            continue

        print(f"  Followers: {user_info['followers']} ✅")

        # Generate reply
        reply_text = generate_reply(tweet)
        if not reply_text:
            print("  (skipped: generation failed)")
            continue

        ko = translate_to_korean(reply_text) if not dry_run else ""
        weighted = count_weighted_chars(reply_text)

        print(f"  Reply JP: {reply_text}")
        if ko:
            print(f"  Reply KO: {ko}")
        print(f"  Weighted: {weighted}/280")

        # Post reply (with mention fallback)
        result = post_reply(tweet["tweet_id"], reply_text, username=tweet["username"], dry_run=dry_run)

        if result["status"] in ("published", "dry_run"):
            reply_count += 1

            # Notify supervisor via Teams
            if result["status"] == "published" and result.get("reply_id"):
                reply_url = f"https://x.com/grosmimi_japan/status/{result['reply_id']}"
                notify_supervisor(tweet, reply_text, reply_url)

            # Log
            log_entry = {
                "replied_at": datetime.now(JST).isoformat(),
                "target_tweet_id": tweet["tweet_id"],
                "target_username": tweet["username"],
                "target_url": tweet["url"],
                "target_text": tweet["description"][:200],
                "reply_text": reply_text,
                "reply_ko": ko,
                "reply_id": result.get("reply_id"),
                "status": result["status"],
            }

            if not dry_run:
                log = load_engage_log()
                log["replies"].append(log_entry)
                save_engage_log(log)

            results.append(log_entry)
            print(f"  Status: {result['status']}")

            if result.get("reply_id"):
                print(f"  Reply URL: https://x.com/grosmimi_japan/status/{result['reply_id']}")

        else:
            print(f"  Failed: {result.get('error', 'unknown')}")

        time.sleep(3)  # Rate limit between replies

    print(f"\n{'='*60}")
    print(f"Session complete: {reply_count} replies posted")
    print(f"Today total: {today_count + reply_count}/{DAILY_REPLY_LIMIT}")

    return {
        "status": "ok",
        "replies_posted": reply_count,
        "today_total": today_count + reply_count,
        "results": results,
    }


def show_history():
    """Show reply history."""
    log = load_engage_log()
    replies = log.get("replies", [])

    if not replies:
        print("No reply history yet")
        return

    print(f"\n{'='*60}")
    print(f"Reply History ({len(replies)} total)")
    print(f"{'='*60}")

    for r in replies[-10:]:
        print(f"\n  [{r.get('replied_at', '?')[:16]}]")
        print(f"  To: @{r.get('target_username')} — {r.get('target_text', '')[:60]}...")
        print(f"  Reply: {r.get('reply_text', '')}")
        if r.get("reply_ko"):
            print(f"  KO: {r['reply_ko']}")
        print(f"  Status: {r.get('status')}")


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Twitter engagement via Firecrawl + API"
    )
    parser.add_argument("--query", type=str, help="Custom search query")
    parser.add_argument("--limit", type=int, default=3, help="Max replies (default: 3)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without posting")
    parser.add_argument("--history", action="store_true", help="Show reply history")
    args = parser.parse_args()

    if args.history:
        show_history()
        return

    run_engagement(
        query=args.query,
        max_replies=args.limit,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
