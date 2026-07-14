# PalmPay — Complete Mobile App Project Plan
### From Zero to Play Store · Android · Palm Vein Biometric Wallet
**Version 1.0 · Authored for Production**

---

> **Reference architecture:** WeChat Pay (China) · Easypaisa (Pakistan) · Alipay Palm Pay (Alibaba)
> **Core differentiator:** Palm vein biometric replaces every PIN, OTP, and card swipe at point of sale
> **Target market:** Pakistan (Phase 1) · Expandable to any market with NIR kiosk infrastructure

---

## TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Product Vision & Scope](#2-product-vision--scope)
3. [User Personas](#3-user-personas)
4. [Feature Specification — Complete](#4-feature-specification--complete)
5. [System Architecture](#5-system-architecture)
6. [Database Design](#6-database-design)
7. [API Specification](#7-api-specification)
8. [Flutter App Structure](#8-flutter-app-structure)
9. [Security Architecture](#9-security-architecture)
10. [Palm Vein Pipeline Integration](#10-palm-vein-pipeline-integration)
11. [Payment Flow — Technical Deep Dive](#11-payment-flow--technical-deep-dive)
12. [UI/UX Design System](#12-uiux-design-system)
13. [Screen Inventory — All 28 Screens](#13-screen-inventory--all-28-screens)
14. [Third-Party Integrations](#14-third-party-integrations)
15. [Testing Strategy](#15-testing-strategy)
16. [Play Store Submission Checklist](#16-play-store-submission-checklist)
17. [10-Day Sprint Plan](#17-10-day-sprint-plan)
18. [Risk Register](#18-risk-register)
19. [Post-Launch Roadmap](#19-post-launch-roadmap)

---

## 1. EXECUTIVE SUMMARY

PalmPay is a biometric digital wallet for Android where a user's palm vein pattern is the sole authentication credential for every financial transaction. It eliminates the need for physical cards, PINs, OTPs, and passwords at point of sale.

The product mirrors the WeChat Pay experience — a clean, trusted, always-accessible wallet — but replaces the QR code payment mechanism with palm vein biometric identification. Like Alibaba's Dragonfly Palm Pay system deployed across 3,000+ stores in China, PalmPay binds a person's vascular identity to their wallet permanently.

**Version 1.0 scope is intentionally narrow and deep:**
- Personal palm vein wallet (load, hold, send money)
- Palm Pay at merchant terminals (NIR kiosk payment)
- Nothing else — no metro, no attendance, no access control

**Why narrow is right for V1:**
Building payments correctly is the hardest problem in fintech. Get this right with zero compromise and every other service becomes a simple module added on top of a trusted, battle-tested foundation.

---

## 2. PRODUCT VISION & SCOPE

### Vision Statement
> "Your hand is your bank account."

### The WeChat Pay Parallel

WeChat Pay succeeded because it did one thing perfectly — made paying so frictionless that users never thought about it. PalmPay follows the same principle but goes one step further: WeChat Pay still requires you to take out your phone. PalmPay requires nothing except your hand.

| Feature | WeChat Pay | Easypaisa | PalmPay V1 |
|---|---|---|---|
| Auth method | PIN / Face ID | PIN / OTP | Palm vein scan |
| At terminal | QR code scan | QR code scan | Palm on NIR scanner |
| Needs phone at terminal | Yes | Yes | **No** |
| Spoofable | Yes (QR screenshot) | Yes | **No (living tissue only)** |
| Wallet | Yes | Yes | Yes |
| P2P transfer | Yes | Yes | Yes |
| Merchant payments | Yes | Yes | Yes |

### V1 In Scope

- User registration (phone + CNIC + palm enrollment)
- Digital wallet (PKR balance, top-up, transfer)
- Palm Pay at merchant kiosk (real-time biometric payment)
- Transaction history and receipts
- Wallet security controls
- Push notification receipts
- Basic merchant portal (web, not in-app)

### V1 Out of Scope (future versions)

- Metro ticketing
- Attendance systems
- International transfers
- Crypto wallet
- Bill payments (utilities, telecom)
- Loan / BNPL products
- Merchant app (V2)
- iOS app (V2)

---

## 3. USER PERSONAS

### Persona 1 — Ahmed, 28, Daily Commuter / Salaried Employee
- Shops at the same 3–4 stores every week
- Uses Easypaisa already but hates entering PIN in crowded shops
- Owns a mid-range Android (Samsung A-series)
- Primary pain: fumbling for phone, entering PIN, network delays at checkout
- Goal: Pay instantly, hands-free, feel secure

### Persona 2 — Fatima, 35, Small Business Owner
- Runs a bakery in Lahore
- Wants to accept digital payments without expensive POS machines
- Tired of cash handling and reconciliation
- Goal: Accept palm payments from customers, see daily sales summary

### Persona 3 — Tariq, 52, Low-tech User
- First smartphone user, recently banked
- Afraid of entering wrong PIN in public
- Trusts biometrics because "the phone knows my face"
- Goal: Pay without remembering anything — just use his hand

### Persona 4 — Zara, 22, University Student / Power User
- Pays for food, rides, shopping digitally
- Wants to split payments, track spending
- Comfortable with apps, expects smooth UX
- Goal: Replace her entire wallet with her phone + palm

---

## 4. FEATURE SPECIFICATION — COMPLETE

### 4.1 Onboarding & Registration

**Step 1 — Phone Verification**
- User enters Pakistani mobile number (+92 format)
- 6-digit OTP sent via SMS (Twilio or Telenor Messaging API)
- OTP expires in 120 seconds, max 3 resend attempts per session
- On success: session token issued, registration flow continues

**Step 2 — Identity Verification (KYC)**
- User enters full name (as on CNIC)
- User enters 13-digit CNIC number
- User takes photo of front + back of CNIC (in-app camera)
- CNIC photo sent to NADRA VERISYS API for verification
- Fallback for V1: manual review queue if VERISYS unavailable
- Result: KYC pending / approved / rejected (async, push notification)
- User can use app with PKR 10,000 monthly limit until KYC approved
- Full limit unlocked post-KYC

**Step 3 — Palm Enrollment**
- Full-screen instruction screen (animated palm diagram)
- User shown how to hold hand (10–15 cm from camera, palm facing down)
- Note: V1 enrollment happens at registered kiosk, not phone camera
  - User visits nearest enrolled merchant / enrollment kiosk
  - Staff initiates enrollment session on kiosk, linked to user's account via QR code shown in app
  - 3 scans captured (slight position variation each time)
  - Model generates encrypted feature template
  - Template stored server-side (never on device)
  - Both left and right hand optional (recommended: enroll both)
- App shows enrollment status: pending / enrolled / failed
- Re-enrollment available anytime from security settings

**Step 4 — Wallet Setup**
- User sets display name / username (unique, used for P2P sends)
- User sets spending PIN (4-digit, used as fallback only — not for palm pay)
- User sets transaction limit preferences
- Wallet created with PKR 0 balance, account number issued
- Onboarding complete — main app unlocked

---

### 4.2 Home / Wallet Dashboard

**Balance display**
- Large, centered current balance (PKR format with paisas)
- Hide / show balance toggle (eye icon) — privacy in public
- Last updated timestamp (real-time via WebSocket subscription)

**Quick action bar (4 icons)**
- Add Money
- Send Money
- Request Money
- Scan (palm pay — opens scan tab)

**Recent transactions (last 5)**
- Each row: merchant name / person name · amount · time
- Color coded: green (money in) · red (money out)
- "See all" → full transaction history screen

**Promotional banner (V1 placeholder)**
- Static banner: "Enroll at nearest kiosk →"
- Later: cashback offers, partner merchant deals

**Bottom navigation (4 tabs)**
- Home (wallet) · Scan (palm) · History · Profile

---

### 4.3 Add Money (Top-Up)

**Methods available in V1:**
- JazzCash wallet → PalmPay (instant)
- Bank transfer (1Link IBFT) — 1–2 hours
- Debit card (via JazzCash payment gateway)

**Flow:**
- User selects method
- Enters amount (minimum PKR 100, maximum PKR 50,000 per transaction)
- Confirms with spending PIN (not palm — palm is for paying out only)
- JazzCash deeplink opens (or in-app browser for card)
- On success: webhook from JazzCash → server → wallet credited → push notification
- Instant reflection in balance

---

### 4.4 Send Money (P2P Transfer)

**Send to:**
- PalmPay username (search by username)
- Mobile number (if registered on PalmPay)
- CNIC number

**Flow:**
- Recipient lookup → preview recipient name + avatar
- Enter amount + optional note
- Review screen: sender, recipient, amount, fee (PKR 0 for V1 — free P2P)
- Confirm with spending PIN
- Transfer instant (internal ledger debit/credit)
- Both users get push notification
- Transaction in both histories

**Request money:**
- User enters amount + note
- Generates a request link / in-app notification to recipient
- Recipient sees pending request, pays with one tap + PIN

---

### 4.5 Palm Pay (At Merchant Terminal)

This is the flagship feature and must work flawlessly.

**Customer flow:**
1. Customer stands at merchant counter
2. Merchant enters amount on kiosk touchscreen
3. Kiosk screen prompts customer: "Place your palm"
4. Customer places palm on NIR scanner (same hardware as enrollment)
5. Camera captures NIR image → sends to PalmPay backend
6. Backend:
   a. Runs palm vein model inference
   b. Returns top match (user_id + confidence score)
   c. Checks: confidence ≥ 97% threshold?
   d. Checks: active wallet? Sufficient balance? Account not frozen? Daily limit not hit?
   e. If all pass: debit wallet, credit merchant, generate transaction record
7. Kiosk screen: shows "Payment Successful · PKR [amount] · [Customer name]"
8. Customer phone: push notification receipt
9. Merchant kiosk: prints / shows digital receipt

**Failure states (handled gracefully):**
- Confidence < 97%: "Scan unclear — please try again" (up to 3 attempts)
- 3 failed attempts: "Payment failed — please use alternate method" (QR fallback shown)
- Insufficient balance: "Insufficient balance — please top up" (QR for top-up shown)
- Account frozen: "Account restricted — please contact support"
- Network timeout: kiosk shows error, no debit occurs (idempotency key prevents double-charge)
- Liveness check failed: "Please use a real hand" (anti-spoof)

**Speed target:** End-to-end (palm placed → screen confirms) < 1.5 seconds

---

### 4.6 Transaction History

**Full list view:**
- Paginated (20 per page, infinite scroll)
- Filter by: date range · type (in/out/palm pay/transfer) · amount range
- Search by merchant name / person name
- Each row: icon (merchant / person / bank) · name · date · amount (colored)

**Transaction detail view:**
- Transaction ID (reference number)
- Date and time (exact, with timezone)
- Type (Palm Pay / Transfer / Top-up / Refund)
- Amount
- Fee (if any)
- Merchant name + location (if palm pay)
- Confidence score (for palm pay transactions — shown as "Biometric verified")
- Status (completed / pending / failed / refunded)
- Share receipt button (PDF or image)
- Report issue button

---

### 4.7 Spending Analytics

- Weekly / monthly spend graph (bar chart)
- Category breakdown (auto-categorized by merchant type)
- Top merchants this month
- Comparison vs last month
- Average daily spend

---

### 4.8 Wallet Security Controls

**Transaction limits (user-configurable):**
- Per-transaction maximum (default PKR 25,000, max PKR 50,000)
- Daily limit (default PKR 50,000, max PKR 100,000)
- Monthly limit (default PKR 500,000)

**Account controls:**
- Freeze wallet instantly (one-tap emergency lock)
- Unfreeze via OTP to registered number
- Block specific merchants
- Enable / disable palm pay (toggle)

**Palm template controls:**
- View enrolled hands (left / right)
- Re-enroll (triggers enrollment flow)
- Revoke specific hand template
- View last 10 scan events (date, location, result)

**Device management:**
- See all logged-in devices
- Remote logout specific device
- Require PIN on app open (toggle)
- Biometric app lock (phone fingerprint to open app — separate from palm pay)

---

### 4.9 Profile & Identity

- Display name and username
- Profile photo
- CNIC number (masked: ####-#######-#)
- KYC status with badge
- Registered phone number (change via OTP)
- Email (optional)
- Account number (for receiving bank transfers)
- Digital ID card (downloadable PDF — name, account number, QR for verification)

---

### 4.10 Notifications

**Transaction notifications (always on):**
- Palm Pay success: "Paid PKR 450 to [Merchant] via palm"
- Palm Pay failure: "Payment of PKR 450 failed at [Merchant] — 3 scan attempts"
- Money received: "[Name] sent you PKR 1,000"
- Top-up success: "PKR 5,000 added to your wallet"
- Low balance alert (user-set threshold)

**Security notifications (always on):**
- New device login
- Palm template changed
- Wallet frozen
- Failed scan attempts (3+ in 10 minutes)
- Large transaction (above user-set threshold)

**Promotional (opt-in):**
- New merchant partners
- Cashback offers
- App updates

---

## 5. SYSTEM ARCHITECTURE

```
┌──────────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                                  │
│                                                                    │
│   ┌─────────────────────┐      ┌──────────────────────────────┐  │
│   │  Flutter Android App │      │  Merchant Kiosk (Python)     │  │
│   │  (User Wallet)       │      │  NIR Camera + Touchscreen    │  │
│   └──────────┬──────────┘      └──────────────┬───────────────┘  │
└──────────────┼──────────────────────────────────┼─────────────────┘
               │ HTTPS + JWT                       │ WSS + Device Token
               ▼                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                    API GATEWAY (Nginx)                             │
│            Rate limiting · SSL termination · Routing               │
└──────────────────────────────┬───────────────────────────────────┘
                                │
               ┌────────────────┼────────────────┐
               ▼                ▼                ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Auth Service    │  │  Wallet Service  │  │  Palm Service    │
│  FastAPI         │  │  FastAPI         │  │  FastAPI         │
│  · Register      │  │  · Balance       │  │  · Enroll        │
│  · OTP           │  │  · Top-up        │  │  · Match         │
│  · JWT           │  │  · Transfer      │  │  · Authorize     │
│  · KYC           │  │  · Palm Pay      │  │  · Audit         │
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
         │                     │                      │
         └─────────────────────┼──────────────────────┘
                               │
               ┌───────────────┼───────────────┐
               ▼               ▼               ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   PostgreSQL      │  │     Redis        │  │   ML Model       │
│   Primary DB      │  │   Cache+Queue    │  │   FastAPI        │
│   · Users         │  │   · Sessions     │  │   (Your existing │
│   · Wallets       │  │   · Rate limits  │  │    pipeline)     │
│   · Transactions  │  │   · Pay requests │  │   Returns:       │
│   · Palm events   │  │   · OTP store    │  │   user_id +      │
│   · Audit log     │  │   · WS state     │  │   confidence     │
└──────────────────┘  └──────────────────┘  └──────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│              EXTERNAL SERVICES                                     │
│  JazzCash API · NADRA VERISYS · Firebase FCM · Twilio SMS         │
│  AWS S3 (palm templates) · Sentry (errors) · Grafana (metrics)    │
└──────────────────────────────────────────────────────────────────┘
```

### Architecture Decisions & Rationale

**Why microservices (3 services)?**
Auth, Wallet, and Palm are independently scalable. Palm inference is CPU/GPU heavy — isolating it means you can scale the ML service independently without scaling the entire backend. Wallet service can be PCI-DSS scoped separately.

**Why FastAPI?**
Your ML model is Python. FastAPI is Python. Zero language switching. Async-native, handles WebSocket natively, auto-generates OpenAPI docs. 60,000+ requests/second on basic hardware.

**Why PostgreSQL?**
Financial data needs ACID transactions. When debiting a wallet and crediting a merchant, both must succeed or both must fail — atomically. PostgreSQL's row-level locking and transaction isolation handles this correctly. No NoSQL database provides this guarantee.

**Why Redis?**
Payment requests live for 60 seconds then expire. Redis TTL is perfect. WebSocket connection state, rate limiting counters, and OTP storage all benefit from Redis's speed (sub-millisecond reads).

**Why WebSocket for payments?**
The merchant kiosk needs real-time feedback when a customer's palm is scanned. HTTP polling introduces 500ms–2s latency. WebSocket pushes the result the moment inference completes — essential for < 1.5s end-to-end target.

---

## 6. DATABASE DESIGN

### Complete Schema

```sql
-- ============================================
-- USERS & IDENTITY
-- ============================================

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone           VARCHAR(13) UNIQUE NOT NULL,       -- +923001234567
    full_name       VARCHAR(255) NOT NULL,
    username        VARCHAR(50) UNIQUE,
    cnic            VARCHAR(15) UNIQUE,                -- 42101-1234567-1
    email           VARCHAR(255),
    profile_photo   VARCHAR(500),                      -- S3 URL
    kyc_status      VARCHAR(20) DEFAULT 'pending',     -- pending/approved/rejected
    kyc_reviewed_at TIMESTAMPTZ,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE user_devices (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    device_id       VARCHAR(255) UNIQUE NOT NULL,      -- Android device ID
    device_name     VARCHAR(255),                      -- "Samsung Galaxy A54"
    fcm_token       VARCHAR(500),                      -- Firebase push token
    last_seen       TIMESTAMPTZ DEFAULT NOW(),
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- PALM BIOMETRICS
-- ============================================

CREATE TABLE palm_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    hand            VARCHAR(5) NOT NULL,               -- left/right
    template_ref    VARCHAR(500) NOT NULL,             -- S3 key (encrypted blob)
    enrolled_at     TIMESTAMPTZ DEFAULT NOW(),
    enrolled_by     UUID,                              -- kiosk device_id
    is_active       BOOLEAN DEFAULT true,
    revoked_at      TIMESTAMPTZ,
    revoked_reason  VARCHAR(255)
);

CREATE TABLE palm_scan_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),         -- NULL if no match
    device_id       UUID REFERENCES kiosk_devices(id),
    confidence      DECIMAL(5,4),                      -- 0.0000–1.0000
    result          VARCHAR(20) NOT NULL,              -- matched/no_match/liveness_fail
    hand_detected   VARCHAR(5),                        -- left/right
    scan_duration   INTEGER,                           -- ms
    triggered_by    VARCHAR(50),                       -- payment/enrollment
    transaction_id  UUID,                              -- linked if payment
    ip_address      INET,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- WALLETS & FINANCIAL
-- ============================================

CREATE TABLE wallets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    account_number  VARCHAR(20) UNIQUE NOT NULL,       -- PLP-2024-000001
    balance         DECIMAL(15,2) DEFAULT 0.00,        -- PKR, never negative
    currency        VARCHAR(3) DEFAULT 'PKR',
    is_frozen       BOOLEAN DEFAULT false,
    frozen_at       TIMESTAMPTZ,
    frozen_reason   VARCHAR(255),
    daily_limit     DECIMAL(15,2) DEFAULT 50000.00,
    per_txn_limit   DECIMAL(15,2) DEFAULT 25000.00,
    monthly_limit   DECIMAL(15,2) DEFAULT 500000.00,
    palm_pay_enabled BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Double-entry ledger — every PKR movement recorded as two entries
CREATE TABLE ledger_entries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id  UUID NOT NULL,                     -- groups debit+credit pair
    wallet_id       UUID REFERENCES wallets(id),
    entry_type      VARCHAR(10) NOT NULL,              -- debit/credit
    amount          DECIMAL(15,2) NOT NULL,            -- always positive
    balance_after   DECIMAL(15,2) NOT NULL,            -- snapshot
    description     VARCHAR(500),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE transactions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_no    VARCHAR(30) UNIQUE NOT NULL,       -- TXN-20241215-XXXXX
    type            VARCHAR(30) NOT NULL,              -- palm_pay/transfer/topup/refund
    status          VARCHAR(20) DEFAULT 'pending',     -- pending/completed/failed/refunded
    sender_id       UUID REFERENCES users(id),
    receiver_id     UUID REFERENCES users(id),         -- merchant or person
    amount          DECIMAL(15,2) NOT NULL,
    fee             DECIMAL(15,2) DEFAULT 0.00,
    note            VARCHAR(500),
    -- Palm Pay specific
    merchant_id     UUID REFERENCES merchants(id),
    kiosk_id        UUID REFERENCES kiosk_devices(id),
    scan_event_id   UUID REFERENCES palm_scan_events(id),
    confidence      DECIMAL(5,4),
    -- Top-up specific
    topup_method    VARCHAR(50),                       -- jazzcash/bank/card
    topup_ref       VARCHAR(255),                      -- external reference
    -- Meta
    idempotency_key VARCHAR(255) UNIQUE,               -- prevents double-charge
    initiated_at    TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    failed_at       TIMESTAMPTZ,
    failure_reason  VARCHAR(500)
);

-- ============================================
-- MERCHANTS & KIOSKS
-- ============================================

CREATE TABLE merchants (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_name   VARCHAR(255) NOT NULL,
    owner_user_id   UUID REFERENCES users(id),
    merchant_code   VARCHAR(20) UNIQUE NOT NULL,
    category        VARCHAR(100),                      -- restaurant/grocery/retail
    address         VARCHAR(500),
    city            VARCHAR(100),
    wallet_id       UUID REFERENCES wallets(id),
    is_active       BOOLEAN DEFAULT true,
    approved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE kiosk_devices (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id     UUID REFERENCES merchants(id),
    device_code     VARCHAR(50) UNIQUE NOT NULL,
    device_token    VARCHAR(500) NOT NULL,             -- hashed auth token
    nickname        VARCHAR(100),                      -- "Counter 1"
    location_lat    DECIMAL(10,8),
    location_lng    DECIMAL(11,8),
    last_ping       TIMESTAMPTZ,
    firmware_version VARCHAR(20),
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- PAYMENT REQUESTS (Redis-first, backed to DB)
-- ============================================

CREATE TABLE payment_requests (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_code    VARCHAR(20) UNIQUE NOT NULL,       -- shown on kiosk
    kiosk_id        UUID REFERENCES kiosk_devices(id),
    merchant_id     UUID REFERENCES merchants(id),
    amount          DECIMAL(15,2) NOT NULL,
    status          VARCHAR(20) DEFAULT 'pending',     -- pending/completed/expired/failed
    transaction_id  UUID REFERENCES transactions(id),
    expires_at      TIMESTAMPTZ NOT NULL,              -- NOW() + 60 seconds
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- NOTIFICATIONS & AUDIT
-- ============================================

CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    title           VARCHAR(255) NOT NULL,
    body            TEXT NOT NULL,
    type            VARCHAR(50),                       -- transaction/security/promo
    is_read         BOOLEAN DEFAULT false,
    metadata        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Immutable audit log — no updates or deletes ever
CREATE TABLE audit_log (
    id              BIGSERIAL PRIMARY KEY,
    user_id         UUID,
    action          VARCHAR(100) NOT NULL,
    entity_type     VARCHAR(50),
    entity_id       UUID,
    old_value       JSONB,
    new_value       JSONB,
    ip_address      INET,
    device_id       VARCHAR(255),
    created_at      TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Indexes for performance
CREATE INDEX idx_transactions_sender ON transactions(sender_id, initiated_at DESC);
CREATE INDEX idx_transactions_receiver ON transactions(receiver_id, initiated_at DESC);
CREATE INDEX idx_palm_events_user ON palm_scan_events(user_id, created_at DESC);
CREATE INDEX idx_ledger_wallet ON ledger_entries(wallet_id, created_at DESC);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_cnic ON users(cnic);
```

---

## 7. API SPECIFICATION

### Base URL
`https://api.palmpay.pk/v1`

### Authentication
All endpoints (except register/OTP) require:
`Authorization: Bearer {access_token}`

Access token: JWT, expires 15 minutes
Refresh token: Opaque, stored in secure HTTP-only cookie, expires 30 days

---

### 7.1 Auth Endpoints

```
POST   /auth/register/phone          → Send OTP to phone number
POST   /auth/register/verify-otp     → Verify OTP, create user, return tokens
POST   /auth/register/kyc            → Submit CNIC + photos for KYC
POST   /auth/login/phone             → Send OTP to existing number
POST   /auth/login/verify-otp        → Login with OTP, return tokens
POST   /auth/token/refresh           → Get new access token via refresh cookie
POST   /auth/logout                  → Invalidate refresh token
GET    /auth/me                      → Get current user profile
PUT    /auth/me                      → Update profile (name, email, photo)
PUT    /auth/me/username             → Set/change username (unique check)
```

### 7.2 Palm Endpoints

```
POST   /palm/enrollment/initiate     → Start enrollment session (returns QR for kiosk)
GET    /palm/enrollment/status       → Poll enrollment completion
GET    /palm/templates               → List enrolled templates (hand, date, status)
DELETE /palm/templates/{id}          → Revoke specific palm template
POST   /palm/re-enroll               → Trigger re-enrollment flow
GET    /palm/scan-history            → Last 50 scan events for user
POST   /palm/match                   → [INTERNAL — kiosk only] Match palm image
```

### 7.3 Wallet Endpoints

```
GET    /wallet                       → Balance, account number, settings
GET    /wallet/limits                → Current limits and usage today/this month
PUT    /wallet/limits                → Update per-txn / daily / monthly limits
POST   /wallet/freeze                → Freeze wallet (requires PIN)
POST   /wallet/unfreeze              → Unfreeze wallet (requires OTP)
PUT    /wallet/settings              → Toggle palm_pay_enabled, low balance threshold
```

### 7.4 Top-Up Endpoints

```
POST   /topup/jazzcash/initiate      → Create JazzCash checkout, return redirect URL
POST   /topup/jazzcash/webhook       → JazzCash callback on success/failure
POST   /topup/bank/initiate          → Get PalmPay bank details for IBFT
GET    /topup/history                → Top-up transaction history
```

### 7.5 Transfer Endpoints

```
GET    /transfer/lookup?q=           → Search user by phone / username / CNIC
POST   /transfer/initiate            → Initiate P2P transfer (returns preview)
POST   /transfer/confirm             → Confirm transfer with spending PIN
POST   /transfer/request             → Request money from another user
GET    /transfer/requests/incoming   → Pending money requests to me
POST   /transfer/requests/{id}/pay  → Pay a money request
POST   /transfer/requests/{id}/decline → Decline a money request
```

### 7.6 Palm Pay Endpoints

```
POST   /palmpay/request/create       → [KIOSK] Merchant creates payment request
                                       Body: {amount, kiosk_id, device_token}
                                       Returns: {request_id, request_code, expires_at}
                                       Also: opens WebSocket channel for this request_id

WS     /palmpay/request/{id}/stream  → [KIOSK] WebSocket — receive payment result

POST   /palmpay/process              → [INTERNAL] Called by Palm Service after match
                                       Body: {user_id, confidence, request_id, scan_event_id}
                                       Orchestrates: balance check → debit → credit → notify

GET    /palmpay/requests/{id}        → Get payment request status
POST   /palmpay/refund/{txn_id}      → Initiate refund (merchant or admin)
```

### 7.7 Transaction Endpoints

```
GET    /transactions                 → Paginated list (filters: type, date, amount)
GET    /transactions/{id}            → Transaction detail
GET    /transactions/{id}/receipt    → PDF receipt (S3 presigned URL)
POST   /transactions/{id}/dispute    → Report a problem
GET    /analytics/summary            → Weekly/monthly spend summary
GET    /analytics/categories         → Spend by category
```

### 7.8 Notification Endpoints

```
GET    /notifications                → All notifications (paginated)
POST   /notifications/register       → Register FCM device token
PUT    /notifications/{id}/read      → Mark as read
PUT    /notifications/read-all       → Mark all as read
PUT    /notifications/preferences    → Update notification opt-in settings
```

---

## 8. FLUTTER APP STRUCTURE

### Folder Architecture

```
palmpay/
├── android/
│   ├── app/
│   │   ├── src/main/
│   │   │   ├── AndroidManifest.xml
│   │   │   └── kotlin/.../MainActivity.kt
│   │   └── build.gradle
│   └── build.gradle
├── lib/
│   ├── main.dart                    # App entry, providers, theme init
│   ├── app.dart                     # MaterialApp, router, theme
│   │
│   ├── core/
│   │   ├── constants/
│   │   │   ├── app_colors.dart      # Color palette
│   │   │   ├── app_text_styles.dart # Typography scale
│   │   │   ├── app_spacing.dart     # 4px grid spacing
│   │   │   └── api_endpoints.dart   # All API URL strings
│   │   ├── network/
│   │   │   ├── dio_client.dart      # Dio instance + interceptors
│   │   │   ├── auth_interceptor.dart# JWT attach + refresh logic
│   │   │   └── network_exceptions.dart
│   │   ├── storage/
│   │   │   ├── secure_storage.dart  # flutter_secure_storage wrapper
│   │   │   └── hive_storage.dart    # Local cache
│   │   ├── router/
│   │   │   ├── app_router.dart      # GoRouter configuration
│   │   │   ├── app_routes.dart      # Route name constants
│   │   │   └── guards.dart          # Auth guard, KYC guard
│   │   └── utils/
│   │       ├── formatters.dart      # Currency, date, CNIC formatters
│   │       ├── validators.dart      # Form validation functions
│   │       └── extensions.dart      # Dart extension methods
│   │
│   ├── features/
│   │   ├── onboarding/
│   │   │   ├── data/
│   │   │   │   ├── auth_repository.dart
│   │   │   │   └── auth_remote_datasource.dart
│   │   │   ├── domain/
│   │   │   │   ├── entities/user_entity.dart
│   │   │   │   └── usecases/register_usecase.dart
│   │   │   └── presentation/
│   │   │       ├── screens/
│   │   │       │   ├── splash_screen.dart
│   │   │       │   ├── language_screen.dart
│   │   │       │   ├── phone_entry_screen.dart
│   │   │       │   ├── otp_screen.dart
│   │   │       │   ├── kyc_screen.dart
│   │   │       │   ├── palm_enrollment_screen.dart
│   │   │       │   └── enrollment_success_screen.dart
│   │   │       ├── widgets/
│   │   │       │   ├── otp_input_field.dart
│   │   │       │   └── enrollment_step_indicator.dart
│   │   │       └── providers/
│   │   │           └── auth_provider.dart
│   │   │
│   │   ├── wallet/
│   │   │   ├── data/
│   │   │   │   ├── wallet_repository.dart
│   │   │   │   └── wallet_remote_datasource.dart
│   │   │   ├── domain/
│   │   │   │   ├── entities/wallet_entity.dart
│   │   │   │   └── entities/transaction_entity.dart
│   │   │   └── presentation/
│   │   │       ├── screens/
│   │   │       │   ├── home_screen.dart
│   │   │       │   ├── add_money_screen.dart
│   │   │       │   ├── send_money_screen.dart
│   │   │       │   ├── send_confirm_screen.dart
│   │   │       │   ├── request_money_screen.dart
│   │   │       │   ├── transaction_history_screen.dart
│   │   │       │   └── transaction_detail_screen.dart
│   │   │       ├── widgets/
│   │   │       │   ├── balance_card.dart
│   │   │       │   ├── quick_action_bar.dart
│   │   │       │   ├── transaction_list_item.dart
│   │   │       │   └── amount_input.dart
│   │   │       └── providers/
│   │   │           ├── wallet_provider.dart
│   │   │           └── transaction_provider.dart
│   │   │
│   │   ├── scan/
│   │   │   ├── data/
│   │   │   │   └── scan_repository.dart
│   │   │   └── presentation/
│   │   │       ├── screens/
│   │   │       │   ├── scan_screen.dart          # Central scan tab
│   │   │       │   ├── scan_result_success.dart
│   │   │       │   ├── scan_result_failed.dart
│   │   │       │   └── scan_result_low_balance.dart
│   │   │       ├── widgets/
│   │   │       │   ├── scan_viewfinder.dart      # Animated frame
│   │   │       │   └── confidence_indicator.dart
│   │   │       └── providers/
│   │   │           └── scan_provider.dart
│   │   │
│   │   ├── analytics/
│   │   │   └── presentation/
│   │   │       ├── screens/
│   │   │       │   └── analytics_screen.dart
│   │   │       └── widgets/
│   │   │           ├── spend_bar_chart.dart
│   │   │           └── category_pie_chart.dart
│   │   │
│   │   └── profile/
│   │       ├── data/
│   │       │   └── profile_repository.dart
│   │       └── presentation/
│   │           ├── screens/
│   │           │   ├── profile_screen.dart
│   │           │   ├── digital_id_screen.dart
│   │           │   ├── palm_manager_screen.dart
│   │           │   ├── security_screen.dart
│   │           │   ├── wallet_settings_screen.dart
│   │           │   ├── notification_settings_screen.dart
│   │           │   ├── device_manager_screen.dart
│   │           │   └── support_screen.dart
│   │           └── providers/
│   │               └── profile_provider.dart
│   │
│   └── shared/
│       ├── widgets/
│       │   ├── pp_button.dart           # Primary button component
│       │   ├── pp_text_field.dart       # Themed input field
│       │   ├── pp_bottom_sheet.dart     # Consistent bottom sheet
│       │   ├── pp_loading.dart          # Loading states
│       │   ├── pp_error_state.dart      # Error display
│       │   ├── pp_avatar.dart           # User avatar component
│       │   ├── pp_amount_display.dart   # Formatted PKR amount
│       │   └── pp_pin_input.dart        # 4-digit PIN entry
│       └── models/
│           ├── api_response.dart        # Generic API response wrapper
│           └── pagination.dart          # Paginated list model
│
├── pubspec.yaml
├── analysis_options.yaml
└── .env                               # Environment variables (gitignored)
```

### pubspec.yaml — Dependencies

```yaml
name: palmpay
description: Palm Vein Biometric Wallet
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'
  flutter: '>=3.10.0'

dependencies:
  flutter:
    sdk: flutter

  # Navigation
  go_router: ^13.0.0

  # State Management
  flutter_riverpod: ^2.4.0
  riverpod_annotation: ^2.3.0

  # Network
  dio: ^5.4.0
  web_socket_channel: ^2.4.0

  # Local Storage
  flutter_secure_storage: ^9.0.0
  hive_flutter: ^1.1.0

  # UI Components
  flutter_svg: ^2.0.9
  cached_network_image: ^3.3.0
  shimmer: ^3.0.0
  lottie: ^3.0.0               # For scan animations
  fl_chart: ^0.66.0            # Analytics charts
  pinput: ^3.0.1               # OTP/PIN input
  image_picker: ^1.0.7         # KYC document photos

  # Utilities
  intl: ^0.19.0                # Currency & date formatting
  freezed_annotation: ^2.4.0  # Immutable data classes
  json_annotation: ^4.8.0
  permission_handler: ^11.1.0  # Camera permissions

  # Firebase
  firebase_core: ^2.24.0
  firebase_messaging: ^14.7.0  # Push notifications

  # Deep Linking (JazzCash redirect)
  uni_links: ^0.5.1

  # PDF
  pdf: ^3.10.7                 # Receipt generation
  printing: ^5.11.1            # Share PDF receipt

  # Security
  local_auth: ^2.1.8           # Fingerprint for app lock

  # Crash Reporting
  sentry_flutter: ^7.13.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  build_runner: ^2.4.7
  riverpod_generator: ^2.3.0
  freezed: ^2.4.6
  json_serializable: ^6.7.1
  flutter_lints: ^3.0.0
  mockito: ^5.4.4
```

---

## 9. SECURITY ARCHITECTURE

### 9.1 Authentication Security

**JWT Token Design:**
```json
{
  "sub": "user-uuid",
  "phone": "+923001234567",
  "device_id": "device-uuid",
  "kyc_status": "approved",
  "iat": 1702000000,
  "exp": 1702000900,         // 15 min
  "iss": "palmpay.pk"
}
```

- Access token: 15-minute expiry (minimizes breach window)
- Refresh token: 30-day expiry, stored HTTP-only cookie (XSS-proof)
- Each refresh token is device-bound (device_id in claims)
- Token rotation on every refresh (old token immediately invalidated)
- Concurrent device support: each device has independent refresh token

**Rate Limiting (Redis):**
- OTP send: max 3 per phone per hour
- OTP verify: max 5 attempts per session then 30-min lockout
- Login attempts: max 5 per IP per hour
- API calls: 100/min per user, 1000/min per IP

### 9.2 Palm Template Security

- Raw NIR images deleted from server immediately after feature extraction
- Only feature vector (mathematical representation) stored
- Feature vector encrypted with AES-256-GCM before storage
- Encryption key stored in AWS KMS (not in application code)
- Template stored in S3 with bucket policy: no public access, encrypted at rest
- Template referenced by opaque key only — never user-identifiable path
- Template never transmitted to client device under any circumstances
- Feature extraction happens server-side only

### 9.3 Payment Security

**Idempotency:**
Every payment request has a UUID idempotency key. If the same request arrives twice (network retry), the second one returns the first result without re-processing. Prevents double-charges.

**Transaction Atomicity (PostgreSQL):**
```sql
BEGIN;
  -- Lock both wallets for update (prevents race condition)
  SELECT balance FROM wallets WHERE id = $sender_wallet FOR UPDATE;
  SELECT balance FROM wallets WHERE id = $merchant_wallet FOR UPDATE;

  -- Verify balance sufficient
  -- Debit sender
  UPDATE wallets SET balance = balance - $amount WHERE id = $sender_wallet;

  -- Credit merchant
  UPDATE wallets SET balance = balance + $amount WHERE id = $merchant_wallet;

  -- Record ledger entries (double-entry)
  INSERT INTO ledger_entries ...;

  -- Record transaction
  INSERT INTO transactions ...;
COMMIT;
```
If any step fails, entire transaction rolls back. Balance never goes negative. No partial states.

**Confidence Threshold Enforcement:**
- Minimum 0.97 (97%) confidence for payment authorization
- Threshold stored in database per service type (not hardcoded)
- Audit log records actual confidence on every payment
- If model version changes, threshold is re-evaluated

### 9.4 Device & Network Security

**Android App:**
- Certificate pinning (pin to your server's TLS certificate)
- Root detection (warn user, disable palm pay on rooted devices)
- Screenshot prevention (FLAG_SECURE on payment screens)
- Minimum Android 7.0 (API 24) required for modern TLS support
- ProGuard/R8 obfuscation for release builds
- No sensitive data in SharedPreferences (use FlutterSecureStorage backed by Android Keystore)

**API Security:**
- TLS 1.3 only (disable 1.0, 1.1, 1.2 on Nginx)
- HSTS header (force HTTPS for 1 year)
- CORS: allow only your app's package origin
- All inputs sanitized and validated server-side
- SQL: parameterized queries only (no string interpolation)
- Kiosk device tokens: SHA-256 hashed in DB (like passwords)

---

## 10. PALM VEIN PIPELINE INTEGRATION

### How Your Existing Model Connects

Your model already works. The mobile app never touches the model directly. Here is the exact integration architecture:

```
Kiosk NIR Camera
      │
      │ Raw NIR image (JPEG/PNG, 640x480 minimum)
      ▼
Palm Service (FastAPI — your existing code wrapped)
POST /internal/palm/match
Body: {image_base64: "...", request_id: "..."}
      │
      │ Calls your existing inference function
      ▼
Your Model
Returns: {user_id: "uuid" | null, confidence: 0.9731, duration_ms: 340}
      │
      ▼
Palm Service validates threshold (≥ 0.97)
      │
If match:
POST /internal/palmpay/process
{user_id, confidence, request_id, scan_event_id}
      │
      ▼
Wallet Service executes payment
      │
      ▼
WebSocket pushes result to waiting merchant kiosk
```

### Palm Service Wrapper (palmpay/services/palm_service.py)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64
import numpy as np
import cv2
import time

# Import your existing model
from your_model import PalmVeinMatcher  # adjust to your actual import

app = FastAPI()
matcher = PalmVeinMatcher()  # your existing class

CONFIDENCE_THRESHOLD = 0.97
LIVENESS_THRESHOLD = 0.85

class MatchRequest(BaseModel):
    image_base64: str
    request_id: str
    device_id: str

class MatchResponse(BaseModel):
    user_id: str | None
    confidence: float
    liveness_score: float
    result: str  # matched / no_match / liveness_fail / low_quality
    duration_ms: int

@app.post("/internal/palm/match", response_model=MatchResponse)
async def match_palm(req: MatchRequest):
    start = time.time()

    # Decode image
    img_bytes = base64.b64decode(req.image_base64)
    img_array = np.frombuffer(img_bytes, dtype=np.uint8)
    image = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)

    if image is None:
        raise HTTPException(400, "Invalid image")

    # Liveness check (your existing function)
    liveness_score = matcher.check_liveness(image)
    if liveness_score < LIVENESS_THRESHOLD:
        return MatchResponse(
            user_id=None,
            confidence=0.0,
            liveness_score=liveness_score,
            result="liveness_fail",
            duration_ms=int((time.time() - start) * 1000)
        )

    # Run matching against enrolled templates
    user_id, confidence = matcher.match(image)

    result = "matched" if (user_id and confidence >= CONFIDENCE_THRESHOLD) else "no_match"

    duration = int((time.time() - start) * 1000)

    # Log scan event to DB
    await log_scan_event(req.device_id, user_id, confidence, result, req.request_id, duration)

    return MatchResponse(
        user_id=user_id if result == "matched" else None,
        confidence=confidence or 0.0,
        liveness_score=liveness_score,
        result=result,
        duration_ms=duration
    )
```

### Kiosk Client (Python, runs on kiosk hardware)

```python
# kiosk_client.py — runs on merchant kiosk
import websocket
import requests
import json
import cv2
import base64
import time

SERVER = "wss://api.palmpay.pk/v1"
DEVICE_TOKEN = "kiosk-device-token-from-setup"
KIOSK_ID = "kiosk-uuid-from-setup"

def capture_palm_image():
    """Capture from NIR camera"""
    cap = cv2.VideoCapture(0)  # adjust index for NIR camera
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None
    _, buffer = cv2.imencode('.jpg', frame)
    return base64.b64encode(buffer).decode('utf-8')

def run_payment(amount: float):
    """Complete payment flow"""

    # Step 1: Create payment request
    resp = requests.post(
        f"https://api.palmpay.pk/v1/palmpay/request/create",
        json={"amount": amount, "kiosk_id": KIOSK_ID},
        headers={"Authorization": f"Device {DEVICE_TOKEN}"}
    )
    request = resp.json()
    request_id = request['request_id']

    # Step 2: Open WebSocket for result
    ws_url = f"{SERVER}/palmpay/request/{request_id}/stream"

    result_received = {"data": None}

    def on_message(ws, message):
        result_received["data"] = json.loads(message)
        ws.close()

    ws = websocket.WebSocketApp(
        ws_url,
        header={"Authorization": f"Device {DEVICE_TOKEN}"},
        on_message=on_message
    )

    # Step 3: Prompt customer to scan
    show_on_screen("Place your palm on the scanner")

    # Step 4: Capture palm image and send to palm service
    image_b64 = capture_palm_image()
    requests.post(
        "https://api.palmpay.pk/v1/internal/palm/match",
        json={"image_base64": image_b64, "request_id": request_id, "device_id": KIOSK_ID}
    )

    # Step 5: Wait for result (max 10 seconds)
    ws.run_forever()

    result = result_received["data"]
    if result and result["status"] == "completed":
        show_on_screen(f"Payment Successful\nPKR {amount}")
        print_receipt(result)
    else:
        show_on_screen(f"Payment Failed\n{result.get('reason', 'Please try again')}")
```

---

## 11. PAYMENT FLOW — TECHNICAL DEEP DIVE

### Sequence Diagram (Millisecond Level)

```
Customer      Kiosk         API Gateway    Wallet Svc    Palm Svc     Your Model    FCM
   │             │                │              │            │             │          │
   │  Approaches │                │              │            │             │          │
   │   counter   │                │              │            │             │          │
   │             │─POST create────►              │            │             │          │
   │             │◄───{request_id}─              │            │             │          │
   │             │                │              │            │             │          │
   │◄──"Place    │                │              │            │             │          │
   │    palm"────│                │              │            │             │          │
   │             │                │              │            │             │          │
t=0│─Places palm─►                │              │            │             │          │
   │             │─NIR capture    │              │            │             │          │
   │             │─POST /match────►──────────────────────────►─────────────►          │
   │             │                │              │            │◄──{id,conf}─│          │
   │             │                │              │            │             │          │
   │             │                │              │◄─POST      │             │          │
   │             │                │              │  process───│             │          │
   │             │                │              │  ┌──BEGIN TX             │          │
   │             │                │              │  │ LOCK wallets          │          │
   │             │                │              │  │ CHECK balance         │          │
   │             │                │              │  │ DEBIT customer        │          │
   │             │                │              │  │ CREDIT merchant       │          │
   │             │                │              │  │ INSERT transaction    │          │
   │             │                │              │  └──COMMIT TX            │          │
   │             │                │              │             │             │          │
   │             │◄──WS: success──────────────────             │             │          │
t=1.2s           │                │              │─────────────────────────────────────►│
   │◄────────────│ "Payment OK"   │              │             │             │ Push notif│
```

**Total time breakdown:**
- NIR capture: ~80ms
- Network to server: ~50ms
- Palm inference (your model): ~300–500ms
- DB transaction: ~20ms
- WebSocket push: ~10ms
- Network back to kiosk: ~50ms
- **Total: ~510–710ms** ← well within 1.5s target

### Edge Cases & How They're Handled

| Scenario | Detection | Response |
|---|---|---|
| Network drops mid-payment | Idempotency key | Safe to retry — same result returned |
| DB crashes mid-transaction | PostgreSQL ACID rollback | No money moved, request expires |
| Customer removes palm too fast | Low confidence score | Retry prompt (up to 3 attempts) |
| Fake hand / photo attack | Liveness check fails | Blocked before matching even runs |
| Two customers scan at same time | Request IDs isolate each session | Independent parallel processing |
| Kiosk offline | Local whitelist cache | Allows known users for small amounts, syncs later |
| Wallet exactly at limit | Balance check before debit | Rejected with exact shortfall amount shown |
| Merchant tries to overcharge | Amount set before palm scan | Customer never touches amount field |

---

## 12. UI/UX DESIGN SYSTEM

### Color Palette

```dart
// app_colors.dart
class AppColors {
  // Brand
  static const primary     = Color(0xFF1A56FF);   // Electric blue — CTAs, active states
  static const palmGlow    = Color(0xFF00D4AA);   // Teal — biometric elements
  static const success     = Color(0xFF00C97A);   // Green — payments complete
  static const warning     = Color(0xFFF5A623);   // Amber — low balance, retry
  static const danger      = Color(0xFFFF4B55);   // Red — failures, freeze

  // Neutrals (Dark theme — primary)
  static const bgBase      = Color(0xFF070C18);   // Page background
  static const bgSurface   = Color(0xFF0D1525);   // Cards, sheets
  static const bgCard      = Color(0xFF111E34);   // Elevated cards
  static const border      = Color(0x2A1E6FFF);   // Subtle borders

  // Text
  static const textPrimary = Color(0xFFE8EDF8);   // Headings, main text
  static const textMuted   = Color(0xFF6B7A9A);   // Secondary, timestamps

  // Light theme (KYC screens, receipt PDF)
  static const ltBg        = Color(0xFFF4F6FB);
  static const ltCard      = Color(0xFFFFFFFF);
  static const ltText      = Color(0xFF0D1525);
  static const ltMuted     = Color(0xFF8C96B0);
}
```

### Typography Scale

```dart
// app_text_styles.dart
class AppTextStyles {
  static const balance = TextStyle(
    fontSize: 40, fontWeight: FontWeight.w600,
    letterSpacing: -1.0, color: AppColors.textPrimary
  );
  static const h1 = TextStyle(
    fontSize: 24, fontWeight: FontWeight.w600,
    letterSpacing: -0.5, color: AppColors.textPrimary
  );
  static const h2 = TextStyle(
    fontSize: 20, fontWeight: FontWeight.w500,
    color: AppColors.textPrimary
  );
  static const body = TextStyle(
    fontSize: 15, fontWeight: FontWeight.w400,
    color: AppColors.textPrimary, height: 1.5
  );
  static const label = TextStyle(
    fontSize: 12, fontWeight: FontWeight.w500,
    letterSpacing: 0.08, color: AppColors.textMuted
  );
  static const amount = TextStyle(
    fontSize: 17, fontWeight: FontWeight.w600,
    fontFeatures: [FontFeature.tabularFigures()]
  );
  static const mono = TextStyle(
    fontFamily: 'RobotoMono', fontSize: 13,
    letterSpacing: 0.05
  );
}
```

### 4px Spacing Grid

```dart
// app_spacing.dart
class S {
  static const xs  = 4.0;
  static const sm  = 8.0;
  static const md  = 16.0;
  static const lg  = 24.0;
  static const xl  = 32.0;
  static const xxl = 48.0;
}
```

### Core Component — PPButton

```dart
// pp_button.dart
enum ButtonStyle { primary, secondary, destructive, ghost }

class PPButton extends StatelessWidget {
  final String label;
  final VoidCallback? onTap;
  final ButtonStyle style;
  final bool isLoading;
  final IconData? icon;

  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: isLoading ? null : onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        height: 52,
        width: double.infinity,
        decoration: BoxDecoration(
          color: _backgroundColor,
          borderRadius: BorderRadius.circular(14),
          border: style == ButtonStyle.secondary
              ? Border.all(color: AppColors.border, width: 0.5)
              : null,
        ),
        child: Center(child: isLoading
            ? SizedBox(width: 20, height: 20,
                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
            : Text(label, style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w600))
        ),
      ),
    );
  }
}
```

### Animation Standards

- Screen transitions: slide from right (forward), slide out right (back), 250ms
- Bottom sheets: slide up, 300ms, elastic curve
- Numbers (balance): count-up animation on load, 600ms
- Scan pulse: radial pulse from center, 1.2s loop
- Success state: Lottie checkmark, 800ms
- Error state: shake animation, 400ms
- All loading states: shimmer skeleton (never spinner alone)

---

## 13. SCREEN INVENTORY — ALL 28 SCREENS

### Onboarding (7 screens)

| # | Screen | Key Elements |
|---|---|---|
| 1 | Splash | App logo, version, 1.5s auto-advance |
| 2 | Language Select | Urdu / English toggle, persist to prefs |
| 3 | Phone Entry | +92 prefix, number field, "Get OTP" button, T&C link |
| 4 | OTP Verification | 6-digit pinput, 120s countdown, resend, auto-submit on fill |
| 5 | KYC — CNIC | Name field, 13-digit CNIC, front/back photo capture |
| 6 | Palm Enrollment | Instruction animation, QR code for kiosk pairing, polling status |
| 7 | Enrollment Success | Success Lottie, "Go to wallet" CTA |

### Home Tab (6 screens)

| # | Screen | Key Elements |
|---|---|---|
| 8 | Wallet Dashboard | Balance card, 4 quick actions, 5 recent transactions, bottom nav |
| 9 | Add Money | Method select, amount input, fee display, confirm |
| 10 | Send Money | Recipient search, recent contacts, amount + note |
| 11 | Send Confirm | Recipient preview, amount, PIN entry, send button |
| 12 | Request Money | Amount, note, recipient, generates request notification |
| 13 | Incoming Requests | List of pending requests, pay / decline each |

### Scan Tab (4 screens)

| # | Screen | Key Elements |
|---|---|---|
| 14 | Scan Home | Explanation of palm pay, "Visit nearest merchant" CTA, QR fallback |
| 15 | Scan Result — Success | Green check, merchant name, amount, timestamp, receipt button |
| 16 | Scan Result — Failed | Red X, failure reason, retry count, fallback options |
| 17 | Scan Result — Low Balance | Balance shown, shortfall amount, "Top up now" deeplink |

### History Tab (2 screens)

| # | Screen | Key Elements |
|---|---|---|
| 18 | Transaction History | Filterable list, date groups, search bar, export button |
| 19 | Transaction Detail | Full receipt view, share as PDF, report dispute |

### Profile Tab (9 screens)

| # | Screen | Key Elements |
|---|---|---|
| 20 | Profile Home | Avatar, name, KYC badge, settings list |
| 21 | Digital ID Card | Name, account no, CNIC (masked), QR, download PDF |
| 22 | Palm Manager | Enrolled hands list, last scan, re-enroll, revoke |
| 23 | Security Settings | Thresholds, limits, app lock, palm pay toggle |
| 24 | Wallet Settings | Limits config, freeze/unfreeze, auto top-up |
| 25 | Device Manager | Active devices list, remote logout |
| 26 | Notification Settings | Toggle each notification type |
| 27 | Help & Support | FAQ, chat link, phone number, ticket history |
| 28 | Spending Analytics | Bar chart, category breakdown, month selector |

---

## 14. THIRD-PARTY INTEGRATIONS

### 14.1 JazzCash (Top-Up)

- **Integration type:** JazzCash Merchant Payment API (REST)
- **Sandbox:** https://sandbox.jazzcash.com.pk/
- **Required credentials:** Merchant ID, Password, Integrity Salt
- **Flow:** App calls your backend → backend creates JazzCash checkout session → returns URL → app opens in WebView → JazzCash redirects back on success/failure → your webhook endpoint receives notification → wallet credited
- **Webhook endpoint:** `POST /topup/jazzcash/webhook` (verify HMAC signature)
- **Docs:** developer.jazzcash.com.pk

### 14.2 NADRA VERISYS (KYC)

- **Integration type:** REST API (requires formal government agreement)
- **What it does:** Verifies CNIC number against national database, validates biographic data
- **V1 fallback:** Manual review queue if VERISYS access not yet obtained
- **Alternative for V1:** Integrate BISP / 8171 CNIC lookup as a lighter verification

### 14.3 Firebase Cloud Messaging (Push Notifications)

- **Setup:** google-services.json in android/app/
- **Flow:** On login, app sends FCM token to your backend (`POST /notifications/register`)
- **Backend sends notifications:** Using Firebase Admin SDK (Python)
```python
import firebase_admin
from firebase_admin import credentials, messaging

def send_push(fcm_token: str, title: str, body: str, data: dict = {}):
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data=data,
        token=fcm_token,
        android=messaging.AndroidConfig(priority='high')
    )
    messaging.send(message)
```

### 14.4 Twilio SMS (OTP)

- **Cost:** ~$0.0075 per SMS to Pakistan
- **Pakistan alternative:** Telenor Messaging API (cheaper, local)
- **Usage:** OTP only — 6-digit code, 120s expiry
- **Rate limit:** 3 OTP requests per phone per hour

### 14.5 AWS Services

- **S3:** Palm template encrypted blob storage + profile photos + receipt PDFs
  - Bucket: `palmpay-templates-prod` (private, server-only access)
  - Bucket: `palmpay-receipts-prod` (presigned URL access, 24hr expiry)
- **KMS:** Encryption key management for palm templates
- **CloudFront:** CDN for static assets (app icons, merchant logos)

### 14.6 Sentry (Error Monitoring)

- Flutter SDK: `sentry_flutter`
- Captures: crashes, unhandled exceptions, slow frames
- Python SDK: FastAPI middleware
- Captures: 5xx errors, slow endpoints (>1s), unhandled exceptions

---

## 15. TESTING STRATEGY

### 15.1 Unit Tests (Flutter)

```
test/
├── features/
│   ├── wallet/
│   │   ├── wallet_provider_test.dart      # Balance updates, limit checks
│   │   └── transaction_entity_test.dart   # Formatting, status logic
│   ├── onboarding/
│   │   ├── auth_provider_test.dart        # OTP flow state machine
│   │   └── validators_test.dart           # Phone, CNIC, amount validation
│   └── scan/
│       └── confidence_threshold_test.dart # Threshold enforcement logic
└── shared/
    └── formatters_test.dart               # PKR formatting, date formatting
```

**Coverage target:** 80% for business logic (providers, use cases)

### 15.2 Widget Tests

- Balance card renders correct amount
- Transaction list item shows correct colors (green/red)
- OTP input auto-submits on 6 digits
- PIN input masks digits correctly
- Error states render correct messages

### 15.3 Integration Tests (flutter_test + Dio mock)

- Full onboarding flow (phone → OTP → KYC → enrollment → home)
- Send money flow end-to-end (search → select → amount → PIN → confirmation)
- Transaction history loads with filters applied

### 15.4 Backend Tests (pytest)

```
tests/
├── test_auth.py              # Register, OTP, token refresh, logout
├── test_wallet.py            # Balance, top-up, transfer, limits
├── test_palm_pay.py          # Payment request, authorization, failure cases
├── test_palm_match.py        # Confidence threshold, liveness, no-match
├── test_transaction.py       # Atomicity, idempotency, concurrent payments
└── test_security.py          # Rate limiting, invalid tokens, injection attempts
```

**Critical test cases:**
- Double-charge prevention (same idempotency key sent twice)
- Concurrent payments (two kiosks scanning same user simultaneously)
- Insufficient balance with exact amount
- Confidence exactly at threshold (97.0% vs 96.9%)
- Wallet freeze blocks all outgoing payments
- Frozen wallet unfreeze requires OTP

### 15.5 Load Testing (Locust)

**Scenarios:**
- 100 concurrent palm pay transactions
- 500 concurrent balance reads
- 1000 push notifications dispatched simultaneously
- Kiosk WebSocket: 50 concurrent connections

**Targets:**
- `POST /palmpay/process`: < 800ms p99
- `GET /wallet`: < 100ms p99
- WebSocket delivery: < 200ms p99

### 15.6 Security Testing

- OWASP Mobile Top 10 manual review
- SQL injection attempts on all input fields
- JWT manipulation (algorithm confusion, expired token acceptance)
- Certificate pinning bypass attempt
- Root detection bypass attempt
- Replay attack on payment (same request_id reused)

---

## 16. PLAY STORE SUBMISSION CHECKLIST

### App Metadata
- [ ] App name: PalmPay (or chosen name)
- [ ] Short description (80 chars): "Pay with your palm. No card, no PIN, no phone at checkout."
- [ ] Full description (4000 chars): Feature overview, how it works, security details
- [ ] App icon: 512×512 PNG (no alpha)
- [ ] Feature graphic: 1024×500 PNG
- [ ] Screenshots: minimum 2 per device type (phone), up to 8
  - [ ] Wallet dashboard
  - [ ] Scan screen
  - [ ] Payment success
  - [ ] Transaction history
  - [ ] Profile / digital ID
- [ ] Category: Finance
- [ ] Content rating: Complete questionnaire (IARC)
- [ ] Privacy policy URL: Required for financial apps (must be live URL)

### Technical Requirements
- [ ] Signed release APK / AAB with upload keystore
- [ ] Keystore backed up in 2+ secure locations (losing it = cannot update app ever)
- [ ] minSdkVersion: 24 (Android 7.0)
- [ ] targetSdkVersion: 34 (Android 14)
- [ ] ProGuard/R8 enabled for release
- [ ] All permissions declared in AndroidManifest with justification
  - CAMERA (KYC document photos)
  - INTERNET
  - POST_NOTIFICATIONS (Android 13+)
  - BIOMETRIC (app lock feature)
  - VIBRATE (haptic feedback)
- [ ] App size < 50MB (use deferred components if needed)
- [ ] No crashing on fresh install + launch

### Policy Compliance (Financial App)
- [ ] Privacy policy covers: data collected, how stored, user rights, deletion
- [ ] Terms of service published
- [ ] Declare if app handles financial transactions (it does)
- [ ] Declare biometric data usage (required disclosure)
- [ ] If accepting real money: SBP compliance documentation
- [ ] For V1 beta: use "closed testing" track (up to 100 testers, no SBP license needed)
- [ ] For public release: requires SBP EMI partnership or license

### Play Store Tracks (Recommended Order)
1. **Internal testing** (team only, instant publish, Days 1–7)
2. **Closed testing / Alpha** (50–100 invited users, Day 8–9)
3. **Open testing / Beta** (public opt-in, Day 10+)
4. **Production** (full rollout — requires SBP license for real transactions)

---

## 17. 10-DAY SPRINT PLAN

> **Assumption:** You have Flutter installed, your FastAPI palm model running, and a PostgreSQL instance available.
> **Goal:** Working Android app + backend + 2 kiosk-tested merchants + Play Store internal testing track by Day 10.

---

### DAY 1 — FOUNDATION & ENVIRONMENT
**Theme: Set up everything so Day 2–10 is pure building**

**Morning (4 hours)**
- [ ] Create Flutter project: `flutter create palmpay --org pk.palmpay`
- [ ] Set up folder structure exactly as specified in Section 8
- [ ] Add all dependencies to pubspec.yaml, run `flutter pub get`
- [ ] Configure GoRouter with all 28 routes (placeholder screens for now)
- [ ] Create app_colors.dart, app_text_styles.dart, app_spacing.dart
- [ ] Set up MaterialApp with dark theme, custom colors
- [ ] Configure 4 bottom tabs with bottom navigation bar
- [ ] Set up Android: change app ID, app name, icons

**Afternoon (4 hours)**
- [ ] Set up FastAPI backend: `fastapi-starter` or manual project
- [ ] Install: FastAPI, uvicorn, sqlalchemy, psycopg2, python-jose, passlib, redis, celery
- [ ] Create PostgreSQL database `palmpay_db`
- [ ] Write all schema SQL from Section 6, run migrations (use Alembic)
- [ ] Create base Dio client with auth interceptor in Flutter
- [ ] Set up FlutterSecureStorage, Hive initialization
- [ ] Set up Sentry in both Flutter and FastAPI
- [ ] Create .env files (.gitignore both)
- [ ] Push to GitHub, set up main + develop branches

**Evening (2 hours)**
- [ ] Set up Firebase project, download google-services.json
- [ ] Configure FCM in FastAPI (firebase-admin)
- [ ] Write README with local setup instructions
- [ ] Verify Flutter app runs on device: sees 4 tabs, navigates between screens
- [ ] Verify FastAPI starts: GET /health returns 200

**End of Day 1 deliverable:** Running Flutter shell + FastAPI skeleton + DB schema in place

---

### DAY 2 — AUTHENTICATION COMPLETE
**Theme: User can register, verify OTP, and be issued a JWT**

**Tasks:**
- [ ] FastAPI: `POST /auth/register/phone` — validate Pakistani number, store in Redis, send OTP via Twilio
- [ ] FastAPI: `POST /auth/register/verify-otp` — check Redis, create user + wallet record, issue JWT pair
- [ ] FastAPI: `POST /auth/token/refresh` — validate refresh cookie, rotate tokens
- [ ] FastAPI: JWT middleware — verify on all protected routes
- [ ] FastAPI: Rate limiting middleware (slowapi library) — 3 OTP requests/hour
- [ ] Flutter: Phone Entry screen — +92 prefix, validation, "Get OTP" → API call
- [ ] Flutter: OTP screen — pinput widget, 120s countdown, auto-submit, resend
- [ ] Flutter: AuthProvider (Riverpod) — store tokens in FlutterSecureStorage
- [ ] Flutter: GoRouter auth guard — redirect to login if no valid token
- [ ] Flutter: Token refresh interceptor in Dio — auto-refresh on 401

**Test:**
- Register new number → receive OTP → enter OTP → JWT stored → redirected to enrollment placeholder
- Enter wrong OTP 5 times → account locked for 30 minutes
- Token expires → Dio interceptor auto-refreshes → request retried transparently

**End of Day 2 deliverable:** Full auth flow working end-to-end on device

---

### DAY 3 — KYC + PALM ENROLLMENT FLOW
**Theme: User can complete identity verification and palm enrollment**

**Tasks:**
- [ ] FastAPI: `POST /auth/register/kyc` — accept CNIC + photos, store in S3, create KYC queue entry
- [ ] FastAPI: KYC status webhook endpoint (NADRA or manual review)
- [ ] FastAPI: `POST /palm/enrollment/initiate` — create enrollment session, return QR data
- [ ] FastAPI: `GET /palm/enrollment/status` — poll enrollment completion
- [ ] FastAPI: Palm enrollment endpoint called by kiosk — receive 3 scans, run your model, store encrypted template in S3
- [ ] Flutter: KYC screen — name input, CNIC input (formatted auto), image_picker for front/back
- [ ] Flutter: Palm Enrollment screen — show QR code (link user_id to kiosk session), polling animation, success/fail states
- [ ] Flutter: Enrollment Success screen — Lottie animation
- [ ] Kiosk: Basic enrollment client — open session by QR scan, capture 3 NIR images, send to enrollment endpoint
- [ ] Set up Alembic migration for palm_templates table

**Test:**
- Submit CNIC + photos → KYC pending status shown
- Visit kiosk, scan QR → kiosk captures 3 palm images → template stored → app shows "Enrolled!"
- Attempt to re-enroll → previous template marked inactive → new template enrolled

**End of Day 3 deliverable:** User can fully enroll — identity verified + palm registered

---

### DAY 4 — WALLET CORE
**Theme: Balance, top-up, and P2P transfer working**

**Tasks:**
- [ ] FastAPI: `GET /wallet` — return balance, account number, settings
- [ ] FastAPI: `POST /topup/jazzcash/initiate` — create JazzCash checkout, return URL
- [ ] FastAPI: `POST /topup/jazzcash/webhook` — verify HMAC, credit wallet, send push notification
- [ ] FastAPI: `GET /transfer/lookup` — search user by phone/username
- [ ] FastAPI: `POST /transfer/initiate` → preview (does not debit yet)
- [ ] FastAPI: `POST /transfer/confirm` — verify spending PIN, execute atomic transfer
- [ ] FastAPI: Double-entry ledger entries written on every balance change
- [ ] Flutter: Wallet Dashboard screen — balance card (hide/show toggle), 4 quick actions, 5 recent transactions
- [ ] Flutter: Balance card — animated count-up on load
- [ ] Flutter: Add Money screen — method select, amount input, opens JazzCash WebView
- [ ] Flutter: Send Money screen — recipient search with debounce, recent contacts
- [ ] Flutter: Send Confirm screen — PIN input (PPPinInput widget), confirmation
- [ ] Flutter: WalletProvider — balance refresh, optimistic UI on send

**Test:**
- Load wallet URL in WebView, complete JazzCash test payment → balance updated → push notification received
- Send PKR 500 to another registered user → both balances update correctly
- Send PKR 999,999 (over limit) → rejected with clear error message
- Send to unknown user → "User not found" message

**End of Day 4 deliverable:** Working wallet — can hold, receive, and send money

---

### DAY 5 — PALM PAY CORE
**Theme: End-to-end palm payment from kiosk to wallet deduction to push notification**

> **This is the most critical day. Take no shortcuts.**

**Tasks:**
- [ ] FastAPI: `POST /palmpay/request/create` — kiosk creates request, store in Redis (60s TTL), open WS channel
- [ ] FastAPI: WebSocket endpoint `/palmpay/request/{id}/stream` — kiosk subscribes
- [ ] FastAPI: Palm Service integration — after match, calls `/internal/palmpay/process`
- [ ] FastAPI: `POST /internal/palmpay/process` — full payment orchestration:
  - Retrieve user wallet
  - Check: frozen? balance sufficient? daily limit? per-txn limit? palm_pay enabled?
  - Atomic PostgreSQL transaction: debit sender, credit merchant, ledger entries, transaction record
  - Push result to WebSocket channel (success or failure with reason)
  - Send FCM push notification to customer
  - Expire payment request in Redis
- [ ] FastAPI: Idempotency key enforcement (unique constraint on transactions table)
- [ ] Kiosk client: Full payment flow (Section 10 code) working end-to-end
- [ ] Flutter: Scan tab screen — explains palm pay, shows nearest merchant (static for now)
- [ ] Flutter: Deep link handling — when app receives FCM with transaction data, show result screen
- [ ] Flutter: Scan Result Success screen — merchant, amount, timestamp, receipt button
- [ ] Flutter: Scan Result Failed screen — reason, retry info
- [ ] Flutter: Scan Result Low Balance screen — shortfall, top-up CTA

**Test:**
- Full flow: kiosk creates request → customer places palm → model matches → wallet debited → kiosk shows success → push notification received on phone
- Confidence 96.9%: rejected → kiosk shows "Please try again"
- Insufficient balance: rejected → kiosk shows shortfall → phone shows top-up CTA
- Same payment request sent twice (idempotency): second call returns first result, no double-debit
- Frozen wallet: scan succeeds biometrically but payment blocked

**End of Day 5 deliverable:** Complete palm payment working. This is your core product done.

---

### DAY 6 — TRANSACTION HISTORY & ANALYTICS
**Theme: User can see, search, filter, and export their full payment history**

**Tasks:**
- [ ] FastAPI: `GET /transactions` — paginated, filterable (type, date, amount range, search)
- [ ] FastAPI: `GET /transactions/{id}` — full detail
- [ ] FastAPI: `GET /transactions/{id}/receipt` — generate PDF receipt, return presigned S3 URL
- [ ] FastAPI: `GET /analytics/summary` — weekly/monthly aggregates
- [ ] FastAPI: `GET /analytics/categories` — merchant category breakdown
- [ ] Flutter: Transaction History screen — infinite scroll list, filter sheet, search
- [ ] Flutter: Transaction Detail screen — full receipt view, PDF share button
- [ ] Flutter: Spending Analytics screen — fl_chart bar chart (weekly/monthly), category pie chart
- [ ] Flutter: PDF receipt generation (pdf package) — formatted receipt with PalmPay branding
- [ ] Flutter: Share receipt — `printing` package for share sheet

**Test:**
- 100 transaction history loads and paginates correctly
- Filter by "palm pay only" shows only merchant payments
- Filter by date range returns correct results
- Download receipt → formatted PDF opens correctly
- Analytics show correct totals matching transaction list

**End of Day 6 deliverable:** Complete money management experience

---

### DAY 7 — PROFILE, SECURITY & NOTIFICATIONS
**Theme: User controls their identity, security, and preferences**

**Tasks:**
- [ ] FastAPI: `PUT /auth/me` — update name, photo
- [ ] FastAPI: `GET /palm/templates` — list enrolled hands
- [ ] FastAPI: `DELETE /palm/templates/{id}` — revoke template
- [ ] FastAPI: `PUT /wallet/limits` — update transaction limits
- [ ] FastAPI: `POST /wallet/freeze` / `POST /wallet/unfreeze`
- [ ] FastAPI: `GET /auth/devices` — all logged-in devices
- [ ] FastAPI: `DELETE /auth/devices/{id}` — remote logout device
- [ ] FastAPI: `PUT /notifications/preferences`
- [ ] Flutter: Profile screen — avatar upload, name edit, KYC status badge
- [ ] Flutter: Digital ID Card screen — card design with QR, download PDF
- [ ] Flutter: Palm Manager screen — enrolled hands, last scan date, revoke
- [ ] Flutter: Security Settings screen — limits config, sliders, toggles
- [ ] Flutter: Wallet Settings screen — freeze toggle, auto top-up
- [ ] Flutter: Device Manager screen — devices list, remote logout
- [ ] Flutter: Notification Settings screen — toggles per category
- [ ] Flutter: local_auth integration — fingerprint lock on app open
- [ ] Android: FLAG_SECURE on wallet/payment screens (prevent screenshots)

**Test:**
- Freeze wallet → palm pay attempt → blocked
- Unfreeze → requires OTP → unfreeze successful
- Remote logout device → that device's token invalidated → redirect to login
- Revoke palm template → scan at kiosk → "no match" correctly

**End of Day 7 deliverable:** Complete profile and security settings

---

### DAY 8 — POLISH, EDGE CASES & PERFORMANCE
**Theme: Make everything feel production-quality**

**Tasks:**
- [ ] All loading states: shimmer skeletons on every list/card (no raw spinners)
- [ ] All error states: specific, actionable messages (not "Something went wrong")
- [ ] Empty states: illustrated empty state for transaction history, no contacts
- [ ] Offline handling: Dio interceptor detects no connection, show offline banner
- [ ] Pull-to-refresh on all list screens
- [ ] Haptic feedback on button presses (HapticFeedback.lightImpact)
- [ ] Success animations: Lottie checkmark on payment complete, transfer complete
- [ ] Amount input: proper keyboard (numericWithDecimal), formatted live as user types
- [ ] All forms: proper TextInputAction chain (next → next → done)
- [ ] Keyboard avoidance: all scrollable screens handle keyboard correctly
- [ ] Deep link: FCM notification → tap → open correct screen with data
- [ ] App launch performance: < 2 seconds to wallet dashboard
- [ ] Backend: Add database indexes from Section 6
- [ ] Backend: Add response caching (Redis) for /wallet GET (1-second cache)
- [ ] Backend: Structured logging (JSON format) for all API requests
- [ ] Backend: Health check endpoint with DB + Redis status
- [ ] Run `flutter analyze` — fix all warnings
- [ ] Run backend on gunicorn with 4 workers, benchmark response times

**Test:**
- Cold launch timer: < 2 seconds
- Background → foreground: resumes instantly, data refreshes
- No internet: clear message shown, graceful degradation
- 50 rapid API calls: rate limiter triggers correctly

**End of Day 8 deliverable:** App feels polished and production-ready

---

### DAY 9 — TESTING, SECURITY AUDIT & BETA DEPLOYMENT
**Theme: Prove it works correctly and securely before anyone uses it**

**Tasks:**
- [ ] Write and run all unit tests (Section 15.1)
- [ ] Write and run all backend pytest tests (Section 15.4)
- [ ] Run OWASP checklist manually:
  - [ ] All inputs validated server-side
  - [ ] JWT algorithm hardcoded to HS256 (no "alg: none" attack)
  - [ ] Rate limiting tested
  - [ ] SQL injection: try `'; DROP TABLE users;--` in all text inputs
  - [ ] Certificate pinning: test with mitmproxy (should fail to intercept)
  - [ ] Root detection: test on rooted emulator
- [ ] Concurrent payment test: 2 kiosks scan same user simultaneously → only 1 payment processes
- [ ] Run Locust load test: 50 concurrent palm pays → all complete, no errors
- [ ] Deploy backend to production server (DigitalOcean Droplet or AWS EC2):
  - [ ] Set up Nginx reverse proxy
  - [ ] SSL certificate (Let's Encrypt / certbot)
  - [ ] Systemd service for FastAPI (auto-restart on crash)
  - [ ] PostgreSQL with daily automated backups
  - [ ] Redis with persistence enabled (RDB snapshot)
- [ ] Build release APK: `flutter build apk --release`
  - [ ] ProGuard enabled
  - [ ] Certificate pinning pointing to production server
  - [ ] All .env values pointing to production
- [ ] Install release APK on 3 different Android devices
- [ ] Complete full user journey on each device: register → enroll → add money → pay at kiosk → check history
- [ ] Set up Grafana dashboard: API latency, error rate, active wallets, transactions/minute

**End of Day 9 deliverable:** Deployed, tested, production-ready application

---

### DAY 10 — PLAY STORE SUBMISSION & CLOSED BETA LAUNCH
**Theme: Ship it**

**Tasks:**
- [ ] Create Google Play Developer account ($25 one-time fee)
- [ ] Generate upload keystore:
  ```bash
  keytool -genkey -v -keystore palmpay-upload.jks \
    -alias palmpay -keyalg RSA -keysize 2048 -validity 10000
  ```
  **BACK THIS UP IN 3 PLACES. LOSING IT = CANNOT UPDATE THE APP EVER.**
- [ ] Configure signing in android/app/build.gradle
- [ ] Build release AAB: `flutter build appbundle --release`
- [ ] Complete Play Store listing:
  - [ ] Upload AAB
  - [ ] App icon 512×512
  - [ ] Feature graphic 1024×500
  - [ ] 5 screenshots (from Day 8 polished app)
  - [ ] Privacy policy URL live
  - [ ] Content rating questionnaire
  - [ ] Financial app declaration
- [ ] Submit to **Internal Testing** track first (instant approval)
- [ ] Install from Play Store on 5 devices — full flow test
- [ ] Invite 20 closed beta testers (merchants, friends, family)
- [ ] Create closed testing track → add testers by email → submit
- [ ] Set up crash reporting dashboard (Sentry)
- [ ] Set up monitoring alerts (Grafana — alert if error rate > 1%)
- [ ] Write v1.0 release notes
- [ ] Document known issues / limitations for V1.1 backlog
- [ ] Celebrate 🎉

**End of Day 10 deliverable:** App live on Play Store internal/closed testing with real users

---

## 18. RISK REGISTER

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| JazzCash API approval takes >1 week | High | High | Use JazzCash sandbox first, build UI/backend regardless; real integration added once approved |
| NADRA VERISYS not accessible | Medium | Medium | Manual KYC review queue as fallback; CNIC captured but not verified automatically |
| Palm model inference > 800ms | Low | Medium | Profile model, optimize (ONNX export, quantization); worst case: show "processing" animation |
| SBP compliance blocks real transactions | High | High | Beta launch with closed testing (play money only); real money needs EMI license or JazzCash partnership |
| Google Play rejects app | Medium | Medium | Submit 2 weeks before deadline; address any compliance issues immediately |
| Kiosk NIR camera hardware varies | Medium | Medium | Test with your specific hardware; document supported models |
| DB connection pool exhausted under load | Low | High | Configure pgbouncer; set pool_size=20, max_overflow=10 per service |
| Push notifications delayed | Low | Medium | FCM is reliable; have in-app balance refresh as secondary indicator |
| User loses phone (tokens at risk) | Medium | Low | All tokens invalidatable remotely; wallet requires OTP to unfreeze |

---

## 19. POST-LAUNCH ROADMAP

### V1.1 (2 weeks post-launch)
- Bug fixes from beta feedback
- Urdu language support
- Bill payments (PTCL, electricity)
- QR code receive payment (for users without kiosk access)

### V1.2 (1 month post-launch)
- Merchant app (separate Flutter app for merchant management)
- Merchant dashboard web portal
- Cashback / loyalty points system
- Referral program

### V2.0 (3 months post-launch)
- Metro transit module
- Spending categories auto-detection (ML-based)
- Savings wallet (interest-bearing, Islamic finance compliant)
- International remittance (UAE → Pakistan)

### V3.0 (6 months post-launch)
- iOS app
- University attendance module
- Employee attendance module
- NADRA identity verification (government partnership)
- Open API for third-party service integration

---

## APPENDIX A — Environment Variables

```bash
# .env (never commit to git)

# Server
SECRET_KEY=your-256-bit-random-secret
ENVIRONMENT=production
DEBUG=false
ALLOWED_ORIGINS=https://palmpay.pk

# Database
DATABASE_URL=postgresql://palmpay_user:password@localhost:5432/palmpay_db
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET=your-jwt-secret-different-from-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# AWS
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-south-1
S3_BUCKET_TEMPLATES=palmpay-templates-prod
S3_BUCKET_RECEIPTS=palmpay-receipts-prod
KMS_KEY_ID=...

# JazzCash
JAZZCASH_MERCHANT_ID=...
JAZZCASH_PASSWORD=...
JAZZCASH_INTEGRITY_SALT=...
JAZZCASH_SANDBOX=false

# Firebase
FIREBASE_SERVICE_ACCOUNT_PATH=/etc/palmpay/firebase-service-account.json

# Twilio
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=+1...

# Sentry
SENTRY_DSN=https://...@sentry.io/...

# Palm Model
PALM_CONFIDENCE_THRESHOLD=0.97
PALM_LIVENESS_THRESHOLD=0.85
PALM_MODEL_PATH=/models/palm_vein_v1.pkl
```

## APPENDIX B — Commands Reference

```bash
# Flutter
flutter create palmpay --org pk.palmpay
flutter pub get
flutter run --debug
flutter build apk --release
flutter build appbundle --release
flutter test
flutter analyze

# Backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
pytest tests/ -v --cov=app --cov-report=html
locust -f tests/load_test.py --host https://api.palmpay.pk

# Keystore
keytool -genkey -v -keystore palmpay-upload.jks -alias palmpay -keyalg RSA -keysize 2048 -validity 10000
keytool -list -v -keystore palmpay-upload.jks

# Server
certbot --nginx -d api.palmpay.pk
systemctl restart palmpay-api
journalctl -u palmpay-api -f
pg_dump palmpay_db > backup_$(date +%Y%m%d).sql
```

---

*Document version: 1.0*
*Last updated: June 2026*
*Author: Project Architecture Plan — PalmPay V1*
*Status: Ready for development*
