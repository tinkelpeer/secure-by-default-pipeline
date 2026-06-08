#!/usr/bin/env bash
set -euo pipefail

python -m sbd_pipeline.cli check --repo . --format table
python -m pytest
