# Instagram コンテンツ運営ワークフロー
> 最終更新: 2026-02-26

---

## 役割
Grosmimi Japan のInstagramコンテンツを **企画 → 制作 → 投稿** まで担当。
Claude Codeに指示を出して、ツールを実行する形で進める。

---

## 日常ルーティン

### 毎朝やること (10分)
1. **競合チェック** — 競合のInstagramを確認
2. **アイデア出し** — Claudeにアイデアを相談
3. **Teamsに共有** — プランをContents Planningチャネルに投稿

### 週1回やること
1. **競合データ更新** — スクレイピングツール実行
2. **来週のプラン作成** — 7日分のコンテンツプラン
3. **Excelアップロード** — TeamsのSharePointに更新版をアップ

---

## 使えるツール

### 1. 競合Instagram分析（無料・API不要）
```bash
# 全競合（b.box, Pigeon, Richell, Thermos）
python tools/scrape_ig_competitor.py

# 特定アカウント
python tools/scrape_ig_competitor.py bboxforkidsjapan --max 10

# 画像なし（メタデータのみ）
python tools/scrape_ig_competitor.py --no-images

# プレビュー
python tools/scrape_ig_competitor.py --dry-run
```
→ `.tmp/competitor_refs/` に画像＋メタデータ保存
→ Claudeに「このフォルダの画像を分析して」と頼める

### 2. コンテンツ企画
```bash
# 1件企画
python tools/plan_content.py

# 7日分
python tools/plan_content.py --count 7

# カルーセル形式
python tools/plan_content.py --format carousel

# テーマ指定
python tools/plan_content.py --topic "夜泣き"
```
→ `.tmp/content_plan.json`

### 3. Teams共有（Contents Planningチャネル）
```bash
# プランをカードで投稿
python tools/teams_content.py --post-plan

# Excelアップロード＋通知
python tools/teams_content.py --upload "ファイル名.xlsx" --notify

# テスト
python tools/teams_content.py --test
```

### 4. Instagram投稿
```bash
# 次の投稿を実行
python tools/post_instagram.py

# ドライラン（テスト）
python tools/post_instagram.py --dry-run
```

---

## 1日の流れ（例）

### Step 1: 競合チェック
Claudeに:
> 「競合の最新投稿をスクレイピングして、トレンドを分析して」

手動の場合:
- 競合Instagramのスクショを `.tmp/competitor_refs/manual/` に保存
- Claudeに「この画像を分析して」

### Step 2: アイデア出し
Claudeに:
> 「今週のInstagramコンテンツを7件企画して」
> 「b.boxのディズニーコラボが人気。PPSUの安全性で対抗するアイデアを」

### Step 3: Teams共有
Claudeに:
> 「プランをContents Planningチャネルに投稿して」

### Step 4: フィードバック反映
- Teamsでチームのコメント確認
- 修正 → Excel更新 → アップロード

### Step 5: 投稿
> 「ドライランで確認して」 → 「OK、本番投稿」

---

## 参考資料

| ファイル | 内容 |
|---------|------|
| `workflows/jp_competitor_insights.md` | 競合分析（b.box, Pigeon等） |
| `workflows/jp_content_creation.md` | コンテンツ作成ガイド |
| `workflows/jp_brand_guideline.md` | ブランドガイドライン |
| `workflows/ig_competitor_analysis.md` | 競合分析ワークフロー |

---

## 注意点
- 画像生成はClaude単体不可 → プロンプトを出してもらい別途生成
- 投稿前に必ず `--dry-run`
- Teams通知は適度に（通知疲れ防止）
- スクレイピングエラー → picuki構造変更の可能性、Claudeに修正依頼
- IG投稿エラー → `python tools/refresh_ig_token.py` でトークン更新
