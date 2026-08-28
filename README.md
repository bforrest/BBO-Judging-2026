# BBO 2026 Judging Schedule Visualization

Interactive HTML visualization tool for managing and viewing the Bluebonnet Brew Off 2026 homebrew competition judging schedule.

## Overview

This tool reads judge assignments and competition data from CSV files and generates an interactive HTML page that shows:

- **Judge assignments** organized by date and location
- **Color-coded judge ranks** (Non-BJCP, Provisional, Recognized, Certified, National)
- **Conflict detection** - highlights when judges have entered beers in categories they're judging
- **Pairing information** - shows which judges are paired together
- **BJCP style information** - displays which beer styles are in each table
- **Table category names** - shows the BBO Medal category for each table

## Files

### Input Data Files
- `Judges_and_Tables_generated.csv` - **Current source of truth** for judge assignments, rankings, pairings, and entries. Committed to the repo (no PII beyond names) and hand-edited directly as pairing updates come in from other organizers.
- `styles by table.csv` - Mapping of BBO Medal tables to BJCP styles
- `medal_category_counts.csv` - Entry counts for each BBO Medal table (fetched from website)
- `JUDGING SCHEDULE.csv` - Schedule dates and locations (for reference)
- `JUDGE WORKSHEET 2026.csv` - Local-only, gitignored roster with PII (addresses, phone, email) and computed distances to each site. Optional — the generator degrades gracefully if it's missing, only losing distance-based suggestions.
- `Bluebonnet_Brew-Off_For_2026_Available_Judge_Emails_*.csv` - Raw signup export from the BCOEM site. Local-only, gitignored. Originally the intended input to `generate_judges_and_tables.py`.
- `Judges and Tables.tsv` - **Legacy** original data format, superseded by `Judges_and_Tables_generated.csv`. Not actively updated (last touched 2026-01-23).

