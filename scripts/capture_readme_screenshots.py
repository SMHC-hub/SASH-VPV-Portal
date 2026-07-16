"""Capture VeinPay / SASH-VPV portal screenshots for README documentation."""
from __future__ import annotations

import re
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

BASE = "http://127.0.0.1:5173"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
VIEWPORT = {"width": 1440, "height": 900}
PWD = "VeinPayDemo1!"

ACCOUNTS = {
    "admin": "saudakbar65367@gmail.com",
    "employee": "ameerkhanf22@nutech.edu.pk",
    "owner": "demo-shop@example.com",
    "customer": "cart.test@veinpay.local",
}


def shot(page: Page, folder: str, name: str, full_page: bool = False) -> Path:
    dest = OUT / folder
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / f"{name}.png"
    page.wait_for_timeout(450)
    page.screenshot(path=str(path), full_page=full_page)
    print(f"  ✓ {folder}/{name}.png")
    return path


def clear_storage(page: Page) -> None:
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.evaluate(
        """() => {
      try { localStorage.clear(); sessionStorage.clear(); } catch (e) {}
    }"""
    )
    page.context.clear_cookies()


def fill_login(page: Page, email_sel: str, pass_sel: str, email: str, password: str) -> None:
    page.fill(email_sel, email)
    page.fill(pass_sel, password)


def click_signin(page: Page) -> None:
    btn = page.get_by_role("button", name=re.compile(r"(sign\s*in|log\s*in|continue)", re.I))
    if btn.count():
        btn.first.click()
    else:
        page.locator('button[type="submit"]').first.click()


def login_admin(page: Page) -> None:
    clear_storage(page)
    page.goto(BASE + "/login", wait_until="networkidle")
    fill_login(page, "#login-email", "#login-password", ACCOUNTS["admin"], PWD)
    click_signin(page)
    page.wait_for_url("**/dashboard**", timeout=20000)


def login_employee(page: Page) -> None:
    clear_storage(page)
    page.goto(BASE + "/employee/login", wait_until="networkidle")
    email_tab = page.get_by_role("button", name=re.compile(r"^email$", re.I))
    if email_tab.count():
        email_tab.first.click()
    fill_login(page, "#emp-email", "#emp-password", ACCOUNTS["employee"], PWD)
    click_signin(page)
    page.wait_for_url("**/employee/**", timeout=20000)


def login_owner(page: Page) -> None:
    clear_storage(page)
    page.goto(BASE + "/owner/login", wait_until="networkidle")
    fill_login(page, "#email", "#password", ACCOUNTS["owner"], PWD)
    click_signin(page)
    page.wait_for_url("**/owner/**", timeout=20000)


def login_customer(page: Page) -> None:
    clear_storage(page)
    page.goto(BASE + "/user/login", wait_until="networkidle")
    page.locator('input[type="email"]').first.fill(ACCOUNTS["customer"])
    page.locator('input[type="password"]').first.fill(PWD)
    click_signin(page)
    page.wait_for_timeout(2500)


def capture_auth(page: Page) -> None:
    print("\n== Auth / Login & Signup ==")
    clear_storage(page)
    routes = [
        ("01-admin-login", "/login"),
        ("02-admin-signup", "/signup"),
        ("03-member-login", "/user/login"),
        ("04-member-signup", "/user/signup"),
        ("05-employee-login", "/employee/login"),
        ("06-employee-signup", "/employee/signup"),
        ("07-owner-login", "/owner/login"),
        ("08-kiosk", "/kiosk"),
        ("09-kiosk-enroll", "/kiosk/enroll"),
    ]
    for name, path in routes:
        page.goto(BASE + path, wait_until="networkidle")
        shot(page, "auth", name)

    # Extra auth UI states
    page.goto(BASE + "/employee/login", wait_until="networkidle")
    palm = page.get_by_role("button", name=re.compile(r"^palm$", re.I))
    if palm.count():
        palm.first.click()
        shot(page, "auth", "10-employee-login-palm-tab")
    page.goto(BASE + "/user/login", wait_until="networkidle")
    shot(page, "auth", "11-member-login-full", full_page=True)


def capture_customer(page: Page) -> None:
    print("\n== Customer Panel (marketing) ==")
    clear_storage(page)
    pages = [
        ("01-home-hero", "/"),
        ("02-technology", "/technology"),
        ("03-how-it-works", "/how-it-works"),
        ("04-security", "/security"),
        ("05-solutions", "/solutions"),
        ("06-contact", "/contact"),
    ]
    for name, path in pages:
        page.goto(BASE + path, wait_until="networkidle")
        shot(page, "customer", name)
        shot(page, "customer", f"{name}-full", full_page=True)

    page.goto(BASE + "/", wait_until="networkidle")
    page.evaluate("window.scrollTo(0, 700)")
    shot(page, "customer", "07-home-pipeline")
    page.evaluate("window.scrollTo(0, 1400)")
    shot(page, "customer", "08-home-features")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    shot(page, "customer", "09-home-footer")
    # Mid scroll for CTAs
    page.evaluate("window.scrollTo(0, 400)")
    shot(page, "customer", "10-home-mid-cta")


