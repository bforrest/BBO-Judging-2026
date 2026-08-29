"""Smoke tests for solve_schedule_cpsat.py. Run: python3 test_solve_schedule_cpsat.py"""

import os
import tempfile

from solve_schedule_cpsat import (
    DEFAULT_NUM_SEARCH_WORKERS,
    DEFAULT_TIME_LIMIT_SECONDS,
    build_candidate_slots,
    build_judge_profiles,
    build_tables,
    eligible_judges_for_table,
    form_pairs_for_display,
    judge_feasible_sites,
    load_config,
    site_host_requirement_met,
    solve_schedule,
)


def test_load_config_reads_solver_time_limit_seconds():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("solver_time_limit_seconds: 45\n")
        path = f.name
    try:
        config = load_config(path)
        assert config['solver_time_limit_seconds'] == 45, config
    finally:
        os.remove(path)


def test_load_config_defaults_solver_time_limit_seconds_when_absent():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("target_beers_per_pair: 9\n")
        path = f.name
    try:
        config = load_config(path)
        assert config['solver_time_limit_seconds'] == DEFAULT_TIME_LIMIT_SECONDS, config
    finally:
        os.remove(path)


def test_load_config_reads_num_search_workers():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("num_search_workers: 8\n")
        path = f.name
    try:
        config = load_config(path)
        assert config['num_search_workers'] == 8, config
    finally:
        os.remove(path)


def test_load_config_defaults_num_search_workers_when_absent():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("target_beers_per_pair: 9\n")
        path = f.name
    try:
        config = load_config(path)
        assert config['num_search_workers'] == DEFAULT_NUM_SEARCH_WORKERS, config
    finally:
        os.remove(path)


def test_solve_schedule_accepts_explicit_num_search_workers():
    # Just confirms num_search_workers is plumbed through without breaking
    # the solve -- correctness of CP-SAT's own parallel search isn't ours
    # to test, only that we set the parameter without erroring.
    tables = [
        {'table': 'T1', 'name': 'A', 'styles': set(), 'entry_count': 9, 'required_pairs': 1},
    ]
    slot = ('02/07', 'AM')
    profiles = {
        'Judge1': {'rank': 'Level 3: Certified', 'substyles': set(), 'availability': {slot}},
        'Judge2': {'rank': 'Non-BJCP', 'substyles': set(), 'availability': {slot}},
    }
    result = solve_schedule(tables, profiles, {}, ['Arlington'], make_config(), num_search_workers=4)
    assert result['max_placed'] == 1, result


def test_build_tables_computes_required_pairs():
    table_styles = {"T50": {"01A"}, "T88": {"27A"}}
    table_names = {"T50": "Pale Lager", "T88": "Specialty Beer"}
    entry_counts = {"T50": 36, "T88": 5}
    tables = build_tables(table_styles, table_names, entry_counts, target_beers_per_pair=9)
    by_table = {t['table']: t for t in tables}
    assert by_table["T50"]['required_pairs'] == 4, by_table["T50"]  # ceil(36/9)
    assert by_table["T88"]['required_pairs'] == 1, by_table["T88"]  # ceil(5/9)


def test_build_judge_profiles_availability_is_site_agnostic():
    rows = [
        {'FULL NAME': 'Brian Street', 'RANKING': 'Non-BJCP', 'SUBSTYLES ENTERED': '1B',
         'slot': ('02/07', 'AM', 'Arlington', 'T53', 'Pale German')},
        {'FULL NAME': 'Brian Street', 'RANKING': 'Non-BJCP', 'SUBSTYLES ENTERED': '1B',
         'slot': ('02/07', 'AM', 'Dallas', 'T55', 'Kolsch and Blonde')},
    ]
    profiles = build_judge_profiles(rows)
    assert profiles['Brian Street']['availability'] == {('02/07', 'AM')}
    assert profiles['Brian Street']['substyles'] == {'1B'}


def test_judge_feasible_sites_within_distance():
    distances = {"Jane Doe": {"Dallas": 5.0, "Keller": 30.0}}
    result = judge_feasible_sites("Jane Doe", distances, ["Dallas", "Keller"], {}, {}, max_distance=20)
    assert result == {"Dallas"}


def test_judge_feasible_sites_missing_judge_is_feasible_everywhere():
    result = judge_feasible_sites("Unknown Judge", {}, ["Dallas", "Keller"], {}, {}, max_distance=20)
    assert result == {"Dallas", "Keller"}


def test_judge_feasible_sites_site_anchor_overrides_distance():
    distances = {"Amanda Long": {"Arlington": 50.0, "Keller": 1.0}}
    anchors = {"Amanda Long": "Arlington"}
    result = judge_feasible_sites("Amanda Long", distances, ["Arlington", "Keller"], anchors, {}, max_distance=20)
    assert result == {"Arlington"}, result


