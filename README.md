# BBO 2026 Judging Schedule Visualization

Interactive HTML visualization tool for managing and viewing the BBO (Best Beers of) 2026 homebrew competition judging schedule.

## Overview

This tool reads judge assignments and competition data from CSV/TSV files and generates an interactive HTML page that shows:

- **Judge assignments** organized by date and location
- **Color-coded judge ranks** (Non-BJCP, Provisional, Recognized, Certified, National)
- **Conflict detection** - highlights when judges have entered beers in categories they're judging
- **Pairing information** - shows which judges are paired together
- **BJCP style information** - displays which beer styles are in each table
- **Table category names** - shows the BBO Medal category for each table

## Files

### Input Data Files
- `Judges and Tables.tsv` - Judge assignments, rankings, and entries
- `styles by table.csv` - Mapping of BBO Medal tables to BJCP styles
- `medal_category_counts.csv` - Entry counts for each BBO Medal table (fetched from website)
- `JUDGING SCHEDULE.csv` - Schedule dates and locations (for reference)
- `~/judge-data-private/JUDGE WORKSHEET 2026.csv` - Master judge roster with PII (tracked separately, not pushed to GitHub)

### Scripts
- `generate_schedule.py` - **Current script** - Creates the visualization with conflict and workload detection
- `fetch_medal_counts.py` - Fetches current entry counts from the BBO website
- `generate_optimized_schedule.py` - Optimizes judge assignments using distance and availability data (deprecated for visualization)
- `calculate_distances.py` - Calculates distances from judge addresses to competition sites
- `visualize_judging.py` - Alternative visualization script

### Generated Files
- `judging_schedule.html` - Interactive HTML schedule (generated locally, open in any browser)
- `judging_schedule.pdf` - Printable PDF version of the schedule

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

Whenever you update your data files, regenerate the schedule:

```bash
python3 generate_schedule.py
```

The script will:
1. Read all data files from the current directory
2. Load entry counts from `medal_category_counts.csv`
3. Process judge assignments and detect conflicts
4. Calculate workload for certified judge pairs
5. Flag tables where certified pairs would need to evaluate more than 9 beers
6. Generate `judging_schedule.html` with the visualization
7. Display summary statistics

**Note:** The first time you run the script, you may need to install required libraries:
```bash
pip3 install weasyprint requests beautifulsoup4
```

### Deploy to GitHub Pages

After generating the schedule locally, commit and push your changes:

```bash
git add judging_schedule.html
git commit -m "Update judging schedule"
git push
```

The GitHub Actions workflow will automatically:
1. Copy `judging_schedule.html` to `index.html`
2. Deploy to GitHub Pages

**Important:** The schedule is generated locally (not on GitHub) because it requires access to protected judge data that should never be pushed to the repository.

### View the Schedule

Open the HTML version in any web browser:

```bash
open judging_schedule.html
```

Or double-click the file in Finder.

The PDF version (`judging_schedule.pdf`) can be opened with any PDF reader and is ideal for printing.

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

### Judges and Tables.tsv

Tab-separated file with columns:
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
- Check for empty first lines in TSV files

**Problem**: Pairing info not showing
- **Solution**: Pairing only displays when the "PAIRING" column has values in the TSV file

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
git add generate_schedule.py judging_schedule.html README.md
git commit -m "Update judging schedule visualization"
```

### Sensitive Data Management

The `JUDGE WORKSHEET 2026.csv` file contains personally identifiable information (names, addresses, phone numbers, emails) and is stored locally but **not pushed to GitHub**. The optimized schedule generation happens locally using this protected data, and only the generated HTML output is committed to the repository.

**Key files protected:**
- `JUDGE WORKSHEET 2026*` is in `.gitignore` and never pushed to remote

**GitHub Actions Workflow:**
The `.github/workflows/deploy.yml` file has been updated to work with local schedule generation:
- It no longer runs `generate_schedule.py` (which would fail without protected data)
- It copies the locally-generated `judging_schedule.html` to `index.html`
- Then deploys to GitHub Pages

**Workflow:**
1. Generate schedule locally: `python3 generate_optimized_schedule.py`
2. Commit the generated HTML: `git add judging_schedule.html && git commit -m "Update schedule"`
3. Push to GitHub: `git push`
4. GitHub Actions automatically deploys to GitHub Pages

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