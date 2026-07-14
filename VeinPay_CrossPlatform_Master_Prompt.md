# MASTER PROMPT — VeinPay × Web App Cross-Platform Integration
## Deep Analysis · Full Architecture · Communication Logic · Feature Specification

---

> **HOW TO USE THIS PROMPT**
> Copy this entire document and paste it into any AI assistant (Claude, GPT-4, Gemini)
> as your opening message. It is self-contained. The AI will analyze both systems,
> understand their relationship, and produce whatever output you request next.

---

## ═══════════════════════════════════════════════
## SECTION 0 — CONTEXT & ROLE ASSIGNMENT
## ═══════════════════════════════════════════════

You are a senior full-stack architect with 15+ years of experience in:
- Biometric systems integration (palm vein, fingerprint, facial recognition)
- Fintech backend architecture (wallets, payments, ledger systems)
- Cross-platform web + mobile communication (REST, WebSocket, shared backends)
- E-commerce systems (cart, inventory, checkout, order management)
- Security-first system design (authentication, authorization, biometric auth flows)

Your task is to deeply analyze TWO existing systems — a web application and a mobile
wallet application — understand their current state, their users, their data models,
and their business logic, then reason about how they connect to a shared backend,
how new features layer on top, and how the entire ecosystem functions as one product.

Read every section below carefully before producing any output. Your analysis must
be logically consistent, technically grounded, and cover every edge case described.

---

## ═══════════════════════════════════════════════
## SECTION 1 — SYSTEM OVERVIEW (WHAT EXISTS TODAY)
## ═══════════════════════════════════════════════

There are currently TWO separate applications sharing ONE backend:

```
┌─────────────────────────────────────────────────────┐
│                  SHARED BACKEND                      │
│            (FastAPI + PostgreSQL + Redis)             │
│    Palm Vein ML Model · JWT Auth · Wallet Ledger     │
└────────────────┬────────────────┬───────────────────┘
                 │                │
    ┌────────────▼───┐    ┌───────▼──────────────┐
    │   WEB APP       │    │   MOBILE APP          │
    │  (Browser)      │    │  (Android · Flutter)  │
    │                 │    │                        │
    │  3 panels:      │    │  VeinPay Wallet        │
    │  · Shop Owner   │    │  · Account creation    │
    │  · Admin        │    │  · Balance top-up      │
    │  · Customer     │    │  · Send money          │
    └─────────────────┘    └────────────────────────┘
```

Both apps talk to THE SAME backend API. They share the same user accounts,
the same wallet balances, the same palm vein templates, the same transaction
history. They are two interfaces into one unified system.

---

## ═══════════════════════════════════════════════
## SECTION 2 — WEB APPLICATION (CURRENT STATE)
## ═══════════════════════════════════════════════

### 2.1 Technology Stack (Web App)
- Frontend: React.js / Next.js (browser-based)
- Backend: FastAPI (Python) — shared with mobile app
- Database: PostgreSQL — shared with mobile app
- Auth: JWT tokens (same auth system as mobile)
- Palm Vein: NIR camera connected to kiosk/PC, model runs server-side

### 2.2 Web App — Three Panels (Current State)

#### PANEL A: Employee Panel → NOW RENAMED: Shop Owner Panel
**Previous purpose:** Employee attendance tracking, timely activity calculation
**New purpose (as described):** Product/inventory management for shop owners

Current features being REPLACED:
- Employee check-in / check-out logs
- Activity time calculation per employee
- Attendance reports

New features being ADDED (Shop Owner Panel):
- Add / edit / delete products (items for sale)
- Set product name, description, price (PKR), category, stock quantity
- Upload product images
- Manage inventory (adjust quantities, mark out-of-stock)
- View orders placed by customers
- View sales history and revenue
- Manage their shop profile (shop name, logo, description)

**Who uses this panel:**
A shop owner / merchant who has registered on the platform, been approved by admin,
and wants to list their products for customers to buy online using palm vein payment.

**Data this panel owns:**
- Products table (id, shop_id, name, description, price_pkr, category,
  stock_qty, image_url, is_active, created_at)
- Orders table (from customer purchases)
- Shop profile (id, owner_user_id, shop_name, logo_url, description, is_approved)

---

#### PANEL B: Admin Panel (Unchanged role, expanded responsibilities)

Current features:
- Manage all users (customers + shop owners)
- Verify / approve palm enrollments
- View system-wide activity
- Control access levels

New responsibilities added:
- Approve / reject shop owner registration requests
- Review and moderate product listings (flag inappropriate items)
- View all transactions across the platform
- Manage platform-wide settings (commission rates, limits)
- View cross-platform analytics (web orders, mobile wallet usage, palm scan events)

**Who uses this panel:**
The platform super-administrator. One or few trusted operators.

---

#### PANEL C: Customer / User Panel (Major update — new Shop tab added)

Current features:
- Home tab: landing/dashboard
- Contact Us tab: support form
- Login / Sign Up flow
- Palm enrollment (NIR camera scan at kiosk/PC — 3 scans captured)
- Palm recognition test
- Info/profile panel

New feature being ADDED:
- **Shop tab** (described in full in Section 4 below)