def capture_dataset(page: Page) -> None:
    print("\n== SASH-VPV Dataset (Customer home) ==")
    clear_storage(page)
    page.goto(BASE + "/", wait_until="networkidle")
    # Scroll dataset section into view
    page.evaluate(
        """() => {
      const el = [...document.querySelectorAll('section,h2,h3')].find(e =>
        (e.textContent||'').toLowerCase().includes('sash') ||
        (e.textContent||'').toLowerCase().includes('dataset') ||
        (e.textContent||'').toLowerCase().includes('kaggle')
      );
      if (el) el.scrollIntoView({behavior:'instant', block:'center'});
    }"""
    )
    page.wait_for_timeout(600)
    shot(page, "dataset", "01-dataset-section")
    shot(page, "dataset", "02-dataset-section-wide")
    page.evaluate("window.scrollBy(0, -180)")
    shot(page, "dataset", "03-dataset-with-context-above")
    page.evaluate("window.scrollBy(0, 360)")
    shot(page, "dataset", "04-dataset-with-context-below")
    # Capture several offsets around the section
    for i, y in enumerate([900, 1100, 1300, 1500, 1700, 1900], start=5):
        page.evaluate(f"window.scrollTo(0, {y})")
        shot(page, "dataset", f"{i:02d}-dataset-scroll-{y}")


def capture_admin(page: Page) -> None:
    print("\n== Admin Panel ==")
    login_admin(page)
    routes = [
        ("01-dashboard", "/dashboard"),
        ("02-enroll", "/enroll"),
        ("03-recognize", "/recognize"),
        ("04-identities", "/identities"),
        ("05-employees", "/employees"),
        ("06-customers", "/customers"),
        ("07-marketplace", "/marketplace"),
        ("08-logs", "/logs"),
        ("09-settings", "/settings"),
    ]
    for name, path in routes:
        page.goto(BASE + path, wait_until="networkidle")
        shot(page, "admin", name)
        shot(page, "admin", f"{name}-full", full_page=True)

    # Extra: recognition tabs if present
    page.goto(BASE + "/recognize", wait_until="networkidle")
    identify = page.get_by_role("tab", name=re.compile(r"identify", re.I))
    if identify.count() == 0:
        identify = page.get_by_role("button", name=re.compile(r"identify", re.I))
    if identify.count():
        identify.first.click()
        shot(page, "admin", "10-recognize-identify-tab")
    verify = page.get_by_role("tab", name=re.compile(r"verify", re.I))
    if verify.count() == 0:
        verify = page.get_by_role("button", name=re.compile(r"verify", re.I))
    if verify.count():
        verify.first.click()
        shot(page, "admin", "11-recognize-verify-tab")


def capture_employee(page: Page) -> None:
    print("\n== Employee Panel ==")
    login_employee(page)
    routes = [
        ("01-dashboard", "/employee/dashboard"),
        ("02-attendance", "/employee/attendance"),
        ("03-activity", "/employee/activity"),
        ("04-settings", "/employee/settings"),
    ]
    for name, path in routes:
        page.goto(BASE + path, wait_until="networkidle")
        shot(page, "employee", name)
        shot(page, "employee", f"{name}-full", full_page=True)
        page.evaluate("window.scrollTo(0, 500)")
        shot(page, "employee", f"{name}-scrolled")


def capture_owner(page: Page) -> None:
    print("\n== Shop Owner Panel ==")
    login_owner(page)
    routes = [
        ("01-dashboard", "/owner/dashboard"),
        ("02-products", "/owner/products"),
        ("03-shop", "/owner/shop"),
        ("04-settings", "/owner/settings"),
    ]
    for name, path in routes:
        page.goto(BASE + path, wait_until="networkidle")
        shot(page, "owner", name)
        shot(page, "owner", f"{name}-full", full_page=True)
        page.evaluate("window.scrollTo(0, 450)")
        shot(page, "owner", f"{name}-scrolled")


