# マーケットプレイス デイリーレポート 実装プラン

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `/デイリーレポート` コマンドを入力すると、楽天・Amazonのデータを自動集計し、韓国語でレポートをチャット出力する

**Architecture:** Pythonツールがデータ取得・集計を担当しJSON出力。Claudeがコマンドファイルの指示に従いツールを実行、ユーザー入力と統合してレポートをフォーマットする。

**Tech Stack:** Python 3.12, Rakuten RMS API, DataKeeper (local JSON), `.claude/commands/` slash command

---

## ファイル構成

| ファイル | 種別 | 役割 |
|---------|------|------|
| `tools/marketplace_daily_report.py` | 新規作成 | 楽天・Amazon データ取得・集計、JSON出力 |
| `tests/test_marketplace_daily_report.py` | 新規作成 | ユニットテスト |
| `.claude/commands/デイリーレポート.md` | 新規作成 | `/デイリーレポート` スラッシュコマンド定義 |
| `workflows/marketplace_daily_report.md` | 新規作成 | Claude用ワークフローSOP |

---

## Task 1: テスト用フィクスチャとテストファイルの骨格を作成

**Files:**
- Create: `tests/test_marketplace_daily_report.py`
- Create: `tests/fixtures/amazon_sales_sample.json`
- Create: `tests/fixtures/amazon_ads_sample.json`

- [ ] **Step 1: フィクスチャ作成 — Amazon sales**

`tests/fixtures/amazon_sales_sample.json` を作成:

```json
[
  {"date": "2026-04-13", "brand": "Grosmimi", "gross_sales": 150.00, "net_sales": 120.00, "orders": 2, "units": 3, "fees": 30.00, "refunds": 0.0},
  {"date": "2026-04-13", "brand": "Naeiae",   "gross_sales": 80.00,  "net_sales": 65.00,  "orders": 1, "units": 1, "fees": 15.00, "refunds": 0.0},
  {"date": "2026-04-12", "brand": "Grosmimi", "gross_sales": 200.00, "net_sales": 160.00, "orders": 3, "units": 4, "fees": 40.00, "refunds": 0.0}
]
```

- [ ] **Step 2: フィクスチャ作成 — Amazon ads**

`tests/fixtures/amazon_ads_sample.json` を作成:

```json
[
  {"date": "2026-04-13", "brand": "Grosmimi", "spend": 45.00, "sales": 180.00, "clicks": 120, "impressions": 5000, "orders": 3},
  {"date": "2026-04-13", "brand": "Naeiae",   "spend": 20.00, "sales": 60.00,  "clicks": 55,  "impressions": 2000, "orders": 1},
  {"date": "2026-04-12", "brand": "Grosmimi", "spend": 50.00, "sales": 200.00, "clicks": 130, "impressions": 5200, "orders": 4}
]
```

- [ ] **Step 3: テストファイルの骨格を作成**

`tests/test_marketplace_daily_report.py` を作成:

```python
"""Tests for marketplace_daily_report.py"""
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

FIXTURES = Path(__file__).parent / "fixtures"


def test_fetch_amazon_sales_returns_totals():
    pass  # Task 2で実装


def test_fetch_amazon_ads_computes_roas():
    pass  # Task 3で実装


def test_fetch_amazon_sales_empty_date():
    pass  # Task 2で実装
```

- [ ] **Step 4: テストが実行できることを確認**

```bash
cd c:/Users/Puser/Desktop/kazuki
python -m pytest tests/test_marketplace_daily_report.py -v
```

Expected: 3 tests PASSED (全部 `pass` なので通る)

- [ ] **Step 5: コミット**

```bash
git add tests/test_marketplace_daily_report.py tests/fixtures/
git commit -m "test: デイリーレポート用フィクスチャとテスト骨格を追加"
```

---

## Task 2: Amazon売上集計関数の実装

