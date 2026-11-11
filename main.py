from csv_handler import load_inventory
from rules_engine import calculate_inventory_metrics
from recommendation import create_recommendation
from justification import justify_many
from llm_client import load_llm

# AI plug-in: uses OpenAI if OPENAI_API_KEY is set (in .env), otherwise the template only.
llm, ai_note = load_llm()
print(ai_note)
fallback_reasons = []

# Load inventory CSV
filename = "data/synthetic_inventory_100.csv"

try:
    inventory = load_inventory(filename)
except FileNotFoundError:
    print(f"Error: the file '{filename}' was not found.")
    raise SystemExit(1)
except ValueError as error:
    print(f"Error: no usable data found. {error}")
    raise SystemExit(1)

if not inventory:
    print("Error: no usable data found. The file has no inventory rows.")
    raise SystemExit(1)

print("Inventory loaded successfully!")
print("Total items:", len(inventory))

# Process inventory through the Rules Engine
results = []
invalid_items = []
recommendations = []
flagged = []  # (item, metrics) pairs that need a recommendation

for item in inventory:

    # Skip records with insufficient required data
    if not item["sufficient_data"]:
        invalid_items.append(item)
        continue

    # Calculate inventory metrics
    metrics = calculate_inventory_metrics(item)

    # Combine original inventory information with calculated metrics
    result = {**item, **metrics}
    results.append(result)

    if metrics["low_stock"]:
        flagged.append((item, metrics))

# Justify all flagged items at once (AI calls run in parallel inside the 15-second limit).
# Manager-review items get no justification.
justifications = justify_many(
    flagged, llm, log=lambda name, why: fallback_reasons.append((name, why))
)

# Create a recommendation for every flagged item
for (item, metrics), (justification, source) in zip(flagged, justifications):
    recommendations.append(create_recommendation(item, metrics, justification, source))


# Display items that could not be processed (insufficient data)
if invalid_items:
    print("\n--- INSUFFICIENT DATA ---")

    for item in invalid_items:
        name = item["item_name"] or "(no item name)"
        print(
            f"Row {item['row_number']} ({item['source_filename']}): "
            f"A reliable recommendation cannot be calculated for {name}. "
            + " ".join(item["data_issues"])
        )


# Display flagged inventory items
print("\n--- LOW-STOCK DETECTION RESULTS ---")

for item in results:
    if item["low_stock"]:
        if item["needs_manager_review"]:
            print(f"\n{item['item_name']} - MANAGER REVIEW REQUIRED")
        else:
            print(f"\n{item['item_name']} - LOW STOCK")
            print("Current stock:", item["current_stock"])
            print("Average daily sales:", item["average_daily_sales"])
            print("Days remaining:", item["days_left"])
            print("Recommended reorder:", item["reorder_quantity"])


# Display inventory summary
low_stock_count = sum(
    1 for item in results
    if item["low_stock"] and not item["needs_manager_review"]
)

manager_review_count = sum(
    1 for item in results
    if item["needs_manager_review"]
)

print("\n--- INVENTORY SUMMARY ---")
print("Total items:", len(inventory))
print("Successfully processed:", len(results))
print("Invalid items:", len(invalid_items))
print("Low-stock items:", low_stock_count)
print("Manager review required:", manager_review_count)


# Display recommendation summary
print("\n--- RECOMMENDATION SUMMARY ---")
print("Total recommendations:", len(recommendations))

for recommendation in recommendations:
    print(
        recommendation["item_name"],
        "| Type:", recommendation["recommendation_type"],
        "| Quantity:", recommendation["original_quantity"],
        "| Status:", recommendation["status"]
    )
    if recommendation["justification"]:
        print("   ", recommendation["justification_source"] + ":", recommendation["justification"])
sources = [r["justification_source"] for r in recommendations if r["justification_source"]]
print("\nJustification sources: AI =", sources.count("AI"), "| TEMPLATE =", sources.count("TEMPLATE"))
for name, why in fallback_reasons:
    print(f"   AI fallback for {name}: {why}")