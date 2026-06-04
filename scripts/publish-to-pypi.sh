#!/usr/bin/env bash
# Build and upload seobuddy to PyPI. Requires TWINE_USERNAME=__token__ and TWINE_PASSWORD.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m pip install --upgrade build twine hatchling -q
python3 -m build
python3 -m twine check dist/*

if [[ -z "${TWINE_PASSWORD:-}" ]]; then
  echo "Set TWINE_USERNAME=__token__ and TWINE_PASSWORD to your PyPI API token, then re-run."
  exit 1
fi

export TWINE_USERNAME="${TWINE_USERNAME:-__token__}"
python3 -m twine upload dist/*

echo "Done. After a few minutes: pip install seobuddy"
