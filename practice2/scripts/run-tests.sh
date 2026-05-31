#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v python3 >/dev/null; then
  echo "python3 not found"
  exit 1
fi

if ! python3 -c "import venv" 2>/dev/null; then
  echo "Missing python3-venv. Run once:"
  echo "  sudo apt update && sudo apt install -y python3-venv python3-pip"
  exit 1
fi

if [[ ! -d .venv/bin ]]; then
  rm -rf .venv
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

PIP_INDEX="${PIP_INDEX_URL:-https://pypi.org/simple}"
pip install --default-timeout=120 --retries 10 -i "$PIP_INDEX" \
  -r services/gateway/requirements.txt \
  -r services/worker/requirements.txt \
  -r requirements-test.txt

export PYTHONPATH="${PWD}:${PWD}/services"
pytest -v "$@"
