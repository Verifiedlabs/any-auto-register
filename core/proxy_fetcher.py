from __future__ import annotations

import json
import time
import urllib.request
from typing import Optional

URL = "https://vwmhbpgwhfwuwtattset.supabase.co/functions/v1/fetch-proxies"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ3bWhicGd3aGZ3dXd0YXR0c2V0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjczMjc0NjYsImV4cCI6MjA4MjkwMzQ2Nn0.LSMD2P4whDzoIW4UCig0ly0j6UOxd5fHhIkUhywnmrg"
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}


def fetch_proxies(limit: int = 100, proxy_type: Optional[str] = None) -> list[dict]:
    body_data: dict = {"limit": min(limit, 9999)}
    if proxy_type and proxy_type.lower() != "all":
        body_data["type"] = proxy_type.upper()
    body = json.dumps(body_data).encode()
    for attempt in range(3):
        try:
            req = urllib.request.Request(URL, data=body, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as r:
                res = json.loads(r.read())
                if res.get("success"):
                    return res.get("proxies", [])
        except Exception:
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
    return []


def fetch_all_unique(proxy_type: Optional[str] = None, max_rounds: int = 10) -> list[dict]:
    seen: dict[str, dict] = {}
    no_new = 0
    for _ in range(max_rounds):
        batch = fetch_proxies(limit=9999, proxy_type=proxy_type)
        new = 0
        for p in batch:
            key = f"{p['ip']}:{p['port']}"
            if key not in seen:
                seen[key] = p
                new += 1
        if new == 0:
            no_new += 1
            if no_new >= 3:
                break
        else:
            no_new = 0
        time.sleep(0.5)
    return list(seen.values())


def format_proxy_url(proxy: dict) -> str:
    proto = (proxy.get("type") or "http").lower()
    if proto == "socks4":
        proto = "socks4"
    elif proto == "socks5":
        proto = "socks5"
    else:
        proto = "http"
    return f"{proto}://{proxy['ip']}:{proxy['port']}"


def check_proxy_alive(proxy_url: str, timeout: int = 5) -> bool:
    try:
        import urllib.request
        proxy_handler = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
        opener = urllib.request.build_opener(proxy_handler)
        req = urllib.request.Request("http://httpbin.org/ip", method="GET")
        with opener.open(req, timeout=timeout) as r:
            return r.status == 200
    except:
        return False


def resolve_ip_country(ip: str) -> str:
    try:
        import urllib.request, json
        req = urllib.request.Request(f"http://ip-api.com/json/{ip}?fields=countryCode")
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
            return data.get("countryCode", "")
    except:
        return ""
