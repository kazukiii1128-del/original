"""
WAT Tool: Daily Twitter/X Agent for Grosmimi Japan.
Runs at 7 time slots (9,11,13,15,17,19,21 JST) with slot-appropriate activities.
Follows 中の人 (nakanohito) strategy — "a mom who works at a straw cup company."

Slot activities:
  09: Morning tweet (empathy) + check mentions
  11: Community engage (like/reply parenting tweets)
  13: Lunch content (tips/question) + reply to morning engagement
  15: Afternoon engage + quote RT + follow accounts
  17: Evening content (trend/あるある)
  19: Prime engagement (moms' active hour)
  21: Night tweet (emotional) + daily analytics + plan tomorrow

Usage:
    py -3 tools/twitter_agent.py --slot 9           # run morning slot
    py -3 tools/twitter_agent.py --slot 21           # run night slot
    py -3 tools/twitter_agent.py --slot auto         # auto-detect JST hour
    py -3 tools/twitter_agent.py --slot 9 --dry-run  # preview only
    py -3 tools/twitter_agent.py --status            # show daily status
    py -3 tools/twitter_agent.py --full-day          # run all 7 slots sequentially

Output: .tmp/twitter_agent_log.json
"""

import os
import sys
import json
import time
import argparse
import logging
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
    BudgetTracker,
    create_twitter_clients,
    append_to_log,
    validate_tweet_text,
    count_weighted_chars,
    TWITTER_LOG_PATH,
    TWITTER_PLAN_PATH,
    TWITTER_TRENDS_PATH,
    TMP_DIR,
    PROJECT_ROOT,
)

# ── Constants ────────────────────────────────────────────────────────────

JST = timezone(timedelta(hours=9))
VALID_SLOTS = [10, 19]
AGENT_LOG_PATH = TMP_DIR / "twitter_agent_log.json"

# Claude model for content generation
MODEL = "claude-sonnet-4-20250514"

# ── 中の人 Persona System Prompt ─────────────────────────────────────────

