"""Smoke tests for analyze_judge_utilization.py. Run: python3 test_analyze_judge_utilization.py"""

from analyze_judge_utilization import analyze_gaps, find_double_bookings, group_by_judge_and_date


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
