"""Supplemental checkout + product screenshots."""
from __future__ import annotations

import re
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5173"
OUT = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
PWD = "VeinPayDemo1!"


def shot(page, folder: str, name: str, full: bool = False) -> None:
    dest = OUT / folder
    dest.mkdir(parents=True, exist_ok=True)
    page.wait_for_timeout(400)
    page.screenshot(path=str(dest / f"{name}.png"), full_page=full)
    print("ok", folder, name)


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.set_default_timeout(20000)

        page.goto(BASE + "/member/shop", wait_until="networkidle")
        hrefs = page.evaluate(
            """() => {
              const set = new Set();
              for (const a of document.querySelectorAll('a[href*=\"/member/shop/\"]')) {
                const h = a.getAttribute('href');
                if (!h) continue;
                const parts = h.split('/').filter(Boolean);
                if (parts.length >= 3) set.add(h);
              }
              return [...set];
            }"""
        )
        print("products", hrefs[:8])
        for i, h in enumerate(hrefs[:6]):
            url = BASE + h if h.startswith("/") else h
            page.goto(url, wait_until="networkidle")
            shot(page, "shop", f"20-product-{i+1}")
            shot(page, "shop", f"20-product-{i+1}-full", True)

        page.goto(BASE + "/user/login", wait_until="networkidle")
        page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
        page.goto(BASE + "/user/login", wait_until="networkidle")
        page.locator('input[type="email"]').first.fill("cart.test@veinpay.local")
        page.locator('input[type="password"]').first.fill(PWD)
        page.get_by_role("button", name=re.compile(r"sign|log|continue", re.I)).first.click()
        page.wait_for_timeout(2000)

        page.goto(BASE + "/member/shop", wait_until="networkidle")
        btns = page.get_by_role("button", name=re.compile(r"add", re.I))
        if btns.count():
            btns.first.click()
            page.wait_for_timeout(500)

        page.goto(BASE + "/member/cart", wait_until="networkidle")
        shot(page, "cart", "11-cart-with-items")
        shot(page, "cart", "12-cart-with-items-full", True)

        page.goto(BASE + "/member/checkout", wait_until="networkidle")
        shot(page, "cart", "13-checkout-page")
        shot(page, "cart", "14-checkout-page-full", True)
        page.evaluate("window.scrollTo(0, 600)")
        shot(page, "cart", "15-checkout-palm-area")
        page.evaluate("window.scrollTo(0, 1200)")
        shot(page, "cart", "16-checkout-lower")

        page.goto(BASE + "/member/enrollment", wait_until="networkidle")
        shot(page, "cart", "17-member-enrollment")
        page.goto(BASE + "/member/recognition", wait_until="networkidle")
        shot(page, "cart", "18-member-recognition")

        for name, path in [
            ("12-admin-login-filled", "/login"),
            ("13-owner-login-defaults", "/owner/login"),
            ("14-employee-signup", "/employee/signup"),
        ]:
            page.goto(BASE + path, wait_until="networkidle")
            shot(page, "auth", name)

        browser.close()

    for folder in sorted(OUT.iterdir()):
        if folder.is_dir():
            print(folder.name, len(list(folder.glob("*.png"))))


if __name__ == "__main__":
    main()
