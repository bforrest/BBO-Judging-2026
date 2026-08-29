#!/usr/bin/env python3
"""
Propose a maximum-coverage BBO judging schedule using OR-Tools' CP-SAT
constraint solver, configured entirely from schedule_config.yaml.

This is an independent alternative to propose_minimal_schedule.py, not a
replacement or upgrade path for it -- that script's greedy heuristic and
its constants are untouched. Where propose_minimal_schedule.py commits
early tables to slots and never revisits that choice, this script asks
CP-SAT to find (and prove) the true maximum number of tables that can be
staffed given the real availability/distance/host data, then, among all
assignments that hit that maximum, the one using the fewest sessions.

See docs/superpowers/specs/2026-08-28-cpsat-schedule-solver-design.md
"""

import math
from collections import defaultdict

import yaml
from ortools.sat.python import cp_model

from judging_common import (
    is_certified_or_higher,
    load_assignments,
    load_entry_counts,
    load_judge_distances,
    load_styles_by_table,
    parse_substyles,
)

DEFAULT_CONFIG_PATH = "schedule_config.yaml"
DEFAULT_TIME_LIMIT_SECONDS = 120
DEFAULT_NUM_SEARCH_WORKERS = 0  # 0 = let CP-SAT pick based on available cores


# --- Config -----------------------------------------------------------

def load_config(path=DEFAULT_CONFIG_PATH):
    """Load schedule_config.yaml into a plain dict of solver settings.

    Missing top-level keys fall back to sensible defaults so a minimal
    config file (or an empty one) is valid.
    """
    with open(path, encoding='utf-8') as f:
        raw = yaml.safe_load(f) or {}

    site_anchors = {
        entry['judge']: entry['site']
        for entry in (raw.get('site_anchors') or [])
    }
    site_host_requirements = {
        site: list(judges)
        for site, judges in (raw.get('site_host_requirements') or {}).items()
    }
    table_site_overrides = list(raw.get('table_site_overrides') or [])

    return {
        'target_beers_per_pair': raw.get('target_beers_per_pair', 9),
        'max_distance_miles': raw.get('max_distance_miles', 20),
        'solver_time_limit_seconds': raw.get('solver_time_limit_seconds', DEFAULT_TIME_LIMIT_SECONDS),
        'num_search_workers': raw.get('num_search_workers', DEFAULT_NUM_SEARCH_WORKERS),
        'site_anchors': site_anchors,
        'site_host_requirements': site_host_requirements,
        'table_site_overrides': table_site_overrides,
    }


# --- Data shaping -------------------------------------------------------
# Duplicated from propose_minimal_schedule.py rather than imported: both
# are small, stable, pure functions, and keeping this script fully
# independent of that one (beyond judging_common.py's loaders) is a
# deliberate design goal -- see the design spec's "Relationship to
# propose_minimal_schedule.py" section.

def build_tables(table_styles, table_names, entry_counts, target_beers_per_pair):
    """Build the list of tables to schedule.

    Returns a list of dicts: {table, name, styles, entry_count, required_pairs}.
    """
    tables = []
    for table, styles in table_styles.items():
        entry_count = entry_counts.get(table, 0)
        required_pairs = max(1, math.ceil(entry_count / target_beers_per_pair))
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


# --- Feasibility rules --------------------------------------------------
# Config-driven equivalents of propose_minimal_schedule.py's SITE_ANCHORS/
# DALLAS_HOST_CANDIDATES logic -- same rules, sourced from the YAML config
# instead of hardcoded Python constants.

def judge_feasible_sites(judge_name, distances, sites, site_anchors,
                          site_host_requirements, max_distance):
    """Return the set of sites this judge could be assigned to judge at."""
    anchor_site = site_anchors.get(judge_name)
    if anchor_site is not None:
        return {anchor_site} & set(sites)

    judge_distances = distances.get(judge_name)
    if not judge_distances:
        feasible = set(sites)
    else:
        feasible = {site for site in sites if judge_distances.get(site, math.inf) <= max_distance}

    hosted_sites = {
        site for site, judges in site_host_requirements.items()
        if judge_name in judges
    }
    return feasible - hosted_sites


def site_host_requirement_met(site, slot, judge_profiles, site_host_requirements):
    """Check any site-specific host-presence requirement for this slot."""
    required_judges = site_host_requirements.get(site)
    if not required_judges:
        return True
    return any(
        slot in judge_profiles[name]['availability']
        for name in required_judges
        if name in judge_profiles
    )


