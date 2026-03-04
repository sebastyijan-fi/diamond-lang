#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

. .venv/bin/activate

python src/probing/probe_repo.py --repo-url https://github.com/hukkin/tomli.git --name tomli_probe --run-tests
python src/probing/probe_repo.py --repo-url https://github.com/pallets/click.git --name click_probe --run-tests
