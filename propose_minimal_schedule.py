#!/usr/bin/env python3
"""
Propose a minimal-day BBO judging schedule from judge availability and
travel distance, ignoring the site each table was historically run at.

See docs/superpowers/specs/2026-08-27-judge-utilization-and-schedule-optimization-design.md
"""

import math
from collections import defaultdict

from judging_common import (
    is_certified_or_higher,
    load_assignments,
    load_entry_counts,
    load_judge_distances,
    load_styles_by_table,
    parse_substyles,
)

TARGET_BEERS_PER_PAIR = 9
MAX_DISTANCE_MILES = 20


def build_tables(table_styles, table_names, entry_counts):
    """Build the list of tables to schedule.

    Returns a list of dicts: {table, name, styles, entry_count, required_pairs}.
    """
    tables = []
    for table, styles in table_styles.items():
        entry_count = entry_counts.get(table, 0)
        required_pairs = max(1, math.ceil(entry_count / TARGET_BEERS_PER_PAIR))
        tables.append({
            'table': table,
            'name': table_names.get(table, ''),
            'styles': styles,
            'entry_count': entry_count,
            'required_pairs': required_pairs,
        })
    return tables


def build_judge_profiles(rows):
    """Build per-judge profiles from parsed assignment rows.

    Returns dict judge_name -> {rank, substyles, availability} where
    availability is a set of (date, session) tuples for which the judge
    has any candidate row (site-agnostic).
    """
    profiles = {}
    for row in rows:
        if row['slot'] is None:
            continue
        name = row['FULL NAME'].strip()
        if not name:
            continue
        profile = profiles.setdefault(name, {
            'rank': row.get('RANKING', '').strip(),
            'substyles': parse_substyles(row.get('SUBSTYLES ENTERED', '')),
            'availability': set(),
        })
        date, session, site, table, description = row['slot']
        profile['availability'].add((date, session))
    return profiles


def judge_feasible_sites(judge_name, distances, sites, max_distance=MAX_DISTANCE_MILES):
    """Return the set of sites within max_distance for this judge.

    A judge missing from `distances` is treated as feasible everywhere
    (fail open, per the shared-loader convention).
    """
    judge_distances = distances.get(judge_name)
    if judge_distances is None:
        return set(sites)
    return {site for site in sites if judge_distances.get(site, math.inf) <= max_distance}


def eligible_judges_for_table(table, judge_profiles, distances, sites, max_distance=MAX_DISTANCE_MILES):
    """Judges with no substyle conflict and at least one feasible site."""
    eligible = []
    for name, profile in judge_profiles.items():
        if table['styles'] & profile['substyles']:
            continue
        if judge_feasible_sites(name, distances, sites, max_distance):
            eligible.append(name)
    return eligible


def form_pairs(available_judges, required_pairs, judge_profiles):
    """Form up to required_pairs valid judging pairs.

    A valid pair has at least one certified-or-higher judge (never two
    below-certified). Returns a list of (judge_a, judge_b) tuples, or
    None if required_pairs can't be formed from available_judges.
    """
    certified = [j for j in available_judges if is_certified_or_higher(judge_profiles[j]['rank'])]
    non_certified = [j for j in available_judges if not is_certified_or_higher(judge_profiles[j]['rank'])]

    pairs = []
    used = set()
    for certified_judge in certified:
        if len(pairs) >= required_pairs:
            break
        partner = next((j for j in non_certified if j not in used), None)
        if partner is None:
            continue
        pairs.append((certified_judge, partner))
        used.add(certified_judge)
        used.add(partner)

    remaining_certified = [j for j in certified if j not in used]
    while len(pairs) < required_pairs and len(remaining_certified) >= 2:
        pairs.append((remaining_certified.pop(), remaining_certified.pop()))

    if len(pairs) < required_pairs:
        return None
    return pairs


def pick_site(available_sites, pairs, distances):
    """Pick the site minimizing total judge travel distance for `pairs`."""
    judges = [j for pair in pairs for j in pair]

    def total_distance(site):
        return sum(distances.get(j, {}).get(site, 0.0) for j in judges)

    return min(available_sites, key=total_distance)
