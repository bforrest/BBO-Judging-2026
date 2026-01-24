import csv

# File paths
JUDGE_WORKSHEET = 'JUDGE WORKSHEET 2026.csv'
GENERATED = 'Judges_and_Tables_generated.csv'
OUTPUT = 'judging_site_contacts.csv'

# Load judge contact info from worksheet
judge_contacts = {}
with open(JUDGE_WORKSHEET, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        full_name = f"{row['First Name'].strip()} {row['Last Name'].strip()}"
        judge_contacts[full_name.lower()] = {
            'Full Name': full_name,
            'Email': row['Email Address'].strip(),
            'Phone': row['Phone Number'].strip()
        }

# Prepare output rows
output_rows = []
with open(GENERATED, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row['FULL NAME'].strip()
        # Extract site from 'DESIRED TABLE TO JUDGE' (e.g., '02/06 Arlington T68 American Pale Ale')
        site_field = row['DESIRED TABLE TO JUDGE']
        if not site_field:
            continue
        site = None
        for s in ['Arlington', 'Dallas', 'Grapevine', 'Keller', 'Stubbies']:
            if s.lower() in site_field.lower():
                site = s
                break
        if not site:
            continue
        contact = judge_contacts.get(name.lower())
        if contact:
            output_rows.append({
                'Site': site,
                'Table': site_field,
                'Full Name': contact['Full Name'],
                'Email': contact['Email'],
                'Phone': contact['Phone']
            })
        else:
            # If not found, still include with blanks
            output_rows.append({
                'Site': site,
                'Table': site_field,
                'Full Name': name,
                'Email': '',
                'Phone': ''
            })

# Write output CSV

with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['Site', 'Table', 'Full Name', 'Email', 'Phone'])
    writer.writeheader()
    writer.writerows(output_rows)

print(f"Contact list written to {OUTPUT}")
