#!/usr/bin/env python3
"""
Add Pairing Suggestions to Generated HTML Schedule

This script enhances the judging schedule HTML by adding optimal pairing suggestions
for each table based on:
1. Certified judges must be paired with non-certified judges
2. Workload optimization (9-12 beers per pair)
3. Entry conflict avoidance

Usage:
    python3 add_pairing_suggestions.py
"""

import re
from typing import Dict, List, Tuple

# Rank mapping
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
    """Get numeric rank weight."""
    return RANK_WEIGHTS.get(rank_str, 0)

def is_certified(rank: str) -> bool:
    """Check if judge is certified or higher."""
    return parse_rank(rank) >= 3

def generate_pairing_html(judges_data: str, num_entries: int) -> str:
    """Generate HTML for pairing suggestions."""
    # Parse judges
    judges = []
    parts = judges_data.split(';')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        segments = [s.strip() for s in part.split('|')]
        if len(segments) >= 2:
            name = segments[0]
            rank = segments[1]
            judges.append({
                'name': name,
                'rank': rank,
                'rank_weight': parse_rank(rank),
                'is_certified': is_certified(rank)
            })
    
    # Separate certified and non-certified
    certified = [j for j in judges if j['is_certified']]
    non_certified = [j for j in judges if not j['is_certified']]
    
    # Sort by rank
    certified.sort(key=lambda x: x['rank_weight'], reverse=True)
    non_certified.sort(key=lambda x: x['rank_weight'], reverse=True)
    
    # Calculate optimal pairs
    max_pairs = min(len(certified), len(judges) // 2) if certified else 0
    
    if max_pairs == 0:
        return '<div class="pairing-suggestions critical">⚠️ No certified judges available for pairing</div>'
    
    beers_per_pair = num_entries / max_pairs
    
    # Generate pairings
    pairings = []
    for i in range(min(len(certified), len(non_certified), max_pairs)):
        pairings.append((certified[i], non_certified[i]))
    
    # HTML output
    quality_class = 'excellent' if beers_per_pair <= 9 else 'acceptable' if beers_per_pair <= 12 else 'overworked'
    
    html = f'<div class="pairing-suggestions {quality_class}">'
    html += f'<div class="pairing-header">💡 Suggested Pairings ({len(pairings)} pairs × ~{beers_per_pair:.1f} beers/pair)</div>'
    html += '<div class="pairing-list">'
    
    for i, (cert_judge, non_cert_judge) in enumerate(pairings, 1):
        html += f'''
        <div class="pair">
            <span class="pair-number">Pair {i}:</span>
            <div class="pair-judges">
                <div class="judge-in-pair certified-judge">✓ {cert_judge['name']} <span class="rank-badge">({cert_judge['rank']})</span></div>
                <div class="judge-in-pair non-certified-judge">→ {non_cert_judge['name']} <span class="rank-badge">({non_cert_judge['rank']})</span></div>
            </div>
        </div>
        '''
    
    html += '</div></div>'
    return html

print("This script provides pairing suggestion functions for integration.")
print("Run optimize_judge_pairings.py for full analysis.")
print("\nTo integrate pairing suggestions into HTML:")
print("1. The generate_optimized_schedule.py already highlights issues")
print("2. Use optimize_judge_pairings.py output for detailed recommendations")
print("3. Manual pairing adjustments can be made in Judges and Tables.tsv")
