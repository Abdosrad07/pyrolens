#!/bin/sh
# PyroLens — restauration des données locales après clonage / décompression.
#
# Ce script régénère tout ce qui est ignoré par git (.gitignore) :
#   data/raw/firms, data/raw/earthdata, data/fixture, data/manifests,
#   reports/anomalies, reports/experiments, reports/logs,
#   baselines/, figures/, web/public/artifacts/, web/dist/
#
# Usage :   sh ./scripts/restore-data.sh
#
# Deux modes, choisis automatiquement :
#   • clés NASA présentes dans l'environnement (FIRMS_MAP_KEY,
#     EARTHDATA_TOKEN ou EARTHDATA_USER/EARTHDATA_PASSWORD)
#       → acquisition des vraies données FIRMS/CMR (les blocages d'accès
#         éventuels sont journalisés tels quels, jamais contournés)
#   • aucune clé → échantillon synthétique de démonstration
#       → l'origine « synthetic_fixture » est étiquetée dans chaque artefact
#
# Les clés ne sont jamais affichées ni écrites dans les rapports.

set -eu

cd "$(dirname "$0")/.."

PY="${PYTHON:-python3}"
export PYTHONPATH=src

step() { printf '\n== %s ==\n' "$1"; }

step "1/7 — prérequis"
command -v "$PY" >/dev/null 2>&1 || { echo "ERREUR : python3 introuvable (Python 3.10+ requis)." >&2; exit 1; }
"$PY" --version
command -v npm >/dev/null 2>&1 || echo "Note : npm absent — le build du frontend sera ignoré."
if [ -f .env ]; then
  echo "Note : un fichier .env est présent. Exportez ses clés avant ce script si besoin :"
  echo "        set -a; . ./.env; set +a"
fi

step "2/7 — dépendances Python"
"$PY" -m pip install --quiet -r requirements.txt

step "3/7 — arborescence des données"
mkdir -p data/raw/firms data/raw/earthdata data/fixture data/manifests \
         reports/anomalies reports/experiments reports/logs \
         baselines figures web/public/artifacts

step "4/7 — état de l'environnement (noms de clés, jamais de valeurs)"
"$PY" -m pyrolens.cli doctor || true

step "5/7 — pipeline complet (geo → inventaire → acquisition → audit → baselines → observabilité → figures → rapport)"
"$PY" -m pyrolens.cli run

step "6/7 — artefacts du frontend"
"$PY" -m pyrolens.cli web-artifacts
if command -v npm >/dev/null 2>&1; then
  npm --prefix web install
  npm --prefix web run build
else
  echo "npm absent : build du frontend ignoré (les JSON d'artefacts sont déjà en place)."
fi

step "7/7 — tests"
"$PY" -m pytest

printf '\nTerminé. Points de contrôle :\n'
printf '  • origine des données : web/public/artifacts/audit.json → champ « data_origin »\n'
printf '  • rapports : reports/  ·  figures : figures/  ·  manifestes : data/manifests/\n'
printf '  • lancement du frontend : npm --prefix web run dev\n'