def test_judge_feasible_sites_host_requirement_judge_excluded_from_that_site():
    distances = {"Terry Olinger": {"Dallas": 1.0, "Keller": 5.0}}
    host_reqs = {"Dallas": ["Terry Olinger", "Mike Grover"]}
    result = judge_feasible_sites("Terry Olinger", distances, ["Dallas", "Keller"], {}, host_reqs, max_distance=20)
    assert result == {"Keller"}, result


def test_site_host_requirement_met_needs_a_named_judge_present():
    profiles = {
        'Terry Olinger': {'availability': {('02/07', 'AM')}},
        'Mike Grover': {'availability': set()},
    }
    host_reqs = {"Dallas": ["Terry Olinger", "Mike Grover"]}
    assert site_host_requirement_met('Dallas', ('02/07', 'AM'), profiles, host_reqs) is True
    assert site_host_requirement_met('Dallas', ('02/07', 'PM'), profiles, host_reqs) is False


def test_site_host_requirement_met_site_with_no_requirement_always_passes():
    assert site_host_requirement_met('Arlington', ('02/07', 'AM'), {}, {}) is True


def test_eligible_judges_excludes_substyle_conflicts():
    table = {'table': 'T66', 'styles': {'16A', '16B'}}
    profiles = {
        'Brian Street': {'substyles': {'16A'}, 'rank': 'Non-BJCP', 'availability': set()},
        'Jane Doe': {'substyles': {'05A'}, 'rank': 'Level 3: Certified', 'availability': set()},
    }
    result = eligible_judges_for_table(table, profiles, {}, ["Dallas"], {}, {}, max_distance=20)
    assert result == ['Jane Doe']


def test_form_pairs_for_display_pairs_certified_with_noncertified():
    profiles = {
        'A': {'rank': 'Level 3: Certified'},
        'B': {'rank': 'Non-BJCP'},
        'C': {'rank': 'Level 3: Certified'},
        'D': {'rank': 'Non-BJCP'},
    }
    pairs = form_pairs_for_display(['A', 'B', 'C', 'D'], profiles)
    assert len(pairs) == 2
    for judge_a, judge_b in pairs:
        certified = [profiles[j]['rank'] == 'Level 3: Certified' for j in (judge_a, judge_b)]
        assert any(certified)


def test_build_candidate_slots_excludes_unmet_host_requirement():
    profiles = {
        'Cert1': {'availability': {('02/07', 'AM')}},
        'Noncert1': {'availability': {('02/07', 'AM')}},
    }
    host_reqs = {"Dallas": ["Terry Olinger"]}
    slots = build_candidate_slots(profiles, ["Dallas", "Keller"], host_reqs)
    assert ('02/07', 'AM', 'Dallas') not in slots
    assert ('02/07', 'AM', 'Keller') in slots


# --- solve_schedule (requires ortools) ------------------------------------

DEFAULT_TEST_CONFIG = {
    'target_beers_per_pair': 9,
    'max_distance_miles': 20,
    'site_anchors': {},
    'site_host_requirements': {},
    'table_site_overrides': [],
}


def make_config(**overrides):
    config = dict(DEFAULT_TEST_CONFIG)
    config.update(overrides)
    return config


def test_solve_schedule_fully_satisfiable_scenario_places_everything():
    tables = [
        {'table': 'T1', 'name': 'A', 'styles': set(), 'entry_count': 9, 'required_pairs': 1},
        {'table': 'T2', 'name': 'B', 'styles': set(), 'entry_count': 9, 'required_pairs': 1},
    ]
    slot = ('02/07', 'AM')
    profiles = {
        'Judge1': {'rank': 'Level 3: Certified', 'substyles': set(), 'availability': {slot}},
        'Judge2': {'rank': 'Non-BJCP', 'substyles': set(), 'availability': {slot}},
        'Judge3': {'rank': 'Level 3: Certified', 'substyles': set(), 'availability': {slot}},
        'Judge4': {'rank': 'Non-BJCP', 'substyles': set(), 'availability': {slot}},
    }
    result = solve_schedule(tables, profiles, {}, ['Arlington', 'Keller'], make_config())
    assert result['max_placed'] == 2, result
    assert result['unfilled'] == []
    assert result['phase1_status'] == 'OPTIMAL'
    assert result['phase2_status'] == 'OPTIMAL'


def test_solve_schedule_unavoidable_conflict_leaves_only_that_table_unfilled():
    # T2's only eligible judges (Judge1/Judge2 share substyle '16A' with it)
    # are entirely conflicted out; T1 has no such conflict and should still
    # be placed using the same judge pool.
    tables = [
        {'table': 'T1', 'name': 'A', 'styles': set(), 'entry_count': 9, 'required_pairs': 1},
        {'table': 'T2', 'name': 'B', 'styles': {'16A'}, 'entry_count': 9, 'required_pairs': 1},
    ]
    slot = ('02/07', 'AM')
    profiles = {
        'Judge1': {'rank': 'Level 3: Certified', 'substyles': {'16A'}, 'availability': {slot}},
        'Judge2': {'rank': 'Non-BJCP', 'substyles': {'16A'}, 'availability': {slot}},
    }
    result = solve_schedule(tables, profiles, {}, ['Arlington'], make_config())
    assert result['max_placed'] == 1, result
    assert [e['table'] for e in result['unfilled']] == ['T2'], result
    assert [e['table'] for e in result['schedule']] == ['T1'], result


