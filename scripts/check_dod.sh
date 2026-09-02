#!/usr/bin/env bash
set -euo pipefail

python scripts/check_dod.py "${1:-all}"
