# -*- coding: utf-8 -*-
"""Rebuild all unified strict-path meta and CASM results."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


CODE = Path(__file__).resolve().parent
SCRIPTS = [
    "01_build_strict_dataset.py",
    "02_run_meta_analysis.py",
    "03_build_casm_scenarios.py",
    "04_run_casm_simulation.py",
    "05_build_submission_summary.py",
]


def main():
    for name in SCRIPTS:
        script = CODE / name
        print(f"\nRunning {script.name}", flush=True)
        subprocess.run([sys.executable, str(script)], check=True)


if __name__ == "__main__":
    main()
