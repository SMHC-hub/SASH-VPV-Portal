# SASH-VPV Portal

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
venv\Scripts\activate
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

## Web UI gallery (browser screenshots)

All images live under [`docs/screenshots/`](docs/screenshots/) and were taken from Chromium against the local Vite app.

### 1. Admin panel

Administrator console for device operations, enrollment, recognition, identity registry, staff/customers, marketplace oversight, audit logs, and system settings.

#### Admin dashboard

![Admin dashboard — operational overview and navigation into biometric workflows.](docs/screenshots/admin/01-dashboard.png)

*Admin dashboard — operational overview and navigation into biometric workflows.*

#### Admin dashboard (full page)

![Admin dashboard (full page) — complete layout of metrics and shortcuts.](docs/screenshots/admin/01-dashboard-full.png)

*Admin dashboard (full page) — complete layout of metrics and shortcuts.*

#### Enrollment workspace

![Enrollment workspace — multi-capture palm registration wizard for new identities.](docs/screenshots/admin/02-enroll.png)

*Enrollment workspace — multi-capture palm registration wizard for new identities.*

#### Enrollment workspace (full page)

![Enrollment workspace (full page) — capture steps and operator guidance.](docs/screenshots/admin/02-enroll-full.png)

*Enrollment workspace (full page) — capture steps and operator guidance.*

#### Recognition console

![Recognition console — live verify/identify against enrolled templates.](docs/screenshots/admin/03-recognize.png)

*Recognition console — live verify/identify against enrolled templates.*

#### Recognition console (full page)

![Recognition console (full page) — confidence readout and probe controls.](docs/screenshots/admin/03-recognize-full.png)

*Recognition console (full page) — confidence readout and probe controls.*

#### Identify tab

![Identify tab — 1:N search across the gallery of enrolled palms.](docs/screenshots/admin/10-recognize-identify-tab.png)

*Identify tab — 1:N search across the gallery of enrolled palms.*

#### Verify tab

![Verify tab — 1:1 confirmation against a claimed identity.](docs/screenshots/admin/11-recognize-verify-tab.png)

*Verify tab — 1:1 confirmation against a claimed identity.*

#### Identities registry

![Identities registry — enrolled hands plus trained dataset classes.](docs/screenshots/admin/04-identities.png)

*Identities registry — enrolled hands plus trained dataset classes.*

#### Identities registry (full page)

![Identities registry (full page) — searchable gallery of subjects.](docs/screenshots/admin/04-identities-full.png)

*Identities registry (full page) — searchable gallery of subjects.*

#### Employees management

![Employees management — staff accounts linked to attendance workflows.](docs/screenshots/admin/05-employees.png)

*Employees management — staff accounts linked to attendance workflows.*

#### Customers management

![Customers management — member accounts for portal and marketplace.](docs/screenshots/admin/06-customers.png)

*Customers management — member accounts for portal and marketplace.*

#### Marketplace admin

![Marketplace admin — approve shops, monitor catalog health, oversee commerce.](docs/screenshots/admin/07-marketplace.png)

*Marketplace admin — approve shops, monitor catalog health, oversee commerce.*

#### Recognition logs

![Recognition logs — accept/reject history for auditing match quality.](docs/screenshots/admin/08-logs.png)

*Recognition logs — accept/reject history for auditing match quality.*

#### Admin settings

![Admin settings — thresholds, security preferences, and account controls.](docs/screenshots/admin/09-settings.png)

*Admin settings — thresholds, security preferences, and account controls.*



### 2. Customer panel (main / marketing)

Public VeinPay customer experience: brand storytelling, technology explanation, solutions, and entry points into shop / palm enrollment.

#### Home

![Home — first viewport when the portal opens in the browser.](docs/screenshots/customer/00-browser-open-home.png)

*Home — first viewport when the portal opens in the browser.*

#### Home hero

![Home hero — brand-first landing with primary call-to-action.](docs/screenshots/customer/01-home-hero.png)

*Home hero — brand-first landing with primary call-to-action.*

#### Home (full page)

