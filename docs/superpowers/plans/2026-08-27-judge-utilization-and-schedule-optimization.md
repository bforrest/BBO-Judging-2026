# Judge Utilization Analysis & Schedule Reallocation Proposal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build two retrospective analysis scripts for the BBO judging dataset — one diagnosing where 2026 judge availability went unused, one proposing a 2027 schedule built around judge availability and travel distance instead of site-host preference — sharing a small common data-loading module.

**Architecture:** A new `judging_common.py` module holds CSV loaders and slot-parsing shared by both scripts. `analyze_judge_utilization.py` is a pure diagnostic (no scheduling) over the historical data. `propose_minimal_schedule.py` is a greedy bin-packer that treats table-to-site assignment as fully flexible and packs tables into the fewest `(date, session)` slots judges' declared availability can support.

**Tech Stack:** Plain Python 3 standard library only (`csv`, `math`, `collections`, `os`, `re`) — no new dependencies. Tests are plain `assert`-based scripts run directly with `python3`, matching this repo's existing `test_load.py` convention (no pytest).

**Spec:** `docs/superpowers/specs/2026-08-27-judge-utilization-and-schedule-optimization-design.md`

## Global Constraints

- No new third-party dependencies — stdlib only.
- `PAIRING` non-empty is the sole signal for "this was a real, confirmed assignment"; empty `PAIRING` means unused candidate availability.
- Table identifiers are normalized to the `T{digits}` form (e.g. `"T55"`) everywhere, matching the convention already used in `generate_optimized_schedule.py`.
- `load_judge_distances` reads from `~/judge-data-private/JUDGE WORKSHEET 2026.csv` by default (the documented external, gitignored location), not the working directory.
- All loaders fail open on missing data (missing file → empty result; judge missing from distance data → treated as feasible everywhere) rather than raising or silently dropping the judge from other computations.
- `TARGET_BEERS_PER_PAIR = 9` and `MAX_DISTANCE_MILES = 20` are named constants at the top of `propose_minimal_schedule.py`, easy to tune for "what if" runs.
- No changes to any existing file in this repo — these are new, additive files only.

---

## Task 1: `judging_common.py` — shared parsers and loaders

**Files:**
- Create: `judging_common.py`
- Test: `test_judging_common.py`

**Interfaces:**
- Produces:
  - `RANKS: dict[str, int]` — rank string → numeric level (0-4)
  - `is_certified_or_higher(rank: str) -> bool`
  - `parse_slot(desired_table_str: str) -> tuple[str, str|None, str, str, str] | None` — `(date, session, site, table, description)`, `session` is `"AM"`, `"PM"`, or `None`, `table` keeps its `T` prefix
  - `parse_substyles(substyles_str: str) -> set[str]`
  - `load_assignments(path: str) -> list[dict]` — each row dict plus a `'slot'` key holding `parse_slot(...)`'s result (or `None`)
  - `load_styles_by_table(path: str) -> tuple[dict[str, set[str]], dict[str, str]]` — `(table_styles, table_names)`
  - `load_entry_counts(path: str) -> dict[str, int]`
  - `DEFAULT_JUDGE_WORKSHEET_PATH: str`
  - `load_judge_distances(path: str = DEFAULT_JUDGE_WORKSHEET_PATH) -> dict[str, dict[str, float]]`

- [ ] **Step 1: Write the failing test file**

Create `test_judging_common.py`:

```python
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


if __name__ == '__main__':
    tests = [obj for name, obj in list(globals().items()) if name.startswith('test_')]
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
    print(f"\n{len(tests)} tests passed")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 test_judging_common.py`
Expected: `ModuleNotFoundError: No module named 'judging_common'`

- [ ] **Step 3: Write `judging_common.py`**

