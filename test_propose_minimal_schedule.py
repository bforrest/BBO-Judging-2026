"""Smoke tests for propose_minimal_schedule.py. Run: python3 test_propose_minimal_schedule.py"""

from propose_minimal_schedule import (
    build_judge_profiles,
    build_tables,
    eligible_judges_for_table,
    form_pairs,
    judge_feasible_sites,
    pick_site,
)


def test_build_tables_computes_required_pairs():
    table_styles = {"T50": {"01A"}, "T88": {"27A"}}
    table_names = {"T50": "Pale Lager", "T88": "Specialty Beer"}
    entry_counts = {"T50": 36, "T88": 5}
    tables = build_tables(table_styles, table_names, entry_counts)
    by_table = {t['table']: t for t in tables}
    assert by_table["T50"]['required_pairs'] == 4, by_table["T50"]  # ceil(36/9)
    assert by_table["T88"]['required_pairs'] == 1, by_table["T88"]  # ceil(5/9)


def test_build_tables_missing_entry_count_defaults_to_one_pair():
    table_styles = {"T1": {"01A"}}
    tables = build_tables(table_styles, {}, {})
    assert tables[0]['required_pairs'] == 1


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
    result = judge_feasible_sites("Jane Doe", distances, ["Dallas", "Keller"], max_distance=20)
    assert result == {"Dallas"}


def test_judge_feasible_sites_missing_judge_is_feasible_everywhere():
    result = judge_feasible_sites("Unknown Judge", {}, ["Dallas", "Keller"], max_distance=20)
    assert result == {"Dallas", "Keller"}


def test_eligible_judges_excludes_conflicts():
    table = {'table': 'T66', 'styles': {'16A', '16B'}}
    profiles = {
        'Brian Street': {'substyles': {'16A'}, 'rank': 'Non-BJCP', 'availability': set()},
        'Jane Doe': {'substyles': {'05A'}, 'rank': 'Level 3: Certified', 'availability': set()},
    }
    result = eligible_judges_for_table(table, profiles, {}, ["Dallas"])
    assert result == ['Jane Doe']


def test_form_pairs_prefers_certified_with_noncertified():
    profiles = {
        'A': {'rank': 'Level 3: Certified'},
        'B': {'rank': 'Non-BJCP'},
        'C': {'rank': 'Level 3: Certified'},
        'D': {'rank': 'Non-BJCP'},
    }
    pairs = form_pairs(['A', 'B', 'C', 'D'], 2, profiles)
    assert pairs is not None
    assert len(pairs) == 2
    for judge_a, judge_b in pairs:
        certified = [profiles[j]['rank'] == 'Level 3: Certified' for j in (judge_a, judge_b)]
        assert any(certified)


def test_form_pairs_rejects_two_noncertified():
    profiles = {'A': {'rank': 'Non-BJCP'}, 'B': {'rank': 'Non-BJCP'}}
    assert form_pairs(['A', 'B'], 1, profiles) is None


def test_form_pairs_returns_none_when_not_enough_judges():
    profiles = {'A': {'rank': 'Level 3: Certified'}, 'B': {'rank': 'Non-BJCP'}}
    assert form_pairs(['A', 'B'], 2, profiles) is None


def test_pick_site_minimizes_total_distance():
    pairs = [('A', 'B')]
    distances = {'A': {'Dallas': 5.0, 'Keller': 40.0}, 'B': {'Dallas': 8.0, 'Keller': 2.0}}
    assert pick_site(['Dallas', 'Keller'], pairs, distances) == 'Dallas'  # 13 < 42


if __name__ == '__main__':
    tests = [obj for name, obj in list(globals().items()) if name.startswith('test_')]
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
    print(f"\n{len(tests)} tests passed")
