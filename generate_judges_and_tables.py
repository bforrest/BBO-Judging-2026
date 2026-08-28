#!/usr/bin/env python3
"""
Generate Judges and Tables from Bluebonnet CSV

Converts the Bluebonnet_Brew-Off email signup sheet into the "Judges and Tables" format.
Creates a CSV file where each row is one judge assignment to a specific table.

Input: Bluebonnet_Brew-Off_For_2026_Available_Judge_Emails_2026-01-23.csv
Output: Judges_and_Tables_generated.csv
"""

import csv
import os

FIELDNAMES = ['FULL NAME', 'DESIRED TABLE TO JUDGE', 'PAIRING', 'BJCP ID', 'RANKING', 'SUBSTYLES ENTERED']


def clean_headers(fieldnames):
    """Clean up CSV headers by removing BOM, quotes, and whitespace."""
    cleaned = []
    for h in fieldnames:
        h = h.strip().strip('"').replace('﻿', '')
        cleaned.append(h)
    return cleaned


def parse_availability(availability_str):
    """Parse pipe-delimited availability string into list of table assignments."""
    if not availability_str:
        return []
    slots = [s.strip() for s in availability_str.split("|") if s.strip()]
    return slots


def normalize_rank(rank_str):
    """Normalize BJCP rank to standard format."""
    if not rank_str:
        return ""
    rank = rank_str.strip()
    if rank.lower() == "certified":
        return "Level 3: Certified"
    elif rank.lower() == "national":
        return "Level 4: National"
    return rank


def load_existing_pairings(path):
    """Load existing pairing values keyed by (name, table)."""
    pairings = {}
    if not os.path.exists(path):
        return pairings
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = (row.get('FULL NAME') or '').strip()
                table = (row.get('DESIRED TABLE TO JUDGE') or '').strip()
                pairing = (row.get('PAIRING') or '').strip()
                if name and table and pairing:
                    pairings[(name, table)] = pairing
    except Exception:
        pass
    return pairings


def main():
    """Main function to generate Judges and Tables CSV."""
    input_file = "Bluebonnet_Brew-Off_For_2026_Available_Judge_Emails_2026-01-23.csv"
    output_file = "Judges_and_Tables_generated.csv"

    print(f"Reading from: {input_file}")
    print(f"Writing to: {output_file}")
    print()

    # Preserve any pairings already recorded in the output file so a
    # regeneration doesn't clobber manual pairing edits.
    existing_pairings = load_existing_pairings(output_file)

    judges_data = []

    try:
        with open(input_file, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            reader.fieldnames = clean_headers(reader.fieldnames)

            for row in reader:
                first = row.get("First Name", "").strip()
                last = row.get("Last Name", "").strip()
                bjcp_id = row.get("BJCP ID", "").strip()
                rank = normalize_rank(row.get("BJCP Rank", "").strip())
                entries = row.get("Entries", "").strip()
                availability = row.get("Availability", "").strip()

                if not first or not last:
                    continue

                full_name = f"{first} {last}"
                slots = parse_availability(availability)

                if not slots:
                    continue

                for slot in slots:
                    pairing_value = existing_pairings.get((full_name, slot), '')
                    judges_data.append({
                        'FULL NAME': full_name,
                        'DESIRED TABLE TO JUDGE': slot,
                        'PAIRING': pairing_value,
                        'BJCP ID': bjcp_id,
                        'RANKING': rank,
                        'SUBSTYLES ENTERED': entries
                    })

    except FileNotFoundError:
        print(f"Error: {input_file} not found")
        return False

    if not judges_data:
        print("Warning: No judge data extracted")
        return False

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(judges_data)

        print(f"✅ Successfully created {output_file}")
        print(f"   Total assignments: {len(judges_data)}")
        print(f"   Unique judges: {len(set(j['FULL NAME'] for j in judges_data))}")
        print()
        print("Preview of first 5 rows:")
        for i, row in enumerate(judges_data[:5], 1):
            print(f"  {i}. {row['FULL NAME']} → {row['DESIRED TABLE TO JUDGE']} ({row['RANKING']})")

        if len(judges_data) > 5:
            print(f"  ... and {len(judges_data) - 5} more assignments")

        return True

    except Exception as e:
        print(f"Error writing output file: {e}")
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
