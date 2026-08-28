#!/usr/bin/env python3
"""
Propose a minimal-day BBO judging schedule from judge availability and
travel distance, ignoring the site each table was historically run at.

Pairing is site-aware: for each candidate slot, `try_fit` tries each open
site in turn, restricts the judge pool to those feasible at that specific
site, and only then pairs by rank — rather than pairing by rank first and
checking site feasibility afterward, which could (and on the real 2026
data, did) produce pairs whose feasible sites never overlapped even when
a fully valid same-site set of pairs existed in the same pool.

KNOWN LIMITATION: the greedy placement still does not achieve full
coverage — on the real 2026 data it places 35 of 44 tables, leaving 9
UNFILLED. This remaining gap is the expected behavior of a greedy,
non-backtracking heuristic (once a table's judges are committed to a
slot, the algorithm never revisits that choice to free them up for a
higher-need table it processes later) rather than the site-blind-pairing
bug this file used to have. See the "Known limitations" and "Out of
scope" sections of the design spec for detail.

Three named-judge site rules also apply: `SITE_ANCHORS` restricts a
handful of site-host judges to their home site only, and
`DALLAS_HOST_CANDIDATES` requires at least one of two named judges to be
available (per their existing judge-availability data) before Dallas is
offered as a candidate site for a slot at all — neither of those two
personally judges at Dallas.

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

# Site hosts: the site is literally this judge's home or workplace, so
# they're never placed anywhere else.
SITE_ANCHORS = {
    "Amanda Long": "Arlington",
    "Jarrett Long": "Arlington",
    "Reni Morriss": "Keller",
    "Matthew Morriss": "Keller",
    "Mark McCurdy": "Grapevine",
}

# Dallas has no single anchor - either of these two must be present to
# run the site, but neither of them personally judges there.
DALLAS_SITE = "Dallas"
DALLAS_HOST_CANDIDATES = {"Terry Olinger", "Mike Grover"}


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
    """Return the set of sites this judge could be assigned to judge at.

    Three rules, in order:
    - A site-anchored judge (`SITE_ANCHORS`) is only ever feasible at
      their home site, regardless of computed distance — it's literally
      their home or workplace, and they're never placed elsewhere.
    - A Dallas host candidate (`DALLAS_HOST_CANDIDATES`) is never
      feasible to judge AT Dallas — they run the site instead of judging
      there — even though their own availability data may list Dallas
      candidate rows (that same data doubles as the site's host-presence
      signal; see `site_host_requirement_met`).
    - Otherwise: a judge with no distance data is treated as feasible
      everywhere (fail open, per the shared-loader convention). That
      covers two cases that must behave identically: the judge is
      missing from `distances` entirely, and the judge is present with
      an empty dict — which is what `load_judge_distances` writes when
      every distance column on their worksheet row is blank. Treating
      the empty case as "feasible nowhere" would silently drop the judge
      from the whole proposal.
    """
    anchor_site = SITE_ANCHORS.get(judge_name)
    if anchor_site is not None:
        return {anchor_site} & set(sites)

    judge_distances = distances.get(judge_name)
    if not judge_distances:
        feasible = set(sites)
    else:
        feasible = {site for site in sites if judge_distances.get(site, math.inf) <= max_distance}

    if judge_name in DALLAS_HOST_CANDIDATES:
        feasible = feasible - {DALLAS_SITE}
    return feasible


def site_host_requirement_met(site, slot, judge_profiles):
    """Check any site-specific host-presence requirement for this slot.

    Dallas requires at least one of `DALLAS_HOST_CANDIDATES` to have an
    existing availability row for this (date, session) — using their
    regular judge-availability data as the presence signal, not a
    separate data source. Sites with no host requirement always pass.
    """
    if site != DALLAS_SITE:
        return True
    return any(
        slot in judge_profiles[name]['availability']
        for name in DALLAS_HOST_CANDIDATES
        if name in judge_profiles
    )


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


def total_travel_distance(pairs, site, distances):
    """Total distance to `site` summed across every judge in `pairs`."""
    return sum(distances.get(j, {}).get(site, 0.0) for pair in pairs for j in pair)


def pick_site(available_sites, pairs, distances):
    """Pick the site minimizing total judge travel distance for `pairs`."""
    return min(available_sites, key=lambda site: total_travel_distance(pairs, site, distances))


def build_schedule(tables, judge_profiles, distances, sites, max_distance=MAX_DISTANCE_MILES):
    """Greedily place every table into the fewest (date, session) slots
    drawn from judges' declared availability.

    Returns (schedule, slots):
      schedule: list of dicts, one per table:
        {table, name, slot, site, pairs, unfilled_pairs_needed}
        `site`/`pairs` are None/[] and `unfilled_pairs_needed` is set when
        a table couldn't be staffed in any available slot.
      slots: list of (date, session) tuples, in the order they were opened.
    """
    sessions_by_date = defaultdict(set)
    for profile in judge_profiles.values():
        for date, session in profile['availability']:
            sessions_by_date[date].add(session)
    available_dates = sorted(sessions_by_date.keys())

    def session_sort_key(session):
        return (session is None, session or '')

    def eligible(table):
        return eligible_judges_for_table(table, judge_profiles, distances, sites, max_distance)

    tables_sorted = sorted(tables, key=lambda t: (len(eligible(t)), -t['required_pairs']))

    slots = []
    slot_sites_used = defaultdict(set)
    slot_judges_used = defaultdict(set)
    schedule = []

    def open_new_slot(excluded=frozenset()):
        # Prefer completing a date that already has one session open.
        for date in available_dates:
            sessions_open = {s for d, s in slots if d == date}
            remaining = {
                s for s in sessions_by_date[date] - sessions_open
                if (date, s) not in excluded
            }
            if sessions_open and remaining:
                next_session = sorted(remaining, key=session_sort_key)[0]
                slot = (date, next_session)
                slots.append(slot)
                return slot
        # Otherwise open the earliest not-yet-used (date, session).
        for date in available_dates:
            for session in sorted(sessions_by_date[date], key=session_sort_key):
                slot = (date, session)
                if slot not in slots and slot not in excluded:
                    slots.append(slot)
                    return slot
        return None

    def try_fit(table, slot, elig):
        available_sites = [
            s for s in sites
            if s not in slot_sites_used[slot] and site_host_requirement_met(s, slot, judge_profiles)
        ]
        if not available_sites:
            return None
        used_judges = slot_judges_used[slot]
        base_candidates = [
            j for j in elig
            if j not in used_judges and slot in judge_profiles[j]['availability']
        ]
        # Site-aware pairing: pick a candidate site FIRST, restrict the
        # pool to judges feasible there, then pair — instead of pairing by
        # rank alone and checking site feasibility afterward. Pairing
        # first can (and on real data, does) produce a set of pairs whose
        # feasible sites don't overlap, even when a different, fully
        # valid same-site set of pairs exists in the same candidate pool.
        candidate_feasible_sites = {
            j: judge_feasible_sites(j, distances, available_sites, max_distance)
            for j in base_candidates
        }
        successes = []
        for site in available_sites:
            site_candidates = [j for j in base_candidates if site in candidate_feasible_sites[j]]
            pairs = form_pairs(site_candidates, table['required_pairs'], judge_profiles)
            if pairs is not None:
                successes.append((site, pairs))
        if not successes:
            return None
        return min(successes, key=lambda site_pairs: total_travel_distance(site_pairs[1], site_pairs[0], distances))

    for table in tables_sorted:
        elig = eligible(table)
        placed = False
        for slot in list(slots):
            fit = try_fit(table, slot, elig)
            if fit is not None:
                site, pairs = fit
                schedule.append({'table': table['table'], 'name': table['name'],
                                  'slot': slot, 'site': site, 'pairs': pairs,
                                  'unfilled_pairs_needed': None})
                slot_sites_used[slot].add(site)
                for pair in pairs:
                    slot_judges_used[slot].update(pair)
                placed = True
                break
        if placed:
            continue

        found_slot = None
        found_fit = None
        excluded_slots = set()
        while True:
            new_slot = open_new_slot(excluded_slots)
            if new_slot is None:
                break
            fit = try_fit(table, new_slot, elig)
            if fit is not None:
                found_slot = new_slot
                found_fit = fit
                break
            # This newly opened slot doesn't work for this table either -
            # remove it so it doesn't linger and inflate the day/session
            # count, exclude it so it isn't offered again, then try opening
            # the next one.
            slots.pop()
            excluded_slots.add(new_slot)

        if found_slot is None:
            schedule.append({'table': table['table'], 'name': table['name'],
                              'slot': None, 'site': None, 'pairs': [],
                              'unfilled_pairs_needed': table['required_pairs']})
            continue

        site, pairs = found_fit
        schedule.append({'table': table['table'], 'name': table['name'],
                          'slot': found_slot, 'site': site, 'pairs': pairs,
                          'unfilled_pairs_needed': None})
        slot_sites_used[found_slot].add(site)
        for pair in pairs:
            slot_judges_used[found_slot].update(pair)

    return schedule, slots


def format_report(schedule, slots, sites, actual_dates=10, actual_slots=14):
    days_used = sorted({day for day, _ in slots})
    lines = []
    lines.append("BBO Judging Schedule Proposal")
    lines.append("=" * 40)
    placed = [e for e in schedule if e['site'] is not None]
    unfilled = [e for e in schedule if e['site'] is None]
    lines.append(f"Proposed: {len(days_used)} days, {len(slots)} sessions, "
                  f"placing {len(placed)} of {len(schedule)} tables "
                  f"({len(unfilled)} unfilled)")
    lines.append(f"2026 actual: {actual_dates} days, {actual_slots} sessions, "
                  f"{len(schedule)} tables (full coverage)")
    # The floor is computed against the tables actually placed, not all
    # tables, so it can't be read as "we matched the optimum" when most of
    # the schedule is unstaffed.
    floor_basis = len(placed)
    theoretical_floor = math.ceil(floor_basis / len(sites)) if sites else floor_basis
    lines.append(f"Theoretical floor for the {floor_basis} placed tables "
                  f"({len(sites)} sites, full parallelism): {theoretical_floor} sessions")
    if unfilled:
        lines.append("")
        lines.append("NOTE: coverage is incomplete, so the day/session counts above are NOT "
                      "comparable to the 2026 baseline or to the all-44-table floor of "
                      f"{math.ceil(len(schedule) / len(sites)) if sites else len(schedule)} "
                      "sessions. Staffing the unfilled tables would require additional "
                      "sessions. See this script's module docstring and the design spec "
                      "for the known limitation behind the unfilled tables.")
    lines.append("")

    if unfilled:
        lines.append(f"UNFILLED ({len(unfilled)} tables could not be staffed):")
        for e in unfilled:
            lines.append(f"  {e['table']} {e['name']}: needs {e['unfilled_pairs_needed']} pairs")
        lines.append("")

    for day in days_used:
        lines.append(f"Day {day}:")
        for session in ('AM', 'PM', None):
            slot = (day, session)
            if slot not in slots:
                continue
            entries = [e for e in schedule if e['slot'] == slot]
            if not entries:
                continue
            label = session if session else "(single session)"
            lines.append(f"  {label}:")
            for e in sorted(entries, key=lambda e: e['table']):
                pair_strs = ", ".join(f"{a} & {b}" for a, b in e['pairs'])
                lines.append(f"    {e['table']} {e['name']} @ {e['site']}: {pair_strs}")

    return "\n".join(lines)


def main():
    rows = load_assignments("Judges_and_Tables_generated.csv")
    table_styles, table_names = load_styles_by_table("styles by table.csv")
    entry_counts = load_entry_counts("medal_category_counts.csv")
    distances = load_judge_distances()

    tables = build_tables(table_styles, table_names, entry_counts)
    judge_profiles = build_judge_profiles(rows)
    sites = sorted({row['slot'][2] for row in rows if row['slot']})

    schedule, slots = build_schedule(tables, judge_profiles, distances, sites)
    print(format_report(schedule, slots, sites))


if __name__ == '__main__':
    main()
