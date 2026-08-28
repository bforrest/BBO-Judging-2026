# Judge Utilization Analysis & Schedule Reallocation Proposal

## Background

The BBO 2026 judging schedule (dates, sites, and which medal category ran
where) was built around site-host preferences, not judge availability or
travel distance. The `Judges_and_Tables_generated.csv` data model reflects
this: judges declared availability against a site-specific, pre-published
schedule, so a judge could — and often did — appear as a candidate for the
same day/session at multiple different sites, of which only one ended up
being their real assignment.

This produced visible inefficiencies. Concretely: judge Brian Street was
confirmed for only one session on several days, despite the site he judged
at running a second session that day. On 02/28, his AM session went
unfilled at every one of his four candidate sites — but that turned out to
be fully explained: all four candidate tables that morning conflicted with
his entered substyles (`Arlington T62 British Bitter` → `11C`,
`Dallas T88 Specialty Beer` → `34C`, `Grapevine T93 Specialty Cider And
Perry` → `C2B`/`C2E`, `Keller T66 British Stout` → `16A`/`16B`). Not every
gap will have such a clean explanation, and the 2026 season is over — this
work is retrospective, aimed at informing how BBO 2027 is planned.

## Goals

1. **Diagnose 2026**: for every judge, find sessions where they had
   declared availability but no confirmed assignment, and determine
   whether that gap was unavoidable (a real substyle conflict) or a missed
   opportunity (idle capacity that could have been used).
2. **Propose a better 2027**: given the same kind of availability data,
   show what schedule (table → date/session/site, judges assigned) would
   let the tables be organized around judge availability and travel
   distance instead of host preference, and how many fewer calendar
   days/sessions that could take.

These are two independent deliverables, not one combined objective —
minimizing total days and maximizing individual judge utilization can
pull in different directions, and forcing them into a single score would
hide that tradeoff rather than surface it.

## Ground-truth rule

A row in `Judges_and_Tables_generated.csv` represents a **confirmed,
historical assignment** if and only if its `PAIRING` column is non-empty.
Rows with an empty `PAIRING` are unused candidate availability — the
judge indicated willingness, but that specific site/table isn't where
they ended up. This was confirmed directly by the data owner and is the
load-bearing assumption behind both scripts.

Known edge case: this undercounts any real *solo* (unpaired) assignment,
if one exists — no evidence of one was found in the 2026 data.

## Shared data layer: `judging_common.py`

A new module, imported by both analysis scripts, so the slot-parsing
regex and CSV loaders aren't duplicated:

- `parse_slot(desired_table_str) -> (date, session, site, table_number, description)`
  — `session` is `"AM"`, `"PM"`, or `None`. Parses strings like
  `"02/07 AM Dallas T55 Kolsch and Blonde"`.
- `load_assignments(path) -> list[dict]` — rows from
  `Judges_and_Tables_generated.csv`, each augmented with its parsed slot.
- `load_styles_by_table(path) -> (dict[table] -> set[style_id], dict[table] -> medal_category_name)`
  — from `styles by table.csv`.
- `load_entry_counts(path) -> dict[table] -> int` — from
  `medal_category_counts.csv`.
- `load_judge_distances(path) -> dict[judge_full_name] -> dict[site] -> float]`
  — from `~/judge-data-private/JUDGE WORKSHEET 2026.csv` (the documented
  external, gitignored location — not read from cwd, which is where
  `generate_optimized_schedule.py` currently and inconsistently looks;
  that inconsistency is pre-existing and out of scope here).

All four loaders degrade gracefully when their file is missing or a judge
is absent from the worksheet (fail open — e.g. treat a judge with no
distance data as feasible for every site — rather than silently dropping
them), matching the pattern already used elsewhere in this codebase.

## Script 1: `analyze_judge_utilization.py`

**Algorithm**, per judge:

1. Group the judge's rows by date. For each date, collect every session
   label (`AM`/`PM`/`None`) for which the judge has *any* row that day
   (confirmed or not).
2. On any date where the judge had candidate rows in more than one
   session, every session with candidate rows but no confirmed row is a
   **gap**. Note this is deliberately broader than "confirmed in one
   session, idle in another" — it covers two distinct cases, which are
   classified and reported separately because they imply different
   remedies:
   - **`wholly_unused`** — the judge had *no* confirmed session at all
     that date, despite being available for more than one. The judge
     simply wasn't used that day. This is the majority case in the 2026
     data (30 of 45 unexplained-idle findings) and is the more valuable
     signal for future planning: it points at a judge who was willing and
     available for a whole day and got no assignment.
   - **`partially_used`** — the judge *was* confirmed for some other
     session that date, so this one specific session was blocked. This
     points at a particular session/table, not at the judge being
     overlooked wholesale.