**Who uses this panel:**
End customers / buyers. They browse products, add to cart, and pay using their
palm vein — which deducts money from their VeinPay mobile wallet.

---

### 2.3 Palm Enrollment & Recognition — Web App Only

**Critical architectural fact:**
Palm enrollment and palm recognition ONLY happen in the web application.
The mobile wallet app (VeinPay) has NO camera, NO palm scanning, NO biometric
capture of any kind.

This means:
- A customer MUST visit a web-enabled kiosk/terminal to enroll their palm
- The NIR camera is attached to the kiosk/PC running the web app
- The palm template (encrypted feature vector) is stored server-side
- The mobile app simply holds the wallet balance
- When a palm is scanned at checkout (web), the backend matches the palm,
  finds the linked user, checks their wallet balance (shared DB), and
  deducts the amount — all without the mobile app being open or involved

The mobile app is notified AFTER the transaction via Firebase push notification.

---

## ═══════════════════════════════════════════════
## SECTION 3 — MOBILE APPLICATION (CURRENT STATE)
## ═══════════════════════════════════════════════

### 3.1 Technology Stack (Mobile App)
- Framework: Flutter (Android primary)
- State management: Riverpod
- Network: Dio with JWT interceptor
- Storage: FlutterSecureStorage (tokens), Hive (local cache)
- Push: Firebase Cloud Messaging (FCM)
- Backend: Same FastAPI backend as web app
- Database: Same PostgreSQL as web app

### 3.2 App Name: VeinPay

### 3.3 Current Features
- Account creation (phone + CNIC verification)
- Wallet balance display
- Top-up (via JazzCash / bank transfer)
- Send money (P2P transfer to another VeinPay user)
- Transaction history
- Basic profile management

### 3.4 What VeinPay Does NOT Do
- No palm enrollment (no NIR camera on phone)
- No palm recognition / biometric scanning
- No product browsing
- No cart or checkout
- No order placement

### 3.5 How VeinPay Connects to the Web App

They share the SAME user account. When a customer registers on the web app
customer panel, the same credentials work on VeinPay. They are one account,
two interfaces.

The wallet balance in VeinPay is the SAME balance used when the customer pays
at the web shop using palm. There is one wallet per user, one balance, one ledger.

The transaction history in VeinPay will show BOTH:
- Transactions initiated from the mobile app (top-up, P2P send)
- Transactions triggered by palm scan at web checkout (shop purchases)

This is the core connection: the mobile wallet is the payment instrument.
The web palm scan is the authentication mechanism. Together they form one
complete payment system.

---

## ═══════════════════════════════════════════════
## SECTION 4 — NEW FEATURE: SHOP TAB (WEB — CUSTOMER PANEL)
## ═══════════════════════════════════════════════

### 4.1 Overview

A new "Shop" tab added to the Customer Panel of the web application.
It functions as an online marketplace where customers browse and buy products
listed by approved shop owners. Payment is exclusively via palm vein scan,
which deducts from the customer's VeinPay mobile wallet balance.

### 4.2 Shop Tab Visibility Rule

```
IS USER LOGGED IN?
       │
   NO  │  YES
       │
┌──────┴──────┐     ┌────────────────────────────────┐
│ Shop tab     │     │ Shop tab VISIBLE + FUNCTIONAL   │
│ VISIBLE      │     │ Cart accessible                 │
│ Browse only  │     │ Checkout requires palm enrolled │
│ Can add to   │     │ Palm scan → wallet deduction    │
│ cart freely  │     └────────────────────────────────┘
│ Checkout     │
│ prompts      │
│ login first  │
└─────────────┘
```

**Rule:** Shop tab is ALWAYS visible. Browsing and adding to cart require no login.
Authentication is only required at the moment of checkout / payment.

### 4.3 Shop Tab — UI Layout & Components

```
SHOP TAB — FULL LAYOUT

┌─────────────────────────────────────────────────────────────┐
│  HEADER: Search bar · Filter by category · Sort (price/new) │
├─────────────────────────────────────────────────────────────┤
│  CATEGORY PILLS: All · Electronics · Clothing · Food ·      │
│                  Accessories · Books · Home · Beauty · More  │
├─────────────────────────────────────────────────────────────┤
│  PRODUCT GRID (responsive, 3-4 columns on desktop,          │
│                2 columns on tablet, 1 on mobile)             │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ [image]  │  │ [image]  │  │ [image]  │  │ [image]  │   │
│  │ Item name│  │ Item name│  │ Item name│  │ Item name│   │
│  │ PKR 1200 │  │ PKR 450  │  │ PKR 3500 │  │ PKR 890  │   │
│  │ ★★★★☆   │  │ ★★★☆☆   │  │ ★★★★★   │  │ ★★★★☆   │   │
│  │ By: Shop │  │ By: Shop │  │ By: Shop │  │ By: Shop │   │
│  │[Add Cart]│  │[Add Cart]│  │[Add Cart]│  │[Add Cart]│   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  [Load more / infinite scroll]                               │
└─────────────────────────────────────────────────────────────┘
│  FLOATING CART ICON (top-right) · Badge shows item count    │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 Product Card — Data Fields

Each product card displays:
- Product image (uploaded by shop owner)
- Product name
- Short description (1–2 lines, truncated)
- Price in PKR (formatted: PKR 1,200)
- Star rating (average from buyers)
- Shop name (who is selling)
- Stock status (In Stock / Only 3 left / Out of Stock)
- "Add to Cart" button (or quantity +/- if already in cart)

Clicking a product opens a Product Detail Page:
- Full image gallery (multiple photos)
- Full description
- Category
- Price
- Quantity selector
- Stock quantity available
- Shop name + shop rating
- Customer reviews section
- "Add to Cart" button (prominent)

### 4.5 Cart System

Cart is stored in:
- **Browser localStorage** if user is NOT logged in (temporary, session-based)
- **Backend database** (cart table) if user IS logged in (persistent across devices)

On login: localStorage cart is merged with backend cart automatically.

Cart page shows:
- List of selected items (image, name, qty, unit price, line total)
- Quantity adjustment (+ / - per item)
- Remove item button
- Cart subtotal
- Any applicable fees (platform fee, if configured by admin)
- **Grand Total in PKR**
- Payment Method: "Pay with Palm Vein (VeinPay Wallet)"
- "Proceed to Pay" button

### 4.6 Checkout & Payment Flow — Complete Decision Tree

```
USER CLICKS "PROCEED TO PAY"
              │
              ▼
    Is user logged in?
    ┌────NO───┴────YES─────┐
    │                       │
    ▼                       ▼
