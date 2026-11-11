"""Generate a fictional inventory CSV for testing. Run: python generate_data.py
Change N below to make the file bigger or smaller (max 100)."""
import csv
import math
import os
import random

N = 100  # number of items

random.seed(42)  # same file every run

PRODUCTS = [
    "Bottled Water", "Wireless Mouse", "Desk Lamp", "USB Cable", "AA Batteries",
    "Notebook", "Winter Scarf", "Cereal", "Coffee", "Phone Charger",
    "Headphones", "Paper Towels", "Toothpaste", "Shampoo", "Laundry Detergent",
    "Dish Soap", "Soda", "Protein Bars", "Granola", "Rice",
    "Pasta", "Olive Oil", "Cooking Spray", "Paper Plates", "Plastic Cups",
    "Light Bulbs", "Extension Cord", "Keyboard", "Computer Monitor", "Mouse Pad",
    "Backpack", "Water Bottle", "Socks", "T-Shirt", "Jeans",
    "Baseball Cap", "Sunglasses", "Phone Case", "HDMI Cable", "Power Bank",
    "Flashlight", "Batteries Pack", "Hand Soap", "Conditioner", "Body Wash",
    "Facial Cleanser", "Pet Food", "Dog Treats", "Cat Litter", "Cleaning Wipes",
    "Dishwasher Tablets", "Trash Bags", "Aluminum Foil", "Plastic Wrap", "Sponges",
    "Broom", "Mop", "Laundry Basket", "Storage Bin", "Food Container Set",
    "Travel Mug", "Water Filter", "Electric Kettle", "Toaster", "Blender",
    "Wireless Earbuds", "Bluetooth Speaker", "Webcam", "Laptop Stand", "Ethernet Cable",
    "Screen Protector", "Phone Stand", "Gaming Mouse", "Gaming Keyboard", "Desk Organizer",
    "Printer Paper", "Pens", "Pencils", "Highlighters", "Sticky Notes",
    "Folder Set", "Stapler", "Scissors", "Tape Dispenser", "Calculator",
    "First Aid Kit", "Hand Sanitizer", "Face Masks", "Sunscreen", "Insect Repellent",
    "Pet Shampoo", "Cat Toys", "Dog Leash", "Pet Food Bowl", "Yoga Mat",
    "Resistance Bands", "Jump Rope", "Tennis Balls", "Soccer Ball", "Reusable Bags",
]

# where each scenario ends (as a count): 25% low, 45% enough, 15% lots, 10% no sales, 5% nothing
low_end = int(N * 0.25)
enough_end = int(N * 0.70)
lots_end = int(N * 0.85)
nosales_end = int(N * 0.95)

rows = []
for i, name in enumerate(PRODUCTS[:N]):
    units = random.randint(20, 400)  # units sold in 30 days
    daily = units / 30

    if i < low_end:                   # low stock: 7 days or less left
        stock = max(1, int(daily * random.uniform(0.5, 6.9)))
    elif i < enough_end:              # enough stock: 8-25 days left
        stock = math.ceil(daily * random.uniform(8, 25))
    elif i < lots_end:                # lots of stock: 26-60 days left
        stock = math.ceil(daily * random.uniform(26, 60))
    elif i < nosales_end:             # no sales, still has stock
        units, stock = 0, random.randint(5, 80)
    else:                             # no sales and no stock
        units, stock = 0, 0

    profit = "" if random.random() < 0.10 else round(random.uniform(5, 45), 2)
    rows.append([name, stock, units, profit, round(random.uniform(1.5, 150), 2)])

random.shuffle(rows)  # mix the scenarios

os.makedirs("data", exist_ok=True)  # create the data/ folder if it doesn't exist
filename = f"data/synthetic_inventory_{N}.csv"
with open(filename, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["item_name", "current_stock", "units_sold_30d", "profit_margin", "supplier_cost"])
    writer.writerows(rows)

print("Wrote", filename, "with", len(rows), "items")