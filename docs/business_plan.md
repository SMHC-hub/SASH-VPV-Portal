# SASH-VPV Palm Vein Biometric Platform — Business Plan

**Product:** Secure Authentication via Subcutaneous Vascular Palm-Veins (SASH-VPV)  
**Institution:** National University of Technology (NUTECH), Islamabad  
**Market:** Pakistan — metro transit, banking, fintech, BPO, corporate, co-working, and adjacent sectors  
**Document purpose:** Strategic roadmap for commercialization, NADRA alignment, and sector-by-sector deployment

---

## 1. Executive Summary

SASH-VPV is a contactless palm vein recognition platform built on the XRTECH MagicVein Plus NIR scanner, a custom-trained neural matcher (EfficientNet-B0 + CBAM, 512-d embeddings), and a full-stack admin/member portal. The system already supports live enrollment, 1:1 verification, 1:N identification, audit logging, and role-based access.

**Commercial thesis:** Palm vein biometrics are more hygienic, harder to spoof, and more privacy-preserving than fingerprints — especially relevant in Pakistan where fingerprint systems face wear-and-tear issues (manual labor, aging skin, dry climate) and public hygiene concerns post-COVID.

**Primary opportunities:**
1. **Metro / mass transit ticketing** — mobile transit app with prepaid wallet; palm scan at any gate auto-deducts fare
2. **NADRA-aligned digital identity** — national ID verification layer for high-trust services
3. **Enterprise access & workforce** — banks, fintech, BPOs, corporate offices, co-working spaces (web admin portal)

**Recommended positioning:** *"Pakistan's contactless vein identity layer — more authentic than fingerprint, built for high-throughput public and financial environments."*

---

## 2. Problem Statement (Pakistan Market)

| Pain point | Fingerprint limitation | Palm vein advantage |
|---|---|---|
| Worn/damaged prints (field workers, elderly) | High false-reject rate | Vein pattern is internal; skin surface condition matters less |
| Hygiene in public/shared devices | Contact required | Contactless (3–8 cm hover) |
| Spoofing (latent prints, molds) | Easier to lift/replay | Liveness via NIR + subdermal pattern |
| Religious/cultural touch aversion | Physical contact | No touch |
| High-throughput gates (metro, offices) | Slower, needs cleaning | Faster flow, no residue |
| Data sensitivity | Fingerprint widely leaked in legacy DBs | Vein templates harder to reverse-engineer; different regulatory narrative |

Pakistan's digital identity stack (CNIC, SIM verification, Raast, branchless banking) is mature at the **document/number** level but weak at **continuous physical authentication** in daily high-volume settings. SASH-VPV fills the gap between *"prove once at onboarding"* and *"authenticate every day at speed."*

---

## 3. Product Foundation (What You Have Today)

| Layer | Capability | Business relevance |
|---|---|---|
| Hardware | XRTECH MagicVein Plus, 480×640 NIR, USB | Deployable gate scanner / kiosk module |
| SDK + capture | Live MJPEG stream, distance sensing, auto-heal | Operator-friendly; reduces downtime |
| AI matcher | SASH-VPV embedder, cosine similarity, quality gates | Custom IP; not vendor-locked to SDK match only |
| Web portal | Admin, member, employee roles; enrollment; logs | Enterprise / BPO / corporate deployments |
| **Transit mobile app** | Passenger wallet, top-up, trip history, palm-linked account | **Primary commuter interface for metro/BRT** |
| Dataset | 2,667 images, 122 subjects (SASH-VPV corpus) | Research credibility; retrain path for local demographics |
| Security | JWT auth, template storage, audit trails | Baseline for SOC/compliance conversations |

**Gap to production (honest):** Scale testing on Pakistani demographics, PAD (presentation attack detection) certification, offline edge deployment, and formal NADRA API integration are roadmap items — not blockers for pilots.

---

## 4. Strategic Pillars

