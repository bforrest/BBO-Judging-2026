#!/usr/bin/env python3
"""Simple BBO 2026 Schedule Generator"""

import csv
from collections import defaultdict

# Load judges
judges = []
with open("Judges and Tables.tsv", 'r', encoding='utf-8') as f:
    next(f)  # Skip blank first line
    reader = csv.DictReader(f, delimiter='\t')
    
    for row in reader:
        name = row.get('FULL NAME', '').strip('"')
        if not name or not row.get('DESIRED TABLE TO JUDGE'):
            continue
            
        # Parse table info
        table_str = row.get('DESIRED TABLE TO JUDGE', '')
        if 'no table' in table_str.lower():
            continue
            
        # Extract date, location, table
        import re
        match = re.match(r'(\d{2}/\d{2})\s+(\w+)\s+T(\d+)', table_str)
        if not match:
            continue
            
        date, location, table_num = match.groups()
        
        # Parse substyles
        substyles_str = row.get('SUBSTYLES ENTERED', '').strip('"')
        substyles = [s.strip() for s in substyles_str.split(',') if s.strip()]
        
        judges.append({
            'name': name,
            'date': date,
            'location': location.upper(),
            'table': f'T{table_num}',
            'pairing': row.get('PAIRING', '').strip(),
            'rank': row.get('RANKING', '').strip(),
            'substyles': substyles
        })

print(f"Loaded {len(judges)} judge assignments")

# Load table styles
table_styles = defaultdict(list)
with open("styles by table.csv", 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        table = row.get('Table Number', '').strip()
        style = row.get('BJCP Style Id', '').strip()
        if table and style:
            table_styles[f'T{table}'].append(style)

print(f"Loaded {len(table_styles)} table mappings")

# Organize by date/location
by_date_loc = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
for j in judges:
    by_date_loc[j['date']][j['location']][j['table']].append(j)

# Generate HTML
html = '''<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<title>BBO 2026 Judging Schedule</title>
<style>
body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
.container { max-width: 1400px; margin: 0 auto; }
h1 { text-align: center; color: #2c3e50; }
.date-section { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
.date-header { font-size: 24px; font-weight: bold; margin-bottom: 15px; color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
.locations { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
.location-card { background: #f8f9fa; border: 2px solid #dee2e6; border-radius: 6px; padding: 15px; }
.location-header { font-size: 18px; font-weight: bold; margin-bottom: 12px; background: #e9ecef; padding: 8px; border-radius: 4px; }
.table-group { background: white; border: 1px solid #dee2e6; border-radius: 4px; padding: 12px; margin-bottom: 10px; }
.table-header { font-weight: bold; margin-bottom: 8px; font-size: 16px; color: #2c3e50; }
.judge { padding: 6px 10px; margin: 4px 0; border-radius: 4px; font-size: 14px; }
.rank-0 { background: #ffc107; }
.rank-1 { background: #ff9800; }
.rank-2 { background: #4caf50; color: white; }
.rank-3 { background: #2196f3; color: white; }
.rank-4 { background: #9c27b0; color: white; }
.conflict { border: 3px solid #dc3545; background: #fff5f5; }
.conflict-badge { background: #dc3545; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-left: 5px; }
.pairing { background: #6c757d; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-left: 5px; }
.legend { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
.legend-items { display: flex; flex-wrap: wrap; gap: 15px; }
.legend-item { display: flex; align-items: center; gap: 8px; }
.legend-box { width: 40px; height: 25px; border-radius: 4px; }
</style>
</head>
<body>
<div class="container">
<h1>🍺 BBO 2026 Judging Schedule</h1>

<div class="legend">
<h3>Judge Rank Legend</h3>
<div class="legend-items">
<div class="legend-item"><div class="legend-box rank-0"></div><span>Non-BJCP</span></div>
<div class="legend-item"><div class="legend-box rank-1"></div><span>Rank Pending/Provisional</span></div>
<div class="legend-item"><div class="legend-box rank-2"></div><span>Recognized</span></div>
<div class="legend-item"><div class="legend-box rank-3"></div><span>Certified</span></div>
<div class="legend-item"><div class="legend-box rank-4"></div><span>National</span></div>
</div>
</div>
'''

# Rank mapping
RANKS = {
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

# Add data
for date in sorted(by_date_loc.keys()):
    html += f'<div class="date-section"><div class="date-header">{date}</div><div class="locations">'
    
    for location in sorted(by_date_loc[date].keys()):
        html += f'<div class="location-card"><div class="location-header">{location}</div>'
        
        for table in sorted(by_date_loc[date][location].keys()):
            judges_at_table = by_date_loc[date][location][table]
            styles = table_styles.get(table, [])
            
            # Check conflicts
            has_conflict = False
            for j in judges_at_table:
                if any(s in styles for s in j['substyles']):
                    has_conflict = True
                    break
            
            conflict_class = ' conflict' if has_conflict else ''
            html += f'<div class="table-group{conflict_class}"><div class="table-header">{table}</div>'
            
            for j in judges_at_table:
                rank_level = RANKS.get(j['rank'], 0)
                conflicts = [s for s in j['substyles'] if s in styles]
                conflict_badge = f'<span class="conflict-badge">⚠ {", ".join(conflicts)}</span>' if conflicts else ''
                pairing_badge = f'<span class="pairing">Pair {j["pairing"]}</span>' if j['pairing'] else ''
                
                html += f'<div class="judge rank-{rank_level}">{j["name"]} {pairing_badge}{conflict_badge}<br><small>{j["rank"]}</small></div>'
            
            html += '</div>'
        
        html += '</div>'
    
    html += '</div></div>'

html += '</div></body></html>'

# Write output
with open('judging_schedule.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n✅ Generated judging_schedule.html")
print(f"Found {len(judges)} total assignments")
print(f"Unique judges: {len(set(j['name'] for j in judges))}")
