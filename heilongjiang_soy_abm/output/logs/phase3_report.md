# Phase 3 估计报告（规格矩阵版）

        model                    var    coef     se      p   n
      m1_base            dpi100_base  0.2428 0.1354 0.0730 300
      m1_base          plant_soy_lag  1.6617 0.5891 0.0048 300
      m1_base              peer_lag0  3.0106 2.2068 0.1725 300
   m1b_ctrlBC            dpi100_base  0.3295 0.1766 0.0621 300
   m1b_ctrlBC          plant_soy_lag  1.2857 0.4783 0.0072 300
   m1b_ctrlBC              peer_lag0  4.6551 1.9739 0.0184 300
 m1c_ctrlFull            dpi100_base  0.2811 0.1592 0.0773 300
 m1c_ctrlFull          plant_soy_lag  1.4639 0.5335 0.0061 300
 m1c_ctrlFull              peer_lag0  3.1519 2.4274 0.1941 300
      m2_roll            dpi100_roll  0.2145 0.1221 0.0789 300
      m2_roll          plant_soy_lag  1.6551 0.5618 0.0032 300
      m2_roll              peer_lag0  2.9269 2.1713 0.1777 300
m3_wooldridge            dpi100_base  1.3468 0.7479 0.0718 300
m3_wooldridge          plant_soy_lag  1.5475 0.8984 0.0850 300
m3_wooldridge              peer_lag0  2.5887 5.0267 0.6066 300
m3_wooldridge                 D_init  0.3038 0.4303 0.4803 300
m3_wooldridge        dpi100_base_bar -1.1797 0.7470 0.1143 300
m3_wooldridge                   logB  2.2784 1.1639 0.0503 300
   m4_lpm_all            dpi100_base  0.0326 0.0157 0.0373 496
   m4_lpm_all          plant_soy_lag  0.3145 0.0879 0.0003 496
   m4_lpm_all              peer_lag0  0.3117 0.3113 0.3168 496
  m4_lpm_nodc            dpi100_base  0.0357 0.0200 0.0745 300
  m4_lpm_nodc          plant_soy_lag  0.3063 0.0881 0.0005 300
  m4_lpm_nodc              peer_lag0  0.3624 0.2583 0.1605 300
       m5_loo             dpi100_loo  1.2845 0.5100 0.0118 300
       m5_loo          plant_soy_lag  1.7365 0.4641 0.0002 300
       m5_loo              peer_lag0  4.6259 2.5663 0.0715 300
  m6_subXsuit          plant_soy_lag  0.2691 0.1042 0.0098 300
  m6_subXsuit              peer_lag0 -0.6322 0.7326 0.3882 300
  m6_subXsuit dpi_sub100:suit_vill_z -0.0644 0.0545 0.2372 300
        r_ipw            dpi100_base  0.2956 0.1649 0.0731 300
        r_ipw          plant_soy_lag  1.5431 0.6306 0.0144 300
        r_ipw              peer_lag0  1.7131 2.2949 0.4554 300
   r_balanced            dpi100_base  0.4427 0.1345 0.0010 244
   r_balanced          plant_soy_lag  1.1403 0.6323 0.0713 244
   r_balanced              peer_lag0  1.8403 2.3418 0.4320 244
     s_uncond            dpi100_base  0.4042 0.1744 0.0205 300
     s_uncond                 s_lag0  3.3082 0.9972 0.0009 300
     s_uncond                   logB  0.2757 0.1248 0.0271 300
       s_cond            dpi100_base  0.2784 0.1009 0.0058  58
       s_cond                 s_lag0  0.2450 0.5672 0.6658  58
       s_cond                   logB -0.7036 0.2570 0.0062  58
      m_sizeX            dpi100_base  0.2562 0.1681 0.1274 300
      m_sizeX          plant_soy_lag  1.3834 0.6436 0.0316 300
      m_sizeX              peer_lag0  4.4749 2.4050 0.0628 300
      m_sizeX     dpi100_base:logB_c -0.0163 0.1247 0.8957 300

AME(基期锁定Δπ+100元): 2.80pp [-0.62, 6.22]
AME(Wooldridge): 13.37pp [-1.88, 28.61]
状态依赖AME: pooled=26.0pp, Wooldridge=19.6pp
σ_a(RE估计)=0.302
wild bootstrap p: {'lpm_all': 0.11202240448089618, 'lpm_nodc': 0.22364472894578916, 'lpm_lag_all': 0.033806761352270454}
Firth β=0.233
Anderson-Hsiao: {'gamma_fd2sls': 0.33048777622892866, 'se': 0.22939418653621416, 'beta_dpi': 0.2808261952717165, 'n': 136}
规格曲线: β范围[0.067,0.389], 全部>0: True
村数=17, 阳性事件=58