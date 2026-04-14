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
    pass  # Task 3で実装


def test_fetch_amazon_sales_empty_date():
    from marketplace_daily_report import fetch_amazon_sales
    result = fetch_amazon_sales("2099-01-01", data_file=FIXTURES / "amazon_sales_sample.json")
    assert result["total_orders"] == 0
    assert result["total_units"] == 0
    assert result["total_gross"] == 0.0
    assert result["total_net"] == 0.0
    assert result["brands"] == {}
