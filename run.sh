#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# immer exakt das Python aus dieser venv verwenden
VENV_PY="$(pwd)/.venv/bin/python"

if [[ ! -x "$VENV_PY" ]]; then
   echo "Fehler: venv Python nicht gefunden: $VENV_PY"
   echo "Hast du die venv in $(pwd)/.venv angelegt?"
   exit 1
fi

PYTHONPATH=src "$VENV_PY" -m frva