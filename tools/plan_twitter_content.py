"""
WAT Tool: Generate Twitter/X content plans using Claude API.
Creates Twitter-native content (280 chars) or converts Instagram plans.

Output: .tmp/twitter_plan.json

Usage:
    py -3 tools/plan_twitter_content.py                         # plan 3 tweets (default)
    py -3 tools/plan_twitter_content.py --count 7               # plan 7 days
    py -3 tools/plan_twitter_content.py --convert-from-ig       # convert IG plan to Twitter
    py -3 tools/plan_twitter_content.py --type thread           # force thread format
    py -3 tools/plan_twitter_content.py --topic "夜泣き"         # force topic
    py -3 tools/plan_twitter_content.py --dry-run               # show prompts only
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta

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
    TWITTER_PLAN_PATH,
    TWITTER_TRENDS_PATH,
    TWITTER_LOG_PATH,
    TMP_DIR,
    validate_tweet_text,
)

MODEL = "claude-sonnet-4-20250514"

TWITTER_SYSTEM_PROMPT = """あなたは日本の育児用品ブランド「Grosmimi（グロミミ）」のTwitter/Xコンテンツストラテジストです。
日本人ママ（20代後半〜30代、0〜3歳の子育て中）向けのツイートを企画してください。

## ブランド概要
- グロミミ = フランス語で「たくさんキスをする」の意味
- 主力商品: PPSU ストローマグ（漏れにくい、洗いやすい、医療グレード素材）
- USP: +CUT クロスカット設計（逆さにしてもこぼれない）

## ツイート種類
1. **single** — 280文字以内の1ツイート
2. **thread** — 3〜5ツイートの連続投稿（🧵スレッド形式）

## カテゴリ（4種類から選択）
- **meme**: 育児あるある、バイラル系、共感ネタ（育児のリアルなあるあるをユーモアたっぷりに）
- **brand**: グロミミ製品紹介、機能説明、使用シーン
- **tips**: 育児の実用的なアドバイス（ストローデビュー時期、離乳食、寝かしつけなど）
- **k_babyfood**: 韓国式離乳食、K-離乳食トレンド

