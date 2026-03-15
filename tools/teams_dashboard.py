"""
WAT Tool: Generate daily tweet plan for each slot using Claude API.

Returns plan dict with structure:
{
  "slots": {
    "10": {"tweet_jp": "...", "tweet_ko": "...", "chars": N, "replies": []},
    "19": {"tweet_jp": "...", "tweet_ko": "...", "chars": N, "replies": []}
  }
}
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = """あなたは日本の育児用品ブランド「Grosmimi（グロミミ）」のTwitter/Xコンテンツストラテジストです。
日本人ママ（20代後半〜30代、0〜3歳の子育て中）向けのツイートを作成してください。

## ブランド概要
- グロミミ = フランス語で「たくさんキスをする」の意味
- 主力商品: PPSU ストローマグ（漏れにくい、洗いやすい、医療グレード素材）
- USP: +CUT クロスカット設計（逆さにしてもこぼれない）

## ルール
- 温かく共感できる、カジュアルなトーン（〜だよ、〜ね）
- 絵文字: 1〜3個
- ハッシュタグ: 2〜3個（#グロミミ or #grosmimi 必須）
- 各ツイートは必ず140文字以内（日本語の場合は全角1文字=2文字換算で280文字以内）
- tweet_jp: 日本語ツイート本文（ハッシュタグ含む）
- tweet_ko: 韓国語要約（内部確認用、30文字以内）

## スロット別テーマ
- 10時: 朝の育児あるある、共感系、ユーモア
- 19時: 夕方の日常エピソード、製品活用シーン

## 出力（JSONのみ）
{
  "slots": {
    "10": {"tweet_jp": "...", "tweet_ko": "...", "chars": N},
    "19": {"tweet_jp": "...", "tweet_ko": "...", "chars": N}
  }
}"""


def generate_daily_plan(slots: list = None, target_date: str = None) -> dict:
    """Generate tweet plan for given slots on target_date using Claude API.

    Args:
        slots: list of slot hours e.g. [10, 19]
        target_date: "YYYY-MM-DD" string, defaults to today

    Returns:
        dict with {"slots": {"10": {...}, "19": {...}}}
    """
    import anthropic

    if slots is None:
        slots = [10, 19]
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY not found in .env")

    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
        dt = datetime.now()

    day_names_jp = ["月", "火", "水", "木", "金", "土", "日"]
    day_jp = day_names_jp[dt.weekday()]

    month = dt.month
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

    slots_str = ", ".join([f"{s}時" for s in slots])
    prompt = f"""投稿日: {target_date}（{day_jp}曜日）
今月のシーズンキーワード: {season}

スロット {slots_str} のツイートを1本ずつ作成してください。
各ツイートのcharsはtweet_jpの文字数を入れてください。
有効なJSONのみ出力してください。"""

    client = anthropic.Anthropic(api_key=api_key)

    for attempt in range(3):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text

            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0].strip()
            else:
                json_str = text.strip()

            plan = json.loads(json_str)

            # Ensure replies key exists in each slot
            for slot_key in plan.get("slots", {}).values():
                slot_key.setdefault("replies", [])

            logger.info(f"Generated plan for {target_date}: {list(plan.get('slots', {}).keys())} slots")
            return plan

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error (attempt {attempt + 1}/3): {e}")
        except Exception as e:
            logger.error(f"Claude API error (attempt {attempt + 1}/3): {e}")
            if attempt < 2:
                time.sleep(2 * (attempt + 1))

    logger.error(f"Failed to generate plan for {target_date}")
    return {}
