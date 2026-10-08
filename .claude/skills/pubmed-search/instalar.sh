#!/usr/bin/env bash
# Descarga pubmed_search.py de un commit FIJADO y comprueba su huella SHA-256
# contra la versión que se revisó el 2026-10-08. Si no coincide, no lo deja instalado.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)/vendor"
COMMIT=bc68a03871058c9614147d23a52a6a943bee381c
BASE="https://raw.githubusercontent.com/JackKuo666/pubmed-search-skill/$COMMIT"
SHA_PY=ba8d9846cd98d3b112f8a5893711f8a873a67f652cd7890c1e8823ffb9879e8a
mkdir -p "$DIR"
curl -fsS -m 30 -o "$DIR/pubmed_search.py.tmp" "$BASE/pubmed_search.py"
echo "$SHA_PY  $DIR/pubmed_search.py.tmp" | sha256sum -c - || { rm -f "$DIR/pubmed_search.py.tmp"; echo "HUELLA DISTINTA: no se instala"; exit 1; }
mv "$DIR/pubmed_search.py.tmp" "$DIR/pubmed_search.py"
python3 -c "import requests" 2>/dev/null || python3 -m pip install --quiet "requests>=2.31.0"
echo "OK: $DIR/pubmed_search.py"
