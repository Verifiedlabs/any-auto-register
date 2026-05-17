from __future__ import annotations

import random
import string
import time
from typing import Optional

import requests

BASE_URL = "https://ccode.scydao.com/api/v1"
DEFAULT_AFF_CODE = "3GLRG6XG8VQE"


def _gmail_trick(base: str) -> str:
    chars = list(base)
    positions = random.sample(range(1, len(chars)), random.randint(1, min(4, len(chars) - 1)))
    for pos in sorted(positions, reverse=True):
        chars.insert(pos, '.')
    return ''.join(chars) + '@gmail.com'


def _gen_password() -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12)) + '!A1'


def register_ccode(
    gmail_base: str,
    password: Optional[str] = None,
    aff_code: str = DEFAULT_AFF_CODE,
    proxy: Optional[str] = None,
) -> dict:
    email = _gmail_trick(gmail_base)
    pwd = password or _gen_password()

    session = requests.Session()
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}

    try:
        resp = session.post(f"{BASE_URL}/auth/register", json={
            "email": email,
            "password": pwd,
            "invitation_code": aff_code,
        }, timeout=15)
        data = resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e), "email": email}

    if data.get("code") != 0:
        return {"ok": False, "error": data.get("message", "Unknown error"), "email": email}

    token = data["data"]["access_token"]
    user = data["data"]["user"]

    try:
        key_resp = session.post(f"{BASE_URL}/keys", json={"name": "auto-key"}, headers={"Authorization": f"Bearer {token}"}, timeout=10)
        key_data = key_resp.json()
        api_key = key_data.get("data", {}).get("key", "")
    except:
        api_key = ""

    return {
        "ok": True,
        "email": email,
        "password": pwd,
        "access_token": token,
        "refresh_token": data["data"].get("refresh_token", ""),
        "api_key": api_key,
        "user_id": user.get("id"),
        "balance": user.get("balance", 0),
    }


def bulk_register_ccode(
    gmail_base: str,
    count: int = 10,
    aff_code: str = DEFAULT_AFF_CODE,
    delay: float = 3.0,
    use_proxy: bool = False,
) -> list[dict]:
    proxies = []
    if use_proxy:
        try:
            from core.db import engine
            from sqlmodel import Session as DbSession, text
            with DbSession(engine) as s:
                rows = s.exec(text("SELECT url FROM proxies WHERE is_active = 1")).all()
                proxies = [r[0] for r in rows]
        except:
            pass

    results = []
    for i in range(count):
        proxy = proxies[i % len(proxies)] if proxies else None
        result = register_ccode(gmail_base, aff_code=aff_code, proxy=proxy)
        results.append(result)
        if not result["ok"] and "频繁" in result.get("error", ""):
            import re
            wait_match = re.search(r"(\d+)\s*秒", result["error"])
            wait_time = int(wait_match.group(1)) + 2 if wait_match else 60
            time.sleep(wait_time)
            proxy = proxies[(i + 1) % len(proxies)] if proxies else None
            retry = register_ccode(gmail_base, aff_code=aff_code, proxy=proxy)
            results[-1] = retry
        if delay > 0:
            time.sleep(delay)
    return results