def eligible_judges_for_table(table, judge_profiles, distances, sites,
                               site_anchors, site_host_requirements, max_distance):
    """Judges with no substyle conflict and at least one feasible site."""
    eligible = []
    for name, profile in judge_profiles.items():
        if table['styles'] & profile['substyles']:
            continue
        if judge_feasible_sites(name, distances, sites, site_anchors,
                                 site_host_requirements, max_distance):
            eligible.append(name)
    return eligible


def form_pairs_for_display(assigned_judges, judge_profiles):
    """Group a table's already-solved assigned judges into display pairs.

    The CP-SAT model only constrains aggregate counts (certified >=
    non-certified among assigned judges), not which two judges are "a
    pair" -- this reconstructs concrete pairs for the report, using the
    same certified-with-non-certified-first strategy as
    propose_minimal_schedule.py's form_pairs. Assumes assigned_judges
    already satisfies the pairing rule (guaranteed by the solve).
    """
    certified = [j for j in assigned_judges if is_certified_or_higher(judge_profiles[j]['rank'])]
    non_certified = [j for j in assigned_judges if not is_certified_or_higher(judge_profiles[j]['rank'])]

    pairs = []
    used = set()
    for certified_judge in certified:
        partner = next((j for j in non_certified if j not in used), None)
        if partner is None:
            continue
        pairs.append((certified_judge, partner))
        used.add(certified_judge)
        used.add(partner)

    remaining_certified = [j for j in certified if j not in used]
    while len(remaining_certified) >= 2:
        pairs.append((remaining_certified.pop(), remaining_certified.pop()))

    return pairs


# --- Candidate slots ------------------------------------------------------

def build_candidate_slots(judge_profiles, sites, site_host_requirements):
    """Every (date, session, site) triple worth giving the solver a variable
    for: every (date, session) appearing in any judge's declared
    availability, crossed with every real site, minus combinations that
    fail a site_host_requirements check -- computed once, up front, the
    same way site_host_requirement_met does today, shrinking the model
    rather than becoming a runtime constraint.
    """
    plain_slots = set()
    for profile in judge_profiles.values():
        plain_slots.update(profile['availability'])

    candidate_slots = []
    for date, session in plain_slots:
        for site in sites:
            if site_host_requirement_met(site, (date, session), judge_profiles, site_host_requirements):
                candidate_slots.append((date, session, site))
    return candidate_slots


# --- CP-SAT model ---------------------------------------------------------