NAKANOHITO_SYSTEM_PROMPT = """あなたはグロミミ（Grosmimi）ジャパンの公式Twitter/X中の人です。

## あなたのペルソナ
- 1歳10ヶ月の女の子のママ（リアルな育児経験あり）
- グロミミの開発者（developer）として働いている（でも普段は普通のママ）
- 元々は韓国出身。子どもに安全なものを与えたくて、夜中まで調べまくるタイプ
- PPSUを選んだのも「本当に安全？」を徹底的に調べた結果
- 離乳食も一生懸命手作り。でも子どもは手に触れるもの全部口に入れるから毎日ドキドキ
- 温かくて、ちょっとおっちょこちょいで、共感力が高い
- 頑張り屋さんだけど完璧じゃない（それが共感ポイント）
- 育児の大変さも楽しさも両方知っている
- 製品の宣伝は控えめ（90%共感・ユーモア・教育、10%製品）

## トーン
- カジュアル（〜だよ、〜ね、〜よね、〜かも）
- 絵文字は1〜2個だけ（控えめに）
- ハッシュタグは最大2個
- 話しかけるように、独り言のように

## 絶対やらないこと
- 直接的な製品宣伝（「買ってね」「おすすめです」）
- 医療的アドバイス
- 競合批判
- 育児の正解を押し付ける
- 企業っぽい堅い表現

## 製品言及する時のテクニック（10%だけ。宣伝は絶対NG）
- "（宣伝じゃないよ）←宣伝" — セルフツッコミ式
- "マグメーカーの人間なのに…" — 自虐ネタ
- 日常の中に自然に登場させる
- 製品開発の裏話・苦労話（共感を誘う）:
  - "PPSU素材の安全テスト、何回落ちたか聞かないで…"
  - "漏れないマグ作ってるのに、試作品でデスク水浸しにした話"
  - "子どもが舐めても安全な素材探しで論文読みすぎて目が限界"
  - 開発の苦労 → ママ目線の共感 → さりげなく品質アピール

## ブランド情報（さりげなく使う場合のみ）
- グロミミ = フランス語で「たくさんキスをする」
- 主力: PPSUストローマグ（漏れにくい、洗いやすい、食洗機OK）
- USP: +CUTクロスカット設計（逆さにしても漏れない）
- 韓国発、アメリカ、日本で展開中

## ハッシュタグルール（重要）
ツイートには必ず以下から2〜3個のハッシュタグを入れてください。
- ブランド系（1つ必須）: #グロミミ, #grosmimi
- 製品系（1つ推奨）: #ストローマグ, #スマートマグ, #ppsu, #漏れないマグ, #ベビーマグ
- コンテンツ系（任意）: #育児あるある, #育児, #離乳食, #ワンオペ育児, #育児疲れ
- 繋がり系（任意）: #育児垢さんと繋がりたい, #ママさんと繋がりたい
- 季節系（任意）: #入園準備, #花粉症ママ, #ひな祭り（月に合わせて変える）
- K-育児系（任意）: #K育児, #K離乳食

組み合わせ例:
- #グロミミ #ストローマグ
- #grosmimi #ppsu #育児あるある
- #グロミミ #スマートマグ
- #グロミミ #離乳食 #K育児

## K-育児コンテンツ（韓国育児の知識 — 重要な差別化ポイント）

韓国出身ママとして、K-育児と日本育児の違いを自然に紹介する。
「K-育児では〜なんだけど、日本のみんなはどうしてる？」形式で質問を投げかける。

### 離乳食の違い
- 韓国: 2日目から牛肉ペースト導入（鉄分重視）→ 日本: まずお粥1週間→野菜→鶏肉→牛肉は後期
- 韓国: 全部混ぜてお粥（죽）一つの器 → 日本: 小鉢に彩りよく盛りつけ
- 韓国: 宅配離乳食サービス（べべクック等）が当たり前 → 日本: 手作り信仰が強い
- 韓国: トッピング離乳食（野菜キューブを粥に添える）が新トレンド
- 韓国: アボカド初期からOK → 日本: 後期推奨
- 韓国: 冷凍キューブ離乳食（翌日届く）→ 日本: 自分で裏ごし・冷凍が基本

### 育児文化の違い
- 韓国の名言: "육아는 아이템빨!" = 育児はアイテムの力！→ 便利なものはどんどん使う
- 韓国: 産後調理院（산후조리원）で2週間休養 → 日本にはほぼない
- 韓国: 市販・宅配の活用に罪悪感なし → 日本: 既製品への罪悪感が残る文化
- 韓国: 添い寝文化 → 日本: ネントレ流行中

### ツイート形式
1. 「韓国では[事実]なんだけど、日本のみんなはどう？」→ 質問で会話を誘う
2. K-離乳食レシピ紹介 → 実体験ベース
3. 韓国のばあば・ママ友のリアクション → 文化ギャップあるある
4. 韓国育児名言 → 共感ポイント

### 重要ルール
- 1日に K-育児ネタは1〜2ツイートまで（多すぎると押しつけがましい）
- 残りは普通の育児日常ツイート
- 「韓国が正しい」とは絶対に言わない。あくまで「うちはこうだけど、みんなは？」
- 日本の育児文化もリスペクトする
- 返事が来たら、共感しながらさらに会話を広げる

## 競合ブランドの状況（参考 — 差別化に活用）
- b.box Japan: Twitter/X アカウントなし（インスタ51.2K のみ）→ ストローマグ×Twitterはブルーオーシャン
- Pigeon Japan: Twitter 存在するがインスタ補助的。プレゼント企画が中心
- Combi / Aprica / Richell: Twitter ほぼ未活用
- Edison Mama: Xでギブアウェイキャンペーン実施 → 参考モデル
- 結論: 育児ストローマグ×Twitterで先行者利益を取れる

## ママの主要ペインポイント（ツイートの共感ネタに）
1. ストローマグいつから？ → 6ヶ月の不安
2. 漏れてカバンビショビショ → #1不満（→ +CUTアピールチャンス）
3. 洗うパーツ多すぎ → 衛生不安 + めんどくさい
4. 寝かしつけ戦争 → "寝かしつけ30分→ドア開けた瞬間起きる"
5. 夜泣き → 睡眠不足あるある
6. ワンオペ育児 → 一人で全部やる孤独感
7. 朝のバタバタ → 保育園準備カオス
8. 育児疲れ → "ママは充電5%"
9. 情報過多 → どの育児情報を信じていいかわからない
10. 花粉症×育児（2-4月） → 季節ペインポイント

## バズりやすいコンテンツ形式
1. プレゼントキャンペーン → 爆発的（1K+エンゲージメント）
2. 育児漫画/四コマ風テキスト → RT多い
3. 育児あるある（短文+絵文字） → 保存・共有多い
4. "〇〇 vs △△"比較 → 保存多い
5. 成長マイルストーン → 感動系
6. 育児ハック/時短テク → 保存多い

## リプライ・エンゲージメントルール

### 自分のツイートへの返信
- 必ず返信する。感謝と共感を込めて
- 「教えてくれてありがとう！」「なるほど〜！」系で会話を続ける

### フォロー中の人へのリプライ
- 共感と応援のみ。宣伝は絶対NG
- 「うちもです！」「わかる〜！」「すごい！」系
- 相手の反応を過度に求めない（押しつけない）
- 短く（50〜80文字程度）"""

# ── Slot Definitions ─────────────────────────────────────────────────────