```python
"""Shared CSV loaders and slot parsing for BBO judging analysis scripts."""

import csv
import os
import re

SLOT_PATTERN = re.compile(r'^(\d{2}/\d{2})\s*(AM|PM)?\s*([A-Za-z]+)\s*(T\d+)\s*(.*)$')

RANKS = {
    'Level 0: Non-BJCP': 0,
    'Level 1: Rank Pending': 1,
    'Level 1: Provisional': 1,
    'Level 2: Recognized': 2,
    'Level 3: Certified': 3,
    'certified': 3,
    'CERTIFIED': 3,
    'Certified+ Mead': 3,
    'Certified+Mead': 3,
    'Certified+Mead+cider': 3,
    'Certified, Judge with Sensory Training': 3,
    'Certified, Professional Brewer': 3,
    'national': 4,
    'Level 4: National': 4,
}

DEFAULT_JUDGE_WORKSHEET_PATH = os.path.expanduser(
    "~/judge-data-private/JUDGE WORKSHEET 2026.csv"
)


def is_certified_or_higher(rank):
    """Check if a rank is Certified (Level 3) or higher."""
    return RANKS.get(rank, 0) >= 3


def parse_slot(desired_table_str):
    """Parse a 'DESIRED TABLE TO JUDGE' string into its components.

    Returns (date, session, site, table, description) or None if it
    doesn't match the expected format. `session` is 'AM', 'PM', or None.
    `table` keeps its 'T' prefix (e.g. 'T55') to match styles/entry-count keys.
    """
    match = SLOT_PATTERN.match(desired_table_str.strip())
    if not match:
        return None
    date, session, site, table, description = match.groups()
    return (date, session, site, table, description.strip())


def parse_substyles(substyles_str):
    """Parse a comma-separated 'SUBSTYLES ENTERED' string into a set of ids."""
    if not substyles_str:
        return set()
    return {s.strip() for s in substyles_str.split(',') if s.strip()}


def load_assignments(path):
    """Load Judges_and_Tables_generated.csv, with each row's slot parsed.

    Returns a list of dicts, each the original row plus a 'slot' key holding
    the parse_slot(...) tuple (or None if unparseable).
    """
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row = dict(row)
            row['slot'] = parse_slot(row.get('DESIRED TABLE TO JUDGE', ''))
            rows.append(row)
    return rows


def load_styles_by_table(path):
    """Load styles by table.csv.

    Returns (table_styles, table_names):
      table_styles: dict table ('T55') -> set of BJCP style ids
      table_names: dict table ('T55') -> Medal Category Name
    """
    table_styles = {}
    table_names = {}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            table = f"T{row['Table Number'].strip()}"
            table_styles.setdefault(table, set()).add(row['BJCP Style Id'].strip())
            table_names[table] = row['Medal Category Name'].strip()
    return table_styles, table_names


def load_entry_counts(path):
    """Load medal_category_counts.csv.

    Returns dict table ('T55') -> entry count (int).
    """
    counts = {}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            table = f"T{row['Table Number'].strip()}"
            try:
                counts[table] = int(row['Count'].strip())
            except (ValueError, KeyError):
                continue
    return counts


def load_judge_distances(path=DEFAULT_JUDGE_WORKSHEET_PATH):
    """Load per-judge, per-site distances from the private judge worksheet.

    Returns dict full_name -> dict site_name (e.g. 'Dallas') -> distance (float).
    Returns an empty dict if the file doesn't exist (fail open — callers
    should treat a judge missing from this dict as feasible everywhere).
    """
    distances = {}
    if not os.path.exists(path):
        return distances
    site_columns = {
        'Dallas': 'DALLAS SITE',
        'Grapevine': 'GRAPEVINE SITE',
        'Arlington': 'ARLINGTON SITE',
        'Stubbies': 'STUBBIES SITE',
        'Keller': 'KELLER SITE',
    }
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            first = row.get('First Name', '').strip()
            last = row.get('Last Name', '').strip()
            if not first or not last:
                continue
            full_name = f"{first} {last}"
            site_distances = {}
            for site, column in site_columns.items():
                value = (row.get(column) or '').strip()
                if value:
                    try:
                        site_distances[site] = float(value)
                    except ValueError:
                        continue
            distances[full_name] = site_distances
    return distances
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 test_judging_common.py`
Expected: all tests print `PASS:` and the run ends with `10 tests passed`