### Scripts
- `generate_optimized_schedule.py` - **Current script**, run in GitHub Actions on every push. Reads `Judges_and_Tables_generated.csv`, `styles by table.csv`, `medal_category_counts.csv`, and (if present locally) `JUDGE WORKSHEET 2026.csv`. Produces the main and per-site HTML pages with conflict, workload, and certification-pairing checks.
- `generate_schedule.py` - **Superseded** by `generate_optimized_schedule.py` as of 2026-01-21 and no longer maintained (last touched 2026-01-20). Kept for reference only.
- `fetch_medal_counts.py` - Fetches current entry counts from the BBO website
- `calculate_distances.py` - Geocodes judge addresses and calculates driving distances to each site; writes results into the local judge worksheet
- `generate_judges_and_tables.py` - Regenerates `Judges_and_Tables_generated.csv` from the raw Bluebonnet signup export, preserving any pairings already recorded in the existing output file.
- `generate_judging_site_contacts.py` - Builds a per-site contact list (`judging_site_contacts.csv`) by joining `Judges_and_Tables_generated.csv` with `JUDGE WORKSHEET 2026.csv`. Output is gitignored since it contains PII.
- `judges_by_site.py` - Quick listing of judges available per site/date, parsed straight from the raw Bluebonnet signup export
- `visualize_judging.py` - Alternative visualization script
- `judging_common.py` - Shared CSV loaders and slot-string parser used by `analyze_judge_utilization.py` and `propose_minimal_schedule.py` (see below)
- `analyze_judge_utilization.py` - Retrospective diagnostic: finds sessions where a judge had availability but no confirmed assignment, and classifies each gap as explained by a real conflict or as unexplained idle capacity. See [Judge Utilization Analysis & Schedule Proposal](#judge-utilization-analysis--schedule-proposal-2027-planning) below.
- `propose_minimal_schedule.py` - Proposes a reallocated schedule (table → date/session/site, judges assigned) built around judge availability and travel distance instead of site-host preference. See below.

### One-time optimization pass (historical, no longer active)
On 2026-01-23 a distance/availability-based optimizer and recommendation system was built to analyze conflicts and workload imbalances: `optimize_judge_pairings.py`, `generate_recommendations.py`, `export_pairing_worksheet.py`, and their docs (`START_HERE.md`, `QUICK_REFERENCE.md`, `JUDGE_RECOMMENDATIONS.md`, `OPTIMIZATION_GUIDE.md`, `OPTIMIZATION_SUMMARY.md`, `README-OPTIMIZATION.md`, `SETUP_COMPLETE.md`, `PAIRING_WORKSHEET.csv`). None of these have been touched since that single pass. They were superseded by manually incorporating real pairing data collected from other organizers directly into `Judges_and_Tables_generated.csv`, plus the conflict/workload/certification checks being built into `generate_optimized_schedule.py` itself.

### Generated Files
- `judging_schedule.html` - Interactive HTML schedule, all sites (committed and deployed to GitHub Pages)
- `judging_schedule_arlington.html`, `judging_schedule_dallas.html`, `judging_schedule_grapevine.html`, `judging_schedule_keller.html` - Per-site HTML pages
- `judging_schedule.pdf` - Printable PDF version of the schedule (requires `weasyprint`)
- `judges_by_site.csv` - Output of `judges_by_site.py`
- `judging_site_contacts.csv` - Output of `generate_judging_site_contacts.py`; gitignored (PII)

## Usage

### Fetch Current Entry Counts

To get the latest entry counts from the BBO website:

```bash
python3 fetch_medal_counts.py
```

This will:
1. Fetch the "Current Medal Category Counts" table from the BBO website
2. Extract entry counts for each table
3. Save to `medal_category_counts.csv`

### Generate/Update the Schedule

Whenever you update `Judges_and_Tables_generated.csv` (or the other data files), regenerate the schedule:

```bash
python3 generate_optimized_schedule.py
```

The script will:
1. Read `Judges_and_Tables_generated.csv`, `styles by table.csv`, `medal_category_counts.csv`, and (if present) `JUDGE WORKSHEET 2026.csv`
2. Process judge assignments and detect conflicts
3. Calculate workload for certified judge pairs
4. Flag tables where certified pairs would need to evaluate more than 9 beers
5. Generate `judging_schedule.html` plus per-site pages (`judging_schedule_dallas.html`, etc.)
6. Generate `judging_schedule.pdf` if `weasyprint` is installed
7. Display summary statistics

**Note:** The first time you run the script, you may need to install required libraries:
```bash
pip3 install weasyprint requests beautifulsoup4
```

### Deploy to GitHub Pages

`generate_optimized_schedule.py` runs automatically in GitHub Actions on every push to `main` (see `.github/workflows/deploy.yml`) — you don't need to generate the HTML locally before pushing. Just commit your data changes:

```bash
git add "Judges_and_Tables_generated.csv"
git commit -m "Update judge assignments"
git push
```

The workflow then:
1. Checks out the repo
2. Runs `generate_optimized_schedule.py` to produce fresh HTML pages
3. Deploys the working directory to GitHub Pages

Running the script locally first is still useful for previewing changes before you push.

### View the Schedule

Open the HTML version in any web browser:

```bash
open judging_schedule.html
```

Or double-click the file in Finder.

The PDF version (`judging_schedule.pdf`) can be opened with any PDF reader and is ideal for printing.

## Judge Utilization Analysis & Schedule Proposal (2027 planning)

These two scripts are retrospective — the 2026 season is over, and they're meant to inform how BBO 2027 gets planned, not to change anything about 2026. Full design details (algorithm, data model, known limitations) are in `docs/superpowers/specs/2026-08-27-judge-utilization-and-schedule-optimization-design.md`.

Both read `Judges_and_Tables_generated.csv`, `styles by table.csv`, and (if present locally) `JUDGE WORKSHEET 2026.csv` for distance data — the same inputs `generate_optimized_schedule.py` uses. Run them from the repo root:

### Diagnose 2026 utilization

```bash
python3 analyze_judge_utilization.py
```

For every judge, finds days where they had availability for more than one session but weren't confirmed (`PAIRING` filled in) for all of them, and explains each gap: was it unavoidable (every candidate table conflicted with something they entered) or a missed opportunity (a non-conflicting table existed but they weren't assigned)? Also flags "double-booking" data anomalies — a judge confirmed at two different sites for the same session, which is physically impossible and usually means a data-entry mistake in that year's manually-assembled pairing spreadsheet.