**Files:**
- Create: `tools/marketplace_daily_report.py`
- Modify: `tests/test_marketplace_daily_report.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_marketplace_daily_report.py` の `test_fetch_amazon_sales_returns_totals` を更新:

```python
def test_fetch_amazon_sales_returns_totals():
    from marketplace_daily_report import fetch_amazon_sales
    result = fetch_amazon_sales("2026-04-13", data_file=FIXTURES / "amazon_sales_sample.json")
    assert result["total_orders"] == 3
    assert result["total_units"] == 4
    assert abs(result["total_gross"] - 230.00) < 0.01
    assert abs(result["total_net"] - 185.00) < 0.01
    assert "Grosmimi" in result["brands"]
    assert result["brands"]["Grosmimi"]["orders"] == 2


def test_fetch_amazon_sales_empty_date():
    from marketplace_daily_report import fetch_amazon_sales
    result = fetch_amazon_sales("2099-01-01", data_file=FIXTURES / "amazon_sales_sample.json")
    assert result["total_orders"] == 0
    assert result["total_gross"] == 0.0
    assert result["brands"] == {}
```

- [ ] **Step 2: テスト失敗を確認**

```bash
python -m pytest tests/test_marketplace_daily_report.py::test_fetch_amazon_sales_returns_totals -v
```

Expected: FAIL with `ModuleNotFoundError` or `ImportError`

- [ ] **Step 3: `tools/marketplace_daily_report.py` を作成、Amazon売上集計を実装**

```python
"""
WAT Tool: マーケットプレイス デイリーレポート データ集計

楽天・Amazon の売上・注文・広告データを集計してJSON出力する。

Usage:
  python tools/marketplace_daily_report.py
  python tools/marketplace_daily_report.py --date 2026-04-13
"""
import sys
import io
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

JST = timezone(timedelta(hours=9))
DATAKEEPER = Path(__file__).parent.parent.parent / "Shared" / "datakeeper" / "latest"


def fetch_amazon_sales(report_date: str, data_file: Path = None) -> dict:
    """DataKeeperからAmazon売上を集計して返す。"""
    path = data_file or (DATAKEEPER / "amazon_sales_daily.json")
    if not path.exists():
        return {"error": f"DataKeeper file not found: {path}", "total_orders": 0, "total_units": 0, "total_gross": 0.0, "total_net": 0.0, "brands": {}}

    with open(path, encoding="utf-8") as f:
        rows = json.load(f)

    brands = defaultdict(lambda: {"orders": 0, "units": 0, "gross_sales": 0.0, "net_sales": 0.0, "fees": 0.0, "refunds": 0.0})
    for row in rows:
        if row.get("date") != report_date:
            continue
        b = row.get("brand", "Unknown")
        brands[b]["orders"]     += row.get("orders", 0)
        brands[b]["units"]      += row.get("units", 0)
        brands[b]["gross_sales"] += row.get("gross_sales", 0.0)
        brands[b]["net_sales"]  += row.get("net_sales", 0.0)
        brands[b]["fees"]       += row.get("fees", 0.0)
        brands[b]["refunds"]    += row.get("refunds", 0.0)

    brands_dict = dict(brands)
    return {
        "total_orders": sum(b["orders"] for b in brands_dict.values()),
        "total_units":  sum(b["units"]  for b in brands_dict.values()),
        "total_gross":  sum(b["gross_sales"] for b in brands_dict.values()),
        "total_net":    sum(b["net_sales"]   for b in brands_dict.values()),
        "brands": brands_dict,
    }
```

- [ ] **Step 4: テスト通過を確認**

```bash
python -m pytest tests/test_marketplace_daily_report.py::test_fetch_amazon_sales_returns_totals tests/test_marketplace_daily_report.py::test_fetch_amazon_sales_empty_date -v
```

Expected: 2 tests PASSED

- [ ] **Step 5: コミット**

```bash
git add tools/marketplace_daily_report.py tests/test_marketplace_daily_report.py
git commit -m "feat: Amazon売上集計関数を実装"
```