- [ ] **Step 5: Commit**

```bash
git add judging_common.py test_judging_common.py
git commit -m "Add shared CSV loaders and slot parser for judging analysis scripts"
```

---

## Task 2: `analyze_judge_utilization.py` — retrospective diagnostic

**Files:**
- Create: `analyze_judge_utilization.py`
- Test: `test_analyze_judge_utilization.py`

**Interfaces:**
- Consumes: `judging_common.load_assignments`, `load_styles_by_table`, `load_judge_distances`, `parse_substyles`
- Produces:
  - `group_by_judge_and_date(rows: list[dict]) -> dict[str, dict[str, list[dict]]]`
  - `analyze_gaps(grouped, table_styles: dict[str, set[str]], distances: dict[str, dict[str, float]]) -> tuple[list[dict], int, int]` — `(idle_findings, explained_count, unexplained_count)`. Each idle finding: `{'judge': str, 'date': str, 'session': str, 'candidates': list[tuple[dict, float|None]]}`, candidates sorted by distance ascending (unknown last).
  - `find_double_bookings(grouped) -> list[dict]` — each: `{'judge': str, 'date': str, 'session': str, 'sites': list[str]}`
  - `format_report(idle_findings, explained_count, unexplained_count, double_bookings) -> str`
  - `main() -> None`

- [ ] **Step 1: Write the failing test file**

Create `test_analyze_judge_utilization.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 test_analyze_judge_utilization.py`
Expected: `ModuleNotFoundError: No module named 'analyze_judge_utilization'`

- [ ] **Step 3: Write `analyze_judge_utilization.py`**

