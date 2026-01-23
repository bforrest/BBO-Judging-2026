# ⚡ QUICK REFERENCE CARD

## Run These Commands

### 1️⃣ See Executive Summary (START HERE)
```bash
cat JUDGE_RECOMMENDATIONS.md
```
Priorities: Critical → Conflicts → Overworked → Imbalanced

### 2️⃣ Open Excel Worksheet
```bash
open PAIRING_WORKSHEET.csv
```
Filter by "Action Needed" column to find what to fix

### 3️⃣ Get Full Analysis
```bash
python3 optimize_judge_pairings.py > analysis.txt
cat analysis.txt | head -100  # See first 100 lines
```
Search for specific table numbers (T68, T77, etc.)

### 4️⃣ Update After Changes
```bash
python3 judges_by_site.py          # Regenerate site list
python3 generate_recommendations.py # Check progress
python3 generate_optimized_schedule.py # Update HTML
open judging_schedule.html          # View changes
```

---

## Key Rules

| Rule | Details |
|------|---------|
| **Pairing** | Non-certified (rank <3) MUST pair with certified (rank ≥3) |
| **Workload** | Ideal: 9 beers/pair, Max: 12, Critical: >15 |
| **Conflicts** | Judge cannot evaluate their own entered beer |
| **Minimum** | At least 1 certified judge per 2 non-certified |

---

## Critical Issues

### 🚨 Tables Needing Immediate Attention
- **T88 Dallas Specialty Beer:** 1 certified, 36 entries → **ADD 2 CERTIFIED**
- **T93 Grapevine Specialty Cider:** 1 certified, 36 entries → **ADD 2 CERTIFIED**

### 🔄 Most Conflicted Judge
- **Brian Street:** Conflicts at 9+ tables → **REASSIGN PRIORITY**

### 📊 Imbalanced Ratio Tables  
- T68, T80, T74, T72, T51 → Need more certified judges

---

## Judge Rank Categories

### ✅ Can Lead (Certified+)
- Certified (3)
- Certified + Sensory Training (3)
- National (4)
- Certified Cicerone (counts as certified)

### ❌ Need Partner (Non-Certified)
- Non-BJCP (0)
- Provisional (1)
- Rank Pending (2)
- Recognized (2)
- Any of above + Sensory Training

---

## Excel Tips for PAIRING_WORKSHEET.csv

**Filter** by "Action Needed":
- "ADD JUDGES" → Too many beers per pair
- "REASSIGN JUDGE" → Entry conflicts
- "Consider adding judges" → Getting close to limit

**Sort** by:
- "Beers/Pair" → Find heaviest loaded tables
- "Conflict?" → Find all conflicts

**Track** in "Notes" column:
- When reassignment is made
- Who was swapped out/in
- Any special considerations

---

## Common Tasks

### Find judges with conflicts
```bash
grep "Conflict?" PAIRING_WORKSHEET.csv | grep "YES"
```

### Find tables with high workload
```bash
awk -F',' '$9 > 12 {print}' PAIRING_WORKSHEET.csv
```

### See specific table details
```bash
cat optimization_output.txt | grep -A 30 "T68"
```

---

## Problem-Solving

### "Not enough certified judges for this table"
→ Look for certified judges at less busy tables (earlier in schedule)  
→ Check if they can be moved

### "Judge has entry in this category"
→ Find them a different table with no conflicts  
→ Use PAIRING_WORKSHEET.csv to find alternatives

### "Want to optimize by distance"
→ Reference JUDGE WORKSHEET 2026.csv for distances  
→ Cross-check with work date availability

### "How do I know if changes worked?"
→ Run: `python3 generate_recommendations.py`  
→ Compare "Sites with issues" count before/after

---

## Files You Need

| File | For What |
|------|----------|
| JUDGE_RECOMMENDATIONS.md | See priorities |
| PAIRING_WORKSHEET.csv | Track & plan changes |
| Judges and Tables.tsv | Make actual changes |
| judging_schedule.html | View/share schedule |

---

## Success Checklist

- [ ] Read JUDGE_RECOMMENDATIONS.md
- [ ] Open PAIRING_WORKSHEET.csv in Excel
- [ ] Identify Brian Street conflicts (priority reassign)
- [ ] Find certified judges for T88 and T93
- [ ] Create reassignment plan
- [ ] Update Judges and Tables.tsv
- [ ] Run `python3 judges_by_site.py`
- [ ] Run `python3 generate_recommendations.py`
- [ ] Check improvements in output
- [ ] Run `python3 generate_optimized_schedule.py`
- [ ] Review updated judging_schedule.html
- [ ] Share with volunteer committee

---

## 30-Second Cheat Sheet

**What's wrong?**
- 2 critical tables with 36 beers and only 1 judge each
- 13 tables with judges evaluating their own entries
- 5 tables with too many non-certified judges

**What to fix?**
1. **Add certified judges** to T88 & T93
2. **Reassign Brian Street** (9+ conflicts)
3. **Reassign other conflicted judges** 
4. **Rebalance ratios** at imbalanced tables

**How to verify?**
- Run recommendations script
- Check "Sites with issues" goes down
- Review updated PAIRING_WORKSHEET

---

Made with 🍺 for the 2026 Bluebonnet Brew-Off
