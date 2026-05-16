from __future__ import annotations

import time
from typing import Any, Callable, Optional

from playwright.sync_api import sync_playwright, Page, BrowserContext

KIRO_ORIGIN = "https://app.kiro.dev"
KIRO_USAGE_URL = f"{KIRO_ORIGIN}/account/usage"
UPGRADE_TO_PRO_RE = r"^Upgrade\s+to\s+Pro$"

KIRO_AUTH_COOKIE_NAMES = {"refreshtoken", "accesstoken", "idtoken", "kiro-visitor-id"}


def _is_kiro_domain(domain: str) -> bool:
    d = domain.lstrip(".").lower()
    return d == "app.kiro.dev" or d == "kiro.dev" or d.endswith(".kiro.dev")


def _filter_auth_cookies(cookies: list[dict]) -> list[dict]:
    return [c for c in cookies if _is_kiro_domain(c.get("domain", "")) and c.get("name", "").lower() in KIRO_AUTH_COOKIE_NAMES]


def _hydrate_session(page: Page, context: BrowserContext, session_data: dict, log: Callable) -> bool:
    cookies = session_data.get("cookies", [])
    filtered = _filter_auth_cookies(cookies)
    if not filtered:
        log("[hydrate] No Kiro auth cookies found")
        return False

    pw_cookies = []
    for c in filtered:
        entry = {
            "name": c["name"],
            "value": c["value"],
            "domain": c.get("domain", ".kiro.dev"),
            "path": c.get("path", "/"),
            "httpOnly": c.get("httpOnly", False),
            "secure": c.get("secure", True),
            "sameSite": "Lax",
        }
        if c.get("expires") and c["expires"] > 0:
            entry["expires"] = c["expires"]
        pw_cookies.append(entry)

    context.add_cookies(pw_cookies)
    log(f"[hydrate] Injected {len(pw_cookies)} cookies")

    try:
        page.goto(f"{KIRO_ORIGIN}/", wait_until="commit", timeout=45000)
    except Exception as e:
        log(f"[hydrate] Navigation failed: {e}")
        return False

    ls = session_data.get("localStorage", {})
    ss = session_data.get("sessionStorage", {})
    if ls or ss:
        page.evaluate("""({ls, ss}) => {
            for (const [k, v] of Object.entries(ls)) { try { localStorage.setItem(k, v); } catch {} }
            for (const [k, v] of Object.entries(ss)) { try { sessionStorage.setItem(k, v); } catch {} }
        }""", {"ls": ls, "ss": ss})

    try:
        page.goto(KIRO_USAGE_URL, wait_until="domcontentloaded", timeout=30000)
    except:
        pass

    return True


def _check_pro_status(page: Page, log: Callable, timeout: int = 30) -> str:
    try:
        page.goto(KIRO_USAGE_URL, wait_until="domcontentloaded", timeout=30000)
    except:
        pass

    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except:
        pass

    deadline = time.time() + timeout
    while time.time() < deadline:
        body = page.locator("body").inner_text(timeout=3000)
        if "KIRO PRO" in body.upper() and "CURRENT PLAN" in body.upper():
            return "pro"
        import re
        if re.search(r"Upgrade\s+to\s+Pro", body):
            return "free"
        page.wait_for_timeout(1000)
    return "unknown"


def _click_upgrade_to_pro(page: Page, log: Callable, timeout: int = 30) -> Optional[str]:
    import re

    try:
        page.locator('[class*="_awsCookieConsent"]').locator("button").first.click(timeout=3000)
    except:
        pass

    btn = page.get_by_role("button", name=re.compile(UPGRADE_TO_PRO_RE, re.I)).first
    if not btn.count():
        btn = page.get_by_role("link", name=re.compile(UPGRADE_TO_PRO_RE, re.I)).first
    if not btn.count():
        log("[upgrade] Upgrade to Pro button not found")
        return None

    with page.context.expect_page(timeout=30000) as new_page_info:
        try:
            btn.click(timeout=10000)
        except:
            btn.evaluate("(el) => el.click()")

    try:
        stripe_page = new_page_info.value
        stripe_page.wait_for_load_state("domcontentloaded", timeout=30000)
        log(f"[upgrade] Stripe page opened: {stripe_page.url[:60]}")
        return stripe_page.url if "stripe.com" in stripe_page.url else None
    except:
        pass

    page.wait_for_timeout(3000)
    if "stripe.com" in page.url:
        log(f"[upgrade] Redirected to Stripe: {page.url[:60]}")
        return page.url

    return None


