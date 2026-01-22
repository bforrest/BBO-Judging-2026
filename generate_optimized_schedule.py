#!/usr/bin/env python3
"""
BBO 2026 Judging Schedule Visualizer

This script reads judge assignment data and creates an interactive HTML page
showing the judging schedule with conflict detection and color-coded ranks.

Input files (must be in same directory):
    - Judges and Tables.tsv: Judge assignments and entries
    - styles by table.csv: BJCP style mappings
    - ~/judge-data-private/JUDGE WORKSHEET 2026.csv: Judge roster with distances

Output:
    - judging_schedule.html: Interactive visualization
    - judging_schedule.pdf: Printable PDF version

Usage:
    python3 generate_schedule.py
"""

# Import required libraries
# csv: For reading CSV and TSV files
# defaultdict: For creating dictionaries with default values
import csv
import os
from collections import defaultdict
PDF_AVAILABLE = False
#try:
#    from weasyprint import HTML
#    PDF_AVAILABLE = True
#except ImportError:
#    PDF_AVAILABLE = False

# =============================================================================
# STEP 1: LOAD JUDGE MASTER ROSTER WITH DISTANCES
# =============================================================================
print("Loading judge master roster...")

# Load judge distance data from the private repo
judge_distances = {}
judge_worksheet_path = os.path.join(os.getcwd(), "JUDGE WORKSHEET 2026.csv")