def solve_schedule(tables, judge_profiles, distances, sites, config,
                    time_limit_seconds=DEFAULT_TIME_LIMIT_SECONDS,
                    num_search_workers=DEFAULT_NUM_SEARCH_WORKERS):
    """Build and solve the two-phase CP-SAT model.

    Returns a dict:
      {
        'max_placed': K,
        'phase1_status', 'phase2_status': solver status names,
        'sessions_used': int,
        'schedule': [{'table','name','slot','site','pairs','required_pairs'}...],
        'unfilled': [{'table','name','required_pairs'}...],
      }
    """
    max_distance = config['max_distance_miles']
    site_anchors = config['site_anchors']
    site_host_requirements = config['site_host_requirements']
    overrides = {o['table']: o['site'] for o in config['table_site_overrides']}

    candidate_slots = build_candidate_slots(judge_profiles, sites, site_host_requirements)

    model = cp_model.CpModel()

    table_slot = {}                       # (table, cslot) -> BoolVar
    table_candidate_slots = defaultdict(list)
    judge_table = {}                      # (judge, table) -> BoolVar
    eligible_by_table = {}
    placed_vars = {}

    for t in tables:
        table_name = t['table']
        override_site = overrides.get(table_name)
        eligible = eligible_judges_for_table(
            t, judge_profiles, distances, sites, site_anchors, site_host_requirements, max_distance)
        eligible_by_table[table_name] = eligible
        for j in eligible:
            judge_table[(j, table_name)] = model.NewBoolVar(f'judge_table[{j}][{table_name}]')

        for cslot in candidate_slots:
            _, _, site = cslot
            if override_site is not None and site != override_site:
                continue
            var = model.NewBoolVar(f'table_slot[{table_name}][{cslot}]')
            table_slot[(table_name, cslot)] = var
            table_candidate_slots[table_name].append(cslot)

    # One slot per table, and a placed[] indicator for the cert-pairing
    # constraint below.
    for t in tables:
        table_name = t['table']
        cslots = table_candidate_slots[table_name]
        placed = model.NewBoolVar(f'placed[{table_name}]')
        if cslots:
            model.Add(sum(table_slot[(table_name, c)] for c in cslots) <= 1)
            model.Add(placed == sum(table_slot[(table_name, c)] for c in cslots))
        else:
            model.Add(placed == 0)
        placed_vars[table_name] = placed

    # One table per (date, session, site).
    tables_by_cslot = defaultdict(list)
    for (table_name, cslot), var in table_slot.items():
        tables_by_cslot[cslot].append(var)
    for cslot, vars_ in tables_by_cslot.items():
        model.Add(sum(vars_) <= 1)

    # judge_table_slot auxiliary variables: only created for (judge, table,
    # cslot) combinations that pass availability and site-feasibility
    # checks -- this is where "judge availability" and "judge feasible
    # sites" are enforced, by simply not offering the solver an option
    # rather than as runtime constraints.
    jts_by_table_cslot = defaultdict(list)   # (table, cslot) -> [(judge, var), ...]
    jts_by_judge_plain = defaultdict(list)   # (judge, (date,session)) -> [var,...]

    for t in tables:
        table_name = t['table']
        for j in eligible_by_table[table_name]:
            jt_var = judge_table[(j, table_name)]
            for cslot in table_candidate_slots[table_name]:
                date, session, site = cslot
                if (date, session) not in judge_profiles[j]['availability']:
                    continue
                if site not in judge_feasible_sites(
                        j, distances, [site], site_anchors, site_host_requirements, max_distance):
                    continue
                ts_var = table_slot[(table_name, cslot)]
                jts_var = model.NewBoolVar(f'jts[{j}][{table_name}][{cslot}]')
                model.Add(jts_var <= jt_var)
                model.Add(jts_var <= ts_var)
                model.Add(jts_var >= jt_var + ts_var - 1)
                jts_by_table_cslot[(table_name, cslot)].append((j, jts_var))
                jts_by_judge_plain[(j, (date, session))].append(jts_var)

    # Required pairs: when a table is placed in a given candidate slot, the
    # number of assigned judges there must equal 2 * required_pairs. (The
    # "if not placed, 0" half is automatic: jts_var <= ts_var already
    # forces every participant var to 0 when ts_var is 0.)
    for t in tables:
        table_name = t['table']
        required = 2 * t['required_pairs']
        for cslot in table_candidate_slots[table_name]:
            ts_var = table_slot[(table_name, cslot)]
            participants = [var for _, var in jts_by_table_cslot[(table_name, cslot)]]
            model.Add(sum(participants) == required).OnlyEnforceIf(ts_var)

    # Certification pairing: among a placed table's assigned judges, the
    # below-certified count may not exceed the certified-or-higher count.
    for t in tables:
        table_name = t['table']
        eligible = eligible_by_table[table_name]
        certified = [j for j in eligible if is_certified_or_higher(judge_profiles[j]['rank'])]
        non_certified = [j for j in eligible if not is_certified_or_higher(judge_profiles[j]['rank'])]
        if not certified and not non_certified:
            continue
        model.Add(
            sum(judge_table[(j, table_name)] for j in non_certified)
            <= sum(judge_table[(j, table_name)] for j in certified)
        ).OnlyEnforceIf(placed_vars[table_name])

    # No judge double-booked in a (date, session), regardless of site.
    for _, vars_ in jts_by_judge_plain.items():
        if len(vars_) > 1:
            model.Add(sum(vars_) <= 1)

    # slot_used[(date,session)] for the phase-2 "fewest sessions" objective.
    vars_by_plain = defaultdict(list)
    for (table_name, cslot), var in table_slot.items():
        date, session, _ = cslot
        vars_by_plain[(date, session)].append(var)
    slot_used_vars = {}
    for plain, vars_ in vars_by_plain.items():
        su = model.NewBoolVar(f'slot_used[{plain}]')
        model.AddMaxEquality(su, vars_)
        slot_used_vars[plain] = su

    all_table_slot_vars = list(table_slot.values())

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    if num_search_workers:
        solver.parameters.num_search_workers = num_search_workers

    # Phase 1: maximize tables placed.
    model.Maximize(sum(all_table_slot_vars))
    phase1_status = solver.Solve(model)
    phase1_status_name = solver.StatusName(phase1_status)
    if phase1_status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"CP-SAT phase 1 failed: {phase1_status_name}")
    max_placed = int(solver.ObjectiveValue())

    # Phase 2: pin the max, minimize sessions used.
    model.Add(sum(all_table_slot_vars) == max_placed)
    model.Minimize(sum(slot_used_vars.values()))
    phase2_status = solver.Solve(model)
    phase2_status_name = solver.StatusName(phase2_status)
    if phase2_status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"CP-SAT phase 2 failed: {phase2_status_name}")

    schedule = []
    unfilled = []
    for t in tables:
        table_name = t['table']
        active_cslot = None
        for cslot in table_candidate_slots[table_name]:
            if solver.Value(table_slot[(table_name, cslot)]):
                active_cslot = cslot
                break
        if active_cslot is None:
            unfilled.append({
                'table': table_name,
                'name': t['name'],
                'required_pairs': t['required_pairs'],
            })
            continue
        date, session, site = active_cslot
        assigned_judges = [
            j for j, var in jts_by_table_cslot[(table_name, active_cslot)]
            if solver.Value(var)
        ]
        pairs = form_pairs_for_display(assigned_judges, judge_profiles)
        schedule.append({
            'table': table_name,
            'name': t['name'],
            'slot': (date, session),
            'site': site,
            'pairs': pairs,
            'required_pairs': t['required_pairs'],
        })

    sessions_used = sum(1 for su in slot_used_vars.values() if solver.Value(su))

    return {
        'max_placed': max_placed,
        'phase1_status': phase1_status_name,
        'phase2_status': phase2_status_name,
        'sessions_used': sessions_used,
        'schedule': schedule,
        'unfilled': unfilled,
    }


