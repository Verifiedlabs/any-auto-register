from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.bin_generator import generate_cards, lookup_bin, luhn_valid
from core.address_gen import generate_billing_address
from core.db import VccModel, engine
from sqlmodel import Session

router = APIRouter(prefix="/bin", tags=["bin"])


class BinGenerateRequest(BaseModel):
    bin: str
    count: int = 10
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None
    length: Optional[int] = None
    save_to_pool: bool = False
    billing_country: str = "US"


class BinLookupRequest(BaseModel):
    bin: str


class AddressGenerateRequest(BaseModel):
    country: str = "US"
    count: int = 1


@router.post("/generate")
def bin_generate(req: BinGenerateRequest):
    try:
        cards = generate_cards(
            bin_prefix=req.bin,
            count=min(req.count, 100),
            exp_month=req.exp_month,
            exp_year=req.exp_year,
            length=req.length,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if req.save_to_pool and cards:
        billing = generate_billing_address(req.billing_country)
        with Session(engine) as s:
            for card in cards:
                vcc = VccModel(
                    number=card["number"],
                    exp_month=card["expMonth"],
                    exp_year=card["expYear"],
                    cvc=card["cvc"],
                    billing_name=billing.get("name", "Generated User"),
                    billing_country=req.billing_country,
                    billing_line1=billing.get("line1", ""),
                    billing_city=billing.get("city", ""),
                    billing_state=billing.get("state", ""),
                    billing_postal_code=billing.get("postalCode", ""),
                    label=f"gen-{card['bin']}-{card['last4']}",
                    status="active",
                )
                s.add(vcc)
            s.commit()

    return {"ok": True, "cards": cards, "count": len(cards), "saved": req.save_to_pool}


@router.post("/lookup")
def bin_lookup(req: BinLookupRequest):
    result = lookup_bin(req.bin)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return {"ok": True, "data": result}


@router.post("/validate")
def bin_validate(number: str):
    cleaned = ''.join(c for c in number if c.isdigit())
    return {"ok": True, "valid": luhn_valid(cleaned), "number": cleaned}


@router.post("/address")
def generate_address(req: AddressGenerateRequest):
    addresses = []
    for _ in range(min(req.count, 20)):
        addr = generate_billing_address(req.country)
        addresses.append(addr)
    return {"ok": True, "addresses": addresses, "count": len(addresses)}