3. For the missing session, check every candidate table the judge
   nominated there against their `SUBSTYLES ENTERED`:
   - Every candidate table conflicts → **explained by conflict**.
   - At least one candidate table has no conflict → **unexplained idle
     capacity** — a real finding.
4. For each unexplained-idle finding, annotate every non-conflicting
   candidate table with the judge's distance to that table's site (via
   `load_judge_distances`), and sort by distance ascending. Distance
   does not change the conflict/no-conflict classification — a closer
   table can't waive a real conflict — it qualifies how good the missed
   opportunity was.
5. **Double-booking detection**: separately flag any judge with two or
   more *confirmed* rows in the same `(date, session)` at different
   sites — physically impossible, and a sign of a data-entry error in
   that year's manually-assembled pairing spreadsheet. (One real
   instance was found in the 2026 data: Brian Street, 02/21 AM, confirmed
   simultaneously at Arlington T83 and Grapevine T82.)

**Output**: a text report, in the same plain style as
`optimize_judge_pairings.py`'s output, containing:

- Season-wide utilization %: confirmed judge-sessions ÷ (confirmed +
  unexplained-idle judge-sessions).
- A ranked list of unexplained-idle findings (judge, date, session,
  non-conflicting candidate tables sorted by distance), ranked by each
  finding's distance to its closest missed opportunity (findings with no
  known distance rank last), and split into two labelled sub-lists —
  `wholly_unused` and `partially_used`, per the algorithm's step 2 —
  with a count for each.
- Summary distance stats (average/median distance-to-missed-opportunity)
  across all unexplained-idle findings — a pattern of "idle capacity
  only existed far away" reads very differently from "idle capacity
  existed nearby."
- A list of double-booking anomalies found.

## Script 2: `propose_minimal_schedule.py`

**Fixed capacity rule**: each `(date, session, site)` slot holds exactly
one table. This matches how every slot in the 2026 season actually ran
(verified: all 44 `(date, session, site)` combinations in the historical
data held exactly one table each) and stands in as a proxy for real
per-site physical capacity.

**Tunable constants** (top of file, easy to adjust for "what if" runs):

- `TARGET_BEERS_PER_PAIR = 9` — tables are sized to this, not the 12-beer
  guideline ceiling, so a proposed schedule doesn't itself sit at the
  warning threshold. `required_pairs = ceil(entry_count / TARGET_BEERS_PER_PAIR)`,
  minimum 1.
- `MAX_DISTANCE_MILES = 20` — a judge is only considered feasible for a
  site if their recorded distance to it is within this cutoff (judges
  missing from the distance worksheet are treated as feasible
  everywhere — fail open, per the shared-loader behavior above).

**Per-judge availability**: the set of `(date, session)` pairs for which
the judge has *any* candidate row, site-agnostic — since site is a free
variable for this proposal, we no longer care which specific site they
originally nominated, only that they indicated willingness that
day/session. (See Limitations — this is an approximation.)

**Greedy placement algorithm**:

1. Sort the 44 tables by scarcity: fewest eligible judges first (eligible
   = no substyle conflict, within `MAX_DISTANCE_MILES` of at least one
   site), ties broken by largest `required_pairs` — hardest-to-place
   tables go first.
2. For each table, try to fit it into an already-open `(date, session)`
   slot, preferring one on a date that already has another session open
   (to consolidate into fewer distinct dates before opening a new one).
   A slot fits if: a site is still unused in that slot, and enough
   eligible, still-available judges remain that slot to form
   `required_pairs` valid pairs. A valid pair is
   (certified-or-above + certified-or-above) or
   (certified-or-above + below-certified) — never two below-certified,
   per the existing BJCP pairing rule.
3. If no open slot fits, open a new one — preferring to add the missing
   session (AM/PM) to an already-used date over opening a brand-new date.
4. Once judges are chosen for a table, pick the site (among sites open in
   that slot) that minimizes total travel distance summed across the
   assigned judges.
5. A judge is marked used for that `(date, session)` once assigned, so
   they can't be double-booked within the proposal.

**Output**: the proposed schedule (table → date/session/site → assigned
judges/pairs) and a headline comparison:

- Proposed total distinct dates and `(date, session)` slots used, stated
  alongside how many tables were actually placed and how many were left
  unfilled (`placing N of 44 tables (M unfilled)`) — never a bare table
  count that reads as full coverage.
- 2026's actual baseline: 10 dates, 14 `(date, session)` slots, 44 tables
  (full coverage).
- Theoretical floor: `ceil(tables / 4 sites)` slots, if judge availability
  allowed full 4-site parallelism every session — computed against the
  tables actually *placed* and labelled as such, so a partial-coverage run
  can't be misread as matching or beating the all-44-table floor of 11
  slots. When coverage is incomplete the report also prints an explicit
  note that the day/session counts are not comparable to the baseline.

## Testing approach

This project has no formal test framework (`test_load.py` is an ad-hoc
print-based smoke script, not pytest) — new code follows that existing
convention rather than introducing one:

- Small synthetic fixtures to validate `judging_common.py`'s parsers and
  each script's core logic in isolation, run manually and inspected
  (matching how the `generate_judges_and_tables.py` fix was verified
  earlier).
- Validation against the real repo data as a sanity check:
  `analyze_judge_utilization.py` must reproduce the Brian Street 02/28
  finding exactly (explained-by-conflict, not idle) and surface the
  02/21 double-booking anomaly. `propose_minimal_schedule.py` is **not**
  guaranteed to place all 44 tables — see the greedy-coverage entry under
  Known limitations; on the real 2026 data it places 20 and leaves 24
  unfilled. The slot/date sanity check therefore applies only to the
  subset of tables actually placed: the reported day/session count must
  be at or above the theoretical floor for *that subset*, and the report
  must state placed-vs-unfilled counts plainly so the numbers are not
  mistaken for a like-for-like win against the 14-slot / 10-date 2026
  baseline.

## Known limitations (to document in script docstrings/output)

- **Site-agnostic availability is an approximation.** 2026's signup
  process bundled site into "availability," so treating a judge's
  day/session availability as site-independent assumes they'd have been
  open to *any* site that day, filtered only by the distance cutoff —
  not confirmed true flexibility. This is worth using as evidence to
  redesign the 2027 signup form to ask day/session and site-willingness
  as separate questions, which would make this whole analysis far more
  reliable next time.
- **`PAIRING`-non-empty as "confirmed"** may undercount a real solo
  (unpaired) assignment, if one exists.
- **Distance coverage is partial.** Only judges present in
  `JUDGE WORKSHEET 2026.csv` *with at least one recorded distance* get a
  real distance-based feasibility check; judges absent from the worksheet
  and judges whose worksheet row has every distance column blank are both
  treated as feasible everywhere. (Five 2026 judges are in the latter
  group, including Mark Wedge.)