---

## Task 3: Amazon広告集計関数の実装

**Files:**
- Modify: `tools/marketplace_daily_report.py`
- Modify: `tests/test_marketplace_daily_report.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_marketplace_daily_report.py` の `test_fetch_amazon_ads_computes_roas` を更新:

```python
def test_fetch_amazon_ads_computes_roas():
    from marketplace_daily_report import fetch_amazon_ads
    result = fetch_amazon_ads("2026-04-13", data_file=FIXTURES / "amazon_ads_sample.json")
    assert abs(result["total_spend"] - 65.00) < 0.01
    assert abs(result["total_sales"] - 240.00) < 0.01
    assert abs(result["roas"] - (240.00 / 65.00)) < 0.01
    assert result["total_clicks"] == 175


def test_fetch_amazon_ads_zero_spend():
    from marketplace_daily_report import fetch_amazon_ads
    result = fetch_amazon_ads("2099-01-01", data_file=FIXTURES / "amazon_ads_sample.json")
    assert result["total_spend"] == 0.0
    assert result["roas"] == 0.0
```

- [ ] **Step 2: テスト失敗を確認**

```bash
python -m pytest tests/test_marketplace_daily_report.py::test_fetch_amazon_ads_computes_roas -v
```

Expected: FAIL with `ImportError: cannot import name 'fetch_amazon_ads'`

- [ ] **Step 3: `fetch_amazon_ads` を `marketplace_daily_report.py` に追加**

`fetch_amazon_sales` の後に追加:

```python
def fetch_amazon_ads(report_date: str, data_file: Path = None) -> dict:
    """DataKeeperからAmazon広告データを集計して返す。"""
    path = data_file or (DATAKEEPER / "amazon_ads_daily.json")
    if not path.exists():
        return {"error": f"DataKeeper file not found: {path}", "total_spend": 0.0, "total_sales": 0.0, "total_clicks": 0, "total_impressions": 0, "roas": 0.0, "cpc": 0.0}

    with open(path, encoding="utf-8") as f:
        rows = json.load(f)

    total_spend = 0.0
    total_sales = 0.0
    total_clicks = 0
    total_impressions = 0

    for row in rows:
        if row.get("date") != report_date:
            continue
        total_spend       += row.get("spend", 0.0)
        total_sales       += row.get("sales", 0.0)
        total_clicks      += row.get("clicks", 0)
        total_impressions += row.get("impressions", 0)

    roas = round(total_sales / total_spend, 2) if total_spend > 0 else 0.0
    cpc  = round(total_spend / total_clicks, 2) if total_clicks > 0 else 0.0

    return {
        "total_spend":       total_spend,
        "total_sales":       total_sales,
        "total_clicks":      total_clicks,
        "total_impressions": total_impressions,
        "roas": roas,
        "cpc":  cpc,
    }
```

- [ ] **Step 4: テスト通過を確認**

```bash
python -m pytest tests/test_marketplace_daily_report.py -v
```

Expected: 全テスト PASSED

- [ ] **Step 5: コミット**

```bash
git add tools/marketplace_daily_report.py tests/test_marketplace_daily_report.py
git commit -m "feat: Amazon広告集計関数を実装"
```

---

## Task 4: 楽天売上集計関数の実装

**Files:**
- Modify: `tools/marketplace_daily_report.py`
- Modify: `tests/test_marketplace_daily_report.py`

- [ ] **Step 1: 失敗するテストを書く**

