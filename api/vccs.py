from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.db import VccModel, engine
from sqlmodel import Session, select

router = APIRouter(prefix="/vccs", tags=["vccs"])


class VccCreateRequest(BaseModel):
    number: str
    exp_month: int
    exp_year: int
    cvc: str
    billing_name: str = ""
    billing_country: str = "US"
    billing_line1: str = ""
    billing_line2: str = ""
    billing_city: str = ""
    billing_state: str = ""
    billing_postal_code: str = ""
    label: str = ""


class VccUpdateRequest(BaseModel):
    status: Optional[str] = None
    used_by: Optional[str] = None
    label: Optional[str] = None


def _vcc_to_dict(vcc: VccModel) -> dict:
    return {
        "id": vcc.id,
        "number": f"****{vcc.number[-4:]}",
        "exp_month": vcc.exp_month,
        "exp_year": vcc.exp_year,
        "billing_name": vcc.billing_name,
        "billing_country": vcc.billing_country,
        "billing_line1": vcc.billing_line1,
        "billing_city": vcc.billing_city,
        "billing_state": vcc.billing_state,
        "billing_postal_code": vcc.billing_postal_code,
        "label": vcc.label,
        "status": vcc.status,
        "used_by": vcc.used_by,
        "created_at": vcc.created_at.isoformat() if vcc.created_at else None,
        "updated_at": vcc.updated_at.isoformat() if vcc.updated_at else None,
    }


def _vcc_to_full_dict(vcc: VccModel) -> dict:
    return {
        **_vcc_to_dict(vcc),
        "number": vcc.number,
        "cvc": vcc.cvc,
        "billing_line2": vcc.billing_line2,
    }


@router.get("")
def list_vccs(status: Optional[str] = None):
    with Session(engine) as s:
        query = select(VccModel)
        if status:
            query = query.where(VccModel.status == status)
        vccs = s.exec(query).all()
        return {"vccs": [_vcc_to_dict(v) for v in vccs], "total": len(vccs)}


@router.post("")
def create_vcc(req: VccCreateRequest):
    number = req.number.replace(" ", "").replace("-", "")
    with Session(engine) as s:
        vcc = VccModel(
            number=number,
            exp_month=req.exp_month,
            exp_year=req.exp_year,
            cvc=req.cvc,
            billing_name=req.billing_name,
            billing_country=req.billing_country,
            billing_line1=req.billing_line1,
            billing_line2=req.billing_line2,
            billing_city=req.billing_city,
            billing_state=req.billing_state,
            billing_postal_code=req.billing_postal_code,
            label=req.label,
            status="active",
        )
        s.add(vcc)
        s.commit()
        s.refresh(vcc)
        return {"ok": True, "vcc": _vcc_to_dict(vcc)}


@router.post("/batch")
def batch_create_vccs(vccs: list[VccCreateRequest]):
    created = []
    with Session(engine) as s:
        for req in vccs:
            number = req.number.replace(" ", "").replace("-", "")
            vcc = VccModel(
                number=number,
                exp_month=req.exp_month,
                exp_year=req.exp_year,
                cvc=req.cvc,
                billing_name=req.billing_name,
                billing_country=req.billing_country,
                billing_line1=req.billing_line1,
                billing_line2=req.billing_line2,
                billing_city=req.billing_city,
                billing_state=req.billing_state,
                billing_postal_code=req.billing_postal_code,
                label=req.label,
                status="active",
            )
            s.add(vcc)
            created.append(vcc)
        s.commit()
        for v in created:
            s.refresh(v)
        return {"ok": True, "created": len(created), "vccs": [_vcc_to_dict(v) for v in created]}


@router.get("/{vcc_id}")
def get_vcc(vcc_id: int):
    with Session(engine) as s:
        vcc = s.get(VccModel, vcc_id)
        if not vcc:
            raise HTTPException(status_code=404, detail="VCC not found")
        return {"vcc": _vcc_to_full_dict(vcc)}


@router.patch("/{vcc_id}")
def update_vcc(vcc_id: int, req: VccUpdateRequest):
    with Session(engine) as s:
        vcc = s.get(VccModel, vcc_id)
        if not vcc:
            raise HTTPException(status_code=404, detail="VCC not found")
        if req.status is not None:
            vcc.status = req.status
        if req.used_by is not None:
            vcc.used_by = req.used_by
        if req.label is not None:
            vcc.label = req.label
        s.add(vcc)
        s.commit()
        s.refresh(vcc)
        return {"ok": True, "vcc": _vcc_to_dict(vcc)}


@router.delete("/{vcc_id}")
def delete_vcc(vcc_id: int):
    with Session(engine) as s:
        vcc = s.get(VccModel, vcc_id)
        if not vcc:
            raise HTTPException(status_code=404, detail="VCC not found")
        s.delete(vcc)
        s.commit()
        return {"ok": True}


@router.get("/next/active")
def get_next_active_vcc():
    with Session(engine) as s:
        vcc = s.exec(select(VccModel).where(VccModel.status == "active").limit(1)).first()
        if not vcc:
            raise HTTPException(status_code=404, detail="No active VCC available")
        return {"vcc": _vcc_to_full_dict(vcc)}
