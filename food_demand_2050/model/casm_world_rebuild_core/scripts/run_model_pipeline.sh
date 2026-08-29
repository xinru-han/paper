#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${project_root}/src"

cd "${project_root}"

python3 -m casm_world.paths
python3 -m casm_world.benchmark
python3 -m casm_world.balancing
python3 -m casm_world.parameters
python3 -m casm_world.drivers
python3 -m casm_world.tfp
python3 -m casm_world.exchange_rates
python3 -m casm_world.policy
python3 -m casm_world.climate
python3 -m casm_world.simulation
python3 -m casm_world.analysis
python3 -m casm_world.scenario_nutrition
python3 -m casm_world.ghg --run-ssp
python3 -m casm_world.validation
python3 scripts/build_paper_analysis.py
python3 -m pytest -q -p no:cacheprovider