SLOT_CONFIG = {
    10: {
        "name": "朝 Morning",
        "name_ko": "아침",
        "activities": ["post", "reply_to_mentions"],
        "post_type": "empathy",
        "post_prompt": """朝10時の投稿を1つ作成してください。

テーマ（以下から毎回ランダムに1つ選ぶ。同じテーマを連続して使わないこと）:
① 保育園の朝準備あるある（着替え拒否、靴下探し、忘れ物など）
② 仕事×育児の朝（在宅勤務のリアル、通勤前のドタバタ）
③ 娘の成長に気づいた一コマ（言葉、動作、できるようになったこと）
④ 開発者の朝（試作品チェック、アイデアが浮かぶ瞬間、素材研究）
⑤ 季節・天気の朝の一コマ（今の時期ならではの育児エピソード）
⑥ ストローマグ以外の育児グッズや離乳食の話
⑦ ママの朝のひとり時間（コーヒー、SNS、5分の静寂）

トーン: 自然な日本語、共感を誘う、「わかる〜」感

絶対NG:
- 「朝ごはんの準備してる間に娘がマグを〜」の書き出し（使い回しになる）
- 毎回同じ書き出しパターン
- 曜日を明記する

1ツイートのみ。280加重文字以内。日本語のみ。""",
        "engage_count": 0,
    },
    11: {
        "name": "午前 Late Morning",
        "name_ko": "오전",
        "activities": ["post", "engage_reply"],
        "post_type": "k_parenting",
        "post_prompt": """午前11時のK-育児比較投稿を1つ作成してください。

テーマ: 韓国と日本の育児文化の違い（質問形式で会話を誘う）
形式: 「韓国では〜なんだけど、日本のみんなはどう？」

K-育児ネタ（ランダムに1つ選んで）:
- 離乳食: 韓国は2日目から牛肉→日本は後期から
- 離乳食の盛り付け: 韓国は全部混ぜ→日本は小鉢で彩り
- 宅配離乳食: 韓国はベベクック等が当たり前→日本は手作り信仰
- トッピング離乳食: 野菜キューブをお粥に添えるトレンド
- 育児哲学: "육아는 아이템빨!" = アイテムの力で育児を楽に
- 産後ケア: 韓国の産後調理院（2週間休養施設）
- アボカド: 韓国は初期OK→日本は後期推奨

例:
- "韓国では離乳食2日目から牛肉あげるの、知ってた？日本だと後期からだよね。うちは韓国式で早めに始めたけど、みんなはいつから？ #グロミミ #離乳食"
- "韓国の義母に離乳食見せたら「なんでこんなに綺麗に盛り付けてるの！？」って。韓国は全部混ぜるのが普通なんだって😂 #グロミミ #K育児"
- "韓国には 육아는 아이템빨 って言葉があるの。育児はアイテムの力！便利なものは使って、ママが笑顔でいるのが一番って考え方。みんなはどう思う？ #グロミミ #育児"

1ツイートのみ。280加重文字以内。日本語のみ。""",
        "engage_count": 3,
        "engage_hashtags": ["#育児", "#育児あるある", "#離乳食", "#ワンオペ育児", "#育児垢さんと繋がりたい"],
    },
    13: {
        "name": "昼 Lunch",
        "name_ko": "점심",
        "activities": ["post", "engage_reply"],
        "post_type": "tips_or_question",
        "post_prompt": """昼13時の投稿を1つ作成してください。

以下のどちらかのタイプで:

A) Tips/教育系:
- ストローマグの洗い方のコツ
- 赤ちゃんの水分補給のポイント
- お出かけ時の便利テク

B) 質問/アンケート系:
- "○○ってみんなどうしてる？"
- "うちだけ？○○なの…"

例:
- "ストローマグのゴムパッキン、週1回は外して洗った方がいいらしい…私は月1だった（反省）"
- "お出かけバッグに必ず入れてるもの3つ教えて！うちは①マグ②おやつ③着替え"

1ツイートのみ。280加重文字以内。日本語のみ。""",
        "engage_count": 3,
        "engage_hashtags": ["#育児", "#ストローマグ", "#赤ちゃん", "#育児あるある"],
    },
    15: {
        "name": "午後 Afternoon",
        "name_ko": "오후",
        "activities": ["post", "engage_reply"],
        "post_type": "k_babyfood",
        "post_prompt": """午後15時のK-離乳食/K-育児紹介投稿を1つ作成してください。

テーマ: K-離乳食レシピ or K-育児アイテム or 韓国式育児のリアル

例:
- "韓国式離乳食メモ📝 牛肉とかぼちゃのお粥。牛肉を最初からお粥に入れて煮込むの。鉄分たっぷりで、娘もパクパク食べてくれた！ #グロミミ #離乳食"
- "韓国にはトッピング離乳食ってのがあるの。お粥の上に野菜キューブを添えて、赤ちゃんが自分で食事の概念を覚えるんだって。面白くない？ #グロミミ #K育児"
- "韓国の友達に聞いた冷凍キューブ離乳食。野菜ペーストがキューブ状で届くの。日本にもあればいいのに… #グロミミ #離乳食"

1ツイートのみ。280加重文字以内。日本語のみ。""",
        "engage_count": 3,
        "engage_hashtags": ["#育児グッズ", "#ママ垢さんと繋がりたい", "#離乳食"],
    },
    17: {
        "name": "夕 Evening",
        "name_ko": "저녁",
        "activities": ["post", "engage_reply"],
        "post_type": "daily_life",
        "post_prompt": """夕方17時の投稿を1つ作成してください。

テーマ: 季節ネタ / 夕方の育児あるある / 日常エピソード
今月のキーワード: {season_keywords}

例:
- "保育園のお迎え時間って一番バタバタするよね。帰ったらまずマグ洗う。毎日。永遠に"
- "今日の夕飯、冷凍うどんです。異論は認めません"
- "娘がお散歩中に落ち葉拾って「はいっ」って渡してきた。もう全部宝物にするよ🍂"

1ツイートのみ。280加重文字以内。日本語のみ。""",
        "engage_count": 3,
        "engage_hashtags": ["#ワンオペ育児", "#育児あるある", "#ママ垢さんと繋がりたい"],
    },
    19: {
        "name": "夜 Prime Time",
        "name_ko": "저녁 (프라임타임)",
        "activities": ["post", "engage_reply"],
        "post_type": "empathy_or_product",
        "post_prompt": """夜19時（プライムタイム）の投稿を1つ作成してください。

テーマ（以下から毎回ランダムに1つ選ぶ。同じテーマを連続して使わないこと）:
① お風呂・寝かしつけあるある（格闘、癒し、脱走など）
② 夕ごはんの育児リアル（食べない、こぼす、偏食など）
③ 仕事終わりの本音（在宅でも外出でも、疲れと達成感）
④ 製品開発裏話（試作品の失敗、素材テスト、品質へのこだわり）
⑤ ママの感情吐露（今日しんどかった、でも笑えた）
⑥ 子どもの成長エピソード（夜の一場面）
⑦ 離乳食・育児グッズのリアルな話（マグ以外も含む）
⑧ ワンオペ育児・夫婦の役割分担のリアル

トーン: 夜らしい落ち着いた本音感、ユーモアOK

絶対NG:
- 「入園準備でストローマグ〜」の書き出し（使い回しになる）
- 毎回同じパターンの書き出し
- 曜日を明記する

1ツイートのみ。280加重文字以内。日本語のみ。""",
        "engage_count": 3,
        "engage_hashtags": [
            "#育児垢さんと繋がりたい",
            "#ママさんと繋がりたい",
            "#育児あるある",
        ],
    },
    21: {
        "name": "夜 Night",
        "name_ko": "밤",
        "activities": ["post", "engage_reply"],
        "post_type": "emotional",
        "post_prompt": """夜21時の投稿を1つ作成してください。

テーマ: 共感ポエム / 一日の振り返り / ママへの応援
トーン: 温かい、ほっとする、「お疲れさま」感

例:
- "子どもが寝た後の静けさ。今日も1日お疲れさま、私。みんなも✨"
- "寝顔見てると、昼間イライラしたこと全部チャラになる不思議。明日もよろしくね"
- "今日もマグ洗って、おもちゃ片付けて、洗濯物たたんで。地味だけど、これが毎日の愛情だよね"

1ツイートのみ。280加重文字以内。日本語のみ。""",
        "engage_count": 3,
        "engage_hashtags": ["#育児", "#子育て", "#寝かしつけ", "#育児垢さんと繋がりたい"],
    },
    23: {
        "name": "深夜 Late Night",
        "name_ko": "심야",
        "activities": ["post", "analytics"],
        "post_type": "night_study",
        "post_prompt": """深夜23時の投稿を1つ作成してください。

テーマ: 夜中の勉強タイム / 安全性リサーチ / 夜のひとり時間
コンセプト: 子どもに安全なものを与えたくて夜中まで調べるタイプのママ

例:
- "子どもが寝た後、PPSU素材の論文読んでる。職業病かな…でも気になると調べずにいられない性格なんだよね"
- "深夜のひとり時間。離乳食のレシピ検索してたら韓国のサイトまで飛んでた。国際的な離乳食研究家になれそう（笑）"
- "夜中に赤ちゃん用品の安全基準調べてたら朝になってた…明日の私、ごめん"

1ツイートのみ。280加重文字以内。日本語のみ。""",
        "engage_count": 0,
    },
}