- **The greedy scheduler does not achieve full coverage.** On the real
  2026 data `propose_minimal_schedule.py` places only 20 of 44 tables and
  reports 24 as UNFILLED. Root cause: `form_pairs` selects judges purely
  on rank and availability, with no regard to which sites those judges
  can reach; `try_fit` then intersects the chosen judges' feasible sites
  *after the fact*, and that intersection is frequently empty even when a
  different, site-aware choice of judges from the same candidate pool
  would have produced a workable pair set at a workable site. The greedy
  pass does not backtrack to try another set of judges. Consequences to
  keep in mind when reading the output:
  - The proposed day/session counts describe only the placed subset and
    are **not** comparable to the 2026 baseline or to the all-44-table
    theoretical floor. The report says so explicitly.
  - The UNFILLED list is an artifact of the heuristic, not proof that
    those tables were unstaffable from the available judge pool.

  Fixing this means making pair selection site-aware (choose a candidate
  site first, filter judges to those who can reach it, then pair) or
  adding backtracking — deliberately out of scope for this iteration, and
  consistent with the "true optimal solver" item under Out of scope.

  **Scoped follow-up (not implemented, for a future session):** confirmed
  concretely on real data — table T76 (Barleywines, needs 4 pairs) has 75
  eligible judges and `form_pairs` successfully forms 4 valid rank-pairs,
  but the 4 pairs' feasible-site sets have no common intersection (one
  judge is Dallas-only, another pair is Grapevine/Dallas-only and can't
  reach Dallas together), even though an all-Grapevine-feasible set of 4
  pairs existed in the same 75-judge pool. This is exactly the bug, not
  an edge case.

  Fix: invert `try_fit`'s order of operations. Today it filters candidates
  by slot-availability and (site-agnostic) feasibility, runs `form_pairs`
  once, and only *then* intersects the chosen judges' feasible sites. The
  new version should, for a given slot: for each site still open in that
  slot, filter the candidate pool to judges feasible **at that specific
  site**, then run `form_pairs` on that site-restricted pool. Collect
  every site where `form_pairs` fully succeeds (returns all
  `required_pairs`), and — per the decision made when this was scoped —
  pick the site minimizing total travel distance across the resulting
  pairs among those successes (reusing `pick_site`'s existing distance
  arithmetic, just invoked once per successful candidate site instead of
  once after the fact). If no site succeeds, the table is genuinely
  unfillable at this slot, and `try_fit` returns `None` as before.

  This only changes `try_fit`'s internals in `propose_minimal_schedule.py`
  — `form_pairs`, `judge_feasible_sites`, `eligible_judges_for_table`, and
  `pick_site` stay as-is and get called from a different place/order, not
  redefined. No change to `judging_common.py` or
  `analyze_judge_utilization.py`. Expect to update or replace a couple of
  the existing `build_schedule` tests in `test_propose_minimal_schedule.py`
  whose fixtures assumed the old pick-then-check behavior (a case
  structured like today's "T76 fails" scenario should now succeed).
  Validate against real data by confirming the placed-table count rises
  materially above 20/44 — full coverage isn't guaranteed even after this
  fix (genuine judge/distance scarcity can still leave a table unfillable),
  but a large unexplained gap surviving the fix would mean the redesign
  itself has a bug, not that the limitation persists as documented here.

  **Additional scoped follow-up: site-host constraints.** A handful of
  named judges are physically tied to a specific site (it's their home or
  workplace) and need hard rules the distance-based feasibility model
  doesn't capture on its own. Confirmed real-data spelling (two of the
  four names given verbally didn't match the CSV — `Marc McCurdy` is
  really `Mark McCurdy`; `Matt Morriss` is really `Matthew Morriss`;
  `Jarrett Long`, `Amanda Long`, `Reni Morriss`, `Terry Olinger`, and
  `Mike Grover` all matched as given):

  - **Site anchors** — `Amanda Long` and `Jarrett Long` (Arlington),
    `Reni Morriss` and `Matthew Morriss` (Keller), `Mark McCurdy`
    (Grapevine): for these five, `judge_feasible_sites` must return
    *only* their home site, overriding the normal distance computation
    entirely rather than intersecting with it. They're ordinary judges
    in every other respect — still subject to the usual certification
    pairing rule, and not required to appear in every session at their
    site, just permanently excluded from being placed anywhere else.
  - **Dallas host requirement** — `Terry Olinger` and `Mike Grover`:
    neither may be selected into a Dallas judging pair (their feasible
    sites are their normal computed set *minus* Dallas), but Dallas
    should only be offered as a candidate site for a given
    `(date, session)` slot if at least one of them has *any* existing
    availability row for that slot — using their regular judge-
    availability data as the presence signal, no new data needed. If
    neither has an availability row for that slot, Dallas is dropped
    from that slot's candidate sites entirely, the same as if every
    site were already booked.

  Both rules are pure filters on the same two functions the pairing
  redesign above already touches (`judge_feasible_sites` for the site
  anchors and judge exclusion; the per-slot candidate-site list for the
  Dallas host check) — implement them together with that redesign, not
  as a separate pass. No change to `judging_common.py` or
  `analyze_judge_utilization.py`. A hardcoded small config (e.g. two
  dicts/sets of judge name → site) at the top of
  `propose_minimal_schedule.py`, alongside `TARGET_BEERS_PER_PAIR` and
  `MAX_DISTANCE_MILES`, is sufficient — no need for a new data file for
  five to seven names. Test by asserting `judge_feasible_sites` for each
  anchored judge returns exactly their one site regardless of the
  `distances` dict passed in, and that a slot with no host-candidate
  availability drops Dallas from that slot's site list.

## Out of scope

- A single combined objective balancing day-count against utilization
  (explicitly rejected in favor of two separate reports).
- A true optimal solver (e.g. OR-Tools CP-SAT) — the greedy heuristic is
  the chosen approach for this iteration; revisit if the heuristic's gap
  from the theoretical floor turns out to matter in practice.
- Changing the 2027 signup form or data collection process itself (a
  follow-up action this analysis is meant to motivate, not implement).
- Any change to the already-existing scripts (`generate_optimized_schedule.py`,
  etc.) beyond reading their output files as input.
