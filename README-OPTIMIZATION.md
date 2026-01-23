# 📋 Judge Optimization Toolkit - Start Here

## What Is This?

A complete suite of tools and analysis to optimize the 2026 Bluebonnet Brew-Off judging schedule for:
- ✅ Fair judge workload (9-12 beers per pair)
- ✅ Proper pairing (certified judges with non-certified)
- ✅ Conflict avoidance (no judge evaluating their own entries)
- ✅ Efficient resource utilization

---

## 🚀 Quick Start (5 minutes)

### Step 1: See the Big Picture
Open this file first:
```
QUICK_REFERENCE.md
```
2-page cheat sheet with everything you need to know.

### Step 2: Understand Your Priorities
Read this next:
```
JUDGE_RECOMMENDATIONS.md
```
Shows exactly which tables need help and what to do.

### Step 3: Get the Worksheet
Open in Excel:
```
PAIRING_WORKSHEET.csv
```
Sortable/filterable list of all pairing suggestions.

### Step 4: Make Changes
Edit this file:
```
Judges and Tables.tsv
```
Update judge assignments based on your plan.

### Step 5: Verify Improvements
Run these commands:
```bash
python3 judges_by_site.py
python3 generate_recommendations.py
python3 generate_optimized_schedule.py
open judging_schedule.html
```

---

## 📚 Documentation

### For Decision Makers
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** ⚡ - 2-page summary (start here!)
- **[JUDGE_RECOMMENDATIONS.md](JUDGE_RECOMMENDATIONS.md)** 📊 - Prioritized action list
- **[OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md)** 📋 - Complete summary with metrics

### For Technical Users
- **[OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)** 📖 - Full usage guide
- **[optimization_output.txt](optimization_output.txt)** 🔍 - Detailed analysis
- **[PAIRING_WORKSHEET.csv](PAIRING_WORKSHEET.csv)** 📈 - Spreadsheet format

---

## 🛠️ Tools

### Optimization Scripts
```bash
# Detailed analysis of every judge assignment
python3 optimize_judge_pairings.py

# Generate executive summary report
python3 generate_recommendations.py

# Export worksheet for Excel
python3 export_pairing_worksheet.py

# (Re)generate visual schedule
python3 generate_optimized_schedule.py

# Regenerate judges by site
python3 judges_by_site.py
```

### Output Files
- `optimization_output.txt` - Full technical analysis
- `JUDGE_RECOMMENDATIONS.md` - Prioritized recommendations
- `PAIRING_WORKSHEET.csv` - Excel-compatible worksheet
- `judges_by_site.csv` - Judge assignments by site
- `judging_schedule.html` - Interactive visual schedule

---

## 🎯 Current Status

| Metric | Value | Status |
|--------|-------|--------|
| **Total Sites** | 44 | - |
| **Running Smoothly** | 23 | ✅ |
| **Critical Issues** | 2 | 🚨 |
| **Overworked** | 1 | ⚠️  |
| **Conflicts** | 13 | 🔄 |
| **Pairing Issues** | 5 | 📊 |

---

## 🚨 Critical Issues

### Tables Needing Immediate Attention
1. **T88 Dallas Specialty Beer** (02/28 AM)
   - Only 1 certified judge, 36 entries
   - ACTION: Add 2 certified judges

2. **T93 Grapevine Specialty Cider** (02/28 AM)
   - Only 1 certified judge, 36 entries
   - ACTION: Add 2 certified judges

### Most Critical Judge
- **Brian Street** has conflicts at 9+ tables
- Needs immediate reassignment

---

## 📖 Reading Guide

