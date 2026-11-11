"""Create recommendations for Store Manager review (FR-04, NFR-06, NFR-07).

A recommendation is created only for flagged items. It starts as "pending review";
the review step later changes the status and fills in modified_quantity / review_reason.
supplier_cost is never copied into a recommendation (NFR-08).
"""
import uuid

STATUS_PENDING = "pending review"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_MODIFIED = "modified"

TYPE_REORDER = "reorder"
TYPE_MANAGER_REVIEW = "manager review"


def create_recommendation(item, metrics, justification=None, justification_source=None):
    """Build a recommendation, or return None if the item is not flagged.

    item must include (added by csv_handler):
      item_name, current_stock, source_filename, row_number, upload_id, upload_date
    item may include:
      profit_margin (optional), missing_fields (list of optional fields that were blank)
    metrics: the dict returned by calculate_inventory_metrics().
    justification / justification_source: the text and "AI" or "TEMPLATE".
      Leave as None for now (the AI step is added later) and for manager-review items,
      which skip the AI and the template.
    """
    if not metrics["low_stock"]:
        return None

    if metrics["needs_manager_review"]:
        recommendation_type = TYPE_MANAGER_REVIEW
        quantity = None  # the Store Manager decides
    else:
        recommendation_type = TYPE_REORDER
        quantity = metrics["reorder_quantity"]

    return {
        "id": uuid.uuid4().hex[:8],
        "item_name": item["item_name"],
        "current_stock": item["current_stock"],
        "average_daily_sales": metrics["average_daily_sales"],
        "days_left": metrics["days_left"],
        "profit_margin": item.get("profit_margin"),  # display only
        "recommendation_type": recommendation_type,
        "original_quantity": quantity,   # never changes
        "modified_quantity": None,       # set only if the manager modifies
        "justification": justification,
        "justification_source": justification_source,
        "missing_fields": list(item.get("missing_fields", [])),
        "status": STATUS_PENDING,
        "review_reason": None,
        "source_filename": item["source_filename"],
        "source_row": item["row_number"],
        "upload_id": item["upload_id"],
        "upload_date": item["upload_date"],
    }