![Home (full page) — hero through deeper marketing sections.](docs/screenshots/customer/01-home-hero-full.png)

*Home (full page) — hero through deeper marketing sections.*

#### Recognition pipeline strip

![Recognition pipeline strip — frame → quality gate → match → decision.](docs/screenshots/customer/07-home-pipeline.png)

*Recognition pipeline strip — frame → quality gate → match → decision.*

#### Feature cards

![Feature cards — optics, model, and operator workflow highlights.](docs/screenshots/customer/08-home-features.png)

*Feature cards — optics, model, and operator workflow highlights.*

#### Mid-page CTA

![Mid-page CTA — convert visitors into members or demo users.](docs/screenshots/customer/10-home-mid-cta.png)

*Mid-page CTA — convert visitors into members or demo users.*

#### Footer

![Footer — secondary navigation and project links.](docs/screenshots/customer/09-home-footer.png)

*Footer — secondary navigation and project links.*

#### Technology page

![Technology page — how subcutaneous vein imaging and matching work.](docs/screenshots/customer/02-technology.png)

*Technology page — how subcutaneous vein imaging and matching work.*

#### Technology page (full page)

![Technology page (full page) — deep technical narrative.](docs/screenshots/customer/02-technology-full.png)

*Technology page (full page) — deep technical narrative.*

#### How it works

![How it works — step-by-step user journey for enrollment and payment.](docs/screenshots/customer/03-how-it-works.png)

*How it works — step-by-step user journey for enrollment and payment.*

#### Security page

![Security page — privacy, liveness, and template protection messaging.](docs/screenshots/customer/04-security.png)

*Security page — privacy, liveness, and template protection messaging.*

#### Solutions page

![Solutions page — workplace, retail, and wallet use-cases.](docs/screenshots/customer/05-solutions.png)

*Solutions page — workplace, retail, and wallet use-cases.*

#### Contact page

![Contact page — reach the SASH-VPV project team.](docs/screenshots/customer/06-contact.png)

*Contact page — reach the SASH-VPV project team.*



### 3. Employee panel

Workplace staff portal for palm-based attendance, activity history, and personal settings.

#### Employee dashboard

![Employee dashboard — today’s attendance status and quick actions.](docs/screenshots/employee/01-dashboard.png)

*Employee dashboard — today’s attendance status and quick actions.*

#### Employee dashboard (full page).

![Employee dashboard (full page).](docs/screenshots/employee/01-dashboard-full.png)

*Employee dashboard (full page).*

#### Employee dashboard (scrolled)

![Employee dashboard (scrolled) — additional widgets below the fold.](docs/screenshots/employee/01-dashboard-scrolled.png)

*Employee dashboard (scrolled) — additional widgets below the fold.*

#### Attendance page

![Attendance page — check-in/out history tied to palm recognition events.](docs/screenshots/employee/02-attendance.png)

*Attendance page — check-in/out history tied to palm recognition events.*

#### Attendance page (full page).

![Attendance page (full page).](docs/screenshots/employee/02-attendance-full.png)

*Attendance page (full page).*

#### Attendance page (scrolled).

![Attendance page (scrolled).](docs/screenshots/employee/02-attendance-scrolled.png)

*Attendance page (scrolled).*

#### Activity feed

![Activity feed — recent scans and workplace events.](docs/screenshots/employee/03-activity.png)

*Activity feed — recent scans and workplace events.*

#### Activity feed (full page).

![Activity feed (full page).](docs/screenshots/employee/03-activity-full.png)

*Activity feed (full page).*

#### Activity feed (scrolled).

![Activity feed (scrolled).](docs/screenshots/employee/03-activity-scrolled.png)

*Activity feed (scrolled).*

#### Employee settings

![Employee settings — profile and notification preferences.](docs/screenshots/employee/04-settings.png)

*Employee settings — profile and notification preferences.*

#### Employee settings (full page).

![Employee settings (full page).](docs/screenshots/employee/04-settings-full.png)

*Employee settings (full page).*

#### Employee settings (scrolled).

![Employee settings (scrolled).](docs/screenshots/employee/04-settings-scrolled.png)

