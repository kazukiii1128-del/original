"""Tests for marketplace_daily_report.py"""
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

FIXTURES = Path(__file__).parent / "fixtures"


def test_fetch_amazon_sales_returns_totals():
    from marketplace_daily_report import fetch_amazon_sales
    result = fetch_amazon_sales("2026-04-13", data_file=FIXTURES / "amazon_sales_sample.json")
    assert result["total_orders"] == 3
    assert result["total_units"] == 4
    assert abs(result["total_gross"] - 230.00) < 0.01
    assert abs(result["total_net"] - 185.00) < 0.01
    assert "Grosmimi" in result["brands"]
    assert result["brands"]["Grosmimi"]["orders"] == 2


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


def test_fetch_amazon_sales_empty_date():
    from marketplace_daily_report import fetch_amazon_sales
    result = fetch_amazon_sales("2099-01-01", data_file=FIXTURES / "amazon_sales_sample.json")
    assert result["total_orders"] == 0
    assert result["total_units"] == 0
    assert result["total_gross"] == 0.0
    assert result["total_net"] == 0.0
    assert result["brands"] == {}


def test_fetch_rakuten_returns_totals():
    from marketplace_daily_report import fetch_rakuten_sales
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
        inst.list_orders.return_value = mock_orders
        result = fetch_rakuten_sales("2026-04-13")

    assert result["total_orders"] == 2
    assert result["total_units"] == 3
    assert abs(result["total_sales"] - 11000.0) < 0.01  # 3000*2 + 5000*1


def test_main_outputs_valid_json(tmp_path, capsys):
    import shutil
    from marketplace_daily_report import main
    sales_dst = tmp_path / "amazon_sales_daily.json"
    ads_dst   = tmp_path / "amazon_ads_daily.json"
    shutil.copy(FIXTURES / "amazon_sales_sample.json", sales_dst)
    shutil.copy(FIXTURES / "amazon_ads_sample.json",   ads_dst)

    with patch("marketplace_daily_report.DATAKEEPER", tmp_path), \
         patch("marketplace_daily_report.RakutenRMSClient") as MockClient:
        inst = MockClient.return_value
        inst.list_orders.return_value = []
        main(["--date", "2026-04-13"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["date"] == "2026-04-13"
    assert "amazon_sales" in data
    assert "amazon_ads" in data
    assert "rakuten_sales" in data