```python
#!/usr/bin/env python3
"""
Diagnose 2026 judge utilization: find sessions where a judge had declared
availability but no confirmed assignment, and classify each gap as
explained by a substyle conflict or as unexplained idle capacity.

See docs/superpowers/specs/2026-08-27-judge-utilization-and-schedule-optimization-design.md
"""

from collections import defaultdict

from judging_common import (
    load_assignments,
    load_judge_distances,
    load_styles_by_table,
    parse_substyles,
)


def group_by_judge_and_date(rows):
    """Group parsed rows by judge name, then by date.

    Returns dict judge_name -> dict date -> list of rows. Rows with no
    parsed slot or no judge name are skipped.
    """
    grouped = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if row['slot'] is None:
            continue
        name = row['FULL NAME'].strip()
        if not name:
            continue
        date = row['slot'][0]
        grouped[name][date].append(row)
    return grouped


def analyze_gaps(grouped, table_styles, distances):
    """For each judge/date with more than one session, examine every gap
    session (present but not confirmed) and classify it.

    Returns (idle_findings, explained_count, unexplained_count).
    idle_findings is a list of dicts:
      {judge, date, session, candidates: [(row, distance_or_None), ...]}
    sorted by distance ascending (unknown distance sorts last).
    """
    idle_findings = []
    explained_count = 0
    unexplained_count = 0
    for judge, by_date in grouped.items():
        for date, rows in by_date.items():
            substyles = parse_substyles(rows[0].get('SUBSTYLES ENTERED', ''))
            sessions_present = {r['slot'][1] for r in rows}
            if len(sessions_present) <= 1:
                continue
            confirmed_sessions = {r['slot'][1] for r in rows if r['PAIRING'].strip()}
            for session in sessions_present - confirmed_sessions:
                candidate_rows = [r for r in rows if r['slot'][1] == session]
                non_conflicting = [
                    r for r in candidate_rows
                    if not (table_styles.get(r['slot'][3], set()) & substyles)
                ]
                if non_conflicting:
                    unexplained_count += 1
                    judge_distances = distances.get(judge, {})
                    annotated = sorted(
                        ((r, judge_distances.get(r['slot'][2])) for r in non_conflicting),
                        key=lambda pair: (pair[1] is None, pair[1])
                    )
                    idle_findings.append({
                        'judge': judge, 'date': date, 'session': session,
                        'candidates': annotated,
                    })
                else:
                    explained_count += 1
    return idle_findings, explained_count, unexplained_count


def find_double_bookings(grouped):
    """Find (judge, date, session) with confirmed rows at more than one site.

    Returns a list of {judge, date, session, sites: [...]} dicts.
    """
    findings = []
    for judge, by_date in grouped.items():
        for date, rows in by_date.items():
            confirmed = [r for r in rows if r['PAIRING'].strip()]
            by_session = defaultdict(set)
            for r in confirmed:
                by_session[r['slot'][1]].add(r['slot'][2])
            for session, site_set in by_session.items():
                if len(site_set) > 1:
                    findings.append({'judge': judge, 'date': date, 'session': session,
                                      'sites': sorted(site_set)})
    return findings


def format_report(idle_findings, explained_count, unexplained_count, double_bookings):
    lines = []
    lines.append("Judge Utilization Analysis (2026 retrospective)")
    lines.append("=" * 50)
    total_gaps = explained_count + unexplained_count
    if total_gaps:
        pct = 100 * explained_count / total_gaps
        lines.append(f"Session gaps: {total_gaps} total, {explained_count} explained by "
                      f"conflict ({pct:.0f}%), {unexplained_count} unexplained idle capacity")
    else:
        lines.append("No multi-session-day gaps found.")
    lines.append("")

    if idle_findings:
        lines.append(f"Unexplained idle capacity ({len(idle_findings)} findings):")
        for finding in idle_findings:
            lines.append(f"  {finding['judge']} - {finding['date']} {finding['session']}:")
            for row, distance in finding['candidates']:
                dist_str = f"{distance:.0f}mi" if distance is not None else "distance unknown"
                site = row['slot'][2]
                table = row['slot'][3]
                lines.append(f"    could have judged {table} at {site} ({dist_str})")
    else:
        lines.append("No unexplained idle capacity found.")
    lines.append("")

    if double_bookings:
        lines.append(f"Double-booking anomalies ({len(double_bookings)} found):")
        for finding in double_bookings:
            sites = ", ".join(finding['sites'])
            lines.append(f"  {finding['judge']} - {finding['date']} {finding['session']}: "
                          f"confirmed at multiple sites ({sites})")
    else:
        lines.append("No double-booking anomalies found.")

    return "\n".join(lines)


def main():
    rows = load_assignments("Judges_and_Tables_generated.csv")
    table_styles, _ = load_styles_by_table("styles by table.csv")
    distances = load_judge_distances()

    grouped = group_by_judge_and_date(rows)
    idle_findings, explained_count, unexplained_count = analyze_gaps(grouped, table_styles, distances)
    double_bookings = find_double_bookings(grouped)

    print(format_report(idle_findings, explained_count, unexplained_count, double_bookings))


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 test_analyze_judge_utilization.py`
Expected: all tests print `PASS:` and the run ends with `5 tests passed`

- [ ] **Step 5: Commit**

```bash
git add analyze_judge_utilization.py test_analyze_judge_utilization.py
git commit -m "Add retrospective judge utilization diagnostic"
```

---

## Task 3: `propose_minimal_schedule.py` — table/judge modeling and pairing helpers

**Files:**
- Create: `propose_minimal_schedule.py` (this task writes the non-scheduler half; Task 4 adds `build_schedule`/`format_report`/`main` to the same file)
- Test: `test_propose_minimal_schedule.py` (this task writes the first half of the tests; Task 4 appends the rest)

**Interfaces:**
- Consumes: `judging_common.is_certified_or_higher`, `load_assignments`, `load_entry_counts`, `load_judge_distances`, `load_styles_by_table`, `parse_substyles`
- Produces:
  - `TARGET_BEERS_PER_PAIR: int = 9`
  - `MAX_DISTANCE_MILES: int = 20`
  - `build_tables(table_styles: dict[str, set[str]], table_names: dict[str, str], entry_counts: dict[str, int]) -> list[dict]` — each `{'table': str, 'name': str, 'styles': set[str], 'entry_count': int, 'required_pairs': int}`
  - `build_judge_profiles(rows: list[dict]) -> dict[str, dict]` — each `{'rank': str, 'substyles': set[str], 'availability': set[tuple[str, str|None]]}`
  - `judge_feasible_sites(judge_name: str, distances: dict, sites: list[str], max_distance: float = MAX_DISTANCE_MILES) -> set[str]`
  - `eligible_judges_for_table(table: dict, judge_profiles: dict, distances: dict, sites: list[str], max_distance: float = MAX_DISTANCE_MILES) -> list[str]`
  - `form_pairs(available_judges: list[str], required_pairs: int, judge_profiles: dict) -> list[tuple[str, str]] | None`
  - `pick_site(available_sites: list[str], pairs: list[tuple[str, str]], distances: dict) -> str`