*Employee settings (scrolled).*



### 4. Shop tab

Member marketplace catalog (VeinPay Demo Mart): browse categories, open product detail pages, and add items for palm checkout.

#### Shop catalog

![Shop catalog — product grid with PKR pricing.](docs/screenshots/shop/01-shop-catalog.png)

*Shop catalog — product grid with PKR pricing.*

#### Shop catalog (full page)

![Shop catalog (full page) — complete demo assortment.](docs/screenshots/shop/02-shop-catalog-full.png)

*Shop catalog (full page) — complete demo assortment.*

#### Shop mid-scroll

![Shop mid-scroll — deeper catalog rows.](docs/screenshots/shop/03-shop-mid-scroll.png)

*Shop mid-scroll — deeper catalog rows.*

#### Shop lower scroll

![Shop lower scroll — clothing / grocery inventory.](docs/screenshots/shop/04-shop-lower-scroll.png)

*Shop lower scroll — clothing / grocery inventory.*

#### Shop deep scroll

![Shop deep scroll — end of catalog.](docs/screenshots/shop/05-shop-deep-scroll.png)

*Shop deep scroll — end of catalog.*

#### Filter: Electronics.

![Filter: Electronics.](docs/screenshots/shop/06-shop-filter-electronics.png)

*Filter: Electronics.*

#### Filter: Clothing.

![Filter: Clothing.](docs/screenshots/shop/07-shop-filter-clothing.png)

*Filter: Clothing.*

#### Filter: Food & groceries.

![Filter: Food & groceries.](docs/screenshots/shop/08-shop-filter-food.png)

*Filter: Food & groceries.*

#### Filter: All products.

![Filter: All products.](docs/screenshots/shop/09-shop-filter-all.png)

*Filter: All products.*

#### Filter: Groceries view.

![Filter: Groceries view.](docs/screenshots/shop/10-shop-filter-groceries.png)

*Filter: Groceries view.*

#### Product detail

![Product detail — USB-C charging cable.](docs/screenshots/shop/20-product-1.png)

*Product detail — USB-C charging cable.*

#### Product detail

![Product detail — wireless earbuds.](docs/screenshots/shop/20-product-2.png)

*Product detail — wireless earbuds.*

#### Product detail

![Product detail — phone screen protector.](docs/screenshots/shop/20-product-3.png)

*Product detail — phone screen protector.*

#### Product detail

![Product detail — power bank.](docs/screenshots/shop/20-product-4.png)

*Product detail — power bank.*

#### Product detail

![Product detail — LED desk lamp.](docs/screenshots/shop/20-product-5.png)

*Product detail — LED desk lamp.*

#### Product detail

![Product detail — men’s cotton t-shirt.](docs/screenshots/shop/20-product-6.png)

*Product detail — men’s cotton t-shirt.*



### 5. Cart and payment tab

Cart, checkout, and palm-pay flow: add items, review bag, and pay using palm-vein confirmation (plus member enroll/scan helpers).

#### Shop before add-to-cart.

![Shop before add-to-cart.](docs/screenshots/cart/01-shop-before-add.png)

*Shop before add-to-cart.*

#### After adding first item.

![After adding first item.](docs/screenshots/cart/02-after-add-1.png)

*After adding first item.*

#### After adding second item.

![After adding second item.](docs/screenshots/cart/03-after-add-2.png)

*After adding second item.*

#### After adding third item.

![After adding third item.](docs/screenshots/cart/04-after-add-3.png)

*After adding third item.*

#### After adding fourth item.

![After adding fourth item.](docs/screenshots/cart/05-after-add-4.png)

*After adding fourth item.*

#### After adding fifth item.

![After adding fifth item.](docs/screenshots/cart/06-after-add-5.png)

*After adding fifth item.*

#### Cart page

![Cart page — line items and totals.](docs/screenshots/cart/08-cart-page.png)

*Cart page — line items and totals.*

#### Cart with items ready for checkout.

![Cart with items ready for checkout.](docs/screenshots/cart/11-cart-with-items.png)

*Cart with items ready for checkout.*

#### Cart with items (full page).