def _fill_and_submit_stripe(page: Page, vcc: dict, log: Callable, timeout: int = 180) -> dict:
    from platforms.windsurf.browser_register import prewarm_stripe_page
    from core.address_gen import generate_billing_address_for_vcc

    page.wait_for_timeout(3000)
    body = page.locator("body").inner_text(timeout=3000)
    if "Something went wrong" in body:
        return {"kind": "error", "message": "Stripe checkout expired"}

    prewarm_stripe_page(page, log)

    billing = generate_billing_address_for_vcc(vcc)

    page.locator("#cardNumber").first.click()
    time.sleep(0.3)
    page.locator("#cardNumber").first.press_sequentially(str(vcc.get("number", "")).replace(" ", ""), delay=80)
    time.sleep(0.5)

    page.locator("#cardExpiry").first.click()
    time.sleep(0.3)
    exp = f"{int(vcc.get('expMonth', 1)):02d}{str(vcc.get('expYear', 2029))[-2:]}"
    page.locator("#cardExpiry").first.press_sequentially(exp, delay=80)
    time.sleep(0.5)

    page.locator("#cardCvc").first.click()
    time.sleep(0.3)
    page.locator("#cardCvc").first.press_sequentially(str(vcc.get("cvc", "")), delay=80)
    time.sleep(0.8)

    name = str(billing.get("name", "Kiro User"))
    page.locator("#billingName").first.click()
    time.sleep(0.2)
    page.locator("#billingName").first.press_sequentially(name, delay=60)
    time.sleep(0.3)

    country = str(billing.get("country", "US"))
    page.locator("#billingCountry").select_option(value=country)
    page.wait_for_timeout(700)

    state = str(billing.get("state", ""))
    if state:
        try:
            page.locator("#billingAdministrativeArea").select_option(value=state)
        except:
            pass

    line1 = str(billing.get("line1", ""))
    if line1:
        page.locator("#billingAddressLine1").first.click()
        time.sleep(0.2)
        page.locator("#billingAddressLine1").first.press_sequentially(line1, delay=60)
        time.sleep(0.3)

    city = str(billing.get("city", ""))
    if city:
        page.locator("#billingLocality").first.click()
        time.sleep(0.2)
        page.locator("#billingLocality").first.press_sequentially(city, delay=60)
        time.sleep(0.3)

    postal = str(billing.get("postalCode", ""))
    postal_loc = page.locator("#billingPostalCode").first
    if postal and postal_loc.count() and postal_loc.is_visible():
        postal_loc.click()
        time.sleep(0.2)
        postal_loc.press_sequentially(postal, delay=60)
    time.sleep(0.5)

    try:
        cb = page.locator("#termsOfServiceConsentCheckbox").first
        if cb.count() and not cb.is_checked():
            cb.check(force=True)
    except:
        pass

    page.keyboard.press("Tab")
    time.sleep(1.5)

    try:
        page.wait_for_function("""() => {
            const btn = document.querySelector("button[data-testid='hosted-payment-submit-button']") || document.querySelector("button[type='submit']");
            return btn && btn.className.includes("complete") && !btn.disabled;
        }""", timeout=15000)
        log("[stripe] Button complete")
    except:
        log("[stripe] Button not complete, submitting anyway")

    state_result = {"kind": "timeout"}

    def on_response(resp):
        if "stripe.com" in resp.url and "r.stripe.com" not in resp.url and "q.stripe.com" not in resp.url:
            try:
                data = resp.json()
                if not isinstance(data, dict):
                    return
                if data.get("object") == "checkout.session":
                    si = data.get("setup_intent")
                    if isinstance(si, dict):
                        if si.get("status") == "succeeded":
                            state_result["kind"] = "success"
                        elif si.get("last_setup_error"):
                            err = si["last_setup_error"]
                            state_result["kind"] = "declined"
                            state_result["message"] = err.get("message", "")
                    st = data.get("status", "")
                    ps = data.get("payment_status", "")
                    if st == "complete" or ps == "paid":
                        state_result["kind"] = "success"
            except:
                pass

    page.on("response", on_response)

    btn = page.locator('button[data-testid="hosted-payment-submit-button"]').last
    if not btn.count():
        btn = page.locator('button[type="submit"]').last
    btn.click()
    log("[stripe] Clicked submit")

    deadline = time.time() + timeout
    while time.time() < deadline:
        page.wait_for_timeout(2000)
        if state_result["kind"] in ("success", "declined"):
            break
        url = page.url
        if "kiro.dev" in url or "subscription/success" in url:
            state_result["kind"] = "success"
            break

    return state_result


