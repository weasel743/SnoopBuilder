#!/usr/bin/env bash
# language: Bash, file: install.sh
# *installe Python, pip, dépendances, PyInstaller, Nuitka, C compiler*

set -e
echo "============================================================"
echo "  Snoop Builder - Installation (macOS/Linux)"
echo "============================================================"

PY=python3
if ! command -v $PY >/dev/null 2>&1; then
    echo "[ERREUR] python3 introuvable. Installe-le :"
    echo "  macOS : brew install python"
    echo "  Ubuntu: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

echo "[1/4] Mise à jour pip..."
$PY -m pip install --upgrade pip --quiet || true

echo "[2/4] Dépendances builder + payload..."
$PY -m pip install --quiet \
    "PyQt5>=5.15.9,<6" \
    requests psutil Pillow pycryptodomex browser-history

echo "[3/4] PyInstaller..."
$PY -m pip install --quiet pyinstaller || echo "  (echec, non-bloquant)"

echo "[4/4] Nuitka + compilateur..."
$PY -m pip install --quiet nuitka ordered-set zstandard || echo "  (echec, non-bloquant)"

if ! command -v gcc >/dev/null 2>&1 && ! command -v clang >/dev/null 2>&1; then
    echo "[ATTENTION] Aucun compilateur C detecte."
    echo "  macOS : xcode-select --install"
    echo "  Ubuntu: sudo apt install build-essential"
fi

echo ""
echo "============================================================"
echo "  Installation terminee. Lancer : python3 builder.py"
echo "============================================================"