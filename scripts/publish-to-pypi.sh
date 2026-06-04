#!/usr/bin/env bash
# Build and upload seobuddy to PyPI.
# Credentials: .env in repo root (gitignored), env vars, or interactive prompt.
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if ! command -v python3 >/dev/null; then
  echo "python3 not found"
  exit 1
fi

PYTHON=python3
if [[ -x .venv/bin/python ]]; then
  PYTHON=.venv/bin/python
elif [[ -x .venv/bin/python3 ]]; then
  PYTHON=.venv/bin/python3
else
  python3 -m venv .venv
  PYTHON=.venv/bin/python
fi

"$PYTHON" -m pip install --upgrade build twine hatchling -q
rm -rf dist
"$PYTHON" -m build
"$PYTHON" -m twine check dist/*

if [[ -z "${TWINE_PASSWORD:-}" ]]; then
  if [[ -t 0 ]]; then
    echo "PyPI upload needs an API token (https://pypi.org/manage/account/token/)"
    echo "Scope: Entire account (first publish) or Project: seobuddy"
    read -rsp "Paste TWINE_PASSWORD (pypi-...): " TWINE_PASSWORD
    echo
    export TWINE_PASSWORD
  else
    echo ""
    echo "No PyPI credentials found. Do one of the following:"
    echo "  1. cp .env.example .env   # edit .env with your pypi-... token"
    echo "  2. export TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-..."
    echo "  3. Run this script in an interactive terminal (it will prompt)"
    echo ""
    echo "Then run: ./scripts/publish-to-pypi.sh"
    echo "Built artifacts are in dist/ — upload only with: twine upload dist/*"
    exit 1
  fi
fi

export TWINE_USERNAME="${TWINE_USERNAME:-__token__}"
"$PYTHON" -m twine upload dist/*

echo ""
echo "Published. In 1–5 minutes verify:"
echo "  https://pypi.org/project/seobuddy/"
echo "  pip index versions seobuddy"
echo "  pip install seobuddy"
