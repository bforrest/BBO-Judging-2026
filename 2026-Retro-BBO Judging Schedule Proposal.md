### BBO Judging Schedule Proposal

========================================
Proposed: 8 days, 11 sessions, placing 20 of 44 tables (24 unfilled)
2026 actual: 10 days, 14 sessions, 44 tables (full coverage)
Theoretical floor for the 20 placed tables (4 sites, full parallelism): 5 sessions

NOTE: coverage is incomplete, so the day/session counts above are NOT comparable to the 2026 baseline or to the all-44-table floor of 11 sessions. Staffing the unfilled tables would require additional sessions. See this script's module docstring and the design spec for theknown limitation behind the unfilled tables.

Why are there 24 unfilled tables? I'm glad you asked.
> Confirmed with a real example — it's a pairing algorithm limitation, not a judge-preference problem.

T76 Barleywines needs 4 judge pairs (36 entries). There are actually 75 eligible judges available for it — plenty of judges willing to judge that style, no shortage there. On the best available date (02/06, 37 of those 75 judges free), the algorithm successfully forms 4 valid certification pairs:

Amanda Long (Keller/Grapevine/Arlington)  + Emily Allen     (all 4 sites)
Mike Grover (Grapevine/Dallas)            + Steve Ballantyne (Keller/Grapevine/Arlington)
Walter Hodges (Grapevine/Dallas)          + C.J. Barley      (all 4 sites)
Brandon Montgomery (Dallas only)          + Bill Hamilton    (all 4 sites)

Each pair individually is fine. But the four pairs together share no common site — Brandon Montgomery can only reach Dallas, while Mike Grover and Steve Ballantyne can't reach Dallas together (Steve isn't feasible there at all). So there's no single site where all 4 pairs could physically show up, and the table gets marked unfilled.

The root cause: form_pairs picks who's certified-paired-with-whom purely on rank, with zero regard to site. Only afterward does try_fit check whether the site sets intersect — by then it's too late, because a different set of 4 pairs (e.g., all Grapevine-feasible judges, of which there are clearly several) would have worked fine. The algorithm just never considered that alternative.


UNFILLED (24 tables could not be staffed):
  T76 Barleywines: needs 4 pairs
  T62 British Bitter: needs 4 pairs
  T68 Pale American Ale: needs 4 pairs
  T79 Belgian Blonde and Saison: needs 4 pairs
  T88 Specialty Beer: needs 4 pairs
  T93 Specialty Cider And Perry: needs 4 pairs
  T73 Specialty IPA: needs 3 pairs
  T74 Hazy and Experimental IPA: needs 3 pairs
  T77 European Sour Ale: needs 3 pairs
  T67 Strong British Ale: needs 4 pairs
  T85 Smoke Beer: needs 4 pairs
  T90 Melomel: needs 4 pairs
  T71 Imperial Stout: needs 3 pairs
  T82 Fruit Beer: needs 4 pairs
  T87 American Wild Ale: needs 3 pairs
  T50 Pale Lager: needs 4 pairs
  T53 Pale German Beer: needs 4 pairs
  T54 Pale European Lager: needs 4 pairs
  T56 Oktoberfest: needs 4 pairs
  T57 European Ambers and Bocks: needs 4 pairs
  T58 Amber Bitter European Beer: needs 4 pairs
  T59 Dark European Lager: needs 4 pairs
  T60 Strong European Beer: needs 4 pairs
  T51 Light Ale: needs 3 pairs

Day 02/06:
  (single session):
    T66 British Stout @ Grapevine: Amanda Long & Emily Allen, Mike Grover & Steve Ballantyne, Walter Hodges & C.J. Barley
Day 02/07:
  AM:
    T63 Brown British Beer @ Dallas: Mike Grover & C.J. Barley, Walter Hodges & Bill Hamilton, Terry Olinger & Mark Schuler, Mark McCurdy & Greg Smith
    T70 American Porter And Stout @ Keller: Jarrett Long & Tim Mercer, Loring Knutson & Reni Morriss, Nancy Knutson & Stacy Myers
    T78 Belgian Ale @ Grapevine: Amanda Long & Douglas Hicks, Steve Russell & Steve Steinheimer, Matthew Morriss & Joseph Cromeans, MikeTreadway & Jerry Keeney
  PM:
    T61 German Wheat Beer @ Keller: Amanda Long & Emily Allen, Steve Brown & C.J. Barley, Steve Russell & Tierney Klee, Matthew Morriss & Michael Porter
    T72 American IPA @ Grapevine: Jarrett Long & Jerry Keeney, Loring Knutson & Brandon Melton, John Shank & Reni Morriss
    T84 Autumn Winter Seasonal @ Dallas: Mike Grover & Mark Schuler, Walter Hodges & William Lawrence, Mark McCurdy & Douglas Robinson
    T86 Wood Aged Beer @ Arlington: John Mosher & Steve Steinheimer, Mike Treadway & Kim Truesdell, Nancy Knutson & Joseph Cromeans
Day 02/13:
  (single session):
    T80 Strong Light Belgian Ale @ Grapevine: Amanda Long & Emily Allen, Jarrett Long & Steve Ballantyne, Mike Grover & C.J. Barley
Day 02/14:
  AM:
    T92 Cider And Perry @ Grapevine: Amanda Long & Mark Schuler, Jarrett Long & James Smith, Mike Grover & Kim Truesdell, Walter Hodges & Joseph Cromeans
  PM:
    T55 Kolsch and Blonde @ Grapevine: Amanda Long & Emily Allen, Mike Grover & Mark Schuler, Walter Hodges & Kim Truesdell
    T75 Strong American Ale @ Arlington: Mike Treadway & Brian Street, Terry-Lynn Faught & Brian English, Kyle Lapointe & John Shank
    T83 Spice Herb Vegetable Beer @ Keller: Jarrett Long & Tim Mercer, Steve Brown & Reni Morriss, Steve Russell & Stacy Myers
    T89 Traditional Mead @ Dallas: Terry Olinger & Mike MacCrory, Alf Syftestad & Taryn Dunn, Matthew Morriss & Clayson Green, Carlos Herrera & Forrest, Barry
Day 02/16:
  (single session):
    T91 Spiced And Specialty Mead @ Grapevine: Mark McCurdy & Walter Hansen, Brian Schoolcraft & Karl King, John Shank & Jerry Richard, Vicki Brown & Jonathan Rollins
Day 02/21:
  AM:
    T81 Strong Dark Belgian Ale @ Grapevine: Amanda Long & Bill Hamilton, Jarrett Long & Mark Schuler, Mike Grover & Kim Truesdell, MarkMcCurdy & Jerry Keeney
  PM:
    T52 Commonwealth Beer @ Grapevine: Amanda Long & Bill Hamilton, Mike Grover & Michael Porter, Steve Brown & Mark Schuler
Day 02/27:
  (single session):
    T64 Scottish and Irish Ale @ Keller: Amanda Long & Emily Allen, Jarrett Long & Steve Ballantyne, Steve Brown & C.J. Barley, Joshua Hayes & Tierney Klee
Day 02/28:
  AM:
    T65 Stout and Porter @ Arlington: Amanda Long & James Klee, Matthew Morriss & Tierney Klee, John Mosher & Mark Schuler, Mike Treadway & Greg Smith
    T69 Amber And Brown American Beer @ Grapevine: Loring Knutson & Kim Truesdell, Nancy Knutson & Reni Morriss, Kyle Lapointe & Stacy Myers, Nigel Curtis & Harry Anderson