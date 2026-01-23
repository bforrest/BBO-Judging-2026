import csv

csv_path = "Bluebonnet_Brew-Off_For_2026_Available_Judge_Emails_2026-01-23.csv"
column_name = "Availability"   # change to your real column header

all_items = []

with open(csv_path, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cell = row[column_name] or ""
        parts = [p.strip() for p in cell.split("|") if p.strip()]
        all_items.extend(parts)

# remove duplicates, sort alphabetically
unique_sorted = sorted(set(all_items))

print("Unique Availability Sites:")
for item in unique_sorted:
    print(item)
