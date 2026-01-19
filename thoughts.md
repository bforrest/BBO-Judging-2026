I have the following sets of data:

`BBO Medal Tables to BJCP Styles.cvs` maps tables from a homebrew contest to styles defined by the BJCP.

The spreadsheet `JUDGING SCHEDULE` lists dates in column A, days in column B, and BBO Medal tables that are being judges in columns C, D, E, and F

The tab separated file 'Judges and Tables' contains 'FULL NAME', 'DESIRED TABLE TO JUDGE', 'PAIRING', 'BJCP ID', 'RANKING', and a comma separated list of	'SUBSTYLES ENTERED'

A judge may not sit for a BBO Medal category where they have entered a beer.
Judge ranks proceed from 'Level 0: Non-BJCP', 'Level 1: Rank Pending', 'Level 2: Recognized', 'Level 3: Certified', 'Certified+Mead', 'Certified+Mead+cider', up to'Level 4: National'. The last being the highest "Rank". Each BBO Medal table should have pairs of judges, indicated by the "PAIRING" column. Any judge below the rank of 'Level 3: Certified' must be paired with a judge holding the Rank of 'Level 3: Certified'

I would like a way to visualize which judges are sitting for which BBO Medal tables and which locations.