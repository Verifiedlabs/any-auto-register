from __future__ import annotations

import random
import time
from typing import Optional

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

US_CITY_QUERIES = [
    ("New York", "NY", "office building Manhattan New York"),
    ("New York", "NY", "office building Brooklyn New York"),
    ("Chicago", "IL", "office building Chicago IL"),
    ("San Francisco", "CA", "office building San Francisco CA"),
    ("Los Angeles", "CA", "office building Los Angeles CA"),
    ("Seattle", "WA", "office building Seattle WA"),
    ("Austin", "TX", "office building Austin TX"),
    ("Boston", "MA", "office building Boston MA"),
    ("Miami", "FL", "office building Miami FL"),
    ("Denver", "CO", "office building Denver CO"),
    ("Atlanta", "GA", "office building Atlanta GA"),
    ("Dallas", "TX", "office building Dallas TX"),
    ("Houston", "TX", "office building Houston TX"),
    ("Phoenix", "AZ", "office building Phoenix AZ"),
    ("Portland", "OR", "office building Portland OR"),
]

US_STATE_ABBR = {
    "New York": "NY", "Illinois": "IL", "California": "CA",
    "Washington": "WA", "Texas": "TX", "Massachusetts": "MA",
    "Florida": "FL", "Colorado": "CO", "Georgia": "GA",
    "Arizona": "AZ", "Oregon": "OR", "Nevada": "NV",
    "Virginia": "VA", "Pennsylvania": "PA", "Ohio": "OH",
    "Michigan": "MI", "Minnesota": "MN", "North Carolina": "NC",
}

STATIC_FALLBACK_US = [
    {"line1": "233 S Wacker Dr", "city": "Chicago", "state": "IL", "postalCode": "60606"},
    {"line1": "350 Fifth Ave", "city": "New York", "state": "NY", "postalCode": "10118"},
    {"line1": "1 Market St", "city": "San Francisco", "state": "CA", "postalCode": "94105"},
    {"line1": "410 Terry Ave N", "city": "Seattle", "state": "WA", "postalCode": "98109"},
    {"line1": "100 Main St", "city": "Austin", "state": "TX", "postalCode": "78701"},
    {"line1": "1600 Amphitheatre Pkwy", "city": "Mountain View", "state": "CA", "postalCode": "94043"},
    {"line1": "1 Microsoft Way", "city": "Redmond", "state": "WA", "postalCode": "98052"},
    {"line1": "500 W 2nd St", "city": "Austin", "state": "TX", "postalCode": "78701"},
    {"line1": "1 Hacker Way", "city": "Menlo Park", "state": "CA", "postalCode": "94025"},
    {"line1": "1 Infinite Loop", "city": "Cupertino", "state": "CA", "postalCode": "95014"},
]

_us_pool: list[dict] = []
_pool_fetched = False


def _fetch_us_addresses(limit_per_query: int = 5) -> list[dict]:
    results = []
    queries = random.sample(US_CITY_QUERIES, min(5, len(US_CITY_QUERIES)))
    for city, state_abbr, query in queries:
        try:
            resp = requests.get(
                NOMINATIM_URL,
                params={"q": query, "format": "json", "addressdetails": 1, "limit": limit_per_query, "countrycodes": "us"},
                headers={"User-Agent": "any-auto-register/1.0"},
                timeout=10,
            )
            if resp.status_code == 429:
                time.sleep(2)
                continue
            if resp.status_code != 200 or not resp.text.strip():
                continue
            data = resp.json()
            for r in data:
                addr = r.get("address") or {}
                house = str(addr.get("house_number") or "").strip()
                road = str(addr.get("road") or "").strip()
                city_name = str(addr.get("city") or addr.get("town") or city).strip()
                state_full = str(addr.get("state") or "").strip()
                state = US_STATE_ABBR.get(state_full, state_abbr)
                postal = str(addr.get("postcode") or "").strip()
                if house and road and city_name and postal and len(postal) == 5:
                    results.append({
                        "line1": f"{house} {road}",
                        "line2": "",
                        "city": city_name,
                        "state": state,
                        "postalCode": postal,
                        "country": "US",
                    })
            time.sleep(1.1)
        except Exception:
            pass
    return results


def _ensure_us_pool() -> list[dict]:
    global _us_pool, _pool_fetched
    if _pool_fetched and _us_pool:
        return _us_pool
    fetched = _fetch_us_addresses()
    if fetched:
        _us_pool = fetched
    else:
        _us_pool = [dict(a) | {"line2": "", "country": "US"} for a in STATIC_FALLBACK_US]
    _pool_fetched = True
    return _us_pool


def generate_billing_address(country: str = "US") -> dict:
    pool = _ensure_us_pool()
    chosen = dict(random.choice(pool))
    chosen["country"] = "US"
    return chosen


def generate_billing_address_for_vcc(vcc: dict) -> dict:
    billing = dict(vcc.get("billing") or {})
    if billing.get("line1") and billing.get("city") and billing.get("postalCode"):
        return billing
    generated = generate_billing_address("US")
    billing.update({k: v for k, v in generated.items() if not billing.get(k)})
    return billing


    generated = generate_billing_address(country)
    billing.update({k: v for k, v in generated.items() if not billing.get(k)})
    return billing
