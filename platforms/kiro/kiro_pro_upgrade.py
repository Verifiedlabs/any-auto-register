from camoufox.sync_api import Camoufox
import time, random

KOREAN_NAMES = ["민준 김", "서준 이", "지우 박", "현우 최", "수빈 정", "예준 강", "도윤 조", "시우 윤", "주원 장", "하준 임"]
KOREAN_ADDRESSES = [
    "1179, 광주, 북구, 두암3동, 333-11",
    "234, 광주, 북구, 용봉동, 112-5",
    "567, 광주, 북구, 오치동, 45-8",
    "89, 광주, 북구, 문흥동, 221-3",
    "432, 광주, 북구, 매곡동, 78-12",
]


def upgrade_kiro_pro_plus(email: str, password: str, card_number: str, card_exp: str, card_cvc: str, headless: bool = False):
    """
    Upgrade Kiro account to Pro+ via Korean VPN.
    
    Args:
        email: Google/Kiro email
        password: Google password
        card_number: card number (UnionPay etc)
        card_exp: expiry as MMYY (e.g. "1028")
        card_cvc: CVC
        headless: run headless or not
    
    Returns:
        dict with success status
    """
    name = random.choice(KOREAN_NAMES)
    address = random.choice(KOREAN_ADDRESSES)
    
    print(f"[kiro-upgrade] email={email} card=****{card_number[-4:]}")
    print(f"[kiro-upgrade] billing: {name} | {address} | Gwangju 57741")
    
    with Camoufox(headless=headless) as browser:
        page = browser.new_page()
        
        # Step 1: Login
        print("[1/6] Signing in to Kiro...")
        page.goto("https://app.kiro.dev/signin", wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)
        try:
            page.locator("button:has-text('Accept')").click(timeout=3000)
        except:
            pass
        time.sleep(1)
        
        page.locator("button:has-text('Google')").click()
        time.sleep(5)
        page.locator("input[type='email']").fill(email)
        page.locator("#identifierNext").click()
        time.sleep(4)
        page.locator("input[type='password']").fill(password)
        page.locator("#passwordNext").click()
        time.sleep(8)
        
        # Handle Korean Google consent
        try:
            page.locator("input[value*='동의']").click(timeout=5000)
            time.sleep(3)
        except:
            pass
        
        # Wait for Kiro redirect
        deadline = time.time() + 20
        while time.time() < deadline:
            if "kiro.dev" in page.url:
                break
            time.sleep(1)
        
        if "kiro.dev" not in page.url:
            return {"ok": False, "error": "Failed to login to Kiro", "url": page.url}
        
        print("[2/6] Logged in! Opening usage page...")
        page.goto("https://app.kiro.dev/account/usage", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        
        # Step 2: Click Upgrade to Pro+
        print("[3/6] Clicking Upgrade to Pro+...")
        context = page.context
        try:
            with context.expect_page(timeout=15000) as new_page_info:
                page.locator("button:has-text('Upgrade to Pro+')").click()
            sp = new_page_info.value
            sp.wait_for_load_state("domcontentloaded", timeout=30000)
        except:
            return {"ok": False, "error": "Pro+ button not found or no Stripe redirect"}
        
        time.sleep(5)
        print(f"[4/6] Stripe checkout opened. Switching to USD and filling card...")
        
        # Step 3: Switch to USD
        try:
            sp.get_by_role("button", name="US USD").click(timeout=5000)
            time.sleep(2)
        except:
            try:
                sp.locator("text=USD").first.click(timeout=3000)
                time.sleep(2)
            except:
                print("  Could not switch to USD, continuing with default currency")
        
        # Step 4: Fill card
        sp.locator("#cardNumber").first.click(); time.sleep(0.3)
        sp.locator("#cardNumber").first.press_sequentially(card_number, delay=80); time.sleep(0.5)
        sp.locator("#cardExpiry").first.click(); time.sleep(0.3)
        sp.locator("#cardExpiry").first.press_sequentially(card_exp, delay=80); time.sleep(0.5)
        sp.locator("#cardCvc").first.click(); time.sleep(0.3)
        sp.locator("#cardCvc").first.press_sequentially(card_cvc, delay=80); time.sleep(0.8)
        
        # Cardholder name (Korean)
        sp.locator("#billingName").first.click(); time.sleep(0.2)
        sp.locator("#billingName").first.press_sequentially(name, delay=60); time.sleep(0.3)
        
        # Country = South Korea
        sp.locator("#billingCountry").select_option(value="KR"); time.sleep(0.7)
        
        # Region = Gwangju
        try:
            sp.locator("#billingAdministrativeArea").select_option(label="광주 — Gwangju")
            time.sleep(0.5)
        except:
            try:
                sp.locator("#billingAdministrativeArea").select_option(value="광주")
                time.sleep(0.5)
            except:
                pass
        
        # City
        city_loc = sp.locator("#billingLocality").first
        if city_loc.count() and city_loc.is_visible():
            city_loc.click(); time.sleep(0.2)
            city_loc.press_sequentially("Gwangju", delay=60); time.sleep(0.3)
        
        # District
        district_loc = sp.locator("input[name='billingDistrict'], input[autocomplete*='district'], input[placeholder*='District'], input[placeholder*='구']").first
        if district_loc.count() and district_loc.is_visible():
            district_loc.click(); time.sleep(0.2)
            district_loc.press_sequentially("Buk-gu", delay=60); time.sleep(0.3)
        
        # Address line 1
        sp.locator("#billingAddressLine1").first.click(); time.sleep(0.2)
        sp.locator("#billingAddressLine1").first.press_sequentially(address, delay=40); time.sleep(0.3)
        
        # Postal code
        postal = sp.locator("#billingPostalCode").first
        if postal.count() and postal.is_visible():
            postal.click(); time.sleep(0.2)
            postal.press_sequentially("57741", delay=60)
        time.sleep(0.5)
        
        sp.keyboard.press("Tab"); time.sleep(1.5)
        
        # Wait for button complete
        try:
            sp.wait_for_function("""() => {
                const btn = document.querySelector("button[data-testid='hosted-payment-submit-button']") || document.querySelector("button[type='submit']");
                return btn && btn.className.includes("complete") && !btn.disabled;
            }""", timeout=15000)
            print("[5/6] Form complete! Clicking Subscribe...")
        except:
            print("[5/6] Button not complete, clicking anyway...")
        
        # Click Subscribe
        btn = sp.locator("button[data-testid='hosted-payment-submit-button']").last
        if not btn.count():
            btn = sp.locator("button[type='submit']").last
        btn.click()
        print("  Submitted! Waiting for hCaptcha...")
        
        # Step 5: Handle hCaptcha checkbox
        time.sleep(5)
        
        # Find and click hCaptcha checkbox
        hcaptcha_clicked = False
        for frame in sp.frames:
            if "hcaptcha" in frame.url.lower() and "newassets" not in frame.url:
                try:
                    checkbox = frame.locator("#checkbox, [id*='checkbox']")
                    if checkbox.count():
                        checkbox.first.click()
                        print("[6/6] hCaptcha checkbox clicked!")
                        hcaptcha_clicked = True
                        break
                except:
                    pass
        
        if not hcaptcha_clicked:
            # Try clicking in HCaptcha.html frame
            for frame in sp.frames:
                if "HCaptcha.html" in frame.url and "Invisible" not in frame.url:
                    try:
                        checkbox = frame.locator("#checkbox, .check, [role='checkbox']")
                        if checkbox.count():
                            checkbox.first.click()
                            print("[6/6] hCaptcha clicked (HCaptcha.html)!")
                            hcaptcha_clicked = True
                            break
                    except:
                        pass
        
        if not hcaptcha_clicked:
            print("  hCaptcha checkbox not found - waiting for manual or auto-pass...")
        
        # Wait for result
        print("  Waiting for completion...")
        for i in range(60):
            time.sleep(2)
            try:
                url = sp.url
                if "kiro.dev" in url:
                    print(f"\n=== SUCCESS! Redirected to Kiro! ===")
                    return {"ok": True, "email": email, "plan": "pro+"}
            except:
                # Page closed = redirected
                print(f"\n=== SUCCESS! Page closed (redirected) ===")
                return {"ok": True, "email": email, "plan": "pro+"}
            
            # Check for green checkmark (success)
            try:
                body = sp.locator("body").inner_text(timeout=2000)
                if "success" in body.lower() or "thank" in body.lower():
                    print(f"\n=== SUCCESS! ===")
                    return {"ok": True, "email": email, "plan": "pro+"}
            except:
                pass
        
        return {"ok": False, "error": "Timeout waiting for completion", "url": sp.url}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 5:
        print("Usage: python kiro_pro_upgrade.py <email> <password> <card_number> <card_exp_MMYY> <card_cvc>")
        sys.exit(1)
    
    result = upgrade_kiro_pro_plus(
        email=sys.argv[1],
        password=sys.argv[2],
        card_number=sys.argv[3],
        card_exp=sys.argv[4],
        card_cvc=sys.argv[5] if len(sys.argv) > 5 else "000",
        headless=False,
    )
    print(f"\nResult: {result}")
