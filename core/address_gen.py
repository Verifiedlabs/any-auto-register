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


STATIC_INTL_ADDRESSES: dict[str, list[dict]] = {
    "KR": [
        {"line1": "231 Teheran-ro", "city": "Seoul", "state": "Gangnam-gu", "postalCode": "06142"},
        {"line1": "92 Hangang-daero", "city": "Seoul", "state": "Yongsan-gu", "postalCode": "04386"},
        {"line1": "300 Olympic-ro", "city": "Seoul", "state": "Songpa-gu", "postalCode": "05551"},
        {"line1": "50 Sejong-daero", "city": "Seoul", "state": "Jung-gu", "postalCode": "04513"},
        {"line1": "12 Yeouido-dong", "city": "Seoul", "state": "Yeongdeungpo-gu", "postalCode": "07241"},
    ],
    "GB": [
        {"line1": "1 London Bridge St", "city": "London", "state": "England", "postalCode": "SE1 9GF"},
        {"line1": "1 Canada Square", "city": "London", "state": "England", "postalCode": "E14 5AH"},
        {"line1": "30 St Mary Axe", "city": "London", "state": "England", "postalCode": "EC3A 8BF"},
    ],
    "AU": [
        {"line1": "120 Collins St", "city": "Melbourne", "state": "VIC", "postalCode": "3000"},
        {"line1": "1 Martin Place", "city": "Sydney", "state": "NSW", "postalCode": "2000"},
        {"line1": "1 William St", "city": "Brisbane", "state": "QLD", "postalCode": "4000"},
    ],
    "CA": [
        {"line1": "100 King St W", "city": "Toronto", "state": "ON", "postalCode": "M5X 1A9"},
        {"line1": "888 Dunsmuir St", "city": "Vancouver", "state": "BC", "postalCode": "V6C 3K4"},
        {"line1": "1000 De La Gauchetiere W", "city": "Montreal", "state": "QC", "postalCode": "H3B 4W5"},
    ],
    "SG": [
        {"line1": "1 Raffles Place", "city": "Singapore", "state": "", "postalCode": "048616"},
        {"line1": "8 Marina View", "city": "Singapore", "state": "", "postalCode": "018960"},
        {"line1": "168 Robinson Rd", "city": "Singapore", "state": "", "postalCode": "068912"},
    ],
    "DE": [
        {"line1": "Unter den Linden 1", "city": "Berlin", "state": "Berlin", "postalCode": "10117"},
        {"line1": "Maximilianstrasse 2", "city": "Munich", "state": "Bavaria", "postalCode": "80539"},
    ],
    "FR": [
        {"line1": "1 Rue de Rivoli", "city": "Paris", "state": "Ile-de-France", "postalCode": "75001"},
        {"line1": "1 Avenue des Champs-Elysees", "city": "Paris", "state": "Ile-de-France", "postalCode": "75008"},
    ],
    "JP": [
        {"line1": "1-1 Marunouchi", "city": "Tokyo", "state": "Tokyo", "postalCode": "100-0005"},
        {"line1": "2-1 Nihonbashi", "city": "Tokyo", "state": "Tokyo", "postalCode": "103-0027"},
    ],
    "ID": [
        {"line1": "Jalan Jenderal Sudirman Kav 1", "city": "Jakarta Selatan", "state": "DKI Jakarta", "postalCode": "12190"},
        {"line1": "Jalan Thamrin 1", "city": "Jakarta Pusat", "state": "DKI Jakarta", "postalCode": "10310"},
    ],
    "IN": [
        {"line1": "1 Nariman Point", "city": "Mumbai", "state": "Maharashtra", "postalCode": "400021"},
        {"line1": "1 Connaught Place", "city": "New Delhi", "state": "Delhi", "postalCode": "110001"},
    ],
    "TR": [
        {"line1": "Buyukdere Cad 1", "city": "Istanbul", "state": "Istanbul", "postalCode": "34394"},
        {"line1": "Ataturk Bulvari 1", "city": "Ankara", "state": "Ankara", "postalCode": "06680"},
    ],
    "HK": [
        {"line1": "1 Harbour Rd", "city": "Wan Chai", "state": "Hong Kong", "postalCode": "000000"},
        {"line1": "1 Connaught Place", "city": "Central", "state": "Hong Kong", "postalCode": "000000"},
    ],
    "NL": [
        {"line1": "1 Herengracht", "city": "Amsterdam", "state": "North Holland", "postalCode": "1017 BZ"},
        {"line1": "1 Coolsingel", "city": "Rotterdam", "state": "South Holland", "postalCode": "3011 AD"},
    ],
    "BR": [
        {"line1": "Av Paulista 1000", "city": "Sao Paulo", "state": "SP", "postalCode": "01310-100"},
        {"line1": "Av Rio Branco 1", "city": "Rio de Janeiro", "state": "RJ", "postalCode": "20040-009"},
    ],
    "MX": [
        {"line1": "Paseo de la Reforma 1", "city": "Mexico City", "state": "CDMX", "postalCode": "06600"},
    ],
    "PH": [
        {"line1": "Ayala Ave 1", "city": "Makati", "state": "Metro Manila", "postalCode": "1226"},
    ],
    "TH": [
        {"line1": "1 Silom Rd", "city": "Bangkok", "state": "Bangkok", "postalCode": "10500"},
    ],
    "VN": [
        {"line1": "1 Le Duan", "city": "Ho Chi Minh City", "state": "District 1", "postalCode": "700000"},
    ],
    "MY": [
        {"line1": "1 Jalan Sultan Ismail", "city": "Kuala Lumpur", "state": "WP Kuala Lumpur", "postalCode": "50250"},
    ],
}


def generate_billing_address(country: str = "US") -> dict:
    country = country.upper()
    if country == "US":
        pool = _ensure_us_pool()
        chosen = dict(random.choice(pool))
        chosen["country"] = "US"
        return chosen
    intl = STATIC_INTL_ADDRESSES.get(country)
    if intl:
        chosen = dict(random.choice(intl))
        chosen.setdefault("line2", "")
        chosen["country"] = country
        return chosen
    pool = _ensure_us_pool()
    chosen = dict(random.choice(pool))
    chosen["country"] = "US"
    return chosen


def generate_billing_address_for_vcc(vcc: dict) -> dict:
    billing = dict(vcc.get("billing") or {})
    country = str(billing.get("country") or "US").upper()
    if billing.get("line1") and billing.get("city") and billing.get("postalCode"):
        return billing
    generated = generate_billing_address(country)
    billing.update({k: v for k, v in generated.items() if not billing.get(k)})
    return billing