try:
    with open(judge_worksheet_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            first_name = row.get('First Name', '').strip()
            last_name = row.get('Last Name', '').strip()
            
            if not first_name or not last_name:
                continue
            
            full_name = f"{first_name} {last_name}"
            
            # Store distance info for this judge
            judge_distances[full_name] = {
                'dallas': int(row.get('DALLAS SITE', 0) or 0),
                'grapevine': int(row.get('GRAPEVINE SITE', 0) or 0),
                'arlington': int(row.get('ARLINGTON SITE', 0) or 0),
                'stubbies': int(row.get('STUBBIES SITE', 0) or 0),
                'keller': int(row.get('KELLER SITE', 0) or 0),
                'status': row.get('JUDGE STATUS', ''),
                'rank': row.get('BJCP Rank', '')
            }
    
    print(f"Loaded distance data for {len(judge_distances)} judges")
except FileNotFoundError:
    print(f"Warning: Judge worksheet not found at {judge_worksheet_path}")
    print("Distance-based assignment suggestions will not be available.")

# =============================================================================
# STEP 2: LOAD JUDGE ASSIGNMENTS
# =============================================================================
print("Loading judge data...")

# Function to normalize ranking text for consistent display
def normalize_rank(rank_text):
    """Normalize ranking values to standard display format."""
    rank = rank_text.strip()
    # Handle lowercase variants
    if rank.lower() == 'certified':
        return 'Level 3: Certified'
    elif rank.lower() == 'national':
        return 'Level 4: National'
    # Return as-is for other values (already formatted)
    return rank

# Create an empty list to store all judge information
judges = []

# Create a dictionary to store substyles for ALL judges (not just assigned ones)
all_judge_substyles = {}

# Open the TSV (tab-separated values) file containing judge assignments
with open("Judges and Tables.tsv", 'r', encoding='utf-8') as f:
    # Skip the first blank line in the file
    next(f)
    
    # Create a CSV reader that uses tabs as separators
    # This will automatically read the header row and use it as column names
    reader = csv.DictReader(f, delimiter='\t')
    
    # Loop through each row in the file (each row is one judge assignment)
    for row in reader:
        # Get the judge's name and remove any quote marks
        name = row.get('FULL NAME', '').strip('"')
        
        if not name:
            continue
        
        # Parse the substyles this judge has entered
        # This is a comma-separated list in the TSV file
        substyles_str = row.get('SUBSTYLES ENTERED', '').strip('"')
        # Split on commas and remove whitespace from each style ID
        substyles = [s.strip() for s in substyles_str.split(',') if s.strip()]
        
        # Store substyles for this judge (for later conflict checking)
        all_judge_substyles[name] = substyles
        
        # Skip if there's no table assignment
        if not row.get('DESIRED TABLE TO JUDGE'):
            continue
            
        # Get the full table assignment string (e.g., "02/06 Arlington T68 American Pale Ale")
        table_str = row.get('DESIRED TABLE TO JUDGE', '')
        
        # Skip judges who haven't been assigned to a table yet
        if 'no table' in table_str.lower():
            continue
            
        # Use regular expressions to extract date, location, and table number
        # Regular expressions (regex) are patterns for matching text
        import re
        
        # This pattern looks for: (2 digits/2 digits) (optional AM/PM + word) T(digits)
        # Example: "02/06 Arlington T68" or "02/07 AM Dallas T55"
        # The (?:\w+\s+)? means "optionally match word+space" (for AM/PM)
        match = re.match(r'(\d{2}/\d{2})\s+(?:\w+\s+)?(\w+)\s+T(\d+)', table_str)
        
        # If the pattern didn't match, skip this row
        if not match:
            continue
            
        # Extract the matched parts
        date, location, table_num = match.groups()
        
        # Add this judge's information to our list as a dictionary
        judges.append({
            'name': name,
            'date': date,                    # e.g., "02/06"
            'location': location.upper(),    # e.g., "ARLINGTON"
            'table': f'T{table_num}',        # e.g., "T68"
            'pairing': row.get('PAIRING', '').strip(),
            'rank': normalize_rank(row.get('RANKING', '')),  # Normalize rank display
            'substyles': substyles           # List of style IDs they entered
        })

print(f"Loaded {len(judges)} judge assignments")
print(f"Loaded substyle data for {len(all_judge_substyles)} judges")

# =============================================================================
# STEP 3: LOAD TABLE STYLES AND CATEGORY NAMES
# =============================================================================
print("Loading table style mappings...")

# Create a special dictionary that automatically creates empty lists for new keys
table_styles = defaultdict(list)

# Create a regular dictionary to store category names for each table
table_names = {}

# Open the CSV file that maps tables to BJCP styles
with open("styles by table.csv", 'r', encoding='utf-8') as f:
    # Create a CSV reader that automatically uses the first row as column names
    reader = csv.DictReader(f)
    
    # Loop through each row in the CSV file
    for row in reader:
        # Get values from each column
        table = row.get('Table Number', '').strip()
        style_id = row.get('BJCP Style Id', '').strip()
        style_name = row.get('BJCP Style Name', '').strip()
        category_name = row.get('Medal Category Name', '').strip()
        
        # Only process rows that have both a table number and style ID
        if table and style_id:
            # Create table key with "T" prefix (e.g., "T68")
            table_key = f'T{table}'
            
            # Add this style ID to the list for this table
            table_styles[table_key].append(style_id)
            
            # Store the category name (only the first time we see this table)
            if table_key not in table_names and category_name:
                table_names[table_key] = category_name

print(f"Loaded {len(table_styles)} table mappings")

# =============================================================================
# STEP 4: LOAD MEDAL CATEGORY COUNTS
# =============================================================================
print("Loading medal category counts...")

# Create a dictionary to store entry counts for each table
table_entry_counts = {}

# Open the CSV file with medal category counts
try:
    with open("medal_category_counts.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            table_num = row.get('Table Number', '').strip()
            count_str = row.get('Count', '').strip()
            
            if table_num and count_str:
                # Create table key with "T" prefix (e.g., "T68")
                table_key = f'T{table_num}'
                
                # Convert count to integer
                try:
                    table_entry_counts[table_key] = int(count_str)
                except ValueError:
                    print(f"Warning: Could not parse count '{count_str}' for table {table_key}")
    
    print(f"Loaded entry counts for {len(table_entry_counts)} tables")
except FileNotFoundError:
    print("Warning: medal_category_counts.csv not found. Workload warnings will not be displayed.")

# =============================================================================
# STEP 5: ORGANIZE JUDGES BY DATE, LOCATION, AND TABLE
# =============================================================================

# Create a nested dictionary structure:
# {date: {location: {table: [list of judges]}}}
# Example: {"02/06": {"ARLINGTON": {"T68": [judge1, judge2, ...]}}}
by_date_loc = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

# Loop through all judges and organize them
for j in judges:
    # Add each judge to the appropriate date/location/table
    by_date_loc[j['date']][j['location']][j['table']].append(j)

# =============================================================================
# STEP 6: ANALYZE JUDGE ASSIGNMENTS AND SUGGEST IMPROVEMENTS
# =============================================================================
print("\nAnalyzing judge assignments...")

def get_location_key(location):
    """Normalize location names to match distance data keys."""
    location_mapping = {
        'DALLAS': 'dallas',
        'GRAPEVINE': 'grapevine',
        'ARLINGTON': 'arlington',
        'STUBBIES': 'stubbies',
        'KELLER': 'keller'
    }
    return location_mapping.get(location.upper(), location.lower())

def is_certified_or_higher(rank):
    """Check if a rank is Certified (Level 3) or higher."""
    rank_levels = {
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
        'national': 4,
        'Level 4: National': 4
    }
    rank_level = rank_levels.get(rank, 0)
    return rank_level >= 3

# Find available judges (all judges who could potentially be assigned)
all_judges_roster = {}
for judge_name, dist_info in judge_distances.items():
    if dist_info.get('status', '').upper() == 'ACTIVE':
        all_judges_roster[judge_name] = dist_info

# Analyze each table for workload and conflicts
table_analysis = []

for date in by_date_loc:
    for location in by_date_loc[date]:
        for table, judges_at_table in by_date_loc[date][location].items():
            entry_count = table_entry_counts.get(table, 0)
            table_substyles = table_styles.get(table, [])
            
            # Check for conflicts
            judges_with_conflicts = []
            for j in judges_at_table:
                judge_conflicts = [s for s in j['substyles'] if s in table_substyles]
                if judge_conflicts:
                    judges_with_conflicts.append({
                        'name': j['name'],
                        'conflicts': judge_conflicts
                    })
            
            # Calculate workload
            certified_count = sum(1 for j in judges_at_table if is_certified_or_higher(j['rank']))
            num_pairs = certified_count if certified_count > 0 else len(judges_at_table) / 2
            beers_per_pair = entry_count / num_pairs if num_pairs > 0 and entry_count > 0 else 0
            
            needs_more_judges = beers_per_pair > 9 and entry_count > 0
            needs_replacement = len(judges_with_conflicts) > 0
            
            if needs_more_judges or needs_replacement:
                # Find suitable replacement/additional judges
                location_key = get_location_key(location)
                
                # Get judges not currently assigned to this table
                # Normalize names to handle different formats (e.g., "First Last" vs "Last, First")
                assigned_judge_names = set()
                for j in judges_at_table:
                    assigned_judge_names.add(j['name'])
                    # Also add reversed format if name contains comma
                    if ',' in j['name']:
                        parts = j['name'].split(',')
                        if len(parts) == 2:
                            reversed_name = f"{parts[1].strip()} {parts[0].strip()}"
                            assigned_judge_names.add(reversed_name)
                    else:
                        # Add comma format too
                        parts = j['name'].split()
                        if len(parts) >= 2:
                            reversed_name = f"{parts[-1]}, {' '.join(parts[:-1])}"
                            assigned_judge_names.add(reversed_name)
                
                # Find candidates: active, not assigned to this table, no conflicts, reasonable distance
                candidates = []
                for judge_name, dist_info in all_judges_roster.items():
                    if judge_name in assigned_judge_names:
                        continue
                    
                    # Check if already assigned somewhere else on this date
                    already_assigned = any(
                        judge_name == j['name'] and j['date'] == date
                        for j in judges
                    )
                    
                    if already_assigned:
                        continue
                    
                    # Check for conflicts with this table using all_judge_substyles
                    judge_substyles = all_judge_substyles.get(judge_name, [])
                    
                    has_conflict = any(s in table_substyles for s in judge_substyles)
                    if has_conflict:
                        continue
                    
                    distance = dist_info.get(location_key, 999)
                    rank = dist_info.get('rank', '')
                    
                    if distance > 0 and distance < 100:  # Reasonable driving distance
                        candidates.append({
                            'name': judge_name,
                            'distance': distance,
                            'rank': rank,
                            'certified': is_certified_or_higher(rank)
                        })
                
                # Sort candidates by distance only (shortest distance first)
                candidates.sort(key=lambda x: x['distance'])
                
                table_analysis.append({
                    'date': date,
                    'location': location,
                    'table': table,
                    'entry_count': entry_count,
                    'current_judges': len(judges_at_table),
                    'certified_judges': certified_count,
                    'beers_per_pair': beers_per_pair,
                    'needs_more_judges': needs_more_judges,
                    'judges_with_conflicts': judges_with_conflicts,
                    'candidates': candidates[:10]  # Top 10 candidates
                })

# Print table analysis
if table_analysis:
    print(f"\n{'='*80}")
    print(f"TABLE STAFFING ANALYSIS")
    print(f"{'='*80}\n")
    
    high_workload = [t for t in table_analysis if t['needs_more_judges']]
    conflict_tables = [t for t in table_analysis if t['judges_with_conflicts']]
    
    if high_workload:
        print(f"⚠️  HIGH WORKLOAD: {len(high_workload)} tables need additional judges (>9 beers/pair):\n")
        for t in high_workload:
            print(f"  • {t['date']} {t['location']} {t['table']}")
            print(f"    Current: {t['entry_count']} entries, {t['certified_judges']} certified judges, {t['current_judges']} total judges")
            print(f"    Workload: {t['beers_per_pair']:.1f} beers per pair")
            
            # Calculate how many more judges needed
            target_beers = 9
            pairs_needed = (t['entry_count'] + target_beers - 1) // target_beers  # Round up
            additional_certified_needed = max(0, pairs_needed - t['certified_judges'])
            
            print(f"    ✓ Need {additional_certified_needed} more certified+ judge(s) to get {pairs_needed} pairs")
            
            if t['candidates']:
                print(f"    Suggested judges (available and not working other tables on {t['date']}):")
                for i, candidate in enumerate(t['candidates'][:3], 1):
                    rank_display = candidate['rank'] if candidate['rank'] else 'Unknown Rank'
                    cert_badge = "✓ Certified+" if candidate['certified'] else "○"
                    print(f"      {i}. {candidate['name']} {cert_badge} [{rank_display}] - {candidate['distance']} mi")
            else:
                print(f"    ⚠️  No available candidates found (all may be working other tables or have conflicts)")
            print()
    
    if conflict_tables:
        print(f"🚫 CONFLICTS: {len(conflict_tables)} tables have judges with entries:\n")
        for t in conflict_tables:
            print(f"  • {t['date']} {t['location']} {t['table']}")
            for jc in t['judges_with_conflicts']:
                print(f"    ⚠️  {jc['name']} entered: {', '.join(jc['conflicts'])}")
            
            print(f"    ✓ MUST replace these {len(t['judges_with_conflicts'])} judge(s)")
            
            if t['candidates']:
                print(f"    Suggested replacements (available and not working other tables on {t['date']}):")
                # Prioritize certified judges for replacements
                certified_candidates = [c for c in t['candidates'] if c['certified']][:3]
                if certified_candidates:
                    for i, candidate in enumerate(certified_candidates, 1):
                        rank_display = candidate['rank'] if candidate['rank'] else 'Unknown Rank'
                        print(f"      {i}. {candidate['name']} ✓ [{rank_display}] - {candidate['distance']} mi")
                else:
                    for i, candidate in enumerate(t['candidates'][:3], 1):
                        rank_display = candidate['rank'] if candidate['rank'] else 'Unknown Rank'
                        cert_badge = "✓" if candidate['certified'] else "○"
                        print(f"      {i}. {candidate['name']} {cert_badge} [{rank_display}] - {candidate['distance']} mi")
            else:
                print(f"    ⚠️  No available replacements found (all may be working other tables or have conflicts)")
            print()
    
    print(f"{'='*80}\n")

# Also analyze individual judge assignments for distance optimization
assignment_analysis = []

for j in judges:
    judge_name = j['name']
    assigned_location = j['location']
    assigned_table = j['table']
    
    # Get distance info for this judge
    dist_info = judge_distances.get(judge_name, {})
    
    if not dist_info:
        continue
    
    # Get distance to assigned location
    location_key = get_location_key(assigned_location)
    assigned_distance = dist_info.get(location_key, 999)
    
    # Find conflicts (styles they entered that are at their assigned table)
    table_substyles = table_styles.get(assigned_table, [])
    judge_substyles = j['substyles']
    conflicts = [s for s in judge_substyles if s in table_substyles]
    
    # Find closer locations without conflicts (only if no conflicts at current location)
    better_options = []
    
    if not conflicts:  # Only suggest moves for judges without conflicts
        for loc in ['DALLAS', 'GRAPEVINE', 'ARLINGTON', 'STUBBIES', 'KELLER']:
            loc_key = get_location_key(loc)
            loc_distance = dist_info.get(loc_key, 999)
            
            # Check if this location is closer and has no conflicts
            if loc_distance < assigned_distance and loc_distance > 0:
                # Find tables at this location on the same date
                tables_at_loc = by_date_loc.get(j['date'], {}).get(loc, {})
                
                # Check each table for conflicts
                for table_num, table_judges in tables_at_loc.items():
                    table_substyles_at_loc = table_styles.get(table_num, [])
                    loc_conflicts = [s for s in judge_substyles if s in table_substyles_at_loc]
                    
                    if not loc_conflicts:
                        better_options.append({
                            'location': loc,
                            'distance': loc_distance,
                            'savings': assigned_distance - loc_distance,
                            'table': table_num
                        })
                        break  # Only need one conflict-free table at this location
    
    if better_options:  # Only track if there are better options
        assignment_analysis.append({
            'judge': judge_name,
            'date': j['date'],
            'current_location': assigned_location,
            'current_table': assigned_table,
            'current_distance': assigned_distance,
            'conflicts': conflicts,
            'better_options': sorted(better_options, key=lambda x: x['distance'])[:3]  # Top 3 closest
        })

# Print distance optimization analysis
if assignment_analysis:
    better_distance = [a for a in assignment_analysis if a['better_options']]
    
    if better_distance:
        print(f"{'='*80}")
        print(f"DISTANCE OPTIMIZATION OPPORTUNITIES")
        print(f"{'='*80}\n")
        print(f"💡 {len(better_distance)} judges could be reassigned to closer locations:")
        total_savings = sum(opt['savings'] for a in better_distance for opt in a['better_options'][:1])
        print(f"   Potential travel savings: ~{total_savings} miles total\n")
        
        for analysis in better_distance[:8]:  # Show first 8
            best = analysis['better_options'][0]
            print(f"  • {analysis['judge']} ({analysis['date']})")
            print(f"    Current: {analysis['current_location']} {analysis['current_table']} ({analysis['current_distance']} mi)")
            print(f"    ✓ Closer: {best['location']} {best['table']} ({best['distance']} mi, saves {best['savings']} mi)")
        if len(better_distance) > 8:
            print(f"  ... and {len(better_distance) - 8} more")
        
        print(f"\n{'='*80}\n")

# =============================================================================
# STEP 7: START BUILDING THE HTML PAGE
# =============================================================================

# This is a multi-line string that contains the beginning of our HTML file
# It includes all the CSS styles that make the page look nice
html = '''<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<title>BBO 2026 Judging Schedule</title>
<style>
/* Main page styling */
body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
.container { max-width: 1400px; margin: 0 auto; }
h1 { text-align: center; color: #2c3e50; }

/* Date section styling */
.date-section { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
.date-header { font-size: 24px; font-weight: bold; margin-bottom: 15px; color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }

/* Location cards in a responsive grid */
.locations { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
.location-card { background: #f8f9fa; border: 2px solid #dee2e6; border-radius: 6px; padding: 15px; }
.location-header { font-size: 18px; font-weight: bold; margin-bottom: 12px; background: #e9ecef; padding: 8px; border-radius: 4px; }

/* Table group styling */
.table-group { background: white; border: 1px solid #dee2e6; border-radius: 4px; padding: 12px; margin-bottom: 10px; }
.table-header { font-weight: bold; margin-bottom: 8px; font-size: 16px; color: #2c3e50; }
.table-category { font-size: 14px; color: #6c757d; margin-bottom: 4px; font-weight: normal; }
.styles-list { font-size: 12px; color: #495057; background: #f8f9fa; padding: 6px 8px; border-radius: 3px; margin-bottom: 8px; line-height: 1.6; }

/* Individual judge styling */
.judge { padding: 6px 10px; margin: 4px 0; border-radius: 4px; font-size: 14px; }

/* Color coding by rank - these match the BJCP certification levels */
.rank-0 { background: #ffc10778;}        /* Non-BJCP: Yellow */
.rank-1 { background: #ff98008c; }       /* Provisional/Pending: Orange */
.rank-2 { background: #ff76008c; color: white; }  /* Recognized: Light Orange */
.rank-3 { background: #2196f3; color: white; }    /* Certified: Blue */
.rank-4 { background: #9c27b0; color: white; }    /* National: Purple */

/* Conflict and warning badges */
.conflict { border: 3px solid #dc3545; background: #fff5f5; }
.conflict-badge { background: #dc3545; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-left: 5px; }
.workload-warning { border: 3px solid #ff9800; background: #fff8e1; }
.workload-badge { background: #ff9800; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; margin-bottom: 8px; display: inline-block; }
.pairing { background: #6c757d; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-left: 5px; }

/* Legend styling */
.legend { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
.legend-items { display: flex; flex-wrap: wrap; gap: 15px; }
.legend-item { display: flex; align-items: center; gap: 8px; }
.legend-box { width: 40px; height: 25px; border-radius: 4px; }

/* Staffing Analysis styling */
.staffing-analysis { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 2px solid #3498db; }
.staffing-analysis h2 { color: #2c3e50; margin-top: 0; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
.staffing-section { margin-bottom: 25px; }
.staffing-section h3 { color: #e74c3c; margin-bottom: 15px; cursor: pointer; user-select: none; }
.staffing-section h3:hover { opacity: 0.8; }
.collapsible-content { overflow: hidden; transition: max-height 0.3s ease; }
.collapsible-content.collapsed { max-height: 0 !important; }
.table-link { color: #2c3e50; text-decoration: none; font-weight: bold; }
.table-link:hover { color: #3498db; text-decoration: underline; }
.back-to-analysis { float: right; font-size: 14px; font-weight: normal; color: #3498db; text-decoration: none; }
.back-to-analysis:hover { text-decoration: underline; }
.staffing-table { background: #fff5f5; border-left: 4px solid #e74c3c; padding: 15px; margin-bottom: 15px; border-radius: 4px; }
.staffing-table.workload { background: #fff8e1; border-left-color: #ff9800; }
.staffing-table.conflict { background: #fff5f5; border-left-color: #dc3545; }
.staffing-header { font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 8px; }
.staffing-details { margin: 8px 0; padding-left: 15px; }
.staffing-details li { margin: 5px 0; list-style: none; }
.staffing-details li:before { content: "• "; color: #3498db; font-weight: bold; }
.conflict-judge { color: #dc3545; font-weight: bold; }
.suggestion { background: #e8f5e9; border-left: 3px solid #4caf50; padding: 10px; margin: 10px 0; border-radius: 3px; }
.suggestion-header { font-weight: bold; color: #2e7d32; margin-bottom: 5px; }
.candidate { padding: 5px 10px; margin: 3px 0; background: white; border-radius: 3px; border: 1px solid #ddd; }
.certified-badge { background: #2196f3; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-left: 5px; }
</style>
<script>
function toggleSection(sectionId) {
  const content = document.getElementById(sectionId);
  const header = document.querySelector('[onclick*="' + sectionId + '"]');
  
  if (content.classList.contains('collapsed')) {
    content.classList.remove('collapsed');
    content.style.maxHeight = content.scrollHeight + "px";
    if (header) header.textContent = header.textContent.replace('▶', '▼');
  } else {
    content.classList.add('collapsed');
    content.style.maxHeight = "0px";
    if (header) header.textContent = header.textContent.replace('▼', '▶');
  }
}
// Initialize collapsible sections to be open
//window.addEventListener('DOMContentLoaded', function() {
//  document.querySelectorAll('.collapsible-content').forEach(function(content) {
//    content.style.maxHeight = content.scrollHeight + "px";
//  });
//});
</script>
</head>
<body>
<div class="container">
<h1>🍺 BBO 2026 Judging Schedule</h1>

<!-- Legend showing what each color means -->
<div class="legend">
<h3>Judge Rank Legend</h3>
<div class="legend-items">
<div class="legend-item"><div class="legend-box rank-0"></div><span>Non-BJCP</span></div>
<div class="legend-item"><div class="legend-box rank-1"></div><span>Rank Pending/Provisional</span></div>
<div class="legend-item"><div class="legend-box rank-2"></div><span>Recognized</span></div>
<div class="legend-item"><div class="legend-box rank-3"></div><span>Certified</span></div>
<div class="legend-item"><div class="legend-box rank-4"></div><span>National</span></div>
</div>
<h3 style="margin-top: 20px;">Table Warnings</h3>
<div class="legend-items">
<div class="legend-item"><div class="legend-box conflict" style="border: 3px solid #dc3545; background: #fff5f5;"></div><span>Judge entered beer in style being judged</span></div>
<div class="legend-item"><div class="legend-box workload-warning" style="border: 3px solid #ff9800; background: #fff8e1;"></div><span>Certified pairs evaluating >9 beers each</span></div>
</div>
</div>
'''

# =============================================================================
# ADD TABLE STAFFING ANALYSIS TO HTML
# =============================================================================

if table_analysis:
    html += '<div class="staffing-analysis" id="staffing-analysis">'
    html += '<h2>⚠️ Table Staffing Analysis</h2>'
    html += '<p style="color: #6c757d; font-style: italic; margin-bottom: 20px;">💡 Click on <strong>High Workload Tables</strong> or <strong>Conflict Tables</strong> below to expand or collapse it.</p>'
    
    high_workload = [t for t in table_analysis if t['needs_more_judges']]
    conflict_tables = [t for t in table_analysis if t['judges_with_conflicts']]
    
    if high_workload:
        html += '<div class="staffing-section">'
        html += f'<h3 onclick="toggleSection(\'workload-content\')" style="cursor: pointer;">▼ High Workload Tables ({len(high_workload)} tables need additional judges)</h3>'
        html += '<div id="workload-content" class="collapsible-content collapsed">'
        
        for t in high_workload:
            html += '<div class="staffing-table workload">'
            html += f'<div class="staffing-header"><a href="#{t["table"]}" class="table-link">{t["date"]} {t["location"]} {t["table"]}</a></div>'
            html += '<ul class="staffing-details">'
            html += f'<li><strong>Current:</strong> {t["entry_count"]} entries, {t["certified_judges"]} certified judges, {t["current_judges"]} total judges</li>'
            html += f'<li><strong>Workload:</strong> {t["beers_per_pair"]:.1f} beers per pair (exceeds recommended 9)</li>'
            
            # Calculate how many more judges needed
            target_beers = 9
            pairs_needed = (t['entry_count'] + target_beers - 1) // target_beers
            additional_certified_needed = max(0, pairs_needed - t['certified_judges'])
            
            html += f'<li><strong>Need:</strong> {additional_certified_needed} more certified+ judge(s) to create {pairs_needed} pairs</li>'
            html += '</ul>'
            
            if t['candidates']:
                html += '<div class="suggestion">'
                html += f'<div class="suggestion-header">Suggested Judges (available and not working other tables on {t["date"]})::</div>'
                for i, candidate in enumerate(t['candidates'][:3], 1):
                    rank_display = candidate['rank'] if candidate['rank'] else 'Unknown Rank'
                    cert_badge = '<span class="certified-badge">✓ Certified+</span>' if candidate['certified'] else '<span style="color: #999;">○</span>'
                    html += f'<div class="candidate">{i}. {candidate["name"]} {cert_badge} <span style="color: #666; font-size: 0.9em;">[{rank_display}]</span> - {candidate["distance"]} mi</div>'
                html += '</div>'
            else:
                html += '<div class="suggestion" style="background: #ffebee; border-left-color: #f44336;">⚠️ No available candidates found (all may be working other tables or have conflicts)</div>'
            
            html += '</div>'
        
        html += '</div></div>'
    
    if conflict_tables:
        html += '<div class="staffing-section">'
        html += f'<h3 onclick="toggleSection(\'conflict-content\')" style="cursor: pointer;">▼ 🚫 Conflict Tables ({len(conflict_tables)} tables have judges with entries)</h3>'
        html += '<div id="conflict-content" class="collapsible-content collapsed">'
        
        for t in conflict_tables:
            html += '<div class="staffing-table conflict">'
            html += f'<div class="staffing-header"><a href="#{t["table"]}" class="table-link">{t["date"]} {t["location"]} {t["table"]}</a></div>'
            html += '<ul class="staffing-details">'
            
            for jc in t['judges_with_conflicts']:
                conflicts_str = ', '.join(jc['conflicts'])
                html += f'<li><span class="conflict-judge">{jc["name"]}</span> entered: {conflicts_str}</li>'
            
            html += f'<li><strong>Action Required:</strong> MUST replace these {len(t["judges_with_conflicts"])} judge(s)</li>'
            html += '</ul>'
            
            if t['candidates']:
                html += '<div class="suggestion">'
                html += f'<div class="suggestion-header">Suggested Replacements (available and not working other tables on {t["date"]}):</div>'
                certified_candidates = [c for c in t['candidates'] if c['certified']][:3]
                candidates_to_show = certified_candidates if certified_candidates else t['candidates'][:3]
                
                for i, candidate in enumerate(candidates_to_show, 1):
                    rank_display = candidate['rank'] if candidate['rank'] else 'Unknown Rank'
                    cert_badge = '<span class="certified-badge">✓ Certified+</span>' if candidate['certified'] else '<span style="color: #999;">○</span>'
                    html += f'<div class="candidate">{i}. {candidate["name"]} {cert_badge} <span style="color: #666; font-size: 0.9em;">[{rank_display}]</span> - {candidate["distance"]} mi</div>'
                html += '</div>'
            else:
                html += '<div class="suggestion" style="background: #ffebee; border-left-color: #f44336;">⚠️ No available replacements found (all may be working other tables or have conflicts)</div>'
            
            html += '</div>'
        
        html += '</div></div>'
    
    html += '</div>'

# =============================================================================
# STEP 8: DEFINE RANK MAPPING
# =============================================================================

# This dictionary maps rank names to numeric levels (0-4)
# We use numbers so we can easily assign colors in the HTML
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
    'national': 4,
    'Level 4: National': 4
}

def is_certified_or_higher(rank):
    """Check if a rank is Certified (Level 3) or higher."""
    rank_level = RANKS.get(rank, 0)
    return rank_level >= 3

# =============================================================================
# STEP 9: GENERATE HTML FOR EACH DATE/LOCATION/TABLE
# =============================================================================

# Loop through each date in chronological order
for date in sorted(by_date_loc.keys()):
    # Start a new date section
    html += f'<div class="date-section"><div class="date-header">{date} <a href="#staffing-analysis" class="back-to-analysis">↑ Back to Analysis</a></div><div class="locations">'
    
    # Loop through each location for this date (alphabetically)
    for location in sorted(by_date_loc[date].keys()):
        # Start a new location card
        html += f'<div class="location-card"><div class="location-header">{location}</div>'
        
        # Loop through each table at this location (numerically)
        for table in sorted(by_date_loc[date][location].keys()):
            # Get all judges assigned to this table
            judges_at_table = by_date_loc[date][location][table]
            
            # Get the list of BJCP styles for this table
            styles = table_styles.get(table, [])
            
            # -------------------------------------------------------------
            # CHECK FOR CONFLICTS
            # A conflict occurs when a judge entered a beer in a style
            # they're assigned to judge
            # -------------------------------------------------------------
            has_conflict = False
            for j in judges_at_table:
                # Check if any of this judge's entered styles match
                # any of the styles being judged at this table
                if any(s in styles for s in j['substyles']):
                    has_conflict = True
                    break
            
            # -------------------------------------------------------------
            # CHECK FOR WORKLOAD ISSUES
            # BJCP recommends max 12 beers per pair, warn at > 9
            # -------------------------------------------------------------
            has_workload_warning = False
            workload_info = ''
            
            # Count certified+ judges at this table
            certified_judges = [j for j in judges_at_table if is_certified_or_higher(j['rank'])]
            certified_count = len(certified_judges)
            non_certified_count = len(judges_at_table) - certified_count
            
            # Get entry count for this table
            entry_count = table_entry_counts.get(table, 0)
            
            if entry_count > 0 and certified_count >= 1:
                # Each certified+ judge forms one qualified pair (paired with a non-certified judge)
                # Number of qualified pairs = number of certified+ judges
                num_pairs = certified_count
                
                # Calculate beers per pair
                beers_per_pair = entry_count / num_pairs if num_pairs > 0 else entry_count
                
                # Flag if exceeds 9 beers per pair
                if beers_per_pair > 9:
                    has_workload_warning = True
                    workload_info = f'⚠️ {int(beers_per_pair)} beers/pair ({entry_count} entries ÷ {num_pairs} qualified pairs) • {certified_count} Certified+ • {non_certified_count} Below Certified'
            
            # Add 'conflict' or 'workload-warning' CSS class if there's a problem
            warning_class = ''
            if has_conflict:
                warning_class = ' conflict'
            elif has_workload_warning:
                warning_class = ' workload-warning'
            
            # -------------------------------------------------------------
            # PREPARE TABLE DISPLAY INFO
            # -------------------------------------------------------------
            
            # Get the BBO Medal category name for this table
            category_name = table_names.get(table, '')
            category_display = f'<div class="table-category">{category_name}</div>' if category_name else ''
            
            # Create a display string of all BJCP styles for this table
            styles_display = ''
            if styles:
                # Sort the style IDs and join them with commas
                styles_str = ', '.join(sorted(styles))
                styles_display = f'<div class="styles-list"><strong>BJCP Styles:</strong> {styles_str}</div>'
            
            # Create entry count display
            entry_display = ''
            if entry_count > 0:
                entry_display = f'<div class="styles-list"><strong>Entries:</strong> {entry_count}</div>'
            
            # Create workload warning badge if needed
            workload_display = ''
            if has_workload_warning:
                workload_display = f'<div class="workload-badge">{workload_info}</div>'
            
            # Start the table group HTML with header and styles (add ID for linking)
            html += f'<div class="table-group{warning_class}" id="{table}"><div class="table-header">{table} <a href="#staffing-analysis" class="back-to-analysis" style="float: right; font-size: 12px;">↑ Back to Analysis</a></div>{category_display}{workload_display}{styles_display}{entry_display}'
            
            # -------------------------------------------------------------
            # ADD EACH JUDGE TO THE TABLE
            # -------------------------------------------------------------
            for j in judges_at_table:
                # Get the numeric rank level for color coding
                rank_level = RANKS.get(j['rank'], 0)
                
                # Find which specific styles this judge entered that conflict
                conflicts = [s for s in j['substyles'] if s in styles]
                
                # Create a conflict badge if there are any conflicts
                conflict_badge = f'<span class="conflict-badge">⚠ {", ".join(conflicts)}</span>' if conflicts else ''
                
                # Create a pairing badge if this judge has a pairing number
                pairing_badge = f'<span class="pairing">Pair {j["pairing"]}</span>' if j.get('pairing') and j['pairing'].strip() else ''
                
                # Add this judge's HTML to the page
                html += f'<div class="judge rank-{rank_level}">{j["name"]} {pairing_badge}{conflict_badge}<br><small>{j["rank"]}</small></div>'
            
            # Close the table group
            html += '</div>'
        
        # Close the location card
        html += '</div>'
    
    # Close the locations grid and date section
    html += '</div></div>'

# Close the container and HTML document
html += '</div></body></html>'

# =============================================================================
# STEP 10: WRITE THE HTML FILE
# =============================================================================

# Write the complete HTML string to a file
with open('judging_schedule.html', 'w', encoding='utf-8') as f:
    f.write(html)

# =============================================================================
# STEP 11: GENERATE PDF VERSION
# =============================================================================

if PDF_AVAILABLE:
    try:
        print("\nGenerating PDF...")
        HTML('judging_schedule.html').write_pdf('judging_schedule.pdf')
        print("✅ Generated judging_schedule.pdf")
    except Exception as e:
        print(f"⚠️  Could not generate PDF: {e}")
else:
    print("\n⚠️  WeasyPrint not installed. To generate PDF, run:")
    print("   pip install weasyprint")

# =============================================================================
# STEP 12: DISPLAY SUMMARY INFORMATION
# =============================================================================

print(f"\n✅ Generated judging_schedule.html")
print(f"Found {len(judges)} total assignments")
print(f"Unique judges: {len(set(j['name'] for j in judges))}")
