# CP-SAT Schedule Solver

## Background

`propose_minimal_schedule.py` (see
`docs/superpowers/specs/2026-08-27-judge-utilization-and-schedule-optimization-design.md`)
proposes a 2027 judging schedule using a greedy, non-backtracking
heuristic. After the site-aware pairing fix, it places 35 of 44 real
tables — the remaining 9 are unplaced not because they're provably
unstaffable, but because the greedy pass commits earlier tables' judges
to slots and never revisits that choice. There's no way to tell, from
the output alone, whether a different processing order would have done
better, and reasoning about "what if I moved this table to a different
site" means hand-tracing the greedy algorithm's control flow (as we did
for table T76 in the prior design doc).

This is a second, independent script — not a modification of
`propose_minimal_schedule.py`, which stays exactly as it is — built
around a real constraint solver (OR-Tools' CP-SAT) instead of a hand-rolled
heuristic. The point isn't a fancier UI; it's replacing "trace the code
to understand a change" with "edit a config value and re-run," and
replacing "this heuristic left 9 tables unfilled" with "this is the
maximum number of tables that can be placed given current constraints,
proven, not just found."

## Goals

1. **Maximize the number of tables staffed**, as the primary objective —
   not minimize days. If full coverage (44/44) isn't achievable given
   the real availability/distance/host data, report the true maximum and
   exactly which tables are left out, with the guarantee that no
   different assignment could have placed more of them.
2. **Make "what if" exploration require no Python.** All organizer-facing
   tunables — beers-per-pair target, max travel distance, site anchors,
   site host requirements, and one-off table→site overrides — live in a
   single commented YAML config file. Changing a scenario means editing
   that file and re-running the script.
3. **Reuse the existing data model.** Same input CSVs, same
   `judging_common.py` loaders, same underlying business rules
   (certification pairing, site anchoring, host presence) as
   `propose_minimal_schedule.py` — just solved differently and configured
   differently.

## Relationship to `propose_minimal_schedule.py`

This is an **alternative**, not a replacement or upgrade path:

- `propose_minimal_schedule.py` is untouched by this work — no shared
  code beyond `judging_common.py`'s loaders. Its `SITE_ANCHORS`,
  `DALLAS_HOST_CANDIDATES`, and constants stay Python constants exactly
  as they are today.
- The new script, `solve_schedule_cpsat.py`, duplicates the two small,
  stable data-shaping functions it needs (`build_tables`-equivalent,
  `build_judge_profiles`-equivalent) rather than importing them from
  `propose_minimal_schedule.py` or extracting them into
  `judging_common.py`. Both are pure, ~15-line functions; the goal above
  ("don't touch the existing script") outweighs the minor duplication of
  code this stable.
- Both scripts can be run side by side and their outputs compared.
  Neither depends on the other.

## New dependencies

- **`ortools`** (Google's OR-Tools, Apache 2.0) — the CP-SAT constraint
  solver. `pip3 install ortools`.
- **`pyyaml`** — parses the config file. `pip3 install pyyaml`.

This breaks the project's stdlib-only convention that every other script
here has followed. That's a deliberate, accepted tradeoff for this one
script — it's exactly the "true optimal solver" item the original design
doc's "Out of scope" section flagged as worth revisiting if the greedy
heuristic's gap ever mattered in practice. It now does.

## Config file: `schedule_config.yaml`

A new file at the repo root, human-edited, no Python required:

```yaml
# BBO Judging Schedule Solver Configuration
# Edit this file and re-run solve_schedule_cpsat.py to try a different
# scenario -- no code changes needed.

# Target number of beers each judging pair evaluates. BJCP guideline caps
# at 12 per pair; lower means more pairs required per table.
target_beers_per_pair: 9

# How far (in miles) a judge can reasonably be asked to drive to a site.
max_distance_miles: 20

# Site hosts: each of these judges is anchored to one site (it's their
# home or workplace) and should never be scheduled anywhere else.
site_anchors:
  - judge: "Amanda Long"
    site: "Arlington"
  - judge: "Jarrett Long"
    site: "Arlington"
  - judge: "Reni Morriss"
    site: "Keller"
  - judge: "Matthew Morriss"
    site: "Keller"
  - judge: "Mark McCurdy"
    site: "Grapevine"

# Some sites need at least one of a named group of judges present to run
# at all, even though those judges don't personally judge there. List
# every site that needs this; a site not listed here has no such
# requirement.
site_host_requirements:
  Dallas:
    - "Terry Olinger"
    - "Mike Grover"

# One-off "what if" experiments: force a specific table to run at a
# specific site, to see how the rest of the schedule adjusts. Leave this
# list empty for a normal run.
table_site_overrides:
  - table: "T50"
    site: "Arlington"
    reason: "Testing whether moving Pale Lager here helps coverage"
```

`table_site_overrides` is a hard constraint (that table's site is fixed,
not merely preferred) and only supports forcing a site in v1 — forcing a
specific date/session, or excluding a site without naming a replacement,
are natural extensions but not built now (YAGNI; add them if the
one-scenario-at-a-time workflow above turns out not to be enough).

## CP-SAT model

**Candidate slots.** Same slot universe as `propose_minimal_schedule.py`:
every `(date, session)` pair appearing in any judge's declared
availability, crossed with every real site from the data — minus any
`(slot, site)` combination that fails a `site_host_requirements` check
(computed once, up front, in plain Python, the same way
`site_host_requirement_met` does today — this shrinks the model rather
than becoming a runtime constraint).

**Variables:**
- `table_slot[table][slot]` (boolean) — is `table` scheduled into this
  candidate slot? At most one true per table (a table runs at most once);
  it's valid for all of a table's `table_slot` variables to be false,
  which is how "this table didn't get placed" is represented — placement
  is optional, not mandatory, so the model is never simply "infeasible."
- `judge_table[judge][table]` (boolean) — is `judge` one of `table`'s
  assigned pair members? Only created for `(judge, table)` pairs with no
  substyle conflict, matching `eligible_judges_for_table` today.
- `judge_table_slot[judge][table][slot]` (boolean, auxiliary) — standard
  boolean-AND linearization of the two above (`judge_table_slot <=
  judge_table`, `<= table_slot`, `>= judge_table + table_slot - 1`), used
  to express "this judge is busy in this slot" without needing a judge to
  know in advance which slot their table landed in.

**Constraints**, each a direct translation of an existing business rule:
- **One slot per table**: `sum(table_slot[t][*]) <= 1` for each table `t`.
- **One table per (slot, site)**: at most one `table_slot[t][slot]` true
  across all tables sharing that exact `(date, session, site)`.
- **Required pairs**: if `table_slot[t][slot]` is true, the number of
  judges with `judge_table[j][t]` true must equal `2 * required_pairs`
  (a pair contributes two judges); if false, it must be zero. Expressed
  as a conditional (reified) linear constraint on the slot's indicator.
- **Certification pairing**: among the judges assigned to a placed table,
  no two below-certified judges may be "paired" — modeled as: the number
  of below-certified assigned judges may not exceed the number of
  certified-or-higher assigned judges, for each placed table. (This
  permits certified+certified and certified+non-certified pairs and
  forbids two non-certified together, matching `form_pairs`'s existing
  rule, without needing to decide which specific two judges are "a
  pair" — the count constraint is sufficient and simpler to model.)
- **Judge availability**: `judge_table[j][t]` can only be true for slots
  in `j`'s declared `(date, session)` availability — enforced by only
  creating `judge_table_slot` variables for available combinations.
- **Judge feasible sites**: `judge_table_slot[j][t][slot]` can only be
  true if `j` is feasible at that slot's site — site anchors, host
  exclusions (a host-requirement judge never personally judges at that
  site), and the distance cutoff all apply here, computed once per
  `(judge, site)` up front in plain Python exactly like
  `judge_feasible_sites` does today, just sourced from the YAML config
  instead of Python constants.
- **No judge double-booked in a slot**: `sum(judge_table_slot[j][*][slot])
  <= 1` for each judge `j` and slot `slot`, summed across every table
  that could occupy that slot.
- **Overrides**: for each `table_site_overrides` entry, restrict that
  table to slots at the given site only — set `table_slot[table][slot] =
  0` for every slot whose site doesn't match, leaving the solver free to
  pick which date/session at that site (or to leave the table unplaced
  if none work there). This is a hard restriction on site, not a forced
  specific slot and not merely a preference.

**Objective**, solved in two phases (a standard CP-SAT pattern for
lexicographic objectives — solve once, pin the result, solve again):
1. Maximize `sum(table_slot[*][*])` (total tables placed). Record the
   optimal count `K`.
2. Re-solve with `sum(table_slot[*][*]) == K` added as a constraint,
   this time minimizing the number of distinct slots used
   (`slot_used[slot] = OR(table_slot[*][slot])`, minimize
   `sum(slot_used)`). This is the secondary, "fewest days" goal from the
   original design, now subordinate to coverage.

A solver time limit (e.g. 120 seconds per phase) guards against a
pathological run; at this problem's real size (44 tables, ~85 judges, 4
sites) both phases are expected to solve in well under a second, but the
report must say plainly if a limit was hit without proving optimality
rather than silently presenting a possibly-suboptimal result as final.

**On "proof," precisely:** because placement is optional, the model
itself is never simply "infeasible" — you can always leave every table
unplaced. What CP-SAT proves is optimality: after phase 1, no assignment
whatsoever could place more than `K` tables given the current config, so
if a table is unfilled, that's a real fact about availability/distance/
host constraints, not an artifact of processing order. This is the
concrete improvement over the greedy script's "might just be bad luck"
caveat. Explaining *why* one specific table can't be placed (e.g. via a
follow-up solve that forces it and reports what breaks) is a natural
follow-on but out of scope for v1 — the core deliverable is the
maximum-coverage assignment and the plain list of what's left out.

## Output

Same terminal-report style as the existing scripts:

```
BBO Judging Schedule Solver (CP-SAT)
=====================================
Config: target_beers_per_pair=9, max_distance_miles=20 (schedule_config.yaml)
Solved optimally: 41 of 44 tables placed (3 unfilled) - proven maximum
Sessions used: 12

UNFILLED (3 tables - no assignment could place them given current config):
  T## Some Style: needs 4 pairs

Day 02/06:
  AM:
    T50 Pale Lager @ Arlington: JudgeA & JudgeB, JudgeC & JudgeD, ...
  ...
```

If `table_site_overrides` were used, the report should note which
tables were pinned and to where, so a re-run's output is self-explanatory
without having to go back and check the config file.

## Testing

Same convention as the rest of this project: plain `assert`-based scripts
run directly with `python3`, no pytest. CP-SAT is deterministic enough at
this scale for small synthetic scenarios to be reliable test fixtures.
Planned coverage:

- A fully-satisfiable tiny scenario (2-3 tables, enough judges) solves
  with 100% placement.
- A scenario with a genuine, unavoidable conflict (e.g. every eligible
  judge for one table has a real substyle conflict) leaves exactly that
  table unplaced while placing the rest — proving the model doesn't
  silently drop a placeable table.
- A site-anchor config entry keeps a named judge out of every slot
  outside their home site, mirroring the equivalent
  `test_propose_minimal_schedule.py` test.
- A `site_host_requirements` entry makes a site unusable in a slot with
  no host candidate available, and usable once one is.
- A `table_site_overrides` entry pins a table to a specific site even
  when an unconstrained solve would have picked a different one.
- The two-phase objective: a scenario with two different max-placement
  solutions using different session counts confirms the solver picks the
  fewer-session one.

## Known limitations

- **No per-table infeasibility explanation.** The report says a table is
  unfilled, not *why* (which specific constraint is binding). A
  follow-up "force this table and show what breaks" mode is a natural
  extension, not built in v1.
- **YAML config has no schema validation.** A malformed
  `schedule_config.yaml` (typo'd judge name, wrong site name) will fail
  silently in the sense that the entry just won't match anything real,
  rather than erroring loudly. Worth revisiting if this trips someone up
  in practice; not built now (YAGNI against a hypothetical).
- **New dependency footprint.** `ortools` is a substantial package (not
  a small pure-Python library). This is accepted for this one script,
  not a precedent for the rest of the project's stdlib-only convention.

## Out of scope

- Modifying `propose_minimal_schedule.py` in any way.
- A GUI, web page, or any interaction model beyond running a terminal
  script and reading its output / editing the YAML file.
- Per-table infeasibility diagnostics (see Known limitations).
- Config schema validation.
- Overrides beyond forcing a table to a site (date/session pinning, site
  exclusion without a replacement).
- Writing results back into `Judges_and_Tables_generated.csv` or any
  other existing file — this script only reads existing data and prints
  a report, same as `propose_minimal_schedule.py` today.