![Cart with items (full page).](docs/screenshots/cart/12-cart-with-items-full.png)

*Cart with items (full page).*

#### Checkout

![Checkout — order summary and payment methods.](docs/screenshots/cart/13-checkout-page.png)

*Checkout — order summary and payment methods.*

#### Checkout (full page)

![Checkout (full page) — palm-pay path visible.](docs/screenshots/cart/14-checkout-page-full.png)

*Checkout (full page) — palm-pay path visible.*

#### Checkout palm-pay area

![Checkout palm-pay area — biometric confirmation step.](docs/screenshots/cart/15-checkout-palm-area.png)

*Checkout palm-pay area — biometric confirmation step.*

#### Checkout lower section

![Checkout lower section — confirm / status UI.](docs/screenshots/cart/16-checkout-lower.png)

*Checkout lower section — confirm / status UI.*

#### Member enrollment helper

![Member enrollment helper — register palm before paying.](docs/screenshots/cart/17-member-enrollment.png)

*Member enrollment helper — register palm before paying.*

#### Member recognition helper

![Member recognition helper — scan palm to authorize payment.](docs/screenshots/cart/18-member-recognition.png)

*Member recognition helper — scan palm to authorize payment.*



### 6. Shop owner panel

Merchant console for VeinPay Demo Mart: sales overview, product CRUD, public shop profile, and owner settings.

#### Owner dashboard

![Owner dashboard — sales/order snapshot.](docs/screenshots/owner/01-dashboard.png)

*Owner dashboard — sales/order snapshot.*

#### Owner dashboard (full page).

![Owner dashboard (full page).](docs/screenshots/owner/01-dashboard-full.png)

*Owner dashboard (full page).*

#### Owner dashboard (scrolled).

![Owner dashboard (scrolled).](docs/screenshots/owner/01-dashboard-scrolled.png)

*Owner dashboard (scrolled).*

#### Products manager

![Products manager — inventory list and stock controls.](docs/screenshots/owner/02-products.png)

*Products manager — inventory list and stock controls.*

#### Products manager (full page).

![Products manager (full page).](docs/screenshots/owner/02-products-full.png)

*Products manager (full page).*

#### Products manager (scrolled).

![Products manager (scrolled).](docs/screenshots/owner/02-products-scrolled.png)

*Products manager (scrolled).*

#### Shop profile editor

![Shop profile editor — name, description, category, approval status.](docs/screenshots/owner/03-shop.png)

*Shop profile editor — name, description, category, approval status.*

#### Shop profile editor (full page).

![Shop profile editor (full page).](docs/screenshots/owner/03-shop-full.png)

*Shop profile editor (full page).*

#### Shop profile editor (scrolled).

![Shop profile editor (scrolled).](docs/screenshots/owner/03-shop-scrolled.png)

*Shop profile editor (scrolled).*

#### Owner settings

![Owner settings — account and store preferences.](docs/screenshots/owner/04-settings.png)

*Owner settings — account and store preferences.*

#### Owner settings (full page).

![Owner settings (full page).](docs/screenshots/owner/04-settings-full.png)

*Owner settings (full page).*

#### Owner settings (scrolled).

![Owner settings (scrolled).](docs/screenshots/owner/04-settings-scrolled.png)

*Owner settings (scrolled).*



### 7. Login and signup panels

Role-specific authentication: admin, member, employee, shop owner, plus kiosk enrollment surfaces.

#### Admin login

![Admin login — email/password for the operations console.](docs/screenshots/auth/01-admin-login.png)

*Admin login — email/password for the operations console.*

#### Admin login (alternate capture).

![Admin login (alternate capture).](docs/screenshots/auth/12-admin-login-filled.png)

*Admin login (alternate capture).*

#### Admin/staff signup entry (where enabled).

![Admin/staff signup entry (where enabled).](docs/screenshots/auth/02-admin-signup.png)

*Admin/staff signup entry (where enabled).*

#### Member login

![Member login — VeinPay customer authentication.](docs/screenshots/auth/03-member-login.png)

*Member login — VeinPay customer authentication.*

#### Member login (full page).