Sample output:
```
Judge Utilization Analysis (2026 retrospective)
==================================================
Season-wide utilization: 86% (286 confirmed judge-sessions / 331 confirmed + unexplained-idle)
Session gaps on multi-session days: 47 total, 2 explained by conflict (4%), 45 unexplained idle capacity
Distance to closest missed opportunity: average 15.5mi, median 12.5mi (across 26 findings); 19 findings skipped - no known distance

Unexplained idle capacity (45 findings: 30 wholly unused, 15 partially used),
ranked by distance to the closest missed opportunity:

  Wholly unused days (judge had NO confirmed session that date) - 30 findings:
    Reni Morriss - 02/28 AM:
      could have judged T66 at Keller (3mi)
    ...
```

### Propose a reallocated schedule

```bash
python3 propose_minimal_schedule.py
```

Treats each table's site as a free variable (rather than fixed by host preference) and greedily packs tables into the fewest `(date, session)` slots that judges' declared availability and travel distance can support. Two constants near the top of the file are meant to be tuned for "what if" comparisons: `TARGET_BEERS_PER_PAIR` (default 9) and `MAX_DISTANCE_MILES` (default 20, how far a judge can reasonably be asked to travel).

**Known limitation:** the current pairing logic picks judges without regard to site, then checks site feasibility afterward — so a meaningful number of tables typically come back `UNFILLED` even when a site-aware assignment would have worked. This is a real gap in the algorithm, not a data problem; see the spec's "Known limitations" section for the root cause and what a fix would take.

Sample output:
```
BBO Judging Schedule Proposal
========================================
Proposed: 8 days, 11 sessions, placing 20 of 44 tables (24 unfilled)
2026 actual: 10 days, 14 sessions, 44 tables (full coverage)
Theoretical floor for the 20 placed tables (4 sites, full parallelism): 5 sessions

NOTE: coverage is incomplete, so the day/session counts above are NOT comparable
to the 2026 baseline or to the all-44-table floor of 11 sessions.

UNFILLED (24 tables could not be staffed):
  T76 Barleywines: needs 4 pairs
  ...
```

## Understanding the Visualization

### Color Legend

- **Yellow** - Level 0: Non-BJCP
- **Orange** - Level 1: Rank Pending/Provisional
- **Light Orange** - Level 2: Recognized
- **Blue** - Level 3: Certified (includes Certified+Mead, Certified+Mead+Cider)
- **Purple** - Level 4: National

### Warning Indicators

#### Conflict Warnings (Red Border)
- **Red border** - Table has at least one judge who entered a beer in that category
- **⚠ Badge** - Shows specific BJCP style IDs that conflict for that judge

#### Workload Warnings (Orange Border)
- **Orange border** - Certified judge pairs would need to evaluate more than 9 beers each
- **⚠️ Badge** - Shows calculation: "X beers/pair (Y entries ÷ Z qualified pairs) • A Certified+ • B Below Certified"
- **BJCP Guideline**: Judge pairs should not evaluate more than 12 beers; warning triggered at >9 beers per pair
- **Pairing Logic**: Each Certified+ judge (Level 3 or higher) forms one qualified pair with a non-certified judge

### Table Information

Each table displays:
- **Table number** (e.g., T68)
- **BBO Medal category name** (e.g., "Pale American Ale")
- **BJCP Styles** - List of beer style IDs being judged at this table
- **Entries** - Number of beers entered in this category
- **Judges** - Color-coded by rank, with pairing and conflict badges

### Pairing Information

- **Gray badge** - Shows pairing number when judges are designated to work together
- Note: Only shows when pairing data exists in the source file

