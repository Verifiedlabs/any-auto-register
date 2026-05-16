from __future__ import annotations

import random
import time
from typing import Optional

import requests


def _luhn_checksum(digits: str) -> int:
    total = 0
    alt = True
    for i in range(len(digits) - 1, -1, -1):
        n = int(digits[i])
        if alt:
            n *= 2
            if n > 9:
                n -= 9
        total += n
        alt = not alt
    return (10 - (total % 10)) % 10


def _random_digits(n: int) -> str:
    return ''.join(str(random.randint(0, 9)) for _ in range(n))


def generate_pan(prefix: str, total: int = 16) -> str:
    cleaned = ''.join(c for c in prefix if c.isdigit())
    if not cleaned:
        raise ValueError("Empty BIN prefix")
    if total < len(cleaned) + 1:
        raise ValueError(f"Total {total} too short for prefix {len(cleaned)} digits")
    filler_len = total - len(cleaned) - 1
    filler = _random_digits(filler_len) if filler_len > 0 else ''
    partial = cleaned + filler
    check = _luhn_checksum(partial)
    return partial + str(check)


def luhn_valid(number: str) -> bool:
    digits = ''.join(c for c in number if c.isdigit())
    if len(digits) < 12:
        return False
    total = 0
    alt = False
    for i in range(len(digits) - 1, -1, -1):
        n = int(digits[i])
        if alt:
            n *= 2
            if n > 9:
                n -= 9
        total += n
        alt = not alt
    return total % 10 == 0


SCHEME_LENGTHS = {
    "visa": 16,
    "mastercard": 16,
    "amex": 15,
    "discover": 16,
    "jcb": 16,
    "diners": 14,
    "unionpay": 16,
    "maestro": 16,
}

AMEX_PREFIXES = {"34", "37"}


def detect_scheme(bin_prefix: str) -> str:
    b = bin_prefix[:2]
    if b in AMEX_PREFIXES:
        return "amex"
    if bin_prefix[0] == "4":
        return "visa"
    if b in ("51", "52", "53", "54", "55") or (2221 <= int(bin_prefix[:4] or "0") <= 2720):
        return "mastercard"
    if b == "62":
        return "unionpay"
    if b in ("60", "65") or bin_prefix[:4] == "6011":
        return "discover"
    if b == "35":
        return "jcb"
    if b in ("36", "38") or bin_prefix[:3] in ("300", "301", "302", "303", "304", "305"):
        return "diners"
    return "unknown"


def generate_cards(
    bin_prefix: str,
    count: int = 10,
    exp_month: Optional[int] = None,
    exp_year: Optional[int] = None,
    length: Optional[int] = None,
) -> list[dict]:
    cleaned = ''.join(c for c in bin_prefix if c.isdigit())
    if len(cleaned) < 6:
        raise ValueError("BIN must be at least 6 digits")

    scheme = detect_scheme(cleaned)
    total = length or SCHEME_LENGTHS.get(scheme, 16)
    cvc_len = 4 if scheme == "amex" else 3

    now_year = 2026
    now_month = 5
    cards = []
    seen = set()

    for _ in range(count * 3):
        if len(cards) >= count:
            break
        pan = generate_pan(cleaned, total)
        if pan in seen:
            continue
        seen.add(pan)

        if exp_month and exp_year:
            em, ey = exp_month, exp_year
        else:
            months_ahead = random.randint(6, 48)
            m = now_month + months_ahead
            ey = now_year + (m - 1) // 12
            em = ((m - 1) % 12) + 1

        cvc = _random_digits(cvc_len)
        while int(cvc) == 0:
            cvc = _random_digits(cvc_len)

        cards.append({
            "number": pan,
            "expMonth": em,
            "expYear": ey,
            "cvc": cvc,
            "scheme": scheme,
            "bin": cleaned,
            "last4": pan[-4:],
        })

    return cards


def check_card_live(number: str, exp_month: int, exp_year: int, cvc: str) -> dict:
    try:
        exp_m = f"{int(exp_month):02d}"
        exp_y = str(exp_year)[-2:] if len(str(exp_year)) == 4 else str(exp_year)
        data = f"{number}|{exp_m}|{exp_y}|{cvc}"
        resp = requests.post(
            "https://api.chkr.cc/",
            json={"data": data},
            timeout=30,
        )
        if resp.status_code == 200:
            result = resp.json()
            return {
                "live": result.get("code") == 1,
                "status": result.get("status", "Unknown"),
                "message": result.get("message", ""),
                "card_info": result.get("card", {}),
            }
        return {"live": False, "status": "error", "message": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"live": False, "status": "error", "message": str(e)}


def lookup_bin(bin_prefix: str) -> dict:
    cleaned = ''.join(c for c in bin_prefix if c.isdigit())[:8]
    if len(cleaned) < 6:
        return {"error": "BIN must be at least 6 digits"}

    result = {"bin": cleaned, "scheme": detect_scheme(cleaned)}

    try:
        resp = requests.get(
            f"https://lookup.binlist.net/{cleaned}",
            headers={"Accept-Version": "3"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            result.update({
                "brand": data.get("scheme", ""),
                "type": data.get("type", ""),
                "category": data.get("brand", ""),
                "country": data.get("country", {}).get("alpha2", ""),
                "country_name": data.get("country", {}).get("name", ""),
                "bank": data.get("bank", {}).get("name", ""),
                "prepaid": data.get("prepaid"),
            })
            return result
    except:
        pass

    try:
        resp = requests.get(
            f"https://data.handyapi.com/bin/{cleaned}",
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("Status") == "SUCCESS":
                result.update({
                    "brand": data.get("Scheme", ""),
                    "type": data.get("Type", ""),
                    "country": data.get("Country", {}).get("A2", ""),
                    "country_name": data.get("Country", {}).get("Name", ""),
                    "bank": data.get("Issuer", ""),
                })
                return result
    except:
        pass

    return result
