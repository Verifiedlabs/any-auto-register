from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from core.proxy_fetcher import fetch_proxies, fetch_all_unique, format_proxy_url, check_proxy_alive
from core.db import engine
from sqlmodel import Session, text

router = APIRouter(prefix="/proxy-fetch", tags=["proxy-fetch"])


class ProxyFetchRequest(BaseModel):
    proxy_type: Optional[str] = None
    limit: int = 100
    save_to_pool: bool = False
    check_alive: bool = False


@router.post("/fetch")
def proxy_fetch(req: ProxyFetchRequest):
    proxies = fetch_proxies(limit=req.limit, proxy_type=req.proxy_type)

    if req.check_alive:
        alive_proxies = []
        for p in proxies:
            url = format_proxy_url(p)
            if check_proxy_alive(url):
                alive_proxies.append(p)
        proxies = alive_proxies

    if req.save_to_pool and proxies:
        from core.db import engine
        count = 0
        with Session(engine) as s:
            for p in proxies:
                url = format_proxy_url(p)
                existing = s.exec(text("SELECT id FROM proxies WHERE url = :url").bindparams(url=url)).first()
                if not existing:
                    s.exec(
                        text("INSERT INTO proxies (url, region, is_active, success_count, fail_count) VALUES (:url, :region, 1, 0, 0)").bindparams(url=url, region=p.get("country", "")),
                    )
                    count += 1
            s.commit()
        return {"ok": True, "fetched": len(proxies), "saved": count}

    formatted = [{"url": format_proxy_url(p), "ip": p["ip"], "port": p["port"], "type": p.get("type", "HTTP"), "country": p.get("country", ""), "status": p.get("status", "")} for p in proxies]
    return {"ok": True, "proxies": formatted, "count": len(formatted)}


@router.post("/fetch-all")
def proxy_fetch_all(req: ProxyFetchRequest):
    proxies = fetch_all_unique(proxy_type=req.proxy_type)

    if req.save_to_pool and proxies:
        count = 0
        with Session(engine) as s:
            for p in proxies:
                url = format_proxy_url(p)
                existing = s.exec(text("SELECT id FROM proxies WHERE url = :url").bindparams(url=url)).first()
                if not existing:
                    s.exec(
                        text("INSERT INTO proxies (url, region, is_active, success_count, fail_count) VALUES (:url, :region, 1, 0, 0)").bindparams(url=url, region=p.get("country", "")),
                    )
                    count += 1
            s.commit()
        return {"ok": True, "fetched": len(proxies), "saved": count}

    formatted = [{"url": format_proxy_url(p), "type": p.get("type", "HTTP"), "country": p.get("country", "")} for p in proxies]
    return {"ok": True, "proxies": formatted, "count": len(formatted)}


@router.get("/stats")
def proxy_fetch_stats():
    proxies = fetch_proxies(limit=1)
    import urllib.request, json
    body = json.dumps({"limit": 1}).encode()
    headers = {"apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ3bWhicGd3aGZ3dXd0YXR0c2V0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjczMjc0NjYsImV4cCI6MjA4MjkwMzQ2Nn0.LSMD2P4whDzoIW4UCig0ly0j6UOxd5fHhIkUhywnmrg", "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ3bWhicGd3aGZ3dXd0YXR0c2V0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjczMjc0NjYsImV4cCI6MjA4MjkwMzQ2Nn0.LSMD2P4whDzoIW4UCig0ly0j6UOxd5fHhIkUhywnmrg", "Content-Type": "application/json"}
    try:
        req = urllib.request.Request("https://vwmhbpgwhfwuwtattset.supabase.co/functions/v1/fetch-proxies", data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read())
            return {"ok": True, "total_available": res.get("totalAvailable", 0)}
    except:
        return {"ok": False, "total_available": 0}
