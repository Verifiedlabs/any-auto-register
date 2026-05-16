from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from application.provider_settings import ProviderSettingsService

router = APIRouter(prefix="/provider-settings", tags=["provider-settings"])
service = ProviderSettingsService()


class ProviderSettingUpsertRequest(BaseModel):
    id: int | None = None
    provider_type: str
    provider_key: str
    display_name: str = ""
    auth_mode: str = ""
    enabled: bool = True
    is_default: bool = False
    config: dict[str, str] = Field(default_factory=dict)
    auth: dict[str, str] = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


@router.get("")
def list_provider_settings(provider_type: str):
    return service.list_settings(provider_type)


@router.put("")
def save_provider_setting(body: ProviderSettingUpsertRequest):
    try:
        return service.save_setting(body.model_dump())
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@router.post("")
def create_provider_setting(body: ProviderSettingUpsertRequest):
    try:
        return service.save_setting(body.model_dump())
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@router.delete("/{setting_id}")
def delete_provider_setting(setting_id: int):
    result = service.delete_setting(setting_id)
    if not result["ok"]:
        raise HTTPException(404, "provider setting not found")
    return result


class ProviderTestRequest(BaseModel):
    provider_type: str
    provider_key: str
    config: dict[str, str] = Field(default_factory=dict)
    auth: dict[str, str] = Field(default_factory=dict)


@router.post("/test")
def test_provider(body: ProviderTestRequest):
    """Test whether the provider configuration is correct — try to create/get a mailbox address."""
    from infrastructure.provider_definitions_repository import ProviderDefinitionsRepository

    definitions = ProviderDefinitionsRepository()
    definition = definitions.get_by_key(body.provider_type, body.provider_key)
    if not definition:
        return {"ok": False, "error": f"Provider definition not found: {body.provider_key}"}

    # Merge config + auth into a flat dict (same as runtime)
    extra = {**body.config, **body.auth}

    if body.provider_type == "mailbox":
        return _test_mailbox(definition.driver_type or body.provider_key, extra, definition)
    elif body.provider_type == "captcha":
        return {"ok": True, "message": "Captcha service does not support online testing yet. Please verify in a registration task."}
    elif body.provider_type == "sms":
        return {"ok": True, "message": "SMS service does not support online testing yet. Please verify in a registration task."}
    else:
        return {"ok": False, "error": f"Unsupported provider type for testing: {body.provider_type}"}


def _test_mailbox(driver_type: str, extra: dict, definition) -> dict:
    """Try to create a mailbox with the given configuration to verify it is correct."""
    import traceback
    from core.base_mailbox import MAILBOX_FACTORY_REGISTRY

    factory = MAILBOX_FACTORY_REGISTRY.get(driver_type)
    if not factory:
        return {"ok": False, "error": f"Mailbox driver not found: {driver_type}"}

    try:
        if driver_type in ("generic_http_mailbox", "generic_http"):
            pipeline_config = definition.get_metadata() if definition else {}
            mailbox = factory(extra, None, pipeline_config=pipeline_config)
        else:
            mailbox = factory(extra, None)

        if hasattr(mailbox, "peek_email"):
            email = mailbox.peek_email()
            return {
                "ok": True,
                "message": f"Test succeeded! Available mailbox: {email}",
                "email": email,
            }

        account = mailbox.get_email()
        return {
            "ok": True,
            "message": f"Test succeeded! Generated mailbox: {account.email}",
            "email": account.email,
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": f"Test failed: {str(exc)}",
            "detail": traceback.format_exc()[-500:],
        }