### If you have 2 minutes:
→ Read [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

### If you have 10 minutes:
→ Read [JUDGE_RECOMMENDATIONS.md](JUDGE_RECOMMENDATIONS.md)

### If you have 30 minutes:
→ Read [OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md)

### If you need everything:
→ Read [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)

### If you're making changes:
→ Use [PAIRING_WORKSHEET.csv](PAIRING_WORKSHEET.csv) in Excel

---

## 🔄 Update Workflow

After making changes to judge assignments:

```bash
# 1. Update the master file
# (Edit Judges and Tables.tsv manually)

# 2. Regenerate the parsed data
python3 judges_by_site.py

# 3. Check your improvements
python3 generate_recommendations.py

# 4. Generate updated visualization
python3 generate_optimized_schedule.py

# 5. View the updated schedule
open judging_schedule.html
```

Each script takes 10-30 seconds to run.

---

## 💡 Key Concepts

### Judge Ranks
**Can Lead a Pair (Certified+):**
- Certified (rank 3)
- National (rank 4)

**Must Have Partner (Non-Certified):**
- Non-BJCP (rank 0)
- Provisional (rank 1)
- Rank Pending (rank 2)
- Recognized (rank 2)

### Workload Targets
- **Ideal:** 9 beers per pair
- **Acceptable:** 9-12 beers per pair
- **Concerning:** 12-15 beers per pair
- **Critical:** 15+ beers per pair

### Pairing Rules
1. Non-certified MUST pair with certified
2. No judge evaluates their own entry
3. Target 1 certified per 1-2 non-certified judges

---

## 🎓 How to Read the Analysis

### Optimization Output Format
```
================================================================================
⚠️  SITE: [Site Name]
================================================================================
Table: T[num] | Entries: [count]
Judges: [total] total ([certified] certified, [non-certified] non-certified)
Quality: [EXCELLENT/ACCEPTABLE/OVERWORKED/CRITICAL] | [beers/pair] beers/pair

ISSUES:
  • [Issue 1]
  • [Issue 2]

CURRENT JUDGES:
  ✓ CERT | [Name] | [Rank]  [Conflict marker if applicable]
  ...

SUGGESTED PAIRINGS ([num] pairs, ~[beers/pair] beers/pair):
  Pair 1:
    • [Judge 1] ([Rank])
    • [Judge 2] ([Rank])
  ...

RECOMMENDED ACTIONS:
  → [Action 1]
  → [Action 2]
```

---

## 📞 Questions?

| Question | Answer | Where |
|----------|--------|-------|
| What should I fix first? | Critical tables T88 & T93 | JUDGE_RECOMMENDATIONS.md |
| What's wrong with T68? | Too many non-certified judges | PAIRING_WORKSHEET.csv |
| Who has conflicts? | Brian Street (9+), others listed | JUDGE_RECOMMENDATIONS.md |
| Can I pair two certified judges? | Yes! That's fine. | OPTIMIZATION_GUIDE.md |
| How do I know if changes worked? | Run generate_recommendations.py again | QUICK_REFERENCE.md |
| Should I optimize by distance? | Yes, use JUDGE WORKSHEET 2026.csv | OPTIMIZATION_GUIDE.md |

---

## 📁 File Organization

```
Judging BBO 2026/
├── 📋 Documentation (START HERE)
│   ├── QUICK_REFERENCE.md ⚡ (2 pages)
│   ├── JUDGE_RECOMMENDATIONS.md 📊 (current priorities)
│   ├── OPTIMIZATION_SUMMARY.md 📋 (full overview)
│   ├── OPTIMIZATION_GUIDE.md 📖 (detailed guide)
│   └── README-OPTIMIZATION.md (this file)
│
├── 🛠️ Tools (Scripts)
│   ├── optimize_judge_pairings.py ← Run first for analysis
│   ├── generate_recommendations.py ← Run for summary
│   ├── export_pairing_worksheet.py ← Run for Excel
│   └── generate_optimized_schedule.py ← Run for HTML
│
├── 📊 Generated Reports
│   ├── optimization_output.txt (full analysis)
│   ├── PAIRING_WORKSHEET.csv (Excel-friendly)
│   ├── judges_by_site.csv (derived data)
│   └── judging_schedule.html (visual schedule)
│
└── 📥 Input Data
    ├── Judges and Tables.tsv (master - YOU EDIT THIS)
    ├── judges_by_site.csv (parsed view)
    ├── medal_category_counts.csv (entries per table)
    ├── styles by table.csv (BJCP mappings)
    └── JUDGE WORKSHEET 2026.csv (optional distances)
```

---

## ✅ Success Indicators

You've done well if:
- ✅ No table has only 1 certified judge
- ✅ Beers/pair average is 9-12 across tables
- ✅ All judges paired with correct ranks
- ✅ No judge evaluating their own entry
- ✅ All judges properly balanced by date

---

## 🎉 Next Steps

1. **Open** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
2. **Read** [JUDGE_RECOMMENDATIONS.md](JUDGE_RECOMMENDATIONS.md)
3. **Download** [PAIRING_WORKSHEET.csv](PAIRING_WORKSHEET.csv) to Excel
4. **Plan** your changes
5. **Edit** Judges and Tables.tsv
6. **Run** the scripts to verify
7. **Share** updated schedule with team

---

**Made with 🍺 for the 2026 Bluebonnet Brew-Off**

Last updated: January 23, 2026
