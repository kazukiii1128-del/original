# Apify Twitter ツール セットアップガイド

## 概要

Apifyを使った競合X(Twitter)モニタリングとトレンド収集ツール。
既存の `twitter_research.py` (Firecrawl版) と `twitter_hashtag.py` を **補完** する安定版。

**既存ツールを壊しません** — 両方を並行して使えます。

## ファイル一覧

| ファイル | 用途 | 配置先 |
|----------|------|--------|
| `apify_twitter_monitor.py` | 競合11ブランドのX運用モニタリング | `tools/` |
| `apify_twitter_trends.py` | JP育児ハッシュタグ・トレンド収集 | `tools/` |
| `apify_twitter_daily.yml` | GitHub Actions 自動実行 | `.github/workflows/` |

## セットアップ手順

### 1. ファイル配置

```bash
# ツール
cp apify_twitter_monitor.py  /path/to/kazuki/tools/
cp apify_twitter_trends.py   /path/to/kazuki/tools/

# GitHub Actions workflow
cp apify_twitter_daily.yml   /path/to/kazuki/.github/workflows/
```

### 2. 依存パッケージ

```bash
pip install apify-client openpyxl requests
```

### 3. API トークン設定

#### ローカル (.env)
```env
# .env に追加
APIFY_API_TOKEN=apify_api_XXXXXXXXXXXX
```

#### GitHub Actions (Secrets)
1. GitHub → Settings → Secrets → Actions
2. `APIFY_API_TOKEN` を追加
3. (オプション) `TEAMS_WEBHOOK_URL` を追加

### 4. テスト実行

```bash
# 競合モニタリング (dry-run)
python tools/apify_twitter_monitor.py --dry-run

# トレンド収集 (dry-run)
python tools/apify_twitter_trends.py --dry-run

# 本番実行 (ファイル保存 + Teams通知)
python tools/apify_twitter_monitor.py --notify
python tools/apify_twitter_trends.py --notify
```

## 既存ツールとの関係

| 既存ツール | Apify版 | 違い |
|-----------|---------|------|
| `twitter_research.py` | `apify_twitter_monitor.py` | Firecrawl→Apify。構造化データで安定 |
| `twitter_hashtag.py` | `apify_twitter_trends.py` | Firecrawl→Apify。ハッシュタグ頻度が正確 |
| `chousa.yml` | `apify_twitter_daily.yml` | 並行運用可能。Apify版は構造化JSON出力 |
| `hashtag.yml` | `apify_twitter_daily.yml` | 金曜のみトレンド収集。並行運用可能 |

**推奨:** しばらく両方を並行運用して、Apify版の安定性を確認後に切り替え。

## スケジュール

| 時間 (JST) | 内容 | GitHub Actions |
|-----------|------|---------------|
| 毎日 09:00 | 競合Xモニタリング | `apify_twitter_daily.yml` |
| 毎週金曜 09:00 | トレンド収集 | `apify_twitter_daily.yml` |

## 出力ファイル

```
.tmp/
  apify_twitter_monitor_20260319_0900.json   # 競合データ (JSON)
  apify_twitter_monitor_20260319_0900.xlsx   # 競合データ (Excel/Teams用)
  apify_twitter_trends_20260319_0900.json    # トレンド (JSON)
  apify_twitter_trends_20260319_0900.xlsx    # トレンド (Excel/Teams用)
```

## コスト

Apify Free Tier: 月$5のクレジット付き。
twitter-scraper: 1回のスキャン (11ブランド × 10ツイート) ≈ $0.50程度。
月間コスト目安: ~$15-20 (毎日モニタリング + 週次トレンド)

## トラブルシューティング

### APIFY_API_TOKEN が設定されていない
```
APIFY_API_TOKEN not set. Set it in .env or environment.
```
→ `.env` に `APIFY_API_TOKEN=apify_api_...` を追加

### apify-client がインストールされていない
```
apify-client not installed
```
→ `pip install apify-client`

### Twitter/X のレート制限
→ Apify Proxyが自動的にハンドルするので、通常は問題なし
→ もしエラーが続く場合は `TIMEOUT_SECS` を増やす
