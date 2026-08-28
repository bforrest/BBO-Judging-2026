#!/usr/bin/env python3
"""
Diagnose 2026 judge utilization: find sessions where a judge had declared
availability but no confirmed assignment, and classify each gap as
explained by a substyle conflict or as unexplained idle capacity.

See docs/superpowers/specs/2026-08-27-judge-utilization-and-schedule-optimization-design.md
"""

import statistics
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
      {judge, date, session, category, candidates: [(row, distance_or_None), ...]}
    `candidates` is sorted by distance ascending (unknown distance sorts
    last), and the findings list itself is ranked by each finding's best
    (closest) candidate distance, so the most actionable missed
    opportunities read first.

    `category` distinguishes two kinds of idle capacity, which imply
    different remedies:
      'wholly_unused'  - the judge had NO confirmed session at all that
                         date, despite being available for more than one.
                         The judge simply wasn't used that day.
      'partially_used' - the judge was confirmed for some other session
                         that date, so this specific session was blocked.
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
                        'category': ('partially_used' if confirmed_sessions
                                     else 'wholly_unused'),
                        'candidates': annotated,
                    })
                else:
                    explained_count += 1
    idle_findings.sort(key=_rank_key)
    return idle_findings, explained_count, unexplained_count


def best_candidate_distance(finding):
    """Distance to this finding's closest missed opportunity, or None.

    `candidates` is already sorted closest-first with unknown distances
    last, so the first entry's distance is the best known one (None only
    when no candidate has a recorded distance).
    """
    if not finding['candidates']:
        return None
    return finding['candidates'][0][1]


def _rank_key(finding):
    distance = best_candidate_distance(finding)
    return (distance is None, distance if distance is not None else 0.0,
            finding['judge'], finding['date'], finding['session'] or '')


def count_confirmed_judge_sessions(rows):
    """Count unique (judge, date, session) triples with a confirmed pairing.

    Counted across the WHOLE dataset — every date, including single-session
    days — not just the multi-session days the gap analysis looks at. A
    judge confirmed at two sites in the same session still counts once.
    """
    confirmed = set()
    for row in rows:
        if row['slot'] is None:
            continue
        name = row['FULL NAME'].strip()
        if not name:
            continue
        if not row['PAIRING'].strip():
            continue
        date, session = row['slot'][0], row['slot'][1]
        confirmed.add((name, date, session))
    return len(confirmed)


def utilization_pct(confirmed_count, unexplained_count):
    """Season-wide utilization, per the spec's formula:

        confirmed judge-sessions / (confirmed + unexplained-idle judge-sessions)

    Returned as a percentage, or None when there is nothing to divide.
    """
    total = confirmed_count + unexplained_count
    if not total:
        return None
    return 100 * confirmed_count / total


def distance_stats(idle_findings):
    """Average/median distance to the closest missed opportunity.

    One distance per finding — its best (closest) candidate. Findings
    whose every candidate distance is unknown are skipped and counted.

    Returns (average, median, skipped_count); average and median are None
    when no finding had a known distance.
    """
    distances = []
    skipped = 0
    for finding in idle_findings:
        distance = best_candidate_distance(finding)
        if distance is None:
            skipped += 1
        else:
            distances.append(distance)
    if not distances:
        return None, None, skipped
    return statistics.mean(distances), statistics.median(distances), skipped


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


CATEGORY_LABELS = [
    ('wholly_unused',
     "Wholly unused days (judge had NO confirmed session that date)"),
    ('partially_used',
     "Partially used days (judge was confirmed in another session that date)"),
]


def format_report(idle_findings, explained_count, unexplained_count, double_bookings,
                  confirmed_count):
    lines = []
    lines.append("Judge Utilization Analysis (2026 retrospective)")
    lines.append("=" * 50)

    util = utilization_pct(confirmed_count, unexplained_count)
    if util is None:
        lines.append("Season-wide utilization: n/a (no confirmed or idle judge-sessions)")
    else:
        lines.append(f"Season-wide utilization: {util:.0f}% "
                      f"({confirmed_count} confirmed judge-sessions / "
                      f"{confirmed_count + unexplained_count} confirmed + unexplained-idle)")

    total_gaps = explained_count + unexplained_count
    if total_gaps:
        pct = 100 * explained_count / total_gaps
        lines.append(f"Session gaps on multi-session days: {total_gaps} total, "
                      f"{explained_count} explained by conflict ({pct:.0f}%), "
                      f"{unexplained_count} unexplained idle capacity")
    else:
        lines.append("No multi-session-day gaps found.")

    average, median, skipped = distance_stats(idle_findings)
    if average is None:
        lines.append("Distance to closest missed opportunity: no findings with a known "
                      f"distance ({skipped} findings had none)")
    else:
        counted = len(idle_findings) - skipped
        line = (f"Distance to closest missed opportunity: average {average:.1f}mi, "
                f"median {median:.1f}mi (across {counted} findings)")
        if skipped:
            line += f"; {skipped} findings skipped - no known distance"
        lines.append(line)
    lines.append("")

    if idle_findings:
        by_category = defaultdict(list)
        for finding in idle_findings:
            by_category[finding['category']].append(finding)
        counts = ", ".join(
            f"{len(by_category[key])} {key.replace('_', ' ')}" for key, _ in CATEGORY_LABELS
        )
        lines.append(f"Unexplained idle capacity ({len(idle_findings)} findings: {counts}),")
        lines.append("ranked by distance to the closest missed opportunity:")
        for key, label in CATEGORY_LABELS:
            findings = by_category[key]
            lines.append("")
            lines.append(f"  {label} - {len(findings)} findings:")
            if not findings:
                lines.append("    (none)")
                continue
            for finding in findings:
                session = finding['session'] or "(single session)"
                lines.append(f"    {finding['judge']} - {finding['date']} {session}:")
                for row, distance in finding['candidates']:
                    dist_str = f"{distance:.0f}mi" if distance is not None else "distance unknown"
                    site = row['slot'][2]
                    table = row['slot'][3]
                    lines.append(f"      could have judged {table} at {site} ({dist_str})")
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
    confirmed_count = count_confirmed_judge_sessions(rows)

    print(format_report(idle_findings, explained_count, unexplained_count, double_bookings,
                        confirmed_count))


if __name__ == '__main__':
    main()