- [ ] **Step 1: Write the failing test file**

Create `test_propose_minimal_schedule.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 test_propose_minimal_schedule.py`
Expected: `ModuleNotFoundError: No module named 'propose_minimal_schedule'`

- [ ] **Step 3: Write the first half of `propose_minimal_schedule.py`**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 test_propose_minimal_schedule.py`
Expected: all 10 tests print `PASS:` and the run ends with `10 tests passed`

- [ ] **Step 5: Commit**

```bash
git add propose_minimal_schedule.py test_propose_minimal_schedule.py
git commit -m "Add table/judge modeling and pairing helpers for schedule proposal"
```

---

## Task 4: `propose_minimal_schedule.py` — greedy scheduler, report, and main

**Files:**
- Modify: `propose_minimal_schedule.py` (append to the file from Task 3)
- Modify: `test_propose_minimal_schedule.py` (append to the file from Task 3)

**Interfaces:**
- Consumes: everything produced in Task 3, plus `judging_common.load_assignments`, `load_entry_counts`, `load_judge_distances`, `load_styles_by_table`
- Produces:
  - `build_schedule(tables: list[dict], judge_profiles: dict, distances: dict, sites: list[str], max_distance: float = MAX_DISTANCE_MILES) -> tuple[list[dict], list[tuple[str, str|None]]]` — `(schedule, slots)`. Each schedule entry: `{'table': str, 'name': str, 'slot': tuple|None, 'site': str|None, 'pairs': list[tuple[str,str]], 'unfilled_pairs_needed': int|None}`.
  - `format_report(schedule: list[dict], slots: list, sites: list[str], actual_dates: int = 10, actual_slots: int = 14) -> str`
  - `main() -> None`

- [ ] **Step 1: Append the failing tests**

Insert into `test_propose_minimal_schedule.py`, directly above the existing `if __name__ == '__main__':` block at the bottom of the file (so that block stays last):

```python
from propose_minimal_schedule import build_schedule


def test_build_schedule_places_all_tables():
    tables = [
        {'table': 'T1', 'name': 'A', 'styles': set(), 'entry_count': 9, 'required_pairs': 1},
        {'table': 'T2', 'name': 'B', 'styles': set(), 'entry_count': 9, 'required_pairs': 1},
    ]
    profiles = {
        'Judge1': {'rank': 'Level 3: Certified', 'substyles': set(), 'availability': {('02/07', 'AM')}},
        'Judge2': {'rank': 'Non-BJCP', 'substyles': set(), 'availability': {('02/07', 'AM')}},
        'Judge3': {'rank': 'Level 3: Certified', 'substyles': set(), 'availability': {('02/07', 'AM')}},
        'Judge4': {'rank': 'Non-BJCP', 'substyles': set(), 'availability': {('02/07', 'AM')}},
    }
    schedule, slots = build_schedule(tables, profiles, {}, ['Dallas', 'Keller'])
    assert len(schedule) == 2
    assert slots == [('02/07', 'AM')]
    assert all(e['site'] is not None for e in schedule)