### Pillar A — Transit (Metro Ticketing via Mobile App)
**Vision:** Palm-in, ride — no card, no physical ticket. Passengers use a **dedicated mobile transit app** (iOS/Android), not a web portal, for everything except the scan at the gate.

**Passenger mobile app (core product for transit):**
- **Account & identity:** Sign up with CNIC + mobile → enroll palm (at station kiosk or partner center) → palm template linked to transit account
- **Wallet / balance:** Load balance via JazzCash, Easypaisa, Raast, debit card, or bank transfer
- **Auto fare deduction:** When passenger scans palm at **any** metro/BRT gate, the system:
  1. Identifies the user (1:N match at gate)
  2. Calculates fare (origin–destination or flat rate, per transit authority rules)
  3. **Automatically deducts** the fare from in-app balance
  4. Opens the gate and logs the trip in the app (timestamp, station, fare, remaining balance)
- **Trip history & receipts:** Full ride log, low-balance alerts, instant top-up push notifications
- **No phone at gate:** Passenger does **not** need to open the app to travel — palm alone triggers payment; the app is for wallet management and history

**Gate / backend flow:**
- **Gate hardware:** Palm vein scanner + turnstile at each entry/exit; 1:N identify in <1 s (GPU) or <3 s (CPU pilot)
- **Fare engine:** Central backend computes fare by entry/exit pair (or zone-based); rejects travel if balance insufficient
- **Interoperability:** One palm account works across all gates on the network — travel anywhere on the line/city without separate tickets
- **Fallback:** QR one-time ticket or NFC card if match fails or balance is zero

**Why mobile app instead of web for transit:**
- Push notifications (low balance, promo fares)
- Native payment SDK integration (easier top-up)
- Offline ticket cache / last-known balance view
- Higher daily engagement vs browser bookmark
- App Store presence = consumer trust for a public-facing product

**Metro engagement path:**
1. Launch transit app beta + pilot 2 gates at one station (e.g., Orange Line Lahore, Islamabad Metro, or Peshawar BRT)
2. Measure: top-up conversion, auto-deduction success rate, throughput (passengers/hour), false accept/reject
3. Expand to full station → line-wide → city-wide; single wallet valid on entire network

**Revenue:** Per-transaction fee (% of fare), mobile wallet float interest (where permitted), annual station license, hardware lease, transit authority integration contract, in-app promotions.

---

### Pillar B — NADRA Collaboration
**Vision:** Palm vein as a **secondary biometric factor** bound to CNIC identity — not a replacement for NADRA's core systems, but an accelerator for private-sector trust.

**Why NADRA would care:**
- Reduces synthetic identity fraud in banking/fintech onboarding
- Contactless alternative where fingerprint quality is poor
- Aligns with Pakistan's digital public infrastructure narrative

**Collaboration models (pick one to start):**

| Model | Description | Your role | NADRA role |
|---|---|---|---|
| **Verification API** | Merchant sends CNIC + live palm → NADRA returns match/no-match | Build capture SDK + relay | Identity authority, legal framework |
| **Delegated enrollment** | NADRA-certified centers enroll vein templates linked to CNIC | Operate enrollment kiosks | Certify process, hold golden record |
| **Private template, public key** | Vein template stored by you; NADRA holds hash/reference only | Template vault + HSM | Audit + dispute resolution |
| **Pilot MOU** | University/industry pilot under NUTECH + NADRA innovation channel | Research + prototype | Sandbox approval, data governance |

**Practical first step:** Propose a **sandbox pilot** — 500–1,000 volunteers, CNIC-verified enrollment, independent evaluation report (EER, FAR, FRR on local population). NADRA responds to evidence, not slides.

**Compliance talking points:**
- Templates are mathematical embeddings, not images
- No palm image stored post-enrollment (configurable)
- Audit logs for every match attempt
- Data residency in Pakistan

---

### Pillar C — Financial Services (Banks & Fintech)
**Vision:** Palm-based step-up authentication for high-risk actions.

