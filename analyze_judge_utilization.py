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
