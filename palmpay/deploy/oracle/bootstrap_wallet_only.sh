#!/usr/bin/env bash
# Bootstrap VeinPay wallet-only backend on Ubuntu 22.04 (Oracle Ampere).
# Run as ubuntu user after uploading repo to /opt/veinpay/palmpay
set -euo pipefail

APP_DIR="/opt/veinpay/palmpay"
cd "$APP_DIR"

echo "==> Installing system packages..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git rsync curl

echo "==> Creating Python virtualenv..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel
export PYTHONPATH="$APP_DIR"

echo "==> Installing wallet-only Python deps (no torch)..."
pip install -r requirements-backend.txt

if [[ ! -f .env ]]; then
  echo "==> Creating .env from template — EDIT BEFORE PRODUCTION"
  cp deploy/oracle/env.production.example .env
  echo "    nano $APP_DIR/.env"
fi

mkdir -p data/store data/palmpay/kyc data/palmpay/enrollment

echo ""
echo "Bootstrap complete."
echo "Next steps:"
echo "  1. nano $APP_DIR/.env   # set AUTH_SECRET + SMTP"
echo "  2. source .venv/bin/activate && python scripts/run_backend.py   # test"
echo "  3. sudo cp deploy/oracle/veinpay.service /etc/systemd/system/"
echo "  4. sudo systemctl enable --now veinpay"
echo "  5. Configure nginx + certbot — see docs/FREE_DEPLOY_ORACLE.md"
