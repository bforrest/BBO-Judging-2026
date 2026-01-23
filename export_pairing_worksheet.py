#!/usr/bin/env python3
"""
Export Pairing Worksheet for Manual Assignment

Creates a CSV file that can be opened in Excel for manual pairing assignments.
Includes columns for suggested pairings and tracking changes.

Usage:
    python3 export_pairing_worksheet.py
"""

import csv
import re
from collections import defaultdict

RANK_WEIGHTS = {
    'Non-BJCP': 0,
    'Non-BJCP, Judge with Sensory Training': 0,
    'Non-BJCP, Certified Cicerone': 0,
    'Provisional, Judge with Sensory Training': 1,
    'Rank Pending': 2,
    'Recognized, Judge with Sensory Training': 2,
    'Recognized': 2,
    'Certified': 3,
    'Certified+Mead': 3,
    'Certified+Mead+cider': 3,
    'Certified, Judge with Sensory Training': 3,
    'Certified, Professional Brewer': 3,
    'National': 4,
    'National, Advanced Cicerone': 4
}

def parse_rank(rank_str: str) -> int:
    return RANK_WEIGHTS.get(rank_str, 0)

def is_certified(rank: str) -> bool:
    return parse_rank(rank) >= 3

def parse_judge_line(judge_data: str):
    judges = []
    parts = judge_data.split(';')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        segments = [s.strip() for s in part.split('|')]
        if len(segments) >= 2:
            name = segments[0]
            rank = segments[1]
            substyles = segments[2].split(',') if len(segments) > 2 and segments[2] else []
            substyles = [s.strip() for s in substyles if s.strip()]
            
            judges.append({
                'name': name,
                'rank': rank,
                'rank_weight': parse_rank(rank),
                'substyles': substyles,
                'is_certified': is_certified(rank)
            })
    
    return judges

def load_entry_counts():
    counts = {}
    with open('medal_category_counts.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            table_num = int(row['Table Number'])
            count = int(row['Count'])
            counts[table_num] = count
    return counts

def extract_table_number(site_name: str):
    match = re.search(r'T(\d+)', site_name)
    return int(match.group(1)) if match else None

def load_table_styles():
    table_styles = defaultdict(set)
    with open('styles by table.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Table Number'] and row['BJCP Style Id']:
                table_num = int(row['Table Number'])
                style_id = row['BJCP Style Id'].strip()
                if style_id:
                    table_styles[table_num].add(style_id)
    return table_styles

def suggest_pairings(judges):
    """Return suggested pairings as list of tuples."""
    certified = [j for j in judges if j['is_certified']]
    non_certified = [j for j in judges if not j['is_certified']]
    
    certified.sort(key=lambda x: x['rank_weight'], reverse=True)
    non_certified.sort(key=lambda x: x['rank_weight'], reverse=True)
    
    max_pairs = min(len(certified), len(judges) // 2) if certified else 0
    
    pairings = []
    for i in range(min(len(certified), len(non_certified), max_pairs)):
        pairings.append((certified[i], non_certified[i]))
    
    # Pair remaining certified judges together if needed
    remaining_certified = certified[len(pairings):]
    for i in range(0, len(remaining_certified) - 1, 2):
        if len(pairings) < max_pairs:
            pairings.append((remaining_certified[i], remaining_certified[i+1]))
    
    return pairings

def export_worksheet():
    """Generate CSV worksheet for manual pairing assignments."""
    
    print("Loading data...")
    entry_counts = load_entry_counts()
    table_styles = load_table_styles()
    
    sites = []
    with open('judges_by_site.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            site_name = row['Site']
            judge_data = row['Judges']
            
            judges = parse_judge_line(judge_data)
            table_num = extract_table_number(site_name)
            
            sites.append({
                'name': site_name,
                'table_num': table_num,
                'judges': judges,
                'entry_count': entry_counts.get(table_num, 0),
                'styles': table_styles.get(table_num, set())
            })
    
    # Create worksheet
    rows = []
    rows.append([
        'Site',
        'Table',
        'Entries',
        'Pair #',
        'Judge 1 Name',
        'Judge 1 Rank',
        'Judge 2 Name',
        'Judge 2 Rank',
        'Beers/Pair',
        'Conflict?',
        'Issue',
        'Action Needed',
        'Notes'
    ])
    
    for site in sites:
        judges = site['judges']
        num_entries = site['entry_count']
        table_num = site['table_num']
        
        # Get suggested pairings
        pairings = suggest_pairings(judges)
        
        if not pairings:
            # No valid pairings
            rows.append([
                site['name'],
                f"T{table_num}",
                num_entries,
                'N/A',
                '',
                '',
                '',
                '',
                'N/A',
                'YES',
                'No certified judges',
                'ADD CERTIFIED JUDGE',
                ''
            ])
            continue
        
        beers_per_pair = num_entries / len(pairings)
        
        # Check for conflicts
        conflicts = {}
        for judge in judges:
            judge_styles = set(judge['substyles'])
            if judge_styles.intersection(site['styles']):
                conflicts[judge['name']] = list(judge_styles.intersection(site['styles']))
        
        # Add rows for each pairing
        for i, (judge1, judge2) in enumerate(pairings, 1):
            conflict = 'YES' if judge1['name'] in conflicts or judge2['name'] in conflicts else 'NO'
            
            issue_parts = []
            if beers_per_pair > 12:
                issue_parts.append(f"High workload ({beers_per_pair:.1f})")
            if judge1['name'] in conflicts:
                issue_parts.append(f"{judge1['name']} conflict: {', '.join(conflicts[judge1['name']])}")
            if judge2['name'] in conflicts:
                issue_parts.append(f"{judge2['name']} conflict: {', '.join(conflicts[judge2['name']])}")
            if not judge1['is_certified'] and not judge2['is_certified']:
                issue_parts.append("Both non-certified")
            
            issue = '; '.join(issue_parts) if issue_parts else ''
            
            action = ''
            if beers_per_pair > 15:
                action = 'ADD JUDGES'
            elif conflict == 'YES':
                action = 'REASSIGN JUDGE'
            elif beers_per_pair > 12:
                action = 'Consider adding judges'
            
            rows.append([
                site['name'] if i == 1 else '',  # Only show site name on first pair
                f"T{table_num}" if i == 1 else '',
                num_entries if i == 1 else '',
                i,
                judge1['name'],
                judge1['rank'],
                judge2['name'],
                judge2['rank'],
                f"{beers_per_pair:.1f}",
                conflict,
                issue,
                action,
                ''
            ])
    
    # Write CSV
    output_file = 'PAIRING_WORKSHEET.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    
    print(f"✅ Generated {output_file}")
    print(f"   Contains {len(rows)-1} pairing rows across {len(sites)} sites")
    print(f"\n📊 Open in Excel to:")
    print("   - Review suggested pairings")
    print("   - Track action items")
    print("   - Add notes and adjustments")
    print("   - Filter by 'Action Needed' column")

if __name__ == '__main__':
    export_worksheet()
