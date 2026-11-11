"""Tests for recommendation creation (FR-04, NFR-06, NFR-07, NFR-08)."""
from recommendation import (
    STATUS_PENDING, TYPE_MANAGER_REVIEW, TYPE_REORDER, create_recommendation,
)
from rules_engine import calculate_inventory_metrics


def make_item(stock, units, **extra):
    item = {
        "item_name": "AA Batteries",
        "current_stock": stock,
        "units_sold_30d": units,
        "source_filename": "inventory.csv",
        "row_number": 4,
        "upload_id": "u1",
        "upload_date": "2026-11-10",
    }
    item.update(extra)
    return item


def build(stock, units, **extra):
    item = make_item(stock, units, **extra)
    return create_recommendation(item, calculate_inventory_metrics(item), "text", "TEMPLATE")


def test_not_flagged_returns_none():
    assert build(10, 6) is None  # slow seller


def test_flagged_item_becomes_reorder_recommendation():
    r = build(10, 90)
    assert r["recommendation_type"] == TYPE_REORDER
    assert r["original_quantity"] == 32
    assert r["modified_quantity"] is None
    assert r["status"] == STATUS_PENDING
    assert r["justification"] == "text"
    assert r["justification_source"] == "TEMPLATE"


def test_zero_stock_zero_sales_is_manager_review_with_no_quantity():
    r = build(0, 0)
    assert r["recommendation_type"] == TYPE_MANAGER_REVIEW
    assert r["original_quantity"] is None
    assert r["status"] == STATUS_PENDING


def test_justification_is_optional_until_the_ai_step_exists():
    item = make_item(10, 90)
    r = create_recommendation(item, calculate_inventory_metrics(item))
    assert r["justification"] is None
    assert r["justification_source"] is None


def test_source_traceability_fields():
    r = build(10, 90)
    assert r["source_filename"] == "inventory.csv"
    assert r["source_row"] == 4
    assert r["upload_id"] == "u1"
    assert r["upload_date"] == "2026-11-10"


def test_missing_profit_is_noted():
    r = build(10, 90, missing_fields=["profit_margin"])
    assert r["profit_margin"] is None
    assert r["missing_fields"] == ["profit_margin"]


def test_profit_is_shown_when_present():
    assert build(10, 90, profit_margin=22.5)["profit_margin"] == 22.5


def test_supplier_cost_never_copied():
    r = build(10, 90, supplier_cost=9.99)
    assert "supplier_cost" not in r


def test_each_recommendation_gets_its_own_id():
    assert build(10, 90)["id"] != build(10, 90)["id"]