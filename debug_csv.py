#!/usr/bin/env python3
import csv

input_file = "Bluebonnet_Brew-Off_For_2026_Available_Judge_Emails_2026-01-23.csv"

with open(input_file, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    print("Fieldnames from DictReader:")
    for i, fn in enumerate(reader.fieldnames):
        print(f"  {i}: '{fn}'")
    
    print("\n--- First 3 rows ---")
    for row_num, row in enumerate(reader):
        if row_num >= 3:
            break
        print(f"\nRow {row_num}:")
        print(f"  First Name: '{row.get('First Name')}'")
        print(f"  Last Name: '{row.get('Last Name')}'")
        avail = row.get('Availability', '')
        print(f"  Availability (first 80 chars): '{avail[:80]}'...")
        print(f"  Entries: '{row.get('Entries')}'")
