#!/usr/bin/env bash
set -u
ROOT=/root/data/Paper/央视数据/cctv_maidads_20261011
STATA=/usr/local/stata17/stata-se
mkdir -p "$ROOT/tmp_corner_bounded_start1" "$ROOT/tmp_corner_bounded_start2" "$ROOT/tmp_corner_bounded_post"
cd "$ROOT/logs" || exit 1
STAMP=$(date +%Y%m%d_%H%M%S)
for START in 1 2; do
    CP="$ROOT/outputs/corner/checkpoint_start$START.csv"
    if test -f "$CP"; then mv "$CP" "$CP.previous_$STAMP"; fi
done
# External bounds also cover vendor optimization code that does not call back.
env STATATMP="$ROOT/tmp_corner_bounded_start1" timeout --signal=INT --kill-after=5s 900s "$STATA" -b do "$ROOT/code/03_corner_fit.do" start1
RC1=$?
env STATATMP="$ROOT/tmp_corner_bounded_start2" timeout --signal=INT --kill-after=5s 600s "$STATA" -b do "$ROOT/code/03_corner_fit.do" start2
RC2=$?
printf 'Start process exit codes: %s %s\n' "$RC1" "$RC2"
test -s "$ROOT/outputs/corner/checkpoint_start1.csv" || exit 1
test -s "$ROOT/outputs/corner/checkpoint_start2.csv" || exit 1
env STATATMP="$ROOT/tmp_corner_bounded_post" timeout --signal=INT --kill-after=5s 900s "$STATA" -b do "$ROOT/code/03_corner_fit.do" checkpoint
