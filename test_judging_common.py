"""Smoke tests for judging_common.py. Run directly: python3 test_judging_common.py"""

import os
import tempfile

from judging_common import (
    is_certified_or_higher,
    load_assignments,
    load_entry_counts,
    load_judge_distances,
    load_styles_by_table,
    parse_slot,
    parse_substyles,
)


def test_parse_slot_with_session():
    result = parse_slot("02/07 AM Dallas T55 Kolsch and Blonde")
    assert result == ("02/07", "AM", "Dallas", "T55", "Kolsch and Blonde"), result


def test_parse_slot_without_session():
    result = parse_slot("02/06 Arlington T68 American Pale Ale")
    assert result == ("02/06", None, "Arlington", "T68", "American Pale Ale"), result


def test_parse_slot_invalid_returns_none():
    assert parse_slot("not a valid slot") is None


def test_is_certified_or_higher():
    assert is_certified_or_higher("Level 3: Certified") is True
    assert is_certified_or_higher("Level 4: National") is True
    assert is_certified_or_higher("Non-BJCP, Judge with Sensory Training") is False
    assert is_certified_or_higher("Level 1: Rank Pending") is False


def test_parse_substyles():
    assert parse_substyles("1B, 2B, C2E") == {"1B", "2B", "C2E"}
    assert parse_substyles("") == set()


def test_load_assignments():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        f.write("FULL NAME,DESIRED TABLE TO JUDGE,PAIRING,BJCP ID,RANKING,SUBSTYLES ENTERED\n")
        f.write("Jane Doe,02/07 AM Dallas T55 Kolsch and Blonde,P1,123,Level 3: Certified,18B\n")
        path = f.name
    try:
        rows = load_assignments(path)
        assert len(rows) == 1
        assert rows[0]['slot'] == ("02/07", "AM", "Dallas", "T55", "Kolsch and Blonde")
        assert rows[0]['FULL NAME'] == "Jane Doe"
    finally:
        os.unlink(path)


def test_load_styles_by_table():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        f.write("Medal Category Name,Table Number,BJCP Style Name,BJCP Style Id,JUDGE FRESH\n")
        f.write("Pale Lager,50,American Light Lager,01A,X\n")
        f.write("Pale Lager,50,American Lager,01B,X\n")
        path = f.name
    try:
        table_styles, table_names = load_styles_by_table(path)
        assert table_styles["T50"] == {"01A", "01B"}
        assert table_names["T50"] == "Pale Lager"
    finally:
        os.unlink(path)


def test_load_entry_counts():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        f.write("Table Number,Table Name,Count\n")
        f.write("50,Pale Lager,36\n")
        path = f.name
    try:
        counts = load_entry_counts(path)
        assert counts["T50"] == 36
    finally:
        os.unlink(path)


def test_load_judge_distances():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        f.write("First Name,Last Name,DALLAS SITE,GRAPEVINE SITE,ARLINGTON SITE,STUBBIES SITE,KELLER SITE\n")
        f.write("Harry,Anderson,4,16,28,30,25\n")
        path = f.name
    try:
        distances = load_judge_distances(path)
        assert distances["Harry Anderson"] == {
            "Dallas": 4.0, "Grapevine": 16.0, "Arlington": 28.0,
            "Stubbies": 30.0, "Keller": 25.0,
        }
    finally:
        os.unlink(path)


def test_load_judge_distances_missing_file():
    assert load_judge_distances("/nonexistent/path.csv") == {}


def test_load_assignments_missing_file():
    assert load_assignments("/nonexistent/path.csv") == []


def test_load_styles_by_table_missing_file():
    table_styles, table_names = load_styles_by_table("/nonexistent/path.csv")
    assert table_styles == {}
    assert table_names == {}


def test_load_entry_counts_missing_file():
    assert load_entry_counts("/nonexistent/path.csv") == {}


def test_load_styles_by_table_skips_blank_rows():
    """Regression test: blank rows (empty Table Number) should be skipped.

    Previously, blank rows would create a phantom "T" key with an empty style set.
    This test ensures that blank rows are completely skipped and don't create
    any spurious entries.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        f.write("Medal Category Name,Table Number,BJCP Style Name,BJCP Style Id,JUDGE FRESH\n")
        f.write("Pale Lager,50,American Light Lager,01A,X\n")
        f.write(",,,,\n")  # blank row
        f.write("IPA,51,American IPA,14B,X\n")
        f.write(",,,,\n")  # another blank row
        path = f.name
    try:
        table_styles, table_names = load_styles_by_table(path)
        # Should have exactly 2 tables, not 3 or 4
        assert len(table_styles) == 2, f"Expected 2 tables, got {len(table_styles)}: {table_styles.keys()}"
        assert len(table_names) == 2, f"Expected 2 tables, got {len(table_names)}: {table_names.keys()}"
        # Should have the real tables
        assert "T50" in table_styles
        assert "T51" in table_styles
        # Should NOT have a phantom "T" key
        assert "T" not in table_styles, "Phantom 'T' key should not exist"
        assert "T" not in table_names, "Phantom 'T' key should not exist in table_names"
    finally:
        os.unlink(path)


if __name__ == '__main__':
    tests = [obj for name, obj in list(globals().items()) if name.startswith('test_')]
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
    print(f"\n{len(tests)} tests passed")
