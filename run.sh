#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

git pull --rebase origin main
.venv/bin/python3 main.py

if ! git diff --quiet state.json; then
  git add state.json
  git commit -m "Update state.json [skip ci]"
  git push origin main
fi