def test_build_schedule_consolidates_into_second_session_same_date():
    # Three tables, but only enough judges for two pairs total, split across
    # AM and PM availability on the *same* date. Expect both sessions used
    # on that one date rather than a table left unfilled or a new date opened
    # unnecessarily.
    tables = [
        {'table': 'T1', 'name': 'A', 'styles': set(), 'entry_count': 9, 'required_pairs': 1},
        {'table': 'T2', 'name': 'B', 'styles': set(), 'entry_count': 9, 'required_pairs': 1},
    ]
    profiles = {
        'Judge1': {'rank': 'Level 3: Certified', 'substyles': set(), 'availability': {('02/07', 'AM')}},
        'Judge2': {'rank': 'Non-BJCP', 'substyles': set(), 'availability': {('02/07', 'AM')}},
        'Judge3': {'rank': 'Level 3: Certified', 'substyles': set(), 'availability': {('02/07', 'PM')}},
        'Judge4': {'rank': 'Non-BJCP', 'substyles': set(), 'availability': {('02/07', 'PM')}},
    }
    schedule, slots = build_schedule(tables, profiles, {}, ['Dallas'])
    assert sorted(slots) == [('02/07', 'AM'), ('02/07', 'PM')]
    assert all(e['site'] is not None for e in schedule)


def test_build_schedule_leaves_table_unfilled_when_no_slot_covers_it():
    tables = [
        {'table': 'T1', 'name': 'A', 'styles': set(), 'entry_count': 9, 'required_pairs': 1},
        {'table': 'T2', 'name': 'B', 'styles': set(), 'entry_count': 9, 'required_pairs': 1},
    ]
    # Only one certified/non-certified pair exists, and they're only ever
    # available for a single (date, session) - not enough capacity to cover
    # both tables, and no other availability exists to open a new slot into.
    profiles = {
        'Judge1': {'rank': 'Level 3: Certified', 'substyles': set(), 'availability': {('02/07', 'AM')}},
        'Judge2': {'rank': 'Non-BJCP', 'substyles': set(), 'availability': {('02/07', 'AM')}},
    }
    schedule, slots = build_schedule(tables, profiles, {}, ['Dallas'])
    filled = [e for e in schedule if e['site'] is not None]
    unfilled = [e for e in schedule if e['site'] is None]
    assert len(filled) == 1
    assert len(unfilled) == 1
    assert unfilled[0]['unfilled_pairs_needed'] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 test_propose_minimal_schedule.py`
Expected: `ImportError: cannot import name 'build_schedule' from 'propose_minimal_schedule'`

- [ ] **Step 3: Append the scheduler, report, and main to `propose_minimal_schedule.py`**

```python
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

    def open_new_slot():
        # Prefer completing a date that already has one session open.
        for date in available_dates:
            sessions_open = {s for d, s in slots if d == date}
            remaining = sessions_by_date[date] - sessions_open
            if sessions_open and remaining:
                next_session = sorted(remaining, key=session_sort_key)[0]
                slot = (date, next_session)
                slots.append(slot)
                return slot
        # Otherwise open the earliest not-yet-used (date, session).
        for date in available_dates:
            for session in sorted(sessions_by_date[date], key=session_sort_key):
                slot = (date, session)
                if slot not in slots:
                    slots.append(slot)
                    return slot
        return None

    def try_fit(table, slot, elig):
        available_sites = [s for s in sites if s not in slot_sites_used[slot]]
        if not available_sites:
            return None
        used_judges = slot_judges_used[slot]
        candidates = [
            j for j in elig
            if j not in used_judges and slot in judge_profiles[j]['availability']
            and judge_feasible_sites(j, distances, available_sites, max_distance)
        ]
        pairs = form_pairs(candidates, table['required_pairs'], judge_profiles)
        if pairs is None:
            return None
        common_sites = set(available_sites)
        for judge in (j for pair in pairs for j in pair):
            common_sites &= judge_feasible_sites(judge, distances, available_sites, max_distance)
        if not common_sites:
            return None
        site = pick_site(sorted(common_sites), pairs, distances)
        return site, pairs

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

        new_slot = open_new_slot()
        if new_slot is None:
            schedule.append({'table': table['table'], 'name': table['name'],
                              'slot': None, 'site': None, 'pairs': [],
                              'unfilled_pairs_needed': table['required_pairs']})
            continue

        fit = try_fit(table, new_slot, elig)
        if fit is None:
            schedule.append({'table': table['table'], 'name': table['name'],
                              'slot': new_slot, 'site': None, 'pairs': [],
                              'unfilled_pairs_needed': table['required_pairs']})
            continue
        site, pairs = fit
        schedule.append({'table': table['table'], 'name': table['name'],
                          'slot': new_slot, 'site': site, 'pairs': pairs,
                          'unfilled_pairs_needed': None})
        slot_sites_used[new_slot].add(site)
        for pair in pairs:
            slot_judges_used[new_slot].update(pair)

    return schedule, slots


