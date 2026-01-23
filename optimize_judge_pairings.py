#!/usr/bin/env python3
"""
BBO 2026 Judge Pairing and Workload Optimizer

This script analyzes judge assignments, identifies pairing and workload issues,
and suggests optimal pairings based on:
1. Pairing rules: Non-certified judges must pair with certified judges (rank >= 3)
2. Workload constraints: Ideal 9 beers/pair, max 12 beers/pair
3. Conflict avoidance: Judges cannot evaluate their own entries

Usage:
    python3 optimize_judge_pairings.py
"""

import csv
from collections import defaultdict
from typing import Dict, List, Tuple, Set
import re

# Rank mapping with weights
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
    """Get numeric rank weight from rank string."""
    return RANK_WEIGHTS.get(rank_str, 0)

def is_certified(rank: str) -> bool:
    """Check if judge is certified or higher (rank >= 3)."""
    return parse_rank(rank) >= 3

def parse_judge_line(judge_data: str) -> List[Dict]:
    """Parse the pipe-separated judge data."""
    judges = []
    parts = judge_data.split(';')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        # Split by pipe: Name | Rank | Substyles
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

def load_entry_counts() -> Dict[int, int]:
    """Load medal category counts by table number."""
    counts = {}
    with open('medal_category_counts.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            table_num = int(row['Table Number'])
            count = int(row['Count'])
            counts[table_num] = count
    return counts

def extract_table_number(site_name: str) -> int:
    """Extract table number from site name like '02/06 Arlington T68 American Pale Ale'."""
    match = re.search(r'T(\d+)', site_name)
    if match:
        return int(match.group(1))
    return None

def calculate_optimal_pairs(num_judges: int, num_certified: int, num_entries: int) -> Tuple[int, float, str]:
    """
    Calculate optimal number of pairs and beers per pair.
    Returns: (num_pairs, beers_per_pair, quality_rating)
    """
    # Each pair needs at least 1 certified judge
    max_pairs = min(num_certified, num_judges // 2)
    
    if max_pairs == 0:
        return (0, 0, "CRITICAL: No certified judges available")
    
    beers_per_pair = num_entries / max_pairs
    
    # Quality rating
    if beers_per_pair <= 9:
        quality = "EXCELLENT"
    elif beers_per_pair <= 12:
        quality = "ACCEPTABLE"
    elif beers_per_pair <= 15:
        quality = "OVERWORKED"
    else:
        quality = "CRITICAL"
    
    return (max_pairs, beers_per_pair, quality)

def suggest_pairings(judges: List[Dict], num_pairs: int) -> List[Tuple[Dict, Dict]]:
    """
    Suggest optimal pairings. Each pair should have one certified judge.
    Returns list of (certified_judge, non_certified_judge) tuples.
    """
    certified = [j for j in judges if j['is_certified']]
    non_certified = [j for j in judges if not j['is_certified']]
    
    # Sort by rank weight (highest first) for best pairings
    certified.sort(key=lambda x: x['rank_weight'], reverse=True)
    non_certified.sort(key=lambda x: x['rank_weight'], reverse=True)
    
    pairings = []
    
    # Pair each certified judge with a non-certified judge
    for i in range(min(len(certified), len(non_certified), num_pairs)):
        pairings.append((certified[i], non_certified[i]))
    
    # If we have extra certified judges and need more pairs
    remaining_certified = certified[len(pairings):]
    if remaining_certified and len(pairings) < num_pairs:
        # Pair certified judges together
        for i in range(0, len(remaining_certified) - 1, 2):
            if len(pairings) >= num_pairs:
                break
            pairings.append((remaining_certified[i], remaining_certified[i+1]))
    
    return pairings

def check_entry_conflicts(judges: List[Dict], table_styles: Set[str]) -> List[Dict]:
    """
    Check if any judge has entered a beer in the styles being judged at this table.
    Returns list of judges with conflicts.
    """
    conflicts = []
    for judge in judges:
        # Check if any of the judge's substyles overlap with table styles
        judge_styles = set(judge['substyles'])
        if judge_styles.intersection(table_styles):
            conflicts.append({
                'judge': judge,
                'conflicting_styles': list(judge_styles.intersection(table_styles))
            })
    return conflicts

def load_table_styles() -> Dict[int, Set[str]]:
    """Load BJCP styles by table number."""
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

def analyze_and_optimize():
    """Main analysis and optimization function."""
    print("=" * 80)
    print("BBO 2026 JUDGE PAIRING AND WORKLOAD OPTIMIZER")
    print("=" * 80)
    print()
    
    # Load data
    print("Loading data...")
    entry_counts = load_entry_counts()
    table_styles = load_table_styles()
    
    # Load judge assignments
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
    
    print(f"Loaded {len(sites)} judging sites")
    print()
    
    # Analyze each site
    issues_found = 0
    recommendations = []
    
    for site in sites:
        judges = site['judges']
        num_entries = site['entry_count']
        table_num = site['table_num']
        
        # Count certified vs non-certified
        certified_judges = [j for j in judges if j['is_certified']]
        non_certified_judges = [j for j in judges if not j['is_certified']]
        
        num_certified = len(certified_judges)
        num_non_certified = len(non_certified_judges)
        total_judges = len(judges)
        
        # Calculate optimal pairings
        num_pairs, beers_per_pair, quality = calculate_optimal_pairs(
            total_judges, num_certified, num_entries
        )
        
        # Check for conflicts
        conflicts = check_entry_conflicts(judges, site['styles'])
        
        # Determine if there are issues
        has_issues = False
        issue_types = []
        
        if quality in ["OVERWORKED", "CRITICAL"]:
            has_issues = True
            issue_types.append(f"Workload: {beers_per_pair:.1f} beers/pair")
        
        if num_certified == 0:
            has_issues = True
            issue_types.append("No certified judges")
        elif num_non_certified > num_certified:
            has_issues = True
            issue_types.append(f"Pairing imbalance: {num_certified}C vs {num_non_certified}NC")
        
        if conflicts:
            has_issues = True
            issue_types.append(f"{len(conflicts)} entry conflicts")
        
        # Print detailed analysis
        if has_issues:
            issues_found += 1
            print("=" * 80)
            print(f"⚠️  SITE: {site['name']}")
            print("=" * 80)
            print(f"Table: T{table_num} | Entries: {num_entries}")
            print(f"Judges: {total_judges} total ({num_certified} certified, {num_non_certified} non-certified)")
            print(f"Quality: {quality} | {beers_per_pair:.1f} beers/pair ({num_pairs} pairs possible)")
            print()
            
            if issue_types:
                print("ISSUES:")
                for issue in issue_types:
                    print(f"  • {issue}")
                print()
            
            # Show current judges
            print("CURRENT JUDGES:")
            for j in judges:
                cert_mark = "✓ CERT" if j['is_certified'] else "✗ Non-Cert"
                conflict_mark = " ⚠️ CONFLICT" if any(c['judge'] == j for c in conflicts) else ""
                print(f"  {cert_mark:12} | {j['name']:30} | {j['rank']}{conflict_mark}")
            print()
            
            # Suggest optimal pairings
            if num_pairs > 0:
                suggested_pairings = suggest_pairings(judges, num_pairs)
                print(f"SUGGESTED PAIRINGS ({len(suggested_pairings)} pairs, ~{num_entries/len(suggested_pairings):.1f} beers/pair):")
                for i, (judge1, judge2) in enumerate(suggested_pairings, 1):
                    print(f"  Pair {i}:")
                    print(f"    • {judge1['name']:30} ({judge1['rank']})")
                    print(f"    • {judge2['name']:30} ({judge2['rank']})")
                print()
            
            # Show conflicts in detail
            if conflicts:
                print("ENTRY CONFLICTS (judge cannot evaluate their own entry):")
                for conflict in conflicts:
                    j = conflict['judge']
                    styles = ', '.join(conflict['conflicting_styles'])
                    print(f"  • {j['name']:30} entered: {styles}")
                print()
            
            # Recommendations
            rec = {
                'site': site['name'],
                'issues': issue_types,
                'actions': []
            }
            
            if num_certified < (num_non_certified // 2 + 1):
                rec['actions'].append(f"Add {(num_non_certified // 2 + 1) - num_certified} more certified judge(s)")
            
            if beers_per_pair > 12:
                needed_pairs = num_entries / 12
                needed_certified = int(needed_pairs) - num_certified
                if needed_certified > 0:
                    rec['actions'].append(f"Add {needed_certified} more certified judge(s) to reduce workload to 12 beers/pair")
            
            if conflicts:
                rec['actions'].append(f"Reassign {len(conflicts)} judge(s) with entry conflicts to different tables")
            
            if rec['actions']:
                print("RECOMMENDED ACTIONS:")
                for action in rec['actions']:
                    print(f"  → {action}")
                print()
            
            recommendations.append(rec)
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total sites analyzed: {len(sites)}")
    print(f"Sites with issues: {issues_found}")
    print(f"Sites running smoothly: {len(sites) - issues_found}")
    print()
    
    if recommendations:
        print("TOP PRIORITIES:")
        # Sort by severity
        critical = [r for r in recommendations if any('CRITICAL' in str(i) for i in r['issues'])]
        overworked = [r for r in recommendations if any('OVERWORKED' in str(i) for i in r['issues'])]
        
        if critical:
            print(f"\n🚨 CRITICAL ISSUES ({len(critical)} sites):")
            for rec in critical[:5]:  # Show top 5
                print(f"  • {rec['site']}")
                for action in rec['actions'][:2]:
                    print(f"    → {action}")
        
        if overworked:
            print(f"\n⚠️  OVERWORKED TABLES ({len(overworked)} sites):")
            for rec in overworked[:5]:  # Show top 5
                print(f"  • {rec['site']}")
                for action in rec['actions'][:2]:
                    print(f"    → {action}")
    
    print()
    print("=" * 80)
    print("Analysis complete!")
    print("=" * 80)

if __name__ == '__main__':
    analyze_and_optimize()
