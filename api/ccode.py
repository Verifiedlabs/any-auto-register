from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from platforms.ccode import register_ccode, bulk_register_ccode

router = APIRouter(prefix="/ccode", tags=["ccode"])


class CcodeRegisterRequest(BaseModel):
    count: int = 10
    aff_code: str = "3GLRG6XG8VQE"
    use_proxy: bool = False


@router.post("/register")
def ccode_register(req: CcodeRegisterRequest):
    results = bulk_register_ccode(count=min(req.count, 15), aff_code=req.aff_code, use_proxy=req.use_proxy)
    success = sum(1 for r in results if r["ok"])
    return {"ok": True, "results": results, "success": success, "failed": len(results) - success}