def test_solve_schedule_site_anchor_keeps_judge_at_home_site():
    tables = [
        {'table': 'T1', 'name': 'A', 'styles': set(), 'entry_count': 9, 'required_pairs': 1},
    ]
    slot = ('02/06', None)
    profiles = {
        'Amanda Long': {'rank': 'Level 3: Certified', 'substyles': set(), 'availability': {slot}},
        'Some Noncert': {'rank': 'Non-BJCP', 'substyles': set(), 'availability': {slot}},
    }
    distances = {'Amanda Long': {'SiteX': 1.0, 'Arlington': 50.0}}
    config = make_config(site_anchors={'Amanda Long': 'Arlington'})
    result = solve_schedule(tables, profiles, distances, ['SiteX', 'Arlington'], config)
    assert result['schedule'][0]['site'] == 'Arlington', result


def test_solve_schedule_site_host_requirement_blocks_then_allows_site():
    tables = [
        {'table': 'T1', 'name': 'A', 'styles': set(), 'entry_count': 9, 'required_pairs': 1},
    ]
    slot = ('02/06', None)
    profiles_no_host = {
        'Cert1': {'rank': 'Level 3: Certified', 'substyles': set(), 'availability': {slot}},
        'Noncert1': {'rank': 'Non-BJCP', 'substyles': set(), 'availability': {slot}},
    }
    config = make_config(site_host_requirements={'Dallas': ['Terry Olinger']})
    result = solve_schedule(tables, profiles_no_host, {}, ['Dallas'], config)
    assert result['unfilled'] == [{'table': 'T1', 'name': 'A', 'required_pairs': 1}], result

    profiles_with_host = dict(profiles_no_host)
    profiles_with_host['Terry Olinger'] = {'rank': 'Non-BJCP', 'substyles': set(), 'availability': {slot}}
    result2 = solve_schedule(tables, profiles_with_host, {}, ['Dallas'], config)
    assert result2['schedule'][0]['site'] == 'Dallas', result2
    judges_used = {j for pair in result2['schedule'][0]['pairs'] for j in pair}
    assert 'Terry Olinger' not in judges_used, result2


def test_solve_schedule_table_site_override_pins_site():
    tables = [
        {'table': 'T1', 'name': 'A', 'styles': set(), 'entry_count': 9, 'required_pairs': 1},
    ]
    slot = ('02/06', None)
    profiles = {
        'Cert1': {'rank': 'Level 3: Certified', 'substyles': set(), 'availability': {slot}},
        'Noncert1': {'rank': 'Non-BJCP', 'substyles': set(), 'availability': {slot}},
    }
    # Both sites are equally usable; without an override the solver could
    # legitimately pick either. The override must force Keller specifically.
    config = make_config(table_site_overrides=[{'table': 'T1', 'site': 'Keller', 'reason': 'test'}])
    result = solve_schedule(tables, profiles, {}, ['Arlington', 'Keller'], config)
    assert result['schedule'][0]['site'] == 'Keller', result


def test_solve_schedule_two_phase_objective_prefers_fewer_sessions():
    # Two tables that could each be placed in either of two open sessions
    # with the same judge pool (all four judges available both times) -
    # the minimum-session solution uses just one session for both tables,
    # not two.
    tables = [
        {'table': 'T1', 'name': 'A', 'styles': set(), 'entry_count': 9, 'required_pairs': 1},
        {'table': 'T2', 'name': 'B', 'styles': set(), 'entry_count': 9, 'required_pairs': 1},
    ]
    slots = {('02/07', 'AM'), ('02/07', 'PM')}
    profiles = {
        'Judge1': {'rank': 'Level 3: Certified', 'substyles': set(), 'availability': slots},
        'Judge2': {'rank': 'Non-BJCP', 'substyles': set(), 'availability': slots},
        'Judge3': {'rank': 'Level 3: Certified', 'substyles': set(), 'availability': slots},
        'Judge4': {'rank': 'Non-BJCP', 'substyles': set(), 'availability': slots},
    }
    result = solve_schedule(tables, profiles, {}, ['Arlington', 'Keller'], make_config())
    assert result['max_placed'] == 2, result
    assert result['sessions_used'] == 1, result


if __name__ == '__main__':
    tests = [obj for name, obj in list(globals().items()) if name.startswith('test_')]
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
    print(f"\n{len(tests)} tests passed")
