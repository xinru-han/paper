# Measurement robustness (audit items #1-#2)

## Scale-free A-line outcomes (table26)
                                                                            spec
1:                                 household HDDS-12 (headline, scale-dependent)
2: HDDS-12 | fixed n recorded members + total recorded meals (rarefaction-style)
3:                                              mean member FGDS-10 (scale-free)
4:                                           union FGDS-10, all recorded members
5:                                               union FGDS-10, EXCLUDING elders
6:                                             union FGDS-10, EXCLUDING children
         est         se            p   n
1: 0.5468816 0.12916586 3.048258e-05 716
2: 0.1422950 0.11939956 2.342963e-01 708
3: 0.0682087 0.08018908 3.956686e-01 708
4: 0.5607617 0.11900473 3.751676e-06 708
5: 0.6764675 0.12607553 1.637927e-07 665
6: 0.3229432 0.12058018 7.807460e-03 707

## Roster vs resident/observed living-arrangement agreement (table27)
                                                      comparison agreement    n
1: resident (>=180 days at home) vs roster, all elder households 0.9893791 1224
2:                resident vs roster, cohabit/threegen subsample 0.9888112  715
3:                  48h-observed vs roster, all elder households 0.7095710 1212
4:            48h-observed vs roster, cohabit/threegen subsample 0.6281690  710

## Main results under resident/observed classifications (table27b)
                                                spec           term        est
1:          A-line, roster classification (headline)          treat  0.5468816
2:       A-line, resident-based (>=180 days at home)          treat  0.5426111
3:                      A-line, 48h-observed members          treat  0.8708692
4:      B-line elder gap, roster threegen (headline)          elder -0.2935278
5:      B-line elder gap, roster threegen (headline) elder:threegen  0.2146178
6:         B-line elder gap, resident-based threegen          elder -0.3001928
7:         B-line elder gap, resident-based threegen elder:threegen  0.2341292
8: B-line elder gap, members >=180 days at home only          elder -0.2979138
9: B-line elder gap, members >=180 days at home only elder:threegen  0.2315267
           se            p    n
1: 0.12916586 3.048258e-05  716
2: 0.12865057 3.268849e-05  707
3: 0.13822854 1.202652e-09  549
4: 0.08659211 8.008390e-04 1594
5: 0.13537753 1.140287e-01 1594
6: 0.08699371 6.462397e-04 1592
7: 0.13366347 8.094380e-02 1592
8: 0.08826785 8.441528e-04 1574
9: 0.13576200 8.925152e-02 1574

Interpretation: household HDDS-12 is partly an observation-scale object;
the scale-free outcomes bound how much of the three-generation association
survives once 'more members recorded' is neutralised. The resident/observed
classifications guard against roster members who are registered but absent.