Show modal:          Is palm enrolled
"Login or            in web system?
Register to          ┌──NO──┴──YES──┐
continue"            │               │
    │                ▼               ▼
    │          Show prompt:    Check VeinPay
    │          "Enroll your    wallet balance
    │          palm first"          │
    │               │         ┌─INSUFFICIENT─┐
    │          Navigate to    │               │
    │          Palm Enroll    ▼               ▼
    │          Page (web)   Show dialog:   Navigate to
    │               │       "Insufficient  Palm Scan
    │          After enroll  balance.       Page
    │          complete:     Top up from        │
    │          auto-return   VeinPay app"   User places
    │          to cart +              │     palm on
    │          show items             │     NIR camera
    │          + scan button          │         │
    │                                 │    Palm matched?
    │                            ┌────┴────NO──┴──YES──┐
    │                            │                       │
    │                            ▼                       ▼
    │                      "Face not           Deduct amount
    │                       recognized.        from wallet
    │                       Try again"         (backend)
    │                      (up to 3x)              │
    │                            │             Show success:
    │                            │             Order confirmed
    │                            │             Receipt shown
    │                            │             Push notif to
    │                            │             VeinPay mobile
    ▼                            │                   │
Redirect to                      ▼             Order stored
Login page                 After 3 fails:      in DB
with cart                  "Use alternate      Transaction in
preserved                  method or           history (web
(localStorage)             contact support"    + mobile app)
```

### 4.7 Palm Enrollment Flow (If Not Enrolled)

When customer is logged in but has no enrolled palm:

1. Show informational dialog:
   - "You need to enroll your palm vein to pay"
   - "Place your hand on the NIR scanner connected to this device"
   - "This takes less than 30 seconds"
   - Button: "Start Enrollment"

2. Navigate to Palm Enrollment Page (already exists in current web app)

3. Capture 3 scans (existing flow — unchanged)

4. On enrollment success:
   - Show: "Palm enrolled successfully!"
   - Auto-navigate back to: Cart Review Page
   - Show previously selected items still in cart
   - Show total amount
   - Show: "Scan your palm to pay PKR [amount]"
   - "Scan & Pay" button

### 4.8 Palm Scan & Payment Page

This page appears after all checks pass (logged in + enrolled + sufficient balance):

```
┌─────────────────────────────────────────────────────────────┐
│  ORDER SUMMARY                                               │
│  ─────────────────────────────────────────────────────────  │
│  [Item 1 name]          x2    PKR 2,400                     │
│  [Item 2 name]          x1    PKR 1,200                     │
│  ─────────────────────────────────────────────────────────  │
│  Total:                        PKR 3,600                     │
│  Payment: VeinPay Wallet (Balance: PKR 12,500)               │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                                                        │  │
│  │          [Animated NIR scanner viewport]               │  │
│  │          Teal corner brackets + sweep line             │  │
│  │          "Place your palm on the scanner"              │  │
│  │                                                        │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  [SCAN & PAY — PKR 3,600]   ← primary CTA button            │
│  [Cancel]                                                     │
└─────────────────────────────────────────────────────────────┘
```

On successful scan and payment:
- Green success animation
- Order confirmation number shown
- "Your VeinPay wallet has been debited PKR 3,600"
- "Check VeinPay app for receipt"
- "Continue Shopping" button

---

## ═══════════════════════════════════════════════
## SECTION 5 — SHOP OWNER PANEL (RENAMED FROM EMPLOYEE PANEL)
## ═══════════════════════════════════════════════

### 5.1 Who Is a Shop Owner?

A shop owner is a registered user who has been approved by the Admin to sell
products on the platform. They manage their own inventory, set their own prices,
and receive payments (minus platform commission) to their VeinPay wallet.

### 5.2 Shop Owner Registration Flow

1. Register as normal user (phone + CNIC)
2. In web app: apply to become a shop owner (fill shop details form)
3. Admin reviews and approves/rejects
4. On approval: Shop Owner panel unlocked in web app

### 5.3 Shop Owner Panel — Full Feature Set

#### Dashboard Tab
- Today's sales (PKR total)
- Today's orders (count)
- Products listed (count)
- Low stock alerts
- Recent orders table (last 10)
- Revenue chart (weekly/monthly toggle)

#### Products Tab
- Product list (sortable by name, price, stock, date added)
- "Add New Product" button → opens product form:
  - Product name (required)
  - Category (dropdown: Electronics / Clothing / Food / etc.)
  - Short description (150 chars)
  - Full description (rich text editor)
  - Price in PKR (required, number input)
  - Stock quantity (number input)
  - Product images (upload, multiple, drag-reorder)
  - Active/Inactive toggle (hide from shop without deleting)
  - Submit → pending admin review OR auto-approved (admin setting)
- Edit existing product (same form, pre-filled)
- Delete product (confirmation dialog)
- Bulk actions (mark inactive, delete selected)

#### Orders Tab
- Incoming orders list
- Each order: Order ID · Customer name · Items · Total PKR · Date · Status
- Order statuses: Pending → Processing → Shipped → Delivered → Cancelled
- Shop owner updates status (e.g., mark as "Processing", add tracking info)
- Filter by status, date range

#### Inventory Tab
- Products with low stock highlighted (< 5 units)
- Quick quantity adjustment without opening full edit form
- Stock history log (when quantities changed and by whom)

#### Earnings Tab
- Total lifetime earnings
- Pending payouts (orders completed but not yet settled)
- Settled payouts (transferred to VeinPay wallet)
- Settlement schedule (e.g., weekly auto-settlement)
- Earnings breakdown by product

#### Settings Tab
- Shop name, description, logo upload
- Business category
- Contact details (shown to customers)
- Bank/wallet details for payouts (linked VeinPay wallet)

### 5.4 Product Data Model

```
products table:
  id              UUID PRIMARY KEY
  shop_id         UUID → shops.id
  name            VARCHAR(255) NOT NULL
  slug            VARCHAR(255) UNIQUE (for URL)
  description     TEXT
  short_desc      VARCHAR(300)
  category        VARCHAR(100)
  price_pkr       DECIMAL(12,2) NOT NULL
  stock_qty       INTEGER DEFAULT 0
  images          JSONB  → [{url, order, is_primary}]
  avg_rating      DECIMAL(3,2) DEFAULT 0.00
  review_count    INTEGER DEFAULT 0
  is_active       BOOLEAN DEFAULT true
  is_approved     BOOLEAN DEFAULT false
  created_at      TIMESTAMPTZ DEFAULT NOW()
  updated_at      TIMESTAMPTZ DEFAULT NOW()

shops table:
  id              UUID PRIMARY KEY
  owner_user_id   UUID → users.id
  name            VARCHAR(255) NOT NULL
  slug            VARCHAR(255) UNIQUE
  description     TEXT
  logo_url        VARCHAR(500)
  category        VARCHAR(100)
  is_approved     BOOLEAN DEFAULT false
  approved_by     UUID → users.id (admin)
  approved_at     TIMESTAMPTZ
  wallet_id       UUID → wallets.id
  commission_rate DECIMAL(5,4) DEFAULT 0.05 (5%)
  created_at      TIMESTAMPTZ DEFAULT NOW()
```

---

## ═══════════════════════════════════════════════
## SECTION 6 — COMPLETE BACKEND DATA MODELS
## ═══════════════════════════════════════════════

### New Tables Required (additions to existing schema)

```sql
-- ── SHOP SYSTEM ──────────────────────────────────────────────

CREATE TABLE shops (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_user_id   UUID REFERENCES users(id),
    name            VARCHAR(255) NOT NULL,
    slug            VARCHAR(255) UNIQUE NOT NULL,
    description     TEXT,
    logo_url        VARCHAR(500),
    category        VARCHAR(100),
    commission_rate DECIMAL(5,4) DEFAULT 0.05,
    is_approved     BOOLEAN DEFAULT false,
    approved_by     UUID REFERENCES users(id),
    approved_at     TIMESTAMPTZ,
    wallet_id       UUID REFERENCES wallets(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE products (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id         UUID REFERENCES shops(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    slug            VARCHAR(255) UNIQUE NOT NULL,
    description     TEXT,
    short_desc      VARCHAR(300),
    category        VARCHAR(100),
    price_pkr       DECIMAL(12,2) NOT NULL,
    stock_qty       INTEGER DEFAULT 0,
    images          JSONB DEFAULT '[]',
    avg_rating      DECIMAL(3,2) DEFAULT 0.00,
    review_count    INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT true,
    is_approved     BOOLEAN DEFAULT false,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── CART SYSTEM ─────────────────────────────────────────────

CREATE TABLE carts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id      VARCHAR(255),   -- for anonymous/guest carts
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE cart_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cart_id         UUID REFERENCES carts(id) ON DELETE CASCADE,
    product_id      UUID REFERENCES products(id),
    quantity        INTEGER NOT NULL DEFAULT 1,
    price_at_add    DECIMAL(12,2) NOT NULL,  -- snapshot price when added
    added_at        TIMESTAMPTZ DEFAULT NOW()
);

-- ── ORDER SYSTEM ─────────────────────────────────────────────

CREATE TABLE orders (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number    VARCHAR(30) UNIQUE NOT NULL,  -- ORD-20241215-XXXXX
    customer_id     UUID REFERENCES users(id),
    status          VARCHAR(30) DEFAULT 'pending',
    -- pending/confirmed/processing/shipped/delivered/cancelled/refunded
    subtotal_pkr    DECIMAL(12,2) NOT NULL,
    platform_fee    DECIMAL(12,2) DEFAULT 0.00,
    total_pkr       DECIMAL(12,2) NOT NULL,
    payment_method  VARCHAR(30) DEFAULT 'palm_vein',
    payment_status  VARCHAR(20) DEFAULT 'pending',
    -- pending/paid/failed/refunded
    transaction_id  UUID REFERENCES transactions(id),
    scan_event_id   UUID REFERENCES palm_scan_events(id),
    palm_confidence DECIMAL(5,4),
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE order_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id        UUID REFERENCES orders(id) ON DELETE CASCADE,
    product_id      UUID REFERENCES products(id),
    shop_id         UUID REFERENCES shops(id),
    quantity        INTEGER NOT NULL,
    unit_price      DECIMAL(12,2) NOT NULL,
    line_total      DECIMAL(12,2) NOT NULL,
    shop_earnings   DECIMAL(12,2) NOT NULL,  -- after commission
    platform_take   DECIMAL(12,2) NOT NULL
);

-- ── REVIEWS ──────────────────────────────────────────────────

CREATE TABLE product_reviews (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id      UUID REFERENCES products(id),
    customer_id     UUID REFERENCES users(id),
    order_id        UUID REFERENCES orders(id),
    rating          SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment         TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── PAYOUTS ──────────────────────────────────────────────────

CREATE TABLE payouts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id         UUID REFERENCES shops(id),
    amount_pkr      DECIMAL(12,2) NOT NULL,
    status          VARCHAR(20) DEFAULT 'pending',
    -- pending/processing/completed/failed
    wallet_id       UUID REFERENCES wallets(id),
    transaction_id  UUID REFERENCES transactions(id),
    period_start    DATE,
    period_end      DATE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    settled_at      TIMESTAMPTZ
);
```

---

## ═══════════════════════════════════════════════
## SECTION 7 — API ENDPOINTS (NEW + UPDATED)
## ═══════════════════════════════════════════════

### 7.1 Shop Public Endpoints (No auth required)

```
GET  /shop/products                → List all active approved products
                                     Query: ?category=&search=&sort=&page=&limit=
GET  /shop/products/{slug}         → Product detail page
GET  /shop/categories              → All available categories
GET  /shop/products/{id}/reviews   → Product reviews (paginated)
GET  /shop/shops                   → All approved shops
GET  /shop/shops/{slug}            → Shop profile + their products
```

### 7.2 Cart Endpoints (Guest + Authenticated)

```
POST /cart/merge                   → Merge localStorage cart on login
GET  /cart                         → Get current cart (auth: backend cart,
                                     guest: pass session_id header)
POST /cart/items                   → Add item {product_id, quantity}
PUT  /cart/items/{id}              → Update quantity
DELETE /cart/items/{id}            → Remove item
DELETE /cart                       → Clear entire cart
GET  /cart/summary                 → Totals, item count, any warnings
```

### 7.3 Checkout & Payment Endpoints

```
POST /checkout/validate            → Pre-checkout validation:
                                     - Is user logged in?
                                     - Is palm enrolled?
                                     - Is wallet balance sufficient?
                                     Returns: {
                                       logged_in: bool,
                                       palm_enrolled: bool,
                                       balance_sufficient: bool,
                                       wallet_balance: decimal,
                                       cart_total: decimal,
                                       shortfall: decimal | null,
                                       action_required: string
                                       (one of: login / enroll_palm /
                                        topup_wallet / proceed_to_scan)
                                     }

POST /checkout/initiate            → Creates pending order record,
                                     locks stock quantity,
                                     returns {order_id, amount, items_summary}

POST /checkout/palm-pay            → Called after successful palm scan:
                                     {order_id, scan_event_id, confidence}
                                     Orchestrates:
                                     1. Verify palm match (confidence ≥ 0.97)
                                     2. Re-verify balance (race condition guard)
                                     3. Atomic wallet debit (customer)
                                     4. Credit shop wallets (per item, after commission)
                                     5. Credit platform fee wallet
                                     6. Update order status → confirmed
                                     7. Reduce stock quantities
                                     8. Send FCM push to customer VeinPay app
                                     9. Return success + order confirmation

POST /checkout/cancel/{order_id}   → Release locked stock, cancel pending order
```

### 7.4 Order Endpoints (Customer)

```
GET  /orders                       → Customer's order history
GET  /orders/{id}                  → Order detail + status
POST /orders/{id}/review           → Submit review for a delivered order
```

### 7.5 Shop Owner Endpoints (Authenticated, role: shop_owner)

```
GET  /owner/dashboard              → Stats (sales, orders, products, revenue)
GET  /owner/products               → Own products list
POST /owner/products               → Create new product
PUT  /owner/products/{id}          → Update product
DELETE /owner/products/{id}        → Delete product
POST /owner/products/{id}/images   → Upload product images
GET  /owner/orders                 → Orders for this shop
PUT  /owner/orders/{id}/status     → Update order status
GET  /owner/inventory              → Low stock alerts + adjustment
PUT  /owner/inventory/{product_id} → Quick stock adjustment
GET  /owner/earnings               → Earnings summary + history
GET  /owner/payouts                → Payout history
GET  /owner/shop                   → Own shop profile
PUT  /owner/shop                   → Update shop profile
```

### 7.6 Admin Endpoints (Authenticated, role: admin)

```
GET  /admin/shops/pending          → Shops awaiting approval
POST /admin/shops/{id}/approve     → Approve shop
POST /admin/shops/{id}/reject      → Reject shop with reason
GET  /admin/products/pending       → Products awaiting review
POST /admin/products/{id}/approve  → Approve product listing
POST /admin/products/{id}/reject   → Reject product listing
GET  /admin/orders                 → All platform orders
GET  /admin/transactions           → All financial transactions
GET  /admin/analytics              → Platform-wide stats
GET  /admin/payouts/pending        → Pending shop payouts
POST /admin/payouts/settle         → Trigger payout settlement batch
```

---

## ═══════════════════════════════════════════════
## SECTION 8 — PAYMENT FLOW TECHNICAL DEEP DIVE
## ═══════════════════════════════════════════════

### 8.1 The Core Money Flow

When a customer pays PKR 3,600 for an order containing items from one shop:

```
Customer Wallet (VeinPay)
    Balance: PKR 12,500
         │
         │ DEBIT PKR 3,600
         ▼
    Balance: PKR 8,900
         │
         │ Split:
         │
         ├── PKR 3,420 (95%) → Shop Owner's Wallet
         │                     (Platform takes 5% commission)
         │
         └── PKR 180   (5%)  → Platform Wallet
                               (Admin-controlled)
```

Multi-shop order (items from 2 different shops):
- Each shop's items are calculated independently
- Each shop receives their portion minus commission
- Platform receives commission from each shop
- Customer is debited the full total in ONE atomic transaction

### 8.2 Atomicity Guarantee

The entire payment (debit customer + credit all shops + credit platform) happens
in a SINGLE PostgreSQL transaction with SELECT FOR UPDATE locks:

```sql
BEGIN;
  -- Lock customer wallet
  SELECT balance FROM wallets WHERE id = $customer_wallet FOR UPDATE;

  -- Lock all shop wallets involved
  SELECT balance FROM wallets WHERE id = ANY($shop_wallet_ids) FOR UPDATE;

  -- Verify customer balance still sufficient (race condition guard)
  -- Debit customer
  -- Credit each shop (after commission)
  -- Credit platform
  -- Record all ledger entries
  -- Update order status
  -- Update stock quantities (also locked)
COMMIT;
```

If ANY step fails → entire transaction rolls back → customer not charged →
stock not reduced → order stays in "pending" → user sees error message.

### 8.3 Push Notification to VeinPay Mobile

After successful payment, backend sends FCM push notification:

```json
{
  "title": "Payment Successful",
  "body": "PKR 3,600 paid to PalmPay Shop. Order #ORD-2024-00123",
  "data": {
    "type": "shop_purchase",
    "order_id": "uuid",
    "amount": "3600.00",
    "shop_name": "Tech Store",
    "new_balance": "8900.00",
    "transaction_id": "uuid"
  }
}
```

VeinPay mobile app, upon receiving this notification:
- Shows banner notification
- On tap: opens Transaction Detail screen showing the purchase
- Transaction appears in history as:
  Type: "Shop Purchase · [Shop Name]"
  Amount: -PKR 3,600
  Date: [timestamp]
  Reference: ORD-2024-00123

### 8.4 Insufficient Balance Dialog

If /checkout/validate returns balance_insufficient = true:

Web app shows dialog:
```
┌────────────────────────────────────────────────┐
│  ⚠  Insufficient Balance                        │
│                                                  │
│  Your VeinPay Wallet: PKR 2,100                 │
│  Order Total:         PKR 3,600                 │
│  Shortfall:           PKR 1,500                 │
│                                                  │
│  Please top up your VeinPay wallet app          │
│  on your mobile phone by at least PKR 1,500     │
│  and then return to complete your purchase.     │
│                                                  │
│  [Open VeinPay App]    [Cancel]                 │
└────────────────────────────────────────────────┘
```

"Open VeinPay App" button: deep link to VeinPay app
(palmpay://topup or opens Play Store if not installed)

After user tops up on mobile and returns to browser:
- Cart is preserved (backend cart, persisted)
- User clicks "Try Again" → /checkout/validate called again
- If now sufficient → proceed to scan

---

## ═══════════════════════════════════════════════
## SECTION 9 — CROSS-PLATFORM COMMUNICATION MAP
## ═══════════════════════════════════════════════

```
┌────────────────────────────────────────────────────────────────────┐
│                      SHARED FASTAPI BACKEND                         │
│                                                                      │
│  Auth Service · Wallet Service · Palm Service · Shop Service         │
│  PostgreSQL · Redis · S3 · Firebase Admin SDK                        │
└───────┬───────────────────────────────────────────┬────────────────┘
        │ REST API (HTTPS)                           │ REST API (HTTPS)
        │ JWT Auth                                   │ JWT Auth
        │                                            │
┌───────▼───────────────────────┐    ┌──────────────▼──────────────┐
│       WEB APPLICATION          │    │   VEINPAY MOBILE APP         │
│                                │    │   (Flutter Android)          │
│  Customer Panel:               │    │                              │
│  · Browse shop                 │    │  · Wallet balance            │
│  · Add to cart                 │    │  · Top-up                    │
│  · Palm enroll (NIR cam)       │◄───┤  · P2P transfer              │
│  · Palm scan → pay             │ FC │  · Transaction history       │
│  · Order history               │ M  │    (includes shop purchases) │
│                                │    │  · Profile                   │
│  Shop Owner Panel:             │    │                              │
│  · Add/edit products           │    │                              │
│  · Manage orders               │    │                              │
│  · View earnings               │    │                              │
│                                │    │                              │
│  Admin Panel:                  │    │                              │
│  · Approve shops               │    │                              │
│  · Approve products            │    │                              │
│  · View all transactions       │    │                              │
│  · Manage users                │    │                              │
└───────────────────────────────┘    └──────────────────────────────┘

KEY SHARED RESOURCES (same DB, same record):
  users table         → same user, same ID, same credentials
  wallets table       → same balance, one source of truth
  transactions table  → both apps read/write to same table
  palm_templates      → enrolled on web, used for payment on web
  notifications       → sent server→mobile after web events
```

### 9.1 What Each Platform OWNS vs SHARES

| Data / Feature | Web App | Mobile App | Shared (DB) |
|---|---|---|---|
| User account | Reads + writes | Reads + writes | ✅ users table |
| Wallet balance | Reads (checkout) | Reads + writes | ✅ wallets table |
| Top-up | ❌ | ✅ | ✅ transactions |
| P2P transfer | ❌ | ✅ | ✅ transactions |
| Shop purchase | ✅ (initiates) | ❌ (receives notif) | ✅ orders + transactions |
| Palm enrollment | ✅ (NIR cam) | ❌ | ✅ palm_templates |
| Palm scan/auth | ✅ (NIR cam) | ❌ | ✅ palm_scan_events |
| Transaction history | Reads (order history) | Reads (full history) | ✅ transactions |
| Push notifications | Sends (via FCM Admin) | Receives | — |
| Product browsing | ✅ | ❌ (V1) | ✅ products table |
| Cart management | ✅ | ❌ | ✅ carts table |

---

## ═══════════════════════════════════════════════
## SECTION 10 — EDGE CASES & BUSINESS RULES
## ═══════════════════════════════════════════════

### 10.1 Stock Management Rules
- Stock is "soft locked" when order is initiated (prevent overselling)
- Lock released if: payment fails / order cancelled / 15-min timeout
- Stock permanently reduced only on confirmed payment
- If product goes out of stock between cart-add and checkout:
  → Show warning: "Item [X] is now out of stock. Remove to continue."

### 10.2 Price Change Between Cart-Add and Checkout
- Price snapshot taken at time of "Add to Cart" (stored in cart_items.price_at_add)
- If shop owner changes price AFTER customer added to cart:
  → Show warning: "Price of [X] changed from PKR [old] to PKR [new]"
  → Customer must re-confirm before proceeding
- Always charge the CURRENT price, not the cart-add price
  (cart_at_add is for display/warning only — current product price is charged)

### 10.3 Multi-Shop Orders
- Customer can add items from multiple shops to one cart
- Single palm scan pays for ALL items across ALL shops
- Each shop receives their portion independently
- One order record → multiple order_items → multiple shop earnings

### 10.4 Palm Scan Failure at Payment
- Up to 3 scan attempts before order is cancelled
- Each failed attempt is logged in palm_scan_events
- After 3 failures: order cancelled, stock locks released, no charge
- User sees: "Payment failed after 3 attempts. Your cart is saved."
- Cart remains intact for retry

### 10.5 Session Persistence for Guests
- Guest adds 5 items to cart (stored in localStorage with session_id)
- Guest registers / logs in
- POST /cart/merge called automatically with {session_id, user_id}
- Backend merges: adds guest items to user's backend cart
- localStorage cart cleared
- User continues from where they left off

### 10.6 Refund Logic
- If order cancelled after payment: full refund to customer wallet
- If partial cancellation (some items): partial refund
- Refund deducts from shop wallet (shop bears the cost)
- Refund credited to customer wallet instantly
- Platform fee also refunded on full cancellation

### 10.7 Shop Owner Wallet = VeinPay Wallet
- Shop owner's earnings go to their VeinPay wallet
- They see earnings in both:
  - Shop Owner Panel (Earnings tab)
  - VeinPay mobile app (transaction history, labeled "Shop Earnings")
- No separate payout system needed — it's the same wallet

---

## ═══════════════════════════════════════════════
## SECTION 11 — DUMMY PRODUCT DATA (FOR DEVELOPMENT)
## ═══════════════════════════════════════════════

Seed these categories and products for development/demo:

### Categories
Electronics · Clothing · Food & Groceries · Books · Home & Living ·
Beauty & Personal Care · Sports & Fitness · Accessories · Stationery ·
Mobile & Gadgets

### Sample Products (with PKR pricing for Pakistan market)

```
ELECTRONICS:
1. USB-C Charging Cable (2m)       — PKR 450    — stock: 100
2. Wireless Earbuds (Basic)        — PKR 2,800  — stock: 30
3. Phone Screen Protector          — PKR 350    — stock: 200
4. Power Bank 10,000mAh            — PKR 3,200  — stock: 25
5. LED Desk Lamp                   — PKR 1,200  — stock: 40

CLOTHING:
6. Men's Cotton T-Shirt            — PKR 890    — stock: 80
7. Women's Lawn Dupatta            — PKR 1,500  — stock: 50
8. Sports Shorts                   — PKR 1,100  — stock: 60
9. Winter Socks (Pack of 3)        — PKR 550    — stock: 150
10. Casual Sneakers (Size 40-45)   — PKR 4,500  — stock: 20

FOOD & GROCERIES:
11. Himalayan Pink Salt 1kg        — PKR 280    — stock: 500
12. Green Tea (50 bags)            — PKR 420    — stock: 200
13. Mixed Dry Fruits 500g          — PKR 1,800  — stock: 75
14. Organic Honey 500ml            — PKR 950    — stock: 100
15. Basmati Rice 5kg               — PKR 1,650  — stock: 300

BOOKS:
16. Atomic Habits (Urdu Edition)   — PKR 750    — stock: 40
17. The Alchemist (English)        — PKR 650    — stock: 35
18. CSS/PMS Guide 2024             — PKR 1,200  — stock: 60
19. Learn Python in 30 Days        — PKR 850    — stock: 45
20. Islamic Calligraphy Workbook   — PKR 480    — stock: 80

HOME & LIVING:
21. Ceramic Coffee Mug             — PKR 380    — stock: 120
22. Bamboo Cutting Board           — PKR 650    — stock: 90
23. Scented Candle Set (3pc)       — PKR 1,100  — stock: 60
24. Storage Basket (Large)         — PKR 780    — stock: 70
25. Digital Kitchen Scale          — PKR 1,400  — stock: 45
```

---

## ═══════════════════════════════════════════════
## SECTION 12 — WHAT YOU (THE AI) MUST NOW PRODUCE
## ═══════════════════════════════════════════════

After reading all of the above, your task is to:

### OUTPUT TASK A — Architecture Validation
Confirm your understanding of the cross-platform architecture.
Identify any logical gaps, conflicts, or missing pieces in the system as described.
Suggest corrections or additions.

### OUTPUT TASK B — Implementation Sequence
Provide a step-by-step implementation plan in the correct order:
1. Which backend changes must happen first
2. Which web app changes depend on which backend endpoints
3. Which mobile app changes depend on which backend events

### OUTPUT TASK C — API Contract
For each new endpoint described in Section 7, write the complete:
- Request schema (headers, body, query params)
- Success response schema (with example values)
- Error responses (all possible error codes and messages)

### OUTPUT TASK D — Database Migration Plan
Write the SQL migrations in the correct order (respecting foreign key dependencies).
Identify which existing tables need new columns.

### OUTPUT TASK E — Frontend Component List
For the new Shop tab in the web Customer Panel, list every React component needed:
- Component name
- Props
- State
- Which API endpoint it calls
- Child components

### OUTPUT TASK F — Security Audit
For the new shop purchase flow, identify every security vulnerability
that must be addressed:
- Race conditions
- Price manipulation
- Stock manipulation
- Palm scan replay attacks
- JWT token reuse across sessions
- Cart injection
- Commission bypass attempts

### OUTPUT TASK G — Test Cases
Write test cases for the complete checkout flow covering:
- Happy path (logged in, enrolled, sufficient balance)
- Each failure state (not logged in / not enrolled / insufficient balance)
- Edge cases from Section 10
- Concurrent payment scenarios

---

## ═══════════════════════════════════════════════
## SECTION 13 — CONSTRAINTS & NON-NEGOTIABLES
## ═══════════════════════════════════════════════

These rules must never be violated in any output:

1. Palm enrollment ONLY happens on web app (NIR camera required)
2. Palm recognition ONLY happens on web app at checkout
3. Mobile app (VeinPay) is the wallet — it ONLY holds/manages money
4. The mobile app is NEVER actively involved in payment — it is
   notified passively via FCM after the web app triggers the payment
5. One user account = one wallet = one palm template set
6. All financial operations must be ACID-compliant (PostgreSQL transactions)
7. Confidence threshold for payment = minimum 97% — hardcoded on backend,
   not configurable by shop owner or user
8. Cart must survive across sessions for logged-in users (backend cart)
9. Stock must never go negative (enforced at DB level: CHECK stock_qty >= 0)
10. Shop owner cannot approve their own products (admin-only approval)
11. Platform commission is deducted BEFORE shop owner receives earnings
12. Refunds must always be processed — no "no refund" shop policy overrides
    (platform-level guarantee)

---

## END OF PROMPT
## ════════════════════════════════════════════════════════════════
## You now have complete context. Proceed with the requested output.
## ════════════════════════════════════════════════════════════════