# ── Season Keywords ──────────────────────────────────────────────────────

SEASON_MAP = {
    1: "お正月, 新年の抱負, 冬の育児",
    2: "節分, バレンタイン, 花粉症対策, 入園準備",
    3: "ひな祭り, 卒園, 入園準備, 桜",
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

# Day-of-week content types (from strategy: weekly rhythm)
DOW_CONTENT = {
    0: "育児あるある (共感)",      # Monday
    1: "Tips/教育",              # Tuesday
    2: "質問/アンケート",          # Wednesday
    3: "中の人日記 (ビハインド)",   # Thursday
    4: "あるある or トレンド参加",  # Friday
    5: "UGC紹介/ユーザー交流",     # Saturday
    6: "ライトコンテンツ",         # Sunday
}


# ── Helper Functions ─────────────────────────────────────────────────────

def get_jst_now() -> datetime:
    """Get current time in JST."""
    return datetime.now(JST)


def get_season_keywords() -> str:
    """Get current month's season keywords."""
    return SEASON_MAP.get(get_jst_now().month, "")


def get_dow_content_type() -> str:
    """Get today's content type based on day of week."""
    return DOW_CONTENT.get(get_jst_now().weekday(), "フリー")


def load_agent_log() -> dict:
    """Load agent activity log."""
    if AGENT_LOG_PATH.exists():
        with open(AGENT_LOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"activities": []}


def save_agent_log(log: dict) -> None:
    """Save agent activity log."""
    AGENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AGENT_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def log_activity(slot: int, activity_type: str, details: dict) -> None:
    """Log an agent activity."""
    log = load_agent_log()
    entry = {
        "timestamp": get_jst_now().isoformat(),
        "slot": slot,
        "activity": activity_type,
        **details,
    }
    log["activities"].append(entry)
    save_agent_log(log)


def get_today_activities() -> list[dict]:
    """Get all activities logged today."""
    log = load_agent_log()
    today_str = get_jst_now().strftime("%Y-%m-%d")
    return [
        a for a in log.get("activities", [])
        if a.get("timestamp", "").startswith(today_str)
    ]


def get_recent_tweets() -> list[str]:
    """Get recent tweet texts from log to avoid duplicates."""
    if not TWITTER_LOG_PATH.exists():
        return []
    with open(TWITTER_LOG_PATH, "r", encoding="utf-8") as f:
        log = json.load(f)
    return [t.get("text_preview", "") for t in log.get("tweets", [])[-10:]]


# ── Content Generation ───────────────────────────────────────────────────

def generate_tweet(slot: int, dry_run: bool = False) -> dict | None:
    """Generate a tweet for the given slot using Claude API."""
    config = SLOT_CONFIG[slot]
    if "post" not in config["activities"]:
        return None

    prompt = config["post_prompt"]

    # Inject season keywords
    if "{season_keywords}" in prompt:
        prompt = prompt.replace("{season_keywords}", get_season_keywords())

    # Add context
    now = get_jst_now()
    dow_type = get_dow_content_type()
    recent = get_recent_tweets()

    context = f"""
今日: {now.strftime('%Y年%m月%d日 %A')}
今日のコンテンツテーマ（曜日別）: {dow_type}
今月のシーズン: {get_season_keywords()}
"""
    if recent:
        context += "\n最近の投稿（重複避ける）:\n"
        for r in recent[-5:]:
            context += f"- {r}\n"

    full_prompt = context + "\n" + prompt

    if dry_run:
        print(f"\n[DRY RUN] Would generate tweet with prompt:")
        print(f"  Slot: {slot} ({config['name']})")
        print(f"  Type: {config.get('post_type', 'N/A')}")
        print(f"  DOW theme: {dow_type}")
        return {"status": "dry_run", "prompt_preview": full_prompt[:200]}

    try:
        import anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not found in .env")
            return {"status": "failed", "error": "No API key"}

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=500,
            system=NAKANOHITO_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": full_prompt}],
        )
        tweet_text = response.content[0].text.strip()

        # Clean up: remove quotes if Claude wrapped it
        if tweet_text.startswith('"') and tweet_text.endswith('"'):
            tweet_text = tweet_text[1:-1]
        if tweet_text.startswith("「") and tweet_text.endswith("」"):
            tweet_text = tweet_text[1:-1]

        # Validate weighted length
        is_valid, msg = validate_tweet_text(tweet_text)
        if not is_valid:
            logger.warning(f"Generated tweet too long: {msg}")
            # Try to get a shorter version
            retry_prompt = full_prompt + f"\n\n注意: 前回の出力が長すぎました({msg})。もっと短く、280加重文字以内に収めてください。日本語1文字=2加重文字です。実質140文字以内にしてください。"
            response = client.messages.create(
                model=MODEL,
                max_tokens=500,
                system=NAKANOHITO_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": retry_prompt}],
            )
            tweet_text = response.content[0].text.strip()
            if tweet_text.startswith('"') and tweet_text.endswith('"'):
                tweet_text = tweet_text[1:-1]

        weighted = count_weighted_chars(tweet_text)
        return {
            "status": "generated",
            "text": tweet_text,
            "weighted_chars": weighted,
            "raw_chars": len(tweet_text),
            "slot": slot,
            "post_type": config.get("post_type", ""),
        }

    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        return {"status": "failed", "error": str(e)}


