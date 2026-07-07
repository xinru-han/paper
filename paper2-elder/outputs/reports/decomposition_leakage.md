# B3 decomposition & leakage

Three-generation co-residence raises household HDDS by 0.519 groups; the marginal pass-through of one HDDS group to elder FGDS-10 is 0.436. The elder-level total effect is 0.214 groups, i.e. 41% of the household provisioning gain reaches the older adult's own 48h intake; leakage = 59% (95% CI 19-108%).

## By-arrangement decomposition
        arrangement       dHDDS      phi1 passthrough_component
1:      elder_alone -0.28349668 0.4357769           -0.12354130
2:      elder_child  0.08520111 0.4357769            0.03712867
3: elder_only_multi -0.36904865 0.4357769           -0.16082287
4:            other  0.39177875 0.4357769            0.17072812
5:         threegen  0.51926377 0.4357769            0.22628314
   total_elder_effect allocation_residual leakage_rate     pass_lo     pass_hi
1:         0.98184538          1.10538667    4.4633399 -0.31318987  0.08884012
2:         0.17496140          0.13783273   -1.0535108 -0.18185204  0.26978650
3:         0.08919604          0.25001891    1.2416918 -0.27664055 -0.02472966
4:         0.23481402          0.06408590    0.4006464 -0.01658473  0.36921751
5:         0.21404072         -0.01224242    0.5877996  0.11897437  0.34625424
      alloc_lo  alloc_hi     leak_lo   leak_hi
1:  0.78863695 1.4082367 -28.2372353 34.211428
2: -0.18039939 0.4175824  -4.8540692 10.480377
3:  0.07760864 0.4009786   0.7268264  3.133529
4: -0.42345073 0.4442837  -1.9828712  3.686646
5: -0.24573305 0.1624549   0.1892127  1.079566

## Heterogeneity (three-gen leakage)
   arrangement     dHDDS      phi1 passthrough_component total_elder_effect
1:    threegen 0.5192638 0.5140801             0.2669432         0.39079530
2:    threegen 0.5192638 0.3579912             0.1858919         0.08090176
3:    threegen 0.5192638 0.4467265             0.2319689         0.18497172
4:    threegen 0.5192638 0.4096507             0.2127168         0.26752325
   allocation_residual leakage_rate         group
1:          0.12385211    0.2474050    elder_cook
2:         -0.10499012    0.8441991 elder_notcook
3:         -0.04699719    0.6437808    low_income
4:          0.05480646    0.4848028   high_income
