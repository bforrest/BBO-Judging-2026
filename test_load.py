import csv

with open("Judges and Tables.tsv", 'r', encoding='utf-8') as f:
    # Skip first blank line
    next(f)
    reader = csv.DictReader(f, delimiter='\t')
    print("Headers:", reader.fieldnames[:6])
    count = 0
    for row in reader:
        if row.get('FULL NAME'):
            count += 1
            if count <= 3:
                print(f"Row {count}:")
                print(f"  Name: {row.get('FULL NAME')}")
                print(f"  Table: {row.get('DESIRED TABLE TO JUDGE')}")
    print(f"\nTotal judges: {count}")
