# Phase 3 估计报告（规格矩阵版）

        model                    var    coef     se      p   n
      m1_base            dpi100_base  0.2391 0.1330 0.0723 300
      m1_base          plant_soy_lag  1.6620 0.5889 0.0048 300
      m1_base              peer_lag0  3.0153 2.2062 0.1717 300
   m1b_ctrlBC            dpi100_base  0.3245 0.1749 0.0635 300
   m1b_ctrlBC          plant_soy_lag  1.2862 0.4778 0.0071 300
   m1b_ctrlBC              peer_lag0  4.6616 1.9709 0.0180 300
 m1c_ctrlFull            dpi100_base  0.2771 0.1584 0.0802 300
 m1c_ctrlFull          plant_soy_lag  1.4644 0.5331 0.0060 300
 m1c_ctrlFull              peer_lag0  3.1572 2.4265 0.1932 300
      m2_roll            dpi100_roll  0.2121 0.1205 0.0783 300
      m2_roll          plant_soy_lag  1.6553 0.5617 0.0032 300
      m2_roll              peer_lag0  2.9307 2.1711 0.1771 300
m3_wooldridge            dpi100_base  1.3258 0.7277 0.0685 300
m3_wooldridge          plant_soy_lag  1.5902 0.9225 0.0847 300
m3_wooldridge              peer_lag0  2.2371 5.4808 0.6832 300
m3_wooldridge                 D_init  0.2778 0.4354 0.5234 300
m3_wooldridge        dpi100_base_bar -1.1623 0.7345 0.1136 300
m3_wooldridge                   logB  2.2246 1.1639 0.0560 300
   m4_lpm_all            dpi100_base  0.0322 0.0155 0.0376 496
   m4_lpm_all          plant_soy_lag  0.3145 0.0879 0.0003 496
   m4_lpm_all              peer_lag0  0.3119 0.3117 0.3170 496
  m4_lpm_nodc            dpi100_base  0.0352 0.0197 0.0740 300
  m4_lpm_nodc          plant_soy_lag  0.3063 0.0881 0.0005 300
  m4_lpm_nodc              peer_lag0  0.3631 0.2583 0.1598 300
       m5_loo             dpi100_loo  1.2385 0.4988 0.0130 300
       m5_loo          plant_soy_lag  1.7366 0.4644 0.0002 300
       m5_loo              peer_lag0  4.6045 2.5633 0.0724 300
  m6_subXsuit          plant_soy_lag  0.2691 0.1042 0.0098 300
  m6_subXsuit              peer_lag0 -0.6320 0.7324 0.3882 300
  m6_subXsuit dpi_sub100:suit_vill_z -0.0644 0.0545 0.2374 300
        r_ipw            dpi100_base  0.3110 0.1856 0.0938 300
        r_ipw          plant_soy_lag  1.6095 0.7164 0.0247 300
        r_ipw              peer_lag0  1.1014 2.3438 0.6384 300
   r_balanced            dpi100_base  0.4378 0.1334 0.0010 244
   r_balanced          plant_soy_lag  1.1405 0.6324 0.0713 244
   r_balanced              peer_lag0  1.8479 2.3396 0.4296 244
     s_uncond            dpi100_base  0.3985 0.1715 0.0201 300
     s_uncond                 s_lag0  3.3129 0.9935 0.0009 300
     s_uncond                   logB  0.2750 0.1249 0.0277 300
       s_cond            dpi100_base  0.2753 0.0987 0.0053  58
       s_cond                 s_lag0  0.2498 0.5666 0.6593  58
       s_cond                   logB -0.7044 0.2568 0.0061  58
      m_sizeX            dpi100_base  0.2523 0.1651 0.1265 300
      m_sizeX          plant_soy_lag  1.3844 0.6435 0.0314 300
      m_sizeX              peer_lag0  4.4739 2.4055 0.0629 300
      m_sizeX     dpi100_base:logB_c -0.0146 0.1230 0.9056 300

AME(基期锁定Δπ+100元): 2.76pp [-0.60, 6.11]
AME(Wooldridge): 13.15pp [-1.37, 27.67]
状态依赖AME: pooled=26.0pp, Wooldridge=20.2pp
σ_a(RE估计)=0.316
wild bootstrap p: {'lpm_all': 0.11402280456091218, 'lpm_nodc': 0.21964392878575714, 'lpm_lag_all': 0.033606721344268856}
Firth β=0.229
Anderson-Hsiao: {'gamma_fd2sls': 0.31812373670747257, 'se': 0.1790850253974127, 'beta_dpi': 0.22789070834677988, 'n': 136, 'first_stage_F': 50.417584771350576, 'n_clusters': 96}
规格曲线: β范围[0.067,0.384], 全部>0: True
村数=17, 阳性事件=58