## トーン & ルール
- 温かく共感できる、カジュアル（〜だよ、〜ね、〜よね）
- 絵文字: 控えめに（1〜3個まで。Instagramより少なめ）
- ハッシュタグ: 2〜3個。ブランド系1つ必須(#グロミミ or #grosmimi) + 製品系1つ推奨(#ストローマグ, #スマートマグ, #ppsu) + コンテンツ系任意
- CTA: さりげなく（いいね、RT、フォロー誘導）
- 禁止: 医療的主張、競合批判、過度な宣伝感、育児の正解を押し付ける表現
- 各ツイートは必ず280文字以内

## スレッド形式のルール
- 1ツイート目: アイキャッチ（問いかけ or 衝撃的事実 + 🧵👇）
- 中間: 1ツイート=1ポイント
- 最終: まとめ + CTA（フォローやいいね）

## 出力JSON形式
```json
{
  "posts": [
    {
      "post_id": "YYYYMMDD_T001",
      "scheduled_date": "YYYY-MM-DD",
      "scheduled_time": "20:00",
      "topic": "トピック名",
      "tweet_type": "single" or "thread",
      "category": "meme/brand/tips/k_babyfood",
      "tweets": [
        {
          "order": 1,
          "text": "ツイート本文（280文字以内）",
          "char_count": 120,
          "image_path": null
        }
      ],
      "hashtags": ["#育児", "#グロミミ"],
      "status": "planned"
    }
  ]
}
```

有効なJSONのみを出力してください。説明文は不要です。"""


def load_trends() -> dict | None:
    """Load scraped trends if available."""
    for path in [TWITTER_TRENDS_PATH, TMP_DIR / "jp_trends_raw.json"]:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded trends from {path.name}: {data.get('total_items', '?')} items")
            return data
    return None


def load_posting_history() -> list[str]:
    """Load recent posting history to avoid duplicate topics."""
    if not TWITTER_LOG_PATH.exists():
        return []
    with open(TWITTER_LOG_PATH, "r", encoding="utf-8") as f:
        log = json.load(f)
    return [t.get("text_preview", "") for t in log.get("tweets", [])[-20:]]


def build_planning_prompt(
    count: int,
    trends: dict | None = None,
    topic: str | None = None,
    tweet_type: str | None = None,
    history: list[str] | None = None,
) -> str:
    """Build the prompt for Claude to generate Twitter content plans."""
    today = datetime.now()
    month = today.month

    # Season keywords
    season_map = {
        1: "お正月, 新年の抱負, 冬の育児",
        2: "節分, バレンタイン, 花粉症対策",
        3: "ひな祭り, 卒園, 春の準備",
        4: "入園・入学, 新生活, お花見",
        5: "こどもの日, 母の日, GW旅行",
        6: "梅雨対策, 父の日, 虫歯予防",
        7: "夏祭り, プール開き, 熱中症対策",
        8: "お盆, 夏休み, 水遊び",
        9: "敬老の日, 秋の味覚, 運動会準備",
        10: "ハロウィン, 運動会, 七五三準備",
        11: "七五三, 紅葉, 乾燥対策",
        12: "クリスマス, 年末, 冬支度",
    }
    season = season_map.get(month, "")

    prompt = f"""今日は{today.strftime('%Y年%m月%d日')}です。
今月のシーズンキーワード: {season}

{count}件のTwitter投稿を企画してください。
"""

    if topic:
        prompt += f"\nテーマ指定: 「{topic}」に関する内容で作成してください。\n"

    if tweet_type:
        prompt += f"\n形式指定: すべて「{tweet_type}」形式で作成してください。\n"

    # Add scheduling
    prompt += f"""
スケジュール:
- 開始日: {today.strftime('%Y-%m-%d')}
- post_id形式: {today.strftime('%Y%m%d')}_T001, T002, ...
- 投稿時間: 7:00, 12:00, 20:00 のいずれか（JST）
- カテゴリのバランスを考慮（meme, brand, tips, k_babyfood）
"""

    if trends:
        items = trends.get("items", [])[:10]
        if items:
            prompt += "\n## 参考トレンド（最新）\n"
            for item in items:
                snippet = item.get("content_snippet", "")[:100]
                tags = ", ".join(item.get("hashtags", [])[:3])
                prompt += f"- {snippet} [{tags}]\n"

    if history:
        prompt += "\n## 最近の投稿（重複避ける）\n"
        for h in history[-5:]:
            prompt += f"- {h}\n"

    return prompt


def plan_with_claude(prompt: str) -> dict | None:
    """Call Claude API to generate content plan. Returns parsed JSON."""
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY not found in .env")

    client = anthropic.Anthropic(api_key=api_key)

    for attempt in range(3):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=8000,
                system=TWITTER_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text

            # Extract JSON from markdown code blocks
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0].strip()
            else:
                json_str = text.strip()

            result = json.loads(json_str)
            logger.info(f"Claude returned {len(result.get('posts', []))} posts")
            return result

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error (attempt {attempt + 1}/3): {e}")
            prompt += "\n\n重要: 有効なJSONのみを出力してください。マークダウンや説明文は不要です。"
        except Exception as e:
            logger.error(f"Claude API error (attempt {attempt + 1}/3): {e}")
            if attempt < 2:
                time.sleep(2 * (attempt + 1))

    return None


def validate_plan(plan: dict) -> list[str]:
    """Validate all tweets in the plan. Returns list of warnings."""
    warnings = []
    for post in plan.get("posts", []):
        for tweet in post.get("tweets", []):
            is_valid, msg = validate_tweet_text(tweet.get("text", ""))
            if not is_valid:
                warnings.append(f"{post['post_id']} tweet {tweet.get('order', '?')}: {msg}")
            # Update char_count
            tweet["char_count"] = len(tweet.get("text", ""))
    return warnings


def convert_instagram_to_twitter(ig_plan_path: Path) -> dict | None:
    """Convert an Instagram content plan to Twitter format."""
    if not ig_plan_path.exists():
        logger.error(f"Instagram plan not found: {ig_plan_path}")
        return None

    with open(ig_plan_path, "r", encoding="utf-8") as f:
        ig_plan = json.load(f)

    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    twitter_posts = []
    for ig_post in ig_plan.get("posts", []):
        caption = ig_post.get("caption_ja", "")
        topic = ig_post.get("topic", "")
        post_id = ig_post.get("post_id", "").replace("_", "_T")

        conversion_prompt = f"""以下のInstagram投稿をTwitter用に変換してください。

## Instagram投稿
トピック: {topic}
キャプション:
{caption}

## 変換ルール
1. 280文字以内のツイートに圧縮
2. ハッシュタグは2〜3個に削減
3. Instagramの「保存してね！」→ Twitterの「いいね・RTで応援してね」に変更
4. カルーセル（複数スライド）の場合はスレッド形式（3〜5ツイート）に変換
5. CTA（プロフリンク誘導）を自然に含める

## 出力（JSONのみ）
{{"post_id": "{post_id}", "tweet_type": "single or thread", "tweets": [{{"order": 1, "text": "...", "char_count": N}}], "hashtags": ["#tag1", "#tag2"]}}"""

        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=2000,
                system="Instagram投稿をTwitter用に変換するアシスタントです。有効なJSONのみ出力してください。",
                messages=[{"role": "user", "content": conversion_prompt}],
            )
            text = response.content[0].text
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0].strip()
            else:
                json_str = text.strip()

            converted = json.loads(json_str)
            converted["scheduled_date"] = ig_post.get("scheduled_date", "")
            converted["topic"] = topic
            converted["category"] = ig_post.get("category", "brand")
            converted["ig_source_post_id"] = ig_post.get("post_id")
            converted["status"] = "planned"
            twitter_posts.append(converted)
            logger.info(f"Converted: {post_id} → {converted.get('tweet_type')}")
            time.sleep(1)  # Rate limit courtesy

        except Exception as e:
            logger.error(f"Conversion failed for {post_id}: {e}")

    return {
        "planned_at": datetime.now().isoformat(),
        "platform": "twitter",
        "source": "instagram_conversion",
        "total_posts": len(twitter_posts),
        "posts": twitter_posts,
    }


def save_plan(plan: dict, plan_path: Path) -> None:
    """Save plan to JSON file, merging with existing if present."""
    plan_path.parent.mkdir(parents=True, exist_ok=True)

    if plan_path.exists():
        with open(plan_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        existing_ids = {p["post_id"] for p in existing.get("posts", [])}
        new_posts = [p for p in plan["posts"] if p["post_id"] not in existing_ids]
        existing["posts"].extend(new_posts)
        existing["total_posts"] = len(existing["posts"])
        plan = existing
        logger.info(f"Merged {len(new_posts)} new posts into existing plan")

    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    logger.info(f"Plan saved: {plan_path} ({plan['total_posts']} posts)")


def main():
    parser = argparse.ArgumentParser(description="Generate Twitter content plans")
    parser.add_argument("--count", type=int, default=3, help="Number of posts to plan")
    parser.add_argument("--convert-from-ig", action="store_true", help="Convert Instagram plan")
    parser.add_argument("--ig-plan", type=str, default=str(TMP_DIR / "content_plan.json"))
    parser.add_argument("--type", type=str, choices=["single", "thread"], help="Force tweet type")
    parser.add_argument("--topic", type=str, help="Force specific topic")
    parser.add_argument("--output", type=str, default=str(TWITTER_PLAN_PATH))
    parser.add_argument("--dry-run", action="store_true", help="Show prompt only")
    args = parser.parse_args()

    output_path = Path(args.output)

    # Instagram conversion mode
    if args.convert_from_ig:
        ig_path = Path(args.ig_plan)
        if args.dry_run:
            print(f"[DRY RUN] Would convert Instagram plan: {ig_path}")
            return

        plan = convert_instagram_to_twitter(ig_path)
        if plan:
            warnings = validate_plan(plan)
            for w in warnings:
                print(f"  ⚠️  {w}")
            save_plan(plan, output_path)
            print(f"\nConverted {plan['total_posts']} posts → {output_path}")
        return

    # Native Twitter planning
    trends = load_trends()
    history = load_posting_history()

    prompt = build_planning_prompt(
        count=args.count,
        trends=trends,
        topic=args.topic,
        tweet_type=args.type,
        history=history,
    )

    if args.dry_run:
        print("[DRY RUN] Planning prompt:")
        print("=" * 60)
        print(f"System prompt: ({len(TWITTER_SYSTEM_PROMPT)} chars)")
        print("=" * 60)
        print(prompt)
        return

    plan = plan_with_claude(prompt)
    if not plan:
        print("Failed to generate plan. Check logs.")
        return

    # Add metadata
    plan["planned_at"] = datetime.now().isoformat()
    plan["platform"] = "twitter"
    plan["total_posts"] = len(plan.get("posts", []))

    # Validate
    warnings = validate_plan(plan)
    if warnings:
        print("Validation warnings:")
        for w in warnings:
            print(f"  ⚠️  {w}")

    save_plan(plan, output_path)

    # Summary
    print(f"\nPlanned {plan['total_posts']} tweets:")
    for post in plan.get("posts", []):
        tweet_type = post.get("tweet_type", "single")
        topic = post.get("topic", "")
        tweets = post.get("tweets", [])
        tweet_count = len(tweets)
        print(f"  {post['post_id']} [{tweet_type}] {topic} ({tweet_count} tweet{'s' if tweet_count > 1 else ''})")


if __name__ == "__main__":
    main()