**Use cases:**
- Branch login / privileged teller actions
- Fintech app: transfer above threshold, device re-bind, password reset
- ATM cardless withdrawal (palm + PIN)
- Merchant POS verification for high-value transactions

**Approach:**
1. **SDK/API integration** — banks embed your capture widget; your cloud matches against enrolled template
2. **On-prem appliance** — box at bank DC for air-gapped matching (regulatory preference)
3. **Co-brand with 1Link / Raast** — position as biometric step-up in payment rails

**Why banks switch from fingerprint:**
- Lower false rejects → fewer branch visits
- Better fraud story for SBP inspections
- Premium "vein secure" tier for corporate banking clients

**Revenue:** Per-seat license, per-transaction auth fee, annual support, hardware bundle.

---

### Pillar D — BPO & Corporate Offices
**Vision:** Shift attendance, secure floor access, and clean-desk policy compliance — one palm scan.

**Use cases:**
- Time & attendance (replace fingerprint machines)
- Data-center / server room access
- Hot-desk booking verification in co-working spaces
- Visitor management: pre-enroll palm + CNIC for recurring contractors

**Approach:**
- **Turnkey kiosk:** Scanner + your portal (employee panel already exists)
- **HRIS integration:** Export attendance to SAP, Oracle, local HR tools via API
- **Multi-tenant SaaS:** One platform, many companies (co-working operators love this)

**Revenue:** Per-employee/month, per-site license, setup fee.

---

### Pillar E — Co-working & Shared Spaces
**Vision:** Members scan palm at door; billing and access auto-sync.

**Approach:**
- Integrate with access control (HID, ZKTeco, Hikvision) via relay/API
- Member app: enroll once, use any location in network
- Day-pass: CNIC verify + single-palm enroll at front desk

**Revenue:** White-label for operators (Regus-style, local brands), rev-share on membership.

---

## 5. Sector Expansion Map

| Sector | Entry use case | Expansion | Sales cycle |
|---|---|---|---|
| Metro / BRT | Mobile app + gate pilot | City-wide palm wallet network | 12–24 months |
| Banks | Branch pilot | API + ATM | 9–18 months |
| Fintech | Step-up auth | Platform SDK | 3–6 months |
| BPO | Attendance | Full access control | 3–6 months |
| Corporate | Single HQ | Multi-site | 6–12 months |
| Co-working | One location | Chain rollout | 1–3 months |
| Healthcare | Staff access | Patient check-in | 12+ months |
| Education | Campus attendance | Exam hall identity | 6–12 months |
| Government offices | Citizen service queue | e-gov kiosk | 18+ months |

**Fastest revenue:** BPO, co-working, fintech (short cycles, less procurement).  
**Highest impact:** Metro + NADRA (credibility + scale).  
**Highest margin:** Bank on-prem appliance + support.

---

## 6. Go-to-Market Strategy

### Phase 1 — Proof (Months 1–3)
- Fix production deployment (GPU inference, gate hardware enclosure)
- **Transit mobile app MVP:** wallet, top-up, trip history, palm enrollment flow
- Run public demo at NUTECH + 1 corporate partner
- Publish Pakistan-specific accuracy benchmark (new local captures)
- File provisional patent / copyright on SASH-VPV pipeline

### Phase 2 — Pilots (Months 4–9)
- **Transit:** mobile app live + 1 metro station gate pilot (auto fare deduction)
- OR 1 bank branch OR 3 BPO sites (pick two, not all three)
- NADRA sandbox MOU application
- Hire 1 enterprise sales + 1 integration engineer + 1 mobile developer

### Phase 3 — Scale (Months 10–18)
- SaaS multi-tenant portal
- Certified enrollment partners
- Channel partners (access control vendors, POS integrators)

### Messaging by audience

