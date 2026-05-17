from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from platforms.ccode import register_ccode, bulk_register_ccode

router = APIRouter(prefix="/ccode", tags=["ccode"])


class CcodeRegisterRequest(BaseModel):
    gmail_base: str
    count: int = 1
    aff_code: str = "3GLRG6XG8VQE"
    delay: float = 3.0
    use_proxy: bool = False


@router.post("/register")
def ccode_register(req: CcodeRegisterRequest):
    if req.count == 1:
        result = register_ccode(req.gmail_base, aff_code=req.aff_code)
        return {"ok": True, "results": [result], "success": 1 if result["ok"] else 0, "failed": 0 if result["ok"] else 1}

    results = bulk_register_ccode(req.gmail_base, count=min(req.count, 50), aff_code=req.aff_code, delay=req.delay, use_proxy=req.use_proxy)
    success = sum(1 for r in results if r["ok"])
    return {"ok": True, "results": results, "success": success, "failed": len(results) - success}
