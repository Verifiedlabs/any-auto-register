from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.bin_generator import generate_cards, lookup_bin, luhn_valid, check_card_live
from core.address_gen import generate_billing_address, generate_holder_name
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
    check_live: bool = False
    billing_country: str = "US"


class BinLookupRequest(BaseModel):
    bin: str


class CardCheckRequest(BaseModel):
    number: str
    exp_month: int
    exp_year: int
    cvc: str


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

    bin_country = ""
    bin_info = lookup_bin(req.bin)
    if bin_info.get("country"):
        bin_country = bin_info["country"]
    if not bin_country:
        bin_country = req.billing_country or "US"

    if req.check_live:
        live_cards = []
        dead_cards = []
        error_cards = []
        max_attempts = req.count * 10
        attempts = 0
        while len(live_cards) < req.count and attempts < max_attempts:
            batch = generate_cards(
                bin_prefix=req.bin,
                count=min(5, req.count - len(live_cards)),
                exp_month=req.exp_month,
                exp_year=req.exp_year,
                length=req.length,
            )
            for card in batch:
                attempts += 1
                result = check_card_live(card["number"], card["expMonth"], card["expYear"], card["cvc"])
                card["check"] = result
                if result["live"]:
                    live_cards.append(card)
                    if len(live_cards) >= req.count:
                        break
                elif result["status"] == "error":
                    error_cards.append(card)
                    if len(error_cards) >= 3:
                        break
                else:
                    dead_cards.append(card)
            if len(error_cards) >= 3:
                break
        cards = live_cards + dead_cards + error_cards
        cards_to_save = live_cards
    else:
        live_cards = cards
        dead_cards = []
        error_cards = []
        cards_to_save = cards

    if req.save_to_pool and cards_to_save:
        billing = generate_billing_address(bin_country)
        with Session(engine) as s:
            for card in cards_to_save:
                holder_name = generate_holder_name(bin_country)
                vcc = VccModel(
                    number=card["number"],
                    exp_month=card["expMonth"],
                    exp_year=card["expYear"],
                    cvc=card["cvc"],
                    billing_name=holder_name,
                    billing_country=bin_country,
                    billing_line1=billing.get("line1", ""),
                    billing_city=billing.get("city", ""),
                    billing_state=billing.get("state", ""),
                    billing_postal_code=billing.get("postalCode", ""),
                    label=f"gen-{card['bin']}-{card['last4']}",
                    status="active",
                )
                s.add(vcc)
            s.commit()

    return {
        "ok": True,
        "cards": cards,
        "count": len(cards),
        "live": len(live_cards),
        "dead": len(dead_cards),
        "errors": len(error_cards),
        "saved": req.save_to_pool and len(cards_to_save) > 0,
        "saved_count": len(cards_to_save) if req.save_to_pool else 0,
    }


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


@router.post("/check")
def card_check(req: CardCheckRequest):
    result = check_card_live(req.number, req.exp_month, req.exp_year, req.cvc)
    return {"ok": True, **result}