| Audience | Lead message |
|---|---|
| Transit authority | Mobile wallet + auto fare deduction; throughput + fare evasion reduction |
| Commuter (B2C) | Load once, travel anywhere — just show your palm |
| NADRA | Fraud reduction + contactless national identity layer |
| Bank CISO | Spoof resistance + audit trail + SBP alignment |
| Fintech founder | Drop-in SDK, faster than building in-house |
| BPO HR | Zero-touch attendance, no fingerprint maintenance |
| Co-working ops | Premium member experience, one scan |

---

## 7. Revenue Models

| Model | Example pricing (PKR, indicative) | Best for |
|---|---|---|
| Mobile wallet float | Revenue share on idle balance | Transit app |
| Per-transaction (% of fare) | 1–3% per ride | Metro, BRT |
| SaaS per user/month | 150–500 / user / month | BPO, corporate, co-working |
| Site license (annual) | 500K–5M / site | Bank branch, metro station |
| Hardware + software bundle | 80K–200K per kiosk | Turnkey gates |
| Integration project | 1M–10M one-time | Enterprise, government |
| NADRA/certification services | Custom | National programs |

**Target Year 1 (conservative):** 3 paid pilots + 2 recurring BPO/co-working contracts → fund Phase 2.

---

## 8. Technical Deployment Strategies

### Strategy 1 — Cloud API (fastest)
- Your FastAPI backend on Azure Pakistan / local DC
- Clients call REST: enroll, verify, identify
- Pros: fast integration; Cons: latency, data residency concerns

### Strategy 2 — On-prem edge box
- Mini PC + scanner at each site; sync gallery nightly
- Pros: bank/gov friendly; Cons: ops overhead

### Strategy 3 — Hybrid (recommended for metro)
- **Mobile app + cloud:** Wallet, top-up, and account management in transit app; palm templates and balance in central DC
- **Edge at gate:** 1:N match locally for speed; fare deduct API call to central wallet service
- Best for metro: central account, local gate speed, auto deduction on every scan

### Strategy 4 — Mobile transit app + fixed enrollment kiosk
- **Enrollment:** Fixed station kiosk (quality-controlled palm capture) or partner center
- **Travel:** Palm scan only at gate — no phone needed; fare auto-deducted from app wallet
- **Management:** Passenger uses mobile app for balance, history, and top-up only

**Hardware BOM (per gate/kiosk, indicative):**
- XRTECH scanner: vendor quote
- Industrial mini PC (GPU optional): 80K–250K PKR
- Enclosure + mount: 30K–80K PKR
- Networking + UPS: 20K–50K PKR

---

## 9. NADRA & Regulatory Roadmap

1. **Legal review** — Personal Data Protection Bill alignment; consent flows for biometric collection
2. **Biometric policy** — Document template format, retention, right to erasure
3. **NADRA engagement** — Innovation cell / MOU for pilot; never claim "NADRA approved" without written consent
4. **SBP (banks)** — Biometric authentication guidelines for digital banking
5. **PTA** — If SIM re-verification angle is pursued, separate track
6. **Certification path** — ISO/IEC 30107 (PAD), ISO 19794 (biometric data interchange) as long-term goals

---

## 10. Competitive Positioning vs Fingerprint

**Sell these five facts:**
1. **Internal pattern** — veins are subdermal; harder to copy than surface prints
2. **Contactless** — faster lines, better hygiene, culturally easier
3. **Lower maintenance** — no optical platen cleaning; fewer "finger not recognized" support tickets
4. **Dual-hand enrollment** — your system already supports Left/Right templates per identity
5. **Custom AI** — SASH-VPV model is yours; not dependent on vendor black-box matching alone

**Objection handling:**
- *"Fingerprint is cheaper"* → TCO: support calls + cleaning + false rejects often exceed hardware savings
- *"We already have NADRA fingerprint"* → Position as **complement** for daily auth, not CNIC replacement
- *"Is it proven?"* → Cite NUTECH dataset, pilot metrics, international vein literature (Fujitsu, Hitachi deployments in Asia)

