#!/bin/bash
cd "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
rm -f outputs/_TOPUP_DONE outputs/_TOPUP_FAILED
{
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 CURV=1 BOOT_B=110 BOOT_CORES=3 \
    BOOT_SEED=20260707 BOOT_TAG=_b2 Rscript src/34_bootstrap_v2.R > outputs/_log_34_topup.txt 2>&1 &&
  CURV=1 Rscript src/34b_bootstrap_merge_v2.R > outputs/_log_34b.txt 2>&1 &&
  CURV=1 Rscript src/35_welfare_cv_v2.R > outputs/_log_35_full.txt 2>&1
} && touch outputs/_TOPUP_DONE || touch outputs/_TOPUP_FAILED