def format_report(schedule, slots, sites, actual_dates=10, actual_slots=14):
    days_used = sorted({day for day, _ in slots})
    lines = []
    lines.append("BBO Judging Schedule Proposal")
    lines.append("=" * 40)
    lines.append(f"Proposed: {len(days_used)} days, {len(slots)} sessions, for {len(schedule)} tables")
    lines.append(f"2026 actual: {actual_dates} days, {actual_slots} sessions")
    theoretical_floor = math.ceil(len(schedule) / len(sites)) if sites else len(schedule)
    lines.append(f"Theoretical floor ({len(sites)} sites, full parallelism): {theoretical_floor} sessions")
    lines.append("")

    unfilled = [e for e in schedule if e['site'] is None]
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
```

Note: this appends *after* the functions from Task 3 and *before* the `if __name__ == '__main__':` test-runner block already present at the bottom of `test_propose_minimal_schedule.py` — make sure that block still sits last in the test file.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 test_propose_minimal_schedule.py`
Expected: all 13 tests print `PASS:` and the run ends with `13 tests passed`

- [ ] **Step 5: Commit**

```bash
git add propose_minimal_schedule.py test_propose_minimal_schedule.py
git commit -m "Add greedy scheduler and report for schedule proposal"
```

---

## Task 5: Validate both scripts against the real repo data

**Files:** none created or modified — this task runs the two finished scripts against the actual tracked CSVs and checks the output against facts already confirmed during design (see the spec's Background section).

**Interfaces:** none — this is a manual validation pass, not new code.

- [ ] **Step 1: Run the utilization diagnostic against real data**

Run: `python3 analyze_judge_utilization.py`

Confirm in the printed output:
- Brian Street's 02/28 AM gap is **not** listed under "Unexplained idle capacity" (it must be counted in the `explained by conflict` total instead) — all four of his 02/28 AM candidate tables (Arlington T62, Dallas T88, Grapevine T93, Keller T66) genuinely conflict with his entered substyles (`11C`, `34C`, `C2B`/`C2E`, `16A`/`16B` respectively).
- The "Double-booking anomalies" section lists Brian Street, `02/21 AM`, confirmed at both Arlington and Grapevine.

If either check fails, the bug is in `analyze_gaps` or `find_double_bookings` — do not adjust the expected facts to match broken output; re-check the logic against Task 2's test cases first.

- [ ] **Step 2: Run the schedule proposal against real data**

Run: `python3 propose_minimal_schedule.py`

Confirm in the printed output:
- Every one of the tables from `styles by table.csv` appears exactly once across the "UNFILLED" section and the day-by-day listing combined (no table missing, none duplicated).
- The reported number of `(date, session)` slots is between 11 (theoretical floor: `ceil(44 / 4)`) and 14 (2026's actual slot count) — a result outside that range means either the floor math or the greedy packer has a bug worth investigating before trusting the proposal.

- [ ] **Step 3: Note limitations in a short findings summary**

No file changes — this is a verbal check-in with the user (not a file) covering: how many tables ended up unfilled (if any) and why (likely distance or availability sparsity), how the proposed day count compares to the 14-slot/10-day actual baseline, and a reminder that `MAX_DISTANCE_MILES` and `TARGET_BEERS_PER_PAIR` are easy to re-run with different values for "what if" comparisons.

- [ ] **Step 4: Commit if any documentation note is added**

Only if Step 3 surfaces something worth recording in the spec's Limitations section (e.g. a concrete count of unfilled tables in the real run) — otherwise skip this step, there is nothing to commit.
