#!/usr/bin/env python3
"""
Generate Judge Assignment Recommendations Report

Creates a concise, actionable report showing:
1. Tables that need more certified judges
2. Judges with entry conflicts who need reassignment
3. Suggested pairing improvements
4. Tables with excessive workload

Usage:
    python3 generate_recommendations.py
"""

import csv
from collections import defaultdict
import re

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

def generate_markdown_report():
    """Generate a markdown report with actionable recommendations."""
    
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
    
    # Analyze and categorize issues
    critical_tables = []
    overworked_tables = []
    conflict_tables = []
    pairing_issues = []
    
    for site in sites:
        judges = site['judges']
        certified_judges = [j for j in judges if j['is_certified']]
        non_certified_judges = [j for j in judges if not j['is_certified']]
        
        num_certified = len(certified_judges)
        num_non_certified = len(non_certified_judges)
        num_entries = site['entry_count']
        
        # Check for conflicts
        conflicts = []
        for judge in judges:
            judge_styles = set(judge['substyles'])
            if judge_styles.intersection(site['styles']):
                conflicts.append({
                    'judge': judge['name'],
                    'styles': list(judge_styles.intersection(site['styles']))
                })
        
        # Calculate workload
        max_pairs = min(num_certified, len(judges) // 2) if num_certified else 0
        beers_per_pair = num_entries / max_pairs if max_pairs > 0 else 999
        
        # Categorize issues
        if num_certified == 0 or beers_per_pair > 15:
            critical_tables.append({
                'site': site,
                'certified': num_certified,
                'non_certified': num_non_certified,
                'beers_per_pair': beers_per_pair,
                'conflicts': conflicts
            })
        elif beers_per_pair > 12:
            overworked_tables.append({
                'site': site,
                'certified': num_certified,
                'beers_per_pair': beers_per_pair,
                'conflicts': conflicts
            })
        elif conflicts:
            conflict_tables.append({
                'site': site,
                'conflicts': conflicts
            })
        elif num_non_certified > num_certified * 2:
            pairing_issues.append({
                'site': site,
                'certified': num_certified,
                'non_certified': num_non_certified
            })
    
    # Generate report
    report = []
    report.append("# BBO 2026 Judge Assignment Recommendations\n")
    report.append(f"Generated from {len(sites)} judging sites\n")
    report.append("")
    
    # Critical issues
    if critical_tables:
        report.append("## 🚨 CRITICAL ISSUES - IMMEDIATE ACTION REQUIRED\n")
        report.append(f"**{len(critical_tables)} table(s) need urgent attention**\n")
        
        for item in critical_tables:
            site = item['site']
            report.append(f"### {site['name']}")
            report.append(f"- **Table:** T{site['table_num']} | **Entries:** {site['entry_count']}")
            report.append(f"- **Current:** {item['certified']} certified, {item['non_certified']} non-certified")
            report.append(f"- **Workload:** {item['beers_per_pair']:.1f} beers/pair")
            report.append(f"- **ACTION:** Add {max(1, int(site['entry_count']/12) - item['certified'])} certified judge(s)")
            
            if item['conflicts']:
                report.append(f"- **Conflicts:** {len(item['conflicts'])} judge(s) with entry conflicts")
                for c in item['conflicts']:
                    report.append(f"  - {c['judge']}: {', '.join(c['styles'])}")
            report.append("")
    
    # Overworked tables
    if overworked_tables:
        report.append("## ⚠️  OVERWORKED TABLES\n")
        report.append(f"**{len(overworked_tables)} table(s) with heavy workload**\n")
        
        for item in overworked_tables:
            site = item['site']
            report.append(f"### {site['name']}")
            report.append(f"- **Workload:** {item['beers_per_pair']:.1f} beers/pair (target: ≤12)")
            report.append(f"- **ACTION:** Add 1-2 more certified judge(s) to reduce workload")
            report.append("")
    
    # Conflict tables
    if conflict_tables:
        report.append("## 🔄 ENTRY CONFLICTS - REASSIGNMENT NEEDED\n")
        report.append(f"**{len(conflict_tables)} table(s) with judges evaluating their own entries**\n")
        
        for item in conflict_tables:
            site = item['site']
            report.append(f"### {site['name']}")
            for c in item['conflicts']:
                report.append(f"- **{c['judge']}** entered: {', '.join(c['styles'])}")
                report.append(f"  - ACTION: Reassign to a different table")
            report.append("")
    
    # Pairing imbalances
    if pairing_issues:
        report.append("## 📊 PAIRING IMBALANCES\n")
        report.append(f"**{len(pairing_issues)} table(s) with too many non-certified judges**\n")
        
        for item in pairing_issues:
            site = item['site']
            report.append(f"### {site['name']}")
            report.append(f"- **Current:** {item['certified']} certified vs {item['non_certified']} non-certified")
            report.append(f"- **Recommendation:** Add {(item['non_certified']//2) - item['certified']} certified judge(s)")
            report.append("")
    
    # Summary statistics
    report.append("## 📈 Summary Statistics\n")
    report.append(f"- **Total sites:** {len(sites)}")
    report.append(f"- **Critical issues:** {len(critical_tables)}")
    report.append(f"- **Overworked:** {len(overworked_tables)}")
    report.append(f"- **Conflicts:** {len(conflict_tables)}")
    report.append(f"- **Pairing issues:** {len(pairing_issues)}")
    report.append(f"- **Running smoothly:** {len(sites) - len(critical_tables) - len(overworked_tables) - len(conflict_tables) - len(pairing_issues)}")
    report.append("")
    
    # Next steps
    report.append("## 🎯 Next Steps\n")
    report.append("1. **Immediate:** Address critical tables (need certified judges)")
    report.append("2. **High Priority:** Reassign judges with entry conflicts")
    report.append("3. **Medium Priority:** Balance pairing ratios")
    report.append("4. **Ongoing:** Monitor workload and adjust as needed")
    report.append("")
    report.append("---")
    report.append("*For detailed pairing suggestions, run: `python3 optimize_judge_pairings.py`*")
    
    return '\n'.join(report)

if __name__ == '__main__':
    report = generate_markdown_report()
    
    # Save to file
    with open('JUDGE_RECOMMENDATIONS.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("✅ Generated JUDGE_RECOMMENDATIONS.md")
    print("\nReport preview:\n")
    print(report)
