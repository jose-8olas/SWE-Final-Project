import csv
import uuid
from datetime import date
from pathlib import Path

REQUIRED_COLUMNS = [
    "item_name",
    "current_stock",
    "units_sold_30d"
]


def load_inventory(filename):
    """Read, convert, and validate inventory records from a CSV file."""

    inventory = []

    upload_id = uuid.uuid4().hex[:8]        # identifies this upload
    upload_date = date.today().isoformat()  # shown so managers know how old the data is

    # utf-8-sig also accepts CSV files saved by Excel (which start with a hidden marker)
    with open(filename, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        # Check that required columns exist
        if not reader.fieldnames:
            raise ValueError("The CSV file is empty or missing headers.")

        missing_columns = [
            column for column in REQUIRED_COLUMNS
            if column not in reader.fieldnames
        ]

        if missing_columns:
            raise ValueError(
                f"Missing required columns: {missing_columns}"
            )

        # Process each inventory row
        for row in reader:

            # Line number in the file (stays correct even if the file has blank lines)
            row_number = reader.line_num

            required_issues = []   # problems that block the Rules Engine
            optional_issues = []   # problems with profit / supplier cost
            missing_fields = []    # optional fields that were blank or invalid

            # Get and validate item name
            item_name = (row.get("item_name") or "").strip()

            if not item_name:
                required_issues.append("Missing item name.")

            # Convert current stock to an integer
            try:
                current_stock = int(row["current_stock"])

                if current_stock < 0:
                    required_issues.append("Current stock cannot be negative.")

            except (ValueError, TypeError):
                current_stock = None
                required_issues.append("Invalid current stock.")

            # Convert units sold to an integer
            try:
                units_sold_30d = int(row["units_sold_30d"])

                if units_sold_30d < 0:
                    required_issues.append("Units sold cannot be negative.")

            except (ValueError, TypeError):
                units_sold_30d = None
                required_issues.append("Invalid units sold.")

            # Optional: profit margin (shown to the manager, never affects the flag)
            profit_margin = None
            profit_text = (row.get("profit_margin") or "").strip()

            if profit_text:
                try:
                    profit_margin = float(profit_text)
                except ValueError:
                    optional_issues.append("Invalid profit margin.")
                    missing_fields.append("profit_margin")
            else:
                missing_fields.append("profit_margin")

            # Optional: supplier cost (confidential, never sent to the AI)
            supplier_cost = None
            cost_text = (row.get("supplier_cost") or "").strip()

            if cost_text:
                try:
                    supplier_cost = float(cost_text)
                except ValueError:
                    optional_issues.append("Invalid supplier cost.")

            inventory_item = {
                "item_name": item_name,
                "current_stock": current_stock,
                "units_sold_30d": units_sold_30d,
                "profit_margin": profit_margin,
                "supplier_cost": supplier_cost,
                "row_number": row_number,
                "source_filename": Path(filename).name,
                "upload_id": upload_id,
                "upload_date": upload_date,
                "data_issues": required_issues + optional_issues,
                "missing_fields": missing_fields,
                # Required data decides whether the Rules Engine and AI can process it
                "sufficient_data": not required_issues
            }

            inventory.append(inventory_item)

    return inventory