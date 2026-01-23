# BBO 2026 Judge Optimization Tools - Quick Reference

## Overview

You now have three powerful tools to optimize your judging schedule:

### 1. **optimize_judge_pairings.py** - Full Analysis
Provides detailed analysis of all judging sites with:
- Workload calculations (beers per pair)
- Pairing quality assessment
- Entry conflict detection
- Specific pairing suggestions
- Prioritized recommendations

**Run:** `python3 optimize_judge_pairings.py`

**Output:** Console display + `optimization_output.txt`

**Use when:** You want comprehensive analysis and specific pairing recommendations for every table

---

### 2. **generate_recommendations.py** - Executive Summary
Creates a concise, actionable report organized by priority:
- 🚨 Critical tables (need immediate attention)
- ⚠️  Overworked tables (>12 beers/pair)
- 🔄 Entry conflicts (judges evaluating own beers)
- 📊 Pairing imbalances
- 📈 Summary statistics

**Run:** `python3 generate_recommendations.py`

**Output:** `JUDGE_RECOMMENDATIONS.md` (Markdown format)

**Use when:** You need a prioritized action list for decision-making

---

### 3. **generate_optimized_schedule.py** - Visual Schedule
Generates the interactive HTML visualization with:
- Color-coded judge rankings
- Conflict warnings (red borders)
- Workload warnings (orange borders)
- Site-specific pages
- Interactive filtering

**Run:** `python3 generate_optimized_schedule.py`

**Output:** `judging_schedule.html` + site-specific pages

**Use when:** You want to view or share the current schedule visually

---

## Key Optimization Rules

### Pairing Requirements
- **Rule 1:** Non-certified judges (rank < 3) **MUST** be paired with certified judges (rank ≥ 3)
- **Rule 2:** Ideal workload is **9 beers per pair** (max 12, critical if >15)
- **Rule 3:** Judges **cannot evaluate their own entries**

### Judge Rankings (by weight)
| Rank | Weight | Can Lead Pair? |
|------|--------|----------------|
| Non-BJCP | 0 | ❌ No |
| Non-BJCP + Sensory Training | 0 | ❌ No |
| Non-BJCP + Certified Cicerone | 0 | ❌ No |
| Provisional + Sensory Training | 1 | ❌ No |
| Rank Pending | 2 | ❌ No |
| Recognized | 2 | ❌ No |
| Recognized + Sensory Training | 2 | ❌ No |
| **Certified** | 3 | ✅ Yes |
| **Certified + Sensory Training** | 3 | ✅ Yes |
| **Certified + Professional Brewer** | 3 | ✅ Yes |
| **National** | 4 | ✅ Yes |
| **National + Advanced Cicerone** | 4 | ✅ Yes |

---

## Quick Start Workflow

### Step 1: Review Current Status
```bash
python3 generate_recommendations.py
cat JUDGE_RECOMMENDATIONS.md
```
Look at the priority sections to understand the biggest issues.

### Step 2: Analyze Specific Tables
```bash
python3 optimize_judge_pairings.py > detailed_analysis.txt
```
Search for specific table numbers to see detailed pairing suggestions.

### Step 3: Make Adjustments
Edit `Judges and Tables.tsv` to:
- Add certified judges to critical tables
- Reassign judges with entry conflicts
- Balance certified/non-certified ratios

### Step 4: Regenerate and Verify
```bash
# Update judges_by_site.csv if you edited the TSV
python3 judges_by_site.py

# Regenerate recommendations
python3 generate_recommendations.py

# Regenerate HTML visualization
python3 generate_optimized_schedule.py

# Open the updated schedule
open judging_schedule.html
```

---

## Current Priority Issues

### 🚨 CRITICAL (2 tables)
1. **T88 Dallas Specialty Beer** - Only 1 certified judge, 36 entries
   - ACTION: Add 2 certified judges immediately
   
2. **T93 Grapevine Specialty Cider** - Only 1 certified judge, 36 entries
   - ACTION: Add 2 certified judges immediately

### 🔄 HIGH PRIORITY (13 tables with conflicts)
Multiple judges are assigned to tables where they entered beers. Most notable:
- **Brian Street** has conflicts at 9+ different tables
- **John Skelton, Mark McCurdy, Tony Silveira, Joshua Hayes** have conflicts

**ACTION:** Reassign these judges to tables where they have no entries

### 📊 MEDIUM PRIORITY (5 tables with pairing imbalances)
Several tables have too many non-certified judges relative to certified judges.
- T68 Arlington American Pale Ale: 3C vs 10NC (need +2 certified)
- T80 Dallas Strong Light Belgian: 3C vs 8NC (need +1 certified)

---

## Tips for Optimization

1. **Prioritize Certified Judges:** Focus on tables with highest entry counts first
   
2. **Minimize Judge Movement:** When fixing conflicts, try swapping judges between similar tables/dates

3. **Consider Geography:** Use judge distance data (if available in JUDGE WORKSHEET 2026.csv)

4. **Balance Workload:** Aim for 8-10 beers per pair across all tables

5. **Experience Pairing:** Try to pair highest-ranked non-certified (Recognized) with Certified judges

6. **Check After Changes:** Always re-run the optimization scripts after making changes

---

## File Reference

### Input Files
- `Judges and Tables.tsv` - Master judge assignments
- `medal_category_counts.csv` - Entry counts per table
- `styles by table.csv` - BJCP style mappings
- `JUDGE WORKSHEET 2026.csv` - Judge roster with distances (optional)

### Generated Files
- `judges_by_site.csv` - Parsed judge data by site
- `optimization_output.txt` - Detailed pairing analysis
- `JUDGE_RECOMMENDATIONS.md` - Executive summary report
- `judging_schedule.html` - Interactive visualization
- `judging_schedule_[site].html` - Site-specific pages

---

## Questions?

- **How many certified judges do I need per table?**  
  Minimum: 1 certified per 2 non-certified  
  Optimal: Entry count ÷ 18 (assuming 2 judges per pair, 9 beers/pair)
  
- **What if I can't fix all conflicts?**  
  Prioritize: Critical workload issues > Entry conflicts > Pairing ratios
  
- **Can two certified judges judge together?**  
  Yes! If you have extra certified judges, pairing them together is fine.
  
- **How do I handle judges with sensory training?**  
  They're still ranked at their base level (0-2) and need certified partners.

---

*Last updated: January 23, 2026*