```python
def test_fetch_rakuten_returns_totals():
    from marketplace_daily_report import fetch_rakuten_sales
    # RMS APIをモック
    mock_orders = [
        {
            "orderDatetime": "2026-04-13T10:00:00+09:00",
            "PackageModelList": [{"ItemModelList": [
                {"manageNumber": "SKU-001", "units": 2, "priceTaxIncl": 3000, "itemName": "【グロミミ公式】商品A/サイズS"}
            ]}]
        },
        {
            "orderDatetime": "2026-04-13T15:00:00+09:00",
            "PackageModelList": [{"ItemModelList": [
                {"manageNumber": "SKU-002", "units": 1, "priceTaxIncl": 5000, "itemName": "商品B"}
            ]}]
        },
        {
            "orderDatetime": "2026-04-12T10:00:00+09:00",  # 対象外の日付
            "PackageModelList": [{"ItemModelList": [
                {"manageNumber": "SKU-001", "units": 5, "priceTaxIncl": 3000, "itemName": "商品A"}
            ]}]
        },
    ]
    with patch("marketplace_daily_report.RakutenRMSClient") as MockClient:
        inst = MockClient.return_value
        inst.search_order_numbers.return_value = ["1", "2", "3"]
        inst.get_orders.return_value = mock_orders
        result = fetch_rakuten_sales("2026-04-13")

    assert result["total_orders"] == 2
    assert result["total_units"] == 3
    assert abs(result["total_sales"] - 11000.0) < 0.01  # 3000*2 + 5000*1
```

`test_marketplace_daily_report.py` の先頭のimportに追加:

```python
from unittest.mock import patch, MagicMock
```

- [ ] **Step 2: テスト失敗を確認**

```bash
python -m pytest tests/test_marketplace_daily_report.py::test_fetch_rakuten_returns_totals -v
```

Expected: FAIL with `ImportError: cannot import name 'fetch_rakuten_sales'`

- [ ] **Step 3: `fetch_rakuten_sales` を `marketplace_daily_report.py` に追加**

ファイル先頭のimport群に追加:

```python
from collections import defaultdict
```

`fetch_amazon_ads` の後に追加:

```python
CONFIG = Path(__file__).parent.parent / "credentials" / "rakuten_rms_config.json"

# RakutenRMSClientをimport（tools/内から）
sys.path.insert(0, str(Path(__file__).parent))
from rakuten_rms_client import RakutenRMSClient


def fetch_rakuten_sales(report_date: str) -> dict:
    """Rakuten RMS APIから売上を集計して返す。"""
    if not CONFIG.exists():
        return {"error": f"RMS config not found: {CONFIG}", "total_orders": 0, "total_units": 0, "total_sales": 0.0}

    try:
        client = RakutenRMSClient(str(CONFIG))
        today = datetime.now(JST).date()
        target = datetime.strptime(report_date, "%Y-%m-%d").date()
        days_back = (today - target).days + 1
        order_numbers = client.search_order_numbers(days=days_back)
        if not order_numbers:
            return {"total_orders": 0, "total_units": 0, "total_sales": 0.0}
        orders = client.get_orders(order_numbers)
    except Exception as e:
        return {"error": str(e), "total_orders": 0, "total_units": 0, "total_sales": 0.0}

    total_orders = 0
    total_units = 0
    total_sales = 0.0

    for o in orders:
        order_date = (o.get("orderDatetime") or "")[:10]
        if order_date != report_date:
            continue
        total_orders += 1
        for pkg in (o.get("PackageModelList") or []):
            for item in (pkg.get("ItemModelList") or []):
                units = int(item.get("units") or 1)
                price = float(item.get("priceTaxIncl") or item.get("price") or 0)
                total_units += units
                total_sales += price * units

    return {
        "total_orders": total_orders,
        "total_units":  total_units,
        "total_sales":  total_sales,
    }
```

- [ ] **Step 4: テスト通過を確認**

```bash
python -m pytest tests/test_marketplace_daily_report.py -v
```

Expected: 全テスト PASSED

- [ ] **Step 5: コミット**

```bash
git add tools/marketplace_daily_report.py tests/test_marketplace_daily_report.py
git commit -m "feat: 楽天売上集計関数を実装"
```

---

## Task 5: `main()` とJSON出力の実装

**Files:**
- Modify: `tools/marketplace_daily_report.py`
- Modify: `tests/test_marketplace_daily_report.py`

