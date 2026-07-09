#!/bin/bash
# Rebuild figures + manuscript after the pcyc re-run completes.
set -uo pipefail
cd /root/data/Paper/央视数据/Paper1-EASI/paper_v2/src
python3 make_figures.py > /tmp/_fig_build.log 2>&1 && echo "figures OK" || { echo "figures FAILED"; tail -5 /tmp/_fig_build.log; exit 1; }
python3 build_paper.py  > /tmp/_paper_build.log 2>&1 && echo "paper OK" || { echo "paper FAILED"; tail -15 /tmp/_paper_build.log; exit 1; }
tail -3 /tmp/_paper_build.log
