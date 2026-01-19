#!/usr/bin/env python3
"""
BBO 2026 Judging Schedule Visualizer
Generates an interactive HTML page showing judge assignments with conflict detection.
"""

import csv
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# Define rank hierarchy
RANK_ORDER = {
    'Level 0: Non-BJCP': 0,
    'Level 1: Rank Pending': 1,
    'Level 1: Provisional': 1,
    'Level 2: Recognized': 2,
    'Level 3: Certified': 3,
    'certified': 3,
    'Certified+ Mead': 3,
    'Certified+Mead': 3,
    'Certified+Mead+cider': 3,
    'national': 4,
    'Level 4: National': 4
}

def parse_table_from_desired(desired_str: str) -> Tuple[str, str, str]:
    """Extract date, location, and table from 'DESIRED TABLE TO JUDGE' field."""
    if not desired_str or desired_str == 'no table identified yet':
        return None, None, None
    
    # Pattern: "02/06 Arlington T68 American Pale Ale"
    match = re.match(r'(\d{2}/\d{2})\s+(\w+)\s+T(\d+)', desired_str)
    if match:
        date, location, table = match.groups()
        return date, location, f"T{table}"
    return None, None, None

def load_judges(filepath: str) -> List[Dict]:
    """Load judge data from TSV file."""
    judges = []
    with open(filepath, 'r', encoding='utf-8') as f:
        # Skip the first blank line
        next(f)
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if not row.get('FULL NAME'):
                continue
            
            # Parse their substyles entered
            substyles_str = row.get('SUBSTYLES ENTERED', '')
            # Remove quotes and split by comma
            substyles = []
            if substyles_str:
                substyles_str = substyles_str.strip('"')
                substyles = [s.strip() for s in substyles_str.split(',') if s.strip()]
            
            date, location, table = parse_table_from_desired(row.get('DESIRED TABLE TO JUDGE', ''))
            
            judges.append({
                'name': row['FULL NAME'].strip('"'),
                'table': row.get('DESIRED TABLE TO JUDGE', ''),
                'date': date,
                'location': location,
                'table_num': table,
                'pairing': row.get('PAIRING', ''),
                'bjcp_id': row.get('BJCP ID', ''),
                'ranking': row.get('RANKING', ''),
                'substyles': substyles
            })
    
    return judges

def load_table_styles(filepath: str) -> Dict[str, List[str]]:
    """Load mapping of table numbers to BJCP styles."""
    table_styles = defaultdict(list)
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            table = row.get('Table Number', '').strip()
            style = row.get('BJCP Style Id', '').strip()
            if table and style:
                table_styles[f"T{table}"].append(style)
    
    return dict(table_styles)

def load_schedule(filepath: str) -> Dict:
    """Load judging schedule."""
    schedule = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header
        
        for row in reader:
            if len(row) < 2 or not row[0]:
                continue
            
            date = row[0]
            day = row[1] if len(row) > 1 else ''
            
            # Parse locations (columns 2-5)
            locations = {}
            location_names = ['ARLINGTON', 'DALLAS', 'GRAPEVINE', 'KELLER']
            for i, loc_name in enumerate(location_names):
                if len(row) > i + 2 and row[i + 2]:
                    locations[loc_name] = row[i + 2]
            
            if locations:
                schedule[date] = {
                    'day': day,
                    'locations': locations
                }
    
    return schedule

def check_conflicts(judge: Dict, table_styles: List[str]) -> List[str]:
    """Check if judge has entered any substyles for this table."""
    conflicts = []
    for substyle in judge['substyles']:
        if substyle in table_styles:
            conflicts.append(substyle)
    return conflicts

