#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHONPATH="${script_dir}/src${PYTHONPATH:+:${PYTHONPATH}}" \
    exec python3 -m portfolio_rebalancer