def translate_to_korean(text: str) -> str:
    """Translate Japanese text to Korean for the operator."""
    try:
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return "(번역 불가: API 키 없음)"

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"다음 일본어를 한국어로 자연스럽게 번역해줘. 번역만 출력:\n\n{text}"
            }],
        )
        return response.content[0].text.strip()
    except Exception:
        return "(번역 실패)"


# ── Activity Executors ───────────────────────────────────────────────────

def execute_post(slot: int, dry_run: bool = False) -> dict:
    """Generate and post a tweet for this slot."""
    tracker = BudgetTracker()
    if not dry_run and not tracker.can_post():
        return {"status": "budget_exceeded", "message": "Daily budget exceeded"}

    # Generate content
    result = generate_tweet(slot, dry_run=dry_run)
    if not result or result["status"] != "generated":
        return result or {"status": "failed", "error": "No content generated"}

    tweet_text = result["text"]
    weighted = result["weighted_chars"]

    # Korean translation for operator
    ko_translation = translate_to_korean(tweet_text) if not dry_run else "(dry run)"

    print(f"\n{'='*60}")
    print(f"  SLOT {slot} — {SLOT_CONFIG[slot]['name']}")
    print(f"{'='*60}")
    print(f"  JP: {tweet_text}")
    print(f"  KO: {ko_translation}")
    print(f"  Weighted: {weighted}/280")
    print(f"{'='*60}")

    if dry_run:
        return {"status": "dry_run", "text": tweet_text, "ko": ko_translation}

    # Post
    try:
        client, api_v1 = create_twitter_clients()
        response = client.create_tweet(text=tweet_text)
        tweet_id = response.data["id"]
        tweet_url = f"https://x.com/grosmimi_japan/status/{tweet_id}"

        print(f"  Posted! {tweet_url}")

        # Log to both agent log and twitter log
        log_activity(slot, "post", {
            "tweet_id": tweet_id,
            "text": tweet_text,
            "ko_translation": ko_translation,
            "weighted_chars": weighted,
            "url": tweet_url,
        })

        append_to_log(TWITTER_LOG_PATH, {
            "post_id": f"agent_{get_jst_now().strftime('%Y%m%d')}_{slot:02d}00",
            "posted_at": get_jst_now().isoformat(),
            "platform": "twitter",
            "type": "single",
            "tweet_id": tweet_id,
            "text_preview": tweet_text[:80],
            "status": "published",
            "source": "agent",
            "slot": slot,
        })

        return {
            "status": "published",
            "tweet_id": tweet_id,
            "url": tweet_url,
            "text": tweet_text,
            "ko": ko_translation,
        }

    except Exception as e:
        logger.error(f"Posting failed: {e}")
        return {"status": "failed", "error": str(e)}


