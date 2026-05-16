from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.db import engine, VccModel
from sqlmodel import Session, select

router = APIRouter(prefix="/upgrade", tags=["upgrade"])


class UpgradeRequest(BaseModel):
    platform: str
    account_id: int
    vcc_id: Optional[int] = None
    headless: bool = False
    on_challenge: str = "pause"
    timeout: int = 180


class BulkUpgradeRequest(BaseModel):
    platform: str
    account_ids: list[int]
    vcc_id: Optional[int] = None
    headless: bool = False
    on_challenge: str = "pause"
    timeout: int = 180


def _get_vcc_dict(vcc_id: Optional[int]) -> Optional[dict]:
    if not vcc_id:
        with Session(engine) as s:
            vcc = s.exec(select(VccModel).where(VccModel.status == "active").limit(1)).first()
            if not vcc:
                return None
    else:
        with Session(engine) as s:
            vcc = s.get(VccModel, vcc_id)
            if not vcc:
                return None
    return {
        "number": vcc.number,
        "expMonth": vcc.exp_month,
        "expYear": vcc.exp_year,
        "cvc": vcc.cvc,
        "billing": {
            "name": vcc.billing_name,
            "country": vcc.billing_country,
            "line1": vcc.billing_line1,
            "line2": vcc.billing_line2,
            "city": vcc.billing_city,
            "state": vcc.billing_state,
            "postalCode": vcc.billing_postal_code,
        },
    }


def _get_account(account_id: int) -> dict:
    from core.db import AccountModel, AccountCredentialModel
    with Session(engine) as s:
        account = s.get(AccountModel, account_id)
        if not account:
            raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
        creds = s.exec(select(AccountCredentialModel).where(AccountCredentialModel.account_id == account_id)).all()
        cred_map = {c.key: c.value for c in creds}
        return {
            "id": account.id,
            "email": account.email,
            "password": account.password,
            "platform": account.platform,
            "extra": cred_map,
        }


def _upgrade_windsurf(account_data: dict, vcc: Optional[dict], headless: bool, timeout: int, on_challenge: str) -> dict:
    from platforms.windsurf.plugin import WindsurfPlatform
    from core.base_platform import Account, RegisterConfig

    config = RegisterConfig(executor_type="headless" if headless else "headed")
    platform = WindsurfPlatform(config=config)

    account = Account(
        email=account_data["email"],
        password=account_data["password"],
        platform="windsurf",
    )
    account.extra = account_data.get("extra", {})

    params = {"timeout": timeout}
    if vcc:
        params["vcc"] = vcc
        params["headless"] = "true" if headless else "false"
        return platform.execute_action("generate_link_browser", account, params)
    else:
        return platform.execute_action("generate_link", account, params)


def _upgrade_kiro(account_data: dict, vcc: Optional[dict], headless: bool, timeout: int, on_challenge: str) -> dict:
    from platforms.kiro.kiro_upgrade import upgrade_kiro_to_pro

    extra = account_data.get("extra", {})
    session_data = {
        "email": account_data["email"],
        "cookies": extra.get("cookies", []),
        "localStorage": extra.get("localStorage", {}),
        "sessionStorage": extra.get("sessionStorage", {}),
        "accessToken": extra.get("accessToken", "") or extra.get("access_token", ""),
        "refreshToken": extra.get("refreshToken", "") or extra.get("refresh_token", ""),
    }

    return upgrade_kiro_to_pro(
        session_data=session_data,
        password=account_data.get("password", ""),
        vcc=vcc,
        headless=headless,
        proxy=None,
        timeout=timeout,
        on_challenge=on_challenge,
    )


PLATFORM_UPGRADERS = {
    "windsurf": _upgrade_windsurf,
    "kiro": _upgrade_kiro,
}


@router.get("/platforms")
def list_upgrade_platforms():
    return {"ok": True, "platforms": list(PLATFORM_UPGRADERS.keys())}


@router.post("/single")
def upgrade_single(req: UpgradeRequest):
    if req.platform not in PLATFORM_UPGRADERS:
        raise HTTPException(status_code=400, detail=f"Platform '{req.platform}' not supported. Available: {list(PLATFORM_UPGRADERS.keys())}")

    account_data = _get_account(req.account_id)
    if account_data["platform"] != req.platform:
        raise HTTPException(status_code=400, detail=f"Account {req.account_id} is {account_data['platform']}, not {req.platform}")

    vcc = _get_vcc_dict(req.vcc_id)

    upgrader = PLATFORM_UPGRADERS[req.platform]
    result = upgrader(account_data, vcc, req.headless, req.timeout, req.on_challenge)
    return {"ok": True, "result": result}


@router.post("/bulk")
def upgrade_bulk(req: BulkUpgradeRequest):
    if req.platform not in PLATFORM_UPGRADERS:
        raise HTTPException(status_code=400, detail=f"Platform '{req.platform}' not supported")

    results = []
    for account_id in req.account_ids:
        try:
            account_data = _get_account(account_id)
            if account_data["platform"] != req.platform:
                results.append({"account_id": account_id, "ok": False, "error": f"Wrong platform: {account_data['platform']}"})
                continue
            vcc = _get_vcc_dict(req.vcc_id)
            if not vcc:
                results.append({"account_id": account_id, "ok": False, "error": "No active VCC available"})
                break
            upgrader = PLATFORM_UPGRADERS[req.platform]
            result = upgrader(account_data, vcc, req.headless, req.timeout, req.on_challenge)
            results.append({"account_id": account_id, "ok": True, "result": result})
        except Exception as e:
            results.append({"account_id": account_id, "ok": False, "error": str(e)})

    return {"ok": True, "results": results, "total": len(results)}


@router.get("/accounts/{platform}")
def list_upgradeable_accounts(platform: str):
    from core.db import AccountModel, AccountOverviewModel
    with Session(engine) as s:
        accounts = s.exec(
            select(AccountModel).where(AccountModel.platform == platform)
        ).all()
        result = []
        for a in accounts:
            overview = s.get(AccountOverviewModel, a.id)
            plan = overview.plan_state if overview else "unknown"
            result.append({
                "id": a.id,
                "email": a.email,
                "plan": plan,
                "upgradeable": plan in ("free", "unknown", "registered"),
            })
        return {"ok": True, "accounts": result, "total": len(result)}
