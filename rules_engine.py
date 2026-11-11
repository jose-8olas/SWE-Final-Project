"""Rules Engine: deterministic low-stock and reorder calculations (FR-03, FR-08).

Only these rules decide the low-stock flag and the reorder quantity. The AI never does.
Input must already be validated and numeric: intake.py is responsible for rejecting
missing, negative, or non-numeric values (the insufficient-data path).
"""
import math

LOW_STOCK_DAYS = 7       # flag when days of stock left <= 7
TARGET_COVER_DAYS = 14   # reorder enough to cover about 14 days
DAYS_IN_PERIOD = 30      # sales are reported for the last 30 days


def calculate_inventory_metrics(item):
    """Return the calculated facts for one item (and nothing else).

    item needs: current_stock, units_sold_30d (numbers).

    Returns a dict with:
      average_daily_sales   units sold per day (rounded for display)
      days_left             days of stock left, or None if there are no sales
      low_stock             True if flagged (including the review-only case)
      needs_manager_review  True only when stock and sales are both zero
      reorder_quantity      whole units, or None if not flagged / no quantity to suggest
    """
    stock = item["current_stock"]
    units = item["units_sold_30d"]

    avg_daily = units / DAYS_IN_PERIOD
    needs_review = units == 0 and stock == 0

    if avg_daily > 0:
        days_left = stock / avg_daily
        low_stock = days_left <= LOW_STOCK_DAYS
    else:
        days_left = None          # no sales: stock lasts "forever"
        low_stock = needs_review  # zero stock and zero sales: flag for the manager

    # Quantity only for flagged items that have sales data (FR-08).
    # The zero-stock, zero-sales case is left for the Store Manager to decide.
    if low_stock and avg_daily > 0:
        reorder_quantity = math.ceil(max(0, avg_daily * TARGET_COVER_DAYS - stock))
    else:
        reorder_quantity = None

    # Decisions above use the exact values; rounding is for display only.
    return {
        "average_daily_sales": round(avg_daily, 2),
        "days_left": round(days_left, 2) if days_left is not None else None,
        "low_stock": low_stock,
        "needs_manager_review": needs_review,
        "reorder_quantity": reorder_quantity,
    }