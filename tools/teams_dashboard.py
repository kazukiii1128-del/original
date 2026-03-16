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

PROJECT_ROOT = Path(__file__).parent.parent
TMP_DIR = PROJECT_ROOT / ".tmp"

MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = """あなたは日本の育児用品ブランド「Grosmimi（グロミミ）」のTwitter/Xコンテンツストラテジストです。
日本人ママ（20代後半〜30代）向けのツイートを作成してください。

## ターゲット設定（重要）
- 子どもの年齢: **1歳10ヶ月（固定）**
- 幼児食移行期、ストロー・コップ飲みが上手になってきた頃、イヤイヤ期の真っ最中、2語文が出始め
- 禁止トピック: 卒園、入学、運動会、七五三、ハイハイ、寝返り（1歳10ヶ月に無関係な話題はNG）

## ブランド概要
- グロミミ = フランス語で「たくさんキスをする」の意味
- 主力商品: PPSU ストローマグ（漏れにくい、洗いやすい、医療グレード素材）
- USP: +CUT クロスカット設計（逆さにしてもこぼれない）

## コンテンツカテゴリ（毎日バランスよく使い分ける）
- meme: 1〜2歳育児あるある、ユーモア、イヤイヤ期共感（製品言及不要）
- tips: 離乳食・ストローデビュー・寝かしつけ・1歳児の食事など実用アドバイス
- brand: グロミミ製品の機能・1〜2歳児の使用シーンを自然に紹介
- k_babyfood: 韓国式離乳食・幼児食トレンド紹介
- lifestyle: 1〜2歳との日常エピソード、成長の記録、ママの本音

1週間で5カテゴリをすべてカバーし、同じカテゴリが連続しないようにすること。

## ルール
- 温かく共感できる、カジュアルなトーン（〜だよ、〜ね、〜よね）
- 絵文字: 1〜3個
- ハッシュタグ: 2〜3個（#グロミミ or #grosmimi 必須）
- tweet_jp: 日本語ツイート本文（ハッシュタグ含む）、140文字以内
- tweet_ko: tweet_jpの**完全な韓国語翻訳**（要約ではなく全文翻訳。ハッシュタグも韓国語に対応したものに変更）

## スロット別テーマ
- 10時: 朝の共感系・ユーモア・meme・tips
- 19時: 夕方の日常エピソード・brand紹介・k_babyfood

## 出力（JSONのみ）
{
  "slots": {
    "10": {"tweet_jp": "...", "tweet_ko": "...", "category": "meme", "chars": N},
    "19": {"tweet_jp": "...", "tweet_ko": "...", "category": "brand", "chars": N}
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
        1: "お正月, 冬の防寒, 加湿器, 室内遊び",
        2: "節分, 花粉症対策, 春の準備, 保湿ケア",
        3: "ひな祭り, 春のお出かけ, 公園デビュー",
        4: "お花見, 外遊び, 新しい食材チャレンジ",
        5: "こどもの日, 母の日, GWのお出かけ, 熱中症予防",
        6: "梅雨対策, 室内遊び, 父の日, むし歯予防",
        7: "水遊び, プール, 熱中症対策, 夏のおやつ",
        8: "お盆, 夏の水分補給, 夜泣き, 外遊び",
        9: "秋の味覚, 幼児食の新レシピ, 過ごしやすい季節",
        10: "ハロウィン, 秋のお出かけ, 乾燥対策",
        11: "紅葉, 乾燥対策, 幼児食レシピ, 防寒グッズ",
        12: "クリスマス, 年末, 冬支度, 感染症対策",
    }
    season = season_map.get(month, "")

    # Load recent categories to avoid repetition
    recent_categories = []
    try:
        import glob as _glob
        recent_files = sorted(_glob.glob(str(TMP_DIR / "daily_tweet_plan_*.json")))[-5:]
        for rf in recent_files:
            with open(rf, encoding="utf-8") as f:
                rp = json.load(f)
            for sd in rp.get("slots", {}).values():
                cat = sd.get("category")
                if cat:
                    recent_categories.append(cat)
    except Exception:
        pass

    slots_str = ", ".join([f"{s}時" for s in slots])
    prompt = f"""投稿日: {target_date}（{day_jp}曜日）
今月のシーズンキーワード: {season}

スロット {slots_str} のツイートを1本ずつ作成してください。

重要:
- 各ツイートは異なるカテゴリ（meme/tips/brand/k_babyfood/lifestyle）を使うこと
- 最近使ったカテゴリ: {recent_categories[-4:] if recent_categories else 'なし'} → これらと重複しないカテゴリを優先
- tweet_koはtweet_jpの完全な韓国語翻訳（要約不可）
- charsはtweet_jpの文字数

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