## Data Format Requirements

### Judges_and_Tables_generated.csv

CSV file with columns (same schema as the legacy `Judges and Tables.tsv`, just comma-delimited):
- `FULL NAME` - Judge's name
- `DESIRED TABLE TO JUDGE` - Format: "MM/DD Location TNN Description"
- `PAIRING` - Optional pairing number
- `BJCP ID` - Judge's BJCP ID
- `RANKING` - Judge's BJCP rank level
- `SUBSTYLES ENTERED` - Comma-separated list of BJCP style IDs

### styles by table.csv

CSV file with columns:
- `Medal Category Name` - BBO category name
- `Table Number` - Numeric table number (without "T" prefix)
- `BJCP Style Name` - Full style name
- `BJCP Style Id` - BJCP style ID (e.g., "18B", "05D")

### medal_category_counts.csv

CSV file with columns (auto-generated by `fetch_medal_counts.py`):
- `Table Number` - Numeric table number (without "T" prefix)
- `Table Name` - BBO Medal category name
- `Count` - Number of entries in this category

## Troubleshooting

**Problem**: HTML page shows headers but no data
- **Solution**: Check that data files are in the same directory as the script
- Check for empty first lines in `Judges_and_Tables_generated.csv`

**Problem**: Pairing info not showing
- **Solution**: Pairing only displays when the "PAIRING" column has values in `Judges_and_Tables_generated.csv`

**Problem**: Entry counts not showing
- **Solution**: Run `python3 fetch_medal_counts.py` to download current entry counts from the BBO website
- Check that `medal_category_counts.csv` exists and contains data

**Problem**: Workload warnings not appearing
- **Solution**: Ensure `medal_category_counts.csv` has been generated and contains entry counts
- Workload warnings only show when certified pairs would need to evaluate more than 9 beers each

**Problem**: Python not found
- **Solution**: Ensure Python 3 is installed: `python3 --version`

## Version Control

Track changes with Git:

```bash
git add "Judges_and_Tables_generated.csv" generate_optimized_schedule.py README.md
git commit -m "Update judging schedule"
```

### Sensitive Data Management

`Judges_and_Tables_generated.csv` (judge names, ranks, table assignments) is committed and tracked normally — it's the data the site is built from. Only the richer roster data with addresses/phone/email lives locally:

**Key files protected (gitignored, never pushed):**
- `JUDGE WORKSHEET 2026*` - full roster with PII and computed distances
- `Bluebonnet_Brew-Off_For_2026_Available_Judge_Emails_*.csv` - raw signup export with emails
- `judging_site_contacts.csv` - generated per-site contact list with phone/email

**GitHub Actions Workflow:**
`.github/workflows/deploy.yml` runs `generate_optimized_schedule.py` directly on GitHub's runners — the gitignored PII files aren't present there, so the script simply skips distance-based suggestions and runs on `Judges_and_Tables_generated.csv` alone.

**Workflow:**
1. Edit `Judges_and_Tables_generated.csv` (pairings, assignments, entries)
2. Optionally preview locally: `python3 generate_optimized_schedule.py`
3. Commit and push: `git add "Judges_and_Tables_generated.csv" && git commit -m "Update assignments" && git push`
4. GitHub Actions regenerates the HTML and deploys to GitHub Pages automatically

**To calculate distances from judge addresses to competition sites:**
```bash
cd "/Users/barryforrest/Documents/Judging BBO 2026"
.venv/bin/python calculate_distances.py
```

This uses geocoding (via the free Nominatim service) to convert addresses to coordinates and calculates driving distances. The script:
- Requires `geopy` package (install with `pip install geopy`)
- Takes several minutes due to API rate limiting (1 second between requests)
- Updates distance columns in the judge worksheet automatically

## Sharing the Schedule

The `judging_schedule.html` file is completely standalone and can be:
- Emailed to other organizers
- Uploaded to a website
- Opened on any device with a web browser
- No internet connection or software required to view