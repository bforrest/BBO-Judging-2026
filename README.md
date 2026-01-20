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
- `JUDGING SCHEDULE.csv` - Schedule dates and locations (for reference)

### Generated Files
- `generate_schedule.py` - Python script that creates the visualization
- `judging_schedule.html` - Interactive HTML schedule (open in any browser)
- `judging_schedule.pdf` - Printable PDF version of the schedule

## Usage

### Generate/Update the Schedule

Whenever you update your data files, regenerate the visualization:

```bash
python3 generate_schedule.py
```

The script will:
1. Read all data files from the current directory
2. Process judge assignments and detect conflicts
3. Generate `judging_schedule.html` and `judging_schedule.pdf`
4. Display summary statistics

**Note:** The first time you run the script, you may need to install the PDF library:
```bash
pip3 install weasyprint
```

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

### Conflict Indicators

- **Red border** - Table has at least one judge who entered a beer in that category
- **⚠ Badge** - Shows specific BJCP style IDs that conflict for that judge

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

## Troubleshooting

**Problem**: HTML page shows headers but no data
- **Solution**: Check that data files are in the same directory as the script
- Check for empty first lines in TSV files

**Problem**: Pairing info not showing
- **Solution**: Pairing only displays when the "PAIRING" column has values in the TSV file

**Problem**: Python not found
- **Solution**: Ensure Python 3 is installed: `python3 --version`

## Version Control

Track changes with Git:

```bash
git add generate_schedule.py judging_schedule.html README.md
git commit -m "Update judging schedule visualization"
```

## Sharing the Schedule

The `judging_schedule.html` file is completely standalone and can be:
- Emailed to other organizers
- Uploaded to a website
- Opened on any device with a web browser
- No internet connection or software required to view