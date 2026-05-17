from __future__ import annotations

import random
import string
import time
from typing import Optional

import requests

BASE_URL = "https://ccode.scydao.com/api/v1"
DEFAULT_AFF_CODE = "3GLRG6XG8VQE"


def _random_email() -> str:
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    name = ''.join(random.choice(chars) for _ in range(8))
    return f"{name}@gmail.com"


def _gen_password() -> str:
    return "qwerty77"


def register_ccode(
    email: Optional[str] = None,
    password: Optional[str] = None,
    aff_code: str = DEFAULT_AFF_CODE,
    proxy: Optional[str] = None,
) -> dict:
    email = email or _random_email()
    pwd = password or _gen_password()

    session = requests.Session()
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}

    try:
        resp = session.post(f"{BASE_URL}/auth/register", json={
            "email": email,
            "password": pwd,
            "aff_code": aff_code,
        }, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        data = resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e), "email": email}

    if data.get("code") != 0:
        return {"ok": False, "error": data.get("message", "Unknown error"), "email": email}

    token = data["data"]["access_token"]
    user = data["data"]["user"]

    try:
        key_resp = session.post(f"{BASE_URL}/keys", json={"name": "auto-key"}, headers={"Authorization": f"Bearer {token}", "User-Agent": "Mozilla/5.0"}, timeout=10)
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
    count: int = 10,
    aff_code: str = DEFAULT_AFF_CODE,
    pause_after: int = 5,
    pause_duration: float = 5.0,
    delay: float = 1.5,
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
        result = register_ccode(aff_code=aff_code, proxy=proxy)
        results.append(result)

        if delay > 0:
            time.sleep(delay + random.uniform(0, 1))

        if (i + 1) % pause_after == 0 and (i + 1) < count:
            time.sleep(pause_duration)

    return results
