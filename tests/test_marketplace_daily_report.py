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