def capture_shop(page: Page) -> None:
    print("\n== Shop Tab ==")
    clear_storage(page)
    page.goto(BASE + "/member/shop", wait_until="networkidle")
    shot(page, "shop", "01-shop-catalog")
    shot(page, "shop", "02-shop-catalog-full", full_page=True)
    page.evaluate("window.scrollTo(0, 500)")
    shot(page, "shop", "03-shop-mid-scroll")
    page.evaluate("window.scrollTo(0, 1000)")
    shot(page, "shop", "04-shop-lower-scroll")
    page.evaluate("window.scrollTo(0, 1500)")
    shot(page, "shop", "05-shop-deep-scroll")

    for i, label in enumerate(["Electronics", "Clothing", "Food", "All", "Groceries"], start=6):
        btn = page.get_by_role("button", name=re.compile(label, re.I))
        if btn.count() == 0:
            btn = page.get_by_text(re.compile(label, re.I))
        if btn.count():
            try:
                btn.first.click(timeout=2000)
                page.wait_for_timeout(500)
                shot(page, "shop", f"{i:02d}-shop-filter-{label.lower().replace(' ', '-')}")
            except Exception:
                pass

    # Product detail pages
    links = page.locator('a[href*="/member/shop/"]')
    count = min(links.count(), 6)
    for i in range(count):
        href = links.nth(i).get_attribute("href") or ""
        if href.rstrip("/").endswith("/member/shop"):
            continue
        page.goto(BASE + href if href.startswith("/") else href, wait_until="networkidle")
        shot(page, "shop", f"{10+i:02d}-product-detail")
        shot(page, "shop", f"{10+i:02d}-product-detail-full", full_page=True)


def capture_cart(page: Page) -> None:
    print("\n== Cart & Payment ==")
    login_customer(page)
    page.goto(BASE + "/member/shop", wait_until="networkidle")
    shot(page, "cart", "01-shop-before-add")

    add_buttons = page.get_by_role("button", name=re.compile(r"add.*cart|add to cart", re.I))
    if add_buttons.count() == 0:
        add_buttons = page.get_by_role("button", name=re.compile(r"^(add|buy|\+)$", re.I))
    added = 0
    for i in range(min(add_buttons.count(), 5)):
        try:
            add_buttons.nth(i).click(timeout=2000)
            page.wait_for_timeout(400)
            added += 1
            shot(page, "cart", f"{2+i:02d}-after-add-{added}")
        except Exception:
            break

    if added == 0:
        link = page.locator('a[href*="/member/shop/"]').first
        if link.count():
            link.click()
            page.wait_for_load_state("networkidle")
            shot(page, "cart", "02-product-before-add")
            btn = page.get_by_role("button", name=re.compile(r"add|cart", re.I))
            if btn.count():
                btn.first.click()
                page.wait_for_timeout(600)
                shot(page, "cart", "03-product-after-add")

    page.goto(BASE + "/member/cart", wait_until="networkidle")
    shot(page, "cart", "08-cart-page")
    shot(page, "cart", "09-cart-page-full", full_page=True)
    page.evaluate("window.scrollTo(0, 400)")
    shot(page, "cart", "10-cart-scrolled")

    checkout = page.get_by_role("link", name=re.compile(r"checkout|pay", re.I))
    if checkout.count() == 0:
        checkout = page.get_by_role("button", name=re.compile(r"checkout|pay", re.I))
    if checkout.count():
        checkout.first.click()
        page.wait_for_timeout(1500)
        shot(page, "cart", "11-checkout")
        shot(page, "cart", "12-checkout-full", full_page=True)
        page.evaluate("window.scrollTo(0, 500)")
        shot(page, "cart", "13-checkout-scrolled")
        palm = page.get_by_text(re.compile(r"palm", re.I))
        if palm.count():
            palm.first.scroll_into_view_if_needed()
            shot(page, "cart", "14-checkout-palm-pay")
    else:
        page.goto(BASE + "/member/checkout", wait_until="networkidle")
        shot(page, "cart", "11-checkout-direct")
        shot(page, "cart", "12-checkout-direct-full", full_page=True)

    page.goto(BASE + "/member/enrollment", wait_until="networkidle")
    shot(page, "cart", "15-member-enrollment")
    page.goto(BASE + "/member/recognition", wait_until="networkidle")
    shot(page, "cart", "16-member-recognition")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])
        context = browser.new_context(viewport=VIEWPORT, device_scale_factor=1)
        page = context.new_page()
        page.set_default_timeout(25000)

        page.goto(BASE + "/", wait_until="networkidle")
        shot(page, "customer", "00-browser-open-home")

        steps = [
            ("auth", capture_auth),
            ("customer", capture_customer),
            ("dataset", capture_dataset),
            ("admin", capture_admin),
            ("employee", capture_employee),
            ("owner", capture_owner),
            ("shop", capture_shop),
            ("cart", capture_cart),
        ]
        for label, fn in steps:
            try:
                fn(page)
            except Exception as exc:
                print(f"!! {label} capture failed: {exc}")
                try:
                    shot(page, label, "zz-error-state")
                except Exception:
                    pass

        page.goto(BASE + "/", wait_until="domcontentloaded")
        time.sleep(2)
        browser.close()

    print("\nScreenshot counts:")
    for folder in sorted(OUT.iterdir()):
        if folder.is_dir():
            n = len(list(folder.glob("*.png")))
            print(f"  {folder.name}: {n}")


if __name__ == "__main__":
    main()
