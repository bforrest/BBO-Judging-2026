"""Smoke tests for analyze_judge_utilization.py. Run: python3 test_analyze_judge_utilization.py"""

from analyze_judge_utilization import (
    analyze_gaps,
    count_confirmed_judge_sessions,
    distance_stats,
    find_double_bookings,
    format_report,
    group_by_judge_and_date,
    utilization_pct,
)


def make_row(name, date, session, site, table, pairing='', substyles=''):
    return {
        'FULL NAME': name,
        'PAIRING': pairing,
        'SUBSTYLES ENTERED': substyles,
        'slot': (date, session, site, table, 'Description'),
    }


def test_explained_by_conflict():
    substyles = "16A, 16B"
    rows = [
        make_row("Brian Street", "02/28", "AM", "Keller", "T66", substyles=substyles),
        make_row("Brian Street", "02/28", "PM", "Arlington", "T92", pairing="P3", substyles=substyles),
    ]
    table_styles = {"T66": {"16A", "16B", "16C"}, "T92": {"C2A"}}
    grouped = group_by_judge_and_date(rows)
    idle_findings, explained, unexplained = analyze_gaps(grouped, table_styles, {})
    assert explained == 1, explained
    assert unexplained == 0, unexplained
    assert idle_findings == []


def test_unexplained_idle_capacity():
    substyles = "16A"
    rows = [
        make_row("Jane Doe", "02/14", "AM", "Keller", "T56", substyles=substyles),
        make_row("Jane Doe", "02/14", "PM", "Arlington", "T57", pairing="P1", substyles=substyles),
    ]
    table_styles = {"T56": {"05A"}, "T57": {"06A"}}
    grouped = group_by_judge_and_date(rows)
    idle_findings, explained, unexplained = analyze_gaps(grouped, table_styles, {})
    assert explained == 0, explained
    assert unexplained == 1, unexplained
    assert len(idle_findings) == 1
    assert idle_findings[0]['judge'] == "Jane Doe"
    assert idle_findings[0]['session'] == "AM"


def test_idle_capacity_sorted_by_distance():
    rows = [
        make_row("Jane Doe", "02/14", "AM", "Keller", "T56"),
        make_row("Jane Doe", "02/14", "AM", "Dallas", "T55"),
        make_row("Jane Doe", "02/14", "PM", "Arlington", "T57", pairing="P1"),
    ]
    table_styles = {"T56": {"05A"}, "T55": {"06A"}, "T57": {"07A"}}
    distances = {"Jane Doe": {"Keller": 30.0, "Dallas": 5.0}}
    grouped = group_by_judge_and_date(rows)
    idle_findings, explained, unexplained = analyze_gaps(grouped, table_styles, distances)
    assert len(idle_findings) == 1
    candidates = idle_findings[0]['candidates']
    assert [row['slot'][3] for row, _ in candidates] == ["T55", "T56"]


def test_gap_category_partially_used():
    # Judge has a confirmed PM session that date, so the AM gap is a
    # specific blocked session, not a wholly wasted day.
    rows = [
        make_row("Jane Doe", "02/14", "AM", "Keller", "T56"),
        make_row("Jane Doe", "02/14", "PM", "Arlington", "T57", pairing="P1"),
    ]
    table_styles = {"T56": {"05A"}, "T57": {"06A"}}
    grouped = group_by_judge_and_date(rows)
    idle_findings, _, _ = analyze_gaps(grouped, table_styles, {})
    assert len(idle_findings) == 1
    assert idle_findings[0]['category'] == 'partially_used', idle_findings[0]


def test_gap_category_wholly_unused():
    # Judge was available AM and PM on a multi-session day and confirmed
    # for neither - the whole day went unused.
    rows = [
        make_row("Jane Doe", "02/14", "AM", "Keller", "T56"),
        make_row("Jane Doe", "02/14", "PM", "Arlington", "T57"),
    ]
    table_styles = {"T56": {"05A"}, "T57": {"06A"}}
    grouped = group_by_judge_and_date(rows)
    idle_findings, _, _ = analyze_gaps(grouped, table_styles, {})
    assert len(idle_findings) == 2
    assert all(f['category'] == 'wholly_unused' for f in idle_findings), idle_findings


def test_idle_findings_ranked_by_best_candidate_distance():
    rows = [
        # Far judge: closest missed opportunity is 30mi.
        make_row("Far Judge", "02/14", "AM", "Keller", "T56"),
        make_row("Far Judge", "02/14", "PM", "Arlington", "T57", pairing="P1"),
        # Near judge: closest missed opportunity is 3mi.
        make_row("Near Judge", "02/14", "AM", "Dallas", "T55"),
        make_row("Near Judge", "02/14", "PM", "Arlington", "T57", pairing="P2"),
        # Unknown judge: no distance data at all - must sort last.
        make_row("Unknown Judge", "02/14", "AM", "Grapevine", "T58"),
        make_row("Unknown Judge", "02/14", "PM", "Arlington", "T57", pairing="P3"),
    ]
    table_styles = {"T55": {"01A"}, "T56": {"05A"}, "T57": {"06A"}, "T58": {"07A"}}
    distances = {"Far Judge": {"Keller": 30.0}, "Near Judge": {"Dallas": 3.0}}
    grouped = group_by_judge_and_date(rows)
    idle_findings, _, _ = analyze_gaps(grouped, table_styles, distances)
    assert [f['judge'] for f in idle_findings] == ["Near Judge", "Far Judge", "Unknown Judge"], \
        [f['judge'] for f in idle_findings]


