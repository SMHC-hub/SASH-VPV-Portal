"""Regenerate README.md with screenshot galleries."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"

HEADER = """# SASH-VPV Portal

## Project team

**University:** National University of Technology (NUTECH), Islamabad

| Role | Name | Email |
|------|------|-------|
| Project Lead | Syed Muhamamd Huzaifa Chishty | muhammadhuzaifaf22@nutech.edu.pk |
| Member | Shanza Rahim | shanzarahimf22@nutech.edu.pk |
| Member | Saud Akbar | saudakbarf22@nutech.edu.pk |
| Supervisor | Dr. Benish Fida (HoD Artificial Intelligence) | benish.fida@nutech.edu.pk |

**Dataset:** [SASH-VPV on Kaggle](https://www.kaggle.com/datasets/sashinoventures/sash-vpv-subcutaneous-vascular-palm-vein-data) — full corpus (2,667 images, 122 subjects) in `data/raw/img/`

## Project layout

```
├── data/
│   ├── raw/img/              # SASH-VPV dataset (2,667 images, 122 subjects)
│   └── processed/            # metadata.csv, visibility_tags.csv, cv_folds.csv
├── models/checkpoints/
│   ├── production/           # checkpoint_production_full.pt (deploy this)
│   ├── validation/           # checkpoint_validation_fold0_held_out.pt
│   └── legacy/               # checkpoint.pt (CPU baseline)
├── src/
│   ├── palm_vein/            # Core Python package (model, deployment)
│   └── xrtech/               # XRTECH MagicVein Plus SDK ctypes wrapper
├── backend/                  # FastAPI service (device, stream, enroll, recognize, hardware)
├── frontend/                 # React 19 + Vite + Tailwind v4 + shadcn/ui web app
├── palmpay/                  # VeinPay wallet + shop marketplace API + Flutter mobile
├── scripts/                  # CLI entry points + run_backend.py / run_frontend.cmd
├── docs/screenshots/         # Browser UI captures used in this README
├── training/gpu/             # GPU training wrappers + setup docs
├── tests/live/               # Real-time capture testing (enroll/ + probe/)
├── outputs/                  # metrics, logs, figures
└── docs/                     # PROJECT_PLAN.md, notes, reports
```

## Quick start

```bash
python -m venv venv
venv\\Scripts\\activate
pip install torch  # install CUDA build from pytorch.org if using GPU
pip install -r requirements.txt
```

## Common commands

| Task | Command |
|------|---------|
| Build metadata | `python scripts/build_metadata.py` |
| Tag visibility | `python scripts/tag_visibility.py` |
| Split CV folds | `python scripts/split_folds.py` |
| Train (production) | `python scripts/train_production.py` |
| Evaluate open-set | `python scripts/evaluate.py` |
| Deployment demo | `python scripts/deploy_demo.py` |
| Live photo test | `python scripts/live_test.py` |
| Tkinter dev capture | `python scripts/live_capture_test.py` |
| PalmPay backend | `cd palmpay && python scripts/run_backend.py` (port **8001**) |
| Frontend (Vite) | `cd frontend && npm run dev` (port **5173**, proxies `/api` → 8001) |
| Capture README screenshots | `python scripts/capture_readme_screenshots.py` |

## Deployment model

Use `models/checkpoints/production/checkpoint_production_full.pt` with `PalmVeinBiometricSystem` from `src/palm_vein/deployment.py`.

## Web application overview

VeinPay / SASH-VPV is a full-stack palm-vein biometric portal with role-based applications built into one React front end:

| Surface | Who uses it | Key routes |
|---------|-------------|------------|
| **Customer / marketing** | Public visitors & members | `/`, `/technology`, `/member/shop`, `/member/cart`, `/member/checkout` |
| **Admin panel** | System administrators | `/dashboard`, `/enroll`, `/recognize`, `/identities`, `/employees`, `/customers`, `/marketplace`, `/logs`, `/settings` |
| **Employee panel** | Workplace staff | `/employee/dashboard`, `/employee/attendance`, `/employee/activity`, `/employee/settings` |
| **Shop owner panel** | Marketplace merchants | `/owner/dashboard`, `/owner/products`, `/owner/shop`, `/owner/settings` |
| **Auth surfaces** | Everyone | `/login`, `/user/login`, `/employee/login`, `/owner/login`, `/kiosk` |

**Architecture**

- **Backend (PalmPay)** — FastAPI + SQLAlchemy/SQLite on `:8001` for auth, wallets, shop cart/checkout, palm enroll/recognize APIs.
- **Frontend** — React 19 + Vite + Tailwind + shadcn/ui. Dev server on `:5173` proxies `/api` to the backend.
- **Biometrics** — XRTECH MagicVein Plus NIR scanner for live enroll / verify / identify where hardware is attached.
- **Payments** — Online shop cart + palm-vein checkout (and JazzCash-related flows in the wallet stack).

**Run it (two terminals)**

```bash
# Terminal 1 — PalmPay / shop API on :8001
cd palmpay
python scripts/run_backend.py

# Terminal 2 — web UI on :5173
cd frontend
npm install
npm run dev
```

Open [http://127.0.0.1:5173/](http://127.0.0.1:5173/).

> Screenshots below were captured from a live local browser session against that stack.

---

## Mobile application

> **Coming soon in this README:** Flutter VeinPay wallet screens (Android APK), Google/email signup, KYC, payment PIN, top-up, P2P transfer, and palm kiosk enrollment. Place mobile captures under `docs/screenshots/mobile/` when ready.

---

"""


def img(path: str, caption: str) -> str:
    return f"![{caption}]({path})\n\n*{caption}*\n"


SECTIONS = [
    (
        "1. Admin panel",
        "Administrator console for device operations, enrollment, recognition, identity registry, staff/customers, marketplace oversight, audit logs, and system settings.",
        "admin",
        [
            ("01-dashboard.png", "Admin dashboard — operational overview and navigation into biometric workflows."),
            ("01-dashboard-full.png", "Admin dashboard (full page) — complete layout of metrics and shortcuts."),
            ("02-enroll.png", "Enrollment workspace — multi-capture palm registration wizard for new identities."),
            ("02-enroll-full.png", "Enrollment workspace (full page) — capture steps and operator guidance."),
            ("03-recognize.png", "Recognition console — live verify/identify against enrolled templates."),
            ("03-recognize-full.png", "Recognition console (full page) — confidence readout and probe controls."),
            ("10-recognize-identify-tab.png", "Identify tab — 1:N search across the gallery of enrolled palms."),
            ("11-recognize-verify-tab.png", "Verify tab — 1:1 confirmation against a claimed identity."),
            ("04-identities.png", "Identities registry — enrolled hands plus trained dataset classes."),
            ("04-identities-full.png", "Identities registry (full page) — searchable gallery of subjects."),
            ("05-employees.png", "Employees management — staff accounts linked to attendance workflows."),
            ("06-customers.png", "Customers management — member accounts for portal and marketplace."),
            ("07-marketplace.png", "Marketplace admin — approve shops, monitor catalog health, oversee commerce."),
            ("08-logs.png", "Recognition logs — accept/reject history for auditing match quality."),
            ("09-settings.png", "Admin settings — thresholds, security preferences, and account controls."),
        ],
    ),
    (
        "2. Customer panel (main / marketing)",
        "Public VeinPay customer experience: brand storytelling, technology explanation, solutions, and entry points into shop / palm enrollment.",
        "customer",
        [
            ("00-browser-open-home.png", "Home — first viewport when the portal opens in the browser."),
            ("01-home-hero.png", "Home hero — brand-first landing with primary call-to-action."),
            ("01-home-hero-full.png", "Home (full page) — hero through deeper marketing sections."),
            ("07-home-pipeline.png", "Recognition pipeline strip — frame → quality gate → match → decision."),
            ("08-home-features.png", "Feature cards — optics, model, and operator workflow highlights."),
            ("10-home-mid-cta.png", "Mid-page CTA — convert visitors into members or demo users."),
            ("09-home-footer.png", "Footer — secondary navigation and project links."),
            ("02-technology.png", "Technology page — how subcutaneous vein imaging and matching work."),
            ("02-technology-full.png", "Technology page (full page) — deep technical narrative."),
            ("03-how-it-works.png", "How it works — step-by-step user journey for enrollment and payment."),
            ("04-security.png", "Security page — privacy, liveness, and template protection messaging."),
            ("05-solutions.png", "Solutions page — workplace, retail, and wallet use-cases."),
            ("06-contact.png", "Contact page — reach the SASH-VPV project team."),
        ],
    ),
    (
        "3. Employee panel",
        "Workplace staff portal for palm-based attendance, activity history, and personal settings.",
        "employee",
        [
            ("01-dashboard.png", "Employee dashboard — today’s attendance status and quick actions."),
            ("01-dashboard-full.png", "Employee dashboard (full page)."),
            ("01-dashboard-scrolled.png", "Employee dashboard (scrolled) — additional widgets below the fold."),
            ("02-attendance.png", "Attendance page — check-in/out history tied to palm recognition events."),
            ("02-attendance-full.png", "Attendance page (full page)."),
            ("02-attendance-scrolled.png", "Attendance page (scrolled)."),
            ("03-activity.png", "Activity feed — recent scans and workplace events."),
            ("03-activity-full.png", "Activity feed (full page)."),
            ("03-activity-scrolled.png", "Activity feed (scrolled)."),
            ("04-settings.png", "Employee settings — profile and notification preferences."),
            ("04-settings-full.png", "Employee settings (full page)."),
            ("04-settings-scrolled.png", "Employee settings (scrolled)."),
        ],
    ),
    (
        "4. Shop tab",
        "Member marketplace catalog (VeinPay Demo Mart): browse categories, open product detail pages, and add items for palm checkout.",
        "shop",
        [
            ("01-shop-catalog.png", "Shop catalog — product grid with PKR pricing."),
            ("02-shop-catalog-full.png", "Shop catalog (full page) — complete demo assortment."),
            ("03-shop-mid-scroll.png", "Shop mid-scroll — deeper catalog rows."),
            ("04-shop-lower-scroll.png", "Shop lower scroll — clothing / grocery inventory."),
            ("05-shop-deep-scroll.png", "Shop deep scroll — end of catalog."),
            ("06-shop-filter-electronics.png", "Filter: Electronics."),
            ("07-shop-filter-clothing.png", "Filter: Clothing."),
            ("08-shop-filter-food.png", "Filter: Food & groceries."),
            ("09-shop-filter-all.png", "Filter: All products."),
            ("10-shop-filter-groceries.png", "Filter: Groceries view."),
            ("20-product-1.png", "Product detail — USB-C charging cable."),
            ("20-product-2.png", "Product detail — wireless earbuds."),
            ("20-product-3.png", "Product detail — phone screen protector."),
            ("20-product-4.png", "Product detail — power bank."),
            ("20-product-5.png", "Product detail — LED desk lamp."),
            ("20-product-6.png", "Product detail — men’s cotton t-shirt."),
        ],
    ),
    (
        "5. Cart and payment tab",
        "Cart, checkout, and palm-pay flow: add items, review bag, and pay using palm-vein confirmation (plus member enroll/scan helpers).",
        "cart",
        [
            ("01-shop-before-add.png", "Shop before add-to-cart."),
            ("02-after-add-1.png", "After adding first item."),
            ("03-after-add-2.png", "After adding second item."),
            ("04-after-add-3.png", "After adding third item."),
            ("05-after-add-4.png", "After adding fourth item."),
            ("06-after-add-5.png", "After adding fifth item."),
            ("08-cart-page.png", "Cart page — line items and totals."),
            ("11-cart-with-items.png", "Cart with items ready for checkout."),
            ("12-cart-with-items-full.png", "Cart with items (full page)."),
            ("13-checkout-page.png", "Checkout — order summary and payment methods."),
            ("14-checkout-page-full.png", "Checkout (full page) — palm-pay path visible."),
            ("15-checkout-palm-area.png", "Checkout palm-pay area — biometric confirmation step."),
            ("16-checkout-lower.png", "Checkout lower section — confirm / status UI."),
            ("17-member-enrollment.png", "Member enrollment helper — register palm before paying."),
            ("18-member-recognition.png", "Member recognition helper — scan palm to authorize payment."),
        ],
    ),
    (
        "6. Shop owner panel",
        "Merchant console for VeinPay Demo Mart: sales overview, product CRUD, public shop profile, and owner settings.",
        "owner",
        [
            ("01-dashboard.png", "Owner dashboard — sales/order snapshot."),
            ("01-dashboard-full.png", "Owner dashboard (full page)."),
            ("01-dashboard-scrolled.png", "Owner dashboard (scrolled)."),
            ("02-products.png", "Products manager — inventory list and stock controls."),
            ("02-products-full.png", "Products manager (full page)."),
            ("02-products-scrolled.png", "Products manager (scrolled)."),
            ("03-shop.png", "Shop profile editor — name, description, category, approval status."),
            ("03-shop-full.png", "Shop profile editor (full page)."),
            ("03-shop-scrolled.png", "Shop profile editor (scrolled)."),
            ("04-settings.png", "Owner settings — account and store preferences."),
            ("04-settings-full.png", "Owner settings (full page)."),
            ("04-settings-scrolled.png", "Owner settings (scrolled)."),
        ],
    ),
    (
        "7. Login and signup panels",
        "Role-specific authentication: admin, member, employee, shop owner, plus kiosk enrollment surfaces.",
        "auth",
        [
            ("01-admin-login.png", "Admin login — email/password for the operations console."),
            ("12-admin-login-filled.png", "Admin login (alternate capture)."),
            ("02-admin-signup.png", "Admin/staff signup entry (where enabled)."),
            ("03-member-login.png", "Member login — VeinPay customer authentication."),
            ("11-member-login-full.png", "Member login (full page)."),
            ("04-member-signup.png", "Member signup — create a customer wallet-linked account."),
            ("05-employee-login.png", "Employee login — email or palm method tabs."),
            ("06-employee-signup.png", "Employee signup — onboarding for workplace accounts."),
            ("14-employee-signup.png", "Employee signup (alternate capture)."),
            ("07-owner-login.png", "Shop owner login — merchant portal access."),
            ("13-owner-login-defaults.png", "Shop owner login with demo credentials fields."),
            ("08-kiosk.png", "Auth kiosk — palm login station UI."),
            ("09-kiosk-enroll.png", "Kiosk enroll — guided palm enrollment for members."),
        ],
    ),
    (
        "8. SASH-VPV dataset description (Customer panel)",
        "Dedicated marketing block on the customer home page describing the SASH-VPV subcutaneous vascular palm-vein corpus (2,667 images / 122 subjects) and Kaggle release.",
        "dataset",
        [
            ("01-dataset-section.png", "Dataset section — primary framed capture of the SASH-VPV contribution block."),
            ("02-dataset-section-wide.png", "Dataset section — wider viewport capture."),
            ("03-dataset-with-context-above.png", "Dataset section with content above (pipeline / story)."),
            ("04-dataset-with-context-below.png", "Dataset section with content below (features / stats)."),
            ("05-dataset-scroll-900.png", "Home scroll position ~900px around dataset."),
            ("06-dataset-scroll-1100.png", "Home scroll position ~1100px around dataset."),
            ("07-dataset-scroll-1300.png", "Home scroll position ~1300px around dataset."),
            ("08-dataset-scroll-1500.png", "Home scroll position ~1500px around dataset."),
            ("09-dataset-scroll-1700.png", "Home scroll position ~1700px around dataset."),
            ("10-dataset-scroll-1900.png", "Home scroll position ~1900px around dataset."),
        ],
    ),
]


def build_gallery() -> str:
    parts = ["## Web UI gallery (browser screenshots)\n"]
    parts.append(
        "All images live under [`docs/screenshots/`](docs/screenshots/) and were taken from Chromium against the local Vite app.\n"
    )
    for title, blurb, folder, items in SECTIONS:
        parts.append(f"### {title}\n")
        parts.append(f"{blurb}\n")
        for filename, caption in items:
            rel = f"docs/screenshots/{folder}/{filename}"
            if not (ROOT / rel).exists():
                continue
            parts.append(f"#### {caption.split(' — ')[0] if ' — ' in caption else caption}\n")
            parts.append(img(rel.replace('\\\\', '/'), caption))
        parts.append("\n")
    return "\n".join(parts)


FOOTER = """
## Documentation

- Design rationale: `docs/PROJECT_PLAN.md`
- Build summary: `docs/FINAL_SUMMARY.md`
- GPU setup: `training/gpu/SETUP.md`
- Re-capture screenshots: `python scripts/capture_readme_screenshots.py` (with backend + frontend running)
"""


def main() -> None:
    text = HEADER + build_gallery() + FOOTER
    README.write_text(text, encoding="utf-8")
    print(f"Wrote {README} ({len(text)} chars)")


if __name__ == "__main__":
    main()
