#!/usr/bin/env bash
# Build standalone AutoExtract binary with PyInstaller.
# Install optional deps first for full feature support:
#   pip install -e ".[full]" && pip install pyinstaller
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/

echo "==> Installing PyInstaller..."
pip install pyinstaller 2>/dev/null || {
    echo "ERROR: Failed to install PyInstaller. Is your venv active?"
    exit 1
}

echo "==> Building standalone binary..."
pyinstaller \
    --noconfirm \
    --clean \
    --onefile \
    --name autoextract \
    --hidden-import send2trash \
    --hidden-import send2trash.platforms \
    --hidden-import py7zr \
    --hidden-import rarfile \
    --hidden-import requests \
    --hidden-import watchdog \
    --hidden-import watchdog.observers \
    --exclude-module tkinter \
    --exclude-module matplotlib \
    --exclude-module numpy \
    --exclude-module pandas \
    --exclude-module PIL \
    --exclude-module cv2 \
    --exclude-module setuptools \
    --exclude-module pip \
    --exclude-module wheel \
    --exclude-module pytest \
    autoextract/__main__.py

echo "==> Binary built: dist/autoextract"
ls -lh dist/autoextract
