# 🚀 Apify Twitter ツール — セットアップ＆テスト

MJ先輩からApifyを使った競合モニタリング＆トレンド収集ツールが届きました。
以下の手順で有効化してテストしてください。

---

## 📦 新しく追加されたファイル

| ファイル | 場所 | 内容 |
|---------|------|------|
| `apify_twitter_monitor.py` | `tools/` | 競合11ブランドのXアカウント自動モニタリング（フォロワー数、エンゲージメント、ハッシュタグ分析） |
| `apify_twitter_trends.py` | `tools/` | JP育児ハッシュタグ＆トレンドキーワード自動収集（13キーワード検索） |
| `apify_twitter_daily.yml` | `.github/workflows/` | GitHub Actionsで毎日09:00 JST自動実行 |
| `APIFY_SETUP.md` | プロジェクトルート | 詳細セットアップガイド |

**既存ツール（twitter_research.py、twitter_hashtag.py）はそのまま残っています。壊しません。**

---

## ⚡ セットアップ手順（Claude実行用）

### Step 1: 依存パッケージインストール

```bash
pip install apify-client openpyxl requests
```

### Step 2: .env にAPIトークン追加

`.env` ファイルに以下を追加してください：

```
APIFY_API_TOKEN=your_apify_api_token_here
```

**確認コマンド：**
```bash
grep APIFY .env
```

### Step 3: Dry-runテスト

**競合モニタリング（Apifyクレジット消費なしでコード検証）：**
```bash
python tools/apify_twitter_monitor.py --dry-run
```

**トレンド収集：**
```bash
python tools/apify_twitter_trends.py --dry-run
```

### Step 4: 本番テスト（1ブランドだけ）

Apifyクレジットを最小限に使って動作確認：
```bash
python tools/apify_twitter_monitor.py --brand ピジョン --json
```

成功すれば、ピジョンのフォロワー数、最新ツイート、エンゲージメントスコアが表示されます。

### Step 5: GitHub Actions設定

GitHubリポジトリの Settings → Secrets → Actions に追加：
- `APIFY_API_TOKEN` = 上記のトークン値
- `TEAMS_WEBHOOK_URL` = 既存のTeams Webhook URL（あれば）

ワークフローは自動でスケジュール実行されます：
- **毎日 09:00 JST**: 競合Xモニタリング
- **毎週金曜 09:00 JST**: トレンド収集

---

## 📊 使い方まとめ

```bash
# === 競合モニタリング ===
python tools/apify_twitter_monitor.py                  # 全ブランドスキャン
python tools/apify_twitter_monitor.py --brand ピジョン   # 特定ブランドのみ
python tools/apify_twitter_monitor.py --notify          # Teams通知付き
python tools/apify_twitter_monitor.py --json            # JSON出力

# === トレンド収集 ===
python tools/apify_twitter_trends.py                    # 全キーワード検索
python tools/apify_twitter_trends.py --notify           # Teams通知付き
python tools/apify_twitter_trends.py --json             # JSON出力
```

---

## 🔄 既存ツールとの関係

| 用途 | 既存（Firecrawl） | 新規（Apify） | 違い |
|------|-------------------|--------------|------|
| 競合分析 | `twitter_research.py` | `apify_twitter_monitor.py` | 構造化データで安定 |
| ハッシュタグ | `twitter_hashtag.py` | `apify_twitter_trends.py` | 頻度カウントが正確 |
| GHA | `chousa.yml` + `hashtag.yml` | `apify_twitter_daily.yml` | 並行運用可能 |

**推奨**: しばらく両方を並行運用 → Apify版が安定したら切り替え

---

## 📁 出力ファイル

実行後、`.tmp/` に以下が生成されます：
- `apify_twitter_monitor_YYYYMMDD_HHMM.json` — 競合データ
- `apify_twitter_monitor_YYYYMMDD_HHMM.xlsx` — Excel（Teams送信用）
- `apify_twitter_trends_YYYYMMDD_HHMM.json` — トレンド
- `apify_twitter_trends_YYYYMMDD_HHMM.xlsx` — Excel（Teams送信用）

---

## ❓ トラブルシューティング

**`APIFY_API_TOKEN not set`** → `.env` にトークンが追加されているか確認
**`apify-client not installed`** → `pip install apify-client` を実行
**タイムアウト** → ネットワーク確認、Apifyダッシュボードでクレジット残高確認

MJ先輩に聞いてもOKです 👍
