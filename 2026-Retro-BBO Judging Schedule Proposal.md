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


UNFILLED (9 tables could not be staffed):
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
    T61 German Wheat Beer @ Keller: Joshua Hayes & James Klee, Steve Russell & Tierney Klee, Matthew Morriss & Greg Smith, Mike Treadway & Matt Parulis
    T65 Stout and Porter @ Arlington: Amanda Long & Emily Allen, Steve Brown & Steve Ballantyne, Brian Schoolcraft & C.J. Barley, Steve Wesstrom & Bill Hamilton
    T69 Amber And Brown American Beer @ Dallas: Walter Hodges & Michael Porter, Brandon Montgomery & Mark Schuler, Eric Morgan & Amanda Garland, Alf Syftestad & William Lawrence
Day 02/07:
  AM:
    T63 Brown British Beer @ Keller: Steve Russell & C.J. Barley, Matthew Morriss & Bill Hamilton, Mike Treadway & Mark Schuler, Loring Knutson & Greg Smith
    T66 British Stout @ Dallas: Walter Hodges & Steve Steinheimer, Marcio Fazzani & Joseph Cromeans, Steve Littel & Jerry Keeney
    T70 American Porter And Stout @ Arlington: Amanda Long & Stacy Myers, Jarrett Long & Aaron Wagner, Nancy Knutson & David Bierschenk
  PM:
    T64 Scottish and Irish Ale @ Grapevine: Mike Grover & Douglas Robinson, Walter Hodges & Steve Steinheimer, Steve Russell & Kim Truesdell, Mike Treadway & Joseph Cromeans
    T78 Belgian Ale @ Dallas: Steve Brown & Emily Allen, Marcio Fazzani & C.J. Barley, Loring Knutson & Michael Porter, Nancy Knutson & Mark Schuler
    T81 Strong Dark Belgian Ale @ Arlington: Amanda Long & Tierney Klee, Jarrett Long & Jerry Keeney, John Mosher & Brandon Melton, John Shank & Stacy Myers
Day 02/13:
  (single session):
    T52 Commonwealth Beer @ Grapevine: Mike Grover & Greg Smith, Joshua Hayes & Douglas Hicks, James Duke & Douglas Robinson
    T76 Barleywines @ Keller: Steve Brown & Emily Allen, Matthew Morriss & Steve Ballantyne, Mike Treadway & C.J. Barley, Vicki Brown & Bill Hamilton
    T80 Strong Light Belgian Ale @ Arlington: Amanda Long & James Klee, Jarrett Long & Tierney Klee, John Mosher & James Smith
    T84 Autumn Winter Seasonal @ Dallas: Eric Morgan & William Lawrence, Alf Syftestad & Kevin Meyer, Marcio Fazzani & Kim Truesdell
Day 02/14:
  AM:
    T62 British Bitter @ Dallas: Walter Hodges & Amanda Garland, Alf Syftestad & Joseph Cromeans, Kyle Lapointe & Jerry Keeney, Brian English & Marqus Burleson
    T68 Pale American Ale @ Arlington: Amanda Long & Brandon Melton, Jarrett Long & Stacy Myers, Mike Treadway & Brian Street, Terry-Lynn Faught & Caroline Forster
    T79 Belgian Blonde and Saison @ Grapevine: Mike Grover & Mike MacCrory, David Johnson & Nichole Pena, Forrest, Barry & Taryn Dunn, Keith Green & Clayson Green
    T86 Wood Aged Beer @ Keller: Steve Brown & Mark Schuler, Steve Russell & James Smith, Matthew Morriss & Kim Truesdell
  PM:
    T74 Hazy and Experimental IPA @ Arlington: Amanda Long & Brian Street, Forrest, Barry & Terry-Lynn Faught, Brian English & Jarrett Long
    T88 Specialty Beer @ Dallas: Walter Hodges & Emily Allen, Steve Brown & Mark Schuler, Alf Syftestad & Kim Truesdell, Kyle Lapointe & Mike MacCrory
    T91 Spiced And Specialty Mead @ Keller: Steve Russell & Reni Morriss, Matthew Morriss & Stacy Myers, Mike Treadway & Taryn Dunn, John Shank & Clayson Green
Day 02/16:
  (single session):
    T93 Specialty Cider And Perry @ Keller: Brian Schoolcraft & Tim Mercer, John Shank & WalterHansen, Vicki Brown & Karl King, Keith Green & Jonathan Rollins
Day 02/20:
  (single session):
    T55 Kolsch and Blonde @ Arlington: Amanda Long & C.J. Barley, Steve Brown & Steve Steinheimer, Brian Schoolcraft & Kim Truesdell
    T72 American IPA @ Keller: Steve Russell & James Smith, James Duke & Tim Mercer, Terry-LynnFaught & Caroline Forster
Day 02/21:
  AM:
    T73 Specialty IPA @ Arlington: Amanda Long & Bill Hamilton, Vicki Brown & Mark Schuler, James Duke & Kim Truesdell
    T77 European Sour Ale @ Grapevine: Mike Grover & Jerry Keeney, Mark McCurdy & Harry Anderson, Charlie Scudder & Walter Hansen
  PM:
    T67 Strong British Ale @ Arlington: Amanda Long & Bill Hamilton, Jarrett Long & Michael Porter, Steve Brown & Mark Schuler, Vicki Brown & Kim Truesdell
    T85 Smoke Beer @ Grapevine: Mike Grover & Brian Street, Steve Russell & Aaron Wagner, JamesDuke & Marqus Burleson, Charlie Scudder & Nichole Pena
Day 02/27:
  (single session):
    T71 Imperial Stout @ Grapevine: Steve Brown & Greg Smith, Mark McCurdy & Kim Truesdell, Vicki Brown & Jerry Keeney
    T82 Fruit Beer @ Arlington: Amanda Long & Tierney Klee, John Mosher & Stacy Myers, James Duke & Mike MacCrory, Kyle Lapointe & Jerry Richard
    T90 Melomel @ Keller: Joshua Hayes & Emily Allen, Matthew Morriss & Steve Ballantyne, Mike Treadway & C.J. Barley, John Shank & James Klee
Day 02/28:
  AM:
    T89 Traditional Mead @ Grapevine: Mark McCurdy & Mark Schuler, Mike Treadway & Greg Smith, Loring Knutson & Kim Truesdell, Nancy Knutson & Stacy Myers
    T92 Cider And Perry @ Arlington: Amanda Long & James Klee, Jarrett Long & Tierney Klee, John Mosher & Brian Street, Kyle Lapointe & Marqus Burleson
  PM:
    T75 Strong American Ale @ Arlington: Amanda Long & Emily Allen, Jarrett Long & C.J. Barley,John Mosher & James Klee
    T83 Spice Herb Vegetable Beer @ Keller: Joshua Hayes & Tierney Klee, Steve Russell & Mark Schuler, Matthew Morriss & Kim Truesdell
    T87 American Wild Ale @ Grapevine: Mike Treadway & Brandon Melton, Loring Knutson & Harry Anderson, Nancy Knutson & Mike MacCrory