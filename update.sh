#!/bin/bash
set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

echo "=== Loyiha yangilanmoqda (git pull) ==="
git pull

source venv/bin/activate
pip install -r requirements.txt

systemctl restart tg_checker
echo "=== Loyiha yangilandi va servis qayta ishga tushirildi! ==="
