"""Tests for the Rules Engine (T-02 rule calculations, T-07 zero sales)."""
from rules_engine import calculate_inventory_metrics


def run(stock, units):
    return calculate_inventory_metrics({"current_stock": stock, "units_sold_30d": units})


# ---- T-02: calculations, flags, reorder quantities ----

def test_fast_seller_is_flagged():
    r = run(10, 90)
    assert r["days_left"] == 3.33
    assert r["low_stock"] is True
    assert r["reorder_quantity"] == 32


def test_slow_seller_same_stock_is_not_flagged():
    r = run(10, 6)
    assert r["days_left"] == 50.0
    assert r["low_stock"] is False
    assert r["reorder_quantity"] is None


def test_reorder_rounds_up():
    # 10 in stock, 50 sold: 6 days left, 50/30*14 - 10 = 13.33 -> 14
    r = run(10, 50)
    assert r["days_left"] == 6.0
    assert r["low_stock"] is True
    assert r["reorder_quantity"] == 14


def test_exactly_seven_days_is_flagged():
    r = run(7, 30)
    assert r["days_left"] == 7.0
    assert r["low_stock"] is True


def test_eight_days_is_not_flagged():
    r = run(8, 30)
    assert r["days_left"] == 8.0
    assert r["low_stock"] is False


# ---- T-07: zero sales ----

def test_zero_sales_with_stock_is_not_flagged():
    r = run(20, 0)
    assert r["days_left"] is None
    assert r["low_stock"] is False
    assert r["needs_manager_review"] is False
    assert r["reorder_quantity"] is None


def test_zero_sales_and_zero_stock_goes_to_manager_review():
    r = run(0, 0)
    assert r["low_stock"] is True
    assert r["needs_manager_review"] is True
    assert r["reorder_quantity"] is None  # manager decides the quantity


# ---- Privacy: only calculated facts come back (NFR-08, minimal AI data) ----

def test_output_has_only_calculated_fields():
    item = {
        "item_name": "AA Batteries",
        "current_stock": 10,
        "units_sold_30d": 90,
        "profit_margin": 20.0,
        "supplier_cost": 9.99,
    }
    r = calculate_inventory_metrics(item)
    assert set(r) == {
        "average_daily_sales", "days_left", "low_stock",
        "needs_manager_review", "reorder_quantity",
    }