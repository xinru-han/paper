#!/bin/bash
cd "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
rm -f outputs/_PIPELINE_DONE outputs/_PIPELINE_FAILED
{
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 CURV=1 BOOT_B=200 BOOT_CORES=5 Rscript src/34_bootstrap_v2.R > outputs/_log_34_full.txt 2>&1 &&
  Rscript src/39_descriptives_v2.R > outputs/_log_39_full.txt 2>&1 &&
  Rscript src/33_robustness_v2.R > outputs/_log_33_full.txt 2>&1 &&
  CURV=1 Rscript src/35_welfare_cv_v2.R > outputs/_log_35_full.txt 2>&1
} && touch outputs/_PIPELINE_DONE || touch outputs/_PIPELINE_FAILED