- [ ] **Step 1: 失敗するテストを書く**

```python
def test_main_outputs_valid_json(tmp_path, capsys):
    from marketplace_daily_report import main
    # Amazon sales/adsのDataKeeperファイルをtmp_pathにコピー
    import shutil
    sales_src = FIXTURES / "amazon_sales_sample.json"
    ads_src   = FIXTURES / "amazon_ads_sample.json"
    sales_dst = tmp_path / "amazon_sales_daily.json"
    ads_dst   = tmp_path / "amazon_ads_daily.json"
    shutil.copy(sales_src, sales_dst)
    shutil.copy(ads_src, ads_dst)

    with patch("marketplace_daily_report.DATAKEEPER", tmp_path), \
         patch("marketplace_daily_report.RakutenRMSClient") as MockClient:
        inst = MockClient.return_value
        inst.search_order_numbers.return_value = []
        main(["--date", "2026-04-13"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["date"] == "2026-04-13"
    assert "amazon_sales" in data
    assert "amazon_ads" in data
    assert "rakuten_sales" in data
```

- [ ] **Step 2: テスト失敗を確認**

```bash
python -m pytest tests/test_marketplace_daily_report.py::test_main_outputs_valid_json -v
```

Expected: FAIL

- [ ] **Step 3: `main()` をファイル末尾に追加**

```python
def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--date", default=None)
    args = p.parse_args(argv)

    today = datetime.now(JST).date()
    report_date = args.date or (today - timedelta(days=1)).strftime("%Y-%m-%d")

    result = {
        "date":          report_date,
        "amazon_sales":  fetch_amazon_sales(report_date),
        "amazon_ads":    fetch_amazon_ads(report_date),
        "rakuten_sales": fetch_rakuten_sales(report_date),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: テスト通過を確認**

```bash
python -m pytest tests/test_marketplace_daily_report.py -v
```

Expected: 全テスト PASSED

- [ ] **Step 5: コミット**

```bash
git add tools/marketplace_daily_report.py tests/test_marketplace_daily_report.py
git commit -m "feat: main()とJSON出力を実装"
```

---

## Task 6: `/デイリーレポート` コマンドファイルを作成

**Files:**
- Create: `.claude/commands/デイリーレポート.md`

テストは不要（Claudeの動作定義ファイル）。

- [ ] **Step 1: コマンドファイルを作成**

`.claude/commands/デイリーレポート.md` を作成:

````markdown
마켓플레이스 데일리 리포트를 생성합니다.

## 처리 순서

1. `python tools/marketplace_daily_report.py` 를 실행하여 JSON 데이터를 취득
2. 사용자 입력에서 아래 항목을 파싱:
   - 라쿠텐 광고: ROAS, 소진액
   - 재고 이상 여부
   - 계정 이슈 여부
   - 클레임・특이사항
   - 오늘 할 일 ① ② ③
3. 데이터를 통합하여 아래 형식으로 한국어 리포트를 출력

## 입력 형식

사용자는 아래 항목을 자유롭게 일본어 또는 한국어로 입력합니다:

```
デイリーレポート
楽天広告: ROAS 3.2, 消化 ¥12,000
在庫: なし
アカウント: なし
クレーム: なし
今日: ①〇〇 ②〇〇 ③〇〇
```

항목이 없으면 「없음」으로 처리합니다.

## 출력 형식

```
━━━━━━━━━━━━━━━━━━━━━━━━
📊 마켓플레이스 데일리 리포트｜YYYY-MM-DD
━━━━━━━━━━━━━━━━━━━━━━━━

【매출・주문 (전일)】
　라쿠텐　　¥X,XXX,XXX / X건
　Amazon　$XXX.XX / X건
　합계　　약 ¥X,XXX,XXX（$1=¥XXX 환산）

【광고 효율】
　라쿠텐　ROAS X.X / 소진 ¥XX,XXX
　Amazon　ROAS X.X / 소진 $XXX / CPC $X.XX

【재고】〇〇

【계정】〇〇

【클레임・특이사항】〇〇

【오늘 할 일】
　① 〇〇
　② 〇〇
　③ 〇〇
━━━━━━━━━━━━━━━━━━━━━━━━
```

## 주의사항

- USD→JPY 환산: 당일 환율이 불명확한 경우 ¥150 고정으로 표시하고 "(고정환율)"을 부기
- 라쿠텐 데이터 취득 실패 시: 해당 항목에 「데이터 취득 실패」라고 표시하고 나머지 항목은 계속 출력
- Amazon DataKeeper 파일 없는 경우: 「DataKeeper 미갱신」으로 표시

---

사용자 입력:
$ARGUMENTS
````

- [ ] **Step 2: コマンドが認識されるか動作確認**

Claude Codeで `/デイリーレポート` と入力してコマンドが表示されることを確認。

- [ ] **Step 3: コミット**

```bash
git add .claude/commands/デイリーレポート.md
git commit -m "feat: /デイリーレポート スラッシュコマンドを追加"
```

---

## Task 7: ワークフローSOPを作成

**Files:**
- Create: `workflows/marketplace_daily_report.md`

- [ ] **Step 1: ワークフローファイルを作成**

`workflows/marketplace_daily_report.md` を作成:

```markdown
# マーケットプレイス デイリーレポート ワークフロー

## 目的

毎朝、楽天・Amazonの前日パフォーマンスを集計し、韓国語でレポートをチャット出力する。

## トリガー

ユーザーが `/デイリーレポート` または「デイリーレポート」と入力する。

## 必要な入力（ユーザー提供）

| 項目 | 例 | 必須 |
|------|-----|------|
| 楽天広告 | `楽天広告: ROAS 3.2, 消化 ¥12,000` | No |
| 在庫 | `在庫: SKU-001残り5個` or `なし` | No |
| アカウント | `アカウント: なし` | No |
| クレーム | `クレーム: 1件（返金対応中）` | No |
| 今日やること | `今日: ①広告調整 ②新商品登録 ③レビュー確認` | Yes |

## 使用ツール

1. `tools/marketplace_daily_report.py` — 楽天・Amazon データ取得

## 実行手順

1. `python tools/marketplace_daily_report.py` を実行（前日データがデフォルト）
2. ユーザー入力をパース
3. JSON + ユーザー入力を統合してレポートを出力

## エラー対処

| エラー | 対応 |
|--------|------|
| RMS API失敗 | 「라쿠텐 데이터 취득 실패」と表示し継続 |
| DataKeeper未更新 | 「DataKeeper 미갱신」と表示し継続 |
| 楽天広告未入力 | セクションを「미입력」と表示 |
```

- [ ] **Step 2: コミット**

```bash
git add workflows/marketplace_daily_report.md
git commit -m "docs: マーケットプレイス デイリーレポート ワークフローを追加"
```

---

## Task 8: エンドツーエンド動作確認

- [ ] **Step 1: ツールを手動実行して出力を確認**

```bash
cd c:/Users/Puser/Desktop/kazuki
python tools/marketplace_daily_report.py --date 2026-04-13
```

Expected: JSONが出力される（DataKeeperがない場合はerrorキーあり、楽天はRMS接続次第）

- [ ] **Step 2: スラッシュコマンドをテスト**

Claude Codeで以下を入力:

```
/デイリーレポート
楽天広告: ROAS 3.2, 消化 ¥12,000
在庫: なし
アカウント: なし
クレーム: なし
今日: ①広告入札確認 ②新商品タイトル修正 ③レビュー返信
```

Expected: 韓国語レポートがチャットに出力される

- [ ] **Step 3: 全テスト通過を確認**

```bash
python -m pytest tests/test_marketplace_daily_report.py -v
```

Expected: 全テスト PASSED
