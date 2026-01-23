import csv
from collections import defaultdict

csv_path = "Bluebonnet_Brew-Off_For_2026_Available_Judge_Emails_2026-01-23.csv"

# site -> set of judge names
site_judges = defaultdict(set)

with open(csv_path, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    # Debug: check what DictReader sees
    # print("Fieldnames:", reader.fieldnames)
    
        # Clean up header names: strip BOM/whitespace and surrounding quotes
    cleaned = []
    for h in reader.fieldnames:
        h2 = h.strip().strip('"')          # remove spaces then double quotes
        h2 = h2.replace('\ufeff', '')      # remove BOM if still present
        cleaned.append(h2)
    reader.fieldnames = cleaned
    
    for row in reader:
        # Rebuild row with cleaned keys
        row = {k.strip().strip('"'): (v.strip() if isinstance(v, str) else v)
           for k, v in row.items()}

        first = row["First Name"].strip()
        last = row["Last Name"].strip()
        rank = row.get("BJCP Rank", "Unknown").strip()
        judge_name = f"{first} {last} ({rank})"

        availability = (row.get("Availability") or "").strip()

        if not availability:
            continue

        # Split pipe-delimited slots for this judge
        slots = [s.strip() for s in availability.split("|") if s.strip()]

        for slot in slots:
            # slot example: "02/06 Arlington T68 American Pale Ale"
            # or "02/07 AM Dallas T55 Kolsch and Blonde"
            site_judges[slot].add(judge_name)
            
# Convert sets to sorted lists if desired
site_judges = {site: sorted(judges) for site, judges in site_judges.items()}

for site, judges in site_judges.items():
    print(site, "->", judges)