![Member login (full page).](docs/screenshots/auth/11-member-login-full.png)

*Member login (full page).*

#### Member signup

![Member signup — create a customer wallet-linked account.](docs/screenshots/auth/04-member-signup.png)

*Member signup — create a customer wallet-linked account.*

#### Employee login

![Employee login — email or palm method tabs.](docs/screenshots/auth/05-employee-login.png)

*Employee login — email or palm method tabs.*

#### Employee signup

![Employee signup — onboarding for workplace accounts.](docs/screenshots/auth/06-employee-signup.png)

*Employee signup — onboarding for workplace accounts.*

#### Employee signup (alternate capture).

![Employee signup (alternate capture).](docs/screenshots/auth/14-employee-signup.png)

*Employee signup (alternate capture).*

#### Shop owner login

![Shop owner login — merchant portal access.](docs/screenshots/auth/07-owner-login.png)

*Shop owner login — merchant portal access.*

#### Shop owner login with demo credentials fields.

![Shop owner login with demo credentials fields.](docs/screenshots/auth/13-owner-login-defaults.png)

*Shop owner login with demo credentials fields.*

#### Auth kiosk

![Auth kiosk — palm login station UI.](docs/screenshots/auth/08-kiosk.png)

*Auth kiosk — palm login station UI.*

#### Kiosk enroll

![Kiosk enroll — guided palm enrollment for members.](docs/screenshots/auth/09-kiosk-enroll.png)

*Kiosk enroll — guided palm enrollment for members.*



### 8. SASH-VPV dataset description (Customer panel)

Dedicated marketing block on the customer home page describing the SASH-VPV subcutaneous vascular palm-vein corpus (2,667 images / 122 subjects) and Kaggle release.

#### Dataset section

![Dataset section — primary framed capture of the SASH-VPV contribution block.](docs/screenshots/dataset/01-dataset-section.png)

*Dataset section — primary framed capture of the SASH-VPV contribution block.*

#### Dataset section

![Dataset section — wider viewport capture.](docs/screenshots/dataset/02-dataset-section-wide.png)

*Dataset section — wider viewport capture.*

#### Dataset section with content above (pipeline / story).

![Dataset section with content above (pipeline / story).](docs/screenshots/dataset/03-dataset-with-context-above.png)

*Dataset section with content above (pipeline / story).*

#### Dataset section with content below (features / stats).

![Dataset section with content below (features / stats).](docs/screenshots/dataset/04-dataset-with-context-below.png)

*Dataset section with content below (features / stats).*

#### Home scroll position ~900px around dataset.

![Home scroll position ~900px around dataset.](docs/screenshots/dataset/05-dataset-scroll-900.png)

*Home scroll position ~900px around dataset.*

#### Home scroll position ~1100px around dataset.

![Home scroll position ~1100px around dataset.](docs/screenshots/dataset/06-dataset-scroll-1100.png)

*Home scroll position ~1100px around dataset.*

#### Home scroll position ~1300px around dataset.

![Home scroll position ~1300px around dataset.](docs/screenshots/dataset/07-dataset-scroll-1300.png)

*Home scroll position ~1300px around dataset.*

#### Home scroll position ~1500px around dataset.

![Home scroll position ~1500px around dataset.](docs/screenshots/dataset/08-dataset-scroll-1500.png)

*Home scroll position ~1500px around dataset.*

#### Home scroll position ~1700px around dataset.

![Home scroll position ~1700px around dataset.](docs/screenshots/dataset/09-dataset-scroll-1700.png)

*Home scroll position ~1700px around dataset.*

#### Home scroll position ~1900px around dataset.

![Home scroll position ~1900px around dataset.](docs/screenshots/dataset/10-dataset-scroll-1900.png)

*Home scroll position ~1900px around dataset.*



## Documentation

- Design rationale: `docs/PROJECT_PLAN.md`
- Build summary: `docs/FINAL_SUMMARY.md`
- GPU setup: `training/gpu/SETUP.md`
- Re-capture screenshots: `python scripts/capture_readme_screenshots.py` (with backend + frontend running)