---

## 11. Partnership Strategy

| Partner type | Target examples | Value exchange |
|---|---|---|
| Scanner OEM | XRTECH / local distributor | Volume pricing, co-marketing |
| Access control | ZKTeco, Hikvision integrators | Your AI + their locks |
| Payments | 1Link, JazzCash, Easypaisa | Transit app top-up + wallet rails |
| System integrators | TRG, NetSol, local SIs | They sell, you deliver API |
| Universities | NUTECH, NUST, COMSATS | Talent + research credibility |
| Government | NADRA, transit authorities | Pilots + policy alignment |

---

## 12. 18-Month Roadmap

| Quarter | Milestone |
|---|---|
| Q1 | Production hardening; transit mobile app MVP; 2 corporate pilots; NADRA sandbox proposal |
| Q2 | Metro station pilot (palm + auto fare deduction); publish local accuracy whitepaper |
| Q3 | Multi-tenant SaaS; 5 paying sites; channel partner signed |
| Q4 | NADRA pilot results; scale first vertical; seek seed/grant funding |
| Q5–Q6 | Second city / second bank; on-prem appliance SKU; team of 8–12 |

---

## 13. Team & Funding

**Core team needed:**
- CEO / business development (gov + bank + transit relationships)
- CTO (platform + security)
- **Mobile developer** (transit app — iOS/Android)
- ML engineer (retrain, PAD)
- Integration engineer (payment APIs, transit fare engine, access control)
- Field ops (gate install, support)

**Funding sources:**
- HEC / Ignite / NCAI grants
- NUTECH incubation
- Angel (fintech founders)
- Strategic (access control vendor)
- Revenue from pilots (preferred — proves market)

---

## 14. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| NADRA timeline slow | Run commercial pilots without NADRA badge; add later |
| Hardware supply | Lock distributor agreement; keep 30-day spare stock |
| False match in wild | Quality gates (already built); human fallback; threshold tuning per sector |
| Privacy backlash | Consent-first enrollment; no image retention option; local hosting |
| Incumbent fingerprint vendors | Integrate alongside; sell upgrade path |
| GPU cost at gates | Edge TPU / model distillation; 1:N cache per station |

---

## 15. Immediate Action List (Next 30 Days)

1. Package a **10-slide pilot deck** (metro mobile app + bank versions)
2. Record a **2-minute demo video** — app top-up → palm scan at gate → auto fare deduction → trip in app
3. Write **NADRA sandbox proposal** (1 page problem, 1 page method, 1 page ask)
4. Contact **1 BPO + 1 co-working space** in Islamabad/Rawalpindi for free 30-day pilot
5. Add **GPU inference** to production backend for gate-speed matching
6. Register **business entity** (SMC / Pvt Ltd) and open business bank account
7. Define **pilot SLA**: uptime, match latency, support response

---

## 16. Success Metrics (KPIs)

| KPI | Pilot target | Production target |
|---|---|---|
| Wallet top-up success rate | > 95% | > 99% |
| Auto fare deduction success | > 98% | > 99.5% |
| False Accept Rate (FAR) | < 0.1% | < 0.01% |
| False Reject Rate (FRR) | < 5% | < 2% |
| Match latency | < 3 s | < 1 s |
| Enrollment time | < 90 s | < 60 s |
| Gate throughput | 20/min | 40+/min |
| Uptime | 99% | 99.9% |
| User satisfaction (NPS) | > 40 | > 60 |

---

## 17. One-Line Pitch

**"SASH-VPV is Pakistan's contactless palm vein platform — load balance in the transit app, scan your palm anywhere, and fare deducts automatically. More reliable than fingerprint, with a clear path to NADRA-aligned national trust."**

---

*Document version: 1.1 — transit channel is mobile app (wallet + auto fare deduction); web portal retained for enterprise/admin. Aligned with SASH-VPV codebase. Update quarterly as pilots produce real metrics.*
