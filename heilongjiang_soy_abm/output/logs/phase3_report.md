# Phase 3 估计报告

          model           var   coef     se      p   n
     logit_main        dpi100 0.2368 0.1307 0.0699 300
     logit_main plant_soy_lag 1.7375 0.5390 0.0013 300
     logit_main     peer_lag0 2.6856 1.7399 0.1227 300
            lpm        dpi100 0.0314 0.0134 0.0195 496
            lpm plant_soy_lag 0.3343 0.0856 0.0001 496
            lpm     peer_lag0 0.2545 0.3008 0.3974 496
      logit_cre        dpi100 0.7792 0.4363 0.0741 300
      logit_cre plant_soy_lag 1.7504 0.4637 0.0002 300
      logit_cre     peer_lag0 3.8763 2.1925 0.0771 300
     logit_size        dpi100 0.0622 0.1863 0.7386 300
     logit_size plant_soy_lag 1.7870 0.5237 0.0006 300
     logit_size     peer_lag0 2.6691 2.0137 0.1850 300
   logit_decomp    dpi_mkt100 0.3234 0.1011 0.0014 300
   logit_decomp    dpi_sub100 0.1371 0.5206 0.7923 300
   logit_decomp plant_soy_lag 1.7428 0.5186 0.0008 300
   logit_decomp     peer_lag0 1.6190 2.5769 0.5298 300
fraclogit_share        dpi100 0.1782 0.0951 0.0611  58
fraclogit_share        s_lag0 0.3667 0.5579 0.5110  58


AME(dpi100, 即Δπ+100元/亩): 0.0277  → 补贴差+100元/亩 ≈ +2.8 个百分点
状态依赖 AME(lag 0→1): 0.2714
规模分组 AME: {'small': 0.0063, 'mid': 0.0168, 'large': 0.0538}

份额方程残差SD: 0.2549