#!/usr/bin/env bash
set -euo pipefail

# Path del repo del sitio en la Pi
REPO_DIR="/home/matzalazar/matzalazar.github.io"

# Directorio base donde el tracker deja sus datos en FHS.
# Apuntamos a /var/lib/personal-track y el builder se encarga
# de buscar recursivamente (subdir "data" o lo que uses).
DATA_SOURCE="/var/lib/personal-track"

# Ruta al vault/colección de notas de Obsidian que se publican en el blog
OBSIDIAN_DIR="/home/matzalazar/dropbox_montado/Aplicaciones/remotely-save/Notas/blog notes"

DATE=$(date '+%Y-%m-%d %H:%M')

# Variables que leerá build.py
export TRACKER_RAW_DATA="$DATA_SOURCE"
export OBSIDIAN_NOTES_PATH="$OBSIDIAN_DIR"

cd "$REPO_DIR"

echo "[+] Ejecutando builder de sitio..."
python3 scripts/build.py

echo "[+] Builder finalizado. Revisando cambios en git..."
if [[ -n $(git status --porcelain) ]]; then
    echo "[+] Cambios detectados. Commiteando y pusheando..."

    # Limitamos el scope del add a lo que genera el builder
    git add _data _logs about.md

    git commit -m "Update: Logs y datos - $DATE"
    git push origin main

    echo "[+] Deploy completado con éxito."
else
    echo "[+] No hubo cambios. Nada que pushear."
fi
