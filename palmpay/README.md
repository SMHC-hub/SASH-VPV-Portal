# VeinPay

Mobile wallet app with palm vein payments — standalone project built on the SASH-VPV recognition stack.

> **App name:** VeinPay (user-facing). Internal repo folder remains `palmpay/` for API compatibility.

## Structure

| Folder | Purpose |
|--------|---------|
| `mobile/` | Flutter app (Day 1+) |
| `backend/` | FastAPI copy from SASH-VPV (auth, enroll, recognize) |
| `src/palm_vein/` | ML model + inference |
| `src/xrtech/` | Palm scanner SDK |
| `models/checkpoints/` | Production checkpoint |
| `scripts/` | `run_backend.py` and utilities |
| `docs/` | Setup, architecture, **Oracle free deploy** |
| `deploy/oracle/` | systemd, nginx, bootstrap scripts for 24/7 cloud |
| `assets/` | Branding, icons |

## Quick start (standalone backend)

```powershell
cd palmpay
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install torch
pip install -r requirements.txt -r requirements-backend.txt
python scripts/run_backend.py
```

API: `http://localhost:8001` · Docs: `http://localhost:8001/docs`

## Deploy 24/7 for free (Oracle Cloud)

Run the backend on **any Wi‑Fi without your laptop** — **$0/month** on Oracle Always Free:

**[docs/FREE_DEPLOY_ORACLE.md](docs/FREE_DEPLOY_ORACLE.md)** — full step-by-step (VM, DuckDNS, HTTPS, APK rebuild)

Quick production APK build:

```powershell
$env:API_HOST="yourname.duckdns.org"
$env:API_PORT="443"
$env:API_HTTPS="true"
.\scripts\build_release_apk.ps1
.\scripts\install_release_apk.ps1
```

## Connect to parent backend instead

For development, you can skip running `palmpay/backend` and point the mobile app at the **parent** SASH-VPV backend already on port `8000`. See [docs/STANDALONE_SETUP.md](docs/STANDALONE_SETUP.md).

## Database

This stack uses **SQLite** (`data/store/app.db`), not PostgreSQL. PostgreSQL is planned later for production wallet ledger only.

## Status

- [x] Standalone copy of backend + ML + scanner SDK
- [x] Day 1: Backend on port 8001 + Flutter shell + API health wiring
- [x] Day 2: Phone OTP auth + JWT + secure storage
- [x] Day 3: KYC + palm enrollment flow (QR + dev kiosk simulate)
- [x] Day 4: Wallet balance, top-up (JazzCash dev), P2P transfer with spending PIN
- [x] Day 5: Palm Pay core — kiosk payment request, wallet debit, WebSocket result, scan tab + result screens
- [x] Day 11: Signup wizard, login PIN, fingerprint unlock, OTP fallback
- [x] Day 12: Email/password auth, signup wizard, 4-digit PIN, biometric login after sign out
- [x] Day 6: Transaction history (paginated), receipt detail, spending analytics charts
- [x] Day 7: Profile & security — wallet freeze, per-txn limits, device manager, notification preferences
- [x] Day 8: Polish — shimmer, offline banner, forms, animations, secure screens, rate limits, wallet cache, DB indexes
- [x] Day 9: Testing & security — pytest suite, Flutter unit tests, rate-limit/idempotency/concurrency tests, Locust script, release APK script, security checklist

**Next:** Day 10 — Play Store submission & closed beta launch

Full product plan: [PalmPay_Complete_Project_Plan.md](PalmPay_Complete_Project_Plan.md)

### Test palm payment (dev)

```powershell
# Terminal 1 — backend (restart after code updates)
cd palmpay
python scripts/run_backend.py

# Terminal 2 — Flutter app (hot restart with R after UI changes)
cd palmpay\mobile
flutter run --dart-define=API_HOST=192.168.18.114

# Terminal 3 — kiosk simulate (no websocket-client needed)
cd palmpay
python scripts/kiosk_payment_dev.py --base http://192.168.18.114:8001 --amount 250 --phone 03XXXXXXXXX
```

Open the **Scan** tab on the phone while the kiosk script runs. Use **Load Money** first if wallet balance is zero.