def upgrade_kiro_to_pro(
    *,
    session_data: dict,
    password: str = "",
    vcc: Optional[dict] = None,
    headless: bool = False,
    proxy: Optional[str] = None,
    timeout: int = 180,
    on_challenge: str = "pause",
    log_fn: Callable[[str], None] = print,
) -> dict:
    try:
        from camoufox.sync_api import Camoufox
        use_camoufox = True
    except:
        use_camoufox = False

    log_fn(f"[kiro-upgrade] email={session_data.get('email', '')} headless={headless} on_challenge={on_challenge}")

    if use_camoufox:
        ctx_manager = Camoufox(headless=headless, proxy={"server": proxy} if proxy else None)
    else:
        pw = sync_playwright().start()
        launch_opts = {"headless": headless, "args": ["--disable-blink-features=AutomationControlled", "--no-sandbox"]}
        browser = pw.chromium.launch(**launch_opts)
        ctx_manager = None

    try:
        if use_camoufox:
            browser = ctx_manager.__enter__()
            page = browser.new_page()
            context = page.context
        else:
            context = browser.new_context(viewport={"width": 1440, "height": 960}, locale="en-US")
            page = context.new_page()

        # Step 1: Hydrate session
        hydrated = _hydrate_session(page, context, session_data, log_fn)
        if not hydrated:
            if not password:
                return {"ok": False, "error": "No session cookies and no password for Google login"}
            log_fn("[kiro-upgrade] Hydrate failed, need Google login (not implemented yet)")
            return {"ok": False, "error": "Hydrate failed, Google login not yet implemented in this flow"}

        # Step 2: Check Pro status
        status = _check_pro_status(page, log_fn)
        if status == "pro":
            log_fn("[kiro-upgrade] Already Pro!")
            return {"ok": True, "data": {"message": "Already Pro", "status": "pro"}}
        if status == "unknown":
            log_fn("[kiro-upgrade] Could not determine plan status")
            return {"ok": False, "error": "Could not determine plan status"}

        log_fn(f"[kiro-upgrade] Status: {status}, proceeding to upgrade")

        # Step 3: Click Upgrade to Pro
        stripe_url = _click_upgrade_to_pro(page, log_fn)
        if not stripe_url:
            return {"ok": False, "error": "Could not navigate to Stripe checkout"}

        log_fn(f"[kiro-upgrade] Stripe URL: {stripe_url[:60]}")

        # Step 4: Fill card and submit
        if not vcc:
            return {"ok": True, "data": {"message": "Stripe checkout URL generated", "checkout_url": stripe_url}}

        stripe_page = page
        for p in context.pages:
            if "stripe.com" in p.url:
                stripe_page = p
                break

        outcome = _fill_and_submit_stripe(stripe_page, vcc, log_fn, timeout=timeout)
        log_fn(f"[kiro-upgrade] Outcome: {outcome}")

        if outcome["kind"] == "success":
            return {"ok": True, "data": {"message": "Kiro Pro activated!", "status": "pro", "outcome": outcome}}

        return {"ok": False, "data": {"outcome": outcome}, "error": f"Stripe checkout: {outcome.get('kind')} - {outcome.get('message', '')}"}

    finally:
        if use_camoufox:
            try:
                ctx_manager.__exit__(None, None, None)
            except:
                pass
        else:
            try:
                browser.close()
                pw.stop()
            except:
                pass
