"""Tests for CSV intake (T-03 data quality, T-08 invalid data, NFR-07 traceability)."""
import pytest

from csv_handler import load_inventory

HEADER = "item_name,current_stock,units_sold_30d,profit_margin,supplier_cost\n"


def write(tmp_path, text, encoding="utf-8", name="inventory.csv"):
    path = tmp_path / name
    path.write_text(text, encoding=encoding, newline="")
    return str(path)


# ---- Normal path ----

def test_valid_row_is_loaded_and_converted(tmp_path):
    items = load_inventory(write(tmp_path, HEADER + "Pens,10,90,25.5,3.2\n"))
    item = items[0]
    assert item["item_name"] == "Pens"
    assert item["current_stock"] == 10
    assert item["units_sold_30d"] == 90
    assert item["profit_margin"] == 25.5
    assert item["supplier_cost"] == 3.2
    assert item["sufficient_data"] is True
    assert item["data_issues"] == []
    assert item["missing_fields"] == []


def test_source_filename_and_row_number(tmp_path):
    items = load_inventory(write(tmp_path, HEADER + "Pens,10,90,,\nCups,5,20,,\n"))
    assert items[0]["source_filename"] == "inventory.csv"
    assert [i["row_number"] for i in items] == [2, 3]


def test_row_numbers_stay_correct_with_blank_lines(tmp_path):
    items = load_inventory(write(tmp_path, HEADER + "Cups,3,9,,\n\nPens,5,10,,\n"))
    assert [(i["item_name"], i["row_number"]) for i in items] == [("Cups", 2), ("Pens", 4)]


# ---- Optional data missing: still usable, but noted (FR-07, NFR-03) ----

def test_blank_profit_is_noted_but_row_is_usable(tmp_path):
    item = load_inventory(write(tmp_path, HEADER + "Pens,10,90,,3.2\n"))[0]
    assert item["sufficient_data"] is True
    assert item["profit_margin"] is None
    assert item["missing_fields"] == ["profit_margin"]


def test_profit_column_absent_is_noted(tmp_path):
    text = "item_name,current_stock,units_sold_30d\nPens,10,90\n"
    item = load_inventory(write(tmp_path, text))[0]
    assert item["sufficient_data"] is True
    assert item["missing_fields"] == ["profit_margin"]


def test_invalid_profit_does_not_block_the_row(tmp_path):
    item = load_inventory(write(tmp_path, HEADER + "Pens,10,90,abc,3.2\n"))[0]
    assert item["sufficient_data"] is True
    assert "Invalid profit margin." in item["data_issues"]
    assert item["missing_fields"] == ["profit_margin"]


def test_invalid_supplier_cost_does_not_block_the_row(tmp_path):
    item = load_inventory(write(tmp_path, HEADER + "Pens,10,90,20,xyz\n"))[0]
    assert item["sufficient_data"] is True
    assert "Invalid supplier cost." in item["data_issues"]


# ---- Required data missing or invalid: insufficient data (T-03, T-08) ----

@pytest.mark.parametrize("row, issue", [
    (",10,90,,", "Missing item name."),
    ("Pens,-3,90,,", "Current stock cannot be negative."),
    ("Pens,10,-5,,", "Units sold cannot be negative."),
    ("Pens,abc,90,,", "Invalid current stock."),
    ("Pens,10,abc,,", "Invalid units sold."),
    ("Pens,,90,,", "Invalid current stock."),
    ("Pens,10,,,", "Invalid units sold."),
])
def test_bad_required_data_is_insufficient(tmp_path, row, issue):
    item = load_inventory(write(tmp_path, HEADER + row + "\n"))[0]
    assert item["sufficient_data"] is False
    assert issue in item["data_issues"]


# ---- Robustness ----

def test_row_shorter_than_header_does_not_crash(tmp_path):
    item = load_inventory(write(tmp_path, HEADER + "Pens,5,10\n"))[0]
    assert item["sufficient_data"] is True
    assert item["missing_fields"] == ["profit_margin"]


def test_excel_csv_with_hidden_marker_is_accepted(tmp_path):
    text = "item_name,current_stock,units_sold_30d\nPens,5,10\n"
    items = load_inventory(write(tmp_path, text, encoding="utf-8-sig"))
    assert items[0]["item_name"] == "Pens"


def test_missing_required_column_raises(tmp_path):
    with pytest.raises(ValueError, match="Missing required columns"):
        load_inventory(write(tmp_path, "item_name,current_stock\nPens,5\n"))


def test_empty_file_raises(tmp_path):
    with pytest.raises(ValueError):
        load_inventory(write(tmp_path, ""))


# ---- Upload info that recommendations need (NFR-07, stale-data warning) ----

def test_every_row_in_an_upload_shares_one_upload_id_and_date(tmp_path):
    items = load_inventory(write(tmp_path, HEADER + "Pens,10,90,,\nCups,5,20,,\n"))
    assert items[0]["upload_id"] == items[1]["upload_id"]
    assert items[0]["upload_date"] == items[1]["upload_date"]
    assert len(items[0]["upload_date"]) == 10  # YYYY-MM-DD


def test_each_upload_gets_a_new_upload_id(tmp_path):
    path = write(tmp_path, HEADER + "Pens,10,90,,\n")
    assert load_inventory(path)[0]["upload_id"] != load_inventory(path)[0]["upload_id"]