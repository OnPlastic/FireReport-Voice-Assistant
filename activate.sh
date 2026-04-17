# Dieses Skript muss gesourced werden:
#    source activate.sh

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
   echo "Bitte so ausführen: source activate.sh"
   exit 1
fi

cd "$(dirname "${BASH_SOURCE[0]}")" || return 1

if [[ ! -f ".venv/bin/activate" ]]; then
   echo "Fehler: .venv nicht gefunden"
   return 1
fi

source .venv/bin/activate
echo "Activated venv in: $(pwd)/.venv"
python --version
