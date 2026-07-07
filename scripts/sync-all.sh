#!/usr/bin/env bash
# Run all paper subfolder sync scripts.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "${SCRIPT_DIR}/sync-covid-wugong.sh"
bash "${SCRIPT_DIR}/sync-feed-import-elasticity.sh"
bash "${SCRIPT_DIR}/sync-cctv-easi-demand.sh"
bash "${SCRIPT_DIR}/sync-separability.sh"
bash "${SCRIPT_DIR}/sync-soybean.sh"
bash "${SCRIPT_DIR}/sync-food-demand-2050.sh"
