"""Shared CSV loaders and slot parsing for BBO judging analysis scripts."""

import csv
import os
import re

SLOT_PATTERN = re.compile(r'^(\d{2}/\d{2})\s*(AM|PM)?\s*([A-Za-z]+)\s*(T\d+)\s*(.*)$')

RANKS = {
    'Level 0: Non-BJCP': 0,
    'Level 1: Rank Pending': 1,
    'Level 1: Provisional': 1,
    'Level 2: Recognized': 2,
    'Level 3: Certified': 3,
    'certified': 3,
    'CERTIFIED': 3,
    'Certified+ Mead': 3,
    'Certified+Mead': 3,
    'Certified+Mead+cider': 3,
    'Certified, Judge with Sensory Training': 3,
    'Certified, Professional Brewer': 3,
    'national': 4,
    'Level 4: National': 4,
}

DEFAULT_JUDGE_WORKSHEET_PATH = os.path.expanduser(
    "~/judge-data-private/JUDGE WORKSHEET 2026.csv"
)


def is_certified_or_higher(rank):
    """Check if a rank is Certified (Level 3) or higher."""
    return RANKS.get(rank, 0) >= 3


def parse_slot(desired_table_str):
    """Parse a 'DESIRED TABLE TO JUDGE' string into its components.

    Returns (date, session, site, table, description) or None if it
    doesn't match the expected format. `session` is 'AM', 'PM', or None.
    `table` keeps its 'T' prefix (e.g. 'T55') to match styles/entry-count keys.
    """
    match = SLOT_PATTERN.match(desired_table_str.strip())
    if not match:
        return None
    date, session, site, table, description = match.groups()
    return (date, session, site, table, description.strip())


def parse_substyles(substyles_str):
    """Parse a comma-separated 'SUBSTYLES ENTERED' string into a set of ids."""
    if not substyles_str:
        return set()
    return {s.strip() for s in substyles_str.split(',') if s.strip()}


def load_assignments(path):
    """Load Judges_and_Tables_generated.csv, with each row's slot parsed.

    Returns a list of dicts, each the original row plus a 'slot' key holding
    the parse_slot(...) tuple (or None if unparseable).
    """
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row = dict(row)
            row['slot'] = parse_slot(row.get('DESIRED TABLE TO JUDGE', ''))
            rows.append(row)
    return rows


def load_styles_by_table(path):
    """Load styles by table.csv.

    Returns (table_styles, table_names):
      table_styles: dict table ('T55') -> set of BJCP style ids
      table_names: dict table ('T55') -> Medal Category Name
    """
    table_styles = {}
    table_names = {}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            table = f"T{row['Table Number'].strip()}"
            table_styles.setdefault(table, set()).add(row['BJCP Style Id'].strip())
            table_names[table] = row['Medal Category Name'].strip()
    return table_styles, table_names


def load_entry_counts(path):
    """Load medal_category_counts.csv.

    Returns dict table ('T55') -> entry count (int).
    """
    counts = {}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            table = f"T{row['Table Number'].strip()}"
            try:
                counts[table] = int(row['Count'].strip())
            except (ValueError, KeyError):
                continue
    return counts


def load_judge_distances(path=DEFAULT_JUDGE_WORKSHEET_PATH):
    """Load per-judge, per-site distances from the private judge worksheet.

    Returns dict full_name -> dict site_name (e.g. 'Dallas') -> distance (float).
    Returns an empty dict if the file doesn't exist (fail open — callers
    should treat a judge missing from this dict as feasible everywhere).
    """
    distances = {}
    if not os.path.exists(path):
        return distances
    site_columns = {
        'Dallas': 'DALLAS SITE',
        'Grapevine': 'GRAPEVINE SITE',
        'Arlington': 'ARLINGTON SITE',
        'Stubbies': 'STUBBIES SITE',
        'Keller': 'KELLER SITE',
    }
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            first = row.get('First Name', '').strip()
            last = row.get('Last Name', '').strip()
            if not first or not last:
                continue
            full_name = f"{first} {last}"
            site_distances = {}
            for site, column in site_columns.items():
                value = (row.get(column) or '').strip()
                if value:
                    try:
                        site_distances[site] = float(value)
                    except ValueError:
                        continue
            distances[full_name] = site_distances
    return distances
