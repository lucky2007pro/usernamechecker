#!/bin/bash
set -e

echo "========================================================"
echo "  Telegram Username Checker - Serverga o'rnatish        "
echo "========================================================"

# Loyiha joylashgan katalog
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

# 1. Tizim paketlarini tekshirish va o'rnatish
echo "[1/5] Python va kerakli paketlar tekshirilmoqda..."
apt update -y
apt install -y python3 python3-pip python3-venv git

# 2. Virtual muhit (venv) yaratish va paketlarni o'rnatish
echo "[2/5] Virtual muhit (venv) tayyorlanmoqda..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. .env faylini tekshirish
echo "[3/5] .env fayli tekshirilmoqda..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo ".env fayli .env.example dan yaratildi. Iltimos, kalitlarni tekshiring."
    fi
fi

# 4. Ma'lumotlar papkasini yaratish
mkdir -p data

# 5. Systemd xizmatini sozlash (avtomatik qayta yonishi uchun)
echo "[4/5] Systemd xizmati sozlanmoqda (tg_checker.service)..."
cat << EOF > /etc/systemd/system/tg_checker.service
[Unit]
Description=Telegram Username Checker Django Service
After=network.target

[Service]
User=root
WorkingDirectory=${APP_DIR}
ExecStart=${APP_DIR}/venv/bin/gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 1 --threads 4 --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 6. Xizmatni yoqish
echo "[5/5] Servis ishga tushirilmoqda..."
systemctl daemon-reload
systemctl enable tg_checker
systemctl restart tg_checker

SERVER_IP=$(curl -s -4 ifconfig.me || hostname -I | awk '{print $1}')
echo ""
echo "========================================================"
echo " TABRIKLAYMIZ! Sayt muvaffaqiyatli ishga tushirildi!   "
echo " Manzil: http://${SERVER_IP}:8000                     "
echo " Servis holati: systemctl status tg_checker           "
echo " Servisni qayta ishga tushirish: systemctl restart tg_checker "
echo " Loglarni ko'rish: journalctl -u tg_checker -f        "
echo "========================================================"