def test_count_confirmed_judge_sessions_counts_unique_triples():
    rows = [
        # Same judge/date/session confirmed at two sites - counts once.
        make_row("Jane Doe", "02/14", "AM", "Keller", "T56", pairing="P1"),
        make_row("Jane Doe", "02/14", "AM", "Dallas", "T55", pairing="P2"),
        # A different session same day - counts separately.
        make_row("Jane Doe", "02/14", "PM", "Arlington", "T57", pairing="P3"),
        # Unconfirmed row - not counted.
        make_row("Jane Doe", "02/21", "AM", "Keller", "T60"),
        # A single-session day for another judge - still counted.
        make_row("John Roe", "02/06", None, "Grapevine", "T66", pairing="P4"),
    ]
    assert count_confirmed_judge_sessions(rows) == 3, count_confirmed_judge_sessions(rows)


def test_count_confirmed_judge_sessions_skips_unparseable_and_nameless():
    rows = [
        {'FULL NAME': 'Jane Doe', 'PAIRING': 'P1', 'SUBSTYLES ENTERED': '', 'slot': None},
        {'FULL NAME': '  ', 'PAIRING': 'P1', 'SUBSTYLES ENTERED': '',
         'slot': ('02/14', 'AM', 'Keller', 'T56', 'd')},
    ]
    assert count_confirmed_judge_sessions(rows) == 0


def test_utilization_pct_uses_spec_formula():
    # 3 confirmed, 1 unexplained idle -> 75%
    assert utilization_pct(3, 1) == 75.0
    assert utilization_pct(0, 0) is None


def test_distance_stats_average_and_median_of_best_candidates():
    findings = [
        {'candidates': [('rowA', 2.0), ('rowB', 10.0)]},
        {'candidates': [('rowC', 4.0)]},
        {'candidates': [('rowD', 9.0)]},
    ]
    average, median, skipped = distance_stats(findings)
    assert average == 5.0, average          # (2 + 4 + 9) / 3
    assert median == 4.0, median
    assert skipped == 0, skipped


def test_distance_stats_skips_findings_with_no_known_distance():
    findings = [
        {'candidates': [('rowA', 6.0)]},
        {'candidates': [('rowB', None), ('rowC', None)]},
    ]
    average, median, skipped = distance_stats(findings)
    assert average == 6.0, average
    assert median == 6.0, median
    assert skipped == 1, skipped


def test_distance_stats_all_unknown_does_not_crash():
    findings = [{'candidates': [('rowA', None)]}, {'candidates': [('rowB', None)]}]
    average, median, skipped = distance_stats(findings)
    assert average is None
    assert median is None
    assert skipped == 2


def test_report_shows_utilization_distance_stats_and_both_categories():
    rows = [
        # Wholly unused multi-session day.
        make_row("Jane Doe", "02/14", "AM", "Keller", "T56"),
        make_row("Jane Doe", "02/14", "PM", "Arlington", "T57"),
        # Partially used multi-session day.
        make_row("John Roe", "02/21", "AM", "Dallas", "T55"),
        make_row("John Roe", "02/21", "PM", "Arlington", "T57", pairing="P1"),
    ]
    table_styles = {"T55": {"01A"}, "T56": {"05A"}, "T57": {"06A"}}
    distances = {"Jane Doe": {"Keller": 10.0, "Arlington": 20.0}, "John Roe": {"Dallas": 6.0}}
    grouped = group_by_judge_and_date(rows)
    idle_findings, explained, unexplained = analyze_gaps(grouped, table_styles, distances)
    confirmed = count_confirmed_judge_sessions(rows)
    report = format_report(idle_findings, explained, unexplained, [], confirmed)
    assert "Season-wide utilization" in report, report
    assert "Wholly unused" in report, report
    assert "Partially used" in report, report
    assert "median" in report, report


def test_double_booking_detection():
    rows = [
        make_row("Brian Street", "02/21", "AM", "Arlington", "T83", pairing="P1"),
        make_row("Brian Street", "02/21", "AM", "Grapevine", "T82", pairing="P2"),
    ]
    grouped = group_by_judge_and_date(rows)
    findings = find_double_bookings(grouped)
    assert len(findings) == 1
    assert findings[0]['judge'] == "Brian Street"
    assert findings[0]['sites'] == ["Arlington", "Grapevine"]


def test_no_double_booking_when_single_site():
    rows = [
        make_row("Jane Doe", "02/14", "AM", "Keller", "T56", pairing="P1"),
    ]
    grouped = group_by_judge_and_date(rows)
    assert find_double_bookings(grouped) == []


if __name__ == '__main__':
    tests = [obj for name, obj in list(globals().items()) if name.startswith('test_')]
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
    print(f"\n{len(tests)} tests passed")