# --- Reporting -------------------------------------------------------

def format_report(result, total_tables, config, config_path=DEFAULT_CONFIG_PATH):
    schedule = result['schedule']
    unfilled = result['unfilled']
    lines = []
    lines.append("BBO Judging Schedule Solver (CP-SAT)")
    lines.append("=" * 37)
    lines.append(
        f"Config: target_beers_per_pair={config['target_beers_per_pair']}, "
        f"max_distance_miles={config['max_distance_miles']}, "
        f"solver_time_limit_seconds={config['solver_time_limit_seconds']}, "
        f"num_search_workers={config['num_search_workers'] or 'auto'} ({config_path})"
    )

    proven_optimal = result['phase1_status'] == 'OPTIMAL' and result['phase2_status'] == 'OPTIMAL'
    status_word = "optimally" if proven_optimal else "(TIME LIMIT HIT - not proven optimal)"
    lines.append(
        f"Solved {status_word}: {result['max_placed']} of {total_tables} tables placed "
        f"({len(unfilled)} unfilled)"
    )
    lines.append(f"Sessions used: {result['sessions_used']}")

    def phase_note(status):
        return "proven optimal" if status == 'OPTIMAL' else "time limit hit, not proven optimal"
    lines.append(
        f"Phase 1 (maximize tables placed): {result['phase1_status']} ({phase_note(result['phase1_status'])})"
    )
    lines.append(
        f"Phase 2 (minimize sessions used): {result['phase2_status']} ({phase_note(result['phase2_status'])})"
    )

    if config['table_site_overrides']:
        lines.append("")
        lines.append("Overrides applied:")
        for o in config['table_site_overrides']:
            reason = f" -- {o['reason']}" if o.get('reason') else ""
            lines.append(f"  {o['table']} pinned to {o['site']}{reason}")

    lines.append("")
    if unfilled:
        lines.append(f"UNFILLED ({len(unfilled)} tables - no assignment could place them given current config):")
        for e in sorted(unfilled, key=lambda e: e['table']):
            lines.append(f"  {e['table']} {e['name']}: needs {e['required_pairs']} pairs")
        lines.append("")

    by_slot = defaultdict(list)
    for e in schedule:
        by_slot[e['slot']].append(e)
    days = sorted({slot[0] for slot in by_slot})

    def session_sort_key(session):
        return (session is None, session or '')

    for day in days:
        lines.append(f"Day {day}:")
        sessions = sorted({s for d, s in by_slot if d == day}, key=session_sort_key)
        for session in sessions:
            entries = by_slot[(day, session)]
            label = session if session else "(single session)"
            lines.append(f"  {label}:")
            for e in sorted(entries, key=lambda e: e['table']):
                pair_strs = ", ".join(f"{a} & {b}" for a, b in e['pairs'])
                lines.append(f"    {e['table']} {e['name']} @ {e['site']}: {pair_strs}")

    return "\n".join(lines)


def main():
    config = load_config()

    rows = load_assignments("Judges_and_Tables_generated.csv")
    table_styles, table_names = load_styles_by_table("styles by table.csv")
    entry_counts = load_entry_counts("medal_category_counts.csv")
    distances = load_judge_distances()

    tables = build_tables(table_styles, table_names, entry_counts, config['target_beers_per_pair'])
    judge_profiles = build_judge_profiles(rows)
    sites = sorted({row['slot'][2] for row in rows if row['slot']})

    result = solve_schedule(tables, judge_profiles, distances, sites, config,
                             time_limit_seconds=config['solver_time_limit_seconds'],
                             num_search_workers=config['num_search_workers'])
    print(format_report(result, len(tables), config))


if __name__ == '__main__':
    main()