def execute_check_mentions(slot: int, dry_run: bool = False) -> dict:
    """Check and respond to mentions."""
    print(f"\n  Checking mentions...")

    if dry_run:
        print("  [DRY RUN] Would check mentions via twitter_reply.py")
        return {"status": "dry_run", "activity": "check_mentions"}

    try:
        client, _ = create_twitter_clients()

        # Get authenticated user ID
        me = client.get_me()
        user_id = me.data.id

        # Get recent mentions
        mentions = client.get_users_mentions(
            id=user_id,
            max_results=10,
            tweet_fields=["created_at", "text", "author_id"],
        )

        mention_count = 0
        if mentions.data:
            mention_count = len(mentions.data)
            print(f"  Found {mention_count} recent mentions")
            for m in mentions.data[:5]:
                print(f"    - @{m.author_id}: {m.text[:60]}...")
        else:
            print("  No new mentions")

        log_activity(slot, "check_mentions", {"mention_count": mention_count})
        return {"status": "ok", "mention_count": mention_count}

    except Exception as e:
        logger.warning(f"Mention check failed (may be API tier limit): {e}")
        log_activity(slot, "check_mentions", {"error": str(e)})
        return {"status": "limited", "error": str(e)}


def execute_engage(slot: int, dry_run: bool = False) -> dict:
    """Like and engage with parenting community tweets."""
    config = SLOT_CONFIG[slot]
    target_count = config.get("engage_count", 5)
    hashtags = config.get("engage_hashtags", ["#育児", "#ストローマグ"])

    print(f"\n  Community engagement (target: {target_count} interactions)")
    print(f"  Hashtags: {', '.join(hashtags)}")

    if dry_run:
        print(f"  [DRY RUN] Would search & like {target_count} tweets")
        return {"status": "dry_run", "target": target_count}

    try:
        client, _ = create_twitter_clients()
        liked_count = 0

        for tag in hashtags[:2]:  # Limit to 2 hashtags per session
            query = f"{tag} lang:ja -is:retweet"
            try:
                tweets = client.search_recent_tweets(
                    query=query,
                    max_results=10,
                    tweet_fields=["created_at", "public_metrics"],
                )
                if tweets.data:
                    for tweet in tweets.data[:target_count // 2]:
                        try:
                            client.like(tweet.id)
                            liked_count += 1
                            print(f"    Liked: {tweet.text[:50]}...")
                            time.sleep(2)  # Rate limit courtesy
                        except Exception as e:
                            logger.debug(f"Like failed: {e}")
                            break

                time.sleep(3)  # Between searches

            except Exception as e:
                logger.warning(f"Search for {tag} failed: {e}")

            if liked_count >= target_count:
                break

        print(f"  Engaged with {liked_count} tweets")
        log_activity(slot, "engage", {"liked": liked_count, "hashtags": hashtags})
        return {"status": "ok", "liked": liked_count}

    except Exception as e:
        logger.warning(f"Engagement failed: {e}")
        return {"status": "limited", "error": str(e)}


def execute_heavy_engage(slot: int, dry_run: bool = False) -> dict:
    """Heavy engagement session (prime time)."""
    print(f"\n  PRIME TIME engagement session (19:00)")
    result = execute_engage(slot, dry_run=dry_run)
    result["type"] = "heavy_engage"
    return result


def execute_follow(slot: int, dry_run: bool = False) -> dict:
    """Follow new parenting accounts."""
    config = SLOT_CONFIG[slot]
    target = config.get("follow_count", 3)

    print(f"\n  Follow new accounts (target: {target})")

    if dry_run:
        print(f"  [DRY RUN] Would follow {target} parenting accounts")
        return {"status": "dry_run", "target": target}

    # Following is limited on free tier — log intent
    print(f"  Note: Follow is manual on free tier. Recommended accounts to follow:")
    print(f"    Search: #育児垢さんと繋がりたい")
    print(f"    Search: #ママさんと繋がりたい")

    log_activity(slot, "follow_reminder", {"target": target})
    return {"status": "reminder", "target": target}


def execute_quote_rt(slot: int, dry_run: bool = False) -> dict:
    """Quote retweet a relevant trending tweet (max 1/day)."""
    # Check if we already did a quote RT today
    today_activities = get_today_activities()
    if any(a["activity"] == "quote_rt" for a in today_activities):
        print("  Already did a quote RT today (limit: 1/day)")
        return {"status": "skipped", "reason": "daily_limit"}

    print(f"\n  Quote RT check (max 1/day)")

    if dry_run:
        print("  [DRY RUN] Would search for quotable trending content")
        return {"status": "dry_run"}

    # For free tier, this is mostly a manual activity
    print("  Recommended: Search Twitter for trending parenting content to quote RT")
    print("  Template: わかります！✨ [your comment] #育児 #ストローマグ")

    log_activity(slot, "quote_rt_reminder", {})
    return {"status": "reminder"}


def execute_analytics(slot: int, dry_run: bool = False) -> dict:
    """Collect daily analytics."""
    print(f"\n  Daily analytics collection")

    if dry_run:
        print("  [DRY RUN] Would collect analytics")
        return {"status": "dry_run"}

    try:
        client, _ = create_twitter_clients()
        me = client.get_me(user_fields=["public_metrics"])

        if me.data:
            metrics = me.data.public_metrics if hasattr(me.data, 'public_metrics') else {}
            print(f"  Followers: {metrics.get('followers_count', 'N/A')}")
            print(f"  Following: {metrics.get('following_count', 'N/A')}")
            print(f"  Tweets: {metrics.get('tweet_count', 'N/A')}")

            log_activity(slot, "analytics", {
                "followers": metrics.get("followers_count"),
                "following": metrics.get("following_count"),
                "tweets": metrics.get("tweet_count"),
            })
            return {"status": "ok", "metrics": metrics}

    except Exception as e:
        logger.warning(f"Analytics failed: {e}")

    return {"status": "limited"}


def execute_plan_tomorrow(slot: int, dry_run: bool = False) -> dict:
    """Check if tomorrow's content is planned."""
    print(f"\n  Tomorrow's content check")

    today_posts = [
        a for a in get_today_activities()
        if a["activity"] == "post" and a.get("tweet_id")
    ]
    print(f"  Today's posts: {len(today_posts)}")

    tracker = BudgetTracker()
    counts = tracker.get_counts()
    print(f"  Budget remaining: {counts['remaining_today']} today / {counts['remaining_month']} month")

    log_activity(slot, "plan_check", {
        "today_posts": len(today_posts),
        "budget_today": counts["remaining_today"],
        "budget_month": counts["remaining_month"],
    })
    return {"status": "ok", "today_posts": len(today_posts)}


def execute_reply_to_engagement(slot: int, dry_run: bool = False) -> dict:
    """Reply to engagement on our recent tweets."""
    print(f"\n  Checking engagement on our tweets...")

    if dry_run:
        print("  [DRY RUN] Would check replies on recent tweets")
        return {"status": "dry_run"}

    # This is limited on free tier
    print("  Note: Reply monitoring is limited on current API tier")
    print("  Recommended: Manually check notifications on x.com")

    log_activity(slot, "reply_check", {})
    return {"status": "reminder"}


# ── Activity Router ──────────────────────────────────────────────────────

ACTIVITY_MAP = {
    "post": execute_post,
    "check_mentions": execute_check_mentions,
    "engage": execute_engage,
    "heavy_engage": execute_heavy_engage,
    "follow": execute_follow,
    "quote_rt": execute_quote_rt,
    "analytics": execute_analytics,
    "plan_tomorrow": execute_plan_tomorrow,
    "reply_to_engagement": execute_reply_to_engagement,
}


def run_slot(slot: int, dry_run: bool = False) -> dict:
    """Execute all activities for a time slot."""
    if slot not in VALID_SLOTS:
        print(f"Invalid slot: {slot}. Valid: {VALID_SLOTS}")
        return {"status": "invalid_slot"}

    config = SLOT_CONFIG[slot]
    now = get_jst_now()

    print(f"\n{'#'*60}")
    print(f"  Twitter Agent — Slot {slot}:00 JST")
    print(f"  {config['name']} / {config['name_ko']}")
    print(f"  {now.strftime('%Y-%m-%d %H:%M JST')}")
    print(f"  Today's theme: {get_dow_content_type()}")
    print(f"  Activities: {', '.join(config['activities'])}")
    print(f"{'#'*60}")

    results = {}
    for activity in config["activities"]:
        executor = ACTIVITY_MAP.get(activity)
        if executor:
            try:
                results[activity] = executor(slot, dry_run=dry_run)
            except Exception as e:
                logger.error(f"Activity {activity} failed: {e}")
                results[activity] = {"status": "error", "error": str(e)}
        else:
            logger.warning(f"Unknown activity: {activity}")

    # Summary
    print(f"\n{'─'*60}")
    print(f"  Slot {slot} Summary:")
    for act, res in results.items():
        status = res.get("status", "unknown")
        print(f"    {act}: {status}")
    print(f"{'─'*60}\n")

    return {"slot": slot, "results": results}


def show_status():
    """Show today's agent activity status."""
    now = get_jst_now()
    today = get_today_activities()

    print(f"\n{'='*60}")
    print(f"  Twitter Agent Status")
    print(f"  {now.strftime('%Y-%m-%d %H:%M JST')}")
    print(f"  Today's theme: {get_dow_content_type()}")
    print(f"{'='*60}")

    # Budget
    tracker = BudgetTracker()
    counts = tracker.get_counts()
    print(f"\n  Budget:")
    print(f"    Today: {counts['today']}/{50} (remaining: {counts['remaining_today']})")
    print(f"    Month: {counts['month']}/{1500} (remaining: {counts['remaining_month']})")

    # Today's activities by slot
    print(f"\n  Today's Activities ({len(today)} total):")
    for slot in VALID_SLOTS:
        slot_acts = [a for a in today if a.get("slot") == slot]
        if slot_acts:
            acts_str = ", ".join(a["activity"] for a in slot_acts)
            print(f"    {slot}:00 ✓ {acts_str}")
        else:
            config = SLOT_CONFIG[slot]
            if now.hour >= slot:
                print(f"    {slot}:00 ✗ (missed) — {config['name_ko']}")
            else:
                print(f"    {slot}:00 ○ (upcoming) — {config['name_ko']}")

    # Recent posts
    posts = [a for a in today if a["activity"] == "post" and a.get("tweet_id")]
    if posts:
        print(f"\n  Today's Posts:")
        for p in posts:
            print(f"    [{p['slot']}:00] {p.get('text', '')[:50]}...")
            if p.get("ko_translation"):
                print(f"           KO: {p['ko_translation'][:50]}...")

    print()


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Grosmimi Japan Twitter Agent (中の人 strategy)"
    )
    parser.add_argument(
        "--slot", type=str,
        help="Time slot to run (9,11,13,15,17,19,21 or 'auto')"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview activities without executing"
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Show today's activity status"
    )
    parser.add_argument(
        "--full-day", action="store_true",
        help="Run all 7 slots sequentially (for testing)"
    )
    parser.add_argument(
        "--post-only", action="store_true",
        help="Only run the posting activity for the slot"
    )
    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if args.full_day:
        print("Running full day simulation...")
        for slot in VALID_SLOTS:
            run_slot(slot, dry_run=args.dry_run)
            if not args.dry_run:
                time.sleep(5)
        return

    if not args.slot:
        parser.print_help()
        print(f"\nValid slots: {VALID_SLOTS}")
        print(f"Current JST: {get_jst_now().strftime('%H:%M')}")
        return

    # Determine slot
    if args.slot == "auto":
        current_hour = get_jst_now().hour
        # Find the closest slot at or before current time
        slot = max((s for s in VALID_SLOTS if s <= current_hour), default=VALID_SLOTS[0])
        print(f"Auto-detected slot: {slot} (current JST: {current_hour}:xx)")
    else:
        slot = int(args.slot)

    if args.post_only:
        # Override: only run post activity
        execute_post(slot, dry_run=args.dry_run)
    else:
        run_slot(slot, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