def check_pairing_issue(judges_at_table: List[Dict]) -> List[str]:
    """Check if pairing follows rules (Level 3+ required for lower ranks)."""
    issues = []
    
    # Group by pairing number
    pairings = defaultdict(list)
    for judge in judges_at_table:
        pairing = judge['pairing'] or 'unpaired'
        pairings[pairing].append(judge)
    
    for pairing_num, judges in pairings.items():
        if pairing_num == 'unpaired':
            continue
        
        # Check if any judge is below Level 3
        has_low_rank = any(RANK_ORDER.get(j['ranking'], 0) < 3 for j in judges)
        has_certified = any(RANK_ORDER.get(j['ranking'], 0) >= 3 for j in judges)
        
        if has_low_rank and not has_certified:
            judge_names = ', '.join(j['name'] for j in judges)
            issues.append(f"Pairing {pairing_num} ({judge_names}) needs a Level 3+ Certified judge")
    
    return issues

def generate_html(judges: List[Dict], table_styles: Dict, schedule: Dict) -> str:
    """Generate HTML visualization."""
    
    # Organize judges by date and location
    by_date_location = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
    for judge in judges:
        if judge['date'] and judge['location'] and judge['table_num']:
            date = judge['date']
            location = judge['location'].upper()
            table = judge['table_num']
            by_date_location[date][location][table].append(judge)
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BBO 2026 Judging Schedule</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }
        .date-section {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .date-header {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 3px solid #3498db;
        }
        .locations {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .location-card {
            background: #f8f9fa;
            border: 2px solid #dee2e6;
            border-radius: 6px;
            padding: 15px;
        }
        .location-header {
            font-size: 18px;
            font-weight: bold;
            color: #495057;
            margin-bottom: 12px;
            padding: 8px;
            background: #e9ecef;
            border-radius: 4px;
        }
        .table-group {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 12px;
            margin-bottom: 10px;
        }
        .table-header {
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
            font-size: 16px;
        }
        .judge {
            padding: 6px 10px;
            margin: 4px 0;
            border-radius: 4px;
            font-size: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .judge-name {
            font-weight: 500;
        }
        .judge-rank {
            font-size: 12px;
            opacity: 0.7;
        }
        .rank-0 { background: #ffc107; color: #000; }
        .rank-1 { background: #ff9800; color: #000; }
        .rank-2 { background: #4caf50; color: white; }
        .rank-3 { background: #2196f3; color: white; }
        .rank-4 { background: #9c27b0; color: white; }
        .pairing {
            display: inline-block;
            background: #6c757d;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            margin-left: 5px;
        }
        .conflict {
            border: 3px solid #dc3545;
            background: #fff5f5;
        }
        .conflict-badge {
            background: #dc3545;
            color: white;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 11px;
            margin-left: 5px;
            font-weight: bold;
        }
        .issue {
            background: #fff3cd;
            border: 1px solid #ffc107;
            color: #856404;
            padding: 8px;
            border-radius: 4px;
            margin-top: 8px;
            font-size: 12px;
        }
        .legend {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .legend h3 {
            margin-top: 0;
        }
        .legend-items {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .legend-box {
            width: 40px;
            height: 25px;
            border-radius: 4px;
        }
        .stats {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .stat-item {
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
            text-align: center;
        }
        .stat-number {
            font-size: 32px;
            font-weight: bold;
            color: #3498db;
        }
        .stat-label {
            font-size: 14px;
            color: #6c757d;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🍺 BBO 2026 Judging Schedule</h1>
"""
    
    # Calculate statistics
    total_judges = len([j for j in judges if j['date']])
    unique_judges = len(set(j['name'] for j in judges if j['date']))
    total_conflicts = 0
    total_pairing_issues = 0
    
    # Add legend
    html += """
        <div class="legend">
            <h3>Judge Rank Legend</h3>
            <div class="legend-items">
                <div class="legend-item">
                    <div class="legend-box rank-0"></div>
                    <span>Non-BJCP</span>
                </div>
                <div class="legend-item">
                    <div class="legend-box rank-1"></div>
                    <span>Rank Pending/Provisional</span>
                </div>
                <div class="legend-item">
                    <div class="legend-box rank-2"></div>
                    <span>Recognized</span>
                </div>
                <div class="legend-item">
                    <div class="legend-box rank-3"></div>
                    <span>Certified</span>
                </div>
                <div class="legend-item">
                    <div class="legend-box rank-4"></div>
                    <span>National</span>
                </div>
            </div>
        </div>
"""
    
    # Process each date
    for date in sorted(by_date_location.keys()):
        schedule_info = schedule.get(date, {})
        day = schedule_info.get('day', '')
        
        html += f"""
        <div class="date-section">
            <div class="date-header">{date} - {day}</div>
            <div class="locations">
"""
        
        for location in sorted(by_date_location[date].keys()):
            html += f"""
                <div class="location-card">
                    <div class="location-header">{location}</div>
"""
            
            for table in sorted(by_date_location[date][location].keys()):
                judges_at_table = by_date_location[date][location][table]
                table_style_list = table_styles.get(table, [])
                
                # Check for conflicts
                has_conflict = False
                pairing_issues = check_pairing_issue(judges_at_table)
                
                conflict_class = ""
                for judge in judges_at_table:
                    conflicts = check_conflicts(judge, table_style_list)
                    if conflicts:
                        has_conflict = True
                        total_conflicts += 1
                        conflict_class = " conflict"
                        break
                
                if pairing_issues:
                    total_pairing_issues += len(pairing_issues)
                
                html += f"""
                    <div class="table-group{conflict_class}">
                        <div class="table-header">{table}</div>
"""
                
                # List judges
                for judge in judges_at_table:
                    rank_level = RANK_ORDER.get(judge['ranking'], 0)
                    conflicts = check_conflicts(judge, table_style_list)
                    conflict_badge = ""
                    if conflicts:
                        conflict_badge = f'<span class="conflict-badge">⚠ CONFLICT: {", ".join(conflicts)}</span>'
                    
                    pairing_badge = ""
                    if judge['pairing']:
                        pairing_badge = f'<span class="pairing">Pair {judge["pairing"]}</span>'
                    
                    html += f"""
                        <div class="judge rank-{rank_level}">
                            <div>
                                <span class="judge-name">{judge['name']}</span>
                                {pairing_badge}
                                {conflict_badge}
                            </div>
                            <span class="judge-rank">{judge['ranking']}</span>
                        </div>
"""
                
                # Show pairing issues
                for issue in pairing_issues:
                    html += f'<div class="issue">⚠ {issue}</div>'
                
                html += """
                    </div>
"""
            
            html += """
                </div>
"""
        
        html += """
            </div>
        </div>
"""
    
    # Add statistics at the end
    html += f"""
        <div class="stats">
            <h3>Summary Statistics</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-number">{unique_judges}</div>
                    <div class="stat-label">Unique Judges</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{total_judges}</div>
                    <div class="stat-label">Total Assignments</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{total_conflicts}</div>
                    <div class="stat-label">Entry Conflicts</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{total_pairing_issues}</div>
                    <div class="stat-label">Pairing Issues</div>
                </div>
            </div>
        </div>
"""
    
    html += """
    </div>
</body>
</html>
"""
    
    return html

def main():
    base_path = Path(__file__).parent
    
    # Load data
    print("Loading data...")
    judges = load_judges(base_path / "Judges and Tables.tsv")
    table_styles = load_table_styles(base_path / "styles by table.csv")
    schedule = load_schedule(base_path / "JUDGING SCHEDULE.csv")
    
    print(f"Loaded {len(judges)} judge assignments")
    print(f"Loaded {len(table_styles)} table style mappings")
    print(f"Loaded {len(schedule)} scheduled dates")
    
    # Generate HTML
    print("Generating visualization...")
    html = generate_html(judges, table_styles, schedule)
    
    # Write output
    output_file = base_path / "judging_schedule.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ Visualization created: {output_file}")
    print(f"\nOpen {output_file.name} in your web browser to view the schedule.")

if __name__ == "__main__":
    main